#!/usr/bin/env python3
"""Asserts no symlinks exist under skills/.

Windows 插件安装器用 Node fs.symlink 重建 symlink，非 admin / 无 Developer Mode
会 EPERM 失败。为防回归，禁止在 skills/ 下提交任何 symlink。跨 skill 共享规则
应改为 SKILL.md 直接引用 canonical 路径（如 long-task-tdd-shared/references/）。
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def test_skills_dir_has_no_symlinks():
    offenders = []
    for path in SKILLS_DIR.rglob("*"):
        if path.is_symlink():
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert not offenders, (
        "Found symlinks under skills/ (break Windows plugin install):\n  "
        + "\n  ".join(offenders)
        + "\nReplace with SKILL.md references to canonical paths."
    )
