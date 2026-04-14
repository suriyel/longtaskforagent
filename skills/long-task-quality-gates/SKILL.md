---
name: long-task-quality-gates
description: "Run coverage and mutation gates for a feature. Input: feature_id."
---

# Quality Gates — Coverage + Mutation

Dispatch a SubAgent to execute coverage and mutation gates. Input: `feature_id`. SubAgent reads all documents and thresholds itself.

**SubAgent Prompt:**

```
You are a Quality Gates SubAgent. Execute coverage and mutation gates for feature #{feature_id}.

## Rules
Read these references:
1. `skills/long-task-quality-gates/references/quality-execution.md` — gate execution rules, structured return contract
2. `skills/long-task-quality/coverage-recipes.md` — tool setup per language (if needed)

## Context Discovery (do this yourself)
1. Read `feature-list.json` → extract feature object, `quality_gates` (thresholds), `tech_stack`, count active (non-deprecated) features
2. Read `long-task-guide.md` → extract coverage command, mutation commands (mutation_full, mutation_feature)
3. Identify feature's test files and changed source files from git diff

## Gates (sequential)
1. Coverage Gate: line >= threshold, branch >= threshold
2. Mutation Gate: score >= threshold (scope: full if active features <= mutation_full_threshold, else feature-scoped)
3. Final test run: confirm all tests still pass

Do NOT mark feature as "passing" in feature-list.json — only report results.
Report summary: success/fail, line_coverage%, branch_coverage%, mutation_score%.
```

**Dispatch:** `Agent(description="Quality Gates for feature #{feature_id}")`

**Parse:** Read SubAgent summary. If all gates pass → proceed to Feature-ST. If failure → escalate.

## Integration

**Called by:** long-task-work (Step 6)
**Requires:** TDD Refactor completed (clean, passing code)
**Produces:** Coverage + mutation metrics
**Chains to:** long-task-feature-st (Step 7)
