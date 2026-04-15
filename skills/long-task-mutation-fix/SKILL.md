---
name: long-task-mutation-fix
description: "Fix surviving mutants by strengthening tests or removing dead code. Input: feature_id."
---

# Mutation Fix — Kill Surviving Mutants

Receive surviving mutant details from the Worker prompt. Strengthen tests or remove dead code.

## Your Task

1. Read execution rules: `skills/long-task-mutation-fix/references/mutation-fix-execution.md`
2. Read shared rules: `skills/long-task-mutation-fix/references/iron-law.md`
3. Read anti-patterns: `skills/long-task-mutation-fix/references/testing-anti-patterns.md`

## Key Constraints

- Input: `Surviving Mutants` section passed in the Agent prompt (file:line | mutator | description)
- Classify each mutant: equivalent → document, real gap → strengthen test, unreachable → remove dead code
- Run `[test-quiet]` to confirm all tests pass — no broken code
- **Do NOT run** mutation or coverage tools — that is Quality Check's responsibility
- **Do NOT mark** feature as "passing" in feature-list.json

Return result using the Structured Return Contract below.

---

## Structured Return Contract

```markdown
## SubAgent Result: Mutation Fix
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — mutants addressed]
### Metrics
mutants_addressed=N/M, equivalent_mutants=N, tests_strengthened=N, dead_code_removed=N, all_tests_pass=true/false
### Artifacts
[test/source files modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## Integration

**Called by:** long-task-work (Step 6c) — Worker dispatches SubAgent with Surviving Mutants
**Requires:** Quality Check returned mutation FAIL with mutant details; Coverage Fix completed (if needed)
**Produces:** Strengthened tests / removed dead code
**Chains to:** Recheck (Step 6d)
