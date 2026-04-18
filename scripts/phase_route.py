#!/usr/bin/env python3
"""
Unified phase router for long-task-agent.

Replaces ``using-long-task`` detection rules and ``long-task-work``
Step 1-4 with a single call. Outputs the next skill to invoke plus
any state the caller needs (validation errors, migration flag, counts).

Routing precedence:
    1. bugfix-request.json            -> long-task-hotfix
    2. increment-request.json         -> long-task-increment
    3. feature-list.json              -> validate + count_pending bucketing
    4. docs/plans/*-ats.md            -> long-task-init
    5. docs/plans/*-design.md         -> long-task-ats
    6. docs/plans/*-ucd.md            -> long-task-design
    7. docs/plans/*-srs.md            -> long-task-ucd
    8. docs/rules/*.md (>=1)          -> long-task-requirements
    9. brownfield heuristic           -> long-task-brownfield-scan
   10. otherwise                      -> long-task-requirements

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

    # 3. Post-init: feature-list.json exists — validate + bucket
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
        if counts["no_sub_status"] > 0:
            out["needs_migration"] = True
            return out
        if counts["design"] > 0:
            out["next_skill"] = "long-task-work-design"
        elif counts["tdd"] > 0:
            out["next_skill"] = "long-task-work-tdd"
        elif counts["st"] > 0:
            out["next_skill"] = "long-task-work-st"
        elif counts["total"] > 0 and counts["done"] == counts["total"]:
            out["next_skill"] = "long-task-st"
        # else: total == 0 — no active features; next_skill stays None
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
        print(f"next={r['next_skill']} ok={r['ok']} "
              f"migration={r['needs_migration']} "
              f"counts={r['counts']}"
              + (f" errors={r['errors']}" if r["errors"] else ""))
    sys.exit(0 if r["ok"] else 2)


if __name__ == "__main__":
    main()
