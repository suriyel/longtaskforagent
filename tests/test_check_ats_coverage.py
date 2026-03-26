"""Tests for check_ats_coverage.py"""

import json
import os
import tempfile

import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from check_ats_coverage import check_coverage


def _write_tmp(content: str, suffix: str = ".md") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _write_json(data: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


MINIMAL_ATS = """\
# ATS

## 2. 需求→验收场景映射

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 |
|--------|---------|---------|---------|--------|
| FR-001 | 用户登录 | 正常/异常 | FUNC,BNDRY,SEC | High |
| FR-002 | 注册 | 正常/异常 | FUNC,BNDRY | Medium |
"""

MINIMAL_FEATURES = {
    "project": "test",
    "features": [
        {
            "id": 1,
            "category": "core",
            "title": "User Login",
            "description": "Login feature",
            "priority": "high",
            "status": "passing",
            "verification_steps": ["step 1"],
            "dependencies": [],
            "ui": False,
        },
        {
            "id": 2,
            "category": "core",
            "title": "User Registration",
            "description": "Registration feature",
            "priority": "medium",
            "status": "failing",
            "verification_steps": ["step 1"],
            "dependencies": [],
            "ui": False,
        },
    ],
}


class TestCheckAtsCoverage:
    def test_missing_ats_file(self):
        fl_path = _write_json(MINIMAL_FEATURES)
        try:
            errors, _ = check_coverage("/nonexistent.md", fl_path)
            assert any("not found" in e.lower() for e in errors)
        finally:
            os.unlink(fl_path)

    def test_missing_feature_list(self):
        ats_path = _write_tmp(MINIMAL_ATS)
        try:
            errors, _ = check_coverage(ats_path, "/nonexistent.json")
            assert any("cannot read" in e.lower() for e in errors)
        finally:
            os.unlink(ats_path)

    def test_no_mapping_rows(self):
        ats_path = _write_tmp("# Empty ATS\n\nNo tables here.\n")
        fl_path = _write_json(MINIMAL_FEATURES)
        try:
            errors, _ = check_coverage(ats_path, fl_path)
            assert any("no mapping rows" in e.lower() for e in errors)
        finally:
            os.unlink(ats_path)
            os.unlink(fl_path)

    def test_valid_coverage_no_st_cases(self):
        """Features without st_case_path generate warnings, not errors."""
        ats_path = _write_tmp(MINIMAL_ATS)
        fl_path = _write_json(MINIMAL_FEATURES)
        try:
            errors, warnings = check_coverage(ats_path, fl_path)
            assert errors == []
        finally:
            os.unlink(ats_path)
            os.unlink(fl_path)

    def test_feature_filter(self):
        ats_path = _write_tmp(MINIMAL_ATS)
        fl_path = _write_json(MINIMAL_FEATURES)
        try:
            errors, warnings = check_coverage(ats_path, fl_path, feature_id=1)
            assert errors == []
        finally:
            os.unlink(ats_path)
            os.unlink(fl_path)

    def test_nonexistent_feature_id(self):
        ats_path = _write_tmp(MINIMAL_ATS)
        fl_path = _write_json(MINIMAL_FEATURES)
        try:
            errors, _ = check_coverage(ats_path, fl_path, feature_id=999)
            assert any("999" in e for e in errors)
        finally:
            os.unlink(ats_path)
            os.unlink(fl_path)

    def test_deprecated_features_skipped(self):
        """Deprecated features should not be checked."""
        features = {
            "project": "test",
            "features": [
                {
                    "id": 1,
                    "category": "core",
                    "title": "Deprecated Feature",
                    "description": "Old",
                    "priority": "low",
                    "status": "passing",
                    "verification_steps": ["step"],
                    "dependencies": [],
                    "deprecated": True,
                    "deprecated_reason": "replaced",
                },
            ],
        }
        ats_path = _write_tmp(MINIMAL_ATS)
        fl_path = _write_json(features)
        try:
            errors, warnings = check_coverage(ats_path, fl_path)
            assert errors == []
        finally:
            os.unlink(ats_path)
            os.unlink(fl_path)

    def test_st_case_missing_category_strict(self):
        """In strict mode, missing ATS-required categories are errors."""
        # Create a minimal ST case doc that references FR-001 but has no SEC cases
        st_content = """\
# Test Cases: User Login

### 用例编号
ST-FUNC-001-001

### 关联需求
FR-001

### 测试目标
Test login

### 前置条件
- None

### 测试步骤
| Step | 操作 | 预期结果 |
| 1 | Login | Success |

### 验证点
- Login works

### 后置检查
- None

### 元数据
- **类别**: functional
"""
        st_path = _write_tmp(st_content)
        features = {
            "project": "test",
            "features": [
                {
                    "id": 1,
                    "category": "core",
                    "title": "User Login",
                    "description": "Login",
                    "priority": "high",
                    "status": "passing",
                    "verification_steps": ["step"],
                    "dependencies": [],
                    "st_case_path": st_path,
                },
            ],
        }
        ats_path = _write_tmp(MINIMAL_ATS)
        fl_path = _write_json(features)
        try:
            errors, warnings = check_coverage(ats_path, fl_path, strict=True)
            # Should have errors for missing BNDRY and SEC categories
            assert len(errors) > 0
            assert any("BNDRY" in e or "SEC" in e for e in errors)
        finally:
            os.unlink(ats_path)
            os.unlink(fl_path)
            os.unlink(st_path)
