#!/usr/bin/env python3
"""
Summarize feature-list.json state.

Output shape:
    {
      "total":     int,   # active (non-deprecated) features
      "passing":   int,   # status == "passing"
      "failing":   int,   # status == "failing" (includes current-locked feature)
      "current":   {"feature_id": N, "phase": "design"|"tdd"|"st"} | None,
      "deprecated": int,
      "legacy_sub_status": int  # features still carrying sub_status field
    }

`legacy_sub_status > 0` signals the project predates the current-lock refactor
and needs `scripts/migrate_sub_status.py`.

Exit codes:
    0 — read OK
    2 — file missing / invalid JSON / no features key

Usage:
    python count_pending.py feature-list.json
    python count_pending.py feature-list.json --json
"""

import argparse
import json
import sys


def count(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError('"features" key missing or not a list')

    result = {
        "total": 0,
        "passing": 0,
        "failing": 0,
        "current": data.get("current"),
        "deprecated": 0,
        "legacy_sub_status": 0,
    }

    for feat in features:
        if not isinstance(feat, dict):
            continue
        if feat.get("deprecated"):
            result["deprecated"] += 1
            continue
        result["total"] += 1
        if feat.get("status") == "passing":
            result["passing"] += 1
        else:
            result["failing"] += 1
        if "sub_status" in feat:
            result["legacy_sub_status"] += 1
    return result


def format_line(counts: dict) -> str:
    cur = counts["current"]
    cur_str = (f"current=#{cur['feature_id']}({cur['phase']})"
               if cur and isinstance(cur, dict) else "current=none")
    parts = [
        cur_str,
        f"passing={counts['passing']}",
        f"failing={counts['failing']}",
        f"(total={counts['total']}",
    ]
    if counts["deprecated"]:
        parts[-1] += f", deprecated={counts['deprecated']}"
    if counts["legacy_sub_status"]:
        parts[-1] += f", legacy_sub_status={counts['legacy_sub_status']}"
    parts[-1] += ")"
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("path", help="Path to feature-list.json")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
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
