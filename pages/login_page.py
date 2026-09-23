"""LoginPage: Page Object representing Authentication and Registration flows."""

from __future__ import annotations

from typing import Any, Dict, Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage, Locator
from utilities.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """Encapsulates login, error handling, auto-registration, and login assertions."""

    # Existing User Login Form Locators
    LOGIN_EMAIL_INPUT: Locator = (By.CSS_SELECTOR, "input[data-qa='login-email']")
    LOGIN_PASSWORD_INPUT: Locator = (By.CSS_SELECTOR, "input[data-qa='login-password']")
    LOGIN_SUBMIT_BTN: Locator = (By.CSS_SELECTOR, "button[data-qa='login-button']")
    LOGIN_ERROR_MSG: Locator = (By.XPATH, "//div[contains(@class, 'login-form')]//p[contains(@style, 'red') or contains(text(), 'incorrect')]")

    # New User Signup Form Locators
    SIGNUP_NAME_INPUT: Locator = (By.CSS_SELECTOR, "input[data-qa='signup-name']")
    SIGNUP_EMAIL_INPUT: Locator = (By.CSS_SELECTOR, "input[data-qa='signup-email']")
    SIGNUP_SUBMIT_BTN: Locator = (By.CSS_SELECTOR, "button[data-qa='signup-button']")
    SIGNUP_ERROR_MSG: Locator = (By.XPATH, "//form[contains(@action, 'signup')]//p[contains(@style, 'red') or contains(text(), 'already exist')]")

    # Full Registration Form Locators
    GENDER_MALE_RADIO: Locator = (By.ID, "id_gender1")
    REG_PASSWORD_INPUT: Locator = (By.ID, "password")
    REG_DAYS_SELECT: Locator = (By.ID, "days")
    REG_MONTHS_SELECT: Locator = (By.ID, "months")
    REG_YEARS_SELECT: Locator = (By.ID, "years")
    REG_FIRST_NAME_INPUT: Locator = (By.ID, "first_name")
    REG_LAST_NAME_INPUT: Locator = (By.ID, "last_name")
    REG_ADDRESS_INPUT: Locator = (By.ID, "address1")
    REG_COUNTRY_SELECT: Locator = (By.ID, "country")
    REG_STATE_INPUT: Locator = (By.ID, "state")
    REG_CITY_INPUT: Locator = (By.ID, "city")
    REG_ZIPCODE_INPUT: Locator = (By.ID, "zipcode")
    REG_MOBILE_INPUT: Locator = (By.ID, "mobile_number")
    REG_CREATE_ACCOUNT_BTN: Locator = (By.CSS_SELECTOR, "button[data-qa='create-account']")

    # Post-Registration Confirmation
    ACCOUNT_CREATED_HEADING: Locator = (By.CSS_SELECTOR, "h2[data-qa='account-created']")
    CONTINUE_BTN: Locator = (By.CSS_SELECTOR, "a[data-qa='continue-button']")

    # Logged In Verification Locator
    LOGGED_IN_INDICATOR: Locator = (By.XPATH, "//header//a[contains(., 'Logged in as')]")

    def __init__(self, driver: WebDriver, timeout: Optional[int] = None) -> None:
        super().__init__(driver, timeout)

    def is_login_page_displayed(self) -> bool:
        """Verifies if login inputs are displayed."""
        return self.is_element_displayed(self.LOGIN_EMAIL_INPUT, timeout=5)

    def login(self, email: str, password: str) -> LoginPage:
        """Submits existing credentials into the login form."""
        logger.info("LOGIN: Entering email '%s'", email)
        self.type_text(self.LOGIN_EMAIL_INPUT, email)
        logger.info("LOGIN: Entering password")
        self.type_text(self.LOGIN_PASSWORD_INPUT, password, is_sensitive=True)
        logger.info("LOGIN: Clicking login submit button")
        self.click(self.LOGIN_SUBMIT_BTN)
        self.dismiss_common_overlays()
        return self

    def is_login_failed(self) -> bool:
        """Checks if login failed with invalid credentials error message."""
        return self.is_element_displayed(self.LOGIN_ERROR_MSG, timeout=3)

    def get_login_error_message(self) -> str:
        """Retrieves text of the login error message."""
        if self.is_login_failed():
            return self.get_text(self.LOGIN_ERROR_MSG)
        return ""

    def register_user(self, data: Dict[str, Any]) -> LoginPage:
        """Executes the complete user registration flow using data row."""
        first_name = data.get("FirstName", "Test")
        last_name = data.get("LastName", "User")
        full_name = f"{first_name} {last_name}".strip()
        email = data.get("Email", "")
        password = data.get("Password", "Password123!")

        logger.info("REGISTRATION: Initiating signup for '%s' (%s)", full_name, email)
        self.type_text(self.SIGNUP_NAME_INPUT, full_name)
        self.type_text(self.SIGNUP_EMAIL_INPUT, email)
        self.click(self.SIGNUP_SUBMIT_BTN)

        # Check if email is already registered on signup attempt
        if self.is_element_displayed(self.SIGNUP_ERROR_MSG, timeout=3):
            logger.warning("Signup indicates account already exists: %s", self.get_text(self.SIGNUP_ERROR_MSG))
            return self

        logger.info("REGISTRATION: Filling profile and address information")
        if self.is_element_displayed(self.GENDER_MALE_RADIO, timeout=5):
            self.click(self.GENDER_MALE_RADIO)

        self.type_text(self.REG_PASSWORD_INPUT, password, is_sensitive=True)

        # Optional date of birth selection
        try:
            if self.is_element_present(self.REG_DAYS_SELECT, timeout=2):
                Select(self.wait_for_visible(self.REG_DAYS_SELECT)).select_by_value("15")
                Select(self.wait_for_visible(self.REG_MONTHS_SELECT)).select_by_value("6")
                Select(self.wait_for_visible(self.REG_YEARS_SELECT)).select_by_value("1995")
        except Exception as e:
            logger.debug("Optional DOB selection skipped: %s", e)

        self.type_text(self.REG_FIRST_NAME_INPUT, first_name)
        self.type_text(self.REG_LAST_NAME_INPUT, last_name)
        self.type_text(self.REG_ADDRESS_INPUT, data.get("Address", "123 Test Avenue"))

        try:
            if self.is_element_present(self.REG_COUNTRY_SELECT, timeout=2):
                country = data.get("Country", "United States")
                Select(self.wait_for_visible(self.REG_COUNTRY_SELECT)).select_by_visible_text(country)
        except Exception:
            pass

        self.type_text(self.REG_STATE_INPUT, data.get("State", "California"))
        self.type_text(self.REG_CITY_INPUT, data.get("City", "Los Angeles"))
        self.type_text(self.REG_ZIPCODE_INPUT, str(data.get("Zipcode", "90001")))
        self.type_text(self.REG_MOBILE_INPUT, str(data.get("MobileNumber", "1234567890")))

        logger.info("REGISTRATION: Submitting Create Account form")
        self.scroll_to_element(self.REG_CREATE_ACCOUNT_BTN)
        self.click(self.REG_CREATE_ACCOUNT_BTN)

        # Wait for "ACCOUNT CREATED!" banner and click Continue
        self.wait_for_visible(self.ACCOUNT_CREATED_HEADING, timeout=10)
        logger.info("REGISTRATION: Account successfully created. Clicking Continue.")
        self.click(self.CONTINUE_BTN)
        self.dismiss_common_overlays()
        return self

    def login_or_register(self, data: Dict[str, Any]) -> LoginPage:
        """Attempts login; if account doesn't exist or credentials fail, auto-registers."""
        email = data.get("Email", "")
        password = data.get("Password", "")

        self.login(email, password)

        # If login was not successful and error is visible, fallback to auto-registration
        if self.is_login_failed() or (not self.is_logged_in() and self.is_login_page_displayed()):
            logger.info("Existing login failed or account absent. Auto-registering user using test data...")
            self.register_user(data)

        return self

    def is_logged_in(self) -> bool:
        """Checks if logged-in indicator is visible."""
        return self.is_element_displayed(self.LOGGED_IN_INDICATOR, timeout=7)

    def assert_logged_in(self, expected_name: Optional[str] = None) -> LoginPage:
        """Asserts that the user session is authenticated.

        Optionally asserts the user name displayed in the header.
        """
        assert self.is_logged_in(), (
            f"Authentication failed: 'Logged in as' header indicator is not visible on page {self.get_current_url()}"
        )
        indicator_text = self.get_text(self.LOGGED_IN_INDICATOR)
        logger.info("AUTHENTICATION SUCCESS: %s", indicator_text)

        if expected_name:
            # Check either first name or full name is part of indicator text
            first_name = expected_name.split()[0] if expected_name else ""
            assert first_name.lower() in indicator_text.lower(), (
                f"Expected user '{expected_name}' not found in authentication header '{indicator_text}'"
            )
        return self
