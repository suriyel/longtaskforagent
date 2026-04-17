#!/usr/bin/env python3
"""
Unit tests for check_st_readiness.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_st_readiness.py")


def create_project(features, docs=None):
    """Create a temporary project directory with feature-list.json and optional docs.

    Args:
        features: list of feature dicts
        docs: dict with optional keys 'srs', 'design', 'ucd' (True to create)

    Returns:
        (tmp_dir, feature_list_path) — caller must clean up tmp_dir
    """
    tmp_dir = tempfile.mkdtemp()
    fl_path = os.path.join(tmp_dir, "feature-list.json")
    data = {
        "project": "test",
        "tech_stack": {"language": "python", "test_framework": "pytest",
                       "coverage_tool": "pytest-cov"},
        "quality_gates": {"line_coverage_min": 90, "branch_coverage_min": 80},
        "features": features,
    }
    with open(fl_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    docs = docs or {}
    plans_dir = os.path.join(tmp_dir, "docs", "plans")
    os.makedirs(plans_dir, exist_ok=True)
    if docs.get("srs"):
        with open(os.path.join(plans_dir, "2025-01-01-test-srs.md"), "w") as f:
            f.write("# SRS\n")
    if docs.get("design"):
        with open(os.path.join(plans_dir, "2025-01-01-test-design.md"), "w") as f:
            f.write("# Design\n")
    if docs.get("ucd"):
        with open(os.path.join(plans_dir, "2025-01-01-test-ucd.md"), "w") as f:
            f.write("# UCD\n")

    return tmp_dir, fl_path


def run_checker(fl_path):
    """Run check_st_readiness.py and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, fl_path],
        capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr


def cleanup(tmp_dir):
    """Remove temporary directory tree."""
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_all_passing_with_docs():
    """All features passing + SRS + design → ready (exit 0)."""
    features = [
        {"id": 1, "status": "passing", "title": "A"},
        {"id": 2, "status": "passing", "title": "B"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code == 0, f"Expected 0: {stdout}"
        assert "READY" in stdout
        assert "2/2 passing" in stdout
    finally:
        cleanup(tmp_dir)


def test_failing_features_not_ready():
    """Some features failing → not ready (exit 1)."""
    features = [
        {"id": 1, "status": "passing", "title": "A"},
        {"id": 2, "status": "failing", "title": "B"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code != 0, f"Expected non-zero: {stdout}"
        assert "NOT READY" in stdout
        assert "1/2 passing" in stdout
        assert "failing" in stdout.lower()
    finally:
        cleanup(tmp_dir)


def test_missing_srs_not_ready():
    """All passing but no SRS → not ready."""
    features = [{"id": 1, "status": "passing", "title": "A"}]
    tmp_dir, fl_path = create_project(features, {"design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code != 0, f"Expected non-zero: {stdout}"
        assert "SRS" in stdout
    finally:
        cleanup(tmp_dir)


def test_missing_design_not_ready():
    """All passing but no design → not ready."""
    features = [{"id": 1, "status": "passing", "title": "A"}]
    tmp_dir, fl_path = create_project(features, {"srs": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code != 0, f"Expected non-zero: {stdout}"
        assert "Design" in stdout or "design" in stdout.lower()
    finally:
        cleanup(tmp_dir)


def test_no_features_not_ready():
    """Empty features array → not ready."""
    tmp_dir, fl_path = create_project([], {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code != 0, f"Expected non-zero: {stdout}"
        assert "NOT READY" in stdout
    finally:
        cleanup(tmp_dir)


def test_ui_features_without_ucd_warns():
    """UI features without UCD doc → warning in output."""
    features = [{"id": 1, "status": "passing", "title": "A", "ui": True}]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        # Still ready (UCD is not a hard gate for ST), but should warn
        assert code == 0, f"Expected 0: {stdout}"
        assert "UCD" in stdout
    finally:
        cleanup(tmp_dir)


def test_ui_features_with_ucd_no_warning():
    """UI features with UCD doc → no UCD warning."""
    features = [{"id": 1, "status": "passing", "title": "A", "ui": True}]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True, "ucd": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code == 0, f"Expected 0: {stdout}"
        assert "READY" in stdout
        assert "MISSING" not in stdout
    finally:
        cleanup(tmp_dir)


def test_nonexistent_file():
    """Non-existent feature-list.json → exit 1 with error."""
    code, stdout, _ = run_checker("/nonexistent/feature-list.json")
    assert code != 0
    assert "ERROR" in stdout


def test_invalid_json():
    """Invalid JSON → exit 1 with error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not json")
        tmp_path = f.name
    try:
        code, stdout, _ = run_checker(tmp_path)
        assert code != 0
        assert "ERROR" in stdout
    finally:
        os.unlink(tmp_path)


def test_failing_ids_listed():
    """Failing feature IDs should be listed in output."""
    features = [
        {"id": 1, "status": "passing", "title": "A"},
        {"id": 3, "status": "failing", "title": "C"},
        {"id": 5, "status": "failing", "title": "E"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code != 0
        assert "3" in stdout
        assert "5" in stdout
    finally:
        cleanup(tmp_dir)


# --- deprecated feature exclusion tests ---

def test_deprecated_features_excluded_from_counts():
    """Deprecated features should be excluded from readiness checks."""
    features = [
        {"id": 1, "status": "passing", "title": "A"},
        {"id": 2, "status": "passing", "title": "B", "deprecated": True, "deprecated_reason": "Old"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code == 0, f"Expected 0 (deprecated excluded): {stdout}"
        assert "READY" in stdout
        assert "1/1" in stdout, f"Expected 1/1 active features: {stdout}"
    finally:
        cleanup(tmp_dir)


def test_deprecated_failing_excluded_still_ready():
    """A deprecated feature with 'failing' status should not block readiness."""
    features = [
        {"id": 1, "status": "passing", "title": "A"},
        {"id": 2, "status": "failing", "title": "B", "deprecated": True, "deprecated_reason": "Removed"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code == 0, f"Expected 0 (deprecated failing excluded): {stdout}"
        assert "READY" in stdout
    finally:
        cleanup(tmp_dir)


def test_all_deprecated_not_ready():
    """If all features are deprecated → not ready (no active features)."""
    features = [
        {"id": 1, "status": "passing", "title": "A", "deprecated": True, "deprecated_reason": "Old"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code != 0, f"Expected non-zero (no active features): {stdout}"
        assert "NOT READY" in stdout
    finally:
        cleanup(tmp_dir)


def test_mixed_active_and_deprecated():
    """Mixed active passing + deprecated → ready."""
    features = [
        {"id": 1, "status": "passing", "title": "A"},
        {"id": 2, "status": "passing", "title": "B"},
        {"id": 3, "status": "passing", "title": "C", "deprecated": True, "deprecated_reason": "Replaced"},
        {"id": 4, "status": "failing", "title": "D", "deprecated": True, "deprecated_reason": "Removed"},
    ]
    tmp_dir, fl_path = create_project(features, {"srs": True, "design": True})
    try:
        code, stdout, _ = run_checker(fl_path)
        assert code == 0, f"Expected 0: {stdout}"
        assert "2/2" in stdout, f"Expected 2/2 active: {stdout}"
    finally:
        cleanup(tmp_dir)


if __name__ == "__main__":
    tests = [
        test_all_passing_with_docs,
        test_failing_features_not_ready,
        test_missing_srs_not_ready,
        test_missing_design_not_ready,
        test_no_features_not_ready,
        test_ui_features_without_ucd_warns,
        test_ui_features_with_ucd_no_warning,
        test_nonexistent_file,
        test_invalid_json,
        test_failing_ids_listed,
        test_deprecated_features_excluded_from_counts,
        test_deprecated_failing_excluded_still_ready,
        test_all_deprecated_not_ready,
        test_mixed_active_and_deprecated,
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
