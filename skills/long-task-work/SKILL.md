---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker — One Feature Per Cycle

Pure flow controller. Each step dispatches a SubAgent via `Agent()`, the SubAgent loads the discipline skill via `Skill()` and executes inline.

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

Dispatch SubAgent:
```
Agent(
  description="Feature Design for feature #{id}",
  prompt="Call Skill(skill='long-task:long-task-feature-design', args='{id}'). Follow the loaded instructions exactly."
)
```

**Parse:** Read result summary.
- Success → ask user to approve design doc via `AskUserQuestion`. If corrections → re-dispatch once.
- Failure → escalate to user.

Update pipeline marker: `Feature #{id} → Step 2 (Feature Design)`

## Step 3: TDD Red

Dispatch SubAgent:
```
Agent(
  description="TDD Red for feature #{id}",
  prompt="Call Skill(skill='long-task:long-task-tdd-red', args='{id}'). Follow the loaded instructions exactly."
)
```

**Parse:** All tests must fail → proceed to Step 4. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 3 (TDD Red)`

## Step 4: TDD Green

Dispatch SubAgent:
```
Agent(
  description="TDD Green for feature #{id}",
  prompt="Call Skill(skill='long-task:long-task-tdd-green', args='{id}'). Follow the loaded instructions exactly."
)
```

**Parse:** All tests pass with zero regressions → proceed to Step 5. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 4 (TDD Green)`

## Step 5: TDD Refactor

Dispatch SubAgent:
```
Agent(
  description="TDD Refactor for feature #{id}",
  prompt="Call Skill(skill='long-task:long-task-tdd-refactor', args='{id}'). Follow the loaded instructions exactly."
)
```

**Parse:** Clean (zero violations, §11 compliant) → proceed to Step 6. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 5 (TDD Refactor)`

## Step 6: Quality Gates

Dispatch SubAgent:
```
Agent(
  description="Quality Gates for feature #{id}",
  prompt="Call Skill(skill='long-task:long-task-quality-gates', args='{id}'). Follow the loaded instructions exactly."
)
```

**Parse:** All gates pass → proceed to Step 7. Failure → escalate.
Update pipeline marker: `Feature #{id} → Step 6 (Quality Gates)`

## Step 7: Feature-ST

Dispatch SubAgent:
```
Agent(
  description="Feature-ST for feature #{id}",
  prompt="Call Skill(skill='long-task:long-task-feature-st', args='{id}'). Follow the loaded instructions exactly."
)
```

**Parse:** Read result summary.
- Success → extract st_case_path, st_case_count. Proceed to Step 8.
- Failure with AI-fixable issues (code bugs, env issues) → fix and re-dispatch (no retry limit).
- Failure requiring human manual testing (credentials, hardware) → escalate via `AskUserQuestion`.

### Manual Test Review Gate

If result reports manual test cases:
1. For each manual case, call `AskUserQuestion` with test objective, steps, and verification points
2. Parse response: PASS / FAIL / SKIP
3. Update test case document with results
4. Re-evaluate: all MANUAL-PASS → proceed. Any MANUAL-FAIL → final FAIL. Any BLOCKED → final BLOCKED.

Update pipeline marker: `Feature #{id} → Step 7 (Feature-ST)`

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
- **Each step = Agent() dispatches SubAgent → SubAgent calls Skill() → executes inline**
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
5. `long-task:long-task-quality-gates` (Step 6)
6. `long-task:long-task-feature-st` (Step 7)
**Reads/Writes:** feature-list.json, task-progress.md, RELEASE_NOTES.md
