#!/usr/bin/env python3
"""
Unit tests for validate_bugfix_request.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "skills", "using-long-task", "scripts", "validate_bugfix_request.py")

VALID_MINIMAL = {
    "title": "Login returns 500 on empty username",
    "description": "Submitting the login form with an empty username causes a 500 error",
    "severity": "Major",
    "feature_id": 3,
    "reproduction_steps": ["Navigate to /login", "Leave username blank", "Click Submit"],
    "expected_behavior": "Should return 400 validation error",
    "actual_behavior": "Returns 500 internal server error",
}


def run_validator(data, *, raw_content=None):
    """Run validate_bugfix_request.py with given data, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        if raw_content is not None:
            f.write(raw_content)
        else:
            json.dump(data, f, indent=2)
        f.flush()
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


def test_valid_minimal():
    code, stdout, _ = run_validator(VALID_MINIMAL)
    assert code == 0, f"Expected exit 0: {stdout}"
    assert "VALID" in stdout


def test_valid_with_optional_fields():
    data = {**VALID_MINIMAL, "environment": "Windows 10, Chrome 120", "attachments": ["/tmp/screenshot.png"]}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 with optional fields: {stdout}"
    assert "VALID" in stdout


def test_missing_title():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "title"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "title" in stdout.lower()


def test_missing_description():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "description"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "description" in stdout.lower()


def test_missing_severity():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "severity"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "severity" in stdout.lower()


def test_missing_feature_id_key():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "feature_id"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "feature_id" in stdout.lower()


def test_missing_reproduction_steps():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "reproduction_steps"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "reproduction_steps" in stdout.lower()


def test_missing_expected_behavior():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "expected_behavior"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "expected_behavior" in stdout.lower()


def test_missing_actual_behavior():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "actual_behavior"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "actual_behavior" in stdout.lower()


def test_invalid_severity():
    data = {**VALID_MINIMAL, "severity": "blocker"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for invalid severity: {stdout}"
    assert "severity" in stdout.lower()


def test_severity_case_sensitive():
    data = {**VALID_MINIMAL, "severity": "critical"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for lowercase severity: {stdout}"


def test_feature_id_null():
    data = {**VALID_MINIMAL, "feature_id": None}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for null feature_id: {stdout}"


def test_feature_id_integer():
    data = {**VALID_MINIMAL, "feature_id": 5}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for integer feature_id: {stdout}"


def test_feature_id_zero():
    data = {**VALID_MINIMAL, "feature_id": 0}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for feature_id=0: {stdout}"
    assert "feature_id" in stdout.lower()


def test_feature_id_string():
    data = {**VALID_MINIMAL, "feature_id": "5"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for string feature_id: {stdout}"


def test_reproduction_steps_empty_list():
    data = {**VALID_MINIMAL, "reproduction_steps": []}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for empty reproduction_steps: {stdout}"


def test_reproduction_steps_empty_string_element():
    data = {**VALID_MINIMAL, "reproduction_steps": ["step 1", ""]}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for empty string in reproduction_steps: {stdout}"


def test_reproduction_steps_null_element():
    data = {**VALID_MINIMAL, "reproduction_steps": ["step 1", None]}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for null element in reproduction_steps: {stdout}"


def test_attachments_non_string_element():
    data = {**VALID_MINIMAL, "attachments": [123]}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-string attachment: {stdout}"


def test_title_too_long():
    data = {**VALID_MINIMAL, "title": "x" * 201}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for title > 200 chars: {stdout}"


def test_title_at_max_length():
    data = {**VALID_MINIMAL, "title": "x" * 200}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for title at exactly 200 chars: {stdout}"


def test_empty_title():
    data = {**VALID_MINIMAL, "title": "   "}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for whitespace-only title: {stdout}"


def test_invalid_json():
    code, stdout, _ = run_validator(None, raw_content="not json")
    assert code != 0, f"Expected non-zero for invalid JSON: {stdout}"


def test_root_not_object():
    code, stdout, _ = run_validator(None, raw_content='["array"]')
    assert code != 0, f"Expected non-zero for non-object root: {stdout}"


def test_extra_fields_ok():
    data = {**VALID_MINIMAL, "reporter": "alice", "ticket": "BUG-123"}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 with extra fields: {stdout}"


def test_nonexistent_file():
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/file.json"],
        capture_output=True, text=True
    )
    assert result.returncode != 0


def test_environment_optional():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "environment"}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 without environment: {stdout}"


def test_attachments_optional():
    data = {k: v for k, v in VALID_MINIMAL.items() if k != "attachments"}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 without attachments: {stdout}"


def test_valid_all_severities():
    for severity in ["Critical", "Major", "Minor", "Cosmetic"]:
        data = {**VALID_MINIMAL, "severity": severity}
        code, stdout, _ = run_validator(data)
        assert code == 0, f"Expected exit 0 for severity '{severity}': {stdout}"


if __name__ == "__main__":
    tests = [
        test_valid_minimal,
        test_valid_with_optional_fields,
        test_missing_title,
        test_missing_description,
        test_missing_severity,
        test_missing_feature_id_key,
        test_missing_reproduction_steps,
        test_missing_expected_behavior,
        test_missing_actual_behavior,
        test_invalid_severity,
        test_severity_case_sensitive,
        test_feature_id_null,
        test_feature_id_integer,
        test_feature_id_zero,
        test_feature_id_string,
        test_reproduction_steps_empty_list,
        test_reproduction_steps_empty_string_element,
        test_reproduction_steps_null_element,
        test_attachments_non_string_element,
        test_title_too_long,
        test_title_at_max_length,
        test_empty_title,
        test_invalid_json,
        test_root_not_object,
        test_extra_fields_ok,
        test_nonexistent_file,
        test_environment_optional,
        test_attachments_optional,
        test_valid_all_severities,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
