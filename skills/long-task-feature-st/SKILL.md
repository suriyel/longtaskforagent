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
2. Follow the checklist exactly (Steps 1-7): Load Context → Load Template → Derive Test Cases → Write Document → Validate → Execute → Cleanup
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
- ALL test cases must be executed one by one — no skipping
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
  2. Record in `task-progress.md`: "Feature-ST: PASS ({N} cases, all passed)"
  3. If `environment_cleaned` is false, run cleanup per `env-guide.md` yourself
  4. Proceed to next step (Inline Check + Persist)

- **`### Verdict: FAIL`**
  1. Read the Issues table — identify which test cases failed (case IDs, actual vs expected)
  2. Record failure in `task-progress.md`. Fix code and re-dispatch SubAgent for re-execution.
  3. If fix fails after 2 attempts, set Verdict to BLOCKED
  4. **No bypass allowed** — a FAIL here blocks the feature from proceeding to Persist

- **`### Verdict: BLOCKED`**
  1. Read the Issues table — identify the blocker (service won't start, environment unavailable, etc.)
  2. Record blocker in `task-progress.md`. If blocker is resolvable, attempt fix and re-dispatch SubAgent.

## Integration

**Called by:** `long-task-work` (Step 9)
**Requires:** Quality Gates passed (long-task-quality complete)
**Produces:** `docs/test-cases/feature-{id}-{slug}.md` with executed results + structured summary
**Chains to:** Inline Check + Persist (Worker Step 10 + 11)
