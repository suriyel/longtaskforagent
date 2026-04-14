---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker — One Feature Per Cycle

Execute multi-session software projects by implementing one feature per cycle. Each cycle follows a strict pipeline: Orient → Feature Design → TDD → Quality → ST Acceptance → Inline Check → Persist.

**Announce at start:** "I'm using the long-task-work skill. Let me orient myself."

**Core principle:** Each sub-step has its own skill. Follow the orchestration order exactly.

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Orient
- Read `task-progress.md` — **only the `## Current State` section** (use Read with offset/limit from `## Current State` heading to the next `##` heading or log separator `---`)
- Grep `feature-list.json` to extract: `quality_gates`, `tech_stack`, `build_system`, `commit_conventions`, `constraints[]`, `assumptions[]`. Then grep for features with `"status": "failing"` to identify the next candidate. Do NOT read the full file.
- Grep `long-task-guide.md` for the environment activation command, test command, coverage command, and mutation command. Do NOT read the full file.
- Read design doc **§13** (Codebase Conventions & Constraints, `docs/plans/*-design.md`) — note §13.1 mandatory libraries, §13.2 prohibited APIs, §13.4 static analysis tools, §13.5 naming conventions, §13.6 error handling pattern. Store as `{section_13_text}` — this is the single canonical copy for the entire session; do NOT re-read §13 in subsequent steps.
- Run `git log --oneline -10` — recent commit context
- Pick next `"status": "failing"` feature by priority, then by array position in `features[]` (first eligible wins) — **skip features with `"deprecated": true`**
- **Dependency satisfaction check**: After selecting a candidate feature, verify that ALL feature IDs in its `dependencies[]` have `"status": "passing"` in `feature-list.json`. If any dependency is still `"failing"`:
  - Log: "Feature #{id} ({title}) skipped — unsatisfied deps: #{dep1}, #{dep2}"
  - Pick the next eligible `"failing"` feature (by priority + dependency order) whose dependencies are all satisfied
  - If NO features have all dependencies satisfied → warn user via `AskUserQuestion`: "All remaining features have unsatisfied dependencies. Circular or over-constrained dependency graph detected." → let user choose which feature to force-start (override dependency check)
  - Record skipped features and reason in `task-progress.md`
**Document Lookup Protocol (used by Steps 2 and 8):**

When you need the design section or SRS requirement for a feature, do NOT grep for the feature title. Instead:

1. **Design document** (`docs/plans/*-design.md`):
   - Scan the design document's **Section 4 heading area** (use Read tool with offset/limit to scan section 4 headers — look for lines matching `### 4.N Feature:`)
   - Identify which `### 4.N` subsection corresponds to the target feature by matching the feature title or FR-ID
   - Record the line range: `{design_start}` = first line of `### 4.N`, `{design_end}` = line before `### 4.(N+1)` (or end of section 4)
   - Do NOT read the subsection content — SubAgents read it themselves

2. **SRS document** (`docs/plans/*-srs.md`):
   - Read the SRS **Section 4 (Functional Requirements)** heading area to find the `### FR-xxx` subsection matching the target feature
   - Store line range as `{srs_start}` / `{srs_end}` for SubAgent dispatch (Step 2)

**Note:** Do NOT read full §4.N or FR-xxx content during Orient. Only locate line ranges. SubAgents read the actual content themselves in their own fresh context.

### 2. Feature Detailed Design
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-feature-design` and follow it exactly.

The Feature Design skill dispatches a SubAgent to produce the detailed design document. The main Agent does NOT read design/SRS document sections or write the design document — the SubAgent handles everything in its own fresh context and returns a structured summary.

> **For `category: "bugfix"` features**: feature-design is condensed. The SubAgent focuses on: (1) root cause documentation, (2) targeted fix approach, (3) regression test inventory. Full diagrams are skipped unless the bug directly touches those surfaces.

Context to carry forward (paths only — SubAgent reads contents itself):
- Feature object (compact JSON)
- `quality_gates` and `tech_stack` (compact JSON)
- File paths + section line ranges: design doc (§4.N), SRS doc (FR-xxx)
- ATS doc path: `docs/plans/*-ats.md` (if exists) — SubAgent uses ATS mapping to align Test Inventory categories
- Design doc §6.2 path — SubAgent reads Internal API Contracts rows where this feature is Provider or Consumer
- Constraints and assumptions from feature-list.json root
- Output path: `docs/features/YYYY-MM-DD-<feature-name>.md`

Output: `docs/features/YYYY-MM-DD-<feature-name>.md` (written by SubAgent) — feature detailed design document containing interface contracts, algorithm pseudocode, diagrams, test inventory, and TDD task decomposition.

**Contract deviation handling**: If SubAgent returns `BLOCKED` with an issue containing "Contract deviation":
1. Present the deviation details (Contract ID, original vs. proposed schema, reason) to user via `AskUserQuestion`
2. If approved: update §6.2 in the design doc to reflect the new contract, then re-dispatch the feature-design SubAgent
3. Propagate impact: identify Consumer features from the §6.2 Consumer column that may be affected; if any are already `"passing"`, warn user they may need re-verification

**Ambiguity clarification handling**: If Feature Design SubAgent returns `CLARIFY`:
- The feature-design skill's CLARIFY handler manages the full clarification loop internally (AskUserQuestion → collect answers → approval gate → re-dispatch with Clarification Addendum)
- Worker does NOT need separate handling — the feature-design skill resolves CLARIFY and returns either PASS (resolved) or BLOCKED (unresolvable after 2 rounds)
- If clarification reveals SRS deficiency (user says "SRS needs updating"):
  1. Record gap in `task-progress.md`: "SRS gap identified during Feature Design for #{id} — user directed to long-task-increment"
  2. Suggest to user: "Consider placing an `increment-request.json` to update the SRS before continuing with this feature"
  3. If user approves: skip this feature, proceed to next eligible feature (or end session if none)
  4. If user says "proceed with current interpretation": continue with the resolved clarifications
- **Same pattern applies to Feature-ST** (Step 7): the feature-st skill's CLARIFY handler manages its own loop (max 1 round); Worker sees PASS or BLOCKED.

### 3-5. TDD Cycle (Red → Green → Refactor)
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-tdd` and follow it exactly.

Context to carry forward:
- Current feature object from feature-list.json
- `quality_gates` and `tech_stack` from feature-list.json
- **Feature design document path** from Step 2 (`docs/features/YYYY-MM-DD-<feature-name>.md`) — TDD reads targeted sections: §7 Test Inventory, §3 Interface Contract, Existing Code Reuse, §5 Algorithm, Clarification Addendum
- **Test commands**: from `long-task-guide.md` — use these directly (no wrapper scripts)

### 6. Quality Gates — SubAgent Dispatch

Delegate quality gate execution to a SubAgent with fresh context. The main Agent only dispatches and parses the structured result — it never reads coverage reports, mutation output, or test runner output directly.

**Construct SubAgent Prompt:**

```
You are a Quality Gates execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-quality/references/quality-execution.md
2. Read long-task-guide.md in the project root for test/coverage/mutation commands and environment activation
3. Execute both gates in order (Gate 1: Coverage → Gate 2: Mutation + Final Test Run)
   - **Note**: Static analysis tools (Design §13.4) are enforced during TDD Refactor, not here. If Design doc §13.7 documents code generation directories, exclude them from coverage measurement in Gate 1.
4. If a gate fails, fix and retry per the rules (max 3 attempts per gate)
5. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates thresholds: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}
- Feature test files: {feature_test_files}
- Active feature count: {active_feature_count}

## Key Constraint
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- If a tool/environment error cannot be resolved after 1 retry, set Verdict to BLOCKED
```

Replace `{skills_root}` with the path to the skills directory.

**Dispatch:** Use the `Agent` tool with description "Quality Gates for feature #{feature_id}".

**Parse Result:**
- **`PASS`** → Record metrics in `task-progress.md`, proceed to Feature-ST
- **`FAIL`** → If SubAgent already retried, escalate to user via `AskUserQuestion`
- **`BLOCKED`** → Escalate blocker details to user via `AskUserQuestion`

### 7. ST Acceptance Test Cases
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-feature-st` and follow it exactly.

Execute black-box acceptance testing for the feature **after** TDD and quality gates pass. The skill dispatches a SubAgent that reads SRS/Design/ATS documents in its own fresh context, generates ISO/IEC/IEEE 29119 compliant test case documents, executes test cases, and manages service lifecycle. The main Agent does NOT read document sections, test case content, or execution output — only the structured summary.

Context to carry forward (paths only — SubAgent reads file contents itself):
- Feature ID and feature object (compact JSON)
- `quality_gates` and `tech_stack` (compact JSON)
- File paths: design doc, SRS doc, ATS doc (if exists), plan doc (from Step 2), env-guide.md
- Working directory path
- `st_case_template_path` and `st_case_example_path` from feature-list.json root (if set)

Output: `docs/test-cases/feature-{id}-{slug}.md` (written by SubAgent)

**Hard Gate:**
- **No bypass allowed** — cannot skip ST for any reason
- Main Agent classifies failures per feature-st SKILL.md: AI self-fix issues (code bugs, env issues) are resolved autonomously with no retry limit; only issues requiring human manual testing (missing credentials, physical device, visual judgment) escalate via `AskUserQuestion`

### 8. Inline Compliance Check (no SubAgent)

Run these mechanical checks directly — no SubAgent dispatch needed.

**a) Dependency versions (D3):**
If feature design §3 or §5 specifies third-party library versions, spot-check that `requirements.txt` / `package.json` / `pom.xml` matches. Flag mismatches.

**b) Codebase convention compliance (blocking for §13.1/§13.2):**

Check new/modified files (`git diff --name-only` of feature changes) against `{section_13_text}` (from Orient):

- §13.1: For each non-empty "Replaces" entry, grep new/modified source files for the replaced import pattern. Match → violation → fix before proceeding.
- §13.2: For each non-empty "Prohibited" entry, grep new/modified source files. Match → violation → fix.

§13.5/§13.6 advisory checks: already enforced by TDD Refactor static analysis gate — log "covered by TDD Refactor" without re-running.

**c) Existing code reuse verification (blocking):**
Read feature design "Existing Code Reuse" section. For each REUSE item: grep implementation files for the expected import. If the REUSE item is NOT imported but equivalent functionality is reimplemented → violation → replace with REUSE import.

On blocking violation: log file:line + what was used vs. what §13 requires; fix the violation; re-run tests to confirm no regression; re-check.

If all checks pass → proceed to Persist.
If any check fails → fix inline, re-verify. No SubAgent dispatch.

Record in `task-progress.md`:
```
- Inline Check: PASS (D3: OK, §13: N violations fixed / M checked, Reuse: R items verified)
```

### 9. Persist
- Git commit (include implementation, tests, **test case document**)
  > **Commit format**: If Design §13.8 documents commit conventions, follow that format. Otherwise use defaults below.
  > **For `category: "bugfix"` features**: use commit prefix `"fix:"` instead of `"feat:"`.
  > Format: `fix: <feature title without the "Fix: " prefix> (#<fixed_feature_id>)`
  > **Commit convention compliance**: Read `commit_conventions` from `feature-list.json` (if present) or Design §13.8 to determine the required format (profile, prefix whitelist, subject length limits, branch naming). Format your commit message to match BEFORE running `git commit`. If `strip_trailers` is true, do NOT add Co-Authored-By, Signed-off-by, or any other trailer lines.
- Capture the commit SHA immediately after the commit:
  ```bash
  git rev-parse --short HEAD
  ```
  Store this value as `{commit_sha}` — it is used in the next two steps.
- Update `RELEASE_NOTES.md` (Keep a Changelog format)
  > **For `category: "bugfix"` features**: add entry under `### Fixed` (not `### Added`):
  > `- [<bug_severity>] <title without "Fix: "> (fixes #<fixed_feature_id>) — <root_cause one-line>`
- Update `task-progress.md`:
  - Update `## Current State` header: progress count (X/Y passing), last completed feature (#id title, date), next feature (#id title)
  - Append session entry below the log separator; session entry format:
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    - Quality Gates: N% line, N% branch, N% mutation
    - Feature-ST: N cases, all PASS
    - Inline Check: PASS
    - Git: {commit_sha} feat: title
    #### Risks                        ← include only if any risks were reported
    - ⚠ [Mutant] file:line — reason
    - ⚠ [Coverage] metric N% — thin margin / uncovered boundary
    - ⚠ [Dependency] lib==ver — known patch / breaking change pending
    ```
  - **`{commit_sha}` must be the actual captured value** — never a placeholder. This ensures `task-progress.md` and `feature-list.json` carry the same verified SHA.
  - **Collecting risks**: after Step 6 (Quality) and Step 7 (Feature-ST) complete, extract every row from their `### Risks` tables; merge into a single list; append as `#### Risks` bullets only if the list is non-empty
- Mark feature `"status": "passing"` in `feature-list.json`
- Set `"st_case_path"`, `"st_case_count"`, and `"git_sha": "{commit_sha}"` on the feature object in `feature-list.json`
- Validate:
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- Git commit (progress files):
  ```bash
  git add feature-list.json task-progress.md RELEASE_NOTES.md
  git commit -m "chore: update progress — feature #{id} passing"
  ```

### 10. End Session
- Output a concise completion summary:
  > **Feature #\<id\> (\<title\>) — DONE**
  >
  > Next: Feature #\<next_id\> (\<next_title\>)
- If **no failing non-deprecated features remain**:
  > All active features passing — next session begins System Testing.
- End session — **never loop back to Step 1**

The auto-loop script (`scripts/auto_loop.py`) handles multi-feature automation externally — each invocation is a fresh context.

## Critical Rules

- **One feature per session** — end session after completing one feature; multi-feature automation is handled by the external auto-loop script (`scripts/auto_loop.py`)
- **Strict step order** — no skipping, no reordering
- **Sub-skills are non-negotiable** — ST Test Cases, TDD, Quality MUST be invoked via Skill tool
- **Never mark "passing" without fresh evidence** — run tests, read output, then mark
- **Systematic debugging only** — on error, read `references/systematic-debugging.md`; trace root cause, never guess-and-fix
- **Update RELEASE_NOTES.md after every git commit**
- **Always commit + update progress before ending session** — bridges context gap
- **Never leave broken code** — revert incomplete work

## Red Flags

| Rationalization | Correct Action |
|---|---|
| "This feature is trivial, skip test cases" | Invoke long-task-feature-st. Every feature. |
| "This feature is trivial, skip TDD" | Invoke long-task-tdd. Every feature. |
| "Tests pass, mark it done" | Run Quality Gates SubAgent first. |
| "Coverage looks close enough" | Thresholds are hard gates. Run the tool. |
| "Let me just try this quick fix" | Systematic debugging first. |
| "I'll generate examples during Worker" | Examples are post-ST (ST Step 13). |
| "I'll update release notes at the end" | Update after every commit. |
| "Mutation score is probably OK" | Run mutation tests and read the report. |
| "ST test case failed but the code is fine" | No bypass. AI must fix code and re-dispatch — no retry limit. If test spec is wrong, use `long-task-increment` to modify. Only escalate if issue genuinely requires human manual testing. |
| "Environment is down, skip ST cases" | BLOCKED, not skipped. Fix environment or ask user. |
| "This deprecated feature still needs work" | Skip it. Deprecated features are excluded. |
| "Backend isn't ready but I'll mock it for now" | Dependency check exists for a reason. Develop backend features first. |
| "I'll skip the dependency check this once" | Never skip. Reorder features so deps are satisfied. |
| "The SRS is ambiguous but I'll just assume..." | SubAgent should flag CLARIFY. Assumptions on critical paths (Interface Contract, Test Inventory expected results, cross-feature contracts) cause late-stage rework. Only low-impact ambiguities may be assumed. |

## On Error

Follow the systematic debugging process — **never guess-and-fix**:
1. Collect evidence (error message, stack trace, git diff)
2. Reproduce the issue
3. Trace root cause (read `references/systematic-debugging.md` for detailed process)
4. Write failing test for the bug
5. Fix with single targeted change
6. Give up after 3 attempts → escalate to user

## Integration

**Called by:** using-long-task (when feature-list.json exists) or long-task-init (Step 16)
**Invokes (in strict order):**
1. `long-task:long-task-tdd` (Steps 3-5) — TDD Red-Green-Refactor
2. Quality Gates SubAgent (Step 6) — Coverage + Mutation (inline dispatch, reads `long-task-quality/references/quality-execution.md`)
3. `long-task:long-task-feature-st` (Step 7) — Black-Box Feature Acceptance Testing (ISO/IEC/IEEE 29119, self-managed lifecycle)
**Reads/Writes:** feature-list.json, task-progress.md (including `## Current State`), RELEASE_NOTES.md
**Read on-demand (via Read tool, NOT Skill tool):** `references/systematic-debugging.md`
