---
name: long-task-feature-design
description: "Use before TDD in a long-task project — produce feature-level detailed design with interface contracts, algorithm pseudocode, diagrams, and test inventory"
---

# Feature-Level Detailed Design — SubAgent Dispatch

Delegate feature detailed design production to a SubAgent with fresh context. The main Agent only dispatches and parses the structured result — it never reads design/SRS/UCD document sections or writes the design document directly.

**Announce at start:** "I'm using the long-task-feature-design skill to produce a detailed design via SubAgent."

## When to Run

- Worker Step 4, before TDD (Steps 5-7)
- For every feature (condensed version for `category: "bugfix"` features)
- Invoked by `long-task-work` as a sub-skill (not directly by router)

> **For `category: "bugfix"` features**: SubAgent should focus on: (1) root cause documentation (from `root_cause` field), (2) targeted fix approach, (3) regression test inventory from SRS acceptance criteria (via `srs_trace`). Skip full interface contracts, data flow diagrams, and state diagrams unless the bug directly touches those surfaces.

## Step 1: Gather Path Parameters

Collect these from the current session state. Do NOT read document contents yourself:

- `feature_json` — current feature object from feature-list.json (compact JSON)
- `quality_gates_json` — quality_gates from feature-list.json (compact JSON)
- `tech_stack_json` — tech_stack from feature-list.json (compact JSON)
- `design_doc_path` — path to design doc (`docs/plans/*-design.md`)
- `design_start` / `design_end` — line range of the §4.N subsection (from Orient Document Lookup)
- `srs_doc_path` — path to SRS doc (`docs/plans/*-srs.md`)
- `srs_start` / `srs_end` — line range of the FR-xxx subsection (from Orient Document Lookup)
- `ucd_doc_path` — path to UCD doc (only if `"ui": true`; omit otherwise)
- `ucd_start` / `ucd_end` — line range of relevant UCD sections (if applicable)
- `ats_doc_path` — path to ATS doc (`docs/plans/*-ats.md`), if it exists; omit otherwise
- `constraints` — constraints[] from feature-list.json root
- `assumptions` — assumptions[] from feature-list.json root
- `output_path` — target file: `docs/features/YYYY-MM-DD-<feature-name>.md`
- `working_dir` — project working directory

## Step 2: Construct SubAgent Prompt

```
You are a Feature Design execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-design/references/feature-design-execution.md
2. Read the template: Read {skills_root}/long-task-feature-design/references/feature-design-template.md
3. Read design section: Read {design_doc_path} lines {design_start} to {design_end}
4. Read SRS section: Read {srs_doc_path} lines {srs_start} to {srs_end}
5. Read UCD sections: Read {ucd_doc_path} lines {ucd_start} to {ucd_end} (only if ui:true)
5b. Read ATS mapping table: Read {ats_doc_path} (only if ATS doc exists) — locate the mapping rows for the feature's requirement ID(s) (from srs_trace); extract required categories
6. Follow the execution rules to produce the detailed design document
7. Write the document to: {output_path}
8. Return your result using the Structured Return Contract in the execution rules

## Input Parameters
- Feature: {feature_json}
- quality_gates: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Constraints: {constraints}
- Assumptions: {assumptions}
- ATS doc path: {ats_doc_path} (or "none" if no ATS doc exists)
- Working directory: {working_dir}

## Key Constraints
- Write the complete design document to {output_path}
- Every section (§2-§6) must be COMPLETE or have "N/A — [reason]"
- Test Inventory negative ratio must be >= 40%
- Test Inventory main categories (FUNC/BNDRY/SEC/UI/PERF) must cover all ATS-required categories for this feature's requirement(s)
- Do NOT start TDD — only produce the design document
```

## Step 3: Dispatch SubAgent

**Claude Code:** Use the `Agent` tool:
```
Agent(
  description = "Feature Design for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode:** Use `@mention` syntax or the platform's native subagent mechanism with the same prompt content.

## Step 4: Parse Result

Read the SubAgent's returned text and locate the `### Verdict:` line:

- **`### Verdict: PASS`**
  1. Verify the design document file exists at `output_path`
  2. Extract Next Step Inputs: `feature_design_doc`, `test_inventory_count`, `tdd_task_count`
  3. Record in `task-progress.md`: "Feature Design: PASS ({N} test scenarios, {M} TDD tasks)"
  4. Proceed to TDD (Steps 5-7)

- **`### Verdict: FAIL`**
  1. Read the Issues table — identify which sections are incomplete
  2. Re-dispatch SubAgent with additional context if needed (max 2 retries)
  3. If still failing, escalate to user via `AskUserQuestion`

- **`### Verdict: BLOCKED`**
  1. Read the Issues table — identify the blocker
  2. Escalate to user via `AskUserQuestion`

## Integration

**Called by:** long-task-work (Step 4)
**Requires:** System design doc, SRS, feature-list.json
**Produces:** `docs/features/YYYY-MM-DD-<feature-name>.md` (written by SubAgent)
**Chains to:** long-task-tdd (via Work Steps 5-7)
