#!/usr/bin/env python3
"""
Validate bugfix-request.json structure.

Checks:
- Valid JSON structure
- Required fields present with correct types
- severity is one of the allowed enum values
- feature_id is integer >= 1 or null
- reproduction_steps is a non-empty list of non-empty strings

Usage:
    python validate_bugfix_request.py <path/to/bugfix-request.json>

Exit codes:
    0 — valid
    1 — invalid (errors printed to stdout)
"""

import json
import sys


def _force_utf8_io() -> None:
    """Force stdout/stderr to UTF-8 so CJK text survives non-UTF-8 locales
    (Windows cp936, LANG=C). Python 3.7+."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


REQUIRED_STRING_FIELDS = {"title", "description", "expected_behavior", "actual_behavior"}
VALID_SEVERITIES = {"Critical", "Major", "Minor", "Cosmetic"}
TITLE_MAX_LEN = 200


def validate(path: str) -> list[str]:
    """Validate bugfix-request.json. Returns list of errors."""
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

    # Check required string fields
    for field in REQUIRED_STRING_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
        else:
            val = data[field]
            if not isinstance(val, str):
                errors.append(f"'{field}' must be a string, got {type(val).__name__}")
            elif len(val.strip()) == 0:
                errors.append(f"'{field}' must not be empty")

    # Check title length
    title = data.get("title")
    if isinstance(title, str) and len(title) > TITLE_MAX_LEN:
        errors.append(f"'title' must be {TITLE_MAX_LEN} characters or fewer, got {len(title)}")

    # Check severity
    if "severity" not in data:
        errors.append("Missing required field: 'severity'")
    else:
        severity = data["severity"]
        if not isinstance(severity, str):
            errors.append(f"'severity' must be a string, got {type(severity).__name__}")
        elif severity not in VALID_SEVERITIES:
            errors.append(
                f"'severity' must be one of {sorted(VALID_SEVERITIES)}, got '{severity}'"
            )

    # Check feature_id (key must be present; value is int >= 1 or null)
    if "feature_id" not in data:
        errors.append("Missing required field: 'feature_id' (use null if unknown)")
    else:
        fid = data["feature_id"]
        if fid is not None:
            if not isinstance(fid, int) or isinstance(fid, bool):
                errors.append(f"'feature_id' must be an integer >= 1 or null, got {type(fid).__name__}")
            elif fid < 1:
                errors.append(f"'feature_id' must be >= 1, got {fid}")

    # Check reproduction_steps
    if "reproduction_steps" not in data:
        errors.append("Missing required field: 'reproduction_steps'")
    else:
        steps = data["reproduction_steps"]
        if not isinstance(steps, list):
            errors.append(f"'reproduction_steps' must be a list, got {type(steps).__name__}")
        elif len(steps) == 0:
            errors.append("'reproduction_steps' must not be empty")
        else:
            for i, step in enumerate(steps):
                if not isinstance(step, str):
                    errors.append(
                        f"'reproduction_steps[{i}]' must be a string, got {type(step).__name__}"
                    )
                elif len(step.strip()) == 0:
                    errors.append(f"'reproduction_steps[{i}]' must not be empty")

    # Check optional: environment
    if "environment" in data and data["environment"] is not None:
        if not isinstance(data["environment"], str):
            errors.append(
                f"'environment' must be a string or null, got {type(data['environment']).__name__}"
            )

    # Check optional: attachments
    if "attachments" in data and data["attachments"] is not None:
        attachments = data["attachments"]
        if not isinstance(attachments, list):
            errors.append(
                f"'attachments' must be a list or null, got {type(attachments).__name__}"
            )
        else:
            for i, item in enumerate(attachments):
                if not isinstance(item, str):
                    errors.append(
                        f"'attachments[{i}]' must be a string, got {type(item).__name__}"
                    )

    return errors


def main():
    _force_utf8_io()
    if len(sys.argv) != 2:
        print("Usage: validate_bugfix_request.py <path/to/bugfix-request.json>")
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
        title = data["title"]
        severity = data["severity"]
        print(f"VALID — severity: {severity}, title: {title[:60]}")
        sys.exit(0)


if __name__ == "__main__":
    main()
