---
name: long-task-tdd-red
description: "TDD Red phase — write failing tests for a feature's Test Inventory. Input: feature_id."
---

# TDD Red — Write Failing Tests

Dispatch a SubAgent to write failing tests for all Test Inventory rows. Input: `feature_id`. SubAgent reads all documents itself.

**SubAgent Prompt:**

```
You are a TDD Red phase SubAgent. Your job: write FAILING tests for feature #{feature_id}.

## Rules
Read these references first:
1. `skills/long-task-tdd-shared/references/iron-law.md` — Iron Law + test scenario rules (Rule 1-5)
2. `skills/long-task-tdd-shared/references/testing-anti-patterns.md` — full anti-pattern catalog

## Context Discovery (do this yourself)
1. Read `feature-list.json` → extract feature object with id={feature_id}, plus `quality_gates` and `tech_stack`
2. Glob `docs/features/*` → find the feature design document matching this feature
3. Read `long-task-guide.md` → extract test command

## Specification Input (from feature design doc)
Read these sections in order:
1. §7 Test Inventory — PRIMARY input. Each row → one or more test cases.
2. §3 Interface Contract — method signatures, pre/postconditions, §11.1 library annotations.
3. Existing Code Reuse — utilities, API clients, §11.1 library usage examples.
4. §5 Algorithm / Core Logic — boundary matrix (§5c), error table (§5d).
5. Clarification Addendum (if present) — user-approved resolutions.

## Test Writing Order
1. Analyze Test Inventory to identify external dependencies
2. Write integration tests first
3. Write unit tests (happy/error/boundary/security)
4. Run all tests → ALL MUST FAIL

## Hard Requirements
- Rule 1: Category coverage (FUNC/happy, FUNC/error, BNDRY/*, SEC/*)
- Rule 2: Negative test ratio >= 40%
- Rule 3: Low-value assertion ratio <= 20%
- Rule 4: "Wrong Implementation" challenge for each test
- Rule 5: Both UT + Integration layers mandatory (unless pure computation)
- Label tests by layer: # [unit] or # [integration]

## Exit
Run test suite. ALL tests MUST FAIL. If any passes → rewrite it.
Report summary: success/fail, test file paths, test count, negative ratio.
```

**Dispatch:** `Agent(description="TDD Red for feature #{feature_id}")`

**Parse:** Read SubAgent summary. If all tests fail → proceed to TDD Green. If failure → escalate.

## Integration

**Called by:** long-task-work (Step 3)
**Produces:** Failing test files
**Chains to:** long-task-tdd-green (Step 4)
