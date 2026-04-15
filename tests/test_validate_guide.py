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

Full: pytest --cov=src tests/

## Coverage Commands

[coverage-quiet]
  cmd: pytest --cov=src --cov-branch --cov-report=term-missing -q --tb=line
  instruction: capture output to temp file; print exit code; show last 10 lines

[coverage-feature-quiet]
  cmd: pytest --cov={changed_modules} --cov-branch --cov-report=term-missing -q --tb=line {test_files}
  instruction: capture output to temp file; print exit code; show last 10 lines

[coverage-feature-detail]
  instruction: search temp file for coverage summary lines; show first 30 matches

Full: pytest --cov=src --cov-branch --cov-report=term-missing

## Mutation Commands

[mutation-feature-quiet]
  cmd: mutmut run --paths-to-mutate={changed_files} --tests-dir={test_files}
  instruction: capture output to temp file; print exit code; show last 10 lines

[mutation-feature-detail]
  instruction: search temp file for 'survived' or 'timeout'; show first 30 matches

[mutation-full-quiet]
  cmd: mutmut run
  instruction: capture output to temp file; print exit code; show last 10 lines

Full: mutmut run
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


def test_missing_coverage_commands_fails():
    """A guide missing coverage commands should fail."""
    content = COMPLETE_GUIDE.replace("coverage-quiet", "xxx-quiet")
    content = content.replace("coverage-feature-quiet", "xxx-feature-quiet")
    content = content.replace("Coverage Commands", "XXX Section")
    content = content.replace("coverage command", "xxx")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when coverage commands missing: {stdout}"


def test_missing_mutation_commands_fails():
    """A guide missing mutation commands should fail."""
    content = COMPLETE_GUIDE.replace("mutation-feature-quiet", "xxx-feature-quiet")
    content = content.replace("mutation-full-quiet", "xxx-full-quiet")
    content = content.replace("Mutation Commands", "XXX Section")
    content = content.replace("mutation command", "xxx")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when mutation commands missing: {stdout}"


def test_alternative_wording_passes():
    """A guide using alternative but equivalent wording should still pass."""
    content = """# Project Tool Reference

## Test command recipes

[test-quiet]
  cmd: npx jest --verbose=false
  instruction: capture output; show last 5 lines

[test-detail]
  instruction: search for FAIL; show first 30

## Coverage command recipes

[coverage-quiet]
  cmd: npx c8 npx jest
  instruction: capture; show last 10 lines

[coverage-feature-quiet]
  cmd: npx c8 --include={changed_modules} npx jest
  instruction: capture; show last 10 lines

## Mutation command recipes

[mutation-feature-quiet]
  cmd: npx stryker run --mutate={changed_files}
  instruction: capture; show last 10 lines

[mutation-full-quiet]
  cmd: npx stryker run
  instruction: capture; show last 10 lines
"""
    code, stdout, _ = run_validator(content)
    assert code == 0, f"Expected exit 0 for alternative wording: {stdout}"


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
        test_missing_coverage_commands_fails,
        test_missing_mutation_commands_fails,
        test_alternative_wording_passes,
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
