#!/usr/bin/env python3
"""
Unit tests for validate_guide.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_guide.py")


def run_validator(content, feature_list_data=None):
    """Write content to temp file, run validate_guide.py, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        tmp_path = f.name

    fl_path = None
    if feature_list_data is not None:
        fl_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(feature_list_data, fl_file, indent=2)
        fl_file.flush()
        fl_file.close()
        fl_path = fl_file.name

    try:
        cmd = [sys.executable, SCRIPT_PATH, tmp_path]
        if fl_path:
            cmd.extend(["--feature-list", fl_path])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)
        if fl_path:
            os.unlink(fl_path)


# A complete guide that contains all required sections
COMPLETE_GUIDE = """# My Project — Long-Task Worker Guide

## Session Workflow

### Step 1: Orient — understand current state
1. Read `task-progress.md` to understand what happened before
2. Read `feature-list.json` to find next priority failing feature

### Step 2: Bootstrap — restore environment
1. Run `bash init.sh`
2. Quick smoke test

### Step 2.5: Config Gate — verify required configurations
1. Read `required_configs` from `feature-list.json`
2. Run: `python scripts/check_configs.py feature-list.json --feature <id>`

### Step 3: TDD Red — write failing tests first
1. Write unit tests covering verification_steps — they MUST fail

### Step 4: TDD Green — implement to pass tests
1. Write minimal code to make ALL tests pass

### Step 4.5: Coverage Gate — verify test coverage
1. Line coverage >= threshold, branch coverage >= threshold
2. Run: `pytest --cov=src --cov-branch`

### Step 5: TDD Refactor — clean up
1. Refactor while keeping tests green

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

### Real Test Convention
Real test marker: @pytest.mark.real_test
Run real tests only: pytest -m real_test

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


def test_missing_config_gate_fails():
    """A guide missing the Config Gate section should fail."""
    # Remove config gate related content
    content = COMPLETE_GUIDE.replace("Config Gate", "Setup Check")
    content = content.replace("required_config", "setup_item")
    content = content.replace("required config", "setup item")
    content = content.replace("check_configs", "setup_checker")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero when Config Gate missing: {stdout}"
    assert "Config Gate" in stdout or "required config" in stdout.lower()


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

### Check required configurations
Run check_configs.py for the target feature.

### Write failing tests first
Write unit tests that MUST fail before implementation.

### Implement to pass tests
Write minimal code to make ALL tests pass.

### Coverage threshold check
Verify line coverage >= 90% and branch coverage >= 80%.

### Clean up
Refactor code while keeping tests green.

### Verification enforcement
NEVER mark "passing" without fresh evidence.

### ST test case generation
Generate 29119 test cases before TDD implementation.

### Inline compliance check
Spec compliance and design compliance checks.

### Save state
git commit, update task-progress.md.

### Real test identification
Real test marker convention for this project.

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


# --- Chrome DevTools conditional section tests ---

UI_FEATURE_LIST = {
    "project": "test",
    "features": [
        {"id": 1, "category": "frontend", "title": "Login Page",
         "description": "A", "priority": "high", "status": "failing",
         "verification_steps": ["[devtools] verify login form"],
         "dependencies": [], "ui": True}
    ]
}

NON_UI_FEATURE_LIST = {
    "project": "test",
    "features": [
        {"id": 1, "category": "core", "title": "API endpoint",
         "description": "A", "priority": "high", "status": "failing",
         "verification_steps": ["Run tests"], "dependencies": []}
    ]
}

COMPLETE_GUIDE_WITH_DEVTOOLS = COMPLETE_GUIDE + """
### Chrome DevTools MCP Testing
Use take_snapshot and functional tests via DevTools MCP for UI features.
"""


def test_ui_project_with_devtools_section_passes():
    """Guide with Chrome DevTools section for UI project should pass."""
    code, stdout, _ = run_validator(COMPLETE_GUIDE_WITH_DEVTOOLS, UI_FEATURE_LIST)
    assert code == 0, f"Expected exit 0 for UI project with devtools section: {stdout}"


def test_ui_project_without_devtools_section_fails():
    """Guide without Chrome DevTools section for UI project should fail."""
    code, stdout, _ = run_validator(COMPLETE_GUIDE, UI_FEATURE_LIST)
    assert code != 0, f"Expected non-zero for UI project without devtools section: {stdout}"
    assert "UI project" in stdout or "Chrome DevTools" in stdout


def test_non_ui_project_without_devtools_section_passes():
    """Guide without Chrome DevTools section for non-UI project should pass."""
    code, stdout, _ = run_validator(COMPLETE_GUIDE, NON_UI_FEATURE_LIST)
    assert code == 0, f"Expected exit 0 for non-UI project without devtools section: {stdout}"


def test_no_feature_list_skips_devtools_check():
    """Without --feature-list, Chrome DevTools check should be skipped."""
    code, stdout, _ = run_validator(COMPLETE_GUIDE)
    assert code == 0, f"Expected exit 0 without feature list: {stdout}"


def test_devtools_section_via_take_snapshot_keyword():
    """Guide mentioning take_snapshot should satisfy Chrome DevTools check."""
    guide_with_snapshot = COMPLETE_GUIDE + "\n### UI Testing\nUse take_snapshot for UI verification.\n"
    code, stdout, _ = run_validator(guide_with_snapshot, UI_FEATURE_LIST)
    assert code == 0, f"Expected exit 0 for guide with take_snapshot: {stdout}"


if __name__ == "__main__":
    tests = [
        test_complete_guide_passes,
        test_empty_guide_fails,
        test_missing_config_gate_fails,
        test_missing_tdd_red_fails,
        test_missing_coverage_gate_fails,
        test_missing_verification_enforcement_fails,
        test_missing_compliance_review_fails,
        test_missing_critical_rules_fails,
        test_alternative_wording_passes,
        test_nonexistent_file,
        test_error_count_in_output,
        test_ui_project_with_devtools_section_passes,
        test_ui_project_without_devtools_section_fails,
        test_non_ui_project_without_devtools_section_passes,
        test_no_feature_list_skips_devtools_check,
        test_devtools_section_via_take_snapshot_keyword,
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
