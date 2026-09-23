"""CartPage: Page Object representing the Shopping Cart and item verification."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage, Locator
from utilities.logger import get_logger

logger = get_logger(__name__)


class CartPage(BasePage):
    """Encapsulates Cart table interactions, quantity updates, and financial assertions."""

    # Cart Table Locators
    CART_TABLE: Locator = (By.ID, "cart_info_table")
    CART_ROWS: Locator = (By.CSS_SELECTOR, "#cart_info_table tbody tr")
    EMPTY_CART_MSG: Locator = (By.ID, "empty_cart")

    # Item Row Column Selectors (relative to row or page)
    ITEM_TITLE: Locator = (By.CSS_SELECTOR, "td.cart_description h4 a, td.text-start a, td.name a")
    ITEM_PRICE: Locator = (By.CSS_SELECTOR, "td.cart_price p, td.price")
    ITEM_QTY_BUTTON: Locator = (By.CSS_SELECTOR, "td.cart_quantity button")
    ITEM_QTY_INPUT: Locator = (By.CSS_SELECTOR, "td.cart_quantity input, input[name*='quantity']")
    ITEM_UPDATE_BTN: Locator = (By.CSS_SELECTOR, "button[type='submit'][data-bs-toggle='tooltip'], button[data-original-title='Update'], td.cart_quantity .btn-update")
    ITEM_TOTAL: Locator = (By.CSS_SELECTOR, "td.cart_total p.cart_total_price, td.total")
    ITEM_DELETE_BTN: Locator = (By.CSS_SELECTOR, "a.cart_quantity_delete, button.btn-danger")

    # Proceed to Checkout Locator
    CHECKOUT_BTN: Locator = (By.CSS_SELECTOR, "a.check_out, a[href*='checkout']")

    def __init__(self, driver: WebDriver, timeout: Optional[int] = None) -> None:
        super().__init__(driver, timeout)

    def is_cart_page_loaded(self) -> bool:
        """Verifies that the cart table or empty cart banner is visible."""
        return self.is_element_displayed(self.CART_TABLE, timeout=10)

    def get_cart_items(self) -> List[WebElement]:
        """Returns list of item rows in the cart table."""
        self.wait_for_visible(self.CART_TABLE, timeout=10)
        return self.find_elements(self.CART_ROWS)

    def get_item_row(self, product_name: Optional[str] = None) -> WebElement:
        """Locates the table row corresponding to a specific product or the first item."""
        rows = self.get_cart_items()
        assert len(rows) > 0, "Cart is empty; no item rows found."

        if not product_name:
            return rows[0]

        for row in rows:
            try:
                title_elem = row.find_element(*self.ITEM_TITLE)
                if product_name.lower() in title_elem.text.lower():
                    return row
            except Exception:
                continue

        logger.warning("Specific product row for '%s' not matched, returning first cart row.", product_name)
        return rows[0]

    def get_item_details(self, product_name: Optional[str] = None) -> Dict[str, Any]:
        """Extracts and normalizes product details (Name, Unit Price, Quantity, Total Price) from the cart."""
        row = self.get_item_row(product_name)

        title_elem = row.find_element(*self.ITEM_TITLE)
        item_name = title_elem.text.strip()

        # Parse unit price
        price_elem = row.find_element(*self.ITEM_PRICE)
        unit_price = self._parse_price(price_elem.text)

        # Parse quantity (handles both input field and button badge)
        quantity = self._parse_quantity(row)

        # Parse total price
        total_elem = row.find_element(*self.ITEM_TOTAL)
        total_price = self._parse_price(total_elem.text)

        details = {
            "name": item_name,
            "unit_price": unit_price,
            "quantity": quantity,
            "total_price": total_price,
            "raw_price": price_elem.text.strip(),
            "raw_total": total_elem.text.strip(),
        }
        logger.info("CART DETAILS RETRIEVED: %s", details)
        return details

    def update_quantity(self, new_quantity: int, product_name: Optional[str] = None) -> CartPage:
        """Updates the item quantity in the cart.

        Handles both direct editable inputs (e.g. OpenCart) and product-detail
        adjustments if the cart quantity is read-only (e.g. AutomationExercise).
        """
        logger.info("CART: Updating quantity to %d for product '%s'", new_quantity, product_name or "active item")
        row = self.get_item_row(product_name)

        # Check if an editable input exists inside the row
        inputs = row.find_elements(*self.ITEM_QTY_INPUT)
        if inputs and inputs[0].is_displayed() and inputs[0].is_enabled():
            qty_input = inputs[0]
            logger.info("Editable quantity input found in cart. Updating directly.")
            qty_input.clear()
            qty_input.send_keys(str(new_quantity))

            # Click update button if present
            update_btns = row.find_elements(*self.ITEM_UPDATE_BTN)
            if update_btns and update_btns[0].is_displayed():
                update_btns[0].click()
                self.dismiss_common_overlays()
            return self

        # If quantity badge already matches target quantity, proceed
        current_qty = self._parse_quantity(row)
        if current_qty == new_quantity:
            logger.info("Cart quantity is already %d; no adjustment needed.", new_quantity)
            return self

        # Otherwise, for platforms with static cart buttons, capture product href, delete old item, and re-add
        logger.info("Cart quantity displayed as static element (%d). Adjusting via product detail.", current_qty)
        title_link = row.find_element(*self.ITEM_TITLE)
        product_href = title_link.get_attribute("href")
        row_id = row.get_attribute("id")

        # Delete existing item to avoid accumulation
        delete_btns = row.find_elements(*self.ITEM_DELETE_BTN)
        if delete_btns:
            logger.info("Removing prior cart entry to set exact updated quantity...")
            self.driver.execute_script("arguments[0].click();", delete_btns[0])
            if row_id:
                self.wait_for_invisibility((By.ID, row_id), timeout=5)

        # Navigate to product page
        if product_href:
            self.open_url(product_href)
        else:
            self.driver.execute_script("arguments[0].click();", title_link)

        self.dismiss_common_overlays()

        # Add target updated quantity on product page and return to cart
        from pages.product_page import ProductPage
        prod_page = ProductPage(self.driver, self.timeout)
        prod_page.set_quantity(new_quantity)
        prod_page.add_to_cart()
        prod_page.proceed_to_cart_from_modal()
        return self

    def verify_cart_details(
        self,
        expected_product: str,
        expected_quantity: int,
        expected_unit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Comprehensive verification of cart details (Requirement 6).

        Asserts:
          1. Product name matches searched product
          2. Quantity equals expected updated quantity
          3. Total price = unit price × quantity
        """
        logger.info("CART VERIFICATION: Checking '%s', Qty: %d", expected_product, expected_quantity)
        details = self.get_item_details(expected_product)

        # 1. Assert Product Name
        assert expected_product.lower() in details["name"].lower(), (
            f"Cart product name mismatch! Expected '{expected_product}' in '{details['name']}'"
        )
        logger.info("PASS: Product name '%s' matched successfully.", details["name"])

        # 2. Assert Quantity
        assert details["quantity"] == expected_quantity, (
            f"Cart quantity mismatch! Expected {expected_quantity}, but found {details['quantity']}"
        )
        logger.info("PASS: Product quantity %d matched successfully.", details["quantity"])

        # 3. Assert Expected Unit Price (if specified)
        if expected_unit_price is not None:
            assert abs(details["unit_price"] - expected_unit_price) < 0.01, (
                f"Cart unit price mismatch! Expected {expected_unit_price}, but found {details['unit_price']}"
            )
            logger.info("PASS: Unit price %s matched expected value.", details["unit_price"])

        # 4. Assert Total Price = Unit Price * Quantity
        expected_total = round(details["unit_price"] * details["quantity"], 2)
        actual_total = round(details["total_price"], 2)
        assert abs(actual_total - expected_total) < 0.01, (
            f"Cart total price calculation error! Expected {expected_total} "
            f"({details['unit_price']} × {details['quantity']}), but found {actual_total}"
        )
        logger.info("PASS: Total calculation verified: %s = %s × %d", actual_total, details["unit_price"], details["quantity"])

        return details

    # ==========================================================================
    # INTERNAL PARSING HELPERS
    # ==========================================================================
    @staticmethod
    def _parse_price(text: str) -> float:
        """Extracts float number from currency strings (e.g. 'Rs. 500', '$400.00')."""
        match = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
        return float(match.group(1)) if match else 0.0

    def _parse_quantity(self, row: WebElement) -> int:
        """Safely extracts quantity from either an input or a button/badge element."""
        # 1. Try input
        inputs = row.find_elements(*self.ITEM_QTY_INPUT)
        if inputs:
            val = inputs[0].get_attribute("value")
            if val and val.strip().isdigit():
                return int(val.strip())

        # 2. Try button / badge
        buttons = row.find_elements(*self.ITEM_QTY_BUTTON)
        if buttons:
            txt = buttons[0].text.strip()
            if txt.isdigit():
                return int(txt)

        # 3. Try whole cell
        cell = row.find_element(By.CSS_SELECTOR, "td.cart_quantity")
        match = re.search(r"(\d+)", cell.text)
        return int(match.group(1)) if match else 1
