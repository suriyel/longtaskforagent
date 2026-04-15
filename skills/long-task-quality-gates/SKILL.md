---
name: long-task-quality-gates
description: "Run coverage and mutation gates for a feature. Input: feature_id."
---

# Quality Gates — Coverage + Mutation

Execute coverage and mutation gates. Read all documents and thresholds yourself.

## Your Task

1. Read execution rules: `skills/long-task-quality-gates/references/quality-execution.md`
2. Read coverage recipes (if needed): `skills/long-task-quality/coverage-recipes.md`

## Key Constraints

- Gate 1: Coverage — line >= threshold, branch >= threshold
- Gate 2: Mutation — score >= threshold (scope: full if active features <= mutation_full_threshold, else feature-scoped)
- Final test run: confirm all tests still pass
- Do NOT mark feature as "passing" in feature-list.json — only report results

Report summary using Structured Return Contract from `quality-execution.md`.

---

## Orchestrator Notes

> Worker解析返回值的指引。SubAgent执行时忽略此段。

**Parse:** Read result summary.
- All gates pass → proceed to Persist.
- Failure → escalate to user.

## Integration

**Called by:** long-task-work (Step 6) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** TDD Refactor completed (clean, passing code)
**Produces:** Coverage + mutation metrics
**Chains to:** Persist (Step 7, inline in Worker)
