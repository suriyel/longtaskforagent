#!/usr/bin/env python3
"""Derive feature-design doc paths from feature-list.json (single authoritative slug implementation).

Consumers (orchestrators and sub-skills) call this instead of globbing `docs/features/*`
or reimplementing kebab-case logic. Keeps slug rules in one place; prevents drift across
the three Phase orchestrators (work-design / work-tdd / work-st) and their sub-skills.

Usage:
    python scripts/feature_paths.py design-doc --feature <id>
    python scripts/feature_paths.py design-doc --feature <id> --must-exist
    python scripts/feature_paths.py design-doc --feature <id> --json
    python scripts/feature_paths.py design-doc --feature <id> --feature-list path/to/feature-list.json

Exit codes:
    0  success
    1  --must-exist and file missing
    2  feature-list.json not found
    3  feature id not found in feature-list.json
"""

import argparse
import json
import os
import sys

SLUG_MAX_LEN = 40
CJK_RANGE = (0x4E00, 0x9FFF)


class FeatureNotFound(Exception):
    def __init__(self, feature_id):
        self.feature_id = feature_id


def _is_kept(ch: str) -> bool:
    if ch.isascii() and ch.isalnum():
        return True
    if CJK_RANGE[0] <= ord(ch) <= CJK_RANGE[1]:
        return True
    return False


def slugify(title: str) -> str:
    """Kebab-case slug: lowercase ASCII, preserve CJK, merge others to '-', cap 40 codepoints."""
    if not title:
        return "untitled"
    title = title.lower()
    out = []
    for ch in title:
        out.append(ch if _is_kept(ch) else "-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    if len(slug) > SLUG_MAX_LEN:
        slug = slug[:SLUG_MAX_LEN].rstrip("-")
    return slug or "untitled"


def design_doc_path(feature_list_path: str, feature_id: int) -> str:
    with open(feature_list_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for feat in data.get("features", []):
        if feat.get("id") == feature_id:
            slug = slugify(feat.get("title", ""))
            return f"docs/features/{feature_id}-{slug}.md"
    raise FeatureNotFound(feature_id)


def _cmd_design_doc(args) -> int:
    fl = args.feature_list or "feature-list.json"
    if not os.path.isfile(fl):
        print(f"feature-list.json not found: {fl}", file=sys.stderr)
        return 2
    try:
        path = design_doc_path(fl, args.feature)
    except FeatureNotFound as e:
        print(f"Feature id={e.feature_id} not found in {fl}", file=sys.stderr)
        return 3

    exists = os.path.isfile(path)
    if args.must_exist and not exists:
        print(f"Design doc not on disk: {path}", file=sys.stderr)
        return 1

    if args.as_json:
        slug = path[len("docs/features/") + len(str(args.feature)) + 1 : -len(".md")]
        print(json.dumps({
            "path": path,
            "exists": exists,
            "feature_id": args.feature,
            "slug": slug,
        }, ensure_ascii=False))
    else:
        print(path)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="feature_paths.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("design-doc", help="Resolve path to feature design doc")
    p.add_argument("--feature", type=int, required=True, help="Feature id")
    p.add_argument("--must-exist", action="store_true", help="Exit 1 if file missing")
    p.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON to stdout")
    p.add_argument("--feature-list", default=None, help="Path to feature-list.json (default: cwd/feature-list.json)")

    args = parser.parse_args()
    if args.cmd == "design-doc":
        return _cmd_design_doc(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
