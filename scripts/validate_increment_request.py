#!/usr/bin/env python3
"""
Validate increment-request.json structure.

Checks:
- Valid JSON structure
- Required fields present: reason, scope
- Fields are non-empty strings

Usage:
    python validate_increment_request.py <path/to/increment-request.json>
"""

import json
import sys


def _force_utf8_io() -> None:
    """Force stdout/stderr to UTF-8 so CJK text survives non-UTF-8 locales
    (Windows cp936, LANG=C). Python 3.7+."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


REQUIRED_FIELDS = {"reason", "scope"}


def validate(path: str) -> list[str]:
    """Validate increment-request.json. Returns list of errors."""
    errors = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found: {path}"]

    if not isinstance(data, dict):
        return ["Root must be a JSON object"]

    # Check required fields
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")

    # Check field types and non-emptiness
    for field in REQUIRED_FIELDS:
        val = data.get(field)
        if val is not None:
            if not isinstance(val, str):
                errors.append(f"'{field}' must be a string, got {type(val).__name__}")
            elif len(val.strip()) == 0:
                errors.append(f"'{field}' must not be empty")

    return errors


def main():
    _force_utf8_io()
    if len(sys.argv) != 2:
        print("Usage: validate_increment_request.py <path/to/increment-request.json>")
        sys.exit(1)

    errors = validate(sys.argv[1])

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"VALID — reason: {data['reason']}")
        print(f"         scope: {data['scope']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
