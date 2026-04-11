---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker — One Feature Per Cycle

Execute multi-session software projects by implementing one feature per cycle. Each cycle follows a strict pipeline: Orient → Gate → Plan → TDD → Quality → ST Acceptance → Inline Check → Persist.

**Announce at start:** "I'm using the long-task-work skill. Let me orient myself."

**Core principle:** Each sub-step has its own skill. Follow the orchestration order exactly.

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Orient
- Load config values if applicable — activate the project environment per `long-task-guide.md`; if the project uses a file-based config (e.g., `.env`), ensure it is sourced so required env vars are set before running checks
- Read `task-progress.md` `## Current State` section — progress stats, last completed feature, next feature up
- Read `feature-list.json` — note `constraints[]`, `assumptions[]`, feature statuses
- Read `long-task-guide.md` — project-specific workflow guidance
- Read `env-guide.md` (if it exists) — note service names, ports, and health check URLs; required if the target feature has service dependencies
- **Determine service dependencies**: A feature has service dependencies if ANY of the following are true:
  1. Its `dependencies[]` include a feature whose title references database setup, schema migration, or service initialization
  2. The design section (`{design_section}`) specifies external service interactions (DB queries, HTTP calls to own services, message queue operations)

  Record determination (yes/no + which services) in `task-progress.md` under the current feature heading. This determination drives Bootstrap Step 2.
- Read design doc **Section 1** (`docs/plans/*-design.md`) — project overview and architecture snapshot for global context
- Read design doc **§13** (Codebase Conventions & Constraints, if exists) — note 2/3方件 library constraints (§13.1), prohibited APIs (§13.2), static analysis tools (§13.4), naming conventions (§13.5), error handling pattern (§13.6). These are binding for all new code.
- Read `build_system` and `commit_conventions` from `feature-list.json` — use `build_command` for compilation, follow `commit_conventions` for git formatting (profile, prefix whitelist, subject length, branch naming, strip_trailers)
- Run `git log --oneline -10` — recent commit context
- Pick next `"status": "failing"` feature by priority, then by array position in `features[]` (first eligible wins) — **skip features with `"deprecated": true`**
- **Dependency satisfaction check**: After selecting a candidate feature, verify that ALL feature IDs in its `dependencies[]` have `"status": "passing"` in `feature-list.json`. If any dependency is still `"failing"`:
  - Log: "Feature #{id} ({title}) skipped — unsatisfied deps: #{dep1}, #{dep2}"
  - Pick the next eligible `"failing"` feature (by priority + dependency order) whose dependencies are all satisfied
  - If NO features have all dependencies satisfied → warn user via `AskUserQuestion`: "All remaining features have unsatisfied dependencies. Circular or over-constrained dependency graph detected." → let user choose which feature to force-start (override dependency check)
  - Record skipped features and reason in `task-progress.md`
**Document Lookup Protocol (used by Steps 4, 9, and 10):**

When you need the design section or SRS requirement for a feature, do NOT grep for the feature title. Instead:

1. **Design document** (`docs/plans/*-design.md`):
   - Read the design document's **Section 4 heading area** (use Read tool with offset/limit to scan section 4 headers — look for lines matching `### 4.N Feature:`)
   - Identify which `### 4.N` subsection corresponds to the target feature by matching the feature title or FR-ID
   - Read the **entire subsection** from `### 4.N` through the line before `### 4.(N+1)` (or end of section 4) — this includes Overview, Class Diagram, Sequence Diagram, Flow Diagram, and Design Decisions
   - Store this full text as `{design_section}` for use in Plan (Step 4) and ST Acceptance (Step 8)

2. **SRS document** (`docs/plans/*-srs.md`):
   - Read the SRS **Section 4 (Functional Requirements)** heading area to find the `### FR-xxx` subsection matching the target feature
   - Read the **entire FR-xxx subsection** including EARS statement, priority, acceptance criteria, and Given/When/Then scenarios
   - Store this as `{srs_section}` for use in Plan

**Why this matters:** Grep returns isolated matching lines without surrounding context. Design sections contain class diagrams, sequence diagrams, flow diagrams, and design rationale that span dozens of lines — all of which are needed for correct implementation and inline compliance checking.

### 2. Bootstrap
- **Development environment readiness**: Check if environment is set up
  - If `init.sh` / `init.ps1` exists and environment is not ready: run it once
  - Record decision in `task-progress.md` if script was executed
- **Confirm test commands available**: Activate environment per `long-task-guide.md` and verify the test/coverage/mutation commands are correct for the tech stack; use these directly throughout the cycle (no wrapper scripts)
- **Service readiness** (conditional — based on Orient service dependency determination):
  - **No service dependencies**: Skip service startup. Feature-ST (Step 9) manages services for acceptance testing.
  - **Has service dependencies**: Integration tests need running infrastructure. Ensure availability:
    1. Read `env-guide.md` → locate "Verify Services Running" health checks
    2. Run health checks. If all pass → record PID/port in `task-progress.md`; proceed
    3. If health checks fail → start via `env-guide.md` "Start All Services" with output capture:
       ```bash
       [start command] > /tmp/svc-<slug>-start.log 2>&1 &
       sleep 3
       head -30 /tmp/svc-<slug>-start.log
       ```
    4. Re-run health checks — block until pass
    5. If start fails → diagnose per `env-guide.md`; escalate via `AskUserQuestion` if unresolvable
    6. Record running services, PIDs, ports in `task-progress.md`
  - Feature-ST (Step 9) handles restart/cleanup. Services started here remain running through TDD and Quality Gates.

### 3. Feature Detailed Design
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
- **Same pattern applies to Feature-ST** (Step 8): the feature-st skill's CLARIFY handler manages its own loop (max 1 round); Worker sees PASS or BLOCKED.

### 4-6. TDD Cycle (Red → Green → Refactor)
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-tdd` and follow it exactly.

Context to carry forward:
- Current feature object from feature-list.json
- `quality_gates` and `tech_stack` from feature-list.json
- **Full feature design document** from Step 4 (`docs/features/YYYY-MM-DD-<feature-name>.md`) — TDD MUST read the complete document cover to cover, not individual sections. Includes: Existing Code Reuse (reusable items + §13.1 library patterns from dependencies), Interface Contract (§3 with §13.1 annotations), Algorithm (§5 with §13 library mapping), Test Inventory (§7, primary TDD spec input).
- Full `{srs_section}` from Document Lookup Protocol — TDD Red uses this alongside Feature Design Test Inventory; `verification_steps` are optional supplementary input
- Full `{design_section}` from Document Lookup Protocol — architectural constraints and interface contracts
- **Design doc §13** (Codebase Conventions & Constraints) — passed as `CODEBASE_CONSTRAINTS` to implementer SubAgent; TDD Red uses §13.5 for test naming
- **Test commands**: from `long-task-guide.md` — use these directly (no wrapper scripts)

### 7. Quality Gates — SubAgent Dispatch

Delegate quality gate execution to a SubAgent with fresh context. The main Agent only dispatches and parses the structured result — it never reads coverage reports, mutation output, or test runner output directly.

**Construct SubAgent Prompt:**

```
You are a Quality Gates execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-quality/references/quality-execution.md
2. Read long-task-guide.md in the project root for test/coverage/mutation commands and environment activation
3. Execute all 3 gates in order (Gate 1 → 2 → 3)
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

### 8. ST Acceptance Test Cases
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-feature-st` and follow it exactly.

Execute black-box acceptance testing for the feature **after** TDD and quality gates pass. The skill dispatches a SubAgent that reads SRS/Design/ATS documents in its own fresh context, generates ISO/IEC/IEEE 29119 compliant test case documents, executes test cases, and manages service lifecycle. The main Agent does NOT read document sections, test case content, or execution output — only the structured summary.

Context to carry forward (paths only — SubAgent reads file contents itself):
- Feature ID and feature object (compact JSON)
- `quality_gates` and `tech_stack` (compact JSON)
- File paths: design doc, SRS doc, ATS doc (if exists), plan doc (from Step 4), env-guide.md
- Working directory path
- `st_case_template_path` and `st_case_example_path` from feature-list.json root (if set)

Output: `docs/test-cases/feature-{id}-{slug}.md` (written by SubAgent)

**Hard Gate:**
- **No bypass allowed** — cannot skip ST for any reason
- Main Agent classifies failures per feature-st SKILL.md: AI self-fix issues (code bugs, env issues) are resolved autonomously with no retry limit; only issues requiring human manual testing (missing credentials, physical device, visual judgment) escalate via `AskUserQuestion`

### 9. Inline Compliance Check (no SubAgent)

Run these mechanical checks directly — no SubAgent dispatch needed.
Read the feature design document (`docs/features/YYYY-MM-DD-<feature-name>.md`)
produced in Step 4.

**a) Interface contract verification (P2 equivalent):**
Read §3 Interface Contract table from the feature design doc. For each PUBLIC
method listed, grep the implementation files to confirm the method exists with
matching signature (name, parameters, return type). Flag missing or mismatched
methods.

**b) Test Inventory ↔ test file cross-check (T2 equivalent):**
Read §7 Test Inventory from the feature design doc. For each test row, confirm
the corresponding test function exists in the test file:
```bash
grep -q "{test_function_name}" {test_file}
```
If any test function is not found, search for similar names and fix the ST
document traceability matrix reference.

**c) Design dependency versions (D3 equivalent):**
If §3 or §5 specifies third-party library versions, spot-check that
`requirements.txt` / `package.json` / `pom.xml` matches. Flag mismatches.

**d) ST document integrity:**
Confirm `validate_st_cases.py` already passed in Feature-ST (Step 8).
No re-validation needed — Feature-ST Step 5b + Step 6 already cover T1.

**f) Codebase convention compliance check (blocking for §13.1/§13.2, advisory for §13.5/§13.6):**

Check ALL new/modified files (`git diff --name-only` of feature changes) against Design doc §13:

**Blocking checks:**
- §13.1: For each non-empty §13.1 "Replaces" entry, grep new/modified source files for the replaced import pattern. Match → violation → fix before proceeding.
  ```bash
  grep -rn "import.*{replaced}\|require.*{replaced}\|from {replaced}" {files}
  ```
- §13.2: For each non-empty §13.2 "Prohibited" entry, grep new/modified source files. Match → violation → fix.

**Advisory checks** (log to `task-progress.md`):
- §13.5: Spot-check variable/function/class naming patterns
- §13.6: Spot-check error handling approach

**Existing code reuse verification** (blocking):
- Read feature design "Existing Code Reuse" section. For each REUSE item: grep implementation files for the expected import. If the REUSE item is NOT imported but equivalent functionality is reimplemented → violation → replace with REUSE import.

On blocking violation: log file:line + what was used vs. what §13 requires; fix the violation; re-run tests to confirm no regression; re-check.

If all checks pass → proceed to Persist.
If any check fails → fix inline, re-verify. No SubAgent dispatch.

Record in `task-progress.md`:
```
- Inline Check: PASS (P2: N/N methods verified, T2: N/N tests found, D3: OK, §13: N violations fixed / M checked, Reuse: R items verified)
```

### 10. Persist
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
  - **Collecting risks**: after Step 7 (Quality) and Step 8 (Feature-ST) complete, extract every row from their `### Risks` tables; merge into a single list; append as `#### Risks` bullets only if the list is non-empty
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

### 11. End Session
- Stop any services you started directly during this cycle (services started during ST acceptance testing in Step 9 are stopped by `long-task-feature-st`)
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
| "Port is busy, let me kill manually" | Use env-guide.md "Stop All Services" (port fallback) to kill it, then restart via env-guide.md Start — update env-guide.md if the command needed correction. |
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
1. `long-task:long-task-tdd` (Steps 4-6) — TDD Red-Green-Refactor
2. Quality Gates SubAgent (Step 7) — Coverage + Mutation (inline dispatch, reads `long-task-quality/references/quality-execution.md`)
3. `long-task:long-task-feature-st` (Step 8) — Black-Box Feature Acceptance Testing (ISO/IEC/IEEE 29119, self-managed lifecycle)
**Reads/Writes:** feature-list.json, task-progress.md (including `## Current State`), RELEASE_NOTES.md
**Read on-demand (via Read tool, NOT Skill tool):** `references/systematic-debugging.md`
