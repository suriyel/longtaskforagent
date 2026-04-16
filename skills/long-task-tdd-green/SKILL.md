---
name: long-task-tdd-green
description: "TDD Green phase — write minimal implementation to make all tests pass. Input: feature_id."
---

# TDD Green — Minimal Implementation

Write minimal code to make all tests pass. Read all documents yourself.

## Your Task

1. Read execution rules: `skills/long-task-tdd-green/references/tdd-green-execution.md`
2. Read shared rules: `skills/long-task-tdd-shared/references/iron-law.md`,`docs/rules`
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
- Test output protocol: `[test-quiet]` first → on PASS done; on FAIL → `[test-detail]` for errors

Return result using the Structured Return Contract below.

---

## Structured Return Contract

When implementation is complete and all tests pass, return your result in EXACTLY this format:

```markdown
## SubAgent Result: TDD Green
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — implementation complete, all tests passing, zero regressions]
### Metrics
test_count=N, tests_pass=N, regressions=0
### Artifacts
[implementation files created/modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## Integration

**Called by:** long-task-work (Step 4) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** TDD Red completed (failing tests exist)
**Produces:** Implementation code + passing tests
**Chains to:** long-task-tdd-refactor (Step 5)
