---
name: long-task-hotfix
description: "Use when bugfix-request.json exists - validate, reproduce, root-cause, and enqueue a user-reported bug as a category=bugfix feature, then chain to Worker for TDD fix"
---

<EXTREMELY-IMPORTANT>
You are using the long-task-hotfix skill. This skill handles bugs found during user manual testing.

Your job is ONLY: validate → reproduce → root cause → enqueue → chain to Worker.
The actual fix (TDD, quality gates, ST, review) is handled by the Worker pipeline — do NOT implement fixes here.
</EXTREMELY-IMPORTANT>

## Step 1: Announce

Print: "I'm using the long-task-hotfix skill. Processing bugfix-request.json."

Use TodoWrite to track your progress through the 8 steps.

---

## Step 2: Validate Signal File

Run:
```bash
python scripts/validate_bugfix_request.py bugfix-request.json
```

If validation fails:
- Print the errors clearly
- `AskUserQuestion` asking the user to fix the file
- Re-validate after the user responds
- Do NOT proceed until validation passes

---

## Step 3: Orient

Read these files in order:
1. `bugfix-request.json` — understand title, description, severity, feature_id, reproduction steps
2. `feature-list.json` — find the linked feature (if `feature_id` non-null), read `tech_stack`, `quality_gates`; determine next available feature `id`
3. `long-task-guide.md` — environment activation commands
4. `env-guide.md` (if exists) — service start/stop commands
5. `task-progress.md` `## Current State` section — recent session history
6. `git log --oneline -10` — recent commit context

If `feature_id` is non-null: read the linked feature's entry from `feature-list.json` to understand context (its `ui` field, existing `srs_trace`, `st_case_path`).

---

## Step 4: Reproduce

**Goal**: Confirm the bug is reproducible before any analysis.

1. Activate environment per `long-task-guide.md`
2. If services are needed (determined from `env-guide.md` or `long-task-guide.md`): start them using `env-guide.md` Start commands; capture first 30 lines of startup output; record PIDs in `task-progress.md`
3. Follow `reproduction_steps` from `bugfix-request.json` exactly
4. Run the existing test suite; note any currently failing tests
5. Record: exact command run, exact output observed, confirmation that bug manifests

**HARD GATE — Cannot Reproduce:**
If the bug cannot be reproduced:
- Record the attempt in `task-progress.md`
- Stop all services started in this step (use `env-guide.md` Stop commands)
- Do NOT delete `bugfix-request.json`
- `AskUserQuestion` asking for clarification (more detailed steps, specific environment, sample data)
- **Stop here until reproduction is confirmed**

---

## Step 5: Root Cause Analysis

Execute the **4-phase systematic debugging process** from `skills/long-task-work/references/systematic-debugging.md`:

**Phase 1 — Root Cause Investigation**: collect full error evidence, find minimal reproduction, check recent git changes, trace data flow from entry point to failure.

**Phase 2 — Pattern Analysis**: find similar working code paths, compare contexts, check dependency versions and config values.

**Phase 3 — Hypothesis & Testing**: form ONE specific testable hypothesis; make ONE minimal diagnostic change to confirm or disprove it; if wrong, return to Phase 1.

**Phase 4 — Confirmed Root Cause**: arrive at a single confirmed root cause statement.

**Required output**: `"Root cause: [one-sentence statement]"`

**Iron Law**: NO FEATURE ENTRY before root cause is confirmed. If you cannot confirm root cause after 3 Phase 3 iterations, `AskUserQuestion` to ask the user for more context.

---

## Step 6: Enqueue as Bugfix Feature

Add a new feature entry to `feature-list.json`. Determine the next available `id` (max existing id + 1).

**New feature object:**
```json
{
  "id": <next available>,
  "wave": <current max wave id>,
  "category": "bugfix",
  "title": "Fix: <title from bugfix-request.json>",
  "description": "<actual_behavior from bugfix-request.json> — Root cause: <confirmed root cause>",
  "priority": "<Critical|Major → 'high', Minor → 'medium', Cosmetic → 'low'>",
  "status": "failing",
  "srs_trace": ["<FR-xxx from linked feature, or new FR-xxx if unlinked>"],
  "dependencies": [<fixed_feature_id>],
  "ui": <copy from linked feature's ui field, or false if feature_id is null>,
  "deprecated": false,
  "deprecated_reason": null,
  "supersedes": null,
  "bug_severity": "<severity from bugfix-request.json>",
  "bug_source": "manual-testing",
  "fixed_feature_id": <feature_id from bugfix-request.json, or null>,
  "root_cause": "<confirmed root cause one-sentence>"
}
```

**Notes:**
- `dependencies`: set to `[fixed_feature_id]` if non-null (ensures Worker processes the original feature before this fix); set to `[]` if null
- `ui`: if `feature_id` is non-null, use the linked feature's `ui` field; otherwise `false`
- `wave`: use the current maximum wave id from `feature-list.json`'s `waves` array
- **ATS hint**: if `fixed_feature_id` is non-null and ATS doc exists (`docs/plans/*-ats.md`), look up the linked feature's requirement in the ATS mapping table. Set `srs_trace` to include the linked feature's requirement IDs so downstream feature-st can derive the required test cases from SRS acceptance criteria

After adding, validate:
```bash
python scripts/validate_features.py feature-list.json
```

Fix any validation errors before continuing.

---

## Step 7: Update task-progress.md

Append a hotfix session entry after the current `## Current State` content:

```markdown
## Hotfix Session — YYYY-MM-DD: <bug title>
- **Severity**: <severity>
- **Bugfix Feature ID**: #<new id>
- **Fixed Feature**: #<fixed_feature_id> <feature title> (or "Unlinked")
- **Root Cause**: <one sentence>
- **Status**: Enqueued — Worker will handle TDD/Quality/ST/Review
```

Also update the `## Current State` header to reflect the new failing feature.

---

## Step 8: Finalize

1. Stop any services started in Step 4 using `env-guide.md` Stop commands; verify stopped
2. Delete `bugfix-request.json` (this is the final irreversible action — only after Steps 6 and 7 are complete and `validate_features.py` has passed)
3. Print:
   ```
   Bug #<id> enqueued as category=bugfix feature.
   Title: Fix: <title>
   Severity: <severity>
   Root cause: <one sentence>
   Worker will handle: TDD → Quality → ST → Review
   ```
4. Chain to: `long-task:long-task-work`

---

## Critical Rules

- **Validate signal file before any action** — validator must pass before Step 3
- **Must reproduce before analyzing** — "Cannot Reproduce" is a valid documented outcome; do NOT skip to root cause on an unreproduced bug
- **Root cause confirmed before enqueuing** — systematic debugging 4-phase process is mandatory; no guess-and-enqueue
- **Signal file deleted LAST** — deletion is the final irreversible action; `validate_features.py` must pass first
- **If both `bugfix-request.json` AND `increment-request.json` exist**: process this hotfix fully first; do NOT delete `increment-request.json`; it will be processed in the next session
- **Stop all services before chaining to Worker** — services started during reproduction must be stopped; Worker manages its own service lifecycle
- **This skill does NOT implement the fix** — Worker owns TDD/Quality/ST/Review; this skill only validates, diagnoses, and enqueues
- **No ad-hoc code edits here** — do not write tests or fix code during this skill; that is Worker's job

## Red Flags

These thoughts mean STOP — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "I can see the bug in the code, let me just fix it" | Root cause 4-phase first; then enqueue; Worker fixes |
| "I know the root cause, skipping Phase 1-3" | All 4 phases are mandatory; documenting them protects against wrong assumptions |
| "Can't reproduce but I know the cause" | Cannot Reproduce = stop; document in task-progress.md; ask user |
| "I'll skip the feature-list.json entry, fix it directly" | Every fix must be traceable in feature-list.json as category=bugfix |
| "Signal file has errors but the intent is clear" | Validator must pass; ask user to fix the file |
| "I'll delete the signal file first, then clean up" | Signal file deletion is the LAST step after everything is verified |
| "The fix is simple, Worker pipeline is overkill" | Worker ensures regression tests, coverage, ST cases, and review — all required |

## Integration

This skill is invoked by the `using-long-task` router when `bugfix-request.json` exists in the project root (highest priority — above increment). After this skill completes:
- `bugfix-request.json` is deleted
- A new `category: "bugfix"` feature is in `feature-list.json` with `status: "failing"`
- The router's next detection: `feature-list.json` exists with failing features → `long-task-work`
- Worker picks up the bugfix feature and runs the full TDD → Quality → ST → Review pipeline
