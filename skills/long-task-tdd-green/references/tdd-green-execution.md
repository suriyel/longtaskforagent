# TDD Green — SubAgent Execution Reference

You are a TDD Green SubAgent. Write MINIMAL code to make all tests pass.

## Step 1: Load Context

1. Read `feature-list.json` → extract feature object by ID, `quality_gates`, `tech_stack`
2. Glob `docs/features/*` → find the feature design document
3. Read `long-task-guide.md` → extract test command, full test command
4. Find test files created by TDD Red (recent test files matching the feature)

## Step 2: Read Implementation Constraints

From the feature design document:

1. **§3 Interface Contract** — §11.1 library annotations ("Uses: ...")
2. **§5e** — §11 library usage mapping table
3. **Existing Code Reuse** — all items with Action (REUSE/EXTEND/PATTERN), file paths, signatures

**Codebase constraint rules:**
- §11.1: Use mandatory internal libraries — do NOT use replaced alternatives
- §11.2: Do not use prohibited APIs
- §11.5: Follow naming conventions
- §11.6: Follow error handling pattern
- REUSE items: import and call directly — do NOT reimplement
- EXTEND items: subclass or extend — do NOT copy-paste
- PATTERN items: follow same structural pattern

## Step 3: Implement

- Implement fresh from tests — never reference pre-deleted code
- One test at a time: make the simplest failing test pass first, then the next
- No premature optimization or extra features
- Use the exact import statements and call patterns from §11.1 library usage examples

## Step 4: Verify

1. Run test command → ALL tests pass
2. Run full test command → zero regressions

If any test fails after implementation: diagnose root cause, fix. If still failing after 3 attempts → escalate.

## Summary

Report: success/fail, implementation file paths, test pass count, regressions count.
