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
- Read `feature-list.json` — note `constraints[]`, `assumptions[]`, `required_configs[]`, feature statuses
- Read `long-task-guide.md` — project-specific workflow guidance
- Read `env-guide.md` (if it exists) — note service names, ports, and health check URLs; required if the target feature has service dependencies
- **Determine service dependencies**: A feature has service dependencies if ANY of the following are true:
  1. Its `required_configs[]` entries include connection-string keys (key contains `URL`, `URI`, `DSN`, `CONNECTION`, `HOST`, or `PORT` — e.g., `DATABASE_URL`, `REDIS_HOST`)
  2. Its `dependencies[]` include a feature whose title references database setup, schema migration, or service initialization
  3. The design section (`{design_section}`) specifies external service interactions (DB queries, HTTP calls to own services, message queue operations)

  Record determination (yes/no + which services) in `task-progress.md` under the current feature heading. This determination drives Bootstrap Step 2 and Config Gate Step 3.
- Read design doc **Section 1** (`docs/plans/*-design.md`) — project overview and architecture snapshot for global context
- Run `git log --oneline -10` — recent commit context
- Pick next `"status": "failing"` feature by priority, then by array position in `features[]` (first eligible wins) — **skip features with `"deprecated": true`**
- **Dependency satisfaction check**: After selecting a candidate feature, verify that ALL feature IDs in its `dependencies[]` have `"status": "passing"` in `feature-list.json`. If any dependency is still `"failing"`:
  - Log: "Feature #{id} ({title}) skipped — unsatisfied deps: #{dep1}, #{dep2}"
  - Pick the next eligible `"failing"` feature (by priority + dependency order) whose dependencies are all satisfied
  - If NO features have all dependencies satisfied → warn user via `AskUserQuestion`: "All remaining features have unsatisfied dependencies. Circular or over-constrained dependency graph detected." → let user choose which feature to force-start (override dependency check)
  - Record skipped features and reason in `task-progress.md`
- If target feature has `"ui": true` and UCD document exists (`docs/plans/*-ucd.md`), read the UCD style guide — reference style tokens, component prompts, and page prompts to ensure frontend implementation matches the approved visual style

**Document Lookup Protocol (used by Steps 5, 10, and 11):**

When you need the design section or SRS requirement for a feature, do NOT grep for the feature title. Instead:

1. **Design document** (`docs/plans/*-design.md`):
   - Read the design document's **Section 4 heading area** (use Read tool with offset/limit to scan section 4 headers — look for lines matching `### 4.N Feature:`)
   - Identify which `### 4.N` subsection corresponds to the target feature by matching the feature title or FR-ID
   - Read the **entire subsection** from `### 4.N` through the line before `### 4.(N+1)` (or end of section 4) — this includes Overview, Class Diagram, Sequence Diagram, Flow Diagram, and Design Decisions
   - Store this full text as `{design_section}` for use in Plan (Step 5) and ST Acceptance (Step 9)

2. **SRS document** (`docs/plans/*-srs.md`):
   - Read the SRS **Section 4 (Functional Requirements)** heading area to find the `### FR-xxx` subsection matching the target feature
   - Read the **entire FR-xxx subsection** including EARS statement, priority, acceptance criteria, and Given/When/Then scenarios
   - Store this as `{srs_section}` for use in Plan

3. **UCD document** (`docs/plans/*-ucd.md`, only for `"ui": true` features):
   - Read the UCD's table of contents or section headers
   - Find sections referencing the target feature's UI components or pages
   - Read the **full relevant sections** including style tokens, component prompts, and page prompts

**Why this matters:** Grep returns isolated matching lines without surrounding context. Design sections contain class diagrams, sequence diagrams, flow diagrams, and design rationale that span dozens of lines — all of which are needed for correct implementation and inline compliance checking.

### 2. Bootstrap
- **Development environment readiness**: Check if environment is set up
  - If `init.sh` / `init.ps1` exists and environment is not ready: run it once
  - Record decision in `task-progress.md` if script was executed
- **Confirm test commands available**: Activate environment per `long-task-guide.md` and verify the test/coverage/mutation commands are correct for the tech stack; use these directly throughout the cycle (no wrapper scripts)
- **Service readiness** (conditional — based on Orient service dependency determination):
  - **No service dependencies**: Skip service startup. Feature-ST (Step 10) manages services for acceptance testing.
  - **Has service dependencies**: Real tests (TDD Rule 5a) need running infrastructure. Ensure availability:
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
  - Feature-ST (Step 10) handles restart/cleanup. Services started here remain running through TDD and Quality Gates.
- Smoke-test previously passing features (activate environment per `long-task-guide.md` → run test command directly)

### 3. Config Gate
```bash
python scripts/check_configs.py feature-list.json --feature <id>
```
`<id>` = the feature ID selected in Step 1. The generated `check_configs.py` loads config values using the project's native format automatically.

**If configs are missing — prompt for text input and save to the project config:**

1. For each missing `env`-type config, use `AskUserQuestion` to ask the user to **type the value** — do NOT provide predefined option buttons. Frame the question with the config's `name`, `description`, and `check_hint` so the user knows what to provide.
   - Example: "Please enter the value for `OPENAI_API_KEY` (OpenAI API key for LLM integration). Hint: Get it from https://platform.openai.com/api-keys"
2. For each missing `file`-type config, ask the user to provide the file path or create the file manually.
3. After receiving all values, **save env-type configs following the project's config format** — refer to the `Config Management` section in `long-task-guide.md` for the exact method (e.g., append to `.env`, set in `application.properties`, export as system env var).
4. Re-run the check to confirm:
   ```bash
   python scripts/check_configs.py feature-list.json --feature <id>
   ```
5. Ensure any secrets config file is listed in `.gitignore` if not already present.
6. **Block until all configs pass.**
7. **Connectivity verification** (features with service dependencies only):
   After config keys pass existence checks, verify connection-string configs actually connect:
   - For each `env`-type config whose key matches a connection-string pattern (`DATABASE_URL`, `REDIS_URL`, etc.): run the corresponding health check from `env-guide.md` "Verify Services Running"
   - If health check fails: config value exists but service is unreachable — start service per Bootstrap service readiness protocol above
   - **Block until connectivity confirmed** — a config pointing to a dead service is functionally missing

**Config Gate is non-negotiable for features with external dependencies.** If configs are missing:
- MUST use `AskUserQuestion` to request values from the user
- MUST NOT proceed to TDD without all configs resolved
- MUST NOT claim "pure-function exemption" for features that have `required_configs[]` entries with connection-string keys (URL, HOST, PORT, DSN, URI, CONNECTION, ENDPOINT)
- Quality Gates (Gate 0) will mechanically enforce this via `check_real_tests.py --require-for-deps`

### 4. Feature Detailed Design
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-feature-design` and follow it exactly.

The Feature Design skill dispatches a SubAgent to produce the detailed design document. The main Agent does NOT read design/SRS/UCD document sections or write the design document — the SubAgent handles everything in its own fresh context and returns a structured summary.

> **For `category: "bugfix"` features**: feature-design is condensed. The SubAgent focuses on: (1) root cause documentation, (2) targeted fix approach, (3) regression test inventory. Full diagrams are skipped unless the bug directly touches those surfaces.

Context to carry forward (paths only — SubAgent reads contents itself):
- Feature object (compact JSON)
- `quality_gates` and `tech_stack` (compact JSON)
- File paths + section line ranges: design doc (§4.N), SRS doc (FR-xxx), UCD doc (if ui:true)
- ATS doc path: `docs/plans/*-ats.md` (if exists) — SubAgent uses ATS mapping to align Test Inventory categories
- Constraints and assumptions from feature-list.json root
- Output path: `docs/features/YYYY-MM-DD-<feature-name>.md`

Output: `docs/features/YYYY-MM-DD-<feature-name>.md` (written by SubAgent) — feature detailed design document containing interface contracts, algorithm pseudocode, diagrams, test inventory, and TDD task decomposition.

### 5-7. TDD Cycle (Red → Green → Refactor)
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-tdd` and follow it exactly.

Context to carry forward:
- Current feature object from feature-list.json
- `quality_gates` and `tech_stack` from feature-list.json
- Feature detailed design document from Step 4 (includes Test Inventory table, Interface Contract, Algorithm pseudocode) — **Test Inventory (section 7) is the primary TDD spec input**
- Full `{srs_section}` from Document Lookup Protocol — TDD Red uses this as specification input alongside Feature Design Test Inventory; `verification_steps` are optional supplementary input
- Full `{design_section}` from Document Lookup Protocol — architectural constraints and interface contracts
- **Test commands**: from `long-task-guide.md` — use these directly (no wrapper scripts)

### 8. Quality Gates
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-quality` and follow it exactly.

The Quality skill dispatches a SubAgent to execute all 4 gates (Real Test → Coverage → Mutation → Verify). The main Agent does NOT read coverage reports, mutation output, or test runner output — the SubAgent handles everything in its own fresh context and returns a structured summary.

Context to carry forward (minimal — SubAgent reads files itself):
- Feature ID from feature-list.json
- `quality_gates` thresholds (compact JSON)
- `tech_stack` (compact JSON)
- Working directory path
- Feature test file paths (test files written/modified during TDD for this feature — for mutation_feature scoping)
- Active feature count (total non-deprecated features in feature-list.json — for mutation_full_threshold decision)

### 9. ST Acceptance Test Cases
**REQUIRED SUB-SKILL:** Invoke `long-task:long-task-feature-st` and follow it exactly.

Execute black-box acceptance testing for the feature **after** TDD and quality gates pass. The skill dispatches a SubAgent that reads SRS/Design/UCD/ATS documents in its own fresh context, generates ISO/IEC/IEEE 29119 compliant test case documents, executes test cases, and manages service lifecycle. The main Agent does NOT read document sections, test case content, or execution output — only the structured summary.

Context to carry forward (paths only — SubAgent reads file contents itself):
- Feature ID and feature object (compact JSON)
- `quality_gates` and `tech_stack` (compact JSON)
- File paths: design doc, SRS doc, UCD doc (if ui:true), ATS doc (if exists), plan doc (from Step 4), env-guide.md
- Working directory path
- `st_case_template_path` and `st_case_example_path` from feature-list.json root (if set)

Output: `docs/test-cases/feature-{id}-{slug}.md` (written by SubAgent)

**Hard Gate:**
- Any execution failure (environment or test case) must be reported to user via `AskUserQuestion`
- **No bypass allowed** — cannot skip ST for any reason

### 10. Inline Compliance Check (no SubAgent)

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

**d) UCD spot check (U1 equivalent, ui:true only):**
Grep CSS/style files for hardcoded color hex values not in UCD palette tokens.

**e) ST document integrity:**
Confirm `validate_st_cases.py` already passed in Feature-ST (Step 9).
No re-validation needed — Feature-ST Step 5b + Step 6 already cover T1.

If all checks pass → proceed to Persist.
If any check fails → fix inline, re-verify. No SubAgent dispatch.

Record in `task-progress.md`:
```
- Inline Check: PASS (P2: N/N methods verified, T2: N/N tests found, D3: OK)
```

### 11. Persist
- Git commit (include implementation, tests, **test case document**)
  > **For `category: "bugfix"` features**: use commit prefix `"fix:"` instead of `"feat:"`.
  > Format: `fix: <feature title without the "Fix: " prefix> (#<fixed_feature_id>)`
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
    - Git: <sha> feat: title
    #### Risks                        ← include only if any risks were reported
    - ⚠ [Mutant] file:line — reason
    - ⚠ [Coverage] metric N% — thin margin / uncovered boundary
    - ⚠ [Dependency] lib==ver — known patch / breaking change pending
    ```
  - **Collecting risks**: after Step 8 (Quality) and Step 9 (Feature-ST) complete, extract every row from their `### Risks` tables; merge into a single list; append as `#### Risks` bullets only if the list is non-empty
- Mark feature `"status": "passing"` in `feature-list.json`
- Set `"st_case_path"` and `"st_case_count"` on the feature object in `feature-list.json`
- Validate:
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- Git commit again (progress files)

### 11.5 Session Reflection (Conditional)

If `retro_authorized` is `true` in `feature-list.json`:
1. Read `skills/long-task-retrospective/prompts/reflection-prompt.md`
2. Fill template variables: feature ID/title, phase, this session's `task-progress.md` entry, any `AskUserQuestion` exchanges where user corrected skill output
3. Dispatch Reflection SubAgent via `Agent(run_in_background=true)` — do NOT wait for completion
4. Proceed to End Session immediately

If `retro_authorized` is absent or `false` → skip entirely (no output, no dispatch).

### 12. End Session
- Stop any services you started directly during this cycle (services started during ST acceptance testing in Step 10 are stopped by `long-task-feature-st`)
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
- **Config gate before planning** — never plan or code when required configs are missing
- **Never mark "passing" without fresh evidence** — run tests, read output, then mark
- **Systematic debugging only** — on error, read `references/systematic-debugging.md`; trace root cause, never guess-and-fix
- **Update RELEASE_NOTES.md after every git commit**
- **Always commit + update progress before ending session** — bridges context gap
- **Never leave broken code** — revert incomplete work

## Red Flags

| Rationalization | Correct Action |
|---|---|
| "I'll mock that config later" | Run Config Gate. Real configs needed. |
| "This feature is trivial, skip test cases" | Invoke long-task-feature-st. Every feature. |
| "This feature is trivial, skip TDD" | Invoke long-task-tdd. Every feature. |
| "Tests pass, mark it done" | Invoke long-task-quality first. |
| "Coverage looks close enough" | Thresholds are hard gates. Run the tool. |
| "Let me just try this quick fix" | Systematic debugging first. |
| "I'll generate examples during Worker" | Examples are post-ST via long-task-finalize. |
| "I'll update release notes at the end" | Update after every commit. |
| "Mutation score is probably OK" | Run mutation tests and read the report. |
| "The UI looks correct to me" | Run automated detection + EXPECT/REJECT. |
| "ST test case failed but the code is fine" | Report to user. No bypass. Fix code or use the `long-task-increment` skill to modify test case. |
| "Port is busy, let me kill manually" | Use env-guide.md "Stop All Services" (port fallback) to kill it, then restart via env-guide.md Start — update env-guide.md if the command needed correction. |
| "Environment is down, skip ST cases" | BLOCKED, not skipped. Fix environment or ask user. |
| "This deprecated feature still needs work" | Skip it. Deprecated features are excluded. |
| "Backend isn't ready but I'll mock it for now" | Dependency check exists for a reason. Develop backend features first. |
| "I'll skip the dependency check this once" | Never skip. Reorder features so deps are satisfied. |

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
1. `long-task:long-task-tdd` (Steps 5-7) — TDD Red-Green-Refactor
2. `long-task:long-task-quality` (Step 8) — Coverage + Mutation
3. `long-task:long-task-feature-st` (Step 9) — Black-Box Feature Acceptance Testing (ISO/IEC/IEEE 29119, self-managed lifecycle)
**Reads/Writes:** feature-list.json, task-progress.md (including `## Current State`), RELEASE_NOTES.md
**Read on-demand (via Read tool, NOT Skill tool):** `references/systematic-debugging.md`
