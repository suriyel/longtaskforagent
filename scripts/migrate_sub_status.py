#!/usr/bin/env python3
"""
Migrate legacy feature-list.json from per-feature `sub_status` to root `current`.

Pick priority (preserves in-flight work):
    most-advanced phase first: st_pending > tdd_pending > design_pending
    then smallest `id` as tiebreaker

Mapping:
    sub_status == "design_pending" → phase = "design"
    sub_status == "tdd_pending"    → phase = "tdd"
    sub_status == "st_pending"     → phase = "st"

After migration:
    - Every feature's `sub_status` field is removed.
    - Root `current` is set to {"feature_id": N, "phase": P} or null if all done.

Idempotent: if `current` key already exists on the root and no feature still
carries `sub_status`, the file is left untouched.

Usage:
    python migrate_sub_status.py feature-list.json
    python migrate_sub_status.py feature-list.json --dry-run
    python migrate_sub_status.py feature-list.json --force
"""

import argparse
import json
import sys


_SUB_TO_PHASE = {
    "design_pending": "design",
    "tdd_pending":    "tdd",
    "st_pending":     "st",
}
# Higher rank = more advanced = higher priority when picking `current`.
_PHASE_RANK = {"st_pending": 2, "tdd_pending": 1, "design_pending": 0}


def migrate(data: dict, force: bool = False) -> dict:
    features = data.get("features", [])
    stats = {"cleared": 0, "current_set": False, "all_done": False, "noop": False}

    any_sub_status = any(
        isinstance(f, dict) and "sub_status" in f for f in features
    )
    already_migrated = "current" in data

    if already_migrated and not any_sub_status and not force:
        stats["noop"] = True
        return stats

    pending = sorted(
        [f for f in features
         if isinstance(f, dict)
         and not f.get("deprecated")
         and f.get("sub_status") in _SUB_TO_PHASE],
        # Most-advanced phase first (preserves in-flight work), then smallest id.
        key=lambda f: (-_PHASE_RANK[f["sub_status"]], f["id"]),
    )

    if pending:
        p = pending[0]
        data["current"] = {
            "feature_id": p["id"],
            "phase": _SUB_TO_PHASE[p["sub_status"]],
        }
        stats["current_set"] = True
    else:
        data["current"] = None
        stats["all_done"] = True

    for f in features:
        if isinstance(f, dict) and "sub_status" in f:
            del f["sub_status"]
            stats["cleared"] += 1

    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("path", help="Path to feature-list.json")
    ap.add_argument("--dry-run", action="store_true", help="Preview without writing")
    ap.add_argument("--force", action="store_true",
                    help="Re-run even if root `current` already exists")
    args = ap.parse_args()

    with open(args.path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = migrate(data, force=args.force)

    if stats["noop"]:
        print("migrate_sub_status: already migrated; no changes")
        return

    desc = "current=null (all done)" if stats["all_done"] else (
        f"current={{feature_id:{data['current']['feature_id']}, "
        f"phase:{data['current']['phase']}}}"
    )
    print(f"migrate_sub_status: cleared sub_status from {stats['cleared']} "
          f"features; {desc}")

    if args.dry_run:
        print("[dry-run] no file written")
        return

    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
