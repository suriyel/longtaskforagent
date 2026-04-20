#!/usr/bin/env python3
"""
Unit tests for validate_increment_request.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "skills", "using-long-task", "scripts", "validate_increment_request.py")


def run_validator(data, *, raw_content=None):
    """Run validate_increment_request.py with given data, return (exit_code, stdout, stderr)."""
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


def test_valid_request():
    data = {"reason": "Add export feature per user feedback", "scope": "CSV and PDF export"}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0: {stdout}"
    assert "VALID" in stdout


def test_missing_reason():
    data = {"scope": "New features"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "reason" in stdout.lower()


def test_missing_scope():
    data = {"reason": "User feedback"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "scope" in stdout.lower()


def test_empty_reason():
    data = {"reason": "  ", "scope": "New features"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for empty reason: {stdout}"


def test_empty_scope():
    data = {"reason": "User feedback", "scope": ""}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for empty scope: {stdout}"


def test_reason_not_string():
    data = {"reason": 42, "scope": "New features"}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-string reason: {stdout}"


def test_scope_not_string():
    data = {"reason": "User feedback", "scope": ["a", "b"]}
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-string scope: {stdout}"


def test_invalid_json():
    code, stdout, _ = run_validator(None, raw_content="not json")
    assert code != 0, f"Expected non-zero for invalid JSON: {stdout}"


def test_root_not_object():
    code, stdout, _ = run_validator(None, raw_content='["array"]')
    assert code != 0, f"Expected non-zero for non-object root: {stdout}"


def test_extra_fields_ok():
    data = {"reason": "Feedback", "scope": "Export", "priority": "high"}
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 with extra fields: {stdout}"


def test_nonexistent_file():
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/file.json"],
        capture_output=True, text=True
    )
    assert result.returncode != 0


if __name__ == "__main__":
    tests = [
        test_valid_request,
        test_missing_reason,
        test_missing_scope,
        test_empty_reason,
        test_empty_scope,
        test_reason_not_string,
        test_scope_not_string,
        test_invalid_json,
        test_root_not_object,
        test_extra_fields_ok,
        test_nonexistent_file,
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
