---
name: long-task-tdd-green
description: "TDD Green phase — write minimal implementation to make all tests pass. Input: feature_id."
---

# TDD Green — Minimal Implementation

Write minimal code to make all tests pass. Read all documents yourself.

## Your Task

1. Read execution rules: `skills/long-task-tdd-green/references/tdd-green-execution.md`
2. Read shared rules: `skills/long-task-tdd-shared/references/iron-law.md`

## Context Discovery (do this yourself)

1. Read `feature-list.json` → extract feature object, `quality_gates`, `tech_stack`
2. Glob `docs/features/*` → find the feature design document
3. Read `long-task-guide.md` → extract test command, full test command
4. Find the test files created by TDD Red (look for recent test files matching the feature)

## Implementation Constraints (from feature design doc)

Read these sections:
1. §3 Interface Contract — §11.1 library annotations ("Uses: ...")
2. §5 Algorithm / Core Logic — §11 library usage mapping (§5e)
3. Existing Code Reuse — all items with Action (REUSE/EXTEND/PATTERN)

## Key Constraints

- Implement fresh from tests — never reference pre-deleted code
- One test at a time: simplest failing test first
- No premature optimization or extra features
- §11.1: Use mandatory internal libraries, NOT replaced alternatives
- §11.2: Do not use prohibited APIs
- §11.5: Follow naming conventions
- §11.6: Follow error handling pattern
- REUSE items: import and call directly — do NOT reimplement
- EXTEND items: subclass or extend — do NOT copy-paste
- PATTERN items: follow same structural pattern
- ALL tests must pass, zero regressions

Report summary: success/fail, implementation file paths, test pass count.

---

## Orchestrator Notes

> Worker解析返回值的指引。SubAgent执行时忽略此段。

**Parse:** Read result summary.
- All tests pass with zero regressions → proceed to TDD Refactor.
- Failure → escalate to user.

## Integration

**Called by:** long-task-work (Step 4) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** TDD Red completed (failing tests exist)
**Produces:** Implementation code + passing tests
**Chains to:** long-task-tdd-refactor (Step 5)
