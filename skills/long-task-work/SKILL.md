---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker — One Feature Per Cycle

Pure flow controller. Each step dispatches a discipline skill in isolated context (SubAgent when available, inline otherwise) and parses its Structured Return Contract.

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

> **DISPATCH** `long-task:long-task-feature-design` args=`{id}` — isolated context

**Parse:** Parse SubAgent return text (Structured Return Contract).
- Verdict PASS → ask user to approve design doc via `AskUserQuestion`. If corrections → re-dispatch once.
- Verdict FAIL / BLOCKED / CLARIFY → escalate to user.

Update pipeline marker: `Feature #{id} → Step 2 (Feature Design)`

## Step 3: TDD Red

> **DISPATCH** `long-task:long-task-tdd-red` args=`{id}` — isolated context

**Parse:** All tests fail (RED PASS) → proceed to Step 4. Any test passes or framework error → escalate.
Update pipeline marker: `Feature #{id} → Step 3 (TDD Red)`

## Step 4: TDD Green

> **DISPATCH** `long-task:long-task-tdd-green` args=`{id}` — isolated context

**Parse:** All tests pass with zero regressions → proceed to Step 5. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 4 (TDD Green)`

## Step 5: TDD Refactor

> **DISPATCH** `long-task:long-task-tdd-refactor` args=`{id}` — isolated context

**Parse:** Clean (zero violations, §11 compliant) → proceed to Step 6. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 5 (TDD Refactor)`

## Step 6: Quality Gates (gate-fix-recheck loop, max 20 rounds)

Initialize: `retry_count = 0`

### Step 6a: Quality Check (hard gate — measurement only)

> **DISPATCH** `long-task:long-task-quality-check` args=`{id}` — isolated context

**Parse:** Parse SubAgent return text (Structured Return Contract).
- Verdict PASS → proceed to Step 7.
- Verdict BLOCKED → escalate to user.
- Verdict FAIL → save `Coverage Gaps` and/or `Surviving Mutants` sections → proceed to Step 6b.

### Step 6b: Coverage Fix (MUST run before mutation fix)

**Skip if coverage PASS.** Otherwise:
> **DISPATCH** `long-task:long-task-coverage-fix` args=`{id}` — isolated context
> Append to prompt: Coverage Gaps section from Quality Check result

**Parse:** Verdict PASS → proceed to Step 6c. Verdict FAIL / BLOCKED → escalate to user.

**Rationale**: Running mutation on uncovered code is wasteful — coverage gaps must be closed first.

### Step 6c: Mutation Fix

**Skip if mutation PASS.** Otherwise:
> **DISPATCH** `long-task:long-task-mutation-fix` args=`{id}` — isolated context
> Append to prompt: Surviving Mutants section from Quality Check result

**Parse:** Verdict PASS → proceed to Step 6d. Verdict FAIL / BLOCKED → escalate to user.

### Step 6d: Recheck

`retry_count += 1`. Re-dispatch Quality Check (same as Step 6a).
- Verdict PASS → proceed to Step 7.
- Verdict FAIL + `retry_count < 20` → loop back to Step 6b.
- Verdict FAIL + `retry_count >= 20` → escalate to user.

Update pipeline marker: `Feature #{id} → Step 6 (Quality Gates) [round {retry_count}]`

## Step 7: Persist (inline)

- Update `RELEASE_NOTES.md` (Keep a Changelog format; bugfix → `### Fixed`)
- Update `task-progress.md`:
  - `## Current State`: progress count (X/Y passing), last completed, next feature
  - Append session entry:
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    - Quality Gates: N% line, N% branch, N% mutation
    ```
- Mark feature `"status": "passing"` in `feature-list.json`
- Validate: `python scripts/validate_features.py feature-list.json`

## Step 8: End Session

- Output: **Feature #\<id\> (\<title\>) — DONE.** Next: Feature #\<next_id\> (\<next_title\>)
- If no failing non-deprecated features remain: "All active features passing — development complete."
- End session — **never loop back to Step 1**

## Critical Rules

- **One feature per session** — external `scripts/auto_loop.py` handles multi-feature
- **Strict step order** — no skipping, no reordering
- **Each step = dispatch discipline skill (isolated context) → execute → return Structured Result**
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
**Dispatches SubAgents (in strict order):**
1. `long-task:long-task-feature-design` (Step 2)
2. `long-task:long-task-tdd-red` (Step 3)
3. `long-task:long-task-tdd-green` (Step 4)
4. `long-task:long-task-tdd-refactor` (Step 5)
5. `long-task:long-task-quality-check` (Step 6a)
6. `long-task:long-task-coverage-fix` (Step 6b, if needed)
7. `long-task:long-task-mutation-fix` (Step 6c, if needed)
**Reads/Writes:** feature-list.json, task-progress.md, RELEASE_NOTES.md
