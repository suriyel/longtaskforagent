---
name: long-task-quality-check
description: "Run coverage and mutation gates — measurement only, never modify code. Input: feature_id."
---

# Quality Check — Hard Gate (Measurement Only)

Run coverage and mutation gates. Report results with gap details. **You MUST NOT modify any source or test files.** Your role is purely measurement and reporting.

## Your Task

1. Read execution rules: `skills/long-task-quality-check/references/quality-check-execution.md`
2. Read coverage recipes (if needed): `skills/long-task-quality-check/references/coverage-recipes.md`

## Key Constraints

- Scope: always feature-scoped (coverage + mutation scoped to changed files)
- Gate 1: Coverage — line >= threshold, branch >= threshold (scoped per unified decision)
- Gate 2: Mutation — score >= threshold (scoped per unified decision)
- Final test run: confirm all tests still pass
- **NEVER modify source or test files** — only measure and report
- Do NOT mark feature as "passing" in feature-list.json — only report results
- On FAIL: provide file:line-level gap details for fix agents

Report summary using Structured Return Contract below.

---

## Structured Return Contract

When all gates are complete (or if blocked), return your result in EXACTLY this format:

```markdown
## SubAgent Result: Quality Check
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — gates run, key outcomes]
### Metrics
line_coverage=N% (≥X%, PASS/FAIL), branch_coverage=N% (≥X%, PASS/FAIL), mutation_score=N% (≥X%, PASS/FAIL), test_count=N, all_tests_pass=true/false
### Coverage Gaps
[Omit section if coverage PASS. One per line: file:line-range | type (line|branch) | description]
### Surviving Mutants
[Omit section if mutation PASS. One per line: file:line | mutator | description]
### Artifacts
[report files read, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

**IMPORTANT**: Do NOT mark the feature as "passing" in feature-list.json — that is the orchestrator's responsibility. Only report the results.

---

## Integration

**Called by:** long-task-work (Step 6a) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** TDD Refactor completed (clean, passing code)
**Produces:** Coverage + mutation metrics with gap details on FAIL
**Chains to:** Coverage Fix (Step 6b) / Mutation Fix (Step 6c) on FAIL, or Persist (Step 7) on PASS
