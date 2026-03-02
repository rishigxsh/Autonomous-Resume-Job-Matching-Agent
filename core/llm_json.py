"""JSON extraction helper for raw LLM output.

LLMs occasionally wrap JSON in markdown fences or add commentary.
This module provides a single function that reliably extracts the first
valid JSON object from any raw text string.
"""

import json
import re
from typing import Any


def extract_json(raw: str) -> Any:
    """Extract and parse the first valid JSON object from a raw LLM string.

    Strategy:
    1. Strip markdown code fences if present (```json ... ``` or ``` ... ```).
    2. Find the first '{' and match its closing '}' to isolate the object.
    3. Parse with json.loads and return the Python dict.

    Args:
        raw: Raw string returned by the LLM.

    Returns:
        Parsed Python dict representing the JSON object.

    Raises:
        ValueError: If no valid JSON object can be extracted or parsed.
    """
    # 1. Remove markdown code fences.
    text = re.sub(r"```(?:json)?", "", raw).strip()

    # 2. Find the outermost JSON object boundaries.
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM output.")

    # Walk forward tracking brace depth to find the matching closing brace.
    depth = 0
    end = -1
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        raise ValueError("Unmatched braces — could not extract JSON object.")

    candidate = text[start : end + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Extracted text is not valid JSON: {exc}") from exc
