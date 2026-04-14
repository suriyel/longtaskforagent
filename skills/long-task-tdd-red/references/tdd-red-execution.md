# TDD Red — SubAgent Execution Reference

You are a TDD Red SubAgent. Write failing tests for ALL Test Inventory rows.

## Step 1: Load Context

1. Read `feature-list.json` → extract feature object by ID, `quality_gates`, `tech_stack`
2. Glob `docs/features/*` → find the feature design document matching this feature
3. Read `long-task-guide.md` → extract test command and environment activation

## Step 2: Read Specification

From the feature design document, read in order:

1. **§7 Test Inventory** — PRIMARY. Each row maps to one or more test cases.
2. **§3 Interface Contract** — method signatures, pre/postconditions. When annotated "Uses: [§11.1 library]", test setup should mock/stub the §11.1 library, NOT the replaced alternative.
3. **Existing Code Reuse** — utilities, API clients, §11.1 library usage examples. Tests use the same imports/patterns.
4. **§5 Algorithm / Core Logic** — boundary matrix (§5c), error table (§5d), §11 library mapping (§5e).
5. **Clarification Addendum** (if present) — user-approved resolutions override defaults.

Sections to SKIP: §2 Data-Flow, §4 Sequence, §6 State (read on demand only if Test Inventory "Traces To" references them).

## Step 3: Write Tests

**Order:**
1. Analyze Test Inventory + feature's `srs_trace` to identify external dependencies
2. Write integration tests first (verify external dependency connectivity)
3. Write unit tests (happy/error/boundary/security)

**Rules (all mandatory):**

| Rule | Requirement |
|------|-------------|
| Category Coverage | FUNC/happy, FUNC/error, BNDRY/*, SEC/* — state N/A explicitly if not applicable |
| Negative Ratio ≥ 40% | negative_test_count / total_test_count >= 0.40 |
| Low-Value ≤ 20% | low_value_count / total_assertion_count <= 0.20 |
| Wrong Implementation | Each test must fail for 2-3 plausible wrong implementations |
| Two Layers | Unit + Integration mandatory (exception: pure computation, state explicitly) |
| Label Tests | `# [unit]` or `# [integration]` comment per test |

## Step 4: Verify All FAIL

Run `[test-quiet]` from `long-task-guide.md`. **ALL tests MUST FAIL.** If any test passes → run `[test-detail]` to identify which test → rewrite it.

Activate environment per `long-task-guide.md`. If tool missing: diagnose, escalate. Never skip.

## Summary

Report: success/fail, test file paths created, total test count, negative ratio, low-value ratio.
