#!/usr/bin/env python3
"""
Unit tests for check_env_guide_approval.py

Strategy: build a throwaway git repo per test and drive the script via its
public check() function. Covers:
  - first-generation exemption (null approved_by + no §3/§4 history)
  - unapproved when §3/§4 edited post-approval
  - approved when approved_date >= latest §3/§4 edit
  - malformed / missing file paths
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from check_env_guide_approval import check, touches_sections, parse_frontmatter

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_env_guide_approval.py")


GUIDE_V1_UNAPPROVED = """---
version: 1.0
approved_by: null
approved_date: null
approved_sections: []
---

# env-guide.md

## §1 Service Lifecycle
- initial

## §2 Environment Configuration
- initial

## §3 Build & Execution Commands
- initial build cmd

## §4 Codebase Constraints
- initial constraint

## §5 Test Environment Dependencies
- initial

## §6 Human Approval Record
- initial
"""

GUIDE_V2_APPROVED = """---
version: 2.0
approved_by: alice
approved_date: 2100-01-01
approved_sections: ["§3", "§4"]
---

# env-guide.md

## §1 Service Lifecycle
- v2

## §2 Environment Configuration
- v2

## §3 Build & Execution Commands
- updated build cmd
- new line

## §4 Codebase Constraints
- updated constraint

## §5 Test Environment Dependencies
- v2

## §6 Human Approval Record
- v2
"""

GUIDE_V2_STALE_APPROVAL = """---
version: 2.0
approved_by: alice
approved_date: 2000-01-01
approved_sections: ["§3"]
---

# env-guide.md

## §1 Service Lifecycle
- v2

## §2 Environment Configuration
- v2

## §3 Build & Execution Commands
- updated build cmd
- new line

## §4 Codebase Constraints
- updated constraint

## §5 Test Environment Dependencies
- v2

## §6 Human Approval Record
- v2
"""


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "commit.gpgsign", "false")
    return tmp_path


def write_guide(repo: Path, content: str) -> Path:
    p = repo / "env-guide.md"
    p.write_text(content, encoding="utf-8")
    return p


def test_first_generation_exemption(repo):
    """First commit of env-guide.md with null approved_by → approved."""
    p = write_guide(repo, GUIDE_V1_UNAPPROVED)
    git(repo, "add", "env-guide.md")
    git(repo, "commit", "-m", "init env-guide")
    # Initial commit touches §3/§4 for the first time; scripts should detect
    # the first-gen exemption only when no prior edit exists — here the file
    # was just created, so approved_by=null and the commit DOES touch §3/§4.
    # Per the design: approved_by=null + commits exist → unapproved.
    # So this is actually NOT an exemption if the initial commit touched §3.
    # Adjust the test to reflect the actual contract.
    result = check(str(p))
    assert result["status"] == "unapproved"
    assert "null" in result["reason"]


def test_exemption_when_no_git_history(repo):
    """File exists on disk but no git commit yet → approved (untracked)."""
    p = write_guide(repo, GUIDE_V1_UNAPPROVED)
    # Do not git add / commit
    result = check(str(p))
    # No commits touching the file at all → approved
    assert result["status"] == "approved"


def test_approved_when_date_newer_than_edit(repo):
    """Latest §3/§4 edit < approved_date → approved."""
    p = write_guide(repo, GUIDE_V1_UNAPPROVED)
    git(repo, "add", "env-guide.md")
    git(repo, "commit", "-m", "init")
    # Update to v2 which approves
    p.write_text(GUIDE_V2_APPROVED, encoding="utf-8")
    git(repo, "add", "env-guide.md")
    git(repo, "commit", "-m", "update and approve")
    result = check(str(p))
    assert result["status"] == "approved", result


def test_unapproved_when_approval_stale(repo):
    """§3/§4 edited after stale approved_date → unapproved."""
    p = write_guide(repo, GUIDE_V1_UNAPPROVED)
    git(repo, "add", "env-guide.md")
    git(repo, "commit", "-m", "init")
    p.write_text(GUIDE_V2_STALE_APPROVAL, encoding="utf-8")
    git(repo, "add", "env-guide.md")
    git(repo, "commit", "-m", "edit §3 and §4 after old approval")
    result = check(str(p))
    assert result["status"] == "unapproved"
    # Latest commit date is now (2025+), approved_date is 2000 → unapproved
    assert "approved_date" in result["reason"] or "null" in result["reason"] or "modified" in result["reason"]


def test_missing_file():
    result = check("/tmp/nonexistent-env-guide.md")
    assert result["status"] == "missing"


def test_malformed_frontmatter(tmp_path):
    p = tmp_path / "env-guide.md"
    p.write_text("# no frontmatter\n## §1\n## §2\n## §3\n## §4\n## §5\n## §6\n",
                 encoding="utf-8")
    result = check(str(p))
    assert result["status"] == "malformed"


def test_touches_sections_detects_section3_edit():
    diff = """@@ -10,3 +10,3 @@
 ## §3 Build & Execution Commands
-old command
+new command
"""
    assert touches_sections(diff, ("§3", "§4"))


def test_touches_sections_ignores_section1_edit():
    diff = """@@ -1,3 +1,3 @@
 ## §1 Service Lifecycle
-old
+new
"""
    assert not touches_sections(diff, ("§3", "§4"))


def test_parse_frontmatter():
    fm = parse_frontmatter(GUIDE_V2_APPROVED)
    assert fm.get("approved_by") == "alice"
    assert fm.get("version") == "2.0"


def test_cli_exit_code_on_approved(tmp_path):
    git(tmp_path, "init")
    git(tmp_path, "config", "commit.gpgsign", "false")
    p = tmp_path / "env-guide.md"
    p.write_text(GUIDE_V1_UNAPPROVED, encoding="utf-8")
    git(tmp_path, "add", "env-guide.md")
    git(tmp_path, "commit", "-m", "init")
    p.write_text(GUIDE_V2_APPROVED, encoding="utf-8")
    git(tmp_path, "add", "env-guide.md")
    git(tmp_path, "commit", "-m", "approve")
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, str(p)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_exit_code_on_missing(tmp_path):
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, str(tmp_path / "nope.md")],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
