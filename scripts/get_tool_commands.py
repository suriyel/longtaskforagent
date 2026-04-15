#!/usr/bin/env python3
"""
Read tech_stack and quality_gates from feature-list.json, output the exact
shell commands for test, coverage, and mutation tooling.

Eliminates the need for the LLM to look up per-language command syntax.

Quiet/detail commands use a declarative (cmd, instruction) format:
  cmd         — the cross-platform tool invocation (mvn, pytest, npx …)
  instruction — what to do with the output (capture, extract, tail …)
The executing LLM composes the shell-appropriate pipeline at runtime.

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
# Quiet commands — (cmd, instruction) tuples.
#
# Architecture:  run → temp file → extract summary on demand
#   *_quiet   : (cmd, instruction) — run + capture + print summary
#   *_detail  : instruction string — extract errors/failures from temp file
#   Full file : read the temp file directly (last resort)
#
# The executing LLM translates the instruction to the appropriate shell:
#   bash:       grep -E "pattern" file | head -30
#   powershell: Select-String -Path file -Pattern 'pattern' | Select-Object -First 30
#
# Why temp file beats piping:
#   - Zero information loss — full output preserved
#   - Repeatable extraction — search the same file for different info
#   - Exit code preserved
#   - On-demand detail — LLM decides what to read based on exit code
# ---------------------------------------------------------------------------

_SUREFIRE_QUIET = "-Dsurefire.redirectTestOutputToFile=true"

# --- Per-tool quiet commands (cmd + instruction) ---

TEST_COMMANDS_QUIET = {
    "pytest": (
        "pytest -q --tb=line",
        "capture output to temp file; print exit code; show last 5 lines of temp file",
    ),
    "junit": (
        f"mvn test -B -q {_SUREFIRE_QUIET}",
        "capture output to temp file; print exit code; "
        "extract lines containing 'Tests run:' or 'BUILD '",
    ),
    "jest": (
        "npx jest --verbose=false",
        "capture output to temp file; print exit code; show last 5 lines of temp file",
    ),
    "vitest": (
        "npx vitest run --reporter=dot",
        "capture output to temp file; print exit code; show last 5 lines of temp file",
    ),
    "ctest": (
        "ctest --test-dir build --output-on-failure",
        "capture output to temp file; print exit code; show last 5 lines of temp file",
    ),
    "gtest": (
        "ctest --test-dir build --output-on-failure",
        "capture output to temp file; print exit code; show last 5 lines of temp file",
    ),
}

# --- Per-tool detail commands (extract errors from temp file, on failure) ---

TEST_COMMANDS_DETAIL = {
    "pytest":  "search temp file for 'FAILED', 'ERROR', or 'assert' (case-insensitive); show first 30 matches",
    "junit":   "search temp file for '[ERROR]', '[WARNING]', or '<<<'; show first 30 matches",
    "jest":    "search temp file for 'FAIL', 'Error', or '\u2715' (case-insensitive); show first 30 matches",
    "vitest":  "search temp file for 'FAIL', 'Error', or '\u2715' (case-insensitive); show first 30 matches",
    "ctest":   "search temp file for 'FAIL' or 'Error' (case-insensitive); show first 30 matches",
    "gtest":   "search temp file for 'FAIL' or 'Error' (case-insensitive); show first 30 matches",
}

COVERAGE_COMMANDS = {
    "pytest-cov": "pytest --cov=src --cov-branch --cov-report=term-missing",
    "jacoco":     "mvn test jacoco:report",
    "c8":         "npx vitest run --coverage",
    "c8-jest":    "npx c8 --branches 80 --lines 90 --reporter=text npx jest",
    "gcov":       "make CFLAGS=\"--coverage\" test && gcov -b src/*.c && lcov --capture -d . -o coverage.info && lcov --summary coverage.info",
}

COVERAGE_FEATURE_COMMANDS = {
    "pytest-cov": "pytest --cov={changed_modules} --cov-branch --cov-report=term-missing {test_files}",
    "jacoco":     "mvn test jacoco:report -Djacoco.includes={changed_classes_slash}",
    "c8":         "npx vitest run --coverage --coverage.include={changed_modules}",
    "c8-jest":    "npx c8 --include={changed_modules} --branches 80 --lines 90 --reporter=text npx jest {test_files}",
    "gcov":       "make CFLAGS=\"--coverage\" test && gcov -b {changed_files} && lcov --capture -d . -o coverage.info --include '{changed_modules}' && lcov --summary coverage.info",
}

COVERAGE_COMMANDS_QUIET = {
    "pytest-cov": (
        "pytest --cov=src --cov-branch --cov-report=term-missing -q --tb=line",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
    "jacoco": (
        f"mvn test jacoco:report -B -q {_SUREFIRE_QUIET}",
        "capture output to temp file; print exit code; "
        "extract lines containing 'Tests run:' or 'BUILD '; "
        "then read target/site/jacoco/jacoco.csv — aggregate "
        "INSTRUCTION_MISSED, INSTRUCTION_COVERED, BRANCH_MISSED, BRANCH_COVERED columns, "
        "print 'Line: X.X%, Branch: X.X%'",
    ),
    "c8": (
        "npx vitest run --coverage --reporter=dot",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
    "c8-jest": (
        "npx c8 --branches 80 --lines 90 --reporter=text npx jest --verbose=false",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
    "gcov": (
        "make CFLAGS=\"--coverage\" test && lcov --capture -d . -o coverage.info && lcov --summary coverage.info",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
}

COVERAGE_FEATURE_COMMANDS_QUIET = {
    "pytest-cov": (
        "pytest --cov={changed_modules} --cov-branch --cov-report=term-missing -q --tb=line {test_files}",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
    "jacoco": (
        f"mvn test jacoco:report -B -q {_SUREFIRE_QUIET} -Djacoco.includes={{changed_classes_slash}}",
        "capture output to temp file; print exit code; "
        "extract lines containing 'Tests run:' or 'BUILD '; "
        "then read target/site/jacoco/jacoco.csv — filter rows matching changed classes, "
        "aggregate INSTRUCTION_MISSED, INSTRUCTION_COVERED, BRANCH_MISSED, BRANCH_COVERED, "
        "print 'Line: X.X%, Branch: X.X%'",
    ),
    "c8": (
        "npx vitest run --coverage --coverage.include={changed_modules} --reporter=dot",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
    "c8-jest": (
        "npx c8 --include={changed_modules} --branches 80 --lines 90 --reporter=text npx jest --verbose=false {test_files}",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
    "gcov": (
        "make CFLAGS=\"--coverage\" test && lcov --capture -d . -o coverage.info --include '{changed_modules}' && lcov --summary coverage.info",
        "capture output to temp file; print exit code; show last 10 lines of temp file",
    ),
}

COVERAGE_FEATURE_COMMANDS_DETAIL = {
    "pytest-cov": "search temp file for 'FAILED', 'ERROR', or lines with 0% coverage; show first 30 matches",
    "jacoco":     ("search temp file for '[ERROR]', '[WARNING]', or '<<<'; show first 30 matches; "
                   "then read target/site/jacoco/jacoco.csv — list changed classes where INSTRUCTION_MISSED > 0, "
                   "format: 'ClassName: missed X/Y lines, X/Y branches'"),
    "c8":         "search temp file for 'FAIL' or 'Error' (case-insensitive); show first 30 matches",
    "c8-jest":    "search temp file for 'FAIL' or 'Error' (case-insensitive); show first 30 matches",
    "gcov":       "search temp file for 'error' or 'fail' (case-insensitive); show first 30 matches",
}

COVERAGE_COMMANDS_DETAIL = {
    "pytest-cov": "search temp file for 'FAILED', 'ERROR', or 'assert' (case-insensitive); show first 30 matches",
    "jacoco":     ("search temp file for '[ERROR]', '[WARNING]', or '<<<'; show first 30 matches; "
                   "then read target/site/jacoco/jacoco.csv — list classes where INSTRUCTION_MISSED > 0, "
                   "format: 'ClassName: missed X/Y lines, X/Y branches'"),
    "c8":         "search temp file for 'FAIL' or 'Error' (case-insensitive); show first 30 matches",
    "c8-jest":    "search temp file for 'FAIL' or 'Error' (case-insensitive); show first 30 matches",
    "gcov":       "search temp file for 'error' or 'fail' (case-insensitive); show first 30 matches",
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
        "full": (
            "mutmut run",
            "capture output to temp file; print exit code; show last 5 lines of temp file",
        ),
        "feature": (
            "mutmut run --paths-to-mutate={changed_files} --runner='{test_runner} {test_files}'",
            "capture output to temp file; print exit code; show last 5 lines of temp file",
        ),
        "results": "mutmut results",
    },
    "pitest": {
        "full": (
            "mvn pitest:mutationCoverage -B -q",
            "capture output to temp file; print exit code; "
            "extract lines starting with '>>' or containing 'BUILD '",
        ),
        "feature": (
            "mvn pitest:mutationCoverage -B -q -DtargetClasses={changed_classes} -DtargetTests={target_test_classes}",
            "capture output to temp file; print exit code; "
            "extract lines starting with '>>' or containing 'BUILD '",
        ),
        "results": ("in target/pit-reports/*/mutations.xml, "
                    "count occurrences of status=\"SURVIVED\" and status=\"KILLED\""),
    },
    "stryker": {
        "full": (
            "npx stryker run --logLevel info",
            "capture output to temp file; print exit code; show last 10 lines of temp file",
        ),
        "feature": (
            "npx stryker run --mutate='{changed_files}' --coverageAnalysis perTest --logLevel info",
            "capture output to temp file; print exit code; show last 10 lines of temp file",
        ),
        "results": "read reports/mutation/mutation.json",
    },
    "mull": {
        "full": (
            "mull-runner ./test-binary",
            "capture output to temp file; print exit code; show last 10 lines of temp file",
        ),
        "feature": (
            "mull-runner ./{feature_test_binary} --filters={changed_files}",
            "capture output to temp file; print exit code; show last 10 lines of temp file",
        ),
        "results": "read mull-report.json",
    },
}

MUTATION_COMMANDS_DETAIL = {
    "mutmut":  "search temp file for 'kill', 'surviv', 'fail', or 'error' (case-insensitive); show first 30 matches",
    "pitest":  "search temp file for '[ERROR]', '[WARNING]', or '<<<'; show first 30 matches",
    "stryker": "search temp file for 'Mutation', 'kill', 'surviv', 'fail', or 'error' (case-insensitive); show first 30 matches",
    "mull":    "search temp file for 'kill', 'surviv', 'fail', or 'error' (case-insensitive); show first 30 matches",
}

COMPILE_COMMANDS_QUIET = {
    "mvn": (
        "mvn compile -B -q",
        "capture output to temp file; print exit code; "
        "extract lines containing '[ERROR]' or 'BUILD '; show last 10",
    ),
    "gradle": (
        "gradle compileJava -q",
        "capture output to temp file; print exit code; show last 5 lines of temp file",
    ),
}

COMPILE_COMMANDS_DETAIL = {
    "mvn":    "search temp file for '[ERROR]'; show first 30 matches",
    "gradle": "search temp file for 'error' or 'fail' (case-insensitive); show first 30 matches",
}


def _pack_quiet(raw):
    """Normalize a quiet entry to {"cmd": ..., "instruction": ...} dict.

    Accepts:
      - (cmd, instruction) tuple → {"cmd": cmd, "instruction": instruction}
      - plain string             → {"cmd": string, "instruction": "run directly"}
    """
    if isinstance(raw, tuple):
        return {"cmd": raw[0], "instruction": raw[1]}
    return {"cmd": raw, "instruction": "run directly"}


def _pack_detail(raw):
    """Normalize a detail entry to {"instruction": ...} dict.

    Accepts:
      - plain string → {"instruction": string}
      - empty / None → {"instruction": ""}
    """
    return {"instruction": raw if raw else ""}


def _pack_mutation_quiet(raw):
    """Normalize a mutation quiet entry (may be tuple, string, or nested dict)."""
    if isinstance(raw, dict):
        result = {}
        for k, v in raw.items():
            if isinstance(v, tuple):
                result[k] = {"cmd": v[0], "instruction": v[1]}
            else:
                result[k] = {"instruction": v}
        return result
    return _pack_quiet(raw)


def get_commands(feature_list: dict) -> dict:
    """Extract tool commands from feature-list.json structure.

    Returns a dict with keys: test, coverage, mutation_incremental,
    mutation_full, mutation_results, mutation_show, thresholds, tech_stack.
    Quiet/detail values are structured {"cmd": ..., "instruction": ...} dicts.
    Plain commands are concrete strings (or 'UNKNOWN: <tool>' if unmapped).
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

    # Quiet variants: (cmd, instruction) tuples → packed dicts
    test_quiet_raw = TEST_COMMANDS_QUIET.get(test_fw)
    test_cmd_quiet = _pack_quiet(test_quiet_raw) if test_quiet_raw else {"cmd": test_cmd, "instruction": "run directly"}
    test_cmd_detail = _pack_detail(TEST_COMMANDS_DETAIL.get(test_fw, ""))

    cov_quiet_raw = COVERAGE_COMMANDS_QUIET.get(cov_tool)
    cov_cmd_quiet = _pack_quiet(cov_quiet_raw) if cov_quiet_raw else {"cmd": cov_cmd, "instruction": "run directly"}
    cov_cmd_detail = _pack_detail(COVERAGE_COMMANDS_DETAIL.get(cov_tool, ""))

    mut_quiet_raw = MUTATION_COMMANDS_QUIET.get(mut_tool, {})
    mut_full_quiet_raw = mut_quiet_raw.get("full") if isinstance(mut_quiet_raw, dict) else None
    mut_full_quiet = _pack_quiet(mut_full_quiet_raw) if mut_full_quiet_raw else {"cmd": mut_full, "instruction": "run directly"}

    mut_results_quiet_raw = mut_quiet_raw.get("results") if isinstance(mut_quiet_raw, dict) else None
    if mut_results_quiet_raw:
        if isinstance(mut_results_quiet_raw, tuple):
            mut_results_quiet = {"cmd": mut_results_quiet_raw[0], "instruction": mut_results_quiet_raw[1]}
        else:
            mut_results_quiet = {"instruction": mut_results_quiet_raw}
    else:
        mut_results_quiet = {"cmd": mut_results, "instruction": "run directly"}

    mut_detail = _pack_detail(MUTATION_COMMANDS_DETAIL.get(mut_tool, ""))

    # Coverage feature-scoped variants
    cov_feature_cmd = COVERAGE_FEATURE_COMMANDS.get(cov_tool, f"UNKNOWN: {cov_tool}")
    cov_feature_quiet_raw = COVERAGE_FEATURE_COMMANDS_QUIET.get(cov_tool)
    cov_feature_quiet = _pack_quiet(cov_feature_quiet_raw) if cov_feature_quiet_raw else {"cmd": cov_feature_cmd, "instruction": "run directly"}
    cov_feature_detail = _pack_detail(COVERAGE_FEATURE_COMMANDS_DETAIL.get(cov_tool, ""))

    # Mutation feature-scoped quiet variant
    mut_feature_quiet_raw = mut_quiet_raw.get("feature") if isinstance(mut_quiet_raw, dict) else None
    mut_feature_quiet = _pack_quiet(mut_feature_quiet_raw) if mut_feature_quiet_raw else {"cmd": mut_feature, "instruction": "run directly"}

    # Compile quiet/detail (keyed by build tool, derived from language)
    lang = ts.get("language", "")
    build_tool = "mvn" if lang == "java" else "gradle" if lang == "kotlin" else None
    compile_quiet_raw = COMPILE_COMMANDS_QUIET.get(build_tool) if build_tool else None
    compile_quiet = _pack_quiet(compile_quiet_raw) if compile_quiet_raw else {}
    compile_detail = _pack_detail(COMPILE_COMMANDS_DETAIL.get(build_tool, "")) if build_tool else {"instruction": ""}

    return {
        "test": test_cmd,
        "coverage": cov_cmd,
        "coverage_feature": cov_feature_cmd,
        "mutation_incremental": mut_inc,
        "mutation_feature": mut_feature,
        "mutation_full": mut_full,
        "mutation_results": mut_results,
        "mutation_show": mut_show,
        "test_quiet": test_cmd_quiet,
        "test_detail": test_cmd_detail,
        "coverage_quiet": cov_cmd_quiet,
        "coverage_detail": cov_cmd_detail,
        "coverage_feature_quiet": cov_feature_quiet,
        "coverage_feature_detail": cov_feature_detail,
        "mutation_full_quiet": mut_full_quiet,
        "mutation_full_detail": mut_detail,
        "mutation_feature_quiet": mut_feature_quiet,
        "mutation_feature_detail": mut_detail,
        "mutation_results_quiet": mut_results_quiet,
        "compile_quiet": compile_quiet,
        "compile_detail": compile_detail,
        "thresholds": {
            "line_coverage_min": qg.get("line_coverage_min", 90),
            "branch_coverage_min": qg.get("branch_coverage_min", 80),
            "mutation_score_min": qg.get("mutation_score_min", 80),
            "mutation_full_threshold": qg.get("mutation_full_threshold", 5),
        },
        "tech_stack": {
            "language": ts.get("language", "TODO"),
            "test_framework": test_fw,
            "coverage_tool": cov_tool,
            "mutation_tool": mut_tool,
        },
    }


def _format_recipe(label: str, recipe) -> list:
    """Format a quiet/detail recipe for text output."""
    lines = [f"[{label}]"]
    if isinstance(recipe, dict):
        if recipe.get("cmd"):
            lines.append(f"  cmd: {recipe['cmd']}")
        if recipe.get("instruction"):
            lines.append(f"  instruction: {recipe['instruction']}")
    elif isinstance(recipe, str):
        lines.append(f"  {recipe}")
    else:
        lines.append(f"  {recipe}")
    return lines


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
        "[test]",
        f"  {cmds['test']}",
        "",
        "[coverage]",
        f"  {cmds['coverage']}",
        "",
        "[coverage-feature]",
        f"  {cmds['coverage_feature']}",
        "",
        "[mutation-incremental]",
        f"  {cmds['mutation_incremental']}",
        "",
        "[mutation-feature]",
        f"  {cmds['mutation_feature']}",
        "",
        "[mutation-full]",
        f"  {cmds['mutation_full']}",
        "",
        "[mutation-results]",
        f"  {cmds['mutation_results']}",
        "",
        "[mutation-show]",
        f"  {cmds['mutation_show']}",
        "",
    ]
    lines += _format_recipe("test-quiet", cmds["test_quiet"])
    lines.append("")
    lines += _format_recipe("test-detail", cmds["test_detail"])
    lines.append("")
    lines += _format_recipe("coverage-quiet", cmds["coverage_quiet"])
    lines.append("")
    lines += _format_recipe("coverage-detail", cmds["coverage_detail"])
    lines.append("")
    lines += _format_recipe("coverage-feature-quiet", cmds["coverage_feature_quiet"])
    lines.append("")
    lines += _format_recipe("coverage-feature-detail", cmds["coverage_feature_detail"])
    lines.append("")
    lines += _format_recipe("mutation-full-quiet", cmds["mutation_full_quiet"])
    lines.append("")
    lines += _format_recipe("mutation-full-detail", cmds["mutation_full_detail"])
    lines.append("")
    lines += _format_recipe("mutation-feature-quiet", cmds["mutation_feature_quiet"])
    lines.append("")
    lines += _format_recipe("mutation-feature-detail", cmds["mutation_feature_detail"])
    lines.append("")
    lines += _format_recipe("mutation-results-quiet", cmds["mutation_results_quiet"])
    lines.append("")
    if cmds.get("compile_quiet"):
        lines += _format_recipe("compile-quiet", cmds["compile_quiet"])
        lines.append("")
        lines += _format_recipe("compile-detail", cmds["compile_detail"])
        lines.append("")
    lines += [
        "[thresholds]",
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
