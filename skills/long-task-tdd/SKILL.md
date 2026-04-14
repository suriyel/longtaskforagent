---
name: long-task-tdd
description: "DEPRECATED — split into long-task-tdd-red, long-task-tdd-green, long-task-tdd-refactor. Do not invoke directly."
---

# TDD — Redirect

This skill has been split into three phase skills:

1. **`long-task:long-task-tdd-red`** — Write failing tests (Red phase)
2. **`long-task:long-task-tdd-green`** — Minimal implementation (Green phase)
3. **`long-task:long-task-tdd-refactor`** — Refactor + static analysis + §11 compliance (Refactor phase)

The Worker (`long-task-work`) invokes them in sequence as Steps 3, 4, 5.

## Shared References

- `skills/long-task-tdd-shared/references/iron-law.md` — Iron Law + test scenario rules
- `skills/long-task-tdd-shared/references/testing-anti-patterns.md` — Full anti-pattern catalog
- `skills/long-task-tdd/prompts/implementer-prompt.md` — Implementer SubAgent prompt template (used by TDD Green)
