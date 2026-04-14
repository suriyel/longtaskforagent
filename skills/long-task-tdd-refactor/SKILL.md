---
name: long-task-tdd-refactor
description: "TDD Refactor phase — clean up code, run static analysis, verify §11 compliance. Input: feature_id."
---

# TDD Refactor — Clean Up + Compliance

Dispatch a SubAgent to refactor, run static analysis, and verify codebase compliance. Input: `feature_id`. SubAgent reads all documents itself.

**SubAgent Prompt:**

```
You are a TDD Refactor SubAgent. Your job: clean up code, pass static analysis, verify §11 compliance for feature #{feature_id}.

## Rules
Read `skills/long-task-tdd-shared/references/iron-law.md` — especially:
- No new functionality in this step
- Run tests after EVERY change

## Context Discovery (do this yourself)
1. Read `feature-list.json` → extract feature object, `tech_stack`
2. Glob `docs/plans/*-design.md` → read §11 (Codebase Conventions & Constraints)
3. Glob `docs/features/*` → find the feature design document, read "Existing Code Reuse" section
4. Read `long-task-guide.md` → extract test command

## Phase 1: Refactor
- Extract duplication, improve naming, simplify
- Run tests after EVERY change
- No new functionality

## Phase 2: Static Analysis Gate
If Design §11.4 lists static analysis tools: run each tool's command.
Fix ALL violations — violations are blocking.

## Phase 3: §11 Compliance Check
a) **Dependency versions (D3):** If feature design §3/§5 specifies library versions, spot-check that `requirements.txt` / `package.json` / `pom.xml` matches.

b) **§11.1/§11.2 compliance:** Run `git diff --name-only` for feature changes. For each non-empty "Replaces" entry in §11.1, grep new/modified files for the replaced import. Match → violation → fix. For each "Prohibited" entry in §11.2, grep new/modified files. Match → violation → fix.

c) **Existing code reuse:** Read feature design "Existing Code Reuse". For each REUSE item: grep implementation files for the expected import. Not imported but reimplemented → violation → replace with REUSE import.

On violation: fix, re-run tests, re-check.

## Exit
1. All tests pass
2. Zero static analysis violations
3. §11 compliance clean
Report summary: success/fail, static analysis result, compliance result.
```

**Dispatch:** `Agent(description="TDD Refactor for feature #{feature_id}")`

**Parse:** Read SubAgent summary. If clean → proceed to Quality Gates. If failure → escalate.

## Integration

**Called by:** long-task-work (Step 5)
**Requires:** TDD Green completed (tests passing)
**Produces:** Refactored code + static analysis clean + §11 compliant
**Chains to:** long-task-quality-gates (Step 6)
