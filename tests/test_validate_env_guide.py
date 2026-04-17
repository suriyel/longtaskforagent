#!/usr/bin/env python3
"""
Unit tests for validate_env_guide.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_env_guide.py")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_env_guide import validate, parse_frontmatter


COMPLETE_GUIDE = """---
version: 1.0
approved_by: alice
approved_date: 2026-04-17
approved_sections: ["§3", "§4"]
---

# env-guide.md

## §1 Service Lifecycle
- content

## §2 Environment Configuration
- content

## §3 Build & Execution Commands
- content

## §4 Codebase Constraints
- content

## §5 Test Environment Dependencies
- content

## §6 Human Approval Record
- content
"""

UNAPPROVED_GUIDE = """---
version: 1.0
approved_by: null
approved_date: null
approved_sections: []
---

# env-guide.md

## §1 Service Lifecycle
## §2 Environment Configuration
## §3 Build & Execution Commands
## §4 Codebase Constraints
## §5 Test Environment Dependencies
## §6 Human Approval Record
"""

MISSING_SECTION_GUIDE = """---
version: 1.0
approved_by: alice
approved_date: 2026-04-17
approved_sections: ["§3"]
---

## §1 Service Lifecycle
## §2 Environment Configuration
## §3 Build & Execution Commands
## §5 Test Environment Dependencies
## §6 Human Approval Record
"""

NO_FRONTMATTER_GUIDE = """# env-guide.md

## §1 Service Lifecycle
## §2 Environment Configuration
## §3 Build & Execution Commands
## §4 Codebase Constraints
## §5 Test Environment Dependencies
## §6 Human Approval Record
"""


def write(tmp_path, content):
    p = tmp_path / "env-guide.md"
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_complete_guide_passes(tmp_path):
    ok, messages = validate(write(tmp_path, COMPLETE_GUIDE))
    assert ok, f"Expected OK, got: {messages}"
    assert messages == []


def test_complete_guide_passes_strict(tmp_path):
    ok, messages = validate(write(tmp_path, COMPLETE_GUIDE), strict=True)
    assert ok, f"Expected OK in strict, got: {messages}"


def test_unapproved_fails_strict(tmp_path):
    path = write(tmp_path, UNAPPROVED_GUIDE)
    ok, messages = validate(path, strict=True)
    assert not ok
    assert any("NOT APPROVED" in m for m in messages)


def test_unapproved_passes_non_strict(tmp_path):
    """Non-strict mode accepts null approved_by (used at init time)."""
    ok, _messages = validate(write(tmp_path, UNAPPROVED_GUIDE), strict=False)
    assert ok


def test_missing_section_fails(tmp_path):
    ok, messages = validate(write(tmp_path, MISSING_SECTION_GUIDE))
    assert not ok
    assert any("§4" in m for m in messages)


def test_no_frontmatter_fails(tmp_path):
    ok, messages = validate(write(tmp_path, NO_FRONTMATTER_GUIDE))
    assert not ok
    assert any("frontmatter" in m.lower() for m in messages)


def test_parse_frontmatter_extracts_keys():
    fm = parse_frontmatter(COMPLETE_GUIDE)
    assert fm.get("version") == "1.0"
    assert fm.get("approved_by") == "alice"
    assert fm.get("approved_date") == "2026-04-17"


def test_missing_file_exits_nonzero(tmp_path):
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, str(tmp_path / "nonexistent.md")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_cli_success(tmp_path):
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, write(tmp_path, COMPLETE_GUIDE)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_cli_strict_fails_on_unapproved(tmp_path):
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, write(tmp_path, UNAPPROVED_GUIDE), "--strict"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "NOT APPROVED" in result.stdout
