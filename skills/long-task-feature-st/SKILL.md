---
name: long-task-feature-st
description: "Use after quality gates pass in a long-task project — executes black-box acceptance testing per feature, generates ISO/IEC/IEEE 29119 compliant test case documents"
---

# Feature-ST — SubAgent Dispatch

Dispatch a SubAgent to execute black-box acceptance testing. Input: `feature_id`. SubAgent reads all documents itself.

**SubAgent Prompt:**

```
You are a Feature-ST execution SubAgent for black-box acceptance testing of feature #{feature_id}.

## Your Task
1. Read execution rules: `skills/long-task-feature-st/references/feature-st-execution.md`
2. Follow checklist exactly (Steps 1-7): Load Context → Load Template → Derive Test Cases → Write Document → Validate → Execute → Cleanup
3. Return summary

## Context Discovery (do this yourself)
1. Read `feature-list.json` → extract feature object by id, `quality_gates`, `tech_stack`, optional `st_case_template_path`, `st_case_example_path`
2. Glob `docs/plans/*-design.md` → find design doc
3. Glob `docs/plans/*-srs.md` → find SRS doc
4. Glob `docs/plans/*-ats.md` → find ATS doc (if exists)
5. Glob `docs/features/*` → find feature design doc

## Key Constraints
- Do NOT mark feature as "passing" in feature-list.json — only report results
- ALL automated test cases must be executed one by one — no skipping
- Manual test cases (已自动化: No) → mark as PENDING-MANUAL, include full details in return

Report summary: success/fail, st_case_path, st_case_count.
```

**Dispatch:** `Agent(description="Feature-ST for feature #{feature_id}")`

**Parse:** Read SubAgent summary.
- Success → extract st_case_path, st_case_count. Proceed to Persist.
- Failure with AI-fixable issues (code bugs, env issues) → fix and re-dispatch (no retry limit).
- Failure requiring human manual testing (credentials, hardware) → escalate via `AskUserQuestion`.

### Manual Test Review Gate

If SubAgent reports manual test cases:
1. For each manual case, call `AskUserQuestion` with test objective, steps, and verification points
2. Parse response: PASS / FAIL / SKIP
3. Update test case document with results
4. Re-evaluate: all MANUAL-PASS → proceed. Any MANUAL-FAIL → final FAIL. Any BLOCKED → final BLOCKED.

## Integration

**Called by:** long-task-work (Step 7)
**Requires:** Quality Gates passed (Step 6)
**Produces:** `docs/test-cases/feature-{id}-{slug}.md`
**Chains to:** Persist (Step 8)
