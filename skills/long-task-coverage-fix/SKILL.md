---
name: long-task-coverage-fix
description: "Fix coverage gaps by adding tests for uncovered lines/branches. Input: feature_id."
---

# Coverage Fix — Add Tests for Uncovered Code

Receive coverage gap details from the Worker prompt. Write tests to close the gaps.

## Your Task

1. Read execution rules: `skills/long-task-coverage-fix/references/coverage-fix-execution.md`
2. Read shared rules: `skills/long-task-coverage-fix/references/iron-law.md`
3. Read anti-patterns: `skills/long-task-coverage-fix/references/testing-anti-patterns.md`

## Key Constraints

- Input: `Coverage Gaps` section passed in the Agent prompt (file:line-range | type | description)
- Write tests to cover the identified gaps
- Run `[test-quiet]` to confirm all tests pass — no broken code
- **Do NOT run** coverage or mutation tools — the caller measures after you return
- **Do NOT mark** feature as "passing" in feature-list.json

Return result using the Structured Return Contract below.

---

## Structured Return Contract

```markdown
## SubAgent Result: Coverage Fix
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — tests added, gaps addressed]
### Metrics
tests_added=N, gaps_addressed=N/M, all_tests_pass=true/false
### Artifacts
[test files created/modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## Integration

**Called by:** long-task-test-retrofit — dispatches SubAgent with Coverage Gaps
**Requires:** Coverage measurement returned FAIL with gap details
**Produces:** Additional tests covering identified gaps
