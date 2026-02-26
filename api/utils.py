"""Shared utilities for the Resume–Job Matching Agent API."""

import json
from pathlib import Path
from typing import Any

from core.errors import internal_error

# Project root is the parent of the /api package directory.
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_EXAMPLES_DIR: Path = _PROJECT_ROOT / "examples"


def load_example(filename: str) -> Any:
    """Read and parse a JSON file from the /examples directory.

    Args:
        filename: Bare filename including extension, e.g. ``"resume_example.json"``.

    Returns:
        The parsed JSON value (dict or list).

    Raises:
        HTTPException(500): If the file does not exist or contains invalid JSON.
    """
    path = _EXAMPLES_DIR / filename
    if not path.is_file():
        raise internal_error(f"Example file not found: examples/{filename}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise internal_error(
            f"Invalid JSON in examples/{filename}: {exc}"
        ) from exc
