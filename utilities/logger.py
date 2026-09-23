"""Enterprise logging utility for SeleniumHub Pro.

Provides console and rotating file logging with automatic masking of sensitive
data (e.g. passwords, authentication tokens).
"""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from typing import Any

from config.config import (
    LOG_BACKUP_COUNT,
    LOG_FILE_PATH,
    LOG_LEVEL,
    LOG_MAX_BYTES,
    LOGS_DIR,
)


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive information in log records."""

    PATTERNS = [
        (re.compile(r"(password['\"]?\s*[:=]\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE), r"\1********\3"),
        (re.compile(r"(token['\"]?\s*[:=]\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE), r"\1********\3"),
        (re.compile(r"(secret['\"]?\s*[:=]\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE), r"\1********\3"),
        (re.compile(r"(passwd['\"]?\s*[:=]\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE), r"\1********\3"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in self.PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        if record.args:
            if isinstance(record.args, dict):
                sanitized_args = {}
                for k, v in record.args.items():
                    if any(s in k.lower() for s in ("pass", "token", "secret")):
                        sanitized_args[k] = "********"
                    else:
                        sanitized_args[k] = v
                record.args = sanitized_args
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    "********" if isinstance(a, str) and len(a) > 5 and any(s in a.lower() for s in ("pass", "secret")) else a
                    for a in record.args
                )
        return True


def setup_logger(name: str = "SeleniumHubPro") -> logging.Logger:
    """Configures and returns a thread-safe singleton-style logger instance."""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if setup is called multiple times
    if logger.hasHandlers():
        return logger

    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(numeric_level)

    # Standard format: timestamp | level | logger | file:line | message
    log_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] (%(name)s - %(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sensitive_filter = SensitiveDataFilter()

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(log_format)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=str(LOG_FILE_PATH),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(log_format)
    file_handler.addFilter(sensitive_filter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_logger(name: str = "SeleniumHubPro") -> logging.Logger:
    """Convenience getter for framework loggers."""
    return setup_logger(name)


def mask_sensitive(text: Any) -> str:
    """Utility function to mask sensitive strings explicitly in messages."""
    if not text:
        return ""
    str_val = str(text)
    if len(str_val) <= 2:
        return "**"
    return str_val[0] + ("*" * (len(str_val) - 2)) + str_val[-1]
