"""Reporting and screenshot path management helper.

Coordinates timestamped execution directories for screenshots and HTML reports.
"""

from __future__ import annotations

import datetime
import os
import re
from pathlib import Path
from typing import Optional

from config.config import REPORTS_DIR, SCREENSHOTS_DIR

# Unique run timestamp shared across the test session
RUN_TIMESTAMP: str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_SCREENSHOTS_DIR: Path = SCREENSHOTS_DIR / RUN_TIMESTAMP
RUN_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitizes strings for safe cross-platform file naming."""
    return re.sub(r"[^\w\-_.]", "_", name.strip())


def get_run_timestamp() -> str:
    """Returns the ISO-style timestamp created at test session initialization."""
    return RUN_TIMESTAMP


def get_screenshot_dir() -> Path:
    """Returns the timestamped screenshot directory for the active run."""
    RUN_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return RUN_SCREENSHOTS_DIR


def get_step_screenshot_path(step_name: str, test_id: Optional[str] = None) -> Path:
    """Generates a clean, absolute filepath for a step-specific screenshot."""
    clean_step = sanitize_filename(step_name)
    prefix = f"{sanitize_filename(test_id)}_" if test_id else ""
    filename = f"{prefix}{clean_step}.png"
    return RUN_SCREENSHOTS_DIR / filename


def get_failure_screenshot_path(test_name: str) -> Path:
    """Generates a filepath for an automated failure screenshot."""
    clean_name = sanitize_filename(test_name)
    now_str = datetime.datetime.now().strftime("%H-%M-%S")
    return RUN_SCREENSHOTS_DIR / f"FAILURE_{clean_name}_{now_str}.png"


def get_html_report_path() -> Path:
    """Returns the default timestamped path for the pytest-html report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / f"report_{RUN_TIMESTAMP}.html"
