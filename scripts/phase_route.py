#!/usr/bin/env python3
"""
Unified phase router for long-task-agent.

Single source of truth for phase routing. ``using-long-task`` delegates
here; no Skill-to-Skill routing anywhere else. Outputs the next skill to
invoke plus any state the caller needs (validation errors, migration
flag, counts).

Routing precedence:
    1. bugfix-request.json            -> long-task-hotfix
    2. increment-request.json         -> long-task-increment
    3. feature-list.json              -> validate + route by root `current`
                                         (or pick next dep-ready feature)
    4. docs/plans/*-ats.md            -> long-task-init
    5. docs/plans/*-design.md         -> long-task-ats
    6. docs/plans/*-ucd.md            -> long-task-design
    7. docs/plans/*-srs.md            -> long-task-ucd
    8. docs/rules/*.md (>=1)          -> long-task-requirements
    9. brownfield heuristic           -> long-task-brownfield-scan
   10. otherwise                      -> long-task-requirements

Post-init emit fields:
    next_skill    — skill to invoke next
    feature_id    — id of the feature to work on (None for system-level skills)
    starting_new  — True when this is a fresh pick (Worker-design must
                    atomically write root `current` before proceeding)
    needs_migration — True when features still carry legacy `sub_status`

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
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from count_pending import count as _count
from validate_features import validate as _validate


_SRC_EXTS = (".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs")
_EXCLUDE_DIRS = {".git", "node_modules", "venv", ".venv",
                 "dist", "build", "__pycache__", "target"}

_PHASE_TO_SKILL = {
    "design": "long-task-work-design",
    "tdd":    "long-task-work-tdd",
    "st":     "long-task-work-st",
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


def _is_brownfield(root: str) -> bool:
    """Heuristic: >3 source files AND >=5 git commits."""
    src = 0
    for _, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        src += sum(1 for f in files if f.endswith(_SRC_EXTS))
        if src > 3:
            break
    if src <= 3:
        return False
    try:
        n = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=root, stderr=subprocess.DEVNULL).strip())
        return n >= 5
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False


def route(root: str = ".") -> dict:
    out = {
        "ok": True,
        "errors": [],
        "needs_migration": False,
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
        if counts["legacy_sub_status"] > 0:
            out["needs_migration"] = True
            return out

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

        # current is null: either pick next or route to system ST
        if counts["total"] == 0:
            return out  # no active features
        if counts["passing"] == counts["total"]:
            out["next_skill"] = "long-task-st"
            return out

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

    # 4-7. Pre-init ladder
    if has_glob("docs/plans/*-ats.md"):
        out["next_skill"] = "long-task-init"
        return out
    if has_glob("docs/plans/*-design.md"):
        out["next_skill"] = "long-task-ats"
        return out
    if has_glob("docs/plans/*-ucd.md"):
        out["next_skill"] = "long-task-design"
        return out
    if has_glob("docs/plans/*-srs.md"):
        out["next_skill"] = "long-task-ucd"
        return out

    # 8. docs/rules/ populated — scan already done
    if has_glob("docs/rules/*.md"):
        out["next_skill"] = "long-task-requirements"
        return out

    # 9-10. Brownfield vs greenfield
    out["next_skill"] = ("long-task-brownfield-scan"
                        if _is_brownfield(root)
                        else "long-task-requirements")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", default=".", help="Project root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    args = ap.parse_args()

    r = route(args.root)
    if args.json:
        json.dump(r, sys.stdout)
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
              f"migration={r['needs_migration']} "
              f"counts={r['counts']}" + extra)
    sys.exit(0 if r["ok"] else 2)


if __name__ == "__main__":
    main()
