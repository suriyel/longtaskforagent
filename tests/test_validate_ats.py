"""Tests for validate_ats.py"""

import json
import os
import tempfile

import pytest

# Adjust path for import
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_ats import validate


def _write_tmp(content: str, suffix: str = ".md") -> str:
    """Write content to a temp file, return path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


MINIMAL_ATS = """\
# 验收测试策略: Test Project

## 1. 测试范围与策略概览

测试目标说明。

## 2. 需求→验收场景映射

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 |
|--------|---------|---------|---------|--------|
| FR-001 | 用户登录 | 正常登录/错误密码 | FUNC,BNDRY,SEC | High |
| FR-002 | 用户注册 | 正常注册/重复邮箱 | FUNC,BNDRY | Medium |
| NFR-001 | 响应时间 | P95延迟 | PERF | High |

## 3. 测试类别策略

各类别说明。
"""

MINIMAL_SRS = """\
# SRS

## 4. Functional Requirements

### FR-001 用户登录

### FR-002 用户注册

### FR-003 密码重置

## 5. Non-Functional Requirements

### NFR-001 响应时间
"""


class TestValidateAts:
    def test_valid_minimal_ats(self):
        path = _write_tmp(MINIMAL_ATS)
        try:
            errors, warnings = validate(path)
            assert errors == []
        finally:
            os.unlink(path)

    def test_empty_file(self):
        path = _write_tmp("")
        try:
            errors, _ = validate(path)
            assert any("empty" in e.lower() for e in errors)
        finally:
            os.unlink(path)

    def test_missing_file(self):
        errors, _ = validate("/nonexistent/path.md")
        assert any("not found" in e.lower() for e in errors)

    def test_missing_required_sections(self):
        content = "# Just a heading\n\nSome content.\n"
        path = _write_tmp(content)
        try:
            errors, _ = validate(path)
            assert len(errors) >= 2  # Missing sections + no mapping rows
        finally:
            os.unlink(path)

    def test_invalid_category(self):
        content = MINIMAL_ATS.replace("FUNC,BNDRY,SEC", "FUNC,BNDRY,INVALID")
        path = _write_tmp(content)
        try:
            errors, _ = validate(path)
            assert any("INVALID" in e for e in errors)
        finally:
            os.unlink(path)

    def test_duplicate_req_id(self):
        content = MINIMAL_ATS + "| FR-001 | 重复 | 场景 | FUNC,BNDRY | Low |\n"
        path = _write_tmp(content)
        try:
            errors, _ = validate(path)
            assert any("duplicate" in e.lower() for e in errors)
        finally:
            os.unlink(path)

    def test_empty_scenarios(self):
        content = MINIMAL_ATS.replace("正常登录/错误密码", "")
        path = _write_tmp(content)
        try:
            errors, _ = validate(path)
            assert any("scenarios" in e.lower() and "empty" in e.lower() for e in errors)
        finally:
            os.unlink(path)

    def test_srs_cross_validation_missing_req(self):
        ats_path = _write_tmp(MINIMAL_ATS)
        srs_path = _write_tmp(MINIMAL_SRS)
        try:
            errors, _ = validate(ats_path, srs_path)
            # FR-003 is in SRS but not in ATS
            assert any("FR-003" in e for e in errors)
        finally:
            os.unlink(ats_path)
            os.unlink(srs_path)

    def test_srs_cross_validation_orphan_row(self):
        # Add a row for FR-099 which is not in SRS
        content = MINIMAL_ATS + "| FR-099 | 不存在 | 场景 | FUNC,BNDRY | Low |\n"
        ats_path = _write_tmp(content)
        srs_path = _write_tmp(MINIMAL_SRS)
        try:
            errors, warnings = validate(ats_path, srs_path)
            assert any("FR-099" in w and "orphan" in w.lower() for w in warnings)
        finally:
            os.unlink(ats_path)
            os.unlink(srs_path)

    def test_single_category_warning(self):
        content = MINIMAL_ATS.replace("FUNC,BNDRY,SEC", "FUNC")
        path = _write_tmp(content)
        try:
            _, warnings = validate(path)
            assert any("only one category" in w.lower() for w in warnings)
        finally:
            os.unlink(path)

    def test_fr_missing_func_warning(self):
        content = MINIMAL_ATS.replace("FUNC,BNDRY,SEC", "BNDRY,SEC")
        path = _write_tmp(content)
        try:
            _, warnings = validate(path)
            assert any("missing FUNC" in w for w in warnings)
        finally:
            os.unlink(path)

