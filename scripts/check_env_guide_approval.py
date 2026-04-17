#!/usr/bin/env python3
"""
Check env-guide.md approval gate.

Rule: If §3 (Build & Execution Commands) or §4 (Codebase Constraints) have been
modified after the frontmatter's approved_date, the guide is **unapproved** —
Worker must block until the user reviews the change and updates approved_date.

How it decides "modified after approved_date":
  1. Read env-guide.md frontmatter → approved_date
  2. Use `git log --format=%cI -- env-guide.md` to list commit dates touching
     the file. For each such commit, run `git show --stat` and look for §3 / §4
     line markers in the unified diff.
  3. If the most recent commit touching §3 or §4 is newer than approved_date
     → FAIL.

First-generation exemption:
  - If approved_date is null AND the file was created in the current working
    tree (no git history yet, or only a single initial commit): PASS with a
    warning. After the first real edit to §3/§4, approval becomes mandatory.

Usage:
    python check_env_guide_approval.py [path/to/env-guide.md]
    python check_env_guide_approval.py [path] --json

Exit codes:
    0 — approved (or first-generation exemption)
    1 — unapproved: §3 or §4 modified after approved_date
    2 — env-guide.md not found or malformed frontmatter
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Match lines added/removed that touch §3 or §4 headers or content near them.
# We use a coarse heuristic: any +/- line inside a section beginning with ## §3 or ## §4.
SECTION_HEADER_RE = re.compile(r"^##\s+§(\d)\b", re.MULTILINE)


def parse_frontmatter(content: str) -> dict:
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


def run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return result.returncode, result.stdout
    except FileNotFoundError:
        return 127, ""


def parse_iso_date(s: str) -> datetime | None:
    """Parse to a timezone-aware datetime (UTC if input is naive)."""
    s = s.strip().strip('"').strip("'")
    if not s or s.lower() in ("null", "none"):
        return None
    # Try full ISO-8601 first
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        dt = None
    if dt is None:
        # Fall back to YYYY-MM-DD
        try:
            dt = datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def commits_touching_sections(repo: Path, relpath: str, sections: tuple[str, ...]) -> list[tuple[str, datetime]]:
    """
    Return [(commit_sha, commit_date)] for commits where the diff touches any
    section in `sections` (e.g. ("§3", "§4")). Most recent first.
    """
    # List all commits that touched the file, ISO-8601 committer date.
    rc, out = run_git(
        ["log", "--format=%H|%cI", "--", relpath],
        cwd=repo,
    )
    if rc != 0 or not out.strip():
        return []

    results: list[tuple[str, datetime]] = []
    for line in out.strip().splitlines():
        if "|" not in line:
            continue
        sha, date_str = line.split("|", 1)
        # Inspect the diff for this commit against its parent
        rc2, diff = run_git(
            ["show", "--unified=0", "--format=", sha, "--", relpath],
            cwd=repo,
        )
        if rc2 != 0:
            continue
        if touches_sections(diff, sections):
            d = parse_iso_date(date_str)
            if d is not None:
                results.append((sha, d))
    return results


def touches_sections(diff: str, sections: tuple[str, ...]) -> bool:
    """
    Detect whether the unified diff modifies any line inside one of the named
    sections. We track which section each hunk line falls into by scanning
    header lines in the diff context.

    Heuristic:
      - `+++`/`---` lines are metadata, skip.
      - `@@` hunk headers contain nearby context; they sometimes include the
        enclosing Markdown heading (git --function-context). We instead
        conservatively treat ANY +/- line as "touches §3" if the hunk
        header contains §3.
      - If hunk header does NOT contain a section marker, fall back to
        matching +/- lines that begin with `## §3` or `## §4` (edits to the
        header itself) or that contain inline `§3`/`§4` references.
    """
    current_section: str | None = None
    in_hunk = False
    for line in diff.splitlines():
        if line.startswith("@@"):
            in_hunk = True
            # Try to infer section from the hunk header context
            for s in sections:
                if s in line:
                    current_section = s
                    break
            else:
                current_section = None
            continue
        if not in_hunk:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith(" "):
            # Context line — check for section headers to update current_section
            hm = SECTION_HEADER_RE.match(line[1:] if len(line) > 1 else "")
            if hm:
                sec = f"§{hm.group(1)}"
                current_section = sec if sec in sections else None
            continue
        if line.startswith("+") or line.startswith("-"):
            body = line[1:]
            # Header-edit case: +/- of a section header
            hm = SECTION_HEADER_RE.match(body)
            if hm:
                sec = f"§{hm.group(1)}"
                if sec in sections:
                    return True
                current_section = None
                continue
            if current_section in sections:
                return True
    return False


def check(path: str) -> dict:
    p = Path(path).resolve()
    if not p.exists():
        return {"status": "missing", "path": str(p),
                "message": f"env-guide.md not found: {p}"}

    content = p.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    if not fm:
        return {"status": "malformed", "path": str(p),
                "message": "missing YAML frontmatter"}

    approved_by_raw = fm.get("approved_by", "").strip().strip('"').strip("'")
    approved_by_is_null = (not approved_by_raw) or approved_by_raw.lower() in ("null", "none")
    approved_date = parse_iso_date(fm.get("approved_date", ""))

    repo = p.parent
    # Walk up to find git root
    for candidate in [repo] + list(repo.parents):
        if (candidate / ".git").exists():
            repo = candidate
            break
    try:
        relpath = str(p.relative_to(repo))
    except ValueError:
        relpath = p.name

    # First-generation exemption: approved_by is null AND no commit has modified §3/§4
    rc, _ = run_git(["rev-parse", "--is-inside-work-tree"], cwd=repo)
    if rc != 0:
        return {"status": "approved", "path": str(p),
                "reason": "not in a git repo — exempt from approval gate",
                "frontmatter": fm}

    commits = commits_touching_sections(repo, relpath, ("§3", "§4"))

    if approved_by_is_null:
        if not commits:
            return {"status": "approved", "path": str(p),
                    "reason": "first-generation exemption (no §3/§4 history)",
                    "frontmatter": fm}
        # There IS history touching §3/§4, but approved_by is null → unapproved
        latest_sha, latest_date = commits[0]
        return {"status": "unapproved", "path": str(p),
                "reason": "frontmatter approved_by is null and §3/§4 have been modified",
                "latest_section_commit": latest_sha,
                "latest_section_commit_date": latest_date.isoformat(),
                "frontmatter": fm}

    if approved_date is None:
        return {"status": "unapproved", "path": str(p),
                "reason": "approved_by set but approved_date is missing/invalid",
                "frontmatter": fm}

    if not commits:
        # approved_by set but §3/§4 never modified in git → approved
        return {"status": "approved", "path": str(p),
                "reason": "no §3/§4 edits in git history",
                "frontmatter": fm}

    latest_sha, latest_date = commits[0]
    if latest_date > approved_date:
        return {"status": "unapproved", "path": str(p),
                "reason": (f"§3 or §4 modified in commit {latest_sha[:8]} at "
                           f"{latest_date.isoformat()}, which is after "
                           f"approved_date {approved_date.isoformat()}"),
                "latest_section_commit": latest_sha,
                "latest_section_commit_date": latest_date.isoformat(),
                "approved_date": approved_date.isoformat(),
                "frontmatter": fm}

    return {"status": "approved", "path": str(p),
            "reason": f"approved_date {approved_date.isoformat()} "
                      f"is at or after latest §3/§4 edit",
            "approved_date": approved_date.isoformat(),
            "frontmatter": fm}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", nargs="?", default="env-guide.md",
                        help="Path to env-guide.md (default: ./env-guide.md)")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    args = parser.parse_args()

    result = check(args.path)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = result.get("status")
        if status == "approved":
            print(f"OK: env-guide.md approved — {result.get('reason', '')}")
        elif status == "missing":
            print(result.get("message", "env-guide.md not found"))
        elif status == "malformed":
            print(f"MALFORMED: {result.get('message', 'invalid frontmatter')}")
        else:
            print(f"UNAPPROVED: {result.get('reason', 'approval required')}")
            latest = result.get("latest_section_commit_date")
            approved = result.get("approved_date")
            if latest:
                print(f"  Latest §3/§4 edit: {latest}")
            if approved:
                print(f"  Current approved_date: {approved}")
            print("  Action: review changes, update env-guide.md frontmatter approved_by/approved_date")

    if result.get("status") == "approved":
        return 0
    if result.get("status") in ("missing", "malformed"):
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
