#!/usr/bin/env python3
"""Unit tests for check_lcd_wiring.py."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "skills", "using-long-task", "scripts", "check_lcd_wiring.py"
)


def run_check(feature_data: dict, srs_text: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as d:
        fl = Path(d) / "feature-list.json"
        srs = Path(d) / "srs.md"
        fl.write_text(json.dumps(feature_data), encoding="utf-8")
        srs.write_text(srs_text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, str(fl), str(srs)],
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout, result.stderr


SRS_WITH_LCDS = """### 1.4.2 Legacy Context Decisions (LCD)

| LCD-ID | 类别 | 原文依据 | 澄清决议 | 权威 | 影响 FR/CON | 状态 |
|--------|------|----------|----------|------|-------------|------|
| LCD-001 | BEHAVIOR | "x" | keep A merge | RESOLVED | FR-005 | ACTIVE |
| LCD-002 | COMPAT | "y" | as-is | QUOTED | IFR-002 | ACTIVE |
| LCD-003 | RATIONALE | "z" | explains why | QUOTED | — | ACTIVE |
| LCD-004 | DATA | "w" | encoding utf-8 | RESOLVED | FR-010 | DEPRECATED |

### 1.4.3 Archive
"""


def _feat(fid: int, lcd_trace: list[str] | None = None) -> dict:
    feat = {
        "id": fid, "category": "core", "title": f"f{fid}",
        "description": "d", "priority": "high", "status": "failing",
        "dependencies": [],
    }
    if lcd_trace is not None:
        feat["lcd_trace"] = lcd_trace
    return feat


def test_happy_path_all_referenced():
    data = {"project": "p", "created": "2026-04-21", "features": [
        _feat(1, ["LCD-001"]),
        _feat(2, ["LCD-002"]),
    ]}
    code, out, _ = run_check(data, SRS_WITH_LCDS)
    assert code == 0, out


def test_missing_lcd_reference_fails():
    data = {"project": "p", "created": "2026-04-21", "features": [
        _feat(1, ["LCD-999"]),
    ]}
    code, out, _ = run_check(data, SRS_WITH_LCDS)
    assert code == 1
    assert "LCD-999 which does not exist" in out


def test_rationale_in_lcd_trace_fails():
    data = {"project": "p", "created": "2026-04-21", "features": [
        _feat(1, ["LCD-003"]),
    ]}
    code, out, _ = run_check(data, SRS_WITH_LCDS)
    assert code == 1
    assert "RATIONALE" in out


def test_deprecated_lcd_referenced_fails():
    data = {"project": "p", "created": "2026-04-21", "features": [
        _feat(1, ["LCD-004"]),
    ]}
    code, out, _ = run_check(data, SRS_WITH_LCDS)
    assert code == 1
    assert "DEPRECATED" in out


def test_orphan_active_lcd_warning_not_blocking():
    # LCD-001 active non-rationale, not referenced by any feature → warning only
    data = {"project": "p", "created": "2026-04-21", "features": [
        _feat(1, ["LCD-002"]),
    ]}
    code, out, _ = run_check(data, SRS_WITH_LCDS)
    assert code == 0  # warnings don't block
    assert "LCD-001" in out
    assert "not referenced" in out


def test_greenfield_empty_lcd_table():
    srs = """### 1.4.2 Legacy Context Decisions (LCD)

| LCD-ID | 类别 | 原文依据 | 澄清决议 | 权威 | 影响 FR/CON | 状态 |
|--------|------|----------|----------|------|-------------|------|

### 1.5 Next
"""
    data = {"project": "p", "created": "2026-04-21", "features": [_feat(1)]}
    code, out, _ = run_check(data, srs)
    assert code == 0, out


def test_no_lcd_trace_fields_ok():
    # features without lcd_trace + LCDs exist → warnings for orphans but pass
    data = {"project": "p", "created": "2026-04-21", "features": [_feat(1), _feat(2)]}
    code, out, _ = run_check(data, SRS_WITH_LCDS)
    assert code == 0
    # LCD-001 and LCD-002 are orphans, LCD-003 RATIONALE exempt, LCD-004 DEPRECATED exempt
    assert "LCD-001" in out
    assert "LCD-002" in out


def test_conflicted_lcd_fails():
    srs = """### 1.4.2 Legacy Context Decisions (LCD)

| LCD-ID | 类别 | 原文依据 | 澄清决议 | 权威 | 影响 FR/CON | 状态 |
|--------|------|----------|----------|------|-------------|------|
| LCD-001 | BEHAVIOR | "x" | ??? | CONFLICTED | FR-001 | ACTIVE |

### 1.5 Next
"""
    data = {"project": "p", "created": "2026-04-21", "features": [_feat(1, ["LCD-001"])]}
    code, out, _ = run_check(data, srs)
    assert code == 1
    assert "CONFLICTED" in out


def test_missing_srs_file_fails():
    with tempfile.TemporaryDirectory() as d:
        fl = Path(d) / "feature-list.json"
        fl.write_text(json.dumps({"project": "p", "features": []}), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, str(fl), "/nonexistent.md"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1


if __name__ == "__main__":
    for test in [
        test_happy_path_all_referenced,
        test_missing_lcd_reference_fails,
        test_rationale_in_lcd_trace_fails,
        test_deprecated_lcd_referenced_fails,
        test_orphan_active_lcd_warning_not_blocking,
        test_greenfield_empty_lcd_table,
        test_no_lcd_trace_fields_ok,
        test_conflicted_lcd_fails,
        test_missing_srs_file_fails,
    ]:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            sys.exit(1)
    print("\nAll tests passed!")
