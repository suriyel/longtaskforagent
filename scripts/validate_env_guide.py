#!/usr/bin/env python3
"""
Validate env-guide.md structural completeness.

env-guide.md is the project's single source of truth for:
  §1 Service lifecycle
  §2 Environment configuration
  §3 Build & execution commands   (consumed by TDD/Quality/Feature-ST)
  §4 Codebase constraints         (consumed by Design/Feature Design)
  §5 Test environment dependencies
  §6 Human approval record        (YAML frontmatter + audit log)

This validator checks only structural presence of section headers. It does NOT
check correctness of the commands or constraints themselves — that is the
human reviewer's job during the approval workflow.

Usage:
    python validate_env_guide.py <path/to/env-guide.md>
    python validate_env_guide.py <path/to/env-guide.md> --strict

Flags:
    --strict — require frontmatter approved_by to be non-null

Exit codes:
    0 — all six sections present (and approved if --strict)
    1 — one or more sections missing (or unapproved in --strict mode)
"""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    ("§1 Service Lifecycle", [r"##\s+§1\s", r"##\s+§\s*1[^0-9]"]),
    ("§2 Environment Configuration", [r"##\s+§2\s", r"##\s+§\s*2[^0-9]"]),
    ("§3 Build & Execution Commands", [r"##\s+§3\s", r"##\s+§\s*3[^0-9]"]),
    ("§4 Codebase Constraints", [r"##\s+§4\s", r"##\s+§\s*4[^0-9]"]),
    ("§5 Test Environment Dependencies", [r"##\s+§5\s", r"##\s+§\s*5[^0-9]"]),
    ("§6 Human Approval Record", [r"##\s+§6\s", r"##\s+§\s*6[^0-9]"]),
]


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    """Parse the YAML-like frontmatter block (minimal parser, no YAML dep)."""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    block = m.group(1)
    fm = {}
    for line in block.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


def validate(path: str, strict: bool = False) -> tuple[bool, list[str]]:
    """Return (ok, messages). Messages list every missing section."""
    p = Path(path)
    if not p.exists():
        return False, [f"File not found: {path}"]

    content = p.read_text(encoding="utf-8")
    messages: list[str] = []

    # 1. Section header check
    for label, patterns in REQUIRED_SECTIONS:
        found = any(re.search(pat, content, flags=re.MULTILINE | re.IGNORECASE)
                    for pat in patterns)
        if not found:
            messages.append(f"MISSING: {label}")

    # 2. Frontmatter presence
    fm = parse_frontmatter(content)
    if not fm:
        messages.append("MISSING: YAML frontmatter (version/approved_by/approved_date/approved_sections)")
    else:
        for key in ("version", "approved_by", "approved_date", "approved_sections"):
            if key not in fm:
                messages.append(f"MISSING: frontmatter key `{key}`")

    # 3. Strict approval check
    if strict and fm:
        approved_by = fm.get("approved_by", "").strip().strip('"').strip("'")
        if not approved_by or approved_by.lower() in ("null", "none", ""):
            messages.append("NOT APPROVED: frontmatter approved_by is null (strict mode requires explicit approval)")

    ok = len(messages) == 0
    return ok, messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", help="Path to env-guide.md")
    parser.add_argument("--strict", action="store_true",
                        help="Require frontmatter approved_by to be non-null")
    args = parser.parse_args()

    ok, messages = validate(args.path, strict=args.strict)

    if ok:
        print(f"OK: {args.path} — all six sections present" +
              (" and approved" if args.strict else ""))
        return 0

    for msg in messages:
        print(msg)
    print(f"\nFAILED: {args.path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
