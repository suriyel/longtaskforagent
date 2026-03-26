# Feature-Level Black-Box Acceptance Testing — SubAgent Execution Reference

You are a Feature-ST execution SubAgent. Follow these rules exactly. When finished, return your result using the **Structured Return Contract** at the bottom of this document.

---

# Feature-Level Black-Box Acceptance Testing

Execute black-box acceptance testing for a completed feature **after** TDD implementation and quality gates pass. This reference independently manages its own environment lifecycle (start → test → cleanup) and generates ISO/IEC/IEEE 29119 compliant test case documents.

## Standard

Default: **ISO/IEC/IEEE 29119-3** (Test Documentation).

Users may override the template and style via `feature-list.json` root fields:
- `st_case_template_path` — custom template file (defines structure)
- `st_case_example_path` — example file (defines style, language, detail level)

## Black-Box Testing Philosophy

TDD (long-task-tdd) has already verified the implementation from the inside:
unit tests exercise code paths; coverage and mutation gates verify completeness.

This skill verifies from the **outside** — as a user or external system would:
- Inputs go in through the real interface (HTTP endpoints, UI, CLI args)
- Outputs observed through the real interface (HTTP responses, rendered UI, stdout)
- Internal implementation is NOT consulted during test design or execution
- Chrome DevTools MCP is the primary execution environment for UI features

**Rule:** If a test case requires reading source code to determine the expected result, it is not a black-box test — rewrite it using only the SRS specification.

## Service Lifecycle (via env-guide.md)

Manage services explicitly using `env-guide.md`. No hooks handle this automatically.

**Pre-existing services**: If Worker Bootstrap already started services (because the feature has service dependencies for TDD), they may still be running when Feature-ST begins. The Start step below checks health first and only starts if not already running. Feature-ST owns **restart** (between test cycles) and **cleanup** (after all cases) — it does NOT assume sole responsibility for first start.

**env-guide.md is the source of truth.** It must always reflect commands that actually work. If a command in env-guide.md fails, fix the command and update env-guide.md before proceeding.

### Start (before first test case)

1. **Read `env-guide.md`** — locate the "Start All Services" section
2. **Check if services are already running**: run the "Verify Services Running" health checks
   - If already running and healthy: record PID/port in `task-progress.md`; proceed
3. **If not running**: execute each start command with output capture:
   ```bash
   # Unix/macOS
   [start command] > /tmp/svc-<slug>-start.log 2>&1 &
   sleep 3
   head -30 /tmp/svc-<slug>-start.log

   # Windows
   cmd /c "start /b [command] > %TEMP%\svc-<slug>-start.log 2>&1"
   timeout /t 3 /nobreak >nul
   powershell "Get-Content $env:TEMP\svc-<slug>-start.log -TotalCount 30"
   ```
   - Extract PID and port from the first 30 lines; record both in `task-progress.md`
   - Run "Verify Services Running" health checks from `env-guide.md` — must respond before proceeding
4. **If start fails**: check the log file, diagnose root cause
   - Try corrected commands (port conflict, missing env vars, env not activated, missing dependencies)
   - Once a working command is found: **update `env-guide.md`** — fix the Services table row and Start command; if the fix requires >2 shell commands, extract to `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-start.ps1` and update env-guide.md to call the script
   - Set Verdict to BLOCKED if service cannot be started after 3 attempts

### Cleanup (after all test cases complete) — MANDATORY

1. **Read `env-guide.md`** — locate "Stop All Services" and "Verify Services Stopped" sections
2. **Stop services**: kill by PID (from `task-progress.md`) — preferred; or kill by port (fallback commands in `env-guide.md`)
   - If the stop command fails (PID not found, kill returns error): try the port-based fallback; once a working command is confirmed, **update `env-guide.md`** Stop command to reflect the fix
3. **Verify stopped**: run "Verify Services Stopped" commands — ports must not respond (max 5 seconds)
4. **Record**: note cleanup status in `task-progress.md`

**Why mandatory**: Leaving services running causes port conflicts in subsequent ST cycles.

### Restart Protocol (between fix-and-retest cycles)

When a test case fails, code is fixed, and services must restart:

1. **Kill**: stop by PID (from `task-progress.md`) or by port (env-guide.md Stop commands)
   - If kill fails: try port-based fallback; once working, **update `env-guide.md`** Stop command
2. **Verify dead**: poll port — must not respond within 5 seconds
3. **Start**: run start command with output capture (`head -30`) — extract new PID/port; update `task-progress.md`
   - If start fails: diagnose, fix, **update `env-guide.md`** before retrying
4. **Verify alive**: poll health endpoint — must respond within 10 seconds

### Scripts Convention (for complex service sequences)

If startup or cleanup requires >2 shell steps (e.g., DB migration + seed + server start), consolidate into versioned scripts rather than keeping complex inline commands in env-guide.md:

- Create `scripts/svc-<slug>-start.sh` (Unix) / `scripts/svc-<slug>-start.ps1` (Windows) — full startup sequence
- Create `scripts/svc-<slug>-stop.sh` / `scripts/svc-<slug>-stop.ps1` — full teardown sequence
- Update `env-guide.md` "Start All Services" to call `bash scripts/svc-<slug>-start.sh` (or `pwsh scripts/svc-<slug>-start.ps1`)
- Commit the scripts and updated env-guide.md together in the same commit

## Checklist

You MUST complete each step in order:

### 1. Load Context

Read all input artifacts for the target feature:

- **Feature object** from `feature-list.json` — ID, title, description, srs_trace, ui flag, dependencies, priority
- **SRS section** — full FR-xxx from `docs/plans/*-srs.md` via Document Lookup Protocol (read the entire subsection, NOT grep)
- **Design section** — full §4.N from `docs/plans/*-design.md` via Document Lookup Protocol
- **ATS constraints** (if `docs/plans/*-ats.md` exists) — read the ATS mapping table rows for the requirement(s) that map to this feature; extract required categories. These category constraints are **binding** for Step 3 (Derive Test Cases).
- **Plan document** — from Step 5 (`docs/features/YYYY-MM-DD-<feature-name>.md`)
- **UCD sections** (only if `"ui": true`) — relevant component prompts and page prompts from `docs/plans/*-ucd.md`
- **Root context** — `constraints[]`, `assumptions[]` from `feature-list.json` root
- **Related NFRs** — check SRS for NFR-xxx requirements that trace to this feature
- **Interface contracts** — API endpoints, CLI commands, UI entry points that form the observable surface of this feature
- **Test results summary** — from TDD and Quality Gates (coverage %, mutation score)

### 2. Load Template

1. Check `feature-list.json` root for `st_case_template_path`:
   - If present and file exists: read the custom template
   - If absent: use default template at `docs/templates/st-case-template.md`
2. Check `feature-list.json` root for `st_case_example_path`:
   - If present and file exists: read the example file — adapt style, language, and detail level from it
   - If absent: use standard professional style

**Template + Example interaction:**
- Both provided → use template's **structure**, example's **style**
- Only template → use template structure with default style
- Only example → infer structure from example, use example's style
- Neither → use the built-in default template (ISO/IEC/IEEE 29119-3)

### 2b. Load UI Execution Protocol (for `"ui": true` features)

If the target feature has `"ui": true`, read `skills/long-task-feature-st/prompts/e2e-scenario-prompt.md`. This provides mandatory rules for generating Chrome DevTools MCP-executable E2E test scenarios. Apply these rules during Step 3 for all UI category test cases.

**Why**: Without this prompt, UI test cases tend to be simple page-load checks. The prompt ensures each test step maps to a concrete MCP tool call (`navigate_page`, `click`, `fill`, `take_snapshot`, `evaluate_script`, `list_console_messages`) and follows the three-layer detection model. Chrome DevTools MCP is the **primary** testing vehicle for UI features in this skill.

### 3. Derive Test Cases

For each SRS acceptance criterion (via the feature's `srs_trace` → SRS doc) mapped to this feature, generate **one or more** test cases. The Feature Design Test Inventory (§7) and boundary matrix (§5c) provide additional test case sources.

**Category assignment rules:**

| Category | Abbrev | When to generate |
|----------|--------|------------------|
| `functional` | FUNC | Always — happy path + error path for every feature |
| `boundary` | BNDRY | Always — edge cases, limits, empty/max/zero values |
| `ui` | UI | Only when `"ui": true` — Chrome DevTools MCP interaction + visual verification |
| `security` | SEC | When feature handles user input, auth, or external data |
| `performance` | PERF | Only when traceable to NFR-xxx with performance metrics |

**UI test case enrichment (mandatory for `"ui": true` features):**
- Every UI category test case MUST have ≥ 5 steps in the test step table
- Every step MUST specify the Chrome DevTools MCP tool that executes it (`navigate_page`, `click`, `fill`, `take_snapshot`, `evaluate_script`, etc.)
- Every test case MUST include all three detection layers (Layer 1: `evaluate_script`, Layer 2: EXPECT/REJECT, Layer 3: `list_console_messages`)
- Test cases that verify data MUST include backend integration steps (real API data, not mocked)
- Test cases MUST test at least one negative path via UI (e.g., submit invalid form → verify error message)
- See `skills/long-task-feature-st/prompts/e2e-scenario-prompt.md` for detailed expansion rules and examples

**ATS enforcement (if ATS document exists):**
- Read the ATS mapping table rows loaded in Step 1
- For each ATS-required category for this feature's requirement(s): generate at least one test case of that category
- If ATS requires SEC but the feature does not handle user input, note the discrepancy in the test case document and generate at least one boundary-security case
- **ATS category constraints are hard gates** — validate via `python scripts/check_ats_coverage.py` in Step 6

**Minimum coverage:**
- Every feature MUST have at least one FUNC and one BNDRY test case
- Every `srs_trace` requirement MUST be covered by at least one test case
- UI features MUST have at least one UI test case
- If ATS exists: all ATS-required categories are met

**Case ID format:**
```
ST-{CATEGORY}-{FEATURE_ID(3 digits)}-{SEQ(3 digits)}
```
Examples: `ST-FUNC-005-001`, `ST-UI-005-002`, `ST-SEC-012-001`

**Test case content rules:**
- Test steps MUST be concrete and executable (no vague "verify it works")
- Expected results MUST be specific and assertable (no "should look correct")
- Preconditions MUST list real, verifiable states
- Verification points MUST be observable and automatable where possible

**Acceptance-level focus:** Test cases confirm the implementation matches requirements from a user/system perspective — not duplicating unit test assertions. Focus on behavioral scenarios, integration paths, and end-to-end workflows.

**Test type labeling (real/mock)** — for each derived test case, set the `Test Type` metadata field:
- Mark as `Real` if the test case executes against a real running system (real DB, real HTTP service, real browser via Chrome DevTools MCP, real file system)
- Mark as `Mock` only if the test case's primary execution path uses a mock or stub service
- Feature-ST test cases executed against a running service (Step 7 starts services before execution) are **always `Real`** — they connect to real services

**Black-box constraint:** Expected results must be derivable solely from the SRS (acceptance criteria via `srs_trace`, Given/When/Then, NFR thresholds) and the observable interface. If the expected result cannot be determined without reading implementation code, raise it as a specification gap.

### 4. UI Test Case Requirements (only if `"ui": true`)

For UI features, test cases consolidate previously separate concerns:

**a) Functional UI testing** — navigation, interaction, state changes:
- Navigation path from `ui_entry` or specific route
- Interaction sequence: `click`, `fill`, `press_key` steps
- EXPECT/REJECT clauses (mandatory for every UI test step)

**b) UCD compliance** — style token verification:
- Reference which UCD color palette tokens apply to verified elements
- Reference which typography scale values apply
- Reference which spacing tokens apply
- This replaces the separate U1-U4 review check for individual elements

**c) Accessibility** — WCAG 2.1 AA:
- Keyboard navigability for interactive elements
- Color contrast verification against WCAG minimum ratios
- ARIA attributes and semantic HTML verification
- Screen reader compatibility notes

**d) Console error gate:**
- Every UI test case MUST include a post-step check: `list_console_messages(types=["error"])` must return 0
- Exception: if test explicitly expects console errors, note with `[expect-console-error: <pattern>]`

**e) Three-layer detection:**
- Layer 1: Automated error detection script via `evaluate_script()` — reference `skills/long-task-tdd/references/ui-error-detection.md`
- Layer 2: EXPECT/REJECT format in test steps
- Layer 3: Console error gate

**f) MCP tool call mapping:**
- Each test step's "操作" column must be specific enough to map to a single Chrome DevTools MCP tool call
- BAD: "检查登录页面" — which tool? what to check?
- GOOD: "`navigate_page(url='/login')` → `wait_for(['Sign In'])` → `take_snapshot()` → 验证 EXPECT: 邮箱输入框, 密码输入框, 登录按钮"
- The test step table becomes a **script** that can be mechanically translated into Chrome DevTools MCP calls
- See `skills/long-task-feature-st/prompts/e2e-scenario-prompt.md` for the full MCP tool → test step mapping table

### 5. Write Test Case Document

Output file: `docs/test-cases/feature-{id}-{slug}.md`
- `{id}` is the feature ID (as-is, not zero-padded in filename)
- `{slug}` is a kebab-case version of the feature title

**Document structure (following template):**

1. **Header** — Feature ID, related requirements, date, standard
2. **Summary table** — count by category
3. **Test case blocks** — one per case, all required sections
4. **Traceability matrix** — Case ID ↔ Requirement (srs_trace) ↔ Feature Design Test Inventory row ↔ Automated test ↔ Result

The traceability matrix `结果` column starts as `PENDING`. Execute each test case in Step 7 below and update to `PASS`/`FAIL` during this step.

### 5b. SRS Trace Coverage Gate (mandatory before validation)

**a) SRS requirement completeness:**
1. List ALL `srs_trace` requirement IDs from the feature object
2. For each requirement ID: confirm at least one ST case maps to it
   in the traceability matrix "Requirement" column
3. If ANY `srs_trace` requirement has zero ST case mapping:
   - Derive additional test case(s) for the uncovered requirement
   - Add to the document and traceability matrix
   - Re-number case IDs if necessary

**b) `# ST-xxx` code annotation is NOT required:**
Traceability is maintained solely via the ST document's traceability matrix
("自动化测试" column maps ST case → test function). Redundant code-level
`# ST-xxx` comments are not required and should not be added.

### 6. Validate

Run the validation scripts:

```bash
python scripts/validate_st_cases.py docs/test-cases/feature-{id}-{slug}.md --feature-list feature-list.json --feature {id}
```

If ATS document exists, also run ATS coverage check:
```bash
python scripts/check_ats_coverage.py docs/plans/*-ats.md --feature-list feature-list.json --feature {id} --strict
```

- **Both exit 0**: proceed to Execute Test Cases (Step 7)
- **Any exit 1**: fix errors and re-validate (do NOT proceed with errors)

### 7. Execute Test Cases

Since implementation code already exists (TDD and Quality Gates are complete), execute each test case to verify acceptance:

**HARD REQUIREMENT: Must execute test cases one by one as defined in `docs/test-cases/feature-{id}-{slug}.md`**
- Each test case must be executed individually and results recorded
- **UI test cases CANNOT be skipped for any reason** — UI verification is mandatory
- No test case may be skipped
- Do not merge or simplify the test case execution process
- **UI test cases MUST use Chrome DevTools MCP for verification**

1. **Start services** per Service Management above — follow env-guide.md start protocol with output capture; record PID and port in `task-progress.md`
2. For **non-UI test cases**: verify by running relevant test commands or manual checks against the running system
3. For **UI test cases**: execute via Chrome DevTools MCP following the step tables — see `skills/long-task-feature-st/prompts/e2e-scenario-prompt.md` for MCP tool mapping
4. Update the traceability matrix `结果` column to `PASS` or `FAIL` for each case
4b. Update the **Real Test Case Execution Summary** table in the test case document:
   - Count all `Real` cases from the traceability matrix and their PASS/FAIL status
   - Fill in the summary table (total / passed / failed / pending)
   - Any `Real` FAIL is a blocking failure — same consequence as any other test case failure
5. **Stop services** per Service Management cleanup above

**If any test case FAILS:**
- Include failure details in the Issues table of the Structured Return Contract
- A failure here blocks the feature from proceeding to Persist
- Set Verdict to FAIL with specific case IDs and failure details

**If all test cases PASS:**
- Set Verdict to PASS

Traceability between ST cases and automated tests is maintained in the ST case
document's traceability matrix (not via code comments). See Step 5b.

## Execution Rules (Hard Gates)

### Environment Gate

Always start from a known-clean state. Do not assume services are already running.

- Start services per Service Management above; verify health endpoint before running any test cases
- If service fails to start after diagnosis: **BLOCKED** — set Verdict to BLOCKED with service details
- After start: verify app is responding before running any test cases

### Failure Is Not Bypassable

- **Any test case execution failure** blocks the feature from being marked `"passing"`
- **ALL bugs found in ST testing MUST be fixed** — regardless of whether they are:
  - Frontend bugs (UI rendering, interaction, state)
  - Backend bugs (API errors, data persistence, logic)
  - Integration bugs (frontend-backend communication)
- **No bypass allowed** for any reason:
  - "Simple feature" — still needs test cases
  - "UI tests are complex" — **UI test cases CANNOT be skipped; use Chrome DevTools MCP**
  - "Browser testing is too complex" — **UI test cases MUST use Chrome DevTools MCP for verification**
  - "This is a frontend bug, not my code" — **ALL bugs must be fixed**
  - "This is a backend bug, let someone else fix it" — **ALL bugs must be fixed**
  - "Environment temporarily unavailable" — BLOCKED, not skipped
  - "Test case might be wrong" — set Verdict to FAIL, don't skip
- All failures MUST be recorded in the Structured Return Contract Issues table

## Critical Rules

- **Requirements-driven**: Test cases derive from SRS/Design, validating implementation against requirements — not duplicating unit test assertions
- **Black-box only**: Expected results must be derivable from SRS and the observable interface alone — no reading implementation code
- **Complete after Quality Gates**: All test cases must be written, validated, and executed after TDD and quality gates pass
- **Immutable after generation**: Test case documents are written and executed in this step and not modified after generation. Changes require the `long-task-increment` skill
- **Traceability mandatory**: Every test case traces to a requirement; every `srs_trace` requirement traces to a test case
- **UI consolidation**: For UI features, this skill consolidates functional, UCD compliance, and accessibility testing into unified test cases
- **Template flexibility**: Users can override the default ISO/IEC/IEEE 29119 template with custom templates and style examples
- **UI tests are mandatory**: For features with `"ui": true`, UI category test cases are NON-SKIPPABLE — they MUST use Chrome DevTools MCP for browser-based verification. There is no alternative or workaround.
- **ALL bugs must be fixed**: Any bug discovered during ST testing — whether frontend, backend, or integration — MUST be fixed before the feature can be marked as passing. There is no "not my code" exemption.

---

## Structured Return Contract

When all test cases are executed (or if blocked), return your result in EXACTLY this format:

```markdown
## SubAgent Result: Feature-ST
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-3 sentences — how many test cases derived, how many executed, key outcomes, environment status]
### Artifacts
- [docs/test-cases/feature-{id}-{slug}.md]: ST test case document with executed results
- [any other files created/modified]
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Total Cases | N | ≥M (ATS or minimum) | PASS/FAIL |
| FUNC Cases | N | ≥1 | PASS/FAIL |
| BNDRY Cases | N | ≥1 | PASS/FAIL |
| UI Cases | N | ≥1 (if ui:true) | PASS/FAIL |
| SEC Cases | N | ≥1 (if applicable) | PASS/FAIL |
| PERF Cases | N | ≥0 | PASS/FAIL |
| Execution Pass Rate | N/M | M/M | PASS/FAIL |
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
| 1 | Critical/Major/Minor | [failed case ID, step details, actual vs expected] |
### Next Step Inputs
- st_case_path: docs/test-cases/feature-{id}-{slug}.md
- st_case_count: [total number of test cases]
- environment_cleaned: true/false
```

**IMPORTANT**: Do NOT mark the feature as "passing" in feature-list.json — that is the orchestrator's responsibility. Only report the results.
