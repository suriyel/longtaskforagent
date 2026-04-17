---
name: long-task-quality
description: "Use after TDD cycle in a long-task project - enforces coverage gate and fresh verification evidence before marking features as passing"
---

# Quality Gates — SubAgent Dispatch

Delegate quality gate execution to a SubAgent with fresh context. The main Agent only dispatches and parses the structured result — it never reads coverage reports or test runner output directly.

**Announce at start:** "I'm using the long-task-quality skill to run quality gates via SubAgent."

## Step 1: Construct SubAgent Prompt

Build the prompt from current session state. Do NOT read any source code, test output, or coverage reports yourself.

```
You are a Quality Gates execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-quality/references/quality-execution.md
2. Read `env-guide.md` §3 (Build & Execution Commands) for test/coverage/static-analysis commands. Read `env-guide.md` §2 for environment activation. Both are the **single source of truth** — do NOT derive commands from long-task-guide.md (it only navigates; env-guide.md §3 owns commands).
3. Execute all 3 gates in order (Gate 0 → 1 → 2)
   - **Note**: Static analysis tools (Design §13.4) are enforced during TDD Refactor, not here. If Design doc §13.7 documents code generation directories, exclude them from coverage measurement in Gate 1.
4. If a gate fails, fix and retry per the rules (max 3 attempts per gate)
5. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates thresholds: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}
- Feature test files: {feature_test_files}  (test files written/modified during TDD for this feature)

## Key Constraint
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- If a tool/environment error cannot be resolved after 1 retry, set Verdict to BLOCKED
```

Replace `{skills_root}` with the path to the skills directory (e.g., `skills` in the project or the installed plugin path).

## Step 2: Dispatch SubAgent

**Claude Code:** Use the `Agent` tool:
```
Agent(
  description = "Quality Gates for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode:** Use `@mention` syntax or the platform's native subagent mechanism with the same prompt content.

## Step 3: Parse Result

Read the SubAgent's returned text and locate the `**status**:` line (unified contract field). The legacy `### Verdict:` line may coexist for backward compatibility but the authoritative field is `**status**`.

- **`**status**: pass`**
  1. Extract `**next_step_input**` (coverage_line, coverage_branch, all_tests_pass, test_count)
  2. Optionally read Metrics table for task-progress.md detail
  3. Record in `task-progress.md`: "Quality Gates: PASS (line {X}%, branch {Y}%)"
  4. Proceed to next step (Feature-ST)

- **`**status**: fail`**
  1. Read `**evidence**` and Issues table — identify which gate failed and why
  2. If the SubAgent already attempted fixes (per the 3-retry rule), escalate to user via `AskUserQuestion` with the failure details
  3. If fixable by re-dispatching (e.g., environment issue resolved), construct a new prompt and dispatch again (max 3 total dispatches)

- **`**status**: blocked`**
  1. Read `**blockers**` array — identify the blocker (tool not installed, environment error, etc.)
  2. Escalate to user via `AskUserQuestion` with the blocker details and what was attempted

## Integration

**Called by:** long-task-work (Step 8)
**Requires:** TDD cycle completed (long-task-tdd passed — tests exist and pass)
**Produces:** Structured summary (coverage %, per-gate pass/fail)
**Chains to:** long-task-feature-st (via Work Step 9)
