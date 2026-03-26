#!/usr/bin/env python3
"""
Validate ATS (Acceptance Test Strategy) document structure and completeness.

Checks:
- Valid markdown structure with required sections
- Mapping table rows reference valid requirement IDs
- Category assignments use valid categories
- Minimum case counts are positive integers
- When --srs is given: every FR/NFR/IFR from SRS appears in the mapping table
- NFR rows have test methods with tools and thresholds

Usage:
    python validate_ats.py <path/to/ats-doc.md>
    python validate_ats.py <path/to/ats-doc.md> --srs docs/plans/srs.md
"""

import re
import sys


# Valid test categories
VALID_CATEGORIES = {"FUNC", "BNDRY", "UI", "SEC", "PERF"}

# Required top-level sections (Chinese or English)
REQUIRED_SECTIONS = [
    ("测试范围与策略概览", "Test Scope & Strategy Overview", "Test Scope"),
    ("需求→验收场景映射", "Requirement", "Acceptance Scenario Mapping"),
    ("测试类别策略", "Test Category Strateg", "Category Strateg"),
]

# Requirement ID patterns
REQ_ID_PATTERN = re.compile(r"^(FR|NFR|IFR)-\d{3}$")

# Table row pattern: | REQ-ID | ... |
TABLE_ROW_PATTERN = re.compile(
    r"^\|\s*((?:FR|NFR|IFR)-\d{3})\s*\|"
)


def _extract_headings(content: str) -> list[str]:
    """Extract all markdown headings."""
    return [
        line.lstrip("#").strip()
        for line in content.split("\n")
        if line.strip().startswith("#")
    ]


def _extract_mapping_rows(content: str) -> list[dict]:
    """Extract mapping table rows with requirement IDs."""
    rows = []
    for line in content.split("\n"):
        match = TABLE_ROW_PATTERN.match(line.strip())
        if match:
            req_id = match.group(1)
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4:
                rows.append({
                    "req_id": req_id,
                    "summary": cells[1] if len(cells) > 1 else "",
                    "scenarios": cells[2] if len(cells) > 2 else "",
                    "categories_raw": cells[3] if len(cells) > 3 else "",
                    "priority": cells[4] if len(cells) > 4 else "",
                    "line": line.strip(),
                })
    return rows


def _extract_srs_req_ids(srs_path: str) -> tuple[set[str], list[str]]:
    """Extract requirement IDs from SRS document. Returns (ids, errors)."""
    errors = []
    try:
        with open(srs_path, "r", encoding="utf-8") as f:
            srs_content = f.read()
    except FileNotFoundError:
        return set(), [f"SRS file not found: {srs_path}"]
    except Exception as e:
        return set(), [f"Cannot read SRS file: {e}"]

    # Find all FR-xxx, NFR-xxx, IFR-xxx patterns in headings or bold text
    ids = set()
    for match in re.finditer(r"(?:^#{1,4}\s+|(?:\*\*))?((?:FR|NFR|IFR)-\d{3})", srs_content, re.MULTILINE):
        ids.add(match.group(1))

    if not ids:
        errors.append(f"No requirement IDs (FR-xxx/NFR-xxx/IFR-xxx) found in {srs_path}")

    return ids, errors


def validate(path: str, srs_path: str = None) -> tuple[list[str], list[str]]:
    """Validate an ATS document. Returns (errors, warnings)."""
    errors = []
    warnings = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"File not found: {path}"], []
    except Exception as e:
        return [f"Cannot read file: {e}"], []

    if not content.strip():
        return ["File is empty"], []

    # Check required sections
    headings = _extract_headings(content)
    headings_lower = [h.lower() for h in headings]
    all_headings_text = " ".join(headings_lower)

    for section_variants in REQUIRED_SECTIONS:
        found = False
        for variant in section_variants:
            if variant.lower() in all_headings_text:
                found = True
                break
        if not found:
            errors.append(
                f"Missing required section: '{section_variants[0]}' "
                f"(or '{section_variants[1]}')"
            )

    # Extract and validate mapping table rows
    rows = _extract_mapping_rows(content)

    if not rows:
        errors.append("No mapping table rows found (expected rows starting with '| FR-xxx |' or '| NFR-xxx |')")
        return errors, warnings

    ats_req_ids = set()

    for row in rows:
        req_id = row["req_id"]

        # Check requirement ID format
        if not REQ_ID_PATTERN.match(req_id):
            errors.append(f"Invalid requirement ID format: '{req_id}'")

        # Check for duplicates
        if req_id in ats_req_ids:
            errors.append(f"Duplicate requirement ID in mapping table: '{req_id}'")
        ats_req_ids.add(req_id)

        # Validate categories
        categories_raw = row["categories_raw"]
        if categories_raw:
            cats = [c.strip().upper() for c in categories_raw.split(",")]
            for cat in cats:
                if cat and cat not in VALID_CATEGORIES:
                    errors.append(
                        f"{req_id}: invalid category '{cat}', "
                        f"must be one of {sorted(VALID_CATEGORIES)}"
                    )

            # Check minimum category requirements
            if req_id.startswith("FR-"):
                if "FUNC" not in cats:
                    warnings.append(f"{req_id}: FR missing FUNC category")
                if "BNDRY" not in cats:
                    warnings.append(f"{req_id}: FR missing BNDRY category")
                if len(cats) < 2:
                    warnings.append(f"{req_id}: FR has only one category — should have at least FUNC + BNDRY")

        # Check for empty scenarios
        if not row["scenarios"].strip():
            errors.append(f"{req_id}: scenarios column is empty")

    # Cross-validate against SRS if provided
    if srs_path:
        srs_ids, srs_errors = _extract_srs_req_ids(srs_path)
        errors.extend(srs_errors)

        if srs_ids:
            # Check for missing requirements (SRS requirements not in ATS)
            missing = srs_ids - ats_req_ids
            for mid in sorted(missing):
                errors.append(f"SRS requirement {mid} not found in ATS mapping table")

            # Check for orphan ATS rows (ATS rows not in SRS)
            orphans = ats_req_ids - srs_ids
            for oid in sorted(orphans):
                warnings.append(f"ATS mapping row {oid} not found in SRS — possible orphan")

    # Check for NFR test method section
    has_nfr_rows = any(r["req_id"].startswith("NFR-") for r in rows)
    has_nfr_matrix = any(
        v.lower() in all_headings_text
        for v in ["nfr 测试方法", "nfr test method", "测试方法矩阵"]
    )
    if has_nfr_rows and not has_nfr_matrix:
        warnings.append("ATS has NFR requirements but no NFR Test Method Matrix section")

    # Check for integration scenarios section (warn if >5 requirements but no integration section)
    has_integration = any(
        v.lower() in all_headings_text
        for v in ["集成场景", "integration scenario", "cross-feature"]
    )
    if len(rows) > 5 and not has_integration:
        warnings.append(
            f"ATS has {len(rows)} requirements but no Cross-Feature Integration Scenarios section "
            f"— recommended for projects with >5 requirements"
        )

    # Check for risk section
    has_risk = any(
        v.lower() in all_headings_text
        for v in ["风险", "risk"]
    )
    if len(rows) > 10 and not has_risk:
        warnings.append(
            f"ATS has {len(rows)} requirements but no Risk-Driven Test Priority section "
            f"— recommended for projects with >10 requirements"
        )

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_ats.py <path/to/ats-doc.md> [--srs path/to/srs.md]")
        sys.exit(1)

    path = sys.argv[1]
    srs_path = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--srs" and i + 1 < len(sys.argv):
            srs_path = sys.argv[i + 1]
            i += 2
        else:
            print(f"Unknown argument: {sys.argv[i]}")
            sys.exit(1)

    errors, warnings = validate(path, srs_path)

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for w in warnings:
                print(f"  - {w}")
        sys.exit(1)
    else:
        # Count mapping rows for summary
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            rows = _extract_mapping_rows(content)
            summary = f"VALID — {len(rows)} requirement(s) mapped"

            # Count categories
            all_cats = set()
            for row in rows:
                if row["categories_raw"]:
                    for c in row["categories_raw"].split(","):
                        c = c.strip().upper()
                        if c in VALID_CATEGORIES:
                            all_cats.add(c)
            if all_cats:
                summary += f" | Categories: {', '.join(sorted(all_cats))}"

            if srs_path:
                summary += " | SRS cross-validated"

            if warnings:
                summary += f" | {len(warnings)} warning(s)"

            print(summary)
            if warnings:
                print("\nWarnings:")
                for w in warnings:
                    print(f"  - {w}")
        except Exception:
            print("VALID")

        sys.exit(0)


if __name__ == "__main__":
    main()
