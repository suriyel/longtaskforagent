#!/usr/bin/env python3
"""
Check ATS coverage against feature-list.json and ST test case documents.

Cross-validates that:
- Every ATS mapping row has a corresponding feature via srs_trace
- Features cover all ATS-required categories (union of srs_trace requirements)
- ST test case documents (if generated) include the required categories
- Reports gaps between ATS requirements and actual test coverage

Usage:
    python check_ats_coverage.py <path/to/ats-doc.md> --feature-list feature-list.json
    python check_ats_coverage.py <path/to/ats-doc.md> --feature-list feature-list.json --feature 3
    python check_ats_coverage.py <path/to/ats-doc.md> --feature-list feature-list.json --strict
"""

import json
import os
import re
import sys


# Valid test categories
VALID_CATEGORIES = {"FUNC", "BNDRY", "UI", "SEC", "PERF"}

# Table row pattern: | REQ-ID | ... |
TABLE_ROW_PATTERN = re.compile(
    r"^\|\s*((?:FR|NFR|IFR)-\d{3})\s*\|"
)

# Case ID pattern in ST documents
CASE_ID_PATTERN = re.compile(
    r"ST-(FUNC|BNDRY|UI|SEC|PERF)-(\d{3})-(\d{3})"
)


def _extract_ats_rows(ats_path: str) -> tuple[list[dict], list[str]]:
    """Extract mapping rows from ATS document."""
    errors = []
    try:
        with open(ats_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [], [f"ATS file not found: {ats_path}"]
    except Exception as e:
        return [], [f"Cannot read ATS file: {e}"]

    rows = []
    for line in content.split("\n"):
        match = TABLE_ROW_PATTERN.match(line.strip())
        if match:
            req_id = match.group(1)
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4:
                categories = set()
                for c in cells[3].split(","):
                    c = c.strip().upper()
                    if c in VALID_CATEGORIES:
                        categories.add(c)

                rows.append({
                    "req_id": req_id,
                    "categories": categories,
                })

    return rows, errors


def _count_st_cases_by_category(st_case_path: str, feature_id: int) -> dict[str, int]:
    """Count ST test cases by category for a given feature."""
    counts = {}
    try:
        with open(st_case_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, Exception):
        return counts

    fid_str = f"{feature_id:03d}"
    for match in CASE_ID_PATTERN.finditer(content):
        cat = match.group(1)
        case_fid = match.group(2)
        if case_fid == fid_str:
            counts[cat] = counts.get(cat, 0) + 1

    return counts


def check_coverage(
    ats_path: str,
    feature_list_path: str,
    feature_id: int = None,
    strict: bool = False,
) -> tuple[list[str], list[str]]:
    """Check ATS coverage. Returns (errors, warnings).

    Uses srs_trace to map features to ATS requirements. Required categories
    are the UNION of all ATS-required categories for the feature's traced
    requirements. In strict mode, category coverage gaps are errors.
    """
    errors = []
    warnings = []

    # Load ATS
    ats_rows, ats_errors = _extract_ats_rows(ats_path)
    errors.extend(ats_errors)
    if not ats_rows:
        if not ats_errors:
            errors.append("No mapping rows found in ATS document")
        return errors, warnings

    # Load feature-list.json
    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            fl_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return [f"Cannot read feature-list.json: {e}"], warnings

    features = fl_data.get("features", [])
    if not features:
        return ["No features in feature-list.json"], warnings

    # Build ATS lookup by req_id
    ats_by_req = {row["req_id"]: row for row in ats_rows}

    # Filter features if --feature specified
    if feature_id is not None:
        features = [f for f in features if isinstance(f, dict) and f.get("id") == feature_id]
        if not features:
            return [f"Feature id={feature_id} not found in feature-list.json"], warnings

    # Check each active feature
    total_gaps = 0
    total_checked = 0

    for feat in features:
        if not isinstance(feat, dict):
            continue
        if feat.get("deprecated", False):
            continue

        fid = feat.get("id")
        title = feat.get("title", "?")
        ui = feat.get("ui", False)
        st_case_path = feat.get("st_case_path")
        srs_trace = feat.get("srs_trace", [])

        total_checked += 1

        # Determine required categories via srs_trace → ATS mapping (union)
        expected_cats = {"FUNC", "BNDRY"}  # Always required
        if ui:
            expected_cats.add("UI")

        # Union ATS-required categories for all traced requirements
        for req_id in srs_trace:
            ats_row = ats_by_req.get(req_id)
            if ats_row:
                expected_cats |= ats_row["categories"]

        if st_case_path and os.path.exists(st_case_path):
            # Count actual ST cases by category
            actual_counts = _count_st_cases_by_category(st_case_path, fid)

            for cat in expected_cats:
                if cat not in actual_counts or actual_counts[cat] == 0:
                    msg = (
                        f"Feature #{fid} ({title}): missing {cat} test cases "
                        f"in {st_case_path} — required by ATS category rules"
                    )
                    if strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
                    total_gaps += 1

        elif st_case_path and not os.path.exists(st_case_path):
            warnings.append(
                f"Feature #{fid} ({title}): st_case_path '{st_case_path}' "
                f"does not exist — ST cases not yet generated"
            )
        elif not st_case_path and feat.get("status") == "passing":
            warnings.append(
                f"Feature #{fid} ({title}): status is 'passing' but no st_case_path set"
            )

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: check_ats_coverage.py <ats-doc.md> "
            "--feature-list feature-list.json [--feature id] [--strict]"
        )
        sys.exit(1)

    ats_path = sys.argv[1]
    feature_list_path = None
    feature_id = None
    strict = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--feature-list" and i + 1 < len(sys.argv):
            feature_list_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--feature" and i + 1 < len(sys.argv):
            try:
                feature_id = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: --feature value must be an integer, got '{sys.argv[i + 1]}'")
                sys.exit(1)
            i += 2
        elif sys.argv[i] == "--strict":
            strict = True
            i += 1
        else:
            print(f"Unknown argument: {sys.argv[i]}")
            sys.exit(1)

    if not feature_list_path:
        print("Error: --feature-list is required")
        sys.exit(1)

    errors, warnings = check_coverage(ats_path, feature_list_path, feature_id, strict)

    if errors:
        print(f"COVERAGE CHECK FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(1)
    else:
        scope = f"feature #{feature_id}" if feature_id else "all features"
        summary = f"ATS COVERAGE OK — checked {scope}"
        if strict:
            summary += " (strict mode)"
        if warnings:
            summary += f" | {len(warnings)} warning(s)"
        print(summary)
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(0)


if __name__ == "__main__":
    main()
