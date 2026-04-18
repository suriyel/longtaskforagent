#!/usr/bin/env python3
"""Unit tests for count_pending.py"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "count_pending.py")


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
        return r.returncode, r.stdout, r.stderr
    finally:
        os.unlink(tmp)


def _feat(id_, sub_status=None, status="failing", deprecated=False):
    d = {
        "id": id_, "category": "core", "title": f"T{id_}",
        "description": "D", "priority": "high", "status": status,
    }
    if sub_status is not None:
        d["sub_status"] = sub_status
    if deprecated:
        d["deprecated"] = True
        d["deprecated_reason"] = "obsolete"
    return d


def test_empty_features_all_zero():
    code, out, _ = run({"project": "p", "features": []})
    assert code == 0
    assert "design=0 tdd=0 st=0 done=0 (total=0)" == out.strip()


def test_mixed_distribution():
    data = {"project": "p", "features": [
        _feat(1, "design_pending"),
        _feat(2, "tdd_pending"),
        _feat(3, "tdd_pending"),
        _feat(4, "st_pending"),
        _feat(5, "done", status="passing"),
        _feat(6, "done", status="passing"),
    ]}
    code, out, _ = run(data)
    assert code == 0, out
    assert "design=1" in out
    assert "tdd=2" in out
    assert "st=1" in out
    assert "done=2" in out
    assert "total=6" in out


def test_deprecated_excluded():
    data = {"project": "p", "features": [
        _feat(1, "done", status="passing"),
        _feat(2, deprecated=True),
    ]}
    code, out, _ = run(data)
    assert code == 0
    assert "total=1" in out
    assert "deprecated=1" in out


def test_no_sub_status_bucket():
    data = {"project": "p", "features": [_feat(1)]}
    code, out, _ = run(data)
    assert code == 0
    assert "no_sub_status=1" in out


def test_missing_file_exits_2():
    r = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/path.json"],
        capture_output=True, text=True
    )
    assert r.returncode == 2


def test_json_output():
    data = {"project": "p", "features": [_feat(1, "tdd_pending")]}
    code, out, _ = run(data, "--json")
    assert code == 0
    parsed = json.loads(out)
    assert parsed["tdd"] == 1
    assert parsed["design"] == 0
    assert parsed["total"] == 1


if __name__ == "__main__":
    tests = [
        test_empty_features_all_zero, test_mixed_distribution,
        test_deprecated_excluded, test_no_sub_status_bucket,
        test_missing_file_exits_2, test_json_output,
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
