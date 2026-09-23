"""HomePage: Page Object representing the e-commerce storefront landing page."""

from __future__ import annotations

from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from config.config import BASE_URL
from pages.base_page import BasePage, Locator
from utilities.logger import get_logger

logger = get_logger(__name__)


class HomePage(BasePage):
    """Encapsulates elements and actions for the storefront home page."""

    # Navigation & Header Locators
    NAV_HOME: Locator = (By.XPATH, "//header//a[normalize-space()='Home']")
    NAV_LOGIN: Locator = (By.XPATH, "//header//a[contains(@href, '/login') or contains(text(), 'Signup / Login')]")
    NAV_PRODUCTS: Locator = (By.XPATH, "//header//a[contains(@href, '/products') or contains(text(), 'Products')]")
    NAV_CART: Locator = (By.XPATH, "//header//a[contains(@href, '/view_cart') or contains(text(), 'Cart')]")
    NAV_LOGGED_IN: Locator = (By.XPATH, "//header//a[contains(., 'Logged in as')]")
    NAV_LOGOUT: Locator = (By.XPATH, "//header//a[contains(@href, '/logout')]")
    NAV_DELETE_ACCOUNT: Locator = (By.XPATH, "//header//a[contains(@href, '/delete_account')]")

    # Consent Banner / Privacy Overlay
    CONSENT_BTN: Locator = (By.CSS_SELECTOR, "p.fc-button-headline, button.fc-cta-consent, .fc-button")

    def __init__(self, driver: WebDriver, timeout: Optional[int] = None) -> None:
        super().__init__(driver, timeout)

    def load(self) -> HomePage:
        """Navigates to the base application home page."""
        logger.info("Loading Home Page: %s", BASE_URL)
        self.open_url(BASE_URL)
        self.handle_consent_if_present()
        return self

    def handle_consent_if_present(self) -> None:
        """Handles consent / cookie popups if rendered on initial visit."""
        if self.is_element_displayed(self.CONSENT_BTN, timeout=3):
            logger.info("Consent overlay detected. Dismissing...")
            try:
                self.click(self.CONSENT_BTN, timeout=3)
            except Exception as e:
                logger.debug("Consent dismissal non-critical: %s", e)

    def go_to_login(self) -> BasePage:
        """Navigates to the Signup / Login page."""
        logger.info("Navigating to Signup / Login page")
        self.click(self.NAV_LOGIN)
        from pages.login_page import LoginPage
        return LoginPage(self.driver, self.timeout)

    def go_to_products(self) -> BasePage:
        """Navigates to the Products catalog page."""
        logger.info("Navigating to Products catalog page")
        self.click(self.NAV_PRODUCTS)
        from pages.product_page import ProductPage
        return ProductPage(self.driver, self.timeout)

    def go_to_cart(self) -> BasePage:
        """Navigates directly to the Shopping Cart page."""
        logger.info("Navigating to Cart page from header")
        self.click(self.NAV_CART)
        from pages.cart_page import CartPage
        return CartPage(self.driver, self.timeout)

    def is_logged_in(self) -> bool:
        """Checks if a user is currently logged in."""
        return self.is_element_displayed(self.NAV_LOGGED_IN, timeout=5)

    def get_logged_in_username(self) -> str:
        """Returns the logged-in user's display name."""
        raw_text = self.get_text(self.NAV_LOGGED_IN)
        # Expected format: 'Logged in as <username>'
        if "Logged in as" in raw_text:
            return raw_text.replace("Logged in as", "").strip()
        return raw_text

    def logout(self) -> HomePage:
        """Logs out the active session if logged in."""
        if self.is_logged_in():
            logger.info("Logging out current user session")
            self.click(self.NAV_LOGOUT)
        return self
