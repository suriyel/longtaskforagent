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
5c. Read internal API contracts: Read {design_doc_path} Section 6.2 — locate rows where this feature appears as Provider or Consumer. These define the exact schemas this feature must produce or consume.
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
- Test Inventory main categories (FUNC/BNDRY/SEC/UI/PERF/INTG) must cover all ATS-required categories for this feature's requirement(s)
- Features with external dependencies must have ≥1 INTG row per dependency type; pure-computation features: "INTG: N/A"
- Features with `"ui": true` MUST have a complete Visual Rendering Contract (§Visual Rendering Contract): all visual elements listed, rendering technology specified, positive rendering assertions defined. "N/A" is only valid for `"ui": false`. For each positive rendering assertion, at least one `UI/render` Test Inventory row must exist. Missing rows → FAIL.
- **Codebase constraints** (if Design doc §13 exists): Read {design_doc_path} §13 for codebase conventions. Interface Contract method names must follow §13.5 naming conventions. Error handling must follow §13.6 pattern. Dependencies must use §13.1 internal libraries where applicable. Do not reference prohibited APIs from §13.2.
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

Read the SubAgent's returned text and locate the `**status**:` line (unified contract field; legacy `### Verdict:` line may coexist for backward compatibility).

- **`**status**: pass`** (legacy: `### Verdict: PASS`)
  1. Verify the design document file exists at `output_path`
  2. **Visual Rendering Contract spot-check (ui:true only):** The main Agent (not the SubAgent) reads the `## Visual Rendering Contract` section from the produced document and verifies:
     - At least one visual element is listed with a concrete DOM/Canvas selector (not generic like "the page" or "the UI")
     - Rendering technology is specified (Canvas 2D / WebGL / DOM / SVG / CSS)
     - At least one positive rendering assertion references a specific visual outcome (not just "element is visible")
     - The number of `UI/render` rows in the Test Inventory matches or exceeds the number of Visual Rendering Contract elements
     - **If any check fails**: re-dispatch SubAgent with feedback: "Visual Rendering Contract is incomplete — [specific gap]. A blank page that passes Layer 1 error detection is NOT acceptable. Every visual element the user should see must be listed with a testable selector and assertion."
  3. Extract Next Step Inputs: `feature_design_doc`, `test_inventory_count`, `tdd_task_count`
  4. Record in `task-progress.md`: "Feature Design: PASS ({N} test scenarios, {M} TDD tasks)"
  5. If `assumption_count > 0`: append to `task-progress.md`: "({K} assumptions documented in Clarification Addendum)"
  6. Proceed to TDD (Steps 5-7)

- **`**status**: clarify`** (legacy: `### Verdict: CLARIFY`)
  1. Read the Ambiguities table — extract all categorized questions
  2. Present to user via `AskUserQuestion` in a structured format:
     ```
     Feature Design Clarification Required: Feature #{id} ({title})

     While analyzing requirements and design documents, {N} ambiguity(ies) were found
     that affect the design. For each, a suggested interpretation is provided —
     you may accept it, provide a different answer, or say "skip" to use the suggestion as an assumption.

     Ambiguity 1 [{category}]: {description}
       Source: {source}
       Impact: {impact}
       Suggested: {suggested_interpretation}
       → Your answer (or "accept" to use suggested, or "skip" to assume):

     Ambiguity 2 [{category}]: ...
     ```
  3. Parse user responses — for each ambiguity, record:
     - "accept" or specific answer → Resolution with Authority = "user-approved"
     - "skip" → Resolution = suggested interpretation with Authority = "assumed"
  4. **Approval gate**: After all answers collected, present a summary via `AskUserQuestion`:
     ```
     Clarification Summary for Feature #{id}:
     1. [{category}] {description} → Resolution: {answer} (Authority: {authority})
     2. ...

     Proceed with these resolutions? (yes / revise #N)
     ```
     - If approved: proceed to step 5
     - If user wants revision: re-ask specific items, then re-present summary
  5. Construct a **Clarification Addendum** and re-dispatch the SubAgent with the original prompt PLUS:
     ```
     ## Clarification Addendum (user-approved resolutions)
     | # | Category | Original Ambiguity | Resolution | Authority |
     |---|----------|--------------------|------------|-----------|
     | 1 | {category} | {description} | {resolution} | user-approved / assumed |

     Apply these resolutions as authoritative constraints. Do NOT re-flag these
     as ambiguities. Incorporate them into the design as if they were in the
     original SRS/Design documents.
     ```
  6. Record in `task-progress.md`: "Feature Design: CLARIFY ({N} ambiguities resolved) → re-dispatching"
  7. **Max 2 clarification rounds**: If SubAgent returns `CLARIFY` a second time after receiving clarifications, escalate remaining ambiguities to user:
     "Persistent specification gaps found after 2 clarification rounds. Consider using `long-task-increment` to update the SRS/Design documents."
     - If user says "SRS needs updating": record gap in `task-progress.md`, suggest `long-task-increment`, skip to next eligible feature
     - If user provides final answers: incorporate and re-dispatch one last time
     - If still unresolvable: set to BLOCKED

- **`**status**: fail`** (legacy: `### Verdict: FAIL`)
  1. Read the Issues table — identify which sections are incomplete
  2. Re-dispatch SubAgent with additional context if needed (max 2 retries)
  3. If still failing, escalate to user via `AskUserQuestion`

- **`**status**: blocked`** (legacy: `### Verdict: BLOCKED`)
  1. Read the Issues table — identify the blocker
  2. Escalate to user via `AskUserQuestion`

## Integration

**Called by:** long-task-work (Step 4)
**Requires:** System design doc, SRS, feature-list.json
**Produces:** `docs/features/YYYY-MM-DD-<feature-name>.md` (written by SubAgent)
**Chains to:** long-task-tdd (via Work Steps 5-7)
