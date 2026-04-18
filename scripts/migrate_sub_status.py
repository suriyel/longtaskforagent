#!/usr/bin/env python3
"""
Migrate existing feature-list.json to include sub_status field.

Rules (conservative — never regresses a feature):
    status=passing               → sub_status=done
    status=failing + git_sha set → sub_status=st_pending
    status=failing, no git_sha   → sub_status=design_pending

Idempotent: features that already have a valid sub_status are left alone
(unless --force is passed). Writes back to the same file with pretty JSON.
Prints a summary of migrations performed.

Usage:
    python migrate_sub_status.py feature-list.json
    python migrate_sub_status.py feature-list.json --dry-run
    python migrate_sub_status.py feature-list.json --force
"""

import argparse
import json
import sys


VALID = {"design_pending", "tdd_pending", "st_pending", "done"}


def infer(feat: dict) -> str:
    status = feat.get("status")
    if status == "passing":
        return "done"
    if feat.get("git_sha"):
        return "st_pending"
    return "design_pending"


def migrate(data: dict, force: bool = False) -> dict:
    features = data.get("features", [])
    stats = {"updated": 0, "skipped": 0, "invalid": 0}
    for feat in features:
        if not isinstance(feat, dict):
            continue
        existing = feat.get("sub_status")
        if existing in VALID and not force:
            stats["skipped"] += 1
            continue
        if existing is not None and existing not in VALID:
            stats["invalid"] += 1
        feat["sub_status"] = infer(feat)
        stats["updated"] += 1
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("path", help="Path to feature-list.json")
    ap.add_argument("--dry-run", action="store_true", help="Preview without writing")
    ap.add_argument("--force", action="store_true", help="Re-infer even if sub_status already valid")
    args = ap.parse_args()

    with open(args.path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = migrate(data, force=args.force)

    print(f"migrate_sub_status: updated={stats['updated']}, "
          f"skipped={stats['skipped']}, invalid={stats['invalid']}")

    if args.dry_run:
        print("[dry-run] no file written")
        return

    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
