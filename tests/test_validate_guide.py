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


# A complete guide that contains all required sections
COMPLETE_GUIDE = """# My Project — Long-Task Worker Guide

## Session Workflow

### Step 1: Orient — understand current state
1. Read `task-progress.md` to understand what happened before
2. Read `feature-list.json` to find next priority failing feature

### Step 2: Bootstrap — restore environment
1. Run `bash init.sh`
2. Quick smoke test

### Step 3: TDD Red — write failing tests first
1. Write unit tests covering verification_steps — they MUST fail

### Step 4: TDD Green — implement to pass tests
1. Write minimal code to make ALL tests pass

### Step 4.5: Coverage Gate — verify test coverage
1. Line coverage >= threshold, branch coverage >= threshold
2. Run: `pytest --cov=src --cov-branch`

### Step 5: TDD Refactor — clean up
1. Refactor while keeping tests green

### Step 5.5m: Mutation Gate — verify test effectiveness
1. Mutation score >= threshold
2. Run: `mutmut run`

### Step 5.5v: Verification enforcement
NEVER mark "passing" without fresh evidence — run tests, read output

### Step 5.5c: ST Test Cases — test case generation
1. Generate ISO/IEC/IEEE 29119 test cases via long-task-st-case
2. Validate with validate_st_cases.py

### Step 5.5r: Inline Compliance Check
1. Spec compliance
2. Design compliance

### Step 6: Persist — save state
1. git commit
2. Update task-progress.md

## Critical Rules
- NEVER write implementation before tests
- NEVER mark passing without evidence
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


def test_missing_tdd_red_fails():
    """A guide missing TDD Red should fail."""
    content = COMPLETE_GUIDE.replace("TDD Red", "Step Three")
    content = content.replace("failing tests first", "initial setup")
    content = content.replace("MUST fail", "MUST work")
    content = content.replace("write failing test", "write initial code")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when TDD Red missing: {stdout}"


def test_missing_coverage_gate_fails():
    """A guide missing Coverage Gate should fail."""
    content = COMPLETE_GUIDE.replace("Coverage Gate", "Quality Check")
    content = content.replace("coverage", "quality")
    content = content.replace("Coverage", "Quality")
    # Also remove branch coverage reference
    content = content.replace("line coverage", "line quality")
    content = content.replace("branch coverage", "branch quality")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when Coverage Gate missing: {stdout}"


def test_missing_mutation_gate_fails():
    """A guide missing Mutation Gate should fail."""
    content = COMPLETE_GUIDE.replace("Mutation Gate", "Extra Check")
    content = content.replace("mutation", "extra")
    content = content.replace("Mutation", "Extra")
    content = content.replace("mutmut", "extratool")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when Mutation Gate missing: {stdout}"


def test_missing_verification_enforcement_fails():
    """A guide missing verification enforcement should fail."""
    content = COMPLETE_GUIDE.replace("Verification enforcement", "Quality check")
    content = content.replace("verification", "quality-check")
    content = content.replace("fresh evidence", "good results")
    content = content.replace("never mark passing without", "always ensure good")
    content = content.replace("NEVER mark", "ALWAYS ensure")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when verification missing: {stdout}"


def test_missing_compliance_review_fails():
    """A guide missing Inline Compliance Check should fail."""
    content = COMPLETE_GUIDE.replace("Inline Compliance Check", "Final Step")
    content = content.replace("inline compliance", "final step")
    content = content.replace("compliance check", "final step")
    content = content.replace("Spec compliance", "Final check A")
    content = content.replace("Design compliance", "Final check B")
    content = content.replace("spec compliance", "final check a")
    content = content.replace("design compliance", "final check b")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when Inline Compliance Check missing: {stdout}"


def test_missing_critical_rules_fails():
    """A guide missing Critical Rules section should fail."""
    content = COMPLETE_GUIDE.replace("Critical Rules", "Guidelines")
    content = content.replace("critical rule", "guideline")
    content = content.replace("must never", "should avoid")
    content = content.replace("NEVER", "AVOID")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when Critical Rules missing: {stdout}"


def test_alternative_wording_passes():
    """A guide using alternative but equivalent wording should still pass."""
    content = """# Project Guide

## Workflow

### Understand current state
Read task-progress.md and feature-list.json.

### Restore environment
Run init.sh to bootstrap.

### Write failing tests first
Write unit tests that MUST fail before implementation.

### Implement to pass tests
Write minimal code to make ALL tests pass.

### Coverage threshold check
Verify line coverage >= 90% and branch coverage >= 80%.

### Clean up
Refactor code while keeping tests green.

### Mutation testing
Run mutation tests, verify mutation score >= 80%.

### Verification enforcement
NEVER mark "passing" without fresh evidence.

### ST test case generation
Generate 29119 test cases before TDD implementation.

### Inline compliance check
Spec compliance and design compliance checks.

### Save state
git commit, update task-progress.md.

## Critical Rules
- Must never skip TDD
- Must never mark passing without evidence
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
        test_missing_tdd_red_fails,
        test_missing_coverage_gate_fails,
        test_missing_mutation_gate_fails,
        test_missing_verification_enforcement_fails,
        test_missing_compliance_review_fails,
        test_missing_critical_rules_fails,
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
