---
name: long-task-coverage-retrofit
description: "Retrofit unit tests for existing/legacy codebases until line + branch coverage thresholds are met — standalone, no pipeline dependency. Supports incremental mode via --branch."
---

# Coverage Retrofit — UT 覆盖率补全

为存量/遗留代码补充单元测试，迭代度量->修复->验证，直至行覆盖率+分支覆盖率达标。

**Announce at start:** "I'm using the long-task-coverage-retrofit skill to add tests until coverage thresholds are met."

## Sole Objective

**Line + Branch Coverage -> thresholds.** Detect tools, measure, add tests, verify, repeat.

## Invocation

**Standalone** — no pipeline dependency, no `feature-list.json` / `long-task-guide.md` required. Can be invoked at any time.

User provides environment info directly in query (language, test commands, coverage commands, test directory, etc.). Skill uses what user provides; auto-detects the rest.

---

## Step 1: Parse Arguments & User Context

| Parameter | Values | Default |
|-----------|--------|---------|
| `--path` | directory path | `.` |
| `--files` | comma-separated source file list | empty (all) |
| `--branch` | branch name for incremental mode | empty (full scan) |
| `--max-iterations` | integer 1-20 | 20 |
| `--line-cov` | integer 0-100 | 90 |
| `--branch-cov` | integer 0-100 | 80 |
| `--dry-run` | flag | false |

Extract from user query any explicitly stated: language, test command, coverage command, test directory, test naming pattern. These take priority over auto-detection.

Print announcement with selected parameters.

## Step 2: Rules Check

Check for project coding conventions:

```
IF docs/rules/ does not exist OR is empty:
  Count source files (*.py, *.java, *.js, *.ts, *.c, *.cpp) excluding .git/, node_modules/, venv/, dist/, build/
  IF count > 3:
    Invoke Skill("long-task:long-task-codebase-scanner")   # standalone mode, no --next-skill
    # Produces docs/rules/{coding-style,coding-constraints,build-and-compilation,README}.md
  ELSE:
    Skip (greenfield / tiny project)
IF docs/rules/ exists:
  Read for later use in SubAgent prompts
```

## Step 3: Environment Detection

Priority: **user-provided > auto-detected**.

### 3a: User-Provided Context

If the user explicitly stated language, test command, coverage command, etc. in their query, use those directly. Skip auto-detection for provided items.

### 3b: Auto-Detection (for items not provided by user)

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

**Command derivation**: Map detected tool names to command templates (see `coverage-recipes.md` for full per-language reference).

**Missing tools**: If coverage tools absent, read `{skill_dir}/references/coverage-recipes.md` and install. This is the **only** config modification allowed.

### 3c: Test Convention Detection

Identify test directory and naming pattern:
- Python: `tests/test_*.py` or `test/test_*.py`
- Java: `src/test/java/**/*Test.java`
- JS/TS: `__tests__/*.test.ts`, `*.spec.ts`, `tests/*.test.js`
- C/C++: `tests/*.cpp`, `test/*.c`

### 3d: Detection Summary

Print:

```
## Environment
| Item | Value |
|------|-------|
| Language | {lang} |
| Build System | {build} |
| Test Framework | {framework} |
| Coverage Tool | {tool} |
| Test Dir | {dir} |
| Test Pattern | {pattern} |

## Commands
| Purpose | Command |
|---------|---------|
| Test (quiet) | {cmd} |
| Coverage (full) | {cmd} |

## Thresholds
| Gate | Threshold |
|------|-----------|
| Line Coverage | {line_cov}% |
| Branch Coverage | {branch_cov}% |
```

If no test framework detected: **STOP** — "No test framework detected. Install one first."

If `--dry-run`: proceed to Step 5 (baseline) then STOP after printing results.

## Step 4: Incremental Scoping

**Skip this step if `--branch` is not specified.**

### 4a: Get Changed Files

```bash
git diff <branch>...HEAD --diff-filter=ACMRT --name-only -- '*.py' '*.java' '*.js' '*.ts' '*.c' '*.cpp'
```

Filter to detected language extensions only.

### 4b: Intersect with --files

If `--files` also specified: intersect changed files with explicit file list.

### 4c: Derive Changed Modules

| Language | Mapping | Coverage Scope |
|----------|---------|---------------|
| Python | `src/foo/bar.py` -> `foo.bar` | `--cov=foo.bar` |
| Java | `src/main/java/com/foo/Bar.java` -> `com.foo` | JaCoCo include filter |
| JS/TS | file path directly | `--include=src/foo.ts` |

### 4d: Validate

If zero changed files: **STOP** — "No changed files detected vs branch `<branch>`."

Print: `"Incremental mode: {N} changed files from branch {branch}."`

Store `changed_files` for subsequent steps.

## Step 5: Baseline Measurement

### 5a: Test Suite Health

Run test-quiet command. If tests **FAIL**: **STOP** — "Existing tests failing. Fix them before retrofitting."

### 5b: Coverage Measurement

Run coverage command. If incremental mode: scope to `changed_files` modules.

Parse coverage report:
- **Overall**: line %, branch %
- **Per-file**: file path -> (line %, branch %, uncovered lines, uncovered branches)

Use Output Optimization Protocol:
1. Run quiet coverage -> exit code + summary
2. If metrics unclear -> read report file directly (JaCoCo CSV, coverage.py XML, etc.)

### 5c: Baseline Check

- Coverage >= thresholds: **STOP** — "Thresholds already met." Print summary.
- `--dry-run`: print baseline metrics and **STOP**.
- Otherwise: extract **Coverage Gaps**:

```
Coverage Gaps format:  file:line-range | type (line|branch) | description
```

Print: `"Baseline: Line {X}%, Branch {X}%. Gap files: {N} below threshold."`

## Step 6: Fix Loop

Initialize: `iteration = 0`, `stall_count = 0`

### 6a: Prioritize & Chunk

Rank source files by `(uncovered_lines + uncovered_branches)` descending. If incremental: filter to `changed_files` only. Select **top 3-5 files** as iteration target.

### 6b: Coverage Fix

> **DISPATCH** create independent SubAgent(use General or Agent) — load then execute skill `long-task:long-task-coverage-fix` in the subagent

**Prompt must provide inline context**:

```
You are retrofitting tests for an existing codebase (not a TDD feature cycle).

## Project Context
- Language: {language}
- Test framework: {test_framework}
- Test directory: {test_dir}
- Test naming: {test_pattern}
- Test command (quiet): {actual_test_quiet_cmd}
- Test command (detail): {actual_test_detail_cmd}

## Coverage Gaps
{gaps for this iteration's target files only}

## Existing Test Files
{list paths to existing test files for target source files, if any}

## Project Conventions (if docs/rules/ exists)
- Read docs/rules/coding-style.md — naming, formatting
- Read docs/rules/coding-constraints.md — library constraints
- Follow these conventions when writing tests

## Rules
- Read execution rules: skills/long-task-coverage-retrofit/references/iron-law.md
- Read anti-patterns: skills/long-task-coverage-retrofit/references/testing-anti-patterns.md
- Write tests to cover the identified gaps
- Follow existing test conventions
- Run the test command to verify — all tests must pass
- Do NOT run coverage tools
```

**Parse** SubAgent return:
- Verdict PASS -> proceed to 6c
- Verdict FAIL / BLOCKED -> log, skip iteration, continue

### 6c: Verify All Tests Pass

Run test-quiet command. If FAIL -> run test-detail -> attempt fix (max 2 retries). If still failing -> revert SubAgent's changes for this iteration, log, continue.

### 6d: Re-Measure

Run coverage again (scoped if incremental). Record:

```
Iteration {N}: Line {before}->{after}% (+{delta}), Branch {before}->{after}%
  Files: {list}
  Tests added: {count}
```

### 6e: Exit Conditions

| Condition | Action |
|-----------|--------|
| Coverage >= thresholds | **SUCCESS** -> Step 7 |
| `iteration >= max_iterations` | Cap reached -> Step 7 |
| Coverage improved < 0.5% | `stall_count += 1`; if `stall_count >= 2` -> stuck, break -> Step 7 |
| Otherwise | Reset `stall_count = 0`, `iteration += 1` -> loop to 6a |

## Step 7: Final Verification & Summary

1. Run full test suite (all tests, not scoped)
2. Run full-project coverage — record final metrics

```
## Coverage Retrofit Complete

### Summary
| Metric | Baseline | Final | Threshold | Status |
|--------|----------|-------|-----------|--------|
| Line Coverage | X% | Y% | Z% | PASS/FAIL |
| Branch Coverage | X% | Y% | Z% | PASS/FAIL |
| Tests Added | — | N | — | — |
| Iterations | — | N | N max | — |
| Files Retrofitted | — | N | — | — |

### Mode
{Full scan | Incremental vs <branch> (N changed files)}

### Iteration History
| # | Line Cov | Branch Cov | Tests Added | Files |
|---|----------|------------|-------------|-------|
| 1 | X->Y% | X->Y% | N | A, B, C |
| ... | | | | |

### Final Verification
| Gate | Result |
|------|--------|
| Full Test Suite | PASS (N tests) |
| Line Coverage | Y% (>= Z%) PASS/FAIL |
| Branch Coverage | Y% (>= Z%) PASS/FAIL |

### Remaining Gaps (if thresholds not fully met)
| File | Line Cov | Branch Cov | Classification |
|------|----------|------------|----------------|
| generated/parser.py | 45% | 30% | Generated code — skip |
```

If incremental mode, append note: "Incremental mode: only changed files vs `<branch>` were targeted. Run without `--branch` for full-project metrics."

---

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| No test framework detected | STOP with message |
| No coverage tool, cannot install | STOP with BLOCKED + installation instructions from coverage-recipes.md |
| Existing tests fail | STOP — fix first |
| Zero coverage (no tests at all) | Valid — first iteration creates initial test files |
| Already meets thresholds | STOP with zero-iteration summary |
| SubAgent fails repeatedly on a file | Skip file, classify as "hard to test", continue |
| Very large codebase (>500 source files) | Chunk to top 3 files per iteration |
| `--branch` + zero changed files | STOP with message |
| `--branch` + `--files` | Intersect: only changed files also in --files list |
| Multi-module project | Run from root; tools handle recursion |

## Rules

- **Only add/strengthen tests** — never modify production source code
- **All tests must pass** after every iteration
- **Git-safe** — do NOT commit. User reviews and commits.
- **Idempotent** — re-running on a codebase meeting thresholds -> zero-iteration summary
- **No pipeline dependency** — does not read feature-list.json or long-task-guide.md

## Integration

**Called by:** User on-demand (standalone)
**Requires:** Source code with a test framework (or installable)
**Produces:** Test files covering gaps, thresholds met (or classified residuals)
**Does NOT chain to:** Any pipeline skill — fully independent
**Reuses (via SubAgent dispatch):**
- `long-task:long-task-coverage-fix` — with inline context override
**References (via symlinks):**
- `coverage-recipes.md` — per-language tool setup
- `iron-law.md` — test quality rules
- `testing-anti-patterns.md` — anti-pattern catalog
