---
name: long-task-quality-gates
description: "DEPRECATED — split into long-task-quality-check, long-task-coverage-fix, long-task-mutation-fix. Do not invoke directly."
---

# Quality Gates — Redirect

This skill has been split into three phase skills:

1. **`long-task:long-task-quality-check`** — Hard gate (measurement only, never modifies code)
2. **`long-task:long-task-coverage-fix`** — Fix coverage gaps (add tests for uncovered lines/branches)
3. **`long-task:long-task-mutation-fix`** — Fix surviving mutants (strengthen tests, remove dead code)

The Worker (`long-task-work`) invokes them in a gate-fix-recheck loop at Step 6.

## Shared References

- `skills/long-task-quality/references/quality-execution.md` — Original execution reference (superseded by `quality-check-execution.md`)
- `skills/long-task-quality/coverage-recipes.md` — Coverage/mutation tool setup recipes (still used by quality-check)
