"""JSON test data reader utility.

Parses structured test data from .json files into normalized lists of dictionaries
for pytest parameterization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from utilities.logger import get_logger

logger = get_logger(__name__)


class JsonReader:
    """Reads structured test data from JSON files."""

    def __init__(self, file_path: Union[str, Path]) -> None:
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"JSON test data file not found: {self.file_path}")

    def read_data(self) -> List[Dict[str, Any]]:
        """Reads JSON data and returns list of dictionaries.

        Supports both direct arrays `[{...}, {...}]` or objects with a `test_cases` key.
        """
        logger.info("Reading JSON test data from: %s", self.file_path)
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        if isinstance(content, list):
            data_list = content
        elif isinstance(content, dict):
            # Check common wrapper keys
            for key in ("test_cases", "data", "tests", "records"):
                if key in content and isinstance(content[key], list):
                    data_list = content[key]
                    break
            else:
                data_list = [content]
        else:
            raise ValueError(f"Unexpected JSON structure in {self.file_path}: expected list or dict")

        logger.info("Successfully loaded %d records from JSON file: %s", len(data_list), self.file_path.name)
        return data_list


def read_json_data(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Convenience function to read test data from a JSON file."""
    reader = JsonReader(file_path)
    return reader.read_data()
