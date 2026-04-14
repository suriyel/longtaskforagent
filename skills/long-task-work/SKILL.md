---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker — One Feature Per Cycle

Pure flow controller. Each step = SubAgent + Skill. Input to each SubAgent: `feature_id`.

**Announce at start:** "I'm using the long-task-work skill. Let me orient myself."

## Step 1: Orient (inline)

- Grep `feature-list.json` for features with `"status": "failing"` — skip `"deprecated": true`
- Pick next by priority, then array position
- **Dependency check**: verify all `dependencies[]` have `"status": "passing"`. If unsatisfied → skip, pick next. If none eligible → warn user via `AskUserQuestion`
- Update `task-progress.md` `## Current State` with pipeline marker:
  ```
  Pipeline: Feature #{id} → Step 1 (Orient) → starting
  ```

## Step 2: Feature Design

Invoke `long-task:long-task-feature-design` with `feature_id`.
After success → ask user to approve design doc via `AskUserQuestion`. If corrections → re-dispatch once.
Update pipeline marker.

## Step 3: TDD Red

Invoke `long-task:long-task-tdd-red` with `feature_id`.
All tests must fail. Update pipeline marker.

## Step 4: TDD Green

Invoke `long-task:long-task-tdd-green` with `feature_id`.
All tests must pass, zero regressions. Update pipeline marker.

## Step 5: TDD Refactor

Invoke `long-task:long-task-tdd-refactor` with `feature_id`.
Static analysis clean, §11 compliant. Update pipeline marker.

## Step 6: Quality Gates

Invoke `long-task:long-task-quality-gates` with `feature_id`.
Coverage + mutation must meet thresholds. Update pipeline marker.

## Step 7: Feature-ST

Invoke `long-task:long-task-feature-st` with `feature_id`.
All test cases must pass. Update pipeline marker.

## Step 8: Persist (inline)

- Update `RELEASE_NOTES.md` (Keep a Changelog format; bugfix → `### Fixed`)
- Update `task-progress.md`:
  - `## Current State`: progress count (X/Y passing), last completed, next feature
  - Append session entry:
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    - Quality Gates: N% line, N% branch, N% mutation
    - Feature-ST: N cases, all PASS
    ```
- Mark feature `"status": "passing"` in `feature-list.json`
- Set `"st_case_path"` and `"st_case_count"` on feature
- Validate: `python scripts/validate_features.py feature-list.json`

## Step 9: End Session

- Output: **Feature #\<id\> (\<title\>) — DONE.** Next: Feature #\<next_id\> (\<next_title\>)
- If no failing non-deprecated features remain: "All active features passing — next session begins System Testing."
- End session — **never loop back to Step 1**

## Critical Rules

- **One feature per session** — external `scripts/auto_loop.py` handles multi-feature
- **Strict step order** — no skipping, no reordering
- **Each step = SubAgent + Skill** — always invoke via Skill tool
- **Never mark "passing" without fresh evidence**
- **Systematic debugging only** — on error, read `references/systematic-debugging.md`; trace root cause
- **Update progress before ending session**
- **Never leave broken code**

## On Error

1. Collect evidence (error message, stack trace, git diff)
2. Reproduce the issue
3. Trace root cause (read `references/systematic-debugging.md`)
4. Write failing test for the bug
5. Fix with single targeted change
6. Give up after 3 attempts → escalate to user

## Integration

**Called by:** using-long-task (when feature-list.json exists)
**Invokes (in strict order):**
1. `long-task:long-task-feature-design` (Step 2)
2. `long-task:long-task-tdd-red` (Step 3)
3. `long-task:long-task-tdd-green` (Step 4)
4. `long-task:long-task-tdd-refactor` (Step 5)
5. `long-task:long-task-quality-gates` (Step 6)
6. `long-task:long-task-feature-st` (Step 7)
**Reads/Writes:** feature-list.json, task-progress.md, RELEASE_NOTES.md
