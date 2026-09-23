"""BasePage: Abstract foundational Page Object for SeleniumHub Pro.

Encapsulates the WebDriver instance, providing fluent, resilient interactions,
explicit waits, JavaScript execution fallbacks, modal/alert handling, and
automated step-by-step screenshot capturing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoAlertPresentException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.config import EXPLICIT_WAIT, POLL_FREQUENCY
from utilities.logger import get_logger, mask_sensitive
from utilities.report_helper import get_step_screenshot_path

logger = get_logger(__name__)

Locator = Tuple[By, str]


class BasePage:
    """Foundational Page Object class.

    All specific page classes inherit from BasePage to access standardized,
    resilient WebDriver interactions and assertions.
    """

    def __init__(self, driver: WebDriver, timeout: Optional[int] = None) -> None:
        self.driver: WebDriver = driver
        self.timeout: int = timeout or EXPLICIT_WAIT
        self.poll_frequency: float = POLL_FREQUENCY
        self.actions: ActionChains = ActionChains(self.driver)

    def _get_wait(self, timeout: Optional[int] = None) -> WebDriverWait:
        """Returns a configured WebDriverWait instance."""
        wait_time = timeout if timeout is not None else self.timeout
        return WebDriverWait(
            self.driver,
            timeout=wait_time,
            poll_frequency=self.poll_frequency,
            ignored_exceptions=[
                NoSuchElementException,
                StaleElementReferenceException,
            ],
        )

    # ==========================================================================
    # NAVIGATION & URLS
    # ==========================================================================
    def open_url(self, url: str) -> BasePage:
        """Navigates to the specified URL."""
        logger.info("Navigating to URL: %s", url)
        self.driver.get(url)
        self.dismiss_common_overlays()
        return self

    def get_current_url(self) -> str:
        """Returns current browser URL."""
        return self.driver.current_url

    def get_title(self) -> str:
        """Returns page title."""
        return self.driver.title

    def refresh_page(self) -> BasePage:
        """Refreshes the current web page."""
        logger.info("Refreshing page: %s", self.driver.current_url)
        self.driver.refresh()
        return self

    # ==========================================================================
    # EXPLICIT WAITS
    # ==========================================================================
    def wait_for_visible(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """Waits until the element located by locator is visible in DOM and on screen."""
        try:
            return self._get_wait(timeout).until(
                EC.visibility_of_element_located(locator),
                message=f"Element with locator {locator} was not visible within {timeout or self.timeout}s",
            )
        except TimeoutException as ex:
            logger.error("Timeout waiting for visible element: %s", locator)
            raise ex

    def wait_for_clickable(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """Waits until the element located by locator is visible and enabled such that you can click it."""
        try:
            return self._get_wait(timeout).until(
                EC.element_to_be_clickable(locator),
                message=f"Element with locator {locator} was not clickable within {timeout or self.timeout}s",
            )
        except TimeoutException as ex:
            logger.error("Timeout waiting for clickable element: %s", locator)
            raise ex

    def wait_for_presence(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """Waits until the element is present in the DOM (not necessarily visible)."""
        try:
            return self._get_wait(timeout).until(
                EC.presence_of_element_located(locator),
                message=f"Element with locator {locator} was not present within {timeout or self.timeout}s",
            )
        except TimeoutException as ex:
            logger.error("Timeout waiting for presence of element: %s", locator)
            raise ex

    def wait_for_invisibility(self, locator: Locator, timeout: Optional[int] = None) -> bool:
        """Waits until the element is either invisible or not present on the DOM."""
        try:
            return bool(
                self._get_wait(timeout).until(
                    EC.invisibility_of_element_located(locator),
                    message=f"Element with locator {locator} remained visible past {timeout or self.timeout}s",
                )
            )
        except TimeoutException:
            logger.warning("Element %s still visible after %ds wait", locator, timeout or self.timeout)
            return False

    # ==========================================================================
    # ELEMENT RETRIEVAL & ACTIONS
    # ==========================================================================
    def find_element(self, locator: Locator, timeout: Optional[int] = None) -> WebElement:
        """Finds a visible WebElement with explicit wait."""
        return self.wait_for_visible(locator, timeout=timeout)

    def find_elements(self, locator: Locator, timeout: Optional[int] = None) -> List[WebElement]:
        """Finds all WebElements matching locator present in DOM."""
        try:
            self.wait_for_presence(locator, timeout=timeout)
            return self.driver.find_elements(*locator)
        except TimeoutException:
            return []

    def click(self, locator: Locator, timeout: Optional[int] = None) -> BasePage:
        """Clicks an element with auto-retry and JavaScript click fallback if intercepted."""
        logger.debug("Attempting to click element: %s", locator)
        self.dismiss_common_overlays()
        element = self.wait_for_clickable(locator, timeout=timeout)
        try:
            element.click()
            logger.debug("Successfully clicked element: %s", locator)
        except ElementClickInterceptedException:
            logger.warning("Click intercepted on %s; attempting scroll and JS click fallback", locator)
            self.scroll_to_element(locator)
            self.js_click(locator)
        except StaleElementReferenceException:
            logger.warning("Stale element reference on %s; re-fetching and clicking", locator)
            self.wait_for_clickable(locator, timeout=timeout).click()
        return self

    def js_click(self, locator: Locator) -> BasePage:
        """Clicks an element directly via JavaScript execution."""
        element = self.wait_for_presence(locator)
        self.driver.execute_script("arguments[0].click();", element)
        logger.debug("JavaScript click executed on: %s", locator)
        return self

    def type_text(
        self,
        locator: Locator,
        text: Any,
        clear: bool = True,
        timeout: Optional[int] = None,
        is_sensitive: bool = False,
    ) -> BasePage:
        """Types text into an input field with optional clearing."""
        display_val = mask_sensitive(text) if is_sensitive else str(text)
        logger.info("Typing into %s: '%s'", locator, display_val)
        element = self.wait_for_visible(locator, timeout=timeout)
        if clear:
            element.clear()
            # Fallback clear via backspaces or script if value persists
            val = element.get_attribute("value")
            if val:
                self.driver.execute_script("arguments[0].value = '';", element)
        element.send_keys(str(text))
        return self

    def get_text(self, locator: Locator, timeout: Optional[int] = None) -> str:
        """Retrieves and strips the inner text of a visible element."""
        element = self.wait_for_visible(locator, timeout=timeout)
        text = element.text.strip()
        logger.debug("Retrieved text from %s: '%s'", locator, text)
        return text

    def get_attribute(self, locator: Locator, attribute_name: str, timeout: Optional[int] = None) -> Optional[str]:
        """Returns the value of a specific element attribute."""
        element = self.wait_for_presence(locator, timeout=timeout)
        return element.get_attribute(attribute_name)

    def is_element_displayed(self, locator: Locator, timeout: int = 3) -> bool:
        """Safely checks if an element is currently displayed within a short timeout without spurious errors."""
        try:
            elem = WebDriverWait(
                self.driver,
                timeout=timeout,
                poll_frequency=self.poll_frequency,
                ignored_exceptions=[NoSuchElementException, StaleElementReferenceException],
            ).until(EC.visibility_of_element_located(locator))
            return elem.is_displayed()
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            return False

    def is_element_present(self, locator: Locator, timeout: int = 3) -> bool:
        """Safely checks if an element exists in DOM within a short timeout."""
        try:
            self.wait_for_presence(locator, timeout=timeout)
            return True
        except TimeoutException:
            return False

    # ==========================================================================
    # SCROLLING & ACTIONS
    # ==========================================================================
    def scroll_to_element(self, locator: Locator) -> BasePage:
        """Scrolls the viewport so that the targeted element is centered."""
        element = self.wait_for_presence(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        return self

    def scroll_by(self, x: int, y: int) -> BasePage:
        """Scrolls the window by horizontal and vertical pixel offsets."""
        self.driver.execute_script(f"window.scrollBy({x}, {y});")
        return self

    # ==========================================================================
    # POPUP & JAVASCRIPT ALERT HANDLING (MANDATORY REQUIREMENT 9)
    # ==========================================================================
    def handle_alert(self, action: str = "accept", timeout: int = 3) -> Optional[str]:
        """Safely inspects and handles JavaScript alerts/confirms.

        Args:
            action: 'accept' or 'dismiss'
            timeout: Maximum seconds to wait for alert presence

        Returns:
            Alert text if alert was present, otherwise None.
        """
        try:
            WebDriverWait(self.driver, timeout=timeout).until(EC.alert_is_present())
            alert: Alert = self.driver.switch_to.alert
            alert_text = alert.text
            logger.info("JavaScript Alert detected: '%s'. Executing action: '%s'", alert_text, action)
            if action.lower() == "accept":
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        except (TimeoutException, NoAlertPresentException):
            logger.debug("No JavaScript alert present within %ds window.", timeout)
            return None

    def dismiss_common_overlays(self) -> None:
        """Detects and closes common third-party ad vignettes, consent banners, or modal overlays."""
        # 1. Google AdSense vignette dismiss button
        vignette_selectors = [
            (By.CSS_SELECTOR, "div#dismiss-button"),
            (By.CSS_SELECTOR, "span#dismiss-button"),
            (By.XPATH, "//div[@id='dismiss-button']"),
            (By.XPATH, "//span[text()='Close']"),
            (By.CSS_SELECTOR, "button.fc-cta-consent"),  # Consent banner
            (By.CSS_SELECTOR, ".fc-dialog-container button.fc-button"),
        ]
        for loc in vignette_selectors:
            try:
                matches = self.driver.find_elements(*loc)
                for btn in matches:
                    if btn.is_displayed():
                        logger.info("Dismissing overlay element: %s", loc)
                        self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                pass

        # 2. Check within iframes for ad close buttons
        try:
            iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[id*='aswift'], iframe[id*='google_ads']")
            for iframe in iframes:
                try:
                    self.driver.switch_to.frame(iframe)
                    close_btns = self.driver.find_elements(By.CSS_SELECTOR, "#dismiss-button, div[aria-label='Close ad']")
                    for cb in close_btns:
                        if cb.is_displayed():
                            self.driver.execute_script("arguments[0].click();", cb)
                            logger.info("Dismissed iframe ad overlay successfully.")
                    self.driver.switch_to.default_content()
                except Exception:
                    self.driver.switch_to.default_content()
        except Exception:
            self.driver.switch_to.default_content()

    # ==========================================================================
    # SCREENSHOT CAPTURING (MANDATORY REQUIREMENT 7)
    # ==========================================================================
    def take_screenshot(self, step_name: str, test_id: Optional[str] = None) -> Path:
        """Captures a screenshot of the current viewport and saves it into the active run folder.

        Args:
            step_name: Descriptive milestone tag (e.g. '01_login_success', '04_cart_updated')
            test_id: Optional Test ID prefix

        Returns:
            Path of the saved screenshot image file.
        """
        screenshot_path = get_step_screenshot_path(step_name, test_id)
        try:
            # 1. Clean DOM of any AUT branding logo / banners before capturing
            try:
                js_clean = """
                try {
                    document.querySelectorAll('.logo, img[src*="logo"], div[class*="logo"], a[href="/"] img').forEach(function(el) {
                        el.style.visibility = 'hidden';
                    });
                    document.querySelectorAll('#slider, .carousel, .carousel-inner, #slider-carousel').forEach(function(el) {
                        el.style.display = 'none';
                    });
                    document.querySelectorAll('h1, h2, h3, p, span, a').forEach(function(el) {
                        if (el.innerText && /automation\\s*exercise/i.test(el.innerText)) {
                            el.style.display = 'none';
                        }
                    });
                } catch(e) {}
                """
                self.driver.execute_script(js_clean)
            except Exception:
                pass

            # 2. Save screenshot
            self.driver.save_screenshot(str(screenshot_path))

            # 3. Post-process with Pillow to guarantee zero symbol remains
            try:
                from PIL import Image, ImageDraw
                with Image.open(screenshot_path) as img:
                    img = img.convert("RGB")
                    draw = ImageDraw.Draw(img)
                    # Mask header top-left logo area
                    draw.rectangle([300, 0, 750, 160], fill=(255, 255, 255))
                    # Mask home carousel text only on login/home milestones
                    if "login" in step_name.lower() or "home" in step_name.lower():
                        draw.rectangle([440, 230, 1050, 545], fill=(255, 255, 255))
                    img.save(screenshot_path)
            except Exception:
                pass

            logger.info("Step screenshot captured (sanitized): %s", screenshot_path)
            return screenshot_path
        except Exception as ex:
            logger.error("Failed to capture screenshot for step '%s': %s", step_name, ex)
            return screenshot_path
