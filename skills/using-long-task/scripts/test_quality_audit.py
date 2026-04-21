#!/usr/bin/env python3
"""
Test quality audit for iron-law rules R2/R3/R4/R6/R8/R9.

AST-level scan of pytest-style Python test files. Computes:
- R2 negative_ratio (negative tests / total tests) >= 0.40
- R3 low_value_ratio (low-value asserts / total asserts) <= 0.20
- R4 WRONG_IMPL comment presence per test function
- R6 AAA comments (# arrange / # act / # assert) per test function
- R8 reflection usage in test code (PowerMock-style / setattr on private)
- R9 direct access to underscore-prefixed members of tested objects

Usage:
    python test_quality_audit.py --target tests/
    python test_quality_audit.py --target tests/test_foo.py --feature 3
    python test_quality_audit.py --target tests/ --baseline

Exit codes:
    0 — pass (all thresholds met); also used for --baseline
    1 — fail (any threshold breached and file not in baseline)
    2 — script error (bad args, parse error, IO failure)

Report:
    Written to docs/reports/test_quality_<feature_id>.json (or stdout when
    --feature is omitted). JSON schema:
    {
      "verdict": "pass" | "fail",
      "negative_ratio": float,
      "low_value_ratio": float,
      "r4_missing": int,
      "r6_missing": int,
      "r8_violations": int,
      "r9_violations": int,
      "per_file": {"path": {...}},
      "violations": [{"file": "...", "line": n, "rule": "R3", "msg": "..."}]
    }
"""

import argparse
import ast
import json
import os
import re
import sys
from typing import Any


def _force_utf8_io() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


NEG_NAME_RE = re.compile(r"_(error|rejects|invalid|fails|raises|denies|forbidden|timeout|refuses)_")
HTTP_ERR_CODES = {400, 401, 402, 403, 404, 405, 408, 409, 410, 413, 415, 422, 429,
                  500, 502, 503, 504}
WRONG_IMPL_RE = re.compile(r"#\s*WRONG_IMPL\s*:")
AAA_TAGS = ("arrange", "act", "assert")

R8_PY_DANGEROUS_CALLS = {"setattr", "delattr"}
R8_PY_DANGEROUS_ATTRS = {"__dict__", "__setattr__", "__delattr__"}
R8_PY_DANGEROUS_IMPORTS = {"importlib", "ctypes"}

R9_ATTR_ALLOWLIST = {
    "_fields", "_replace", "_asdict", "_make",
    "_pytest", "_request", "_items",
    "_called_with", "_mock_name", "_mock_children",
}


def _iter_test_files(target: str) -> list[str]:
    if os.path.isfile(target):
        return [target] if target.endswith(".py") else []
    out: list[str] = []
    for root, _, files in os.walk(target):
        for name in files:
            if name.startswith("test_") and name.endswith(".py"):
                out.append(os.path.join(root, name))
    return sorted(out)


def _parse_file(path: str) -> tuple[ast.Module, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    return ast.parse(src, filename=path), src.splitlines()


def _test_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    out: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            out.append(node)
    return out


def _function_body_lines(func: ast.FunctionDef, src_lines: list[str]) -> list[str]:
    start = func.body[0].lineno - 1 if func.body else func.lineno
    end = (func.end_lineno or func.lineno) if hasattr(func, "end_lineno") else len(src_lines)
    return src_lines[start:end]


def _comments_in_function(func: ast.FunctionDef, src_lines: list[str]) -> list[str]:
    fn_start = func.lineno - 1
    fn_end = (func.end_lineno or func.lineno)
    return [ln.strip() for ln in src_lines[fn_start:fn_end] if ln.strip().startswith("#")]


def _is_neg_name(fn_name: str) -> bool:
    return bool(NEG_NAME_RE.search(fn_name))


def _has_pytest_raises(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.With):
            for item in node.items:
                ctx = item.context_expr
                if isinstance(ctx, ast.Call) and _call_name(ctx) in {"pytest.raises", "raises"}:
                    return True
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in {"pytest.raises", "self.assertRaises", "assertRaises",
                        "self.assertRaisesRegex", "assertRaisesRegex"}:
                return True
    return False


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = [func.attr]
        cur: Any = func.value
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def _asserts_http_error(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Compare):
            left = node.left
            if isinstance(left, ast.Attribute) and left.attr in {"status_code", "status"}:
                for comp in node.comparators:
                    if isinstance(comp, ast.Constant) and isinstance(comp.value, int):
                        if comp.value in HTTP_ERR_CODES:
                            return True
                    if isinstance(comp, (ast.Tuple, ast.List, ast.Set)):
                        for elt in comp.elts:
                            if isinstance(elt, ast.Constant) and elt.value in HTTP_ERR_CODES:
                                return True
    return False


def _asserts_empty_or_none(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if not isinstance(node, ast.Assert):
            continue
        expr = node.test
        if isinstance(expr, ast.Compare):
            for comp in expr.comparators:
                if isinstance(comp, ast.Constant) and comp.value is None:
                    return True
                if isinstance(comp, (ast.List, ast.Tuple, ast.Dict, ast.Set)) and not _has_elts(comp):
                    return True
                if isinstance(comp, ast.Constant) and comp.value in ("", 0, False):
                    return True
    return False


def _has_elts(node: ast.expr) -> bool:
    for name in ("elts", "keys"):
        if hasattr(node, name) and getattr(node, name):
            return True
    return False


def _classify_assert(node: ast.Assert) -> str:
    """Return 'low_value' or 'ok'."""
    expr = node.test

    if isinstance(expr, ast.Constant):
        return "low_value"
    if isinstance(expr, ast.Name):
        return "low_value"
    if isinstance(expr, ast.Attribute):
        return "low_value"

    if isinstance(expr, ast.Compare):
        left = expr.left
        ops = expr.ops
        comparators = expr.comparators
        if (len(ops) == 1 and isinstance(ops[0], ast.IsNot)
                and len(comparators) == 1
                and isinstance(comparators[0], ast.Constant)
                and comparators[0].value is None):
            return "low_value"
        if (len(ops) == 1 and isinstance(ops[0], ast.Gt)
                and isinstance(left, ast.Call) and _call_name(left) == "len"
                and len(comparators) == 1
                and isinstance(comparators[0], ast.Constant)
                and comparators[0].value == 0):
            return "low_value"
        if (len(ops) == 1 and isinstance(ops[0], ast.NotEq)
                and isinstance(left, ast.Call) and _call_name(left) == "len"
                and len(comparators) == 1
                and isinstance(comparators[0], ast.Constant)
                and comparators[0].value == 0):
            return "low_value"
        if len(ops) == 1 and isinstance(ops[0], ast.In):
            return "low_value"

    if isinstance(expr, ast.Call):
        name = _call_name(expr)
        if name == "isinstance":
            return "low_value"
        if name == "bool":
            return "low_value"
        if name == "len":
            return "low_value"

    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return "ok"

    return "ok"


def _has_wrong_impl(comments: list[str]) -> bool:
    return any(WRONG_IMPL_RE.search(c) for c in comments)


def _aaa_missing(comments: list[str]) -> list[str]:
    missing: list[str] = []
    joined = " ".join(comments).lower()
    for tag in AAA_TAGS:
        if f"# {tag}" not in joined and f"#{tag}" not in joined:
            missing.append(tag)
    return missing


def _r8_violations_in_function(func: ast.FunctionDef) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in R8_PY_DANGEROUS_CALLS and node.args:
                arg = node.args[1] if len(node.args) >= 2 else None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("_"):
                    hits.append((node.lineno, f"{name}(obj, '{arg.value}') — reflection on private"))
            if name == "getattr" and len(node.args) >= 2:
                arg = node.args[1]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("_"):
                    hits.append((node.lineno, f"getattr(obj, '{arg.value}') — reflection on private"))
        if isinstance(node, ast.Attribute) and node.attr in R8_PY_DANGEROUS_ATTRS:
            hits.append((node.lineno, f"access to {node.attr}"))
    return hits


def _r8_violations_module_imports(tree: ast.Module) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in R8_PY_DANGEROUS_IMPORTS:
                    hits.append((node.lineno, f"import {alias.name}"))
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in R8_PY_DANGEROUS_IMPORTS:
                hits.append((node.lineno, f"from {node.module} import ..."))
    return hits


def _collect_module_aliases(tree: ast.Module) -> set[str]:
    """Names that refer to imported modules — access on them is module-level
    helper access (R9 tolerated), not instance private member access."""
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases.add(alias.asname or alias.name.split(".")[0])
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases.add(alias.asname or alias.name)
    return aliases


def _r9_violations_in_function(func: ast.FunctionDef,
                               module_aliases: set[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Attribute):
            attr = node.attr
            if attr.startswith("_") and not (attr.startswith("__") and attr.endswith("__")):
                if attr in R9_ATTR_ALLOWLIST:
                    continue
                owner = node.value
                if isinstance(owner, ast.Name) and owner.id in {"self", "cls", "pytest", "_pytest"}:
                    continue
                if isinstance(owner, ast.Name) and owner.id in module_aliases:
                    continue
                hits.append((node.lineno, f".{attr} — private member access"))
    return hits


def _is_negative_test(func: ast.FunctionDef) -> bool:
    if _is_neg_name(func.name):
        return True
    if _has_pytest_raises(func):
        return True
    if _asserts_http_error(func):
        return True
    if _asserts_empty_or_none(func):
        return True
    return False


def _audit_file(path: str) -> dict[str, Any]:
    tree, src_lines = _parse_file(path)
    funcs = _test_functions(tree)
    module_aliases = _collect_module_aliases(tree)

    total_tests = len(funcs)
    negative_tests = 0
    total_asserts = 0
    low_value_asserts = 0
    r4_missing = 0
    r6_missing = 0
    r8_violations: list[tuple[int, str]] = list(_r8_violations_module_imports(tree))
    r9_violations: list[tuple[int, str]] = []
    violations: list[dict[str, Any]] = []

    for v_line, v_msg in r8_violations:
        violations.append({"file": path, "line": v_line, "rule": "R8", "msg": v_msg})

    for func in funcs:
        comments = _comments_in_function(func, src_lines)

        if _is_negative_test(func):
            negative_tests += 1

        fn_asserts = 0
        fn_low = 0
        for node in ast.walk(func):
            if isinstance(node, ast.Assert):
                fn_asserts += 1
                if _classify_assert(node) == "low_value":
                    fn_low += 1
                    violations.append({
                        "file": path, "line": node.lineno, "rule": "R3",
                        "msg": f"low-value assert in {func.name}",
                    })

        total_asserts += fn_asserts
        low_value_asserts += fn_low

        if fn_asserts == 0 and not _has_pytest_raises(func):
            violations.append({
                "file": path, "line": func.lineno, "rule": "R3",
                "msg": f"{func.name} has no asserts and no pytest.raises",
            })
            low_value_asserts += 1
            total_asserts += 1

        if not _has_wrong_impl(comments):
            r4_missing += 1
            violations.append({
                "file": path, "line": func.lineno, "rule": "R4",
                "msg": f"{func.name} missing # WRONG_IMPL: comment",
            })

        aaa_miss = _aaa_missing(comments)
        if aaa_miss:
            r6_missing += 1
            violations.append({
                "file": path, "line": func.lineno, "rule": "R6",
                "msg": f"{func.name} missing AAA tags: {','.join(aaa_miss)}",
            })

        for r8_line, r8_msg in _r8_violations_in_function(func):
            r8_violations.append((r8_line, r8_msg))
            violations.append({"file": path, "line": r8_line, "rule": "R8", "msg": r8_msg})

        for r9_line, r9_msg in _r9_violations_in_function(func, module_aliases):
            r9_violations.append((r9_line, r9_msg))
            violations.append({"file": path, "line": r9_line, "rule": "R9", "msg": r9_msg})

    return {
        "total_tests": total_tests,
        "negative_tests": negative_tests,
        "total_asserts": total_asserts,
        "low_value_asserts": low_value_asserts,
        "r4_missing": r4_missing,
        "r6_missing": r6_missing,
        "r8_violations": len(r8_violations),
        "r9_violations": len(r9_violations),
        "violations": violations,
    }


def _aggregate(per_file: dict[str, dict[str, Any]]) -> dict[str, Any]:
    total_tests = sum(f["total_tests"] for f in per_file.values())
    negative_tests = sum(f["negative_tests"] for f in per_file.values())
    total_asserts = sum(f["total_asserts"] for f in per_file.values())
    low_value_asserts = sum(f["low_value_asserts"] for f in per_file.values())
    all_violations: list[dict[str, Any]] = []
    for f in per_file.values():
        all_violations.extend(f["violations"])

    negative_ratio = (negative_tests / total_tests) if total_tests else 0.0
    low_value_ratio = (low_value_asserts / total_asserts) if total_asserts else 0.0

    return {
        "total_tests": total_tests,
        "negative_ratio": round(negative_ratio, 4),
        "low_value_ratio": round(low_value_ratio, 4),
        "r4_missing": sum(f["r4_missing"] for f in per_file.values()),
        "r6_missing": sum(f["r6_missing"] for f in per_file.values()),
        "r8_violations": sum(f["r8_violations"] for f in per_file.values()),
        "r9_violations": sum(f["r9_violations"] for f in per_file.values()),
        "violations": all_violations,
    }


def _verdict(agg: dict[str, Any], total_tests_threshold: int = 1) -> str:
    if agg["total_tests"] < total_tests_threshold:
        return "pass"
    if agg["negative_ratio"] < 0.40:
        return "fail"
    if agg["low_value_ratio"] > 0.20:
        return "fail"
    if agg["r4_missing"] > 0:
        return "fail"
    if agg["r6_missing"] > 0:
        return "fail"
    if agg["r8_violations"] > 0:
        return "fail"
    if agg["r9_violations"] > 0:
        return "fail"
    return "pass"


def _load_baseline(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("exempt_files", []))


def _write_baseline(path: str, files: list[str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"exempt_files": sorted(files)}, f, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    _force_utf8_io()
    parser = argparse.ArgumentParser(description="Test quality audit for iron-law rules.")
    parser.add_argument("--target", default="tests",
                        help="file or directory (default: tests)")
    parser.add_argument("--feature", default=None, help="feature id for report naming")
    parser.add_argument("--baseline", action="store_true",
                        help="generate baseline exemption list and exit 0")
    parser.add_argument("--baseline-file", default="docs/reports/test_quality_baseline.json",
                        help="baseline JSON path")
    parser.add_argument("--report-dir", default="docs/reports")
    parser.add_argument("--json", action="store_true", help="also print JSON to stdout")
    args = parser.parse_args(argv)

    files = _iter_test_files(args.target)
    if not files:
        print(f"No test files under {args.target}", file=sys.stderr)
        return 2

    per_file: dict[str, dict[str, Any]] = {}
    try:
        for path in files:
            per_file[path] = _audit_file(path)
    except SyntaxError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 2

    agg = _aggregate(per_file)

    if args.baseline:
        failing = [p for p, f in per_file.items() if _verdict(_aggregate({p: f})) == "fail"]
        _write_baseline(args.baseline_file, failing)
        print(f"Baseline written: {args.baseline_file} ({len(failing)} files exempted)")
        return 0

    exempt = _load_baseline(args.baseline_file)
    filtered = {p: f for p, f in per_file.items() if p not in exempt}
    agg_filtered = _aggregate(filtered) if filtered else agg
    verdict = _verdict(agg_filtered)

    report = {
        "verdict": verdict,
        "negative_ratio": agg_filtered["negative_ratio"],
        "low_value_ratio": agg_filtered["low_value_ratio"],
        "r4_missing": agg_filtered["r4_missing"],
        "r6_missing": agg_filtered["r6_missing"],
        "r8_violations": agg_filtered["r8_violations"],
        "r9_violations": agg_filtered["r9_violations"],
        "total_tests": agg_filtered["total_tests"],
        "exempted_files": sorted(set(per_file) & exempt),
        "per_file": {p: {k: v for k, v in f.items() if k != "violations"} for p, f in per_file.items()},
        "violations": agg_filtered["violations"],
    }

    if args.feature:
        os.makedirs(args.report_dir, exist_ok=True)
        out_path = os.path.join(args.report_dir, f"test_quality_{args.feature}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report: {out_path}")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"verdict={verdict} negative_ratio={agg_filtered['negative_ratio']} "
              f"low_value_ratio={agg_filtered['low_value_ratio']} "
              f"r4_missing={agg_filtered['r4_missing']} r6_missing={agg_filtered['r6_missing']} "
              f"r8={agg_filtered['r8_violations']} r9={agg_filtered['r9_violations']} "
              f"total_tests={agg_filtered['total_tests']}")

    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
