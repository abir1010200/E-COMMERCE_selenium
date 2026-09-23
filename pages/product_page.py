"""ProductPage: Page Object representing catalog search, details, and add-to-cart."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage, Locator
from utilities.logger import get_logger

logger = get_logger(__name__)


class ProductPage(BasePage):
    """Encapsulates catalog search, filtering, product details, and add-to-cart operations."""

    # Search & Catalog Locators
    SEARCH_INPUT: Locator = (By.ID, "search_product")
    SEARCH_SUBMIT_BTN: Locator = (By.ID, "submit_search")
    SEARCHED_PRODUCTS_HEADING: Locator = (By.XPATH, "//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'searched products')]")
    PRODUCT_CARDS: Locator = (By.CSS_SELECTOR, ".features_items .col-sm-4")
    FIRST_PRODUCT_VIEW_BTN: Locator = (By.XPATH, "(//a[contains(@href, '/product_details/')])[1]")

    # Product Details Page Locators
    PRODUCT_NAME_HEADING: Locator = (By.XPATH, "//div[contains(@class, 'product-information')]//h2")
    PRODUCT_PRICE_TEXT: Locator = (By.XPATH, "//div[contains(@class, 'product-information')]//span/span")
    PRODUCT_QUANTITY_INPUT: Locator = (By.ID, "quantity")
    ADD_TO_CART_BTN: Locator = (By.CSS_SELECTOR, "button.cart")

    # Add to Cart Modal Dialog Locators (Requirement 9)
    CART_MODAL: Locator = (By.ID, "cartModal")
    MODAL_VIEW_CART_LINK: Locator = (By.XPATH, "//div[@id='cartModal']//a[contains(@href, '/view_cart')] | //div[@id='cartModal']//u[contains(text(), 'View Cart')]")
    MODAL_CONTINUE_SHOPPING_BTN: Locator = (By.XPATH, "//div[@id='cartModal']//button[contains(@class, 'close-modal')]")

    # Header Cart Link (Fallback)
    HEADER_CART_LINK: Locator = (By.XPATH, "//header//a[contains(@href, '/view_cart')]")

    def __init__(self, driver: WebDriver, timeout: Optional[int] = None) -> None:
        super().__init__(driver, timeout)

    def search_product(self, product_name: str) -> ProductPage:
        """Searches for a product using the search bar."""
        logger.info("SEARCH: Querying catalog for '%s'", product_name)
        self.type_text(self.SEARCH_INPUT, product_name)
        self.click(self.SEARCH_SUBMIT_BTN)
        self.dismiss_common_overlays()
        return self

    def verify_search_results_displayed(self, expected_product: Optional[str] = None) -> ProductPage:
        """Verifies that search results are displayed and contain matching items."""
        self.wait_for_visible(self.SEARCHED_PRODUCTS_HEADING, timeout=10)
        product_elements = self.find_elements(self.PRODUCT_CARDS)
        assert len(product_elements) > 0, f"No products found for search query '{expected_product}'"

        logger.info("SEARCH: %d matching product(s) returned by catalog query", len(product_elements))

        if expected_product:
            # Verify at least one card contains the expected product name
            found_match = False
            for elem in product_elements:
                if expected_product.lower() in elem.text.lower():
                    found_match = True
                    break
            assert found_match, f"Expected product '{expected_product}' was not found in catalog search results"
            logger.info("SEARCH: Confirmed expected product '%s' is present in results", expected_product)

        return self

    def open_product_details(self, product_name: Optional[str] = None) -> ProductPage:
        """Opens product detail page either for a specific named product or the first result."""
        if product_name:
            logger.info("Opening details for product: '%s'", product_name)
            xpath = (
                f"//div[contains(@class, 'productinfo')]//p[contains(translate(text(), "
                f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{product_name.lower()}')]"
                f"/ancestor::div[contains(@class, 'col-sm-4')]//a[contains(@href, '/product_details/')]"
            )
            specific_btn: Locator = (By.XPATH, xpath)
            if self.is_element_present(specific_btn, timeout=5):
                self.scroll_to_element(specific_btn)
                self.click(specific_btn)
            else:
                logger.warning("Specific view button for '%s' not found, opening first product result", product_name)
                self.click(self.FIRST_PRODUCT_VIEW_BTN)
        else:
            logger.info("Opening first product result details")
            self.click(self.FIRST_PRODUCT_VIEW_BTN)

        self.dismiss_common_overlays()
        self.wait_for_visible(self.PRODUCT_NAME_HEADING, timeout=10)
        return self

    def get_product_name(self) -> str:
        """Retrieves the product title from the details page."""
        return self.get_text(self.PRODUCT_NAME_HEADING)

    def get_product_unit_price(self) -> float:
        """Retrieves and parses the numeric unit price from the details page."""
        price_text = self.get_text(self.PRODUCT_PRICE_TEXT)
        # Extract digits: e.g. 'Rs. 500' -> 500.0
        match = re.search(r"(\d+(?:\.\d+)?)", price_text.replace(",", ""))
        if match:
            return float(match.group(1))
        return 0.0

    def set_quantity(self, quantity: int) -> ProductPage:
        """Sets the desired purchase quantity on the product detail page."""
        logger.info("PRODUCT DETAIL: Setting quantity to %d", quantity)
        self.type_text(self.PRODUCT_QUANTITY_INPUT, quantity, clear=True)
        return self

    def add_to_cart(self, quantity: Optional[int] = None) -> ProductPage:
        """Sets quantity (if provided) and clicks Add to Cart."""
        if quantity is not None and quantity > 1:
            self.set_quantity(quantity)

        logger.info("ADD TO CART: Clicking 'Add to cart' button")
        self.click(self.ADD_TO_CART_BTN)
        return self

    def proceed_to_cart_from_modal(self) -> BasePage:
        """Safely handles the Add to Cart confirmation modal and navigates to the cart.

        Meets Requirement 9 (popup / modal handling).
        """
        logger.info("POPUP HANDLING: Waiting for Add to Cart confirmation modal...")
        try:
            self.wait_for_visible(self.CART_MODAL, timeout=8)
            logger.info("Confirmation modal displayed. Clicking 'View Cart' link.")
            self.click(self.MODAL_VIEW_CART_LINK, timeout=5)
        except Exception:
            logger.warning("Modal link interaction failed; navigating to cart via header")
            try:
                self.click(self.HEADER_CART_LINK, timeout=5)
            except Exception:
                from config.config import BASE_URL
                self.open_url(f"{BASE_URL}/view_cart")

        self.dismiss_common_overlays()
        from pages.cart_page import CartPage
        return CartPage(self.driver, self.timeout)
