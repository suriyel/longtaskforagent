---
name: long-task-feature-design
description: "Use before TDD in a long-task project — produce feature-level detailed design with interface contracts, algorithm pseudocode, diagrams, and test inventory"
---

# Feature-Level Detailed Design — SubAgent Dispatch

Delegate feature detailed design production to a SubAgent with fresh context. The main Agent only dispatches and parses the structured result — it never reads design/SRS document sections or writes the design document directly.

**Announce at start:** "I'm using the long-task-feature-design skill to produce a detailed design via SubAgent."

## When to Run

- Worker Step 2, before TDD (Steps 3-5)
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
- `ats_doc_path` — path to ATS doc (`docs/plans/*-ats.md`), if it exists; omit otherwise
- `constraints` — constraints[] from feature-list.json root
- `assumptions` — assumptions[] from feature-list.json root
- `constraints_section` — line range of §11 (Codebase Conventions & Constraints) in the design doc — §11 is always present
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
5. Read ATS mapping table: Read {ats_doc_path} (only if ATS doc exists) — locate the mapping rows for the feature's requirement ID(s) (from srs_trace); extract required categories
5c. Read internal API contracts: Read {design_doc_path} Section 6.2 — locate rows where this feature appears as Provider or Consumer. These define the exact schemas this feature must produce or consume.
5d. Read §11 (Codebase Conventions): Read {design_doc_path} §11 section — always present
5e. Discover existing code: For each passing dependency feature in the feature object's dependencies[], read implementation files to discover reusable utilities, API clients, data access patterns, error helpers, §11.1 library usage examples
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
- Test Inventory main categories (FUNC/BNDRY/SEC/PERF/INTG) must cover all ATS-required categories for this feature's requirement(s)
- Features with external dependencies must have ≥1 INTG row per dependency type; pure-computation features: "INTG: N/A"
- **Codebase constraints enforcement** (§11 always present):
  - Read {design_doc_path} §11 for codebase conventions (empty tables = no constraints)
  - Step 1c: scan passing dependency implementations for §11.1 usage patterns and reusable code
  - Step 1b: check for CONSTRAINT-CONFLICT (§11 vs. feature requirements)
  - §3 Interface Contract: names follow §11.5; operations use §11.1 libraries; reuse existing code per Existing Code Reuse section
  - §5 Algorithm: pseudocode uses §11.1 libraries; error handling follows §11.6; §11 library mapping table is mandatory
  - Verification Checklist: §11 compliance items 9-11 are mandatory
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
  4. Record in `task-progress.md`: "Feature Design: PASS ({N} test scenarios, {M} TDD tasks)"
  5. If `assumption_count > 0`: append to `task-progress.md`: "({K} assumptions documented in Clarification Addendum)"
  6. Proceed to TDD (Steps 3-5)

- **`### Verdict: CLARIFY`**
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
**Chains to:** long-task-tdd (via Work Steps 3-5)
