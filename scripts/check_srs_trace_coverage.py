#!/usr/bin/env python3
"""
Check SRS trace coverage — verify every requirement ID in a feature's
srs_trace appears literally in at least one test artifact (filename,
function name, docstring, comment, or assertion message).

Rationale:
    Quality Gates currently only validates coverage %. When SRS changes
    between feature cycles, tests that still pass full coverage may no
    longer anchor the new acceptance criteria. This gate catches that
    silent drift by requiring each FR-ID in a feature's srs_trace to be
    referenced somewhere in the test suite.

Matching semantics:
    For each ID in srs_trace (e.g. "FR-012"), search test artifacts for
    a word-boundary literal occurrence (case-insensitive). An FR-ID is
    considered covered when the literal ID OR any configured alias is
    found in:
      - test file path / filename,
      - test function name,
      - test function body (comments, docstrings, string literals),
      - file-level module docstring.

    Aliases may be declared per-feature in feature-list.json:
        features[i].srs_trace_aliases = {
            "FR-012": ["fr_012", "@srs FR-012"]
        }

Test file scope:
    1. If --test-files is passed, exactly those files are scanned.
    2. Else, files under tech_stack.language's test directory that
       reference the feature via `feature_ref_pattern` (same mechanism
       as check_real_tests.py) are used.
    3. Else, all test files under the test directory are scanned.

Usage:
    python check_srs_trace_coverage.py <feature-list.json>
    python check_srs_trace_coverage.py <feature-list.json> --feature 3
    python check_srs_trace_coverage.py <feature-list.json> \\
        --feature 3 --test-files tests/test_foo.py tests/test_bar.py
    python check_srs_trace_coverage.py <feature-list.json> --feature 3 --json

Exit codes:
    0 — every FR-ID in scope covered
    1 — at least one FR-ID uncovered
    2 — input error (missing file, malformed JSON, feature not found, ...)
"""

import argparse
import json
import os
import re
import sys


TEST_FILE_PATTERNS = {
    "python": re.compile(r"^test_.*\.py$|^.*_test\.py$"),
    "java": re.compile(r"^.*Test\.java$|^.*Tests\.java$"),
    "javascript": re.compile(r"^.*\.test\.(js|jsx)$|^.*\.spec\.(js|jsx)$"),
    "typescript": re.compile(r"^.*\.test\.(ts|tsx)$|^.*\.spec\.(ts|tsx)$"),
    "c": re.compile(r"^test_.*\.c$|^.*_test\.c$"),
    "cpp": re.compile(r"^test_.*\.cpp$|^.*_test\.cpp$"),
    "c++": re.compile(r"^test_.*\.cpp$|^.*_test\.cpp$"),
}

DEFAULT_FEATURE_REF_PATTERN = r"feature[_:\s#-]*{id}(?!\d)"


def find_test_files(test_dir, language):
    pattern = TEST_FILE_PATTERNS.get(language)
    if not pattern:
        pattern = re.compile(
            r"^test_.*\.\w+$|^.*_test\.\w+$|^.*Test\.\w+$|"
            r"^.*\.test\.\w+$|^.*\.spec\.\w+$"
        )

    files = []
    if not os.path.isdir(test_dir):
        return files
    for root, _dirs, names in os.walk(test_dir):
        for fname in sorted(names):
            if pattern.match(fname):
                files.append(os.path.join(root, fname))
    return files


def filter_files_by_feature_ref(files, feature_id, feature_ref_pattern):
    """Return files whose name or content references feature_id via pattern."""
    try:
        ref_re = re.compile(
            feature_ref_pattern.replace("{id}", str(feature_id)),
            re.IGNORECASE,
        )
    except re.error:
        return list(files)

    matched = []
    for fpath in files:
        if ref_re.search(os.path.basename(fpath)):
            matched.append(fpath)
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as fobj:
                content = fobj.read()
        except OSError:
            continue
        if ref_re.search(content):
            matched.append(fpath)
    return matched


def build_id_regex(fr_id, aliases):
    """Build a case-insensitive regex matching the FR-ID or any alias.

    The FR-ID is matched with word boundaries so FR-1 does not match
    FR-10. Hyphens inside the ID (e.g. the '-' in 'FR-001') are treated
    as interchangeable with underscores so Python test function names
    like ``test_fr_001_login`` still count as coverage for ``FR-001``.

    Aliases are matched as literal substrings (no word boundary) so
    aliases like "@srs FR-012" or " srs-login" work regardless of
    surrounding punctuation.
    """
    id_literal = re.escape(fr_id).replace(r"\-", r"[-_]")
    # Custom boundaries: hyphen and underscore are acceptable neighbors
    # (so `test_fr_001_login` matches FR-001), but alphanumerics are not
    # (so `FR-10` does not match FR-1, and `XFR-001` does not match
    # FR-001).
    parts = [r"(?<![A-Za-z0-9])" + id_literal + r"(?![A-Za-z0-9])"]
    for alias in aliases:
        if alias:
            parts.append(re.escape(alias))
    return re.compile("(?:" + "|".join(parts) + ")", re.IGNORECASE)


def find_coverage(fr_id, aliases, files, path_cache):
    """Return list of {file, evidence} for each file that covers fr_id."""
    id_re = build_id_regex(fr_id, aliases)
    hits = []
    for fpath in files:
        if id_re.search(os.path.basename(fpath)):
            hits.append({"file": fpath, "evidence": "filename"})
            continue
        if fpath not in path_cache:
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fobj:
                    path_cache[fpath] = fobj.read()
            except OSError:
                path_cache[fpath] = ""
        content = path_cache[fpath]
        m = id_re.search(content)
        if m:
            # Record line number of first hit for readable evidence
            line_no = content.count("\n", 0, m.start()) + 1
            hits.append({"file": fpath, "evidence": f"content:line{line_no}"})
    return hits


def check_feature(feat, all_test_files, feature_ref_pattern,
                  explicit_test_files, base_dir, path_cache):
    """Check a single feature's srs_trace coverage."""
    fid = feat.get("id")
    srs_trace = feat.get("srs_trace", []) or []
    aliases_map = feat.get("srs_trace_aliases", {}) or {}

    if explicit_test_files is not None:
        scope_files = list(explicit_test_files)
    else:
        scope_files = filter_files_by_feature_ref(
            all_test_files, fid, feature_ref_pattern
        )
        if not scope_files:
            scope_files = list(all_test_files)

    per_id = {}
    for fr_id in srs_trace:
        aliases = aliases_map.get(fr_id, []) or []
        hits = find_coverage(fr_id, aliases, scope_files, path_cache)
        per_id[fr_id] = [
            {"file": os.path.relpath(h["file"], base_dir),
             "evidence": h["evidence"]}
            for h in hits
        ]

    uncovered = [fr for fr, h in per_id.items() if not h]
    return {
        "feature_id": fid,
        "title": feat.get("title", "?"),
        "srs_trace": list(srs_trace),
        "scope_files": [os.path.relpath(f, base_dir) for f in scope_files],
        "coverage": per_id,
        "uncovered_fr_ids": uncovered,
    }


def check(feature_list_path, feature_id=None, explicit_test_files=None):
    """Main entry. Returns a result dict."""
    result = {
        "verdict": "FAIL",
        "project": "",
        "language": "",
        "test_dir": "",
        "features_checked": 0,
        "per_feature": [],
        "issues": [],
        "uncovered_total": 0,
    }

    if not os.path.isfile(feature_list_path):
        result["issues"].append(f"File not found: {feature_list_path}")
        return result

    try:
        with open(feature_list_path, "r", encoding="utf-8") as fobj:
            data = json.load(fobj)
    except (json.JSONDecodeError, OSError) as e:
        result["issues"].append(f"Failed to read {feature_list_path}: {e}")
        return result
    if not isinstance(data, dict):
        result["issues"].append("feature-list.json root must be an object")
        return result

    result["project"] = data.get("project", "unknown")
    language = data.get("tech_stack", {}).get("language", "python")
    if language == "c++":
        language = "cpp"
    result["language"] = language

    real_test_cfg = data.get("real_test", {}) or {}
    test_dir = real_test_cfg.get("test_dir", "tests")
    feature_ref_pattern = real_test_cfg.get(
        "feature_ref_pattern", DEFAULT_FEATURE_REF_PATTERN
    )
    result["test_dir"] = test_dir

    base_dir = os.path.dirname(os.path.abspath(feature_list_path))

    explicit_abs = None
    if explicit_test_files is not None:
        explicit_abs = []
        for rel in explicit_test_files:
            abs_p = rel if os.path.isabs(rel) else os.path.join(base_dir, rel)
            if not os.path.isfile(abs_p):
                result["issues"].append(f"Test file not found: {rel}")
                continue
            explicit_abs.append(abs_p)
        if result["issues"]:
            return result

    abs_test_dir = os.path.join(base_dir, test_dir)
    all_test_files = find_test_files(abs_test_dir, language)

    features = data.get("features", []) or []
    if feature_id is not None:
        features = [
            f for f in features
            if isinstance(f, dict) and f.get("id") == feature_id
        ]
        if not features:
            result["issues"].append(f"Feature {feature_id} not found")
            return result

    active = [
        f for f in features
        if isinstance(f, dict) and not f.get("deprecated", False)
    ]
    result["features_checked"] = len(active)

    path_cache = {}
    total_uncovered = 0
    for feat in active:
        feat_result = check_feature(
            feat, all_test_files, feature_ref_pattern,
            explicit_abs, base_dir, path_cache,
        )
        result["per_feature"].append(feat_result)
        total_uncovered += len(feat_result["uncovered_fr_ids"])

    result["uncovered_total"] = total_uncovered

    # Features with no srs_trace are treated as N/A — they do not fail
    # the gate by themselves, but they are surfaced as a warning issue.
    features_no_trace = [
        f["feature_id"] for f in result["per_feature"] if not f["srs_trace"]
    ]
    if features_no_trace:
        result["issues"].append(
            "Features without srs_trace: "
            + ", ".join(str(i) for i in features_no_trace)
        )

    if total_uncovered == 0:
        result["verdict"] = "PASS"
    else:
        result["verdict"] = "FAIL"

    return result


def format_text(result):
    lines = []
    lines.append(f"SRS Trace Coverage — {result['project']}")
    lines.append("=" * max(30, len(lines[0])))
    lines.append(
        f"Scanned: {result['test_dir']}/ ({result['language']}) — "
        f"{result['features_checked']} feature(s) checked"
    )
    lines.append("")

    for issue in result["issues"]:
        lines.append(f"  ! {issue}")
    if result["issues"]:
        lines.append("")

    for feat in result["per_feature"]:
        fid = feat["feature_id"]
        title = feat["title"]
        lines.append(f"Feature #{fid}: {title}")
        if not feat["srs_trace"]:
            lines.append("  (no srs_trace declared — skipped)")
            lines.append("")
            continue
        for fr_id, hits in feat["coverage"].items():
            if hits:
                lines.append(
                    f"  OK  {fr_id}: {len(hits)} hit(s) — "
                    f"{hits[0]['file']} ({hits[0]['evidence']})"
                )
            else:
                lines.append(f"  !!  {fr_id}: UNCOVERED")
        lines.append("")

    verdict = result["verdict"]
    if verdict == "PASS":
        summary = (
            f"PASS — all {result['features_checked']} feature(s) have every "
            f"srs_trace ID referenced in test artifacts"
        )
    else:
        summary = (
            f"FAIL — {result['uncovered_total']} FR-ID(s) uncovered across "
            f"{result['features_checked']} feature(s)"
        )
    lines.append(f"Result: {summary}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check SRS trace coverage for a long-task project"
    )
    parser.add_argument("path", help="Path to feature-list.json")
    parser.add_argument(
        "--feature", type=int, default=None,
        help="Check a specific feature by ID"
    )
    parser.add_argument(
        "--test-files", nargs="+", default=None,
        help=(
            "Explicit test file list to scan (relative to project root). "
            "If omitted, scope is auto-derived from feature_ref_pattern."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output as JSON"
    )
    args = parser.parse_args()

    result = check(
        args.path,
        feature_id=args.feature,
        explicit_test_files=args.test_files,
    )

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_text(result))

    if result["issues"] and any(
        "not found" in msg or "must be" in msg or "Failed to read" in msg
        for msg in result["issues"]
    ):
        sys.exit(2)
    if result["verdict"] == "PASS":
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
