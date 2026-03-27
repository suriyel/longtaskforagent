---
name: long-task-st
description: "Use when all features in feature-list.json are passing - run comprehensive system testing before release, aligned with IEEE 829 and ISTQB best practices"
---

# System Testing — Cross-Feature & System-Wide Verification Before Release

Run cross-feature and system-wide testing after all features are implemented and passing. Per-feature ST test cases (functional, boundary, UI, security) have already been executed during each Worker cycle via `long-task-feature-st`. This phase focuses on what per-feature testing **cannot** cover: cross-feature interactions, multi-feature E2E workflows, system-wide NFR verification, compatibility, and exploratory testing.

**Announce at start:** "I'm using the long-task-st skill. All features are passing — time for cross-feature system testing."

**Core principle:** Per-feature ST test cases prove individual features meet their requirements. System testing proves the whole works together across feature boundaries.

<HARD-GATE>
Do NOT skip any applicable test category. A "Go" verdict requires evidence from EVERY category that applies to this project. "It probably works" is not evidence.
</HARD-GATE>

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. ST Readiness Gate

```bash
python scripts/check_st_readiness.py feature-list.json
```

- All features have `"status": "passing"` — if any failing, invoke `long-task:long-task-work` instead
- SRS document exists (`docs/plans/*-srs.md`); Design document exists (`docs/plans/*-design.md`)
- Load config values if applicable — activate environment per `long-task-guide.md`; if the project uses a file-based config, ensure it is sourced before running the checks
- **Start ST runtime services**: Start services using commands from `env-guide.md` (skip if CLI/library only)
  - Read `env-guide.md` — use "Start All Services" section; run each command with output redirect:
    ```bash
    [start command] > /tmp/svc-<slug>-start.log 2>&1 &
    sleep 3
    head -30 /tmp/svc-<slug>-start.log
    ```
  - Extract PID and port from the first 30 lines
  - Run "Verify Services Running" health checks from `env-guide.md` — must respond before proceeding
  - If start fails: check the log, diagnose root cause; try corrected commands (port conflict, env vars, missing deps); once a working command is confirmed **update `env-guide.md`** (Services table + Start command); if the fix needs >2 steps, extract to `scripts/svc-<slug>-start.sh` and reference from env-guide.md; then report to user via `AskUserQuestion`
  - **Record info**: PIDs and ports in `task-progress.md` — required for Step 11 cleanup
- Read `feature-list.json` — note `tech_stack`, `quality_gates`, `constraints[]`, `assumptions[]`
- Read SRS — extract all FR-xxx, NFR-xxx, IFR-xxx, CON-xxx requirements; read Stakeholders, User Personas, and Glossary sections
- Read Design doc — extract architecture, API design, testing strategy (§9), third-party dependencies (§8)
- If UI features exist: read UCD doc (`docs/plans/*-ucd.md`)
- Read `task-progress.md` — session history context

### 2. ST Plan

Create `docs/plans/YYYY-MM-DD-st-plan.md` with:

#### 2a. Test Scope

| Category | Applies When | Skip When |
|----------|-------------|-----------|
| Regression | Always | Never |
| Integration | 2+ features with shared data/state/APIs | Single isolated feature |
| E2E Scenarios | SRS has multi-step user workflows | Pure library/utility projects |
| Performance | SRS has NFR-xxx with response time / throughput targets | No performance NFRs |
| Security | Security NFRs OR project handles user input / auth / external data | Isolated offline tools |
| Compatibility | SRS specifies platform / browser / runtime targets | Single-platform CLI tools |
| Exploratory | Always | Never |

#### 2b. Requirements Traceability Matrix (RTM)

Map EVERY SRS requirement to ST test approach. Reference per-feature test case documents from Worker Step 9:

```markdown
| Req ID | Requirement | Feature ST Status | System ST Category | ATS Categories | Test Approach | Priority |
|--------|-------------|-------------------|--------------------|----------------|---------------|----------|
| FR-001 | ... | docs/test-cases/feature-1-xxx.md (PASS) | E2E | FUNC,BNDRY,SEC | Scenario: ... | High |
| NFR-001 | ... | docs/test-cases/feature-5-xxx.md (PASS) | Performance | PERF | Load test: ... | Critical |
| IFR-001 | ... | N/A (cross-feature) | Integration | FUNC,BNDRY | Contract test: ... | High |
```

Every FR-xxx, NFR-xxx, IFR-xxx must appear in the RTM. Requirements without a test approach = **gap**.

**ATS compliance gate** (if ATS document exists):
```bash
python scripts/check_ats_coverage.py docs/plans/*-ats.md --feature-list feature-list.json --strict
```
Must exit 0. Any ATS category gap = finding to resolve before proceeding.

#### 2c. Entry / Exit Criteria

**Entry** (must ALL be true): all features passing, environment provisioned, all required configs present.

**Exit** (must ALL be true for Go verdict): all regression/integration/E2E tests pass, all NFR thresholds met with measured evidence, no Critical or Major defects open, RTM shows 100% requirement coverage, **ATS category compliance verified** (if ATS exists: `check_ats_coverage.py --strict` exits 0).

#### 2d. Risk-Based Prioritization

1. Critical path — core user workflows, highest business impact
2. Integration boundaries — cross-feature data flows, API contracts
3. NFR thresholds — performance, security (highest technical risk)
4. Edge cases — boundary conditions, error recovery
5. Compatibility — platform/browser variations

### 3. Regression Testing

1. Run full project test suite using commands from `long-task-guide.md`

2. Verify ALL tests pass — zero failures, zero errors
3. Verify line and branch coverage thresholds met project-wide
4. Check for new warnings, deprecation notices, dependency conflicts
5. Any failure → **STOP** — this is a regression. Diagnose before proceeding.

**Record:** total tests, passed/failed, line/branch coverage vs thresholds.

### 3b. Full Mutation Regression

Run full-codebase mutation testing. Per-feature mutation during Worker cycles may have only scoped feature tests (when active features > `mutation_full_threshold`); this step verifies mutation score holds project-wide with the full test suite.

1. Get the `mutation_full` command from `long-task-guide.md`
2. Run full mutation testing (all source files, all tests)
3. Verify: mutation score >= `quality_gates.mutation_score_min` from `feature-list.json`
4. If surviving mutants found:
   - Analyze: equivalent mutant (document + skip) vs real gap (add test → Major severity defect)
   - If score below threshold → treat as regression defect (Major severity)
5. Record: mutation score, killed/survived/total, command used

See `references/st-recipes.md` section "Full Mutation Regression" for per-tool commands and result interpretation.

**Record:** mutation score vs threshold, surviving mutant count, tool output summary.

### 4. Integration Testing

Test cross-feature interactions. Read `references/st-recipes.md` for language-specific patterns and real-vs-contract test classification.

**Terminology** (see st-recipes.md §1 for details):
- **Contract test** = mock-based, verifies call signatures — supplementary, not sufficient
- **Integration test** = real-service, verifies actual data flow — required per boundary

<HARD-GATE>
Every internal cross-feature boundary MUST have at least one real integration test (real DB, real HTTP, real file system). Contract tests (mocks) do NOT satisfy this gate.

For external third-party boundaries: first ask the user (via `AskUserQuestion`) to provide test credentials or sandbox environment. Only if the user confirms they cannot provide credentials may contract-only tests be used — record the user's confirmation in the ST plan as mock authorization.
</HARD-GATE>

For each pair of features sharing data, state, or API boundaries:
- **Data flow**: Feature A produces data → Feature B consumes it → verify data integrity end-to-end; shared DB/state consistency
- **API contracts**: internal API calls between modules — verify request/response schemas; error propagation; version compatibility
- **Dependency chains**: walk `dependencies[]` graph in `feature-list.json`; verify features work in dependency order; test each dependency edge

**Classification table** (include in ST plan):

| Boundary | Features | Type | Real Tests | Contract Tests | Mock Authorization | Status |
|----------|----------|------|-----------|----------------|-------------------|--------|
| shared DB | F1 → F3 | Internal | 2 | 1 | N/A | PASS |
| REST API | F2 → F4 | Internal | 1 | 0 | N/A | PASS |
| GitHub API | F5 → ext | External | 1 | 0 | N/A (user provided token) | PASS |
| Stripe API | F7 → ext | External | 0 | 2 | User confirmed no sandbox | PASS |

**Minimum per internal boundary:**
- ≥1 real test that writes/reads through the real shared resource
- If real service cannot start: boundary is **BLOCKED** (not skipped) — diagnose via env-guide.md

**External boundary protocol:**
1. Use `AskUserQuestion` to ask user for test credentials/sandbox environment
2. If user provides → write real integration tests (preferred)
3. If user confirms cannot provide → use contract tests; record in Mock Authorization column
4. Never assume mock is acceptable without asking user first

Write integration tests in `tests/integration/` or `tests/st/`. Tag each test:
```python
# Integration: Feature A → Feature B (shared DB) [Real]
def test_feature_a_data_consumed_by_feature_b():
    ...

# Contract: Feature C → External API [Contract]
def test_external_api_response_shape():
    ...
```

Run and record results per boundary.

### 4b. Full-Pipeline Smoke Test

Before E2E scenario testing, verify at least one complete data flow path through the entire system. This catches integration bugs that per-boundary tests miss.

<HARD-GATE>
At least ONE smoke test must exercise a real end-to-end data path (input → processing → storage → retrieval → output) using only real services. No mocks.
</HARD-GATE>

1. Identify the **critical path** — the single most important data flow through the system (e.g., "create entity → store → query → return")
2. Write one smoke test that:
   - Starts from external input (API call, CLI command, UI action)
   - Passes through all intermediate processing
   - Persists to real storage (if applicable)
   - Retrieves and verifies the persisted result
   - Uses ONLY real services — no mocks
3. Run the smoke test against running services (started in Step 1)
4. If it fails → **Critical** severity defect — diagnose before proceeding to E2E

**Scaling:**
| Project Size | Smoke Tests |
|---|---|
| Tiny (1-5 features) | 1 critical path |
| Small (5-15) | 1-2 critical paths |
| Medium (15-50) | 2-3 critical paths |
| Large (50+) | 3-5 critical paths covering major subsystems |

**Record:** smoke test description, real services used, pass/fail, execution evidence.

### 5. Cross-Feature E2E Scenario Testing

Test complete user workflows that **span multiple features** from SRS acceptance criteria. Single-feature scenarios are already covered by per-feature ST test cases.

For each user persona in SRS Stakeholders:
- Extract primary workflows that **cross feature boundaries**
- Create E2E scenarios spanning multiple features (happy path + error recovery)
- For each scenario: set up initial state → execute workflow → verify intermediate AND final states → clean up

For each scenario: set up initial state, execute step-by-step, verify intermediate states AND final outcome, clean up.

**UI E2E Testing** (only if `"ui": true` features exist): Use Chrome DevTools MCP tools — `navigate_page`, `take_snapshot`, `click`/`fill`/`press_key`, `take_screenshot`, `list_console_messages`, `list_network_requests`.

Write E2E tests in `tests/e2e/` or `tests/st/`. Run and record results.

### 6. System-Wide NFR Verification

Per-feature NFR checks were handled in feature-level ST. This step focuses on **system-wide aggregate** NFR measurement. For each NFR-xxx in SRS, verify with **measured evidence** — not estimates.

- **Performance**: measure p50/p95/p99 under expected load; throughput; memory/CPU/disk I/O. See `references/st-recipes.md` for benchmarking tools. Record: measured value vs SRS threshold.
- **Security**: input validation audit (SQL, XSS, command injection, path traversal); auth/session/privilege escalation; dependency vulnerability scan (npm audit, pip-audit, etc.); OWASP Top 10 checklist; secrets in code/logs. Record: per-check PASS/FAIL with evidence.
- **Scalability** (if load targets in SRS): run load tests at 1x, 2x, 5x expected load; measure degradation curve; identify bottlenecks.
- **Reliability**: error handling produces meaningful messages; graceful degradation when dependencies unavailable; no data corruption under error conditions.

### 7. Compatibility Testing

Skip if SRS does not specify platform/browser/runtime targets.

- **Cross-browser** (UI only): run E2E scenarios in each target browser; verify visual consistency via screenshots; check browser-specific console errors
- **Cross-platform**: build/install/run full test suite on each target OS; verify platform-specific behavior (file paths, line endings, permissions)
- **Runtime versions**: run full test suite for each target runtime version; verify no version-specific API issues

Record: per-platform/browser PASS/FAIL matrix.

### 8. Exploratory Testing

Charter-based, time-boxed sessions to find issues that scripted tests miss.

Create one charter per major feature area:
```
Charter: Explore [feature area]
         with [technique: stress/edge/abuse/workflow variation]
         to discover [bugs/usability issues/undocumented behavior]
```

For each charter: time-box 15-30 minutes; follow intuition — try unexpected inputs, unusual sequences, rapid interactions; log observations in real-time (Bug / Question / Note with severity).

After all charters: consolidate findings; cross-reference with RTM for requirement gaps; add new defects to triage queue.

### 9. Defect Triage

If ANY defects were found in Steps 3-8:

| Severity | Definition | Action |
|----------|-----------|--------|
| **Critical** | System crash, data loss, security breach | BLOCK release — fix immediately |
| **Major** | Core workflow broken, NFR threshold failed | BLOCK release — fix before release |
| **Minor** | Non-core affected, workaround exists | Document — fix now or defer (decide with user) |
| **Cosmetic** | Visual/text issue, no functional impact | Document — defer to next release |

**Escape analysis** — for each defect, classify where it should have been caught:

| Escaped From | Meaning | Systemic Action |
|---|---|---|
| Unit | TDD should have caught this | Add unit test; review coverage for similar gaps |
| Feature-ST | Per-feature acceptance testing gap | Add test case via increment skill |
| Mock-Leaked | Mock test passed but real integration fails | Replace mock with real integration test |
| Integration | Cross-feature boundary not tested | Add integration test for boundary |
| Spec | Requirement ambiguous or missing | Clarify SRS via increment skill |

Include the "Escaped From" column in the defect table:

| # | Severity | Escaped From | Category | Description | Status | Fix Ref |
|---|----------|-------------|----------|-------------|--------|---------|

**Fix loop** (if Critical/Major defects exist):
1. Mark affected features `"status": "failing"` in `feature-list.json`; document in `task-progress.md`
2. Invoke `long-task:long-task-work` to fix
3. After fixes: re-run affected ST test categories (not full ST)
4. Return to triage — repeat until no Critical/Major remain

For Minor/Cosmetic deferrals: document in ST report with severity, description, workaround.

### 10. ST Report

Before writing, verify: every SRS requirement appears in RTM; every NFR has a measured value meeting the threshold; every applicable category has results; all defects are classified.

Generate `docs/plans/YYYY-MM-DD-st-report.md` with these sections:
1. **Executive Summary** — 1-3 sentences: overall quality assessment and release recommendation
2. **Requirements Traceability Matrix** — full RTM table with Feature ST status, System ST category, ATS categories, result, evidence; coverage count (X/Y requirements, Z%); list any gaps; include ATS compliance check result (`check_ats_coverage.py --strict` output)
3. **Test Execution Summary** — table: category, tests run, passed, failed, skipped, notes (one row per category from Step 2a); include a final row **Real Test Cases** — aggregate `Real` test case counts (total / passed / failed) from all feature ST documents (`docs/test-cases/feature-*.md` Real Test Case Execution Summary tables)
4. **Defect Summary** — table: severity, **escaped from**, category, description, status (fixed/deferred), fix reference; totals; open Critical/Major count (must be 0 for Go); if ≥2 defects share the same "Escaped From" source, flag as systemic gap in Risk Assessment
5. **Quality Metrics** — line/branch coverage vs thresholds, **full mutation score** vs threshold (from Step 3b), total test count; real test cases: total / passed / failed (aggregated from all `docs/test-cases/feature-*.md` Real Test Case Execution Summary tables)
6. **Risk Assessment** — residual risks with likelihood, impact, mitigation
7. **Recommendations** — post-release monitoring, known limitations, suggested improvements

### 11. Persist

- Git commit ST artifacts (`docs/plans/*-st-plan.md`, `docs/plans/*-st-report.md`, test files)
- Validate: `python scripts/validate_features.py feature-list.json`
- **Cleanup (MANDATORY)**: Stop services started in Step 1
  - Read `env-guide.md` "Stop All Services" section — kill by PID (from `task-progress.md`, preferred) or by port (fallback)
  - If the stop command fails: try port-based fallback; once a working command is confirmed, **update `env-guide.md`** Stop command; if >2 steps are needed, extract to `scripts/svc-<slug>-stop.sh` and reference from env-guide.md
  - Run `env-guide.md` "Verify Services Stopped" commands — ports must not respond
  - **Record cleanup result**: Note cleanup status in `task-progress.md`

### 12.5 Retrospective Report (Conditional)

```bash
python scripts/check_retrospective_readiness.py
```

If exit 0 (records found) AND `retro_authorized` is `true` in `feature-list.json`:
- Invoke `long-task:long-task-retrospective`
- Wait for completion before proceeding to Verdict

If exit 1 (no records) OR `retro_authorized` is absent/false → skip to Verdict.

### 12. Verdict

Present the ST report summary and Go/No-Go recommendation to the user via `AskUserQuestion`:
- **Go**: All exit criteria met, no open Critical/Major defects, RTM 100% covered
- **Conditional-Go**: Minor/Cosmetic defects deferred, all critical paths verified
- **No-Go**: Open Critical/Major defects, NFR thresholds not met, or RTM gaps

### 13. Finalize (on Go/Conditional-Go)

If verdict is Go or Conditional-Go:
- Invoke `long-task:long-task-finalize`
- Wait for completion before ending session

If No-Go → skip (loop back to Worker for fixes; Finalize runs after eventual Go).

## Scaling ST to Project Size

| Project Size | Features | ST Depth |
|---|---|---|
| Tiny (1-5) | 1-5 features | Regression + lightweight integration + 1 smoke test + 2-3 E2E scenarios + 1-2 exploratory charters |
| Small (5-15) | 5-15 features | Full regression + integration per shared boundary + 1-2 smoke tests + E2E per persona + NFR spot-checks + 3-5 charters |
| Medium (15-50) | 15-50 features | Full regression + systematic integration + 2-3 smoke tests + comprehensive E2E + full NFR + compatibility matrix + 5-10 charters |
| Large (50+) | 50+ features | Full regression + integration test suite + 3-5 smoke tests + E2E automation + full NFR load testing + full compatibility + security audit + 10+ charters |

## Critical Rules

- **Readiness gate first** — never start ST with failing features
- **Evidence-based verdicts** — every PASS must have measured evidence; "it looks OK" is not evidence
- **RTM completeness** — every SRS requirement must appear in the RTM; gaps are findings
- **NFR thresholds are hard gates** — measured value must meet SRS threshold, not "close enough"
- **Defect severity is non-negotiable** — Critical/Major defects block release; no exceptions
- **ALL bugs must be fixed** — Any bug found in ST testing (frontend, backend, integration) MUST be fixed before release. There is no "not my code" exemption.
- **Re-test after fix** — never assume a fix works; re-run affected test categories
- **Real test cases must pass** — any failed `Real` test case in the ST report's Real Test Cases row is an unresolved defect that blocks a Go verdict
- **Exploratory testing is mandatory** — scripted tests cannot find everything
- **ST report before verdict** — document first, then decide; never skip the report
- **No new features during ST** — ST tests the integrated system as-is
- **ATS categories are binding** — if ATS exists, `check_ats_coverage.py --strict` must exit 0; every required category must have test coverage
- **Real integration tests required per boundary** — internal boundaries need ≥1 real test; external boundaries need user confirmation before mock is allowed
- **Full-pipeline smoke test mandatory** — at least one real end-to-end data path must be verified before E2E scenarios
- **Defect escape analysis required** — every defect must be classified by "Escaped From" source to identify systemic testing gaps

## Integration

**Called by:** `using-long-task` (when feature-list.json exists AND all features passing), or `long-task-work` (Step 12 when no failing features remain)
**Reads:** `feature-list.json`, `docs/plans/*-srs.md`, `docs/plans/*-design.md`, `docs/plans/*-ucd.md` (if UI), `docs/test-cases/feature-*.md` (per-feature ST from `long-task-feature-st`), `task-progress.md`, project config file (if applicable)
**May invoke:** `long-task:long-task-work` (if Critical/Major defects found → fix loop), `long-task:long-task-finalize` (after Go/Conditional-Go verdict)
**Produces:** `docs/plans/YYYY-MM-DD-st-plan.md`, `docs/plans/YYYY-MM-DD-st-report.md`
**Read on-demand (via Read tool, NOT Skill tool):** `references/st-recipes.md`
