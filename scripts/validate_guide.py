#!/usr/bin/env python3
"""
Validate LLM-generated long-task-guide.md for structural completeness.

Checks that the guide contains all required workflow sections and critical
rule keywords. This prevents the LLM from accidentally omitting essential
workflow steps when generating a project-tailored guide.

When --feature-list is provided and the project has UI features (any feature
with "ui": true), additionally checks for Chrome DevTools MCP sections.

Does NOT check exact content — only that required concepts are present.

Usage:
    python validate_guide.py <path/to/long-task-guide.md>
    python validate_guide.py <path/to/long-task-guide.md> --feature-list <path/to/feature-list.json>

Exit codes:
    0 — all required sections present
    1 — one or more required sections missing
"""

import argparse
import json
import re
import sys


# Required section concepts — each is (label, list of alternative patterns).
# The guide passes if at least ONE pattern from each group is found (case-insensitive).
REQUIRED_SECTIONS = [
    ("Orient / current state",
     [r"orient", r"current state", r"understand.*state"]),
    ("Bootstrap / restore environment",
     [r"bootstrap", r"restore.*environment", r"init\s*script", r"init\.sh"]),
    ("Config Gate / required configurations",
     [r"config\s*gate", r"required.config", r"check_configs"]),
    ("TDD Red / failing tests first",
     [r"tdd\s*red", r"failing\s*tests?\s*first", r"write.*failing.*test"]),
    ("TDD Green / implement to pass",
     [r"tdd\s*green", r"implement.*pass", r"minimal.*code.*pass"]),
    ("Coverage Gate",
     [r"coverage\s*gate", r"coverage.*threshold", r"line.*coverage.*branch.*coverage"]),
    ("TDD Refactor",
     [r"tdd\s*refactor", r"refactor.*keeping.*test", r"clean\s*up"]),
    ("Verification enforcement",
     [r"verification.*enforce", r"fresh.*evidence", r"never.*mark.*passing.*without"]),
    ("ST Test Cases / test case generation",
     [r"st\s*test\s*case", r"test\s*case\s*generat", r"29119", r"st-case", r"long-task-st-case"]),
    ("Inline Compliance Check",
     [r"inline.*compliance", r"compliance.*check", r"spec.*coverage", r"design.*compliance"]),
    ("Persist / save state / commit",
     [r"persist", r"save.*state", r"git.*commit", r"task-progress"]),
    ("Critical Rules",
     [r"critical\s*rule", r"iron\s*rule", r"must\s*never"]),
    ("Real Test Convention",
     [r"real\s*test\s*convention", r"real.test.identification", r"real.test.marker"]),
]


# Conditional sections — only required when the project has UI features (ui: true).
CHROME_DEVTOOLS_SECTIONS = [
    ("Chrome DevTools MCP / UI functional testing",
     [r"chrome\s*devtools", r"devtools\s*mcp", r"take_snapshot", r"functional\s*test.*ui"]),
]


def has_ui_features(feature_list_path: str) -> bool:
    """Check if a feature-list.json contains any feature with ui=true."""
    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        return any(
            isinstance(feat, dict) and feat.get("ui") is True
            for feat in features
        )
    except (json.JSONDecodeError, FileNotFoundError, Exception):
        return False


def validate_guide(path: str, feature_list_path: str = None) -> list[str]:
    """
    Validate that a long-task-guide.md contains all required sections.

    Args:
        path: Path to the guide markdown file
        feature_list_path: Optional path to feature-list.json; when provided
            and the project has UI features, Chrome DevTools sections are
            additionally required.

    Returns:
        List of error strings (empty = valid)
    """
    errors = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except Exception as e:
        return [f"Cannot read file: {e}"]

    if not content.strip():
        return ["Guide file is empty"]

    content_lower = content.lower()

    for label, patterns in REQUIRED_SECTIONS:
        found = False
        for pattern in patterns:
            if re.search(pattern, content_lower):
                found = True
                break
        if not found:
            errors.append(f"Missing required section: {label}")

    # Enforce env-guide.md §3 pointer — build/test/coverage commands must live
    # in env-guide.md (the single source of truth), not duplicated here.
    if not re.search(r"env-guide\.md", content, re.IGNORECASE):
        errors.append(
            "Missing reference to env-guide.md — the guide must delegate "
            "build/test/coverage commands to env-guide.md §3 rather than "
            "embedding them inline (single source of truth)."
        )

    # Conditional Chrome DevTools sections — only when project has UI features
    check_ui = False
    if feature_list_path:
        check_ui = has_ui_features(feature_list_path)

    if check_ui:
        for label, patterns in CHROME_DEVTOOLS_SECTIONS:
            found = False
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    found = True
                    break
            if not found:
                errors.append(f"Missing required section (UI project): {label}")

    return errors


FOOTER = "\n\n*by long task skill*\n"
FOOTER_MARKER = "*by long task skill*"


def _append_footer(path: str) -> None:
    """Append '*by long task skill*' to the guide if not already present."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if FOOTER_MARKER not in content:
            with open(path, "a", encoding="utf-8") as f:
                f.write(FOOTER)
            print("Appended footer: *by long task skill*")
    except Exception as e:
        print(f"Warning: could not append footer: {e}")


def main():
    parser = argparse.ArgumentParser(description="Validate LLM-generated long-task-guide.md")
    parser.add_argument("guide_path", help="Path to long-task-guide.md")
    parser.add_argument("--feature-list", default=None,
                        help="Path to feature-list.json; enables Chrome DevTools section "
                             "checks when UI features are present")
    args = parser.parse_args()

    errors = validate_guide(args.guide_path, args.feature_list)

    total_sections = len(REQUIRED_SECTIONS)
    if args.feature_list and has_ui_features(args.feature_list):
        total_sections += len(CHROME_DEVTOOLS_SECTIONS)

    _append_footer(args.guide_path)

    if errors:
        print(f"GUIDE VALIDATION FAILED — {len(errors)} issue(s):\n")
        for e in errors:
            print(f"  - {e}")
        print(f"\nTotal required sections: {total_sections}")
        print(f"Missing: {len(errors)}, Present: {total_sections - len(errors)}")
        sys.exit(1)
    else:
        print(f"VALID — all {total_sections} required sections present")
        sys.exit(0)


if __name__ == "__main__":
    main()
