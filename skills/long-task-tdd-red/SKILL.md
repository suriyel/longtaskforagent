---
name: long-task-tdd-red
description: "TDD Red phase — write failing tests for a feature's Test Inventory. Input: feature_id."
---

# TDD Red — Write Failing Tests

Write failing tests for all Test Inventory rows. Read all documents yourself.

## Your Task

1. Read execution rules: `skills/long-task-tdd-red/references/tdd-red-execution.md`
2. Read shared rules: `skills/long-task-tdd-shared/references/iron-law.md`
3. Read anti-patterns: `skills/long-task-tdd-shared/references/testing-anti-patterns.md`

## Specification Input (from feature design doc)

Read these sections in order:
1. §7 Test Inventory — PRIMARY input. Each row → one or more test cases.
2. §3 Interface Contract — method signatures, pre/postconditions, §11.1 library annotations.
3. Existing Code Reuse — utilities, API clients, §11.1 library usage examples.
4. §5 Algorithm / Core Logic — boundary matrix (§5c), error table (§5d).
5. Clarification Addendum (if present) — user-approved resolutions.
6. Related existing tests (Step 1b) — explore dependency features' test files for assertion style, fixtures, imports, mock patterns.

## Key Constraints

- Write integration tests first, then unit tests (happy/error/boundary/security)
- Rule 1: Category coverage (FUNC/happy, FUNC/error, BNDRY/*, SEC/*)
- Rule 2: Negative test ratio >= 40%
- Rule 3: Low-value assertion ratio <= 20%
- Rule 4: "Wrong Implementation" challenge for each test
- Rule 5: Both UT + Integration layers mandatory (unless pure computation)
- Label tests by layer: # [unit] or # [integration]
- ALL tests MUST FAIL (exit code != 0 is SUCCESS). Exit 0 means tests are wrong — rewrite
- Follow related existing test conventions (Step 1b) for consistency. §11.5 and Test Inventory take precedence.
- Test output protocol: `[test-quiet]` first → on PASS (wrong!) rewrite; on all-FAIL (correct!) done. If unclear → `[test-detail]`

Return result using the Structured Return Contract below.

---

## Structured Return Contract

When all tests are written and verified failing, return your result in EXACTLY this format:

```markdown
## SubAgent Result: TDD Red
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — tests written, all confirmed failing (RED)]
### Metrics
test_count=N, negative_ratio=N% (≥40%, PASS/FAIL), all_tests_fail=true/false
### Artifacts
[test files created, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## Integration

**Called by:** long-task-work (Step 3) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Produces:** Failing test files
**Chains to:** long-task-tdd-green (Step 4)
