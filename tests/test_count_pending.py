#!/usr/bin/env python3
"""Unit tests for count_pending.py (current-lock summary)."""

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


def _feat(id_, status="failing", deprecated=False, sub_status=None):
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


def _data(features, current=None):
    return {"project": "p", "features": features, "current": current}


def test_empty_features():
    code, out, _ = run(_data([]))
    assert code == 0
    assert "current=none" in out
    assert "passing=0" in out
    assert "failing=0" in out
    assert "total=0" in out


def test_current_lock_reported():
    data = _data([_feat(1), _feat(2, "passing")],
                 current={"feature_id": 1, "phase": "tdd"})
    code, out, _ = run(data)
    assert code == 0
    assert "current=#1(tdd)" in out
    assert "passing=1" in out
    assert "failing=1" in out
    assert "total=2" in out


def test_null_current_no_lock():
    data = _data([_feat(1, "passing"), _feat(2, "passing")], current=None)
    code, out, _ = run(data)
    assert "current=none" in out
    assert "passing=2" in out
    assert "failing=0" in out


def test_deprecated_excluded_from_total():
    data = _data([_feat(1, "passing"), _feat(2, deprecated=True)])
    code, out, _ = run(data)
    assert code == 0
    assert "total=1" in out
    assert "deprecated=1" in out


def test_legacy_sub_status_signalled():
    """Feature carrying legacy sub_status field shows legacy_sub_status count."""
    data = _data([_feat(1, sub_status="design_pending")])
    code, out, _ = run(data)
    assert code == 0
    assert "legacy_sub_status=1" in out


def test_missing_file_exits_2():
    r = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/path.json"],
        capture_output=True, text=True
    )
    assert r.returncode == 2


def test_json_output_fields():
    data = _data([_feat(1), _feat(2, "passing")],
                 current={"feature_id": 1, "phase": "design"})
    code, out, _ = run(data, "--json")
    assert code == 0
    parsed = json.loads(out)
    assert parsed["total"] == 2
    assert parsed["passing"] == 1
    assert parsed["failing"] == 1
    assert parsed["current"] == {"feature_id": 1, "phase": "design"}
    assert parsed["deprecated"] == 0
    assert parsed["legacy_sub_status"] == 0


def test_json_legacy_sub_status_reported():
    data = _data([_feat(1, sub_status="tdd_pending"),
                  _feat(2, sub_status="design_pending")])
    code, out, _ = run(data, "--json")
    parsed = json.loads(out)
    assert parsed["legacy_sub_status"] == 2


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
