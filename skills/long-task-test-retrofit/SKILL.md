---
name: long-task-test-retrofit
description: "Retrofit tests for existing/legacy codebases until coverage + mutation thresholds are met — standalone, no pipeline dependency"
---

# Test Retrofit — 存量代码 UT 补全

为存量/遗留代码补充单元测试，迭代度量→修复→验证，直至覆盖率+变异测试达标。

**Announce at start:** "I'm using the long-task-test-retrofit skill to add tests to this codebase until coverage and mutation thresholds are met."

## Sole Objective

**Coverage + Mutation → thresholds.** Detect tools, measure, add tests, verify, repeat until met.

## Invocation

This skill is **standalone** — no pipeline dependency, no `feature-list.json` required. Can be invoked at any time.

---

## Step 1: Parse Arguments & Announce

| Parameter | Values | Default |
|-----------|--------|---------|
| `--path` | directory path | `.` (project root) |
| `--files` | comma-separated source file list | empty (all source files in --path) |
| `--max-iterations` | integer 1–20 | 20 |
| `--line-cov` | integer 0–100 | 90 |
| `--branch-cov` | integer 0–100 | 80 |
| `--mutation` | integer 0–100 | 80 |
| `--coverage-only` | flag | false (skip mutation gate) |
| `--dry-run` | flag | false (measure only, no fixing) |

Print announcement with selected parameters.

## Step 2: Environment Detection (Read-Only)

Detect language, build system, test/coverage/mutation commands. Priority order:

### 2a: Pipeline Artifacts (prefer if available)

1. **`long-task-guide.md`** exists → read `[test-quiet]`, `[test-detail]`, `[coverage-quiet]`, `[coverage-feature-quiet]`, `[mutation-full-quiet]`, `[mutation-feature-quiet]` commands and `[thresholds]` directly. These are already validated.
2. **`feature-list.json`** exists → read `tech_stack` + `quality_gates`. Run `python scripts/get_tool_commands.py feature-list.json --json` (path relative to `{plugin_root}`) to derive all commands.

CLI args (`--line-cov`, `--branch-cov`, `--mutation`) override detected thresholds.

### 2b: Auto-Detection (no pipeline artifacts)

If neither `long-task-guide.md` nor `feature-list.json` exists:

**Language**: Count files by extension (`*.py`, `*.java`, `*.js`, `*.ts`, `*.c`, `*.cpp`), excluding `.git/`, `node_modules/`, `venv/`, `dist/`, `build/`, `__pycache__/`. Primary = highest count.

**Build system**:
| File | System |
|------|--------|
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python (pip/poetry) |
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |
| `package.json` | npm/yarn |
| `CMakeLists.txt` / `Makefile` | CMake/Make |

**Test framework**: Grep dependency manifests for `pytest`, `junit`, `jest`, `vitest`, `gtest`, `catch2`.

**Coverage tool**: Grep for `pytest-cov`/`coverage`, `jacoco`, `c8`/`nyc`/`istanbul`, `gcov`/`lcov`.

**Mutation tool**: Grep for `mutmut`, `pitest`, `stryker`, `mull`.

**Command derivation**: Map detected tool names to command templates using the same mappings as `scripts/get_tool_commands.py` (see `coverage-recipes.md` for full per-language reference).

**Missing tools**: If coverage or mutation tools are absent from dependency manifest, read `{plugin_root}/skills/long-task-test-retrofit/references/coverage-recipes.md` and install per its recipes. This is the **only** config modification allowed.

### 2c: Test Convention Detection

Identify test directory and naming pattern:
- Python: `tests/test_*.py` or `test/test_*.py`
- Java: `src/test/java/**/*Test.java`
- JS/TS: `__tests__/*.test.ts`, `*.spec.ts`, `tests/*.test.js`
- C/C++: `tests/*.cpp`, `test/*.c`

### 2d: Detection Summary

Print:

```
## Environment
| Item | Value |
|------|-------|
| Language | Python |
| Build System | pyproject.toml (poetry) |
| Test Framework | pytest |
| Coverage Tool | pytest-cov |
| Mutation Tool | mutmut |
| Test Dir | tests/ |
| Test Pattern | test_*.py |

## Commands
| Purpose | Command |
|---------|---------|
| Test (quiet) | pytest -q --tb=line |
| Coverage (full) | pytest --cov=src --cov-branch --cov-report=term-missing |
| Mutation (full) | mutmut run --paths-to-mutate=src/ |

## Thresholds
| Gate | Threshold |
|------|-----------|
| Line Coverage | 90% |
| Branch Coverage | 80% |
| Mutation Score | 80% |
```

If no test framework detected: **STOP** — "No test framework detected. Install one first."

If `--dry-run`: proceed to Step 3 (baseline measurement) then STOP after printing results.

## Step 3: Baseline Measurement

The orchestrator runs all measurement tools directly — no SubAgent dispatch for measurement.

### 3a: Test Suite Health

Run test-quiet command. If tests **FAIL**: **STOP** — "Existing tests failing. Fix them before retrofitting." The skill does not fix broken existing tests.

### 3b: Coverage Measurement

Run full-project coverage command (or scoped if `--path`/`--files` set — fill `{changed_modules}` placeholder with scope).

Parse coverage report to extract:
- **Overall**: line %, branch %
- **Per-file**: file path → (line %, branch %, uncovered lines, uncovered branches)

Use the Output Optimization Protocol:
1. Run `[coverage-quiet]` → exit code + summary
2. If metrics unclear → run `[coverage-detail]` or read report file directly (JaCoCo CSV, coverage.py XML, etc.)

### 3c: Mutation Measurement (skip if `--coverage-only`)

Run full-project mutation command (`[mutation-full-quiet]` or derived).

Parse mutation report to extract:
- **Overall**: mutation score %
- **Per-file**: surviving mutants list

### 3d: Baseline Check

- If coverage >= thresholds AND (mutation >= threshold OR `--coverage-only`): **STOP** — "Thresholds already met." Print summary.
- If `--dry-run`: print baseline metrics and **STOP**.
- Otherwise: extract **Coverage Gaps** and **Surviving Mutants** in standard format:

```
Coverage Gaps format:  file:line-range | type (line|branch) | description
Surviving Mutants format:  file:line | mutator | description
```

Print baseline:
```
Baseline: Line X%, Branch X%, Mutation X%
Gap files: N files below threshold
```

## Step 4: Fix Loop

Initialize: `iteration = 0`, `stall_count = 0`

### 4a: Prioritize & Chunk

Rank source files by `(uncovered_lines + uncovered_branches)` descending. Select **top 3–5 files** as this iteration's target. Filter Surviving Mutants to only those in target files.

### 4b: Coverage Fix (if coverage below threshold)

> **DISPATCH** independent SubAgent(Task or Agent tool) — load then execute skill `long-task:long-task-coverage-fix`

**Prompt must provide inline context** (the SubAgent's execution reference Step 1 expects feature-list.json — override by providing everything inline):

```
You are retrofitting tests for an existing codebase (not a TDD feature cycle).

## Project Context
- Language: {language}
- Test framework: {test_framework}
- Test directory: {test_dir}
- Test naming: {test_pattern}
- Test command (quiet): {actual_test_quiet_cmd}
- Test command (detail): {actual_test_detail_instruction}

## Coverage Gaps
{gaps for this iteration's target files only}

## Existing Test Files
{list paths to existing test files for target source files, if any}

## Rules
- Read execution rules: skills/long-task-test-retrofit/references/iron-law.md
- Read anti-patterns: skills/long-task-test-retrofit/references/testing-anti-patterns.md
- Write tests to cover the identified gaps
- Follow existing test conventions
- Run the test command to verify — all tests must pass
- Do NOT run coverage or mutation tools
```

**Parse** SubAgent return:
- Verdict PASS → proceed to 4c
- Verdict FAIL / BLOCKED → log, skip this iteration's remaining steps, continue to next iteration

### 4c: Verify All Tests Pass

Run test-quiet command. If FAIL → run test-detail → attempt fix (max 2 retries). If still failing → revert SubAgent's changes for this iteration, log, continue.

### 4d: Mutation Fix (if mutation below threshold and not `--coverage-only`)

> **DISPATCH** independent SubAgent(Task or Agent tool) — load then execute skill `long-task:long-task-mutation-fix`

**Prompt inline context** (same pattern as 4b):

```
You are retrofitting tests for an existing codebase (not a TDD feature cycle).

## Project Context
- Language: {language}
- Test framework: {test_framework}
- Test directory: {test_dir}
- Test command (quiet): {actual_test_quiet_cmd}
- Test command (detail): {actual_test_detail_instruction}

## Surviving Mutants
{mutants in this iteration's target files only}

## Rules
- Read execution rules: skills/long-task-test-retrofit/references/iron-law.md
- Read anti-patterns: skills/long-task-test-retrofit/references/testing-anti-patterns.md
- Classify: equivalent → document, real gap → strengthen test, dead code → remove
- Run the test command to verify — all tests must pass
- Do NOT run mutation or coverage tools
```

**Parse** SubAgent return: same as 4b.

### 4e: Verify All Tests Pass Again

Same as 4c.

### 4f: Re-Measure

Run full coverage + mutation again (Step 3b/3c). Record:

```
Iteration {N}: Line {before}→{after}% (+{delta}), Branch {before}→{after}%, Mutation {before}→{after}%
  Files: {list}
  Tests added: {count}
```

### 4g: Exit Conditions

| Condition | Action |
|-----------|--------|
| Coverage >= thresholds AND mutation >= threshold (or `--coverage-only`) | **SUCCESS** → Step 5 |
| `iteration >= max_iterations` | Cap reached → Step 5 |
| Coverage + mutation both improved < 0.5% | `stall_count += 1`; if `stall_count >= 2` → stuck, break → Step 5 |
| Otherwise | Reset `stall_count = 0`, `iteration += 1` → loop to 4a |

## Step 5: Final Verification

1. Run full test suite (all tests, not scoped)
2. Run full-project coverage — record final metrics
3. Run full-project mutation (unless `--coverage-only`) — record final metrics

## Step 6: Summary Report

```
## Test Retrofit Complete

### Summary
| Metric | Baseline | Final | Threshold | Status |
|--------|----------|-------|-----------|--------|
| Line Coverage | X% | Y% | Z% | PASS/FAIL |
| Branch Coverage | X% | Y% | Z% | PASS/FAIL |
| Mutation Score | X% | Y% | Z% | PASS/FAIL |
| Tests Added | — | N | — | — |
| Iterations | — | N | N max | — |
| Files Retrofitted | — | N | — | — |

### Iteration History
| # | Line Cov | Branch Cov | Mutation | Tests Added | Files |
|---|----------|------------|----------|-------------|-------|
| 1 | X→Y% | X→Y% | X→Y% | N | A, B, C |
| ... | | | | | |

### Final Verification
| Gate | Result |
|------|--------|
| Full Test Suite | PASS (N tests) |
| Line Coverage | Y% (>= Z%) PASS/FAIL |
| Branch Coverage | Y% (>= Z%) PASS/FAIL |
| Mutation Score | Y% (>= Z%) PASS/FAIL |

### Remaining Gaps (if thresholds not fully met)
| File | Line Cov | Branch Cov | Classification |
|------|----------|------------|----------------|
| generated/parser.py | 45% | 30% | Generated code — skip |
| config/bootstrap.py | 60% | 50% | Framework hooks — hard to test |
```

If `task-progress.md` exists, append:
```
- Test Retrofit: {tests_added} tests added in {iterations} iterations, coverage {baseline}→{final}%, mutation {baseline_mut}→{final_mut}%
```

---

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| No test framework detected | STOP with message |
| No coverage tool, cannot install | STOP with BLOCKED + installation instructions from coverage-recipes.md |
| No mutation tool, `--coverage-only` not set | Warn, implicitly set `--coverage-only` |
| Existing tests fail | STOP — fix first |
| Zero coverage (no tests at all) | Valid — first iteration creates initial test files |
| Already meets thresholds | STOP with zero-iteration summary |
| SubAgent fails repeatedly on a file | Skip file, classify as "hard to test", continue |
| Very large codebase (>500 source files) | Chunk to top 3 files per iteration |
| `feature-list.json` exists | Use for commands/thresholds but ignore feature scoping |
| Multi-module project | Run from root; tools handle recursion (Maven, Gradle) |

## Rules

- **Only add/strengthen tests** — never modify production source code (dead code removal by mutation-fix is the sole exception)
- **All tests must pass** after every iteration — no shortcuts
- **Git-safe** — do NOT commit. User reviews and commits.
- **Idempotent** — re-running on a codebase meeting thresholds → zero-iteration summary
- **Pipeline-compatible** — respects `long-task-guide.md` / `feature-list.json` as authoritative when present

## Integration

**Called by:** User on-demand (standalone)
**Requires:** Source code with a test framework (or installable)
**Produces:** Test files covering gaps, thresholds met (or classified residuals)
**Does NOT chain to:** Any pipeline skill — fully independent
**Reuses (via SubAgent dispatch):**
- `long-task:long-task-coverage-fix` — with inline context override
- `long-task:long-task-mutation-fix` — with inline context override
**References (via symlinks):**
- `coverage-recipes.md` — per-language tool setup
- `iron-law.md` — test quality rules
- `testing-anti-patterns.md` — anti-pattern catalog
