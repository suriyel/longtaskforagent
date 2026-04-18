#!/usr/bin/env python3
"""
Count pending features per phase by sub_status.

Outputs one line:
    design=N tdd=N st=N done=N (total=N)

Only active (non-deprecated) features are counted. Features without a
sub_status field are reported under 'no_sub_status' (indicates the project
predates the phase-per-session refactor and needs migration via
scripts/migrate_sub_status.py).

Exit codes:
    0 — read OK (even if all zero)
    2 — file missing / invalid JSON / no features key

Usage:
    python count_pending.py feature-list.json
    python count_pending.py feature-list.json --json
"""

import argparse
import json
import sys


PHASES = ("design_pending", "tdd_pending", "st_pending", "done")
SHORT = {
    "design_pending": "design",
    "tdd_pending": "tdd",
    "st_pending": "st",
    "done": "done",
}


def count(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError('"features" key missing or not a list')

    result = {SHORT[p]: 0 for p in PHASES}
    result["no_sub_status"] = 0
    result["total"] = 0
    result["deprecated"] = 0

    for feat in features:
        if not isinstance(feat, dict):
            continue
        if feat.get("deprecated"):
            result["deprecated"] += 1
            continue
        result["total"] += 1
        ss = feat.get("sub_status")
        if ss in PHASES:
            result[SHORT[ss]] += 1
        else:
            result["no_sub_status"] += 1
    return result


def format_line(counts: dict) -> str:
    parts = [f"{SHORT[p]}={counts[SHORT[p]]}" for p in PHASES]
    line = " ".join(parts) + f" (total={counts['total']}"
    if counts["no_sub_status"]:
        line += f", no_sub_status={counts['no_sub_status']}"
    if counts["deprecated"]:
        line += f", deprecated={counts['deprecated']}"
    line += ")"
    return line


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("path", help="Path to feature-list.json")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of one-line format")
    args = ap.parse_args()

    try:
        counts = count(args.path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"count_pending: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(counts))
    else:
        print(format_line(counts))
    sys.exit(0)


if __name__ == "__main__":
    main()
