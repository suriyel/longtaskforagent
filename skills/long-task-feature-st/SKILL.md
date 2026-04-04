---
name: long-task-feature-st
description: "Use after quality gates pass in a long-task project — independently manages test environment lifecycle (start/cleanup), executes black-box acceptance testing per feature, generates ISO/IEC/IEEE 29119 compliant test case documents"
---

# Feature-ST — SubAgent Dispatch

Delegate black-box acceptance testing to a SubAgent with fresh context. The main Agent only dispatches and parses the structured result — it never reads SRS/Design/UCD sections, test case documents, or execution output directly.

**Announce at start:** "I'm using the long-task-feature-st skill to run acceptance testing via SubAgent."

## Step 1: Gather Path Parameters

Collect file paths from the current session state (do NOT read the file contents yourself):

- `feature_id` — current feature ID
- `feature_json` — current feature object from feature-list.json (compact JSON)
- `design_doc_path` — path to `docs/plans/*-design.md`
- `srs_doc_path` — path to `docs/plans/*-srs.md`
- `ucd_doc_path` — path to `docs/plans/*-ucd.md` (only if `"ui": true`; omit otherwise)
- `ats_doc_path` — path to `docs/plans/*-ats.md` (if exists; omit otherwise)
- `plan_doc_path` — path to `docs/features/YYYY-MM-DD-<feature-name>.md` (from Feature Design step)
- `env_guide_path` — `env-guide.md` (if exists)
- `quality_gates_json` — quality_gates thresholds from feature-list.json
- `tech_stack_json` — tech_stack from feature-list.json
- `working_dir` — project working directory
- `st_case_template_path` — from feature-list.json root (optional)
- `st_case_example_path` — from feature-list.json root (optional)

## Step 2: Construct SubAgent Prompt

```
You are a Feature-ST execution SubAgent for black-box acceptance testing.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-st/references/feature-st-execution.md
2. Follow the checklist exactly (Steps 1-8): Load Context → Load Template → Derive Test Cases → Write Document → Validate → Execute → Visual Assessment (ui:true) → Cleanup
3. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}

## Document Paths (read these yourself using the Read tool)
- Design doc: {design_doc_path}
- SRS doc: {srs_doc_path}
- UCD doc: {ucd_doc_path} (omit if not UI)
- ATS doc: {ats_doc_path} (omit if not present)
- Feature design plan: {plan_doc_path}
- Environment guide: {env_guide_path}

## Template/Example (optional)
- ST case template: {st_case_template_path} (omit if not set)
- ST case example: {st_case_example_path} (omit if not set)

## Key Constraints
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- You MUST manage service lifecycle: start before tests, cleanup after all tests
- UI test cases require browser-based verification — no skip
- If environment cannot start after 3 attempts, set Verdict to BLOCKED
- ALL automated test cases must be executed one by one — no skipping
- Manual test cases (已自动化: No) must NOT be executed by SubAgent — mark as PENDING-MANUAL in the traceability matrix and include full case details in the Manual Test Cases section of the return contract
- For `"ui": true` features: after scripted tests, you MUST perform the Exploratory Visual Assessment (Step 8). Navigate the live application yourself via Chrome DevTools MCP, screenshot every page, click every interactive element, and grade against the 4 visual quality criteria. You are an independent QA evaluator, not the developer — be skeptical. A blank canvas with working buttons is a FAIL. "Display-only" elements that render but don't respond to interaction are Major defects.
```

## Step 3: Dispatch SubAgent

**Claude Code:** Use the `Agent` tool:
```
Agent(
  description = "Feature-ST for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode:** Use `@mention` syntax or the platform's native subagent mechanism with the same prompt content.

## Step 4: Parse Result

Read the SubAgent's returned text and locate the `### Verdict:` line:

- **`### Verdict: PASS`**
  1. Extract Next Step Inputs: `st_case_path`, `st_case_count`, `environment_cleaned`
  2. If feature is `"ui": true`: extract Visual Assessment scores. If any score ≤ 2 or Display-Only Defects > 0, treat as FAIL (SubAgent should have already done this, but double-check).
  3. Record in `task-progress.md`: "Feature-ST: PASS ({N} cases, all passed)" — for ui:true, append visual assessment min score
  4. If `environment_cleaned` is false, run cleanup per `env-guide.md` yourself
  5. Proceed to next step (Inline Check + Persist)

- **`### Verdict: FAIL`** or **`### Verdict: BLOCKED`**
  1. Read the Issues table — identify failure details
  2. **Main Agent classifies each issue** into one of two categories:
     - **Human manual testing** (escalate immediately via `AskUserQuestion`): missing `required_configs[]` secrets or credentials the AI cannot provide, UI verification requiring physical device or visual judgment beyond Chrome DevTools MCP capability, external human action required (third-party approval, manual account setup, hardware interaction)
     - **AI self-fix** (everything else): code bugs causing test failures, environment startup issues, port conflicts, dependency errors, external service errors, test execution failures due to implementation issues
  3. For AI self-fix issues: record in `task-progress.md`, fix code or environment, re-dispatch SubAgent. **No retry limit** — AI must keep fixing until resolved.
  4. For human manual testing issues: escalate via `AskUserQuestion` with issue details. Feature stays BLOCKED until human responds.
  5. **No bypass allowed** — every failure must be resolved (by AI or human) before proceeding to Persist.

- **`### Verdict: CLARIFY`**
  1. Read the Specification Gaps table — extract all categorized questions
  2. **Cross-check**: read the Feature Design document's `## Clarification Addendum` section (at `plan_doc_path`). Filter out any gaps that were already resolved there — do NOT re-ask.
  3. For genuinely new gaps: present to user via `AskUserQuestion`:
     ```
     Feature-ST Specification Gap: Feature #{feature_id} ({title})

     While deriving acceptance test cases, {N} specification gap(s) were found
     that prevent writing correct expected results. For each, a suggested interpretation
     is provided — you may accept it, provide a different answer, or say "skip".

     Gap 1 [{category}]: {description}
       Source: {source}
       Impact on test cases: {impact_on_test_cases}
       Suggested: {suggested_interpretation}
       → Your answer (or "accept" / "skip"):

     Gap 2 [{category}]: ...
     ```
  4. Parse user responses and present approval summary:
     ```
     Specification Gap Summary for Feature #{feature_id}:
     1. [{category}] {description} → Resolution: {answer}

     Proceed with these resolutions? (yes / revise #N)
     ```
  5. If approved: construct a **Specification Gap Addendum** and re-dispatch SubAgent with original prompt PLUS:
     ```
     ## Specification Gap Addendum (user-approved resolutions)
     | # | Category | Original Gap | Resolution | Authority |
     |---|----------|-------------|------------|-----------|
     | 1 | {category} | {description} | {resolution} | user-approved / assumed |

     Apply these resolutions as authoritative. Derive test case expected results
     from these resolutions. Do NOT re-flag them as gaps.
     ```
  6. Record in `task-progress.md`: "Feature-ST: CLARIFY ({N} gaps resolved) → re-dispatching"
  7. **Max 1 clarification round** for Feature-ST (design-level ambiguities should have been caught in Feature Design; ST gaps are typically minor). If SubAgent returns `CLARIFY` again after receiving the addendum, set to BLOCKED and escalate: "Persistent specification gaps in Feature-ST. Consider using `long-task-increment` to update source documents."

### Step 4b: Manual Test Review Gate

After parsing the SubAgent's verdict, check for a `### Manual Test Cases` section in the return.

If **no manual test cases**: skip directly to Step 4 outcome handling (PASS/FAIL/BLOCKED above).

If **manual test cases exist**:

1. For each manual test case row, call `AskUserQuestion` with this format:

   ```
   Manual Test Required: {Case ID}

   Test Objective: {Test Objective from table}
   Reason for manual testing: {Manual Reason from table}

   Preconditions:
   {Preconditions from table}

   Test Steps:
   {Test Steps Summary from table}

   Verification Points:
   {Verification Points from table}

   ---
   Please perform this test and respond with:
   Line 1: PASS or FAIL
   Line 2: What you observed
   Line 3: Evidence (screenshot path, log excerpt, or "none")

   Example response:
   PASS
   Login page renders correctly with all expected form fields
   /tmp/screenshots/login-page.png

   To skip this test temporarily, respond: SKIP {reason}
   ```

2. Parse the human response:
   - First line: extract `PASS`, `FAIL`, or `SKIP`
   - If first line cannot be parsed: re-prompt ONCE with:
     `Could not parse your response. Please respond with PASS, FAIL, or SKIP on the first line.`
   - If still unparseable after re-prompt: record as `BLOCKED` with raw response as evidence

3. Record result:
   - `PASS` → update traceability matrix `结果` to `MANUAL-PASS`, record observation
   - `FAIL` → update traceability matrix `结果` to `MANUAL-FAIL`, record observation
   - `SKIP {reason}` → update traceability matrix `结果` to `BLOCKED`, record reason
     (preserves the "no bypass" principle — BLOCKED is tracked, not silently skipped)

4. After all manual cases are collected:
   - Update the test case document (`docs/test-cases/feature-{id}-{slug}.md`):
     - Set each manual case's traceability matrix `结果` to the collected result
     - Update the **Manual Test Case Summary** section counts
   - Re-evaluate the feature-level verdict:
     - If SubAgent verdict was PASS AND all manual cases are `MANUAL-PASS` → final verdict **PASS**
     - If any manual case is `MANUAL-FAIL` → final verdict **FAIL** (same as automated failure)
     - If any manual case is `BLOCKED` → final verdict **BLOCKED**

5. Proceed with the final verdict to Step 4 outcome handling (existing PASS/FAIL/BLOCKED logic above).

## Integration

**Called by:** `long-task-work` (Step 9)
**Requires:** Quality Gates passed (long-task-quality complete)
**Produces:** `docs/test-cases/feature-{id}-{slug}.md` with executed results + structured summary
**Chains to:** Inline Check + Persist (Worker Step 10 + 11)
