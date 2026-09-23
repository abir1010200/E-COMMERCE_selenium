"""Pytest configuration and fixtures for Selenium E-Commerce Automation.

Implements:
1. Browser setup and teardown (Chrome/Firefox)
2. Dynamic test data loading from Excel/JSON
3. Automated screenshot capture on failure
4. Pytest HTML report generation and metadata customization
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from config.config import (
    BASE_URL,
    BROWSER,
    DATA_SOURCE,
    EXPLICIT_WAIT,
    HEADLESS,
    PAGE_LOAD_TIMEOUT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from utilities.data_loader import get_test_ids, load_test_data
from utilities.logger import get_logger
from utilities.report_helper import get_failure_screenshot_path

logger = get_logger(__name__)


# ==============================================================================
# PYTEST CLI OPTIONS & DYNAMIC PARAMETERIZATION (Requirement 8)
# ==============================================================================
def pytest_addoption(parser: pytest.Parser) -> None:
    """Registers command-line options for runtime overrides."""
    parser.addoption(
        "--browser",
        action="store",
        default=None,
        help="Browser selection: 'chrome' or 'firefox' (default: config.BROWSER)",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=None,
        help="Run browser in headless mode",
    )
    parser.addoption(
        "--data-source",
        action="store",
        default=None,
        help="Test data source selection: 'excel' or 'json' (default: config.DATA_SOURCE)",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Dynamically parameterizes 'test_case' fixture from Excel or JSON test data."""
    if "test_case" in metafunc.fixturenames:
        cli_source = metafunc.config.getoption("--data-source")
        records = load_test_data(source=cli_source)
        ids = get_test_ids(records)
        metafunc.parametrize("test_case", records, ids=ids)


# ==============================================================================
# BROWSER FIXTURES (Requirement 1)
# ==============================================================================
@pytest.fixture(scope="function")
def driver(request: pytest.FixtureRequest) -> Generator[WebDriver, None, None]:
    """WebDriver factory fixture managing browser lifecycle."""
    cli_browser = request.config.getoption("--browser")
    target_browser = (cli_browser or BROWSER).strip().lower()

    cli_headless = request.config.getoption("--headless")
    is_headless = cli_headless if cli_headless is not None else HEADLESS

    logger.info("Initializing %s WebDriver (Headless: %s)", target_browser.upper(), is_headless)

    web_driver: WebDriver

    if target_browser == "firefox":
        ff_options = FirefoxOptions()
        if is_headless:
            ff_options.add_argument("--headless")
            ff_options.add_argument(f"--width={WINDOW_WIDTH}")
            ff_options.add_argument(f"--height={WINDOW_HEIGHT}")
        service = FirefoxService(GeckoDriverManager().install())
        web_driver = webdriver.Firefox(service=service, options=ff_options)
    else:
        ch_options = ChromeOptions()
        if is_headless:
            ch_options.add_argument("--headless=new")
        ch_options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
        ch_options.add_argument("--start-maximized")
        ch_options.add_argument("--disable-notifications")
        ch_options.add_argument("--disable-popup-blocking")
        ch_options.add_argument("--no-sandbox")
        ch_options.add_argument("--disable-dev-shm-usage")
        service = ChromeService(ChromeDriverManager().install())
        web_driver = webdriver.Chrome(service=service, options=ch_options)

    web_driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    if not is_headless:
        web_driver.maximize_window()

    # Store driver on node for failure screenshot hook
    request.node.driver = web_driver

    yield web_driver

    # Teardown
    try:
        web_driver.quit()
    except Exception as e:
        logger.error("Error closing WebDriver: %s", e)


@pytest.fixture(scope="function")
def browser(driver: WebDriver) -> WebDriver:
    """Convenience alias for driver fixture."""
    return driver


# ==============================================================================
# REPORTING & SCREENSHOT HOOKS (Requirements 7 & 10)
# ==============================================================================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator[None, Any, None]:
    """Captures screenshot on test failure and embeds it in the HTML report."""
    outcome = yield
    report: pytest.TestReport = outcome.get_result()

    if report.when == "call" and report.failed:
        web_driver: Optional[WebDriver] = getattr(item, "driver", None)
        if web_driver is not None:
            try:
                failure_path = get_failure_screenshot_path(item.nodeid)
                web_driver.save_screenshot(str(failure_path))
                logger.error("Failure screenshot captured: %s", failure_path)

                import pytest_html
                extras = getattr(report, "extras", [])
                extras.append(pytest_html.extras.image(str(failure_path)))
                report.extras = extras
            except Exception as err:
                logger.debug("Could not attach screenshot to report: %s", err)


def pytest_html_report_title(report: Any) -> None:
    """Sets a clean title for the HTML execution report."""
    report.title = "E-Commerce Automation Test Execution Report"


def pytest_configure(config: pytest.Config) -> None:
    """Enriches HTML report environment metadata."""
    metadata = getattr(config, "_metadata", None)
    if metadata is not None:
        metadata["Application"] = "Automation Exercise (E-Commerce)"
        metadata["Base URL"] = BASE_URL
        metadata["Browser"] = BROWSER.title()
        metadata["Data Source"] = DATA_SOURCE.upper()
