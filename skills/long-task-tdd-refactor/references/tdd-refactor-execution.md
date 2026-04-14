# TDD Refactor — SubAgent Execution Reference

You are a TDD Refactor SubAgent. Clean up code, pass static analysis, verify §11 compliance.

## Step 1: Load Context

1. Read `feature-list.json` → extract feature object by ID, `tech_stack`
2. Glob `docs/plans/*-design.md` → read §11 (Codebase Conventions & Constraints)
3. Glob `docs/features/*` → find the feature design document, read "Existing Code Reuse" section
4. Read `long-task-guide.md` → extract test command

## Step 2: Refactor

- Extract duplication, improve naming, simplify
- Run `[test-quiet]` after EVERY change; on FAIL run `[test-detail]` for errors
- No new functionality in this step

## Step 3: Static Analysis Gate

If Design §11.4 lists static analysis tools (e.g., `npx eslint .`, `mvn checkstyle:check`, `mypy src/`):

1. Run each tool's command
2. Fix ALL violations — violations are **blocking**
3. Re-run tests after fixes
4. Tools read their own config; do not parse configs manually

## Step 4: §11 Compliance Check

**a) Dependency versions (D3):**
If feature design §3 or §5 specifies third-party library versions, spot-check that `requirements.txt` / `package.json` / `pom.xml` matches. Flag mismatches.

**b) §11.1/§11.2 compliance:**
1. Run `git diff --name-only` to identify feature's new/modified files
2. Read Design §11.1: for each non-empty "Replaces" entry, grep new/modified source files for the replaced import pattern. Match → violation → fix.
3. Read Design §11.2: for each non-empty "Prohibited" entry, grep new/modified source files. Match → violation → fix.

**c) Existing code reuse verification:**
1. Read feature design "Existing Code Reuse" section
2. For each REUSE item: grep implementation files for the expected import
3. If REUSE item NOT imported but equivalent functionality reimplemented → violation → replace with REUSE import

On any violation: fix, re-run tests to confirm no regression, re-check.

## Step 5: Final Verify

Run `[test-quiet]` — all tests pass, zero static analysis violations, §11 compliance clean.

## Summary

Report: success/fail, refactorings count, static analysis violations fixed, §11 compliance result (D3, §11.1/§11.2, Reuse).
