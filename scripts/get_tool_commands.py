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

# ---------------------------------------------------------------------------
# Quiet commands — capture to temp file, then extract summary on demand.
#
# Architecture:  run → temp file → grep/tail to extract
#   *_quiet   : run + capture + print summary   (2-5 lines, always used first)
#   *_detail  : extract errors/failures from temp file (up to 30 lines, on failure)
#   Full file : Read /tmp/_build.log directly    (last resort)
#
# Why temp file beats piping:
#   - Zero information loss — full output preserved
#   - Repeatable extraction — grep the same file for different info
#   - Exit code preserved — $? after command
#   - On-demand detail — LLM decides what to read based on EXIT code
# ---------------------------------------------------------------------------

_BUILD_LOG = "/tmp/_build.log"

# grep patterns use bracket-prefixed patterns (\[ERROR\]) not bare keywords
# (error) — this distinguishes Maven diagnostics from application log content
# even when application logs contain words like "error" or "fail".
_MVN_GREP_SUMMARY = 'grep -E "Tests run:|BUILD " "{log}"'
_MVN_GREP_ERRORS  = 'grep -E "\\[ERROR\\]|\\[WARNING\\]|<<<" "{log}" | head -30'
_PIT_GREP_SUMMARY = 'grep -E "^>>|BUILD " "{log}"'

# JaCoCo coverage metric extraction from CSV (structured, encoding-safe)
_JACOCO_AWK = ("awk -F',' "
               "'NR>1{mi+=$4;ci+=$5;mb+=$6;cb+=$7} "
               "END{printf \"Line: %.1f%%, Branch: %.1f%%\\n\", "
               "100*ci/(mi+ci+0.001), 100*cb/(mb+cb+0.001)}' "
               "target/site/jacoco/jacoco.csv")
_JACOCO_AWK_DETAIL = ("awk -F',' "
                      "'NR>1 && ($4>0) "
                      "{printf \"%s: missed %d/%d lines, %d/%d branches\\n\","
                      "$3,$4,$4+$5,$6,$6+$7}' "
                      "target/site/jacoco/jacoco.csv")

_SUREFIRE_QUIET = "-Dsurefire.redirectTestOutputToFile=true"

# --- Per-tool quiet commands (run + capture + summary) ---

TEST_COMMANDS_QUIET = {
    "pytest":  f'pytest -q --tb=line >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"',
    "junit":   (f'mvn test -B -q {_SUREFIRE_QUIET} >"{_BUILD_LOG}" 2>&1; '
                f'echo "EXIT:$?"; '
                + _MVN_GREP_SUMMARY.format(log=_BUILD_LOG)),
    "jest":    f'npx jest --verbose=false >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"',
    "vitest":  f'npx vitest run --reporter=dot >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"',
    "ctest":   f'ctest --test-dir build --output-on-failure >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"',
    "gtest":   f'ctest --test-dir build --output-on-failure >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"',
}

# --- Per-tool detail commands (extract errors from temp file, on failure) ---

TEST_COMMANDS_DETAIL = {
    "pytest":  f'grep -iE "FAILED|ERROR|assert" "{_BUILD_LOG}" | head -30',
    "junit":   _MVN_GREP_ERRORS.format(log=_BUILD_LOG),
    "jest":    f'grep -iE "FAIL|Error|✕" "{_BUILD_LOG}" | head -30',
    "vitest":  f'grep -iE "FAIL|Error|✕" "{_BUILD_LOG}" | head -30',
    "ctest":   f'grep -iE "FAIL|Error" "{_BUILD_LOG}" | head -30',
    "gtest":   f'grep -iE "FAIL|Error" "{_BUILD_LOG}" | head -30',
}

COVERAGE_COMMANDS = {
    "pytest-cov": "pytest --cov=src --cov-branch --cov-report=term-missing",
    "jacoco":     "mvn test jacoco:report",
    "c8":         "npx vitest run --coverage",
    "c8-jest":    "npx c8 --branches 80 --lines 90 --reporter=text npx jest",
    "gcov":       "make CFLAGS=\"--coverage\" test && gcov -b src/*.c && lcov --capture -d . -o coverage.info && lcov --summary coverage.info",
}

COVERAGE_COMMANDS_QUIET = {
    "pytest-cov": (f'pytest --cov=src --cov-branch --cov-report=term-missing -q --tb=line >"{_BUILD_LOG}" 2>&1; '
                   f'echo "EXIT:$?"; tail -10 "{_BUILD_LOG}"'),
    "jacoco":     (f'mvn test jacoco:report -B -q {_SUREFIRE_QUIET} >"{_BUILD_LOG}" 2>&1; '
                   f'echo "EXIT:$?"; '
                   + _MVN_GREP_SUMMARY.format(log=_BUILD_LOG) + "; "
                   + _JACOCO_AWK),
    "c8":         f'npx vitest run --coverage --reporter=dot >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -10 "{_BUILD_LOG}"',
    "c8-jest":    f'npx c8 --branches 80 --lines 90 --reporter=text npx jest --verbose=false >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -10 "{_BUILD_LOG}"',
    "gcov":       (f'make CFLAGS="--coverage" test >"{_BUILD_LOG}" 2>&1 && '
                   f'lcov --capture -d . -o coverage.info >> "{_BUILD_LOG}" 2>&1 && '
                   f'lcov --summary coverage.info >> "{_BUILD_LOG}" 2>&1; '
                   f'echo "EXIT:$?"; tail -10 "{_BUILD_LOG}"'),
}

COVERAGE_COMMANDS_DETAIL = {
    "pytest-cov": f'grep -iE "FAILED|ERROR|assert" "{_BUILD_LOG}" | head -30',
    "jacoco":     (_MVN_GREP_ERRORS.format(log=_BUILD_LOG) + "; " + _JACOCO_AWK_DETAIL),
    "c8":         f'grep -iE "FAIL|Error" "{_BUILD_LOG}" | head -30',
    "c8-jest":    f'grep -iE "FAIL|Error" "{_BUILD_LOG}" | head -30',
    "gcov":       f'grep -iE "error|fail" "{_BUILD_LOG}" | head -30',
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

MUTATION_COMMANDS_QUIET = {
    "mutmut": {
        "full":    f'mutmut run >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"',
        "results": "mutmut results",
    },
    "pitest": {
        "full":    (f'mvn pitest:mutationCoverage -B -q >"{_BUILD_LOG}" 2>&1; '
                    f'echo "EXIT:$?"; '
                    + _PIT_GREP_SUMMARY.format(log=_BUILD_LOG)),
        "results": ("grep -c 'status=\"SURVIVED\"' target/pit-reports/*/mutations.xml; "
                    "grep -c 'status=\"KILLED\"' target/pit-reports/*/mutations.xml"),
    },
    "stryker": {
        "full":    f'npx stryker run --logLevel info >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -10 "{_BUILD_LOG}"',
        "results": "cat reports/mutation/mutation.json",
    },
    "mull": {
        "full":    f'mull-runner ./test-binary >"{_BUILD_LOG}" 2>&1; echo "EXIT:$?"; tail -10 "{_BUILD_LOG}"',
        "results": "cat mull-report.json",
    },
}

MUTATION_COMMANDS_DETAIL = {
    "mutmut": f'grep -iE "kill|surviv|fail|error" "{_BUILD_LOG}" | head -30',
    "pitest": _MVN_GREP_ERRORS.format(log=_BUILD_LOG),
    "stryker": f'grep -iE "Mutation|kill|surviv|fail|error" "{_BUILD_LOG}" | head -30',
    "mull":    f'grep -iE "kill|surviv|fail|error" "{_BUILD_LOG}" | head -30',
}

COMPILE_COMMANDS_QUIET = {
    "mvn":    (f'mvn compile -B -q >"{_BUILD_LOG}" 2>&1; '
               f'echo "EXIT:$?"; '
               f'grep -E "\\[ERROR\\]|BUILD " "{_BUILD_LOG}" | tail -10'),
    "gradle": (f'gradle compileJava -q >"{_BUILD_LOG}" 2>&1; '
               f'echo "EXIT:$?"; tail -5 "{_BUILD_LOG}"'),
}

COMPILE_COMMANDS_DETAIL = {
    "mvn":    f'grep "\\[ERROR\\]" "{_BUILD_LOG}" | head -30',
    "gradle": f'grep -iE "error|fail" "{_BUILD_LOG}" | head -30',
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

    # Quiet variants: capture to temp file + summary extraction
    test_cmd_quiet = TEST_COMMANDS_QUIET.get(test_fw, test_cmd)
    test_cmd_detail = TEST_COMMANDS_DETAIL.get(test_fw, "")
    cov_cmd_quiet = COVERAGE_COMMANDS_QUIET.get(cov_tool, cov_cmd)
    cov_cmd_detail = COVERAGE_COMMANDS_DETAIL.get(cov_tool, "")

    mut_quiet = MUTATION_COMMANDS_QUIET.get(mut_tool, {})
    mut_full_quiet = mut_quiet.get("full", mut_full)
    mut_results_quiet = mut_quiet.get("results", mut_results)
    mut_detail = MUTATION_COMMANDS_DETAIL.get(mut_tool, "")

    return {
        "test": test_cmd,
        "coverage": cov_cmd,
        "mutation_incremental": mut_inc,
        "mutation_feature": mut_feature,
        "mutation_full": mut_full,
        "mutation_results": mut_results,
        "mutation_show": mut_show,
        "test_quiet": test_cmd_quiet,
        "test_detail": test_cmd_detail,
        "coverage_quiet": cov_cmd_quiet,
        "coverage_detail": cov_cmd_detail,
        "mutation_full_quiet": mut_full_quiet,
        "mutation_full_detail": mut_detail,
        "mutation_results_quiet": mut_results_quiet,
        "build_log": _BUILD_LOG,
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
        f"[build-log]",
        f"  {cmds['build_log']}",
        "",
        f"[test-quiet]",
        f"  {cmds['test_quiet']}",
        "",
        f"[test-detail]",
        f"  {cmds['test_detail']}",
        "",
        f"[coverage-quiet]",
        f"  {cmds['coverage_quiet']}",
        "",
        f"[coverage-detail]",
        f"  {cmds['coverage_detail']}",
        "",
        f"[mutation-full-quiet]",
        f"  {cmds['mutation_full_quiet']}",
        "",
        f"[mutation-full-detail]",
        f"  {cmds['mutation_full_detail']}",
        "",
        f"[mutation-results-quiet]",
        f"  {cmds['mutation_results_quiet']}",
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
