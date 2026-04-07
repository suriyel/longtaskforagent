---
name: long-task-finalize
description: "Use after ST Go verdict — generate usage examples and finalize release documentation via SubAgent"
---

# Finalize — Post-ST Documentation & Examples

Generate scenario-based usage examples and finalize release documentation after System Testing passes with a Go/Conditional-Go verdict.

**Announce at start:** "I'm using the long-task-finalize skill. ST passed — generating examples and finalizing documentation."

**Idempotent**: Safe to re-invoke after ST defect-fix loops. Overwrites `examples/` content cleanly on each run.

<HARD-GATE>
Do NOT invoke this skill unless the ST verdict is Go or Conditional-Go. If the verdict is No-Go, loop back to Worker for fixes instead.
</HARD-GATE>

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Gather Context

- Read `feature-list.json` — all passing non-deprecated features, `tech_stack`, `quality_gates`
- Read SRS document (`docs/plans/*-srs.md`) — requirement descriptions, user personas
- Read Design document (`docs/plans/*-design.md`) — architecture, public API surface
- Read `task-progress.md` — session history for ST summary entry
- Read `RELEASE_NOTES.md` — current state for version entry
- Note paths for SubAgent dispatch

### 2. Generate Examples (SubAgent)

Dispatch the example-generator SubAgent to produce scenario-based usage examples.

1. Construct SubAgent prompt:
   ```
   You are an Example Generator SubAgent.

   ## Your Task
   1. Read the agent definition: Read <skills_root>/../agents/example-generator.md
   2. Follow the process to generate scenario-based usage examples
   3. Return your result using the Structured Return Contract

   ## Input Parameters
   - feature-list.json: <path>
   - SRS: <srs_path>
   - Design: <design_path>
   - tech_stack: <tech_stack_json>
   - Working directory: <project_root>
   ```

2. Dispatch:
   ```
   Agent(
     description = "Generate usage examples for all features",
     prompt = [constructed prompt]
   )
   ```

3. Parse return contract:
   - **PASS**: All planned scenarios generated and verified
   - **PARTIAL**: Some examples generated; log warnings for gaps
   - **FAIL**: Log error; proceed anyway — examples are non-blocking

Record in `task-progress.md`:
```
- Examples: <verdict> — N scenarios, N examples generated, N features covered
```

### 3. Update RELEASE_NOTES.md

Add ST completion and version entry (moved from ST Persist):
- Add entry under `[Unreleased]` or create versioned section if appropriate
- Include: ST verdict, date, test summary (categories run, defects found/fixed)
- Reference the ST report document path

### 4. Update task-progress.md

Add ST session summary entry (moved from ST Persist):
- ST categories executed, pass/fail counts
- Defects found and fixed (with severity)
- Full mutation score
- Final quality metrics
- Example generation results (from Step 2)

### 5. Persist

- Git commit all documentation artifacts:
  ```
  git add examples/ RELEASE_NOTES.md task-progress.md
  git commit -m "docs: finalize release — examples, release notes, progress update"
  ```
- Validate:
  ```bash
  python scripts/validate_features.py feature-list.json
  ```

### 6. Summary

Output completion summary:
> **Finalize — DONE**
>
> Examples: N scenarios generated (N features covered, N skipped)
> RELEASE_NOTES.md: Updated with ST completion
> task-progress.md: Updated with ST session summary

## Critical Rules

- **Non-blocking** — example generation failure does NOT retroactively change the Go verdict
- **Idempotent** — safe to re-run; overwrites examples/ cleanly
- **SubAgent for examples only** — RELEASE_NOTES and task-progress are updated directly by this skill (not by the SubAgent)
- **No new features** — do not add, modify, or test any features; documentation only
- **Follow project conventions** — examples match the project's language, style, and patterns

## Integration

**Called by:** `long-task-st` (Step 13, after Go/Conditional-Go verdict)
**Reads:** `feature-list.json`, `docs/plans/*-srs.md`, `docs/plans/*-design.md`, `task-progress.md`, `RELEASE_NOTES.md`, implementation code
**Produces:** `examples/` (usage examples + README.md), updated `RELEASE_NOTES.md`, updated `task-progress.md`
**Agent:** `agents/example-generator.md`
