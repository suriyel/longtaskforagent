#!/usr/bin/env python3
"""
Unit tests for get_tool_commands.py

Tests command lookup from tech_stack and quality_gates in feature-list.json.
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "get_tool_commands.py")

# Also import get_commands directly for unit tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from get_tool_commands import (get_commands, format_text, MUTATION_COMMANDS,
                               TEST_COMMANDS_QUIET, TEST_COMMANDS_DETAIL,
                               COVERAGE_COMMANDS_QUIET, COVERAGE_COMMANDS_DETAIL,
                               MUTATION_COMMANDS_QUIET, MUTATION_COMMANDS_DETAIL,
                               COMPILE_COMMANDS_QUIET, COMPILE_COMMANDS_DETAIL)


def make_feature_list(language="python", test_fw="pytest", cov_tool="pytest-cov",
                      mut_tool="mutmut", line_cov=90, branch_cov=80, mut_score=80):
    """Build a minimal feature-list.json dict."""
    return {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {
            "language": language,
            "test_framework": test_fw,
            "coverage_tool": cov_tool,
            "mutation_tool": mut_tool,
        },
        "quality_gates": {
            "line_coverage_min": line_cov,
            "branch_coverage_min": branch_cov,
            "mutation_score_min": mut_score,
        },
        "features": [],
    }


def run_script(feature_list_path, extra_args=None):
    """Run get_tool_commands.py, return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, SCRIPT_PATH, feature_list_path]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# --- Unit tests for get_commands() ---

def test_python_commands():
    """Python tech stack should resolve to pytest/mutmut commands."""
    cmds = get_commands(make_feature_list("python", "pytest", "pytest-cov", "mutmut"))
    assert cmds["test"] == "pytest"
    assert "pytest --cov" in cmds["coverage"]
    assert "--cov-branch" in cmds["coverage"]
    assert "mutmut run --paths-to-mutate" in cmds["mutation_incremental"]
    assert cmds["mutation_full"] == "mutmut run"
    assert "mutation_feature" in cmds


def test_java_commands():
    """Java tech stack should resolve to mvn/pitest commands."""
    cmds = get_commands(make_feature_list("java", "junit", "jacoco", "pitest"))
    assert cmds["test"] == "mvn test"
    assert "jacoco" in cmds["coverage"]
    assert "pitest" in cmds["mutation_incremental"] or "DtargetClasses" in cmds["mutation_incremental"]
    assert "pitest" in cmds["mutation_full"] or "mutationCoverage" in cmds["mutation_full"]


def test_javascript_commands():
    """JavaScript tech stack should resolve to jest/c8-jest/stryker commands."""
    cmds = get_commands(make_feature_list("javascript", "jest", "c8-jest", "stryker"))
    assert cmds["test"] == "npx jest"
    assert "c8" in cmds["coverage"]
    assert "jest" in cmds["coverage"]
    assert "stryker" in cmds["mutation_incremental"]
    assert "stryker" in cmds["mutation_full"]


def test_typescript_commands():
    """TypeScript tech stack should resolve to vitest/stryker commands."""
    cmds = get_commands(make_feature_list("typescript", "vitest", "c8", "stryker"))
    assert "vitest" in cmds["test"]
    assert "coverage" in cmds["coverage"]
    assert "stryker" in cmds["mutation_incremental"]
    assert "stryker" in cmds["mutation_full"]


def test_c_commands():
    """C tech stack should resolve to ctest/gcov/mull commands."""
    cmds = get_commands(make_feature_list("c", "ctest", "gcov", "mull"))
    assert "ctest" in cmds["test"]
    assert "gcov" in cmds["coverage"]
    assert "mull" in cmds["mutation_full"]


def test_cpp_commands():
    """C++ tech stack should resolve to gtest/gcov/mull commands."""
    cmds = get_commands(make_feature_list("cpp", "gtest", "gcov", "mull"))
    assert "ctest" in cmds["test"]
    assert "gcov" in cmds["coverage"]
    assert "mull" in cmds["mutation_full"]


def test_unknown_tool_returns_unknown_prefix():
    """Unknown tool names should return 'UNKNOWN: <name>' instead of crashing."""
    cmds = get_commands(make_feature_list("rust", "cargo-test", "tarpaulin", "cargo-mutants"))
    assert cmds["test"].startswith("UNKNOWN:")
    assert cmds["coverage"].startswith("UNKNOWN:")
    assert cmds["mutation_full"].startswith("UNKNOWN:")


def test_thresholds_from_quality_gates():
    """Thresholds should come from quality_gates."""
    cmds = get_commands(make_feature_list(line_cov=85, branch_cov=75, mut_score=70))
    assert cmds["thresholds"]["line_coverage_min"] == 85
    assert cmds["thresholds"]["branch_coverage_min"] == 75
    assert cmds["thresholds"]["mutation_score_min"] == 70


def test_default_thresholds():
    """Missing quality_gates should fall back to defaults."""
    data = {"tech_stack": {"test_framework": "pytest", "coverage_tool": "pytest-cov",
                           "mutation_tool": "mutmut", "language": "python"}}
    cmds = get_commands(data)
    assert cmds["thresholds"]["line_coverage_min"] == 90
    assert cmds["thresholds"]["branch_coverage_min"] == 80
    assert cmds["thresholds"]["mutation_score_min"] == 80


def test_tech_stack_in_output():
    """Output should include the tech_stack metadata."""
    cmds = get_commands(make_feature_list("python", "pytest", "pytest-cov", "mutmut"))
    assert cmds["tech_stack"]["language"] == "python"
    assert cmds["tech_stack"]["test_framework"] == "pytest"


def test_mutation_feature_key_present():
    """All known mutation tools should have a mutation_feature command."""
    for tool_name in MUTATION_COMMANDS:
        assert "feature" in MUTATION_COMMANDS[tool_name], (
            f"Missing 'feature' key in MUTATION_COMMANDS['{tool_name}']"
        )


def test_mutation_feature_distinct_from_others():
    """mutation_feature should differ from incremental and full for all tools."""
    for lang, fw, cov, mut in [
        ("python", "pytest", "pytest-cov", "mutmut"),
        ("java", "junit", "jacoco", "pitest"),
        ("typescript", "vitest", "c8", "stryker"),
        ("c", "ctest", "gcov", "mull"),
    ]:
        cmds = get_commands(make_feature_list(lang, fw, cov, mut))
        assert cmds["mutation_feature"] != cmds["mutation_incremental"], (
            f"{mut}: mutation_feature should differ from incremental"
        )
        assert cmds["mutation_feature"] != cmds["mutation_full"], (
            f"{mut}: mutation_feature should differ from full"
        )


def test_unknown_tool_mutation_feature_returns_unknown():
    """Unknown mutation tool should return UNKNOWN for mutation_feature."""
    cmds = get_commands(make_feature_list("rust", "cargo-test", "tarpaulin", "cargo-mutants"))
    assert cmds["mutation_feature"].startswith("UNKNOWN:")


def test_mutation_full_threshold_default():
    """Default mutation_full_threshold should be 100."""
    data = {"tech_stack": {"test_framework": "pytest", "coverage_tool": "pytest-cov",
                           "mutation_tool": "mutmut", "language": "python"}}
    cmds = get_commands(data)
    assert cmds["thresholds"]["mutation_full_threshold"] == 100


def test_mutation_full_threshold_custom():
    """Custom mutation_full_threshold should be respected."""
    fl = make_feature_list()
    fl["quality_gates"]["mutation_full_threshold"] = 50
    cmds = get_commands(fl)
    assert cmds["thresholds"]["mutation_full_threshold"] == 50


def test_format_text_contains_sections():
    """Text format should contain all expected section labels."""
    cmds = get_commands(make_feature_list())
    text = format_text(cmds)
    assert "[test]" in text
    assert "[coverage]" in text
    assert "[mutation-incremental]" in text
    assert "[mutation-feature]" in text
    assert "[mutation-full]" in text
    assert "[mutation-results]" in text
    assert "[test-quiet]" in text
    assert "[test-detail]" in text
    assert "[coverage-quiet]" in text
    assert "[coverage-detail]" in text
    assert "[mutation-full-quiet]" in text
    assert "[mutation-full-detail]" in text
    assert "[mutation-results-quiet]" in text
    assert "[thresholds]" in text
    assert "mutation_full_threshold" in text


# --- Quiet recipe structure tests ---

def test_quiet_commands_are_tuples():
    """All quiet command entries should be (cmd, instruction) tuples."""
    for tool, entry in TEST_COMMANDS_QUIET.items():
        assert isinstance(entry, tuple), f"TEST_COMMANDS_QUIET['{tool}'] should be a tuple"
        assert len(entry) == 2, f"TEST_COMMANDS_QUIET['{tool}'] should have 2 elements"
        assert isinstance(entry[0], str), f"TEST_COMMANDS_QUIET['{tool}'][0] (cmd) should be str"
        assert isinstance(entry[1], str), f"TEST_COMMANDS_QUIET['{tool}'][1] (instruction) should be str"

    for tool, entry in COVERAGE_COMMANDS_QUIET.items():
        assert isinstance(entry, tuple), f"COVERAGE_COMMANDS_QUIET['{tool}'] should be a tuple"
        assert len(entry) == 2

    for tool, entries in MUTATION_COMMANDS_QUIET.items():
        assert isinstance(entries, dict), f"MUTATION_COMMANDS_QUIET['{tool}'] should be a dict"
        for key, entry in entries.items():
            if isinstance(entry, tuple):
                assert len(entry) == 2, f"MUTATION_COMMANDS_QUIET['{tool}']['{key}'] tuple should have 2 elements"

    for tool, entry in COMPILE_COMMANDS_QUIET.items():
        assert isinstance(entry, tuple), f"COMPILE_COMMANDS_QUIET['{tool}'] should be a tuple"
        assert len(entry) == 2


def test_detail_commands_are_strings():
    """All detail command entries should be plain instruction strings."""
    for tool, entry in TEST_COMMANDS_DETAIL.items():
        assert isinstance(entry, str), f"TEST_COMMANDS_DETAIL['{tool}'] should be a string"

    for tool, entry in COVERAGE_COMMANDS_DETAIL.items():
        assert isinstance(entry, str), f"COVERAGE_COMMANDS_DETAIL['{tool}'] should be a string"

    for tool, entry in MUTATION_COMMANDS_DETAIL.items():
        assert isinstance(entry, str), f"MUTATION_COMMANDS_DETAIL['{tool}'] should be a string"

    for tool, entry in COMPILE_COMMANDS_DETAIL.items():
        assert isinstance(entry, str), f"COMPILE_COMMANDS_DETAIL['{tool}'] should be a string"


def test_java_quiet_structured():
    """Java quiet commands should return structured {cmd, instruction} dicts."""
    cmds = get_commands(make_feature_list("java", "junit", "jacoco", "pitest"))
    # test_quiet
    assert isinstance(cmds["test_quiet"], dict)
    assert "mvn test" in cmds["test_quiet"]["cmd"]
    assert "capture" in cmds["test_quiet"]["instruction"]
    assert "exit code" in cmds["test_quiet"]["instruction"]
    assert "Tests run:" in cmds["test_quiet"]["instruction"]
    # coverage_quiet
    assert isinstance(cmds["coverage_quiet"], dict)
    assert "jacoco" in cmds["coverage_quiet"]["cmd"]
    assert "jacoco.csv" in cmds["coverage_quiet"]["instruction"]
    assert "INSTRUCTION_MISSED" in cmds["coverage_quiet"]["instruction"]
    # mutation_full_quiet
    assert isinstance(cmds["mutation_full_quiet"], dict)
    assert "pitest" in cmds["mutation_full_quiet"]["cmd"] or "mutationCoverage" in cmds["mutation_full_quiet"]["cmd"]
    assert ">>" in cmds["mutation_full_quiet"]["instruction"]


def test_java_detail_structured():
    """Java detail commands should return structured {instruction} dicts."""
    cmds = get_commands(make_feature_list("java", "junit", "jacoco", "pitest"))
    assert isinstance(cmds["test_detail"], dict)
    assert "[ERROR]" in cmds["test_detail"]["instruction"]
    assert "30" in cmds["test_detail"]["instruction"]
    assert isinstance(cmds["coverage_detail"], dict)
    assert "[ERROR]" in cmds["coverage_detail"]["instruction"]
    assert "jacoco.csv" in cmds["coverage_detail"]["instruction"]
    assert isinstance(cmds["mutation_full_detail"], dict)
    assert "instruction" in cmds["mutation_full_detail"]


def test_python_quiet_structured():
    """Python quiet should have cmd and instruction."""
    cmds = get_commands(make_feature_list("python", "pytest", "pytest-cov", "mutmut"))
    assert isinstance(cmds["test_quiet"], dict)
    assert "pytest" in cmds["test_quiet"]["cmd"]
    assert "last 5 lines" in cmds["test_quiet"]["instruction"]


def test_quiet_fallback_to_verbose():
    """Unknown tools should fall back to verbose command with 'run directly' instruction."""
    cmds = get_commands(make_feature_list("rust", "cargo-test", "tarpaulin", "cargo-mutants"))
    assert cmds["test_quiet"]["cmd"] == cmds["test"]
    assert cmds["test_quiet"]["instruction"] == "run directly"
    assert cmds["coverage_quiet"]["cmd"] == cmds["coverage"]
    assert cmds["coverage_quiet"]["instruction"] == "run directly"
    assert cmds["mutation_full_quiet"]["cmd"] == cmds["mutation_full"]
    assert cmds["mutation_full_quiet"]["instruction"] == "run directly"


def test_quiet_keys_in_output():
    """Output should include quiet, detail, and compile keys."""
    cmds = get_commands(make_feature_list())
    for key in ["test_quiet", "test_detail", "coverage_quiet", "coverage_detail",
                "mutation_full_quiet", "mutation_full_detail", "mutation_results_quiet"]:
        assert key in cmds, f"Missing key: {key}"
        assert isinstance(cmds[key], dict), f"{key} should be a dict"


def test_pitest_results_quiet():
    """PIT results-quiet should reference XML report with SURVIVED/KILLED."""
    cmds = get_commands(make_feature_list("java", "junit", "jacoco", "pitest"))
    instr = cmds["mutation_results_quiet"]["instruction"]
    assert "SURVIVED" in instr
    assert "KILLED" in instr


def test_no_bash_specific_in_quiet():
    """Quiet/detail commands should not contain bash-specific utilities."""
    import re
    # Use word-boundary patterns to avoid false positives (e.g. "missed" contains "sed")
    bash_patterns = [
        (re.compile(r'\bgrep\b'), "grep"),
        (re.compile(r'\btail\b'), "tail"),
        (re.compile(r'\bhead\b'), "head"),
        (re.compile(r'\bawk\b'), "awk"),
        (re.compile(r'\bsed\b'), "sed"),
    ]
    for lang, fw, cov, mut in [
        ("python", "pytest", "pytest-cov", "mutmut"),
        ("java", "junit", "jacoco", "pitest"),
        ("typescript", "vitest", "c8", "stryker"),
        ("c", "ctest", "gcov", "mull"),
    ]:
        cmds = get_commands(make_feature_list(lang, fw, cov, mut))
        for key in ["test_quiet", "test_detail", "coverage_quiet", "coverage_detail",
                     "mutation_full_quiet", "mutation_full_detail"]:
            recipe = cmds[key]
            if isinstance(recipe, dict):
                for field in ["cmd", "instruction"]:
                    val = recipe.get(field, "")
                    for regex, name in bash_patterns:
                        assert not regex.search(val), (
                            f"{key}.{field} for {lang} contains bash-specific '{name}': {val}"
                        )


def test_compile_quiet_wired_for_java():
    """Java projects should have compile_quiet/compile_detail in output."""
    cmds = get_commands(make_feature_list("java", "junit", "jacoco", "pitest"))
    assert cmds["compile_quiet"], "compile_quiet should be non-empty for Java"
    assert "mvn compile" in cmds["compile_quiet"]["cmd"]
    assert "capture" in cmds["compile_quiet"]["instruction"]
    assert cmds["compile_detail"]["instruction"], "compile_detail should have instruction for Java"
    assert "[ERROR]" in cmds["compile_detail"]["instruction"]


def test_compile_quiet_empty_for_python():
    """Python projects should have empty compile_quiet (no build step)."""
    cmds = get_commands(make_feature_list("python", "pytest", "pytest-cov", "mutmut"))
    assert cmds["compile_quiet"] == {}


def test_format_text_shows_cmd_and_instruction():
    """Text format should show cmd: and instruction: for quiet recipes."""
    cmds = get_commands(make_feature_list("java", "junit", "jacoco", "pitest"))
    text = format_text(cmds)
    assert "cmd:" in text
    assert "instruction:" in text
    # compile section should appear for Java
    assert "[compile-quiet]" in text
    assert "[compile-detail]" in text


# --- CLI integration tests ---

def test_cli_text_output():
    """CLI should output text format by default."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    try:
        json.dump(make_feature_list(), tmp)
        tmp.close()
        code, stdout, stderr = run_script(tmp.name)
        assert code == 0, f"Exit {code}: {stderr}"
        assert "[test]" in stdout
        assert "[coverage]" in stdout
        assert "pytest" in stdout
    finally:
        os.unlink(tmp.name)


def test_cli_json_output():
    """CLI --json should output valid JSON with structured quiet commands."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    try:
        json.dump(make_feature_list(), tmp)
        tmp.close()
        code, stdout, stderr = run_script(tmp.name, ["--json"])
        assert code == 0, f"Exit {code}: {stderr}"
        data = json.loads(stdout)
        assert "test" in data
        assert "coverage" in data
        assert "mutation_feature" in data
        assert "thresholds" in data
        assert "mutation_full_threshold" in data["thresholds"]
        # Verify quiet entries are structured dicts
        assert isinstance(data["test_quiet"], dict)
        assert "cmd" in data["test_quiet"]
        assert "instruction" in data["test_quiet"]
    finally:
        os.unlink(tmp.name)


def test_cli_json_java():
    """CLI --json for Java should include compile_quiet with cmd."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    try:
        json.dump(make_feature_list("java", "junit", "jacoco", "pitest"), tmp)
        tmp.close()
        code, stdout, stderr = run_script(tmp.name, ["--json"])
        assert code == 0, f"Exit {code}: {stderr}"
        data = json.loads(stdout)
        assert "compile_quiet" in data
        assert "cmd" in data["compile_quiet"]
        assert "mvn compile" in data["compile_quiet"]["cmd"]
    finally:
        os.unlink(tmp.name)


def test_cli_missing_file():
    """CLI should exit 1 for missing file."""
    code, _, stderr = run_script("/nonexistent/path.json")
    assert code == 1


def test_cli_invalid_json():
    """CLI should exit 1 for invalid JSON."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    try:
        tmp.write("not json")
        tmp.close()
        code, _, stderr = run_script(tmp.name)
        assert code == 1
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    tests = [
        test_python_commands,
        test_java_commands,
        test_javascript_commands,
        test_typescript_commands,
        test_c_commands,
        test_cpp_commands,
        test_unknown_tool_returns_unknown_prefix,
        test_thresholds_from_quality_gates,
        test_default_thresholds,
        test_tech_stack_in_output,
        test_mutation_feature_key_present,
        test_mutation_feature_distinct_from_others,
        test_unknown_tool_mutation_feature_returns_unknown,
        test_mutation_full_threshold_default,
        test_mutation_full_threshold_custom,
        test_format_text_contains_sections,
        test_quiet_commands_are_tuples,
        test_detail_commands_are_strings,
        test_java_quiet_structured,
        test_java_detail_structured,
        test_python_quiet_structured,
        test_quiet_fallback_to_verbose,
        test_quiet_keys_in_output,
        test_pitest_results_quiet,
        test_no_bash_specific_in_quiet,
        test_compile_quiet_wired_for_java,
        test_compile_quiet_empty_for_python,
        test_format_text_shows_cmd_and_instruction,
        test_cli_text_output,
        test_cli_json_output,
        test_cli_json_java,
        test_cli_missing_file,
        test_cli_invalid_json,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
