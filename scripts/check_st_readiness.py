#!/usr/bin/env python3
"""
Check system testing readiness for a long-task project.

Verifies:
- feature-list.json exists and all features are "passing"
- SRS document exists in docs/plans/
- Design document exists in docs/plans/

Usage:
    python check_st_readiness.py <path/to/feature-list.json>

Exit codes:
    0 — ready for system testing (all features passing, docs present)
    1 — not ready (failing features or missing docs)
"""

import argparse
import glob
import json
import os
import sys


def check_st_readiness(path: str) -> dict:
    """
    Check whether the project is ready for system testing.

    Args:
        path: Path to feature-list.json

    Returns:
        dict with keys:
            ready: bool
            total_features: int
            passing_features: int
            failing_features: int
            failing_ids: list[int]
            srs_found: bool
            srs_path: str or None
            design_found: bool
            design_path: str or None
            issues: list[str]
    """
    result = {
        "ready": False,
        "total_features": 0,
        "passing_features": 0,
        "failing_features": 0,
        "deprecated_features": 0,
        "failing_ids": [],
        "srs_found": False,
        "srs_path": None,
        "design_found": False,
        "design_path": None,
        "issues": [],
    }

    # Load feature-list.json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])

    # Separate deprecated from active features
    active_features = []
    for feat in features:
        if feat.get("deprecated", False):
            result["deprecated_features"] += 1
        else:
            active_features.append(feat)

    result["total_features"] = len(active_features)

    if len(active_features) == 0:
        result["issues"].append("No active features defined in feature-list.json")
        return result

    # Check feature statuses (only active features)
    for feat in active_features:
        status = feat.get("status", "failing")
        feat_id = feat.get("id", "?")
        if status == "passing":
            result["passing_features"] += 1
        else:
            result["failing_features"] += 1
            result["failing_ids"].append(feat_id)
    if result["failing_features"] > 0:
        result["issues"].append(
            f"{result['failing_features']} feature(s) still failing: "
            f"{result['failing_ids']}"
        )

    # Check docs/plans/ for SRS and design docs
    base_dir = os.path.dirname(os.path.abspath(path))
    plans_dir = os.path.join(base_dir, "docs", "plans")

    # SRS doc
    srs_matches = glob.glob(os.path.join(plans_dir, "*-srs.md"))
    if srs_matches:
        result["srs_found"] = True
        result["srs_path"] = srs_matches[0]
    else:
        result["issues"].append("SRS document not found (docs/plans/*-srs.md)")

    # Design doc
    design_matches = glob.glob(os.path.join(plans_dir, "*-design.md"))
    if design_matches:
        result["design_found"] = True
        result["design_path"] = design_matches[0]
    else:
        result["issues"].append("Design document not found (docs/plans/*-design.md)")

    # Check ST test case coverage (warning, not blocking)
    features_with_st_cases = 0
    features_without_st_cases = []
    for feat in active_features:
        if feat.get("st_case_path"):
            features_with_st_cases += 1
        else:
            features_without_st_cases.append(feat.get("id", "?"))
    result["st_case_coverage"] = features_with_st_cases
    result["st_case_missing"] = features_without_st_cases

    # Check docs/test-cases/ directory exists
    test_cases_dir = os.path.join(base_dir, "docs", "test-cases")
    result["test_cases_dir_found"] = os.path.isdir(test_cases_dir)

    # Determine readiness (based on active features only)
    result["ready"] = (
        result["failing_features"] == 0
        and result["srs_found"]
        and result["design_found"]
        and result["total_features"] > 0
    )

    # Note: deprecated features are excluded from readiness checks

    return result


def main():
    parser = argparse.ArgumentParser(description="Check system testing readiness")
    parser.add_argument("path", help="Path to feature-list.json")
    args = parser.parse_args()

    try:
        result = check_st_readiness(args.path)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: Cannot read feature-list.json: {e}")
        sys.exit(1)

    # Print summary
    print(f"Active features: {result['passing_features']}/{result['total_features']} passing")
    if result["deprecated_features"] > 0:
        print(f"Deprecated: {result['deprecated_features']} (excluded from checks)")
    if result["failing_features"] > 0:
        print(f"Failing: {result['failing_ids']}")
    print(f"SRS: {'found' if result['srs_found'] else 'MISSING'}")
    print(f"Design: {'found' if result['design_found'] else 'MISSING'}")
    # ST test case coverage (warning) — only if st_case_coverage was computed
    if "st_case_coverage" in result:
        if result["st_case_missing"]:
            print(f"ST test cases: {result['st_case_coverage']}/{result['total_features']} features covered")
            print(f"  Warning: features without ST test cases: {result['st_case_missing']}")
        else:
            print(f"ST test cases: {result['st_case_coverage']}/{result['total_features']} features covered")

    if result["ready"]:
        print("\nREADY for system testing.")
        sys.exit(0)
    else:
        print(f"\nNOT READY — {len(result['issues'])} issue(s):")
        for issue in result["issues"]:
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
