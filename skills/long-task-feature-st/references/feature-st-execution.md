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

### 3. Derive Test Cases

For each SRS acceptance criterion (via the feature's `srs_trace` → SRS doc) mapped to this feature, generate **one or more** test cases. The Feature Design Test Inventory (§7) and boundary matrix (§5c) provide additional test case sources.

**Category assignment rules:**

| Category | Abbrev | When to generate |
|----------|--------|------------------|
| `functional` | FUNC | Always — happy path + error path for every feature |
| `boundary` | BNDRY | Always — edge cases, limits, empty/max/zero values |
| `ui` | UI | Only when `"ui": true` — browser-based interaction + visual verification |
| `security` | SEC | When feature handles user input, auth, or external data |
| `performance` | PERF | Only when traceable to NFR-xxx with performance metrics |

**UI test case enrichment (mandatory for `"ui": true` features):**
- UI category test cases should cover navigation, interaction, and visual verification using Chrome DevTools MCP tools
- Test cases that verify data MUST include backend integration steps (real API data, not mocked)
- Test cases MUST test at least one negative path via UI (e.g., submit invalid form → verify error message)

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

**Acceptance-level focus:** Test cases confirm the implementation matches requirements from a user/system perspective — not duplicating unit test assertions. Focus on behavioral scenarios and end-to-end workflows from the user/system perspective. Per-feature integration with external dependencies is verified during TDD (via INTG rows in Test Inventory). ST focuses on verifying the feature works correctly through the real running system interface.

**Test type labeling (real/mock)** — for each derived test case, set the `Test Type` metadata field:
- Mark as `Real` if the test case executes against a real running system (real DB, real HTTP service, real browser via Chrome DevTools MCP, real file system)
- Mark as `Mock` only if the test case's primary execution path uses a mock or stub service
- Feature-ST test cases executed against a running service (Step 7 starts services before execution) are **always `Real`** — they connect to real services

**Automation feasibility labeling** — for each derived test case, set the `已自动化` metadata field:
- `Yes` (default) — test can be executed programmatically (CLI, API, Chrome DevTools MCP)
- `No` — test genuinely cannot be automated; requires physical device, human visual judgment, or external human action

When `已自动化: No`, also set:
- **手动测试原因 (Manual Test Reason)**: one of `physical-device`, `visual-judgment`, `external-action`, `other: {description}`

**Decision authority:**
- If ATS document exists and has `自动化可行性` column: inherit the ATS value as primary source
- SubAgent may mark a case as `已自动化: No` during derivation if it determines the test requires physical/visual/external action, even if ATS did not flag it — but MUST document the reason
- A case marked `Auto` in ATS SHOULD NOT be downgraded to `No` without explicit justification in the test case document

**Conservative flagging**: Only mark as `已自动化: No` when automation is genuinely impossible, not merely difficult. Chrome DevTools MCP covers most UI testing; mock services cover most external dependencies. Reserve `No` for true gaps.

**Black-box constraint:** Expected results must be derivable solely from the SRS (acceptance criteria via `srs_trace`, Given/When/Then, NFR thresholds) and the observable interface. If the expected result cannot be determined without reading implementation code, document it as a specification gap in the test case document and proceed with best interpretation from SRS.

### 4. UI Test Case Requirements (only if `"ui": true`)

For UI features, test cases consolidate previously separate concerns:

**a) Functional UI testing** — navigation, interaction, state changes:
- Navigation path from `ui_entry` or specific route
- Interaction sequence using Chrome DevTools MCP tools
- Expected results for each interaction step

**b) UCD compliance** — style token verification:
- Reference which UCD color palette tokens apply to verified elements
- Reference which typography scale values apply
- Reference which spacing tokens apply
- This replaces the separate U1-U4 review check for individual elements

**c) Backend integration verification** (when feature depends on backend APIs):
- Test cases MUST verify real data from backend — not hardcoded or mocked data
- Include at least one data mutation + persistence scenario: create/update/delete via UI → verify backend persisted → refresh page → verify UI reflects the change
- Include at least one error state scenario: what the UI shows when backend returns error (500/503/timeout) — verify user-friendly error message
- Include at least one empty state scenario: what the UI shows when backend returns empty data — verify the empty state is visually correct per UCD

**d) Cross-page workflow** (when feature spans multiple pages):
- Test the complete workflow across page transitions (page A → action → page B → verify → page C → verify)
- Do NOT test pages in isolation — the E2E value comes from the transitions
- Each page transition should verify the new page loaded without errors

**e) State mutation verification** (when feature creates/updates/deletes data):
- Perform mutation via UI → navigate away from current page → navigate back → verify the mutation persisted
- This confirms backend persistence, not just frontend state
- Verify related views also reflect the change (e.g., create order → order list shows new order → dashboard counter incremented)

**f) Positive rendering verification** (mandatory for all `"ui": true` features):

Every UI category ST test case MUST include at least one step that verifies expected visual elements are **positively present**, not just error-free. This uses the Layer 1b positive rendering verification script from `references/ui-error-detection.md` (in long-task-tdd).

For each visual element listed in the Feature Design Visual Rendering Contract (§Visual Rendering Contract of the feature design document):
1. Navigate to the page or trigger the rendering condition specified in the contract
2. Execute the Layer 1b positive rendering script with the element's selector/canvas ID
3. Assert `missingCount === 0` — all expected elements are rendered and visible

**Hard gate**: An ST test case that only runs the error detection script (Layer 1) without positive rendering verification (Layer 1b) is **incomplete** for UI features. A page with zero errors but no rendered game content, no rendered data, or no rendered visual elements is a FAIL.

Test step example for Canvas game:

| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 3 | evaluate_script(positive_render_checker, [], ['game-canvas']) | Layer 1b: missingCount = 0, canvas has non-transparent pixels |
| 4 | evaluate_script(() => { const segments = document.querySelectorAll('.snake-segment'); return segments.length; }) | Snake segments rendered: count >= 1 |

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
- **UI test cases require browser-based verification**

1. **Start services** per Service Management above — follow env-guide.md start protocol with output capture; record PID and port in `task-progress.md`
2. For **automated non-UI test cases** (`已自动化: Yes`): verify by running relevant test commands or programmatic checks against the running system
2b. For **manual test cases** (`已自动化: No`): do NOT attempt to execute.
   - Record `PENDING-MANUAL` in the traceability matrix `结果` column
   - These cases will be presented to the human AFTER the SubAgent returns (via the dispatcher's Step 4b)
   - Continue to the next test case
3. For **UI test cases** (`已自动化: Yes`, `ui` category): execute via Chrome DevTools MCP
4. Update the traceability matrix `结果` column:
   - Automated cases: `PASS` or `FAIL`
   - Manual cases: `PENDING-MANUAL` (human review happens post-SubAgent in the dispatcher)
4b. Update the **Real Test Case Execution Summary** table in the test case document:
   - Count all `Real` cases from the traceability matrix and their PASS/FAIL status (exclude `PENDING-MANUAL`)
   - Fill in the summary table (total / passed / failed / pending)
   - Any `Real` FAIL is a blocking failure — same consequence as any other test case failure
4c. If manual test cases exist, update the **Manual Test Case Summary** table:
   - Count all manual cases (all should be `PENDING-MANUAL` at this point)
5. **Do NOT stop services yet** — if the feature is `"ui": true`, Step 8 (Exploratory Visual Assessment) requires the application to be running. Services are stopped AFTER Step 8.

**If any automated test case FAILS:**
- Include failure details in the Issues table of the Structured Return Contract
- A failure here blocks the feature from proceeding to Persist
- Set Verdict to FAIL with specific case IDs and failure details

**If all automated test cases PASS (manual cases may still be PENDING-MANUAL):**
- Set Verdict to PASS (the dispatcher will re-evaluate after collecting manual results)

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
  - "UI tests are complex" — **UI test cases CANNOT be skipped**
  - "Browser testing is too complex" — **UI test cases require browser-based verification**
  - "This is a frontend bug, not my code" — **ALL bugs must be fixed**
  - "This is a backend bug, let someone else fix it" — **ALL bugs must be fixed**
  - "Environment temporarily unavailable" — BLOCKED, not skipped
  - "Test case might be wrong" — set Verdict to FAIL, don't skip
- All failures MUST be recorded in the Structured Return Contract Issues table

## Step 8: Exploratory Visual Assessment (mandatory for `"ui": true`)

After all scripted test cases are executed (Step 7), perform a **free-form visual assessment** of the running application. This step is inspired by the GAN-style generator-evaluator pattern: the scripted tests verify specification compliance, but the exploratory assessment catches issues that scripted tests miss — "display-only" features without interactive depth, visual incoherence, and rendering gaps invisible to mechanical checks.

**Do NOT skip this step.** This is where you act as a skeptical QA evaluator, not a generator defending its own work.

### 8a. Navigate and Screenshot

1. Start from the feature's `ui_entry` URL
2. Navigate through ALL pages/views related to this feature
3. At each page: `take_screenshot()` → visually study the result
4. Interact with every rendered element: click buttons, hover links, type into inputs, scroll containers, trigger animations
5. Record what you observe — do NOT assume anything works until you verify it

### 8b. Grade Against Visual Quality Criteria

Score each criterion 1-5 using the anchors below. **Any criterion scoring ≤ 2 is a FAIL.**

**Score anchors** (apply to ALL criteria):
- **1**: Complete absence — nothing related to this criterion is present
- **2**: Minimal/broken — some elements exist but core content is missing or non-functional (e.g., canvas exists but is blank; form renders but can't submit)
- **3**: Partial — core content present with notable gaps (e.g., game board renders but some visual elements missing; data list shows items but pagination broken)
- **4**: Complete with minor gaps — all expected elements rendered and interactive, minor polish issues (e.g., alignment slightly off; one state variant not styled)
- **5**: Fully complete — all Visual Rendering Contract elements present, interactive, correctly styled, reflecting real data

| Criterion | Weight | What to assess | Failure signals |
|-----------|--------|----------------|-----------------|
| **Rendering Completeness** | High | Are ALL visual elements from the Visual Rendering Contract actually rendered and visible? Is the core visual content present (game board, data visualization, interactive canvas), not just chrome (buttons, menus, headers)? | Blank canvas, empty containers, placeholder text, "display-only" UI with no actual content rendered |
| **Interactive Depth** | High | Do rendered elements actually respond to user interaction? Can the user perform the feature's core action through the UI, not just see static elements? | Buttons that don't respond, canvas with no input handling, forms that don't submit, game board that doesn't update on key press |
| **Visual Coherence** | Medium | Does the UI feel like a coherent whole? Are colors, typography, spacing, and layout consistent? Do elements align to a grid? | Misaligned elements, inconsistent spacing, clashing colors, mixed font sizes with no hierarchy |
| **Functional Accuracy** | Medium | Does the rendered output reflect actual data/state? Does the score display match the game state? Does the list show real items? | Hardcoded placeholder data, counters showing 0 when data exists, stale state after interactions |

**Anti-leniency rules (read these before grading):**
- "Looks OK at first glance" is not a passing grade — **click every interactive element**
- A page that renders a header and sidebar but has a blank main content area is a **FAIL on Rendering Completeness**, even if the header and sidebar look perfect
- "The core logic works in unit tests" is irrelevant — you are grading what the **user sees and can interact with in the browser**
- If you find yourself writing "this is acceptable because..." — STOP. That is leniency bias. Grade what you see, not what you wish were there.
- A snake game where the canvas is blank but the score counter works is a **FAIL** — the canvas IS the feature
- A form that renders all fields but doesn't submit is a **FAIL on Interactive Depth** — rendering without interaction is display-only

### 8c. "Display-Only" Detection

For each rendered element from the Visual Rendering Contract, verify it has **interactive depth** — not just visual presence:

| Element Type | Presence Check (Layer 1b) | Interactive Depth Check (this step) |
|-------------|--------------------------|-------------------------------------|
| Canvas (game) | Has non-transparent pixels | Responds to keyboard/mouse input; game state updates; visual output changes |
| Form | Input fields visible | Fields accept input; submit triggers action; validation fires |
| Data display | Elements visible with content | Reflects real data; updates on state change; pagination/scroll works |
| Navigation | Links/buttons visible | Click navigates to correct route; back button works |
| Interactive widget | Widget rendered | Drag, resize, toggle, slider — the interaction it's designed for actually works |

If any element passes Layer 1b (presence) but fails interactive depth → record as **"Display-Only Defect"** in the Issues table with severity **Major**.

### 8d. Record Assessment

Add to the Structured Return Contract:

```markdown
### Visual Assessment (ui:true only)
| Criterion | Score (1-5) | Evidence |
|-----------|-------------|----------|
| Rendering Completeness | N | [what was/wasn't rendered] |
| Interactive Depth | N | [what responded/didn't respond to interaction] |
| Visual Coherence | N | [alignment, spacing, color consistency observations] |
| Functional Accuracy | N | [data correctness observations] |

Display-Only Defects: [count]
[list each: element, what it renders, what interaction it lacks]
```

**Verdict impact:** Any criterion ≤ 2 OR any Display-Only Defect → overall Verdict is **FAIL**.

### 8e. Service Cleanup (after Visual Assessment)

**Stop services** per Service Management cleanup above. For non-UI features, this was done in Step 7.5. For UI features, it is deferred to here because Step 8 requires a running application.

---

## Critical Rules

- **Requirements-driven**: Test cases derive from SRS/Design, validating implementation against requirements — not duplicating unit test assertions
- **Black-box only**: Expected results must be derivable from SRS and the observable interface alone — no reading implementation code
- **Complete after Quality Gates**: All test cases must be written, validated, and executed after TDD and quality gates pass
- **Immutable after generation**: Test case documents are written and executed in this step and not modified after generation. Changes require the `long-task-increment` skill
- **Traceability mandatory**: Every test case traces to a requirement; every `srs_trace` requirement traces to a test case
- **UI consolidation**: For UI features, this skill consolidates functional and UCD compliance testing into unified test cases
- **Template flexibility**: Users can override the default ISO/IEC/IEEE 29119 template with custom templates and style examples
- **UI tests are mandatory**: For features with `"ui": true`, UI category test cases are NON-SKIPPABLE and require browser-based verification.
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
| Manual Cases | N | N/A | INFO |
| Visual Assessment Min Score | N | ≥3 (if ui:true) | PASS/FAIL/N/A |
| Display-Only Defects | N | 0 (if ui:true) | PASS/FAIL/N/A |
### Visual Assessment (only if ui:true)
| Criterion | Score (1-5) | Evidence |
|-----------|-------------|----------|
| Rendering Completeness | N | [observations] |
| Interactive Depth | N | [observations] |
| Visual Coherence | N | [observations] |
| Functional Accuracy | N | [observations] |
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
| 1 | Critical/Major/Minor | [failed case ID, step details, actual vs expected] |
### Manual Test Cases (only if any 已自动化: No cases exist)
| Case ID | Test Objective | Manual Reason | Preconditions | Test Steps Summary | Verification Points |
|---------|---------------|---------------|---------------|-------------------|---------------------|
| ST-FUNC-005-003 | {objective} | visual-judgment | {preconditions} | {summarized steps} | {verification points} |
### Next Step Inputs
- st_case_path: docs/test-cases/feature-{id}-{slug}.md
- st_case_count: [total number of test cases]
- manual_case_count: [number of manual test cases, 0 if none]
- environment_cleaned: true/false
```

**IMPORTANT**: Do NOT mark the feature as "passing" in feature-list.json — that is the orchestrator's responsibility. Only report the results.
