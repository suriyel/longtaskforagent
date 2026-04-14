#!/usr/bin/env python3
"""
Read tech_stack and quality_gates from feature-list.json, output the exact
shell commands for test, coverage, and mutation tooling.

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
# Values = dict of command templates
#   {changed_files}  — placeholder the LLM fills with actual paths
#   {changed_classes} — placeholder for Java class patterns
# ---------------------------------------------------------------------------

TEST_COMMANDS = {
    "pytest":  "pytest",
    "junit":   "mvn test",
    "jest":    "npx jest",
    "vitest":  "npx vitest run",
    "ctest":   "ctest --test-dir build",
    "gtest":   "ctest --test-dir build",
}

COVERAGE_COMMANDS = {
    "pytest-cov": "pytest --cov=src --cov-branch --cov-report=term-missing",
    "jacoco":     "mvn test jacoco:report",
    "c8":         "npx vitest run --coverage",
    "c8-jest":    "npx c8 --branches 80 --lines 90 --reporter=text npx jest",
    "gcov":       "make CFLAGS=\"--coverage\" test && gcov -b src/*.c && lcov --capture -d . -o coverage.info && lcov --summary coverage.info",
}

MUTATION_COMMANDS = {
    "mutmut": {
        "incremental": "mutmut run --paths-to-mutate={changed_files}",
        "feature":     "mutmut run --paths-to-mutate={changed_files} --runner='{test_runner} {test_files}'",
        "full":        "mutmut run",
        "results":     "mutmut results",
        "show":        "mutmut show <mutant-id>",
    },
    "pitest": {
        "incremental": "mvn pitest:mutationCoverage -DtargetClasses={changed_classes}",
        "feature":     "mvn pitest:mutationCoverage -DtargetClasses={changed_classes} -DtargetTests={target_test_classes}",
        "full":        "mvn pitest:mutationCoverage",
        "results":     "cat target/pit-reports/*/mutations.xml",
        "show":        "open target/pit-reports/*/index.html",
    },
    "stryker": {
        "incremental": "npx stryker run --mutate='{changed_files}'",
        "feature":     "npx stryker run --mutate='{changed_files}' --coverageAnalysis perTest",
        "full":        "npx stryker run",
        "results":     "cat reports/mutation/mutation.json",
        "show":        "open reports/mutation/html/index.html",
    },
    "mull": {
        "incremental": "mull-runner ./test-binary --filters={changed_files}",
        "feature":     "mull-runner ./{feature_test_binary} --filters={changed_files}",
        "full":        "mull-runner ./test-binary",
        "results":     "cat mull-report.json",
        "show":        "cat mull-report.json",
    },
}


def get_commands(feature_list: dict) -> dict:
    """Extract tool commands from feature-list.json structure.

    Returns a dict with keys: test, coverage, mutation_incremental,
    mutation_full, mutation_results, mutation_show, thresholds, tech_stack.
    Values are concrete command strings (or 'UNKNOWN: <tool>' if unmapped).
    """
    ts = feature_list.get("tech_stack", {})
    qg = feature_list.get("quality_gates", {})

    test_fw = ts.get("test_framework", "TODO")
    cov_tool = ts.get("coverage_tool", "TODO")
    mut_tool = ts.get("mutation_tool", "TODO")

    test_cmd = TEST_COMMANDS.get(test_fw, f"UNKNOWN: {test_fw}")
    cov_cmd = COVERAGE_COMMANDS.get(cov_tool, f"UNKNOWN: {cov_tool}")

    mut_cmds = MUTATION_COMMANDS.get(mut_tool, {})
    mut_inc = mut_cmds.get("incremental", f"UNKNOWN: {mut_tool}")
    mut_feature = mut_cmds.get("feature", f"UNKNOWN: {mut_tool}")
    mut_full = mut_cmds.get("full", f"UNKNOWN: {mut_tool}")
    mut_results = mut_cmds.get("results", f"UNKNOWN: {mut_tool}")
    mut_show = mut_cmds.get("show", f"UNKNOWN: {mut_tool}")

    return {
        "test": test_cmd,
        "coverage": cov_cmd,
        "mutation_incremental": mut_inc,
        "mutation_feature": mut_feature,
        "mutation_full": mut_full,
        "mutation_results": mut_results,
        "mutation_show": mut_show,
        "thresholds": {
            "line_coverage_min": qg.get("line_coverage_min", 90),
            "branch_coverage_min": qg.get("branch_coverage_min", 80),
            "mutation_score_min": qg.get("mutation_score_min", 80),
            "mutation_full_threshold": qg.get("mutation_full_threshold", 100),
        },
        "tech_stack": {
            "language": ts.get("language", "TODO"),
            "test_framework": test_fw,
            "coverage_tool": cov_tool,
            "mutation_tool": mut_tool,
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
        f"Mutation tool: {ts['mutation_tool']}",
        "",
    ]
    lines += [
        f"[test]",
        f"  {cmds['test']}",
        "",
        f"[coverage]",
        f"  {cmds['coverage']}",
        "",
        f"[mutation-incremental]",
        f"  {cmds['mutation_incremental']}",
        "",
        f"[mutation-feature]",
        f"  {cmds['mutation_feature']}",
        "",
        f"[mutation-full]",
        f"  {cmds['mutation_full']}",
        "",
        f"[mutation-results]",
        f"  {cmds['mutation_results']}",
        "",
        f"[mutation-show]",
        f"  {cmds['mutation_show']}",
        "",
        f"[thresholds]",
        f"  line_coverage  >= {th['line_coverage_min']}%",
        f"  branch_coverage >= {th['branch_coverage_min']}%",
        f"  mutation_score  >= {th['mutation_score_min']}%",
        f"  mutation_full_threshold = {th['mutation_full_threshold']} features",
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
