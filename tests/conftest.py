"""Pytest configuration and shared fixtures for SeleniumHub Pro.

Implements browser factory, centralized configuration fixtures, failure screenshot
hooks, and pytest-html custom report enrichments.
"""

from __future__ import annotations

import datetime
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
    SCRIPT_TIMEOUT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    get_config_summary,
)
from utilities.data_loader import load_test_data
from utilities.logger import get_logger
from utilities.report_helper import get_failure_screenshot_path, get_run_timestamp

logger = get_logger(__name__)


# ==============================================================================
# PYTEST CLI OPTIONS & DYNAMIC PARAMETERIZATION
# ==============================================================================
def pytest_addoption(parser: pytest.Parser) -> None:
    """Registers command-line options for runtime overrides."""
    parser.addoption(
        "--browser",
        action="store",
        default=None,
        help="Browser selection: 'chrome' or 'firefox' (overrides config.BROWSER)",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=None,
        help="Run browser in headless mode (overrides config.HEADLESS)",
    )
    parser.addoption(
        "--data-source",
        action="store",
        default=None,
        help="Test data source selection: 'excel' or 'json' (overrides config.DATA_SOURCE)",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Dynamically parameterizes 'test_case' fixture based on --data-source CLI or config."""
    if "test_case" in metafunc.fixturenames:
        cli_source = metafunc.config.getoption("--data-source")
        records = load_test_data(source=cli_source)
        from utilities.data_loader import get_test_ids
        ids = get_test_ids(records)
        metafunc.parametrize("test_case", records, ids=ids)



# ==============================================================================
# FIXTURES
# ==============================================================================
@pytest.fixture(scope="session")
def framework_config(request: pytest.FixtureRequest) -> Dict[str, Any]:
    """Provides the active framework configuration parameters."""
    cfg = get_config_summary()
    cli_browser = request.config.getoption("--browser")
    if cli_browser:
        cfg["Browser"] = cli_browser.title()
    cli_data_source = request.config.getoption("--data-source")
    if cli_data_source:
        cfg["Data Source"] = cli_data_source.upper()
    return cfg


@pytest.fixture(scope="session")
def test_data(request: pytest.FixtureRequest) -> list[Dict[str, Any]]:
    """Loads all test data rows based on CLI option or config."""
    cli_source = request.config.getoption("--data-source")
    return load_test_data(source=cli_source)


@pytest.fixture(scope="function")
def driver(request: pytest.FixtureRequest) -> Generator[WebDriver, None, None]:
    """WebDriver factory fixture.

    Instantiates and configures the target browser with WebDriver Manager,
    maximizes window, configures timeouts, yields to the test, and ensures clean
    teardown even on uncaught exceptions.
    """
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
        ff_options.set_preference("dom.webnotifications.enabled", False)
        service = FirefoxService(GeckoDriverManager().install())
        web_driver = webdriver.Firefox(service=service, options=ff_options)

    else:  # Default to Chrome
        ch_options = ChromeOptions()
        if is_headless:
            ch_options.add_argument("--headless=new")
        ch_options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
        ch_options.add_argument("--start-maximized")
        ch_options.add_argument("--disable-search-engine-choice-screen")
        ch_options.add_argument("--disable-popup-blocking")
        ch_options.add_argument("--disable-notifications")
        ch_options.add_argument("--disable-infobars")
        ch_options.add_argument("--disable-dev-shm-usage")
        ch_options.add_argument("--no-sandbox")
        ch_options.add_argument("--ignore-certificate-errors")
        # Experimental flags for clean execution
        ch_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        ch_options.add_experimental_option("useAutomationExtension", False)
        ch_options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
            },
        )

        service = ChromeService(ChromeDriverManager().install())
        web_driver = webdriver.Chrome(service=service, options=ch_options)

    # Configure driver timeouts
    web_driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    web_driver.set_script_timeout(SCRIPT_TIMEOUT)
    web_driver.implicitly_wait(0)  # Rely exclusively on explicit waits (Requirement 1)

    if not is_headless:
        web_driver.maximize_window()

    # Attach driver to test node for failure screenshot hook access
    request.node.driver = web_driver

    logger.info("WebDriver successfully initialized and window sized to %dx%d", WINDOW_WIDTH, WINDOW_HEIGHT)
    yield web_driver

    # Teardown
    logger.info("Quitting WebDriver instance for test node: %s", request.node.name)
    try:
        web_driver.quit()
    except Exception as e:
        logger.error("Error encountered during WebDriver quit: %s", e)


# Alias fixture for flexibility
@pytest.fixture(scope="function")
def browser(driver: WebDriver) -> WebDriver:
    """Alias for driver fixture."""
    return driver


SESSION_TEST_RESULTS: List[Dict[str, Any]] = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator[None, Any, None]:
    """Captures automatic failure screenshot, records test result metadata, and attaches to report."""
    outcome = yield
    report: pytest.TestReport = outcome.get_result()

    if report.when == "call":
        # Extract parameterized test case if present
        params = getattr(item, "callspec", None)
        test_case_dict = params.params.get("test_case", {}) if params else {}

        test_info = {
            "nodeid": item.nodeid,
            "name": item.name,
            "test_id": test_case_dict.get("TestID", item.name),
            "product": test_case_dict.get("Product", "N/A"),
            "user": test_case_dict.get("Email", "N/A"),
            "quantity": test_case_dict.get("UpdatedQuantity", 1),
            "unit_price": float(test_case_dict.get("ExpectedUnitPrice", 0.0) or 0.0),
            "total_price": float(test_case_dict.get("ExpectedUnitPrice", 0.0) or 0.0) * int(test_case_dict.get("UpdatedQuantity", 1) or 1),
            "status": "PASSED" if report.passed else ("SKIPPED" if report.skipped else "FAILED"),
            "duration": f"{report.duration:.2f}s",
            "error": str(report.longrepr) if report.failed else "",
        }
        SESSION_TEST_RESULTS.append(test_info)

        if report.failed:
            web_driver: Optional[WebDriver] = getattr(item, "driver", None)
            if web_driver is not None:
                try:
                    failure_path = get_failure_screenshot_path(item.nodeid)
                    web_driver.save_screenshot(str(failure_path))
                    logger.error("AUTOMATED FAILURE SCREENSHOT SAVED: %s", failure_path)

                    try:
                        import importlib
                        pytest_html = importlib.import_module("pytest_html")
                        extras = getattr(report, "extras", [])
                        extras.append(pytest_html.extras.image(str(failure_path)))
                        extras.append(pytest_html.extras.html(f"<div><strong>Failure Screenshot:</strong> {failure_path.name}</div>"))
                        report.extras = extras
                    except Exception as extra_err:
                        logger.debug("Failed attaching screenshot to pytest-html extras: %s", extra_err)

                except Exception as ss_err:
                    logger.error("Failed to capture automated failure screenshot: %s", ss_err)


def pytest_html_report_title(report: Any) -> None:
    """Customizes the HTML report header title."""
    report.title = "SeleniumHub Pro: Enterprise Test Execution Report"


def pytest_configure(config: pytest.Config) -> None:
    """Enriches pytest-html report environment metadata."""
    metadata = getattr(config, "_metadata", None)
    if metadata is not None:
        metadata["Project Title"] = "SeleniumHub Pro E-Commerce Automation"
        metadata["Application Under Test"] = "https://ecommerce-storefront.demo"
        metadata["Browser"] = BROWSER.title()
        metadata["Headless Mode"] = str(HEADLESS)
        metadata["Data Source Strategy"] = DATA_SOURCE.upper()
        metadata["Explicit Wait"] = f"{EXPLICIT_WAIT}s"
        metadata["Execution Session"] = get_run_timestamp()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Handles end-of-run tasks: generates HTML, PDF reports, output.pdf, and pure output-only file."""
    import shutil
    from utilities.report_helper import get_html_report_path, get_run_timestamp, get_screenshot_dir
    from config.config import REPORTS_DIR, LOG_FILE_PATH
    from utilities.pdf_report_generator import PDFReportGenerator, sanitize_text

    run_time = get_run_timestamp()
    timestamped_report_path = get_html_report_path()
    latest_report = REPORTS_DIR / "latest_execution_report.html"

    # 1. Clean HTML report of any demo AUT mentions
    if latest_report.exists():
        try:
            with open(latest_report, "r", encoding="utf-8", errors="ignore") as hf:
                html_data = hf.read()
            clean_html = sanitize_text(html_data)
            with open(latest_report, "w", encoding="utf-8") as hf:
                hf.write(clean_html)
            with open(timestamped_report_path, "w", encoding="utf-8") as hf:
                hf.write(clean_html)
            logger.info("Sanitized HTML report saved at: %s and %s", latest_report, timestamped_report_path)
        except Exception as e:
            logger.debug("Could not process HTML report: %s", e)

    cli_source = session.config.getoption("--data-source")
    effective_data_source = (cli_source or DATA_SOURCE).upper()
    cli_browser = session.config.getoption("--browser")
    effective_browser = (cli_browser or BROWSER).title()
    cli_headless = session.config.getoption("--headless")
    effective_headless = cli_headless if cli_headless is not None else HEADLESS

    # 2. Prepare Metrics
    summary_metrics = {
        "total_tests": len(SESSION_TEST_RESULTS),
        "passed_tests": sum(1 for t in SESSION_TEST_RESULTS if t["status"] == "PASSED"),
        "failed_tests": sum(1 for t in SESSION_TEST_RESULTS if t["status"] == "FAILED"),
        "base_url": "https://ecommerce-storefront.demo",
        "browser": effective_browser,
        "headless": effective_headless,
        "data_source": effective_data_source,
        "timestamp": run_time,
        "duration": "N/A",
    }

    # Gather screenshots from the active run directory
    screenshot_dir = get_screenshot_dir()
    screenshots_list = sorted(list(screenshot_dir.glob("*.png"))) if screenshot_dir.exists() else []

    # 3. Build Pure Output-Only text (with zero demo AUT mentions)
    output_only_latest = REPORTS_DIR / "test_output_only.txt"
    output_only_dated = REPORTS_DIR / f"output_only_{run_time}.txt"
    root_output_txt = Path("test_output_only.txt")

    output_lines = [
        "=" * 80,
        "SELENIUMHUB PRO - PURE TEST EXECUTION OUTPUT",
        "=" * 80,
        f"Execution Timestamp : {run_time}",
        f"Target AUT URL      : https://ecommerce-storefront.demo",
        f"Browser Engine      : {effective_browser}",
        f"Headless Mode       : {effective_headless}",
        f"Data Source         : {effective_data_source}",
        f"Exit Status Code    : {exitstatus}",
        "=" * 80,
        "TEST RESULTS MATRIX:",
        "-" * 80,
    ]

    for tc in SESSION_TEST_RESULTS:
        output_lines.append(
            f"[{tc['status']:<6}] {tc['test_id']:<15} | Product: {tc['product']:<20} | "
            f"Qty: {tc['quantity']:<2} | Unit: Rs. {tc['unit_price']:<6.2f} | "
            f"Total: Rs. {tc['total_price']:<8.2f} | Duration: {tc['duration']}"
        )
        if tc["error"]:
            output_lines.append(f"       ERROR: {tc['error'].strip().splitlines()[-1] if tc['error'].strip() else ''}")

    output_lines.extend([
        "-" * 80,
        f"TOTAL: {summary_metrics['total_tests']} | PASSED: {summary_metrics['passed_tests']} | FAILED: {summary_metrics['failed_tests']}",
        "=" * 80,
        "",
        "=" * 80,
        "DETAILED EXECUTION LOG STREAM:",
        "=" * 80,
    ])

    # Append recent execution logs if available
    if LOG_FILE_PATH.exists():
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as lf:
                recent_logs = lf.readlines()[-200:]
                output_lines.extend([line.rstrip() for line in recent_logs])
        except Exception:
            pass

    pure_output_text = sanitize_text("\n".join(output_lines))
    try:
        with open(output_only_latest, "w", encoding="utf-8") as out_f:
            out_f.write(pure_output_text)
        with open(output_only_dated, "w", encoding="utf-8") as out_dated_f:
            out_dated_f.write(pure_output_text)
        with open(root_output_txt, "w", encoding="utf-8") as out_root_f:
            out_root_f.write(pure_output_text)
        logger.info("Output-only file generated at: %s and %s", output_only_latest, output_only_dated)
    except Exception as out_err:
        logger.error("Failed to generate output-only file: %s", out_err)

    # 4. Generate Standard PDF Execution Report
    pdf_latest_path = REPORTS_DIR / "latest_execution_report.pdf"
    pdf_dated_path = REPORTS_DIR / f"report_{run_time}.pdf"

    try:
        generator = PDFReportGenerator(pdf_latest_path)
        generator.generate_report(summary_metrics, SESSION_TEST_RESULTS, screenshots_list)
        shutil.copy2(pdf_latest_path, pdf_dated_path)
        logger.info("PDF Report saved at: %s and %s", pdf_latest_path, pdf_dated_path)
    except Exception as pdf_err:
        logger.error("Failed to generate PDF execution report: %s", pdf_err)

    # 5. Generate dedicated output.pdf (Requirement: "make a output.pdf file there also no automation exercise should mention")
    output_pdf_path = REPORTS_DIR / "output.pdf"
    root_output_pdf = Path("output.pdf")

    try:
        gen_output = PDFReportGenerator(output_pdf_path)
        gen_output.generate_report(
            summary_metrics,
            SESSION_TEST_RESULTS,
            screenshots=screenshots_list,
            execution_logs=pure_output_text,
            is_output_pdf=True,
        )
        shutil.copy2(output_pdf_path, root_output_pdf)
        logger.info("Dedicated output.pdf generated at: %s and %s", output_pdf_path, root_output_pdf)
    except Exception as out_pdf_err:
        logger.error("Failed to generate output.pdf: %s", out_pdf_err)

    # 6. Standard summary output
    summary_path = REPORTS_DIR / f"summary_{run_time}.txt"
    summary_lines = [
        "=" * 70,
        "SELENIUMHUB PRO - TEST EXECUTION SUMMARY",
        "=" * 70,
        f"Execution Timestamp : {run_time}",
        f"Application URL     : https://ecommerce-storefront.demo",
        f"Browser Engine      : {effective_browser}",
        f"Headless Mode       : {effective_headless}",
        f"Data Source Used    : {effective_data_source}",
        f"Exit Status Code    : {exitstatus}",
        f"HTML Report (Latest): {latest_report}",
        f"PDF Report (Latest) : {pdf_latest_path}",
        f"Output PDF (Latest) : {output_pdf_path}",
        f"Output Only (Latest): {output_only_latest}",
        "=" * 70,
    ]
    summary_text = sanitize_text("\n".join(summary_lines))
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_text)
        logger.info("\n" + summary_text)
    except Exception as e:
        logger.debug("Failed writing summary file: %s", e)


