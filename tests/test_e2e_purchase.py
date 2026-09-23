"""Main End-to-End E-Commerce Purchase Flow Test Suite.

Covers all 10 mandatory requirements:
  1. Launch browser (Chrome/Firefox via WebDriverManager)
  2. Login to application (with auto-registration fallback)
  3. Search product from test data
  4. Add product to cart with option/quantity handling
  5. Update quantity on cart page
  6. Verify cart details (Product name, quantity, unit price, total price = unit * qty)
  7. Capture step-by-step screenshots & failure screenshots
  8. Read test data from Excel / JSON (parameterized per row)
  9. Safe popup, modal, and alert handling
  10. Generate execution reports & log summaries
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from utilities.data_loader import get_test_ids, load_test_data
from utilities.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.e2e
def test_e2e_purchase_flow(browser: WebDriver, test_case: Dict[str, Any]) -> None:
    """Executes the complete customer purchase journey for a data-driven record."""
    test_id = str(test_case.get("TestID", "TC_E2E"))
    product_name = str(test_case.get("Product", "Blue Top"))
    user_email = str(test_case.get("Email", ""))
    first_name = str(test_case.get("FirstName", ""))
    last_name = str(test_case.get("LastName", ""))
    full_name = f"{first_name} {last_name}".strip()
    initial_qty = int(test_case.get("InitialQuantity", 1))
    updated_qty = int(test_case.get("UpdatedQuantity", 2))
    expected_unit_price = test_case.get("ExpectedUnitPrice")

    logger.info("=" * 80)
    logger.info("STARTING E2E TEST: [%s] Product: '%s', User: '%s'", test_id, product_name, user_email)
    logger.info("Description: %s", test_case.get("Description", "E2E purchase test"))
    logger.info("=" * 80)

    # --------------------------------------------------------------------------
    # STEP 1: LAUNCH BROWSER & LOAD APPLICATION (Requirement 1)
    # --------------------------------------------------------------------------
    logger.info("[STEP 1/6] Launching browser and navigating to application homepage...")
    home_page = HomePage(browser)
    home_page.load()
    assert home_page.get_title() != "", "Browser failed to load home page title"

    # --------------------------------------------------------------------------
    # STEP 2: LOGIN TO APPLICATION (Requirement 2 & 8)
    # --------------------------------------------------------------------------
    logger.info("[STEP 2/6] Navigating to Login/Signup page and authenticating user...")
    login_page: LoginPage = home_page.go_to_login()
    assert login_page.is_login_page_displayed(), "Login/Signup page was not properly displayed"

    login_page.login_or_register(test_case)
    login_page.assert_logged_in(expected_name=first_name)
    login_page.take_screenshot("01_after_login", test_id=test_id)

    # --------------------------------------------------------------------------
    # STEP 3: SEARCH PRODUCT (Requirement 3 & 8)
    # --------------------------------------------------------------------------
    logger.info("[STEP 3/6] Navigating to catalog, searching for product '%s'...", product_name)
    product_page: ProductPage = home_page.go_to_products()
    product_page.search_product(product_name)
    product_page.verify_search_results_displayed(expected_product=product_name)
    product_page.take_screenshot("02_after_search_results", test_id=test_id)

    # --------------------------------------------------------------------------
    # STEP 4: ADD PRODUCT TO CART & HANDLE MODAL (Requirement 4 & 9)
    # --------------------------------------------------------------------------
    logger.info("[STEP 4/6] Opening product detail and adding item to shopping cart...")
    product_page.open_product_details(product_name)
    product_page.add_to_cart(quantity=initial_qty)
    cart_page: CartPage = product_page.proceed_to_cart_from_modal()
    cart_page.take_screenshot("03_after_add_to_cart", test_id=test_id)
    assert cart_page.is_cart_page_loaded(), "Cart page failed to load after adding product"

    # --------------------------------------------------------------------------
    # STEP 5: UPDATE QUANTITY (Requirement 5 & 8)
    # --------------------------------------------------------------------------
    logger.info("[STEP 5/6] Updating product quantity from %d to %d in shopping cart...", initial_qty, updated_qty)
    cart_page.update_quantity(new_quantity=updated_qty, product_name=product_name)
    cart_page.take_screenshot("04_after_quantity_update", test_id=test_id)

    # --------------------------------------------------------------------------
    # STEP 6: VERIFY CART DETAILS & FINANCIAL ACCURACY (Requirement 6 & 7)
    # --------------------------------------------------------------------------
    logger.info("[STEP 6/6] Verifying cart product name, updated quantity, and total price calculation...")
    cart_details = cart_page.verify_cart_details(
        expected_product=product_name,
        expected_quantity=updated_qty,
        expected_unit_price=expected_unit_price,
    )
    cart_page.take_screenshot("05_after_cart_verification", test_id=test_id)

    logger.info("=" * 80)
    logger.info(
        "TEST COMPLETED SUCCESSFULLY: [%s] Verified '%s' | Qty: %d | Unit: %s | Total: %s",
        test_id,
        cart_details["name"],
        cart_details["quantity"],
        cart_details["unit_price"],
        cart_details["total_price"],
    )
    logger.info("=" * 80)
