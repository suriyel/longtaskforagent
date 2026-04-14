---
name: long-task-tdd-green
description: "TDD Green phase — write minimal implementation to make all tests pass. Input: feature_id."
---

# TDD Green — Minimal Implementation

Dispatch a SubAgent to write minimal code making all tests pass. Input: `feature_id`. SubAgent reads all documents itself.

**SubAgent Prompt:**

```
You are a TDD Green phase SubAgent. Your job: write MINIMAL implementation to make all tests pass for feature #{feature_id}.

## Rules
Read `skills/long-task-tdd-shared/references/iron-law.md` — especially:
- Implement fresh from tests — never reference pre-deleted code
- One test at a time: simplest failing test first
- No premature optimization or extra features

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

Rules:
- §11.1: Use mandatory internal libraries, NOT replaced alternatives
- §11.2: Do not use prohibited APIs
- §11.5: Follow naming conventions
- §11.6: Follow error handling pattern
- REUSE items: import and call directly — do NOT reimplement
- EXTEND items: subclass or extend — do NOT copy-paste
- PATTERN items: follow same structural pattern

## Exit
1. Run test command → ALL tests pass
2. Run full test command → zero regressions
Report summary: success/fail, implementation file paths, test pass count.
```

**Dispatch:** `Agent(description="TDD Green for feature #{feature_id}")`

**Parse:** Read SubAgent summary. If all tests pass with zero regressions → proceed to TDD Refactor. If failure → escalate.

## Integration

**Called by:** long-task-work (Step 4)
**Requires:** TDD Red completed (failing tests exist)
**Produces:** Implementation code + passing tests
**Chains to:** long-task-tdd-refactor (Step 5)
