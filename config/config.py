"""Centralized configuration module for SeleniumHub Pro.

Supports environment overrides for CI/CD runs and runtime flexibility.
Handles application targets, browser configurations, explicit waits,
and test-data source selection without requiring any code changes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


# ==============================================================================
# PROJECT ROOT & PATH DEFINITIONS
# ==============================================================================
BASE_DIR: Path = Path(__file__).resolve().parent.parent

TEST_DATA_DIR: Path = BASE_DIR / "test_data"
EXCEL_DATA_PATH: Path = TEST_DATA_DIR / "test_data.xlsx"
JSON_DATA_PATH: Path = TEST_DATA_DIR / "test_data.json"

REPORTS_DIR: Path = BASE_DIR / "reports"
SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots"
LOGS_DIR: Path = BASE_DIR / "logs"

# Ensure runtime directories exist
for directory in (REPORTS_DIR, SCREENSHOTS_DIR, LOGS_DIR, TEST_DATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# APPLICATION UNDER TEST (AUT) CONFIGURATION
# ==============================================================================
AUT_REGISTRY: Dict[str, Dict[str, str]] = {
    "automationexercise": {
        "name": "Automation Exercise",
        "base_url": "https://automationexercise.com",
        "description": "Primary e-commerce demo application for end-to-end automation",
    },
    "tutorialsninja": {
        "name": "TutorialsNinja Demo",
        "base_url": "https://tutorialsninja.com/demo",
        "description": "Alternative OpenCart-based e-commerce storefront",
    },
    "opencart": {
        "name": "OpenCart Official Demo",
        "base_url": "https://demo.opencart.com",
        "description": "Alternative OpenCart official demo storefront",
    },
}

ACTIVE_AUT: str = os.getenv("AUT_NAME", "automationexercise").strip().lower()
if ACTIVE_AUT not in AUT_REGISTRY:
    ACTIVE_AUT = "automationexercise"

AUT_DETAILS: Dict[str, str] = AUT_REGISTRY[ACTIVE_AUT]
BASE_URL: str = os.getenv("BASE_URL", AUT_DETAILS["base_url"]).rstrip("/")


# ==============================================================================
# BROWSER & DRIVER CONFIGURATION
# ==============================================================================
BROWSER: str = os.getenv("BROWSER", "chrome").strip().lower()
HEADLESS: bool = os.getenv("HEADLESS", "false").strip().lower() in ("true", "1", "yes")

WINDOW_WIDTH: int = int(os.getenv("WINDOW_WIDTH", "1920"))
WINDOW_HEIGHT: int = int(os.getenv("WINDOW_HEIGHT", "1080"))

# Timeouts in seconds
EXPLICIT_WAIT: int = int(os.getenv("EXPLICIT_WAIT", "15"))
PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
SCRIPT_TIMEOUT: int = int(os.getenv("SCRIPT_TIMEOUT", "20"))
POLL_FREQUENCY: float = float(os.getenv("POLL_FREQUENCY", "0.5"))


# ==============================================================================
# DATA SOURCE CONFIGURATION
# ==============================================================================
# Select "excel" or "json"
DATA_SOURCE: str = os.getenv("DATA_SOURCE", "excel").strip().lower()
if DATA_SOURCE not in ("excel", "json"):
    DATA_SOURCE = "excel"


# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE_PATH: Path = LOGS_DIR / "test_execution.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB per log file
LOG_BACKUP_COUNT: int = 5


# ==============================================================================
# HELPER / SUMMARY UTILITY
# ==============================================================================
def get_config_summary() -> Dict[str, Any]:
    """Returns a dictionary summary of active framework configurations for reports."""
    return {
        "Active AUT": AUT_DETAILS["name"],
        "Base URL": BASE_URL,
        "Browser": BROWSER.title(),
        "Headless": "Enabled" if HEADLESS else "Disabled",
        "Data Source": DATA_SOURCE.upper(),
        "Explicit Wait": f"{EXPLICIT_WAIT}s",
        "Page Load Timeout": f"{PAGE_LOAD_TIMEOUT}s",
        "Reports Directory": str(REPORTS_DIR),
        "Screenshots Directory": str(SCREENSHOTS_DIR),
        "Logs Directory": str(LOGS_DIR),
    }
