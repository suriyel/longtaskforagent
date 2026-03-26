# Quality Gates — SubAgent Execution Reference

You are a Quality Gates execution SubAgent. Follow these rules exactly. When finished, return your result using the **Structured Return Contract** at the bottom of this document.

---

# Quality Gates & Verification

Four sequential gates that MUST pass before a feature can be marked "passing". No shortcuts, no exceptions.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.


**On tool/environment errors**:
1. **Read** error output — identify the specific tool or environment issue
2. **Diagnose** root cause (tool not installed, env not activated, wrong path, missing config)
3. **Attempt fix** — run `init.sh` if needed, or install the missing tool
4. **Re-run** once
5. **If still fails** → set Verdict to BLOCKED with error details
6. **NEVER skip** — testing is a hard gate; no bypass allowed

## Gate 0: Real Test Verification

Gate 0 runs BEFORE coverage. Coverage numbers are meaningless when the test suite is all-mock.

### Step 1: Run verification script

```bash
python scripts/check_real_tests.py feature-list.json --feature {current_feature_id} --require-for-deps
```

The `--require-for-deps` flag cross-checks the feature's `required_configs[]` for connection-string keys (URL, HOST, PORT, etc.). If found, real tests are **mandatory** — pure-function exemption is blocked.

Read script output:
- **FAIL** (no real tests) → GATE 0 FAIL, return to TDD Red to write real tests
- **FAIL** with "has external dependencies" → see Step 1b below
- **WARN** (mock warnings found) → proceed to Step 2
- **PASS** (real tests found, no mock warnings) → proceed to Step 3

### Step 1b: Dependency-blocked FAIL handling

If Gate 0 FAIL reason includes "has external dependencies but no real tests":
1. This is NOT a code problem — it's an infrastructure/config problem
2. Run: `python scripts/check_configs.py feature-list.json --feature {current_feature_id}`
3. If configs are missing → set Verdict to **BLOCKED** with message: "Feature #{id} requires external dependencies ({config_names}) but configs are not provided. Use AskUserQuestion to request the user to provide the missing configs."
4. If configs exist but services aren't running → read `env-guide.md`, start services, re-run Gate 0
5. NEVER proceed without real tests for features with external dependencies
6. NEVER claim pure-function exemption for features that have connection-string `required_configs[]`

### Step 2: LLM sampling review (WARN only)

For each mock warning flagged by the script:
1. Read the corresponding real test function body
2. Determine: is the mock targeting the **primary dependency** this real test claims to verify?
   - Yes → real test is invalid; rewrite, re-run script
   - No (mock is on an unrelated auxiliary service) → mark as legitimate, proceed

### Step 3: Run real tests (with skip detection)

Execute real tests in isolation using the run command declared in `long-task-guide.md` Real Test Convention section:
- All real tests MUST PASS
- Any FAIL → GATE 0 FAIL, fix and re-run
- **Skip detection (mandatory)**: Read the full test runner output. If ANY real test is reported as `skipped`, `pending`, `disabled`, or `ignored` — treat it as a GATE 0 FAIL. Real tests must execute, not skip.
  - Common skip indicators: pytest `s` marker or "skipped" count > 0; JUnit `@Disabled`; Jest/Vitest "skipped"/"pending" count > 0; gtest "DISABLED_" prefix
  - If skip is caused by missing infrastructure → service/DB is not running. Read `env-guide.md`, start the service, re-run.
  - If skip is caused by an environment guard (`if not env: return`) → rewrite the test to assert-fail instead (Anti-Pattern #16). Real tests must fail loudly, not silently pass.

### Evidence required
```
Gate 0 Result:
- Script output: [paste check_real_tests.py output]
- Mock warning review: [for each warning — primary dep / auxiliary service]
- Real test execution: passed N / failed N / skipped N
- Skip verdict: 0 skipped (or: N skipped → FAIL, reason and fix applied)
- Gate 0: PASS/FAIL
```

### On Gate 0 FAIL
```
GATE 0 FAIL — [reason]
Required action:
1. [Fix missing real tests / rewrite mock-using real tests / set up test infrastructure]
2. Re-run TDD Red verification (real tests must FAIL first, then PASS after Green)
3. Return to Gate 0
Do NOT skip Gate 0 and proceed to coverage.
```

## Gate 1: Coverage

After TDD Green (all tests pass), run the coverage tool.

1. **Run** the coverage tool (activate env per `long-task-guide.md`)
2. **Read** the output — verify line%/branch% numbers are visible
3. **Verify**: line coverage >= `[thresholds] line_coverage`, branch coverage >= `[thresholds] branch_coverage`
4. **If FAIL**: identify uncovered lines/branches from the output → add tests → re-run TDD cycle for those paths
5. **If PASS**: proceed to Mutation Gate

**Evidence required:**
```
- Coverage summary showing line % and branch %
- Line coverage >= threshold
- Branch coverage >= threshold
- List of uncovered lines (if any, with justification)
```

## Gate 2: Mutation Testing

After TDD Refactor, run mutation testing scoped to this feature.

### Scope Decision

Check `quality_gates.mutation_full_threshold` (default 100) against total active (non-deprecated) features in `feature-list.json`:
- If active features ≤ threshold → use `mutation_full` command (small project — full suite is fast enough)
- If active features > threshold → use `mutation_feature` command (large project — scope to feature's tests)

### Running mutation_feature (large project)

1. **Identify** changed source files for this feature (from git diff or TDD artifacts)
2. **Identify** test files written/modified during TDD for this feature
3. **Run** the `mutation_feature` command from `long-task-guide.md`, filling placeholders:
   - `{changed_files}` → changed source file paths
   - `{test_files}` → feature's test file paths (or test pattern/marker)
   - Other tool-specific placeholders as needed per tech stack (see `coverage-recipes.md` Per-Feature Mutation Test Scoping section)
4. **Read** the output, **verify** mutation score >= `[thresholds] mutation_score`.

### Running mutation_full (small project)

1. **Run** the `mutation_full` command from `long-task-guide.md` (no placeholders needed)
2. **Read** the output, **verify** mutation score >= `[thresholds] mutation_score`.

### Common steps (both modes)

- **If surviving mutants**, analyze each:
  - **Equivalent mutant** (code change has no observable effect) → document and skip
  - **Real gap** (test doesn't catch the mutation) → add/strengthen test, re-run
  - **Unreachable code** → remove dead code
- **If PASS** → proceed to Verify & Mark

**Evidence required:**
```
- Mutation summary showing killed/survived/total
- Mutation score >= threshold
- Scope: feature-scoped | full (state which mode was used and why)
- List of surviving mutants (if any, with justification or fix)
```

**Mutation Scope by Phase:**
| Phase | Mode | Mutated Files | Tests Run |
|-------|------|---------------|-----------|
| Per feature (Gate 2, large project) | `mutation_feature` | Changed source files | Feature's tests only |
| Per feature (Gate 2, small project) | `mutation_full` | All source files | Full test suite |
| System Testing (ST Step 3b) | `mutation_full` | All source files | Full test suite |

## Gate 3: Verify & Mark

The final gate before marking a feature as "passing".

```

1. IDENTIFY → Get test, coverage, and mutation commands from `long-task-guide.md` (use the same mutation mode as Gate 2 — `mutation_feature` or `mutation_full` based on the threshold decision)


2. RUN → Execute each command (fresh, in this message — not cached from earlier)

3. READ → Output for each command:
   - Check exit codes (PASS/FAIL)
   - Count test pass/fail/skip from output
   - Read coverage percentages from output
   - Read mutation score from output

4. VERIFY → Does ALL output confirm the claim?
   - All tests pass (0 failures)?
   - Coverage >= thresholds?
   - Mutation >= threshold?

5. THEN CLAIM → Only now:
   - Report results with evidence

If ANY step fails → STOP. Do NOT claim passing. Fix the issue first.
```

## Red Flag Words

If you catch yourself using any of these, STOP and re-verify:

| Red Flag | Required Action |
|----------|----------------|
| "should pass" | Run the tests NOW |
| "probably works" | Execute and verify NOW |
| "seems to be working" | Get concrete test output |
| "I believe this is correct" | Run verification command |
| "this looks good" | Run automated tests |
| "based on the implementation" | Tests verify behavior, not code |
| "the tests should be green" | Run tests and read output |
| "I've verified" (no output shown) | Show the actual output |
| "coverage is probably fine" | Run coverage tool NOW |
| "mutation score should be high enough" | Run mutation tests NOW |

## Tool Setup

If coverage or mutation tools are not yet configured for this project's tech stack, read `skills/long-task-quality/coverage-recipes.md` for full setup instructions per language (Python, Java, JavaScript, TypeScript, C, C++).

## Verification Timing Summary

| Event | What to verify |
|-------|---------------|
| After TDD Green + Refactor | `check_real_tests.py` output PASS, all real tests passing |
| After TDD Green | Full test suite output |
| After Coverage Gate | Coverage report (line% + branch%) |
| After TDD Refactor | Full test suite (still passing) |
| After Mutation Gate | Mutation report (score%) |
| Before marking "passing" | ALL of the above + SRS acceptance criteria (via srs_trace) |
| Before git commit | Full test suite (no broken code committed) |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Mark "passing" after writing code without running tests | Run tests, read output, then mark |
| Trust that refactoring didn't break anything | Re-run full suite after every refactor |
| Read only the summary line of test output | Read complete output |
| Run mutation on uncovered code | Pass coverage gate FIRST; mutation on uncovered code is wasteful |
| Skip re-verification at session start | Always smoke-test passing features |
| Skip Gate 0 because "coverage will catch mock issues" | Coverage is blind to mock vs. real. Gate 0 runs first, always. |
| Script reports WARN but proceed without reviewing | Must review each mock warning to determine if it targets the primary dependency. |

---

## Structured Return Contract

When all gates are complete (or if blocked), return your result in EXACTLY this format:

```markdown
## SubAgent Result: Quality Gates
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-3 sentences — what gates were run, key outcomes]
### Artifacts
- [any files created or modified during gate execution]
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Gate 0 (Real Test) | PASS/FAIL | PASS | PASS/FAIL |
| Line Coverage | N% | ≥X% | PASS/FAIL |
| Branch Coverage | N% | ≥X% | PASS/FAIL |
| Mutation Score | N% | ≥X% | PASS/FAIL |
### Risks
<!-- Output even on PASS. Omit this section only if the list is empty. -->
| # | Category | Location | Description |
|---|----------|----------|-------------|
| 1 | Mutant \| Coverage \| Dependency | file:line or metric name | [one-sentence explanation] |

<!-- Category rules:
  Mutant   — surviving mutants judged equivalent or known gap (file:line + reason)
  Coverage — any metric within +5% of its threshold, or known uncovered boundary
  Dependency — third-party library with a known security patch or breaking change not yet applied -->
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
| 1 | Critical/Major/Minor | [what failed, what was attempted] |
### Next Step Inputs
- coverage_line: [actual line coverage %]
- coverage_branch: [actual branch coverage %]
- mutation_score: [actual mutation score %]
- all_tests_pass: true/false
- test_count: [total test count]
```

**IMPORTANT**: Do NOT mark the feature as "passing" in feature-list.json — that is the orchestrator's responsibility. Only report the results.
