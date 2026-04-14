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

## Context Discovery (do this yourself)

1. Read `feature-list.json` → extract feature object by id, `quality_gates`, `tech_stack`
2. Glob `docs/features/*` → find the feature design document matching this feature
3. Read `long-task-guide.md` → extract test command and environment activation

## Specification Input (from feature design doc)

Read these sections in order:
1. §7 Test Inventory — PRIMARY input. Each row → one or more test cases.
2. §3 Interface Contract — method signatures, pre/postconditions, §11.1 library annotations.
3. Existing Code Reuse — utilities, API clients, §11.1 library usage examples.
4. §5 Algorithm / Core Logic — boundary matrix (§5c), error table (§5d).
5. Clarification Addendum (if present) — user-approved resolutions.

## Key Constraints

- Write integration tests first, then unit tests (happy/error/boundary/security)
- Rule 1: Category coverage (FUNC/happy, FUNC/error, BNDRY/*, SEC/*)
- Rule 2: Negative test ratio >= 40%
- Rule 3: Low-value assertion ratio <= 20%
- Rule 4: "Wrong Implementation" challenge for each test
- Rule 5: Both UT + Integration layers mandatory (unless pure computation)
- Label tests by layer: # [unit] or # [integration]
- ALL tests MUST FAIL — if any passes, rewrite it

Report summary: success/fail, test file paths, test count, negative ratio.

---

## Orchestrator Notes

> Worker解析返回值的指引。SubAgent执行时忽略此段。

**Parse:** Read result summary.
- All tests fail → proceed to TDD Green.
- Failure → escalate to user.

## Integration

**Called by:** long-task-work (Step 3) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Produces:** Failing test files
**Chains to:** long-task-tdd-green (Step 4)
