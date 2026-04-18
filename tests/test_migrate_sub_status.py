#!/usr/bin/env python3
"""Unit tests for migrate_sub_status.py"""

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


def test_passing_becomes_done():
    code, out, result = run({"features": [_f(1, status="passing")]})
    assert code == 0
    assert result["features"][0]["sub_status"] == "done"
    assert "updated=1" in out


def test_failing_no_git_sha_becomes_design_pending():
    code, _, result = run({"features": [_f(1)]})
    assert code == 0
    assert result["features"][0]["sub_status"] == "design_pending"


def test_failing_with_git_sha_becomes_st_pending():
    code, _, result = run({"features": [_f(1, git_sha="abc1234")]})
    assert code == 0
    assert result["features"][0]["sub_status"] == "st_pending"


def test_existing_valid_sub_status_skipped():
    code, out, result = run({"features": [_f(1, sub_status="tdd_pending")]})
    assert code == 0
    assert result["features"][0]["sub_status"] == "tdd_pending"
    assert "skipped=1" in out


def test_force_overrides_existing():
    code, out, result = run(
        {"features": [_f(1, status="passing", sub_status="design_pending")]},
        "--force",
    )
    assert code == 0
    assert result["features"][0]["sub_status"] == "done"
    assert "updated=1" in out


def test_dry_run_does_not_write():
    data = {"features": [_f(1)]}
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
        assert "sub_status" not in content["features"][0]
    finally:
        os.unlink(tmp)


def test_idempotent_second_run_is_noop():
    data = {"features": [_f(1, status="passing")]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        json.dump(data, fh)
        tmp = fh.name
    try:
        subprocess.run([sys.executable, SCRIPT_PATH, tmp], capture_output=True, text=True)
        r2 = subprocess.run([sys.executable, SCRIPT_PATH, tmp], capture_output=True, text=True)
        assert r2.returncode == 0
        assert "skipped=1" in r2.stdout
        assert "updated=0" in r2.stdout
    finally:
        os.unlink(tmp)


def test_mixed_migration():
    data = {"features": [
        _f(1, status="passing"),
        _f(2, status="failing"),
        _f(3, status="failing", git_sha="deadbeef"),
        _f(4, status="passing", sub_status="done"),  # already valid, skipped
    ]}
    code, out, result = run(data)
    assert code == 0
    statuses = [f["sub_status"] for f in result["features"]]
    assert statuses == ["done", "design_pending", "st_pending", "done"]
    assert "updated=3" in out
    assert "skipped=1" in out


if __name__ == "__main__":
    tests = [
        test_passing_becomes_done,
        test_failing_no_git_sha_becomes_design_pending,
        test_failing_with_git_sha_becomes_st_pending,
        test_existing_valid_sub_status_skipped,
        test_force_overrides_existing,
        test_dry_run_does_not_write,
        test_idempotent_second_run_is_noop,
        test_mixed_migration,
    ]
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
