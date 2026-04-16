#!/usr/bin/env python3
"""
Validate LLM-generated long-task-guide.md for structural completeness.

Checks that the guide contains all required workflow sections and critical
rule keywords. This prevents the LLM from accidentally omitting essential
workflow steps when generating a project-tailored guide.

Does NOT check exact content — only that required concepts are present.

Usage:
    python validate_guide.py <path/to/long-task-guide.md>

Exit codes:
    0 — all required sections present
    1 — one or more required sections missing
"""

import argparse
import re
import sys


# Required section concepts — each is (label, list of alternative patterns).
# The guide passes if at least ONE pattern from each group is found (case-insensitive).
REQUIRED_SECTIONS = [
    ("Test commands",
     [r"test-quiet", r"test-detail", r"test.*command"]),
    ("UT Style",
     [r"ut\s*style", r"\[test-framework\]", r"\[mock-style\]"]),
]


def validate_guide(path: str) -> list[str]:
    """
    Validate that a long-task-guide.md contains all required sections.

    Args:
        path: Path to the guide markdown file

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
    args = parser.parse_args()

    errors = validate_guide(args.guide_path)

    total_sections = len(REQUIRED_SECTIONS)

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
