"""Unified test data loader for SeleniumHub Pro.

Acts as a single entry point for reading test datasets.
Switches between Excel (.xlsx) and JSON based on configuration or environment
variables, normalizing records into a consistent dictionary format.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from config.config import DATA_SOURCE, EXCEL_DATA_PATH, JSON_DATA_PATH
from utilities.excel_reader import read_excel_data
from utilities.json_reader import read_json_data
from utilities.logger import get_logger

logger = get_logger(__name__)


def load_test_data(source: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads test data rows from either Excel or JSON based on source flag.

    Args:
        source: Optional override ("excel" or "json"). If None, uses config.DATA_SOURCE
                or environment variable DATA_SOURCE.

    Returns:
        List of dictionaries containing row-level test data.
    """
    selected_source = (source or os.getenv("DATA_SOURCE", DATA_SOURCE)).strip().lower()

    logger.info("Loading test data using source strategy: '%s'", selected_source)

    if selected_source == "excel":
        if not EXCEL_DATA_PATH.exists():
            logger.warning("Excel data file missing at %s, generating it from JSON...", EXCEL_DATA_PATH)
            from utilities.create_excel_data import generate_excel_data
            generate_excel_data()

        records = read_excel_data(EXCEL_DATA_PATH)
    elif selected_source == "json":
        records = read_json_data(JSON_DATA_PATH)
    else:
        raise ValueError(f"Unsupported DATA_SOURCE: '{selected_source}'. Must be 'excel' or 'json'.")

    # Validate essential fields in loaded records
    validated_records = []
    required_keys = {"TestID", "Product", "Email", "Password"}

    for idx, row in enumerate(records, start=1):
        missing = required_keys - set(row.keys())
        if missing:
            logger.error("Record #%d missing mandatory keys: %s. Row data: %s", idx, missing, row)
            continue

        # Convert types where appropriate
        normalized = dict(row)
        if "InitialQuantity" in normalized and normalized["InitialQuantity"] is not None:
            try:
                normalized["InitialQuantity"] = int(normalized["InitialQuantity"])
            except (ValueError, TypeError):
                normalized["InitialQuantity"] = 1

        if "UpdatedQuantity" in normalized and normalized["UpdatedQuantity"] is not None:
            try:
                normalized["UpdatedQuantity"] = int(normalized["UpdatedQuantity"])
            except (ValueError, TypeError):
                normalized["UpdatedQuantity"] = 1

        if "ExpectedUnitPrice" in normalized and normalized["ExpectedUnitPrice"] is not None:
            try:
                normalized["ExpectedUnitPrice"] = float(normalized["ExpectedUnitPrice"])
            except (ValueError, TypeError):
                pass

        validated_records.append(normalized)

    logger.info("Total validated test cases available: %d", len(validated_records))
    return validated_records


def get_test_ids(records: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Generates readable test IDs for pytest parameterization markers."""
    if records is None:
        records = load_test_data()

    ids: List[str] = []
    for row in records:
        tid = str(row.get("TestID", "TC"))
        product = str(row.get("Product", "Item")).replace(" ", "_")
        ids.append(f"{tid}_{product}")
    return ids


def get_test_case_by_id(test_id: str, records: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Returns a specific test case dict matching test_id."""
    if records is None:
        records = load_test_data()
    for row in records:
        if str(row.get("TestID")).strip().lower() == test_id.strip().lower():
            return row
    return None
