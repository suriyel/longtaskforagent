---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline"
---

# Worker — One Feature Per Cycle

Pure flow controller. Each step launches an independent SubAgent to load and execute the corresponding discipline Skill, then parses its Structured Return Contract.

**Announce at start:** "I'm using the long-task-work skill. Let me orient myself."

## Step 1: Orient (inline)

- Grep `feature-list.json` for features with `"status": "failing"` — skip `"deprecated": true`
- Pick next by priority, then array position
- **Dependency check**: verify all `dependencies[]` have `"status": "passing"`. If unsatisfied → skip, pick next. If none eligible → warn user via `AskUserQuestion`
- **Resume check**: Read `task-progress.md` `## Current State` `Pipeline:` marker — if same Feature #{id} and step > 1, jump to that step; otherwise start at Step 2
- Update `task-progress.md` `## Current State` with pipeline marker:
  ```
  Pipeline: Feature #{id} → Step 1 (Orient) → starting
  ```

## Step 2: Feature Design

> **DISPATCH** create independent SubAgent(use General or Agent) args=`{id}` — load then execute skill `long-task:long-task-feature-design` in the subagent

**Parse:** Parse SubAgent return text (Structured Return Contract).
- Verdict PASS → ask user to approve design doc via `AskUserQuestion`. If corrections → re-dispatch once.
- Verdict FAIL / BLOCKED / CLARIFY → escalate to user.

Update pipeline marker: `Feature #{id} → Step 2 (Feature Design)`

## Step 3: TDD Red

> **DISPATCH** create independent SubAgent(use General or Agent) args=`{id}` — load then execute skill `long-task:long-task-tdd-red` in the subagent

**Parse:** All tests fail (RED PASS) → proceed to Step 4. Any test passes or framework error → escalate.
Update pipeline marker: `Feature #{id} → Step 3 (TDD Red)`

## Step 4: TDD Green

> **DISPATCH** create independent SubAgent(use General or Agent) args=`{id}` — load then execute skill `long-task:long-task-tdd-green` in the subagent

**Parse:** All tests pass with zero regressions → proceed to Step 5. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 4 (TDD Green)`

## Step 5: TDD Refactor

> **DISPATCH** independent SubAgent(use General or Agent) args=`{id}`— load then execute skill `long-task:long-task-tdd-refactor` in the subagent 

**Parse:** Clean (zero violations, §11 compliant) → proceed to Step 6. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 5 (TDD Refactor)`

## Step 6: Persist (inline)

- Update `RELEASE_NOTES.md` (Keep a Changelog format; bugfix → `### Fixed`)
- Update `task-progress.md`:
  - `## Current State`: progress count (X/Y passing), last completed, next feature
  - Append session entry:
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    ```
- Mark feature `"status": "passing"` in `feature-list.json`
- Validate: `python scripts/validate_features.py feature-list.json`

## Step 7: End Session

- Output: **Feature #\<id\> (\<title\>) — DONE.** Next: Feature #\<next_id\> (\<next_title\>)
- If no failing non-deprecated features remain: "All active features passing — development complete."
- End session — **never loop back to Step 1**

## Critical Rules

- **One feature per session** — external `scripts/auto_loop.py` handles multi-feature
- **Strict step order** — no skipping, no reordering
- **Each step = launch independent SubAgent → load discipline Skill → return Structured Result**
- **Never mark "passing" without fresh evidence**
- **Systematic debugging only** — on error, read `references/systematic-debugging.md`; trace root cause
- **Update progress before ending session**
- **Never leave broken code**

## Integration

**Called by:** using-long-task (when feature-list.json exists)
**Dispatches SubAgents (in strict order):**
1. `long-task:long-task-feature-design` (Step 2)
2. `long-task:long-task-tdd-red` (Step 3)
3. `long-task:long-task-tdd-green` (Step 4)
4. `long-task:long-task-tdd-refactor` (Step 5)
**Reads/Writes:** feature-list.json, task-progress.md, RELEASE_NOTES.md
