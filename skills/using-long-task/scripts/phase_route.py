#!/usr/bin/env python3
"""
Unified phase router for long-task-agent (simple branch).

Single source of truth for phase routing. ``using-long-task`` delegates
here; no Skill-to-Skill routing anywhere else. Outputs the next skill to
invoke plus any state the caller needs.

Routing precedence:
    1. bugfix-request.json            -> long-task-hotfix
    2. increment-request.json         -> long-task-increment
    3. feature-list.json              -> validate + route by root `current`
                                         (or pick next dep-ready feature)
    4. docs/plans/*-design.md         -> long-task-init
    5. docs/plans/*-srs.md            -> long-task-design if rules present,
                                         else long-task-codebase-scanner
    6. docs/rules/*.md (>=1)          -> long-task-requirements
    7. otherwise (no rules)           -> long-task-codebase-scanner

Post-init emit fields:
    next_skill    — skill to invoke next (None if all features passing)
    feature_id    — id of the feature to work on (None pre-init / all done)
    starting_new  — True when this is a fresh pick (work-design must
                    atomically write root `current` before proceeding)

Exit codes:
    0 — ok
    2 — validation failed (errors is non-empty)

Usage:
    python phase_route.py [--root DIR] [--json]
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from count_pending import count as _count
from validate_features import validate as _validate


def _force_utf8_io() -> None:
    """Force stdout/stderr to UTF-8 so CJK text survives non-UTF-8 locales
    (Windows cp936, LANG=C). Python 3.7+."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


_PHASE_TO_SKILL = {
    "design": "long-task-work-design",
    "tdd":    "long-task-work-tdd",
}
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _select_next(features: list) -> tuple:
    """Return (pick_feature, blocked_ids). pick=None + blocked_ids non-empty
    means all failing features are dep-blocked (cycle / misconfig)."""
    active = [x for x in features if not x.get("deprecated")]
    passing = {x["id"] for x in active if x.get("status") == "passing"}
    failing = [x for x in active if x.get("status") != "passing"]
    eligible = [x for x in failing
                if all(d in passing for d in x.get("dependencies", []))]
    if not eligible:
        return None, [x["id"] for x in failing]
    eligible.sort(key=lambda f: (_PRIORITY_RANK.get(f.get("priority"), 3),
                                 f["id"]))
    return eligible[0], []


def route(root: str = ".") -> dict:
    out = {
        "ok": True,
        "errors": [],
        "counts": None,
        "next_skill": None,
        "feature_id": None,
        "starting_new": False,
    }
    j = lambda *p: os.path.join(root, *p)
    has_glob = lambda pat: bool(sorted(glob.glob(j(*pat.split("/")))))

    # 1-2. Signal files (highest priority)
    if os.path.isfile(j("bugfix-request.json")):
        out["next_skill"] = "long-task-hotfix"
        return out
    if os.path.isfile(j("increment-request.json")):
        out["next_skill"] = "long-task-increment"
        return out

    # 3. Post-init: feature-list.json exists
    fl = j("feature-list.json")
    if os.path.isfile(fl):
        errors, _ = _validate(fl)
        if errors:
            out["ok"] = False
            out["errors"] = errors
            return out
        try:
            counts = _count(fl)
        except (ValueError, json.JSONDecodeError) as e:
            out["ok"] = False
            out["errors"] = [f"count_pending: {e}"]
            return out
        out["counts"] = counts

        with open(fl, "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data.get("features", [])
        cur = data.get("current")

        if cur and isinstance(cur, dict) and cur.get("feature_id") is not None:
            phase = cur.get("phase")
            if phase not in _PHASE_TO_SKILL:
                out["ok"] = False
                out["errors"] = [f"current.phase invalid: {phase!r}"]
                return out
            out["next_skill"] = _PHASE_TO_SKILL[phase]
            out["feature_id"] = cur["feature_id"]
            return out

        # current is null: pick next failing feature or signal all done
        if counts["total"] == 0:
            return out  # no active features — caller may suggest increment
        if counts["passing"] == counts["total"]:
            return out  # all done — next_skill stays None

        pick, blocked_ids = _select_next(features)
        if pick is None:
            out["ok"] = False
            out["errors"] = [
                f"No dependency-ready feature among {len(blocked_ids)} failing "
                f"features (ids={blocked_ids}); check dependencies[] for "
                f"cycles or unfinished upstream deps"
            ]
            return out
        out["next_skill"] = "long-task-work-design"
        out["feature_id"] = pick["id"]
        out["starting_new"] = True
        return out

    # 4. Pre-init: design doc exists → init
    if has_glob("docs/plans/*-design.md"):
        out["next_skill"] = "long-task-init"
        return out

    # 5. SRS exists but no design — scanner unless rules already populated
    if has_glob("docs/plans/*-srs.md"):
        out["next_skill"] = ("long-task-design"
                             if has_glob("docs/rules/*.md")
                             else "long-task-codebase-scanner")
        return out

    # 6. Rules populated — requirements
    if has_glob("docs/rules/*.md"):
        out["next_skill"] = "long-task-requirements"
        return out

    # 7. No rules — scanner (self-adapts via fast-path for greenfield)
    out["next_skill"] = "long-task-codebase-scanner"
    return out


def main():
    _force_utf8_io()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", default=".", help="Project root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    args = ap.parse_args()

    r = route(args.root)
    if args.json:
        json.dump(r, sys.stdout, ensure_ascii=False)
        print()
    else:
        extra = ""
        if r["feature_id"] is not None:
            extra += f" feature_id={r['feature_id']}"
        if r["starting_new"]:
            extra += " starting_new=True"
        if r["errors"]:
            extra += f" errors={r['errors']}"
        print(f"next={r['next_skill']} ok={r['ok']} "
              f"counts={r['counts']}" + extra)
    sys.exit(0 if r["ok"] else 2)


if __name__ == "__main__":
    main()
