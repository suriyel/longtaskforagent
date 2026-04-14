---
name: long-task-tdd-refactor
description: "TDD Refactor phase — clean up code, run static analysis, verify §11 compliance. Input: feature_id."
---

# TDD Refactor — Clean Up + Compliance

Refactor code, run static analysis, and verify codebase compliance. Read all documents yourself.

## Your Task

1. Read execution rules: `skills/long-task-tdd-refactor/references/tdd-refactor-execution.md`
2. Read shared rules: `skills/long-task-tdd-shared/references/iron-law.md`

## Context Discovery (do this yourself)

1. Read `feature-list.json` → extract feature object, `tech_stack`
2. Glob `docs/plans/*-design.md` → read §11 (Codebase Conventions & Constraints)
3. Glob `docs/features/*` → find the feature design document, read "Existing Code Reuse" section
4. Read `long-task-guide.md` → extract test command

## Key Constraints

- **Phase 1: Refactor** — extract duplication, improve naming, simplify. Run tests after EVERY change. No new functionality.
- **Phase 2: Static Analysis Gate** — if Design §11.4 lists static analysis tools, run each tool's command. Fix ALL violations — violations are blocking.
- **Phase 3: §11 Compliance Check:**
  - a) Dependency versions (D3): spot-check that `requirements.txt` / `package.json` / `pom.xml` matches feature design §3/§5 library versions.
  - b) §11.1/§11.2 compliance: `git diff --name-only` for feature changes. Grep new/modified files for replaced imports (§11.1) and prohibited APIs (§11.2). Match → violation → fix.
  - c) Existing code reuse: for each REUSE item, grep implementation files for expected import. Not imported but reimplemented → violation → replace with REUSE import.
- On violation: fix, re-run tests, re-check.
- All tests must pass, zero static analysis violations, §11 compliance clean.

Report summary: success/fail, static analysis result, compliance result.

---

## Orchestrator Notes

> Worker解析返回值的指引。SubAgent执行时忽略此段。

**Parse:** Read result summary.
- Clean → proceed to Quality Gates.
- Failure → escalate to user.

## Integration

**Called by:** long-task-work (Step 5) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** TDD Green completed (tests passing)
**Produces:** Refactored code + static analysis clean + §11 compliant
**Chains to:** long-task-quality-gates (Step 6)
