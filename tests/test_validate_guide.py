#!/usr/bin/env python3
"""
Unit tests for validate_guide.py
"""

import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_guide.py")


def run_validator(content):
    """Write content to temp file, run validate_guide.py, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        tmp_path = f.name

    try:
        cmd = [sys.executable, SCRIPT_PATH, tmp_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


# A complete guide with all required sections (pure tool config)
COMPLETE_GUIDE = """# My Project — Tool Command Reference

## Test Commands

[test-quiet]
  cmd: pytest -q --tb=line
  instruction: capture output to temp file; print exit code; show last 5 lines

[test-detail]
  instruction: search temp file for 'FAILED', 'ERROR'; show first 30 matches

Full: pytest tests/

## UT Style

[test-framework]  pytest + unittest.mock
[mock-style]      patch/Mock (boundary-only); prefer fakes for internal deps
[conventions]     explore related existing tests + source code before writing; reuse discovered fixtures/helpers

## Caveats

- [mock] conftest.py uses pytest-mock mocker fixture → use mocker, not unittest.mock.patch
- [coverage] pyproject.toml [tool.coverage] has branch=true → --cov-branch not needed explicitly
"""


def test_complete_guide_passes():
    """A guide with all required sections should pass validation."""
    code, stdout, _ = run_validator(COMPLETE_GUIDE)
    assert code == 0, f"Expected exit 0 for complete guide: {stdout}"
    assert "VALID" in stdout


def test_empty_guide_fails():
    """An empty guide should fail validation."""
    code, stdout, _ = run_validator("")
    assert code != 0, f"Expected non-zero for empty guide: {stdout}"


def test_missing_test_commands_fails():
    """A guide missing test commands should fail."""
    content = COMPLETE_GUIDE.replace("test-quiet", "xxx-quiet")
    content = content.replace("test-detail", "xxx-detail")
    content = content.replace("Test Commands", "XXX Section")
    content = content.replace("test command", "xxx")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when test commands missing: {stdout}"


def test_alternative_wording_passes():
    """A guide using alternative but equivalent wording should still pass."""
    content = """# Project Tool Reference

## Test command recipes

[test-quiet]
  cmd: npx jest --verbose=false
  instruction: capture output; show last 5 lines

[test-detail]
  instruction: search for FAIL; show first 30

## UT Style

[test-framework]  Jest + jest.fn/jest.mock
[mock-style]      jest.fn()/jest.mock() (boundary-only)
[conventions]     explore existing tests before writing

## 注意事项

- [mock] __mocks__/ directory exists with manual mocks for axios → reuse
"""
    code, stdout, _ = run_validator(content)
    assert code == 0, f"Expected exit 0 for alternative wording: {stdout}"


def test_missing_ut_style_fails():
    """A guide missing UT Style section should fail."""
    content = """# Project Tool Reference

## Test Commands

[test-quiet]
  cmd: pytest -q --tb=line
  instruction: capture output; show last 5 lines

[test-detail]
  instruction: search for FAIL; show first 30
"""
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when UT Style missing: {stdout}"
    assert "UT Style" in stdout


def test_ut_style_with_tag_only_passes():
    """A guide with [test-framework] tag but no 'UT Style' heading should still pass."""
    content = """# Project Tool Reference

## Test Commands

[test-quiet]
  cmd: npx jest --verbose=false
  instruction: capture output; show last 5 lines

[test-detail]
  instruction: search for FAIL; show first 30

[test-framework]  Jest + jest.fn/jest.mock
[mock-style]      jest.fn()/jest.mock() (boundary-only)
[conventions]     explore existing tests before writing

## Caveats

- [config] jest.config uses moduleNameMapper for path aliases
"""
    code, stdout, _ = run_validator(content)
    assert code == 0, f"Expected exit 0 for tag-only UT Style: {stdout}"


def test_missing_caveats_fails():
    """A guide missing Caveats section should fail."""
    content = """# Project Tool Reference

## Test Commands

[test-quiet]
  cmd: pytest -q --tb=line
  instruction: capture output; show last 5 lines

[test-detail]
  instruction: search for FAIL; show first 30

## UT Style

[test-framework]  pytest + unittest.mock
[mock-style]      patch/Mock (boundary-only)
[conventions]     explore existing tests before writing
"""
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when Caveats missing: {stdout}"
    assert "Caveats" in stdout


def test_nonexistent_file():
    """Validating a nonexistent file should fail."""
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/path/guide.md"],
        capture_output=True, text=True
    )
    assert result.returncode != 0


def test_error_count_in_output():
    """Output should show how many sections are missing."""
    code, stdout, _ = run_validator("# Empty guide\nNothing here.")
    assert code != 0
    assert "FAILED" in stdout
    assert "Missing required section" in stdout


if __name__ == "__main__":
    tests = [
        test_complete_guide_passes,
        test_empty_guide_fails,
        test_missing_test_commands_fails,
        test_alternative_wording_passes,
        test_missing_ut_style_fails,
        test_ut_style_with_tag_only_passes,
        test_missing_caveats_fails,
        test_nonexistent_file,
        test_error_count_in_output,
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
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
