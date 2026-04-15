---
name: long-task-feature-design
description: "Use before TDD in a long-task project — produce feature-level detailed design with interface contracts, algorithm pseudocode, diagrams, and test inventory"
---

# Feature-Level Detailed Design

Produce the feature detailed design document. Read all documents yourself.

> **For `category: "bugfix"` features**: Focus on: (1) root cause documentation, (2) targeted fix approach, (3) regression test inventory. Skip full diagrams unless the bug directly touches those surfaces.

## Your Task

1. Read execution rules: `skills/long-task-feature-design/references/feature-design-execution.md`
2. Read template: `skills/long-task-feature-design/references/feature-design-template.md`

## Key Constraints

- Write complete design document to `docs/features/YYYY-MM-DD-<feature-name>.md`
- Every section (§2-§6) must be COMPLETE or "N/A — [reason]"
- Test Inventory negative ratio >= 40%
- Test Inventory categories should cover FUNC, BNDRY, SEC as appropriate based on SRS acceptance criteria
- §11 compliance: names follow §11.5, operations use §11.1 libraries, error handling per §11.6
- Do NOT start TDD

Report summary using Structured Return Contract from `feature-design-execution.md`.

---

## Orchestrator Notes

> Worker解析返回值的指引。SubAgent执行时忽略此段。

**Parse:** Parse SubAgent return text (Structured Return Contract).
- Verdict PASS → Ask user to review design doc via `AskUserQuestion`: "Please review feature design at {path}. Approve or provide corrections." If approved → proceed to TDD Red. If corrections → re-dispatch once with corrections.
- Verdict FAIL / BLOCKED / CLARIFY → escalate to user.

## Integration

**Called by:** long-task-work (Step 2) — Worker dispatches SubAgent, SubAgent loads this Skill and executes inline
**Requires:** System design doc, SRS, feature-list.json
**Produces:** `docs/features/YYYY-MM-DD-<feature-name>.md`
**Chains to:** long-task-tdd-red (Step 3)
