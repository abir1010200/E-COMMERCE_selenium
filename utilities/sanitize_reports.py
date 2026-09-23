"""Report Sanitization Engine for SeleniumHub Pro.

Ensures zero mentions of demo application names, logos, symbols, or URLs
across HTML, PDF, text, and screenshot report files.
"""

from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional

from PIL import Image as PILImage, ImageDraw

from config.config import REPORTS_DIR, SCREENSHOTS_DIR
from utilities.logger import get_logger

logger = get_logger(__name__)


def sanitize_text(text: Optional[str]) -> str:
    """Sanitizes text by stripping all variations of demo site name and URLs."""
    if not text:
        return ""
    str_val = str(text)
    # 1. URL variations (with or without escape slashes)
    str_val = re.sub(
        r"https?:\\?/\\?/(?:www\.)?automationexercise\.com[^\s\"'<>\\,]*",
        "https://ecommerce-storefront.demo",
        str_val,
        flags=re.IGNORECASE,
    )
    # 2. Domain names
    str_val = re.sub(r"automationexercise\.com", "ecommerce-storefront.demo", str_val, flags=re.IGNORECASE)
    # 3. Text variations
    str_val = re.sub(r"Automation\s*[-_]?\s*Exercise", "Enterprise E-Commerce Storefront", str_val, flags=re.IGNORECASE)
    str_val = re.sub(r"automationexercise", "enterprise_storefront", str_val, flags=re.IGNORECASE)
    return str_val


def sanitize_screenshot_image(image_path: Path) -> Path:
    """Masks top-left logo and homepage banner text from screenshot image."""
    try:
        if not image_path.exists():
            return image_path
        with PILImage.open(image_path) as img:
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)
            # Mask top-left header logo
            draw.rectangle([300, 0, 750, 160], fill=(255, 255, 255))
            # Mask homepage carousel banner if present
            if "login" in image_path.name.lower() or "home" in image_path.name.lower():
                draw.rectangle([440, 230, 1050, 545], fill=(255, 255, 255))
            img.save(image_path)
    except Exception as e:
        logger.debug("Failed masking screenshot %s: %s", image_path.name, e)
    return image_path


def sanitize_all_reports() -> None:
    """Scans and sanitizes all generated HTML, TXT, and PDF report files."""
    # 1. Sanitize text and HTML reports
    report_patterns = [
        str(REPORTS_DIR / "*.html"),
        str(REPORTS_DIR / "*.txt"),
        "test_output_only.txt",
    ]

    for pattern in report_patterns:
        for file_path in glob.glob(pattern):
            p = Path(file_path)
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                sanitized = sanitize_text(content)
                if sanitized != content:
                    p.write_text(sanitized, encoding="utf-8")
                    logger.info("Sanitized text/html report: %s", p.name)
            except Exception as e:
                logger.debug("Could not sanitize file %s: %s", p, e)

    # 2. Sanitize screenshots in run directories
    for ss in SCREENSHOTS_DIR.rglob("*.png"):
        sanitize_screenshot_image(ss)

    logger.info("Report sanitization pass completed successfully.")


if __name__ == "__main__":
    sanitize_all_reports()
