#!/usr/bin/env python3
"""
Cross-document integrity check for Legacy Context Decisions (LCD).

Validates:
- Every `lcd_trace` ID in feature-list.json exists in SRS §1.4.2 LCD table
- Every referenced LCD has status = ACTIVE (not DEPRECATED)
- Every referenced LCD has category != RATIONALE (RATIONALE is explanatory only)
- Every ACTIVE non-RATIONALE LCD is referenced by at least one active feature (orphan check)
- DEPRECATED LCDs have no active feature references

Usage:
    python check_lcd_wiring.py <feature-list.json> <srs.md>

Exits non-zero on any violation. Prints a summary on success.
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


VALID_CATEGORIES = {"BEHAVIOR", "COMPAT", "DATA", "PERF", "RATIONALE"}
VALID_AUTHORITIES = {"RESOLVED", "QUOTED", "CONFLICTED"}
VALID_STATUSES = {"ACTIVE", "DEPRECATED"}


@dataclass
class Lcd:
    id: str
    category: str
    authority: str
    status: str
    row_text: str


def _force_utf8_io() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_lcd_table(srs_text: str) -> tuple[list[Lcd], list[str]]:
    """Extract §1.4.2 LCD rows from SRS markdown. Returns (lcds, parse_errors)."""
    errors: list[str] = []

    # Find §1.4.2 heading; accept either "#### 1.4.2" or raw "1.4.2 Legacy" heuristic.
    m = re.search(r"^#{2,4}\s*1\.4\.2\b.*$", srs_text, re.MULTILINE)
    if not m:
        return [], ["SRS §1.4.2 heading not found"]

    start = m.end()
    # Stop at next heading of same or higher level or next 1.4.x / 1.5.
    next_m = re.search(r"^#{2,4}\s*(?:1\.4\.3|1\.5|2\.)\b", srs_text[start:], re.MULTILINE)
    section = srs_text[start:start + next_m.start()] if next_m else srs_text[start:]

    lcds: list[Lcd] = []
    table_rows = re.findall(r"^\|.*\|\s*$", section, re.MULTILINE)
    if not table_rows:
        return [], []  # empty §1.4.2 is valid (greenfield)

    for raw in table_rows:
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        first = cells[0]
        if not re.match(r"^LCD-\d{3}$", first):
            continue  # header / separator / malformed row
        lcd_id, category, _evidence, _decision, authority, _fr_impact, status = cells[:7]
        if category not in VALID_CATEGORIES:
            errors.append(f"{lcd_id}: category '{category}' not in {sorted(VALID_CATEGORIES)}")
        if authority not in VALID_AUTHORITIES:
            errors.append(f"{lcd_id}: authority '{authority}' not in {sorted(VALID_AUTHORITIES)}")
        if status not in VALID_STATUSES:
            errors.append(f"{lcd_id}: status '{status}' not in {sorted(VALID_STATUSES)}")
        if authority == "CONFLICTED":
            errors.append(
                f"{lcd_id}: authority=CONFLICTED is not allowed in a finalized SRS; "
                "resolve via Step 3 Gap Fill before commit"
            )
        lcds.append(Lcd(id=lcd_id, category=category, authority=authority,
                        status=status, row_text=raw))

    # Detect duplicate IDs.
    seen: dict[str, int] = {}
    for lcd in lcds:
        seen[lcd.id] = seen.get(lcd.id, 0) + 1
    for lid, count in seen.items():
        if count > 1:
            errors.append(f"{lid}: duplicate row (appears {count} times in §1.4.2)")

    return lcds, errors


def validate_wiring(feature_list_path: Path, srs_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        fl = json.loads(feature_list_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        return [f"Cannot read feature-list.json: {e}"], []

    try:
        srs_text = srs_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        return [f"Cannot read SRS file: {e}"], []

    lcds, parse_errors = parse_lcd_table(srs_text)
    errors.extend(parse_errors)
    lcd_by_id: dict[str, Lcd] = {l.id: l for l in lcds}

    features = fl.get("features", []) or []
    active_features = [f for f in features if isinstance(f, dict) and not f.get("deprecated", False)]

    # Check 1-3: every referenced LCD exists + active + not RATIONALE
    referenced_ids: set[str] = set()
    for feat in active_features:
        fid = feat.get("id")
        lcd_trace = feat.get("lcd_trace") or []
        for ref in lcd_trace:
            referenced_ids.add(ref)
            lcd = lcd_by_id.get(ref)
            if lcd is None:
                errors.append(
                    f"Feature id={fid}: lcd_trace references {ref} which does not exist in SRS §1.4.2"
                )
                continue
            if lcd.status == "DEPRECATED":
                errors.append(
                    f"Feature id={fid}: lcd_trace references DEPRECATED {ref}; "
                    "active features must not depend on deprecated LCDs"
                )
            if lcd.category == "RATIONALE":
                errors.append(
                    f"Feature id={fid}: lcd_trace references {ref} with category=RATIONALE; "
                    "RATIONALE LCDs are explanatory only and must not enter lcd_trace"
                )

    # Check 4: orphan detection — every ACTIVE non-RATIONALE LCD must be referenced
    for lcd in lcds:
        if lcd.status == "ACTIVE" and lcd.category != "RATIONALE":
            if lcd.id not in referenced_ids:
                warnings.append(
                    f"{lcd.id} ({lcd.category}, ACTIVE) is not referenced by any active feature's lcd_trace "
                    "— either wire it via long-task-init-features/increment, or demote to RATIONALE if no execution impact"
                )

    # Check 5: deprecated LCDs must have no active references (subsumed by check 2, kept for clarity)
    for lcd in lcds:
        if lcd.status == "DEPRECATED" and lcd.id in referenced_ids:
            # Already flagged in check 2 per feature; nothing extra.
            pass

    return errors, warnings


def main() -> int:
    _force_utf8_io()
    if len(sys.argv) != 3:
        print("Usage: check_lcd_wiring.py <feature-list.json> <srs.md>", file=sys.stderr)
        return 2

    feature_list_path = Path(sys.argv[1])
    srs_path = Path(sys.argv[2])

    errors, warnings = validate_wiring(feature_list_path, srs_path)

    if errors:
        print(f"LCD WIRING FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for w in warnings:
                print(f"  - {w}")
        return 1

    if warnings:
        print(f"LCD WIRING OK — {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("LCD WIRING OK — all lcd_trace references resolved, no orphans")

    return 0


if __name__ == "__main__":
    sys.exit(main())
