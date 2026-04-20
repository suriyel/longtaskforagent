#!/usr/bin/env python3
"""
Read tech_stack and quality_gates from feature-list.json, output the exact
shell commands for test and coverage tooling.

Eliminates the need for the LLM to look up per-language command syntax.

Usage:
    python get_tool_commands.py feature-list.json
    python get_tool_commands.py feature-list.json --json
"""

import argparse
import json
import sys

# ---------------------------------------------------------------------------
# Command templates per tool
# Keys = lowercase tool names as they appear in tech_stack
# ---------------------------------------------------------------------------

TEST_COMMANDS = {
    "pytest":  "pytest",
    "junit":   "mvn test",
    "jest":    "npx jest",
    "vitest":  "npx vitest run",
    "ctest":   "ctest --test-dir build",
    "gtest":   "ctest --test-dir build",
    "go-test": "go test ./...",
}

COVERAGE_COMMANDS = {
    "pytest-cov": "pytest --cov=src --cov-branch --cov-report=term-missing",
    "jacoco":     "mvn test jacoco:report",
    "c8":         "npx vitest run --coverage",
    "c8-jest":    "npx c8 --branches 80 --lines 90 --reporter=text npx jest",
    "gcov":       "make CFLAGS=\"--coverage\" test && gcov -b src/*.c && lcov --capture -d . -o coverage.info && lcov --summary coverage.info",
    "go-cover":   "go test -coverprofile=coverage.out -covermode=atomic ./... && go tool cover -func=coverage.out",
}


def get_commands(feature_list: dict) -> dict:
    """Extract tool commands from feature-list.json structure.

    Returns a dict with keys: test, coverage, thresholds, tech_stack.
    Values are concrete command strings (or 'UNKNOWN: <tool>' if unmapped).
    """
    ts = feature_list.get("tech_stack", {})
    qg = feature_list.get("quality_gates", {})

    test_fw = ts.get("test_framework", "TODO")
    cov_tool = ts.get("coverage_tool", "TODO")

    test_cmd = TEST_COMMANDS.get(test_fw, f"UNKNOWN: {test_fw}")
    cov_cmd = COVERAGE_COMMANDS.get(cov_tool, f"UNKNOWN: {cov_tool}")

    return {
        "test": test_cmd,
        "coverage": cov_cmd,
        "thresholds": {
            "line_coverage_min": qg.get("line_coverage_min", 90),
            "branch_coverage_min": qg.get("branch_coverage_min", 80),
        },
        "tech_stack": {
            "language": ts.get("language", "TODO"),
            "test_framework": test_fw,
            "coverage_tool": cov_tool,
        },
    }


def format_text(cmds: dict) -> str:
    """Format commands as human-readable text output."""
    ts = cmds["tech_stack"]
    th = cmds["thresholds"]
    lines = [
        f"Language: {ts['language']}",
        f"Test framework: {ts['test_framework']}",
        f"Coverage tool: {ts['coverage_tool']}",
        "",
        f"[test]",
        f"  {cmds['test']}",
        "",
        f"[coverage]",
        f"  {cmds['coverage']}",
        "",
        f"[thresholds]",
        f"  line_coverage  >= {th['line_coverage_min']}%",
        f"  branch_coverage >= {th['branch_coverage_min']}%",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Output exact tool commands for a long-task project"
    )
    parser.add_argument("feature_list", help="Path to feature-list.json")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of text")
    args = parser.parse_args()

    try:
        with open(args.feature_list, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {args.feature_list}: {e}", file=sys.stderr)
        sys.exit(1)

    cmds = get_commands(data)

    if args.json:
        print(json.dumps(cmds, indent=2))
    else:
        print(format_text(cmds))


if __name__ == "__main__":
    main()
