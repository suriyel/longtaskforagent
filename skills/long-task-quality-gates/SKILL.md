---
name: long-task-quality-gates
description: "Run coverage and mutation gates for a feature. Input: feature_id."
---

# Quality Gates — Coverage + Mutation

Execute coverage and mutation gates. Read all documents and thresholds yourself.

## Your Task

1. Read execution rules: `skills/long-task-quality-gates/references/quality-execution.md`
2. Read coverage recipes (if needed): `skills/long-task-quality/coverage-recipes.md`

## Context Discovery (do this yourself)

1. Read `feature-list.json` → extract feature object, `quality_gates` (thresholds), `tech_stack`, count active (non-deprecated) features
2. Read `long-task-guide.md` → extract coverage command, mutation commands (mutation_full, mutation_feature)
3. Identify feature's test files and changed source files from git diff

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
- All gates pass → proceed to Feature-ST.
- Failure → escalate to user.

## Integration

**Called by:** long-task-work (Step 6) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** TDD Refactor completed (clean, passing code)
**Produces:** Coverage + mutation metrics
**Chains to:** long-task-feature-st (Step 7)
