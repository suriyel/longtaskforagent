#!/usr/bin/env python3
"""Unit tests for migrate_sub_status.py (legacy sub_status → root current)."""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "migrate_sub_status.py")


def run(data, *extra):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        tmp = f.name
    try:
        r = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp, *extra],
            capture_output=True, text=True
        )
        if "--dry-run" in extra:
            written = None
        else:
            with open(tmp) as f:
                written = json.load(f)
        return r.returncode, r.stdout, written
    finally:
        os.unlink(tmp)


def _f(id_, **kw):
    d = {"id": id_, "category": "core", "title": f"T{id_}",
         "description": "D", "priority": "high", "status": "failing"}
    d.update(kw)
    return d


def test_design_pending_becomes_current_design():
    code, out, result = run({"features": [_f(1, sub_status="design_pending")]})
    assert code == 0
    assert result["current"] == {"feature_id": 1, "phase": "design"}
    assert "sub_status" not in result["features"][0]
    assert "cleared sub_status from 1" in out


def test_tdd_pending_becomes_current_tdd():
    code, _, result = run({"features": [_f(1, sub_status="tdd_pending")]})
    assert code == 0
    assert result["current"] == {"feature_id": 1, "phase": "tdd"}


def test_st_pending_becomes_current_st():
    code, _, result = run({"features": [_f(1, sub_status="st_pending")]})
    assert code == 0
    assert result["current"] == {"feature_id": 1, "phase": "st"}


def test_most_advanced_phase_wins():
    """Migration should preserve in-flight work: F8 tdd beats F1 design."""
    data = {"features": [
        _f(1, sub_status="design_pending"),
        _f(7, sub_status="design_pending"),
        _f(8, sub_status="tdd_pending"),
        _f(5, status="passing", sub_status="done"),
    ]}
    code, _, result = run(data)
    assert code == 0
    assert result["current"] == {"feature_id": 8, "phase": "tdd"}
    for f in result["features"]:
        assert "sub_status" not in f


def test_smallest_id_tiebreaks_same_phase():
    """When multiple features share the same (most-advanced) phase, lowest id wins."""
    data = {"features": [
        _f(5, sub_status="tdd_pending"),
        _f(3, sub_status="tdd_pending"),
        _f(1, sub_status="design_pending"),  # less advanced → ignored
    ]}
    code, _, result = run(data)
    assert code == 0
    assert result["current"] == {"feature_id": 3, "phase": "tdd"}


def test_all_done_becomes_current_null():
    data = {"features": [
        _f(1, status="passing", sub_status="done"),
        _f(2, status="passing", sub_status="done"),
    ]}
    code, out, result = run(data)
    assert code == 0
    assert result["current"] is None
    assert "current=null (all done)" in out


def test_deprecated_features_skipped_when_picking_current():
    """Deprecated features with sub_status should be ignored when picking current."""
    data = {"features": [
        _f(1, sub_status="design_pending", deprecated=True, deprecated_reason="old"),
        _f(2, sub_status="tdd_pending"),
    ]}
    code, _, result = run(data)
    assert code == 0
    assert result["current"] == {"feature_id": 2, "phase": "tdd"}
    # But the sub_status field is still cleared from all features including deprecated
    for f in result["features"]:
        assert "sub_status" not in f


def test_idempotent_second_run_noop():
    """Already-migrated file (current set, no sub_status) is left alone."""
    data = {"current": {"feature_id": 1, "phase": "design"},
            "features": [_f(1)]}
    code, out, result = run(data)
    assert code == 0
    assert "already migrated" in out
    assert result["current"] == {"feature_id": 1, "phase": "design"}


def test_force_re_runs_even_if_migrated():
    """--force re-picks current from sub_status even if current already exists."""
    data = {"current": {"feature_id": 99, "phase": "st"},
            "features": [_f(1, sub_status="design_pending")]}
    code, _, result = run(data, "--force")
    assert code == 0
    assert result["current"] == {"feature_id": 1, "phase": "design"}


def test_dry_run_does_not_write():
    data = {"features": [_f(1, sub_status="design_pending")]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        json.dump(data, fh)
        tmp = fh.name
    try:
        r = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp, "--dry-run"],
            capture_output=True, text=True
        )
        assert r.returncode == 0
        assert "[dry-run]" in r.stdout
        with open(tmp) as f:
            content = json.load(f)
        # File unchanged: sub_status still there, no `current` injected
        assert content["features"][0]["sub_status"] == "design_pending"
        assert "current" not in content
    finally:
        os.unlink(tmp)


def test_reference_scenario_f8_tdd():
    """Mirrors reference/feature-list.json: F1-F7, F9-F12 are design_pending;
    F8 is tdd_pending. Migration should pick F8 (most-advanced phase)."""
    features = [
        _f(1, sub_status="design_pending"),
        _f(2, sub_status="design_pending"),
        _f(3, sub_status="design_pending"),
        _f(4, sub_status="design_pending"),
        _f(5, sub_status="design_pending"),
        _f(6, sub_status="design_pending"),
        _f(7, sub_status="design_pending"),
        _f(8, sub_status="tdd_pending"),
        _f(9, sub_status="design_pending"),
        _f(10, sub_status="design_pending"),
        _f(11, sub_status="design_pending"),
        _f(12, sub_status="design_pending"),
    ]
    code, _, result = run({"features": features})
    assert code == 0
    # F8 tdd beats all design_pending (most-advanced phase wins)
    assert result["current"] == {"feature_id": 8, "phase": "tdd"}


if __name__ == "__main__":
    import inspect
    tests = [t for name, t in sorted(globals().items())
             if name.startswith("test_") and inspect.isfunction(t)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
