#!/usr/bin/env python3
"""
Unit tests for validate_st_cases.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_st_cases.py")

# Minimal valid test case document
VALID_DOC = """\
# 测试用例集: User Login

**Feature ID**: 1
**关联需求**: FR-001
**日期**: 2026-02-28
**测试标准**: ISO/IEC/IEEE 29119-3

## 摘要

| 类别 | 用例数 |
|------|--------|
| functional | 1 |
| **合计** | **1** |

---

### 用例编号

ST-FUNC-001-001

### 关联需求

FR-001（用户登录）

### 测试目标

验证用户使用有效凭证能够成功登录

### 前置条件

- 用户已注册
- 系统服务正常运行

### 测试步骤

| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | 打开登录页面 | 页面加载成功 |
| 2 | 输入有效邮箱和密码 | 输入框显示内容 |
| 3 | 点击登录按钮 | 跳转至首页 |

### 验证点

- 用户会话已创建
- 数据库记录登录时间

### 后置检查

- 日志无 error
- 前端无 JS 报错

### 元数据

- **优先级**: High
- **类别**: functional
- **已自动化**: Yes
- **测试引用**: tests/test_login.py::test_valid_login

## 可追溯矩阵

| 用例 ID | 关联需求 | verification_step | 自动化测试 | 结果 |
|---------|----------|-------------------|-----------|------|
| ST-FUNC-001-001 | FR-001 | verification_step[0] | test_valid_login | PENDING |
"""


def run_validator(doc_content, feature_list_data=None, feature_id=None):
    """Run validate_st_cases.py with given content, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(doc_content)
        f.flush()
        doc_path = f.name

    fl_path = None
    try:
        cmd = [sys.executable, SCRIPT_PATH, doc_path]

        if feature_list_data is not None:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fl:
                json.dump(feature_list_data, fl, indent=2)
                fl.flush()
                fl_path = fl.name
            cmd.extend(["--feature-list", fl_path])

        if feature_id is not None:
            cmd.extend(["--feature", str(feature_id)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(doc_path)
        if fl_path:
            os.unlink(fl_path)


def test_valid_document():
    code, stdout, _ = run_validator(VALID_DOC)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"
    assert "VALID" in stdout
    assert "1 test case" in stdout


def test_empty_file():
    code, stdout, _ = run_validator("")
    assert code != 0
    assert "empty" in stdout.lower()


def test_no_case_blocks():
    doc = "# Some Document\n\nNo test cases here.\n"
    code, stdout, _ = run_validator(doc)
    assert code != 0
    assert "No test case blocks found" in stdout


def test_missing_case_id_content():
    doc = """\
### 用例编号

### 关联需求

FR-001

### 测试目标

Test something

### 前置条件

- None

### 测试步骤

| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | Do thing | Thing done |

### 验证点

- Check result

### 后置检查

- None

### 元数据

- **优先级**: High
"""
    code, stdout, _ = run_validator(doc)
    assert code != 0
    assert "missing case ID" in stdout


def test_invalid_case_id_format():
    doc = VALID_DOC.replace("ST-FUNC-001-001", "INVALID-ID")
    code, stdout, _ = run_validator(doc)
    assert code != 0
    assert "does not match pattern" in stdout


def test_duplicate_case_ids():
    # Add a second case with the same ID
    second_case = """
---

### 用例编号

ST-FUNC-001-001

### 关联需求

FR-001（重复用例）

### 测试目标

验证重复

### 前置条件

- None

### 测试步骤

| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | Do | Done |

### 验证点

- Check

### 后置检查

- None

### 元数据

- **优先级**: Low
"""
    doc = VALID_DOC + second_case
    code, stdout, _ = run_validator(doc)
    assert code != 0
    assert "duplicate" in stdout.lower()


def test_missing_required_section():
    # Remove 验证点 section
    doc = VALID_DOC.replace("### 验证点\n\n- 用户会话已创建\n- 数据库记录登录时间\n", "")
    code, stdout, _ = run_validator(doc)
    assert code != 0
    assert "验证点" in stdout or "Verification Points" in stdout


def test_feature_id_mismatch():
    """Case ID has feature 001 but --feature 2 is specified."""
    code, stdout, _ = run_validator(VALID_DOC, feature_id=2)
    assert code != 0
    assert "does not match" in stdout


def test_feature_id_match():
    code, stdout, _ = run_validator(VALID_DOC, feature_id=1)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"


def test_feature_list_verification_step_coverage():
    """Check that verification_steps from feature-list.json are covered."""
    fl_data = {
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "User Login",
                "description": "Login feature",
                "priority": "high",
                "status": "failing",
                "verification_steps": ["User can login with valid credentials"],
            }
        ]
    }
    code, stdout, _ = run_validator(VALID_DOC, feature_list_data=fl_data, feature_id=1)
    # Should pass (verification_step[0] is referenced in traceability matrix)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"


def test_feature_list_missing_feature():
    """Specified feature not found in feature-list.json."""
    fl_data = {
        "features": [
            {
                "id": 99,
                "category": "core",
                "title": "Other",
                "description": "Other",
                "priority": "high",
                "status": "failing",
                "verification_steps": ["Step"],
            }
        ]
    }
    code, stdout, _ = run_validator(VALID_DOC, feature_list_data=fl_data, feature_id=1)
    assert code != 0
    assert "not found" in stdout.lower()


def test_english_section_names():
    """Test case using English section names should also be valid."""
    doc = """\
# Test Case Set: User Login

## Summary

| Category | Count |
|----------|-------|
| functional | 1 |

---

### Case ID

ST-FUNC-001-001

### Related Requirement

FR-001 (User Login)

### Test Objective

Verify user can login with valid credentials

### Preconditions

- User is registered

### Test Steps

| Step | Action | Expected Result |
| ---- | ------ | --------------- |
| 1 | Open login page | Page loads |
| 2 | Enter credentials | Fields populated |

### Verification Points

- Session created

### Post-Conditions

- No errors in logs

### Metadata

- **Priority**: High
- **Category**: functional
- **Automated**: Yes
- **Test Reference**: test_login.py::test_valid

## Traceability Matrix

| Case ID | Requirement | verification_step | Automated Test | Result |
|---------|-------------|-------------------|----------------|--------|
| ST-FUNC-001-001 | FR-001 | verification_step[0] | test_valid | PENDING |
"""
    code, stdout, _ = run_validator(doc)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"
    assert "VALID" in stdout


def test_valid_categories():
    """Test that all valid category abbreviations are accepted."""
    categories = ["FUNC", "BNDRY", "UI", "SEC", "PERF"]
    for i, cat in enumerate(categories):
        doc = VALID_DOC.replace("ST-FUNC-001-001", f"ST-{cat}-001-{i+1:03d}")
        doc = doc.replace("functional", cat.lower())
        code, stdout, _ = run_validator(doc)
        assert code == 0, f"Category {cat} should be valid, got: {stdout}"


def test_missing_summary_warning():
    """Missing summary section should produce warning, not error."""
    doc = VALID_DOC.replace("## 摘要", "## Other Section")
    doc = doc.replace("## 可追溯矩阵", "## Other Matrix")
    code, stdout, _ = run_validator(doc)
    # Should still pass (warnings, not errors)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"
    assert "warning" in stdout.lower()


def test_multiple_cases():
    """Document with multiple valid test cases."""
    second_case = """
---

### 用例编号

ST-BNDRY-001-001

### 关联需求

FR-001（用户登录 - 边界条件）

### 测试目标

验证空密码输入被拒绝

### 前置条件

- 用户已注册

### 测试步骤

| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | 打开登录页面 | 页面加载成功 |
| 2 | 输入邮箱，密码留空 | 密码框为空 |
| 3 | 点击登录按钮 | 显示错误提示 |

### 验证点

- 显示"密码不能为空"提示
- 未创建会话

### 后置检查

- 无

### 元数据

- **优先级**: Medium
- **类别**: boundary
- **已自动化**: Yes
- **测试引用**: tests/test_login.py::test_empty_password
"""
    doc = VALID_DOC + second_case
    code, stdout, _ = run_validator(doc)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"
    assert "2 test case" in stdout


def test_empty_verification_points():
    """Empty verification points should be an error."""
    doc = VALID_DOC.replace(
        "### 验证点\n\n- 用户会话已创建\n- 数据库记录登录时间",
        "### 验证点\n\n"
    )
    code, stdout, _ = run_validator(doc)
    assert code != 0
    assert "verification points" in stdout.lower() or "验证点" in stdout


# --- Quality warning tests ---

def test_quality_warning_vague_expected_result():
    """Test step with vague expected result should produce quality warning."""
    doc_vague = VALID_DOC.replace(
        "| 1 | 打开登录页面 | 页面加载成功 |",
        "| 1 | Open login page | Page displays correctly |"
    )
    code, stdout, _ = run_validator(doc_vague)
    assert code == 0
    assert "[QUALITY]" in stdout and "vague" in stdout.lower(), f"Expected vague result warning: {stdout}"


def test_quality_warning_no_negative_path():
    """Document with no negative/error test cases should warn."""
    # VALID_DOC only has a single positive happy-path case
    code, stdout, _ = run_validator(VALID_DOC)
    assert code == 0
    assert "negative" in stdout.lower() or "error path" in stdout.lower(), \
        f"Expected no-negative-path warning: {stdout}"


def test_quality_no_warning_for_func_cases():
    """Non-UI FUNC test cases should NOT produce UI-specific quality warnings."""
    code, stdout, _ = run_validator(VALID_DOC)
    assert code == 0
    # VALID_DOC has ST-FUNC-001-001 — should not get Layer 1/2/3 warnings
    assert "Layer 1" not in stdout, f"Unexpected Layer 1 warning for FUNC case: {stdout}"
    assert "Layer 2" not in stdout, f"Unexpected Layer 2 warning for FUNC case: {stdout}"
    assert "Layer 3" not in stdout, f"Unexpected Layer 3 warning for FUNC case: {stdout}"


