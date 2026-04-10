# Quality Gates — SubAgent Execution Reference

You are a Quality Gates execution SubAgent. Follow these rules exactly. When finished, return your result using the **Structured Return Contract** at the bottom of this document.

---

# Quality Gates & Verification

Three sequential gates that MUST pass before a feature can be marked "passing". No shortcuts, no exceptions.

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
| Skip re-verification at session start | Always re-verify passing features |

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
