---
name: long-task-mutation-retrofit
description: "Retrofit mutation testing for existing/legacy codebases until mutation score threshold is met — standalone, no pipeline dependency. Supports incremental mode via --branch."
---

# Mutation Retrofit — 变异测试补全

为存量/遗留代码补充变异测试，迭代度量->修复->验证，直至变异分数达标。

**Announce at start:** "I'm using the long-task-mutation-retrofit skill to strengthen tests until mutation score threshold is met."

## Sole Objective

**Mutation Score -> threshold.** Detect tools, measure, kill surviving mutants, verify, repeat.

## Invocation

**Standalone** — no pipeline dependency, no `feature-list.json` / `long-task-guide.md` required. Can be invoked at any time.

User provides environment info directly in query (language, test commands, mutation commands, etc.). Skill uses what user provides; auto-detects the rest.

---

## Step 1: Parse Arguments & User Context

| Parameter | Values | Default |
|-----------|--------|---------|
| `--path` | directory path | `.` |
| `--files` | comma-separated source file list | empty (all) |
| `--branch` | branch name for incremental mode | empty (full scan) |
| `--max-iterations` | integer 1-20 | 20 |
| `--mutation` | integer 0-100 | 80 |
| `--skip-coverage-check` | flag | false |
| `--dry-run` | flag | false |

Extract from user query any explicitly stated: language, test command, mutation command, test directory, etc. These take priority over auto-detection.

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

If the user explicitly stated language, test command, mutation command, etc. in their query, use those directly. Skip auto-detection for provided items.

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

**Coverage tool** (for prerequisite check): Grep for `pytest-cov`/`coverage`, `jacoco`, `c8`/`nyc`/`istanbul`, `gcov`/`lcov`.

**Mutation tool**: Grep for `mutmut`, `pitest`, `stryker`, `mull`.

**Command derivation**: Map detected tool names to command templates (see `coverage-recipes.md` for full per-language reference).

**Missing mutation tool**: If mutation tool absent, read `{skill_dir}/references/coverage-recipes.md` for installation recipes. If cannot install: **STOP** — "No mutation tool detected. Install one first." with tool-specific instructions.

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
| Coverage Tool | {tool} (prerequisite check) |
| Mutation Tool | {tool} |
| Test Dir | {dir} |
| Test Pattern | {pattern} |

## Commands
| Purpose | Command |
|---------|---------|
| Test (quiet) | {cmd} |
| Coverage (full) | {cmd} |
| Mutation (full) | {cmd} |

## Thresholds
| Gate | Threshold |
|------|-----------|
| Mutation Score | {mutation}% |
| Coverage Prerequisite | 80% line (bypass with --skip-coverage-check) |
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

| Language | Mapping | Mutation Scope |
|----------|---------|---------------|
| Python | `src/foo/bar.py` -> file path | `--paths-to-mutate=src/foo/bar.py` |
| Java | `src/main/java/com/foo/Bar.java` -> `com.foo` | `-DtargetClasses=com.foo.*` |
| JS/TS | file path directly | `--mutate=src/foo.ts` |

### 4d: Validate

If zero changed files: **STOP** — "No changed files detected vs branch `<branch>`."

Print: `"Incremental mode: {N} changed files from branch {branch}."`

Store `changed_files` for subsequent steps.

## Step 5: Prerequisite + Baseline

### 5a: Test Suite Health

Run test-quiet command. If tests **FAIL**: **STOP** — "Existing tests failing. Fix them before retrofitting."

### 5b: Coverage Prerequisite Check

Unless `--skip-coverage-check` is set:

Run coverage (scoped if incremental). If **line coverage < 80%**: **STOP** — "Coverage too low ({X}%). Run `/coverage-retrofit` first to bring coverage above 80%, or use `--skip-coverage-check` to bypass."

Rationale: Mutation testing on poorly-covered code wastes time — most mutants survive simply because no test exercises the code at all (anti-pattern #13 in testing-anti-patterns.md).

### 5c: Mutation Measurement

Run mutation command (scoped if incremental).

Parse mutation report:
- **Overall**: mutation score %
- **Per-file**: surviving mutants list

Use Output Optimization Protocol:
1. Run quiet mutation -> exit code + summary
2. If metrics unclear -> read report file directly (pitest XML, mutmut results, stryker JSON)

### 5d: Baseline Check

- Mutation score >= threshold: **STOP** — "Threshold already met." Print summary.
- `--dry-run`: print baseline metrics and **STOP**.
- Otherwise: extract **Surviving Mutants**:

```
Surviving Mutants format:  file:line | mutator | description
```

Print: `"Baseline: Mutation {X}%. Surviving mutants: {N} across {M} files."`

## Step 6: Fix Loop

Initialize: `iteration = 0`, `stall_count = 0`

### 6a: Prioritize & Chunk

Rank source files by surviving mutants count descending. If incremental: filter to `changed_files` only. Select **top 3-5 files** as iteration target.

### 6b: Mutation Fix

> **DISPATCH** create independent SubAgent(use General or Agent) — load then execute skill `long-task:long-task-mutation-fix` in the subagent

**Prompt must provide inline context**:

```
You are retrofitting tests for an existing codebase (not a TDD feature cycle).

## Project Context
- Language: {language}
- Test framework: {test_framework}
- Test directory: {test_dir}
- Test command (quiet): {actual_test_quiet_cmd}
- Test command (detail): {actual_test_detail_cmd}

## Surviving Mutants
{mutants in this iteration's target files only}

## Project Conventions (if docs/rules/ exists)
- Read docs/rules/coding-style.md — naming, formatting
- Read docs/rules/coding-constraints.md — library constraints
- Follow these conventions when writing/modifying tests

## Rules
- Read execution rules: skills/long-task-mutation-retrofit/references/iron-law.md
- Read anti-patterns: skills/long-task-mutation-retrofit/references/testing-anti-patterns.md
- Classify: equivalent -> document, real gap -> strengthen test, dead code -> remove
- Run the test command to verify — all tests must pass
- Do NOT run mutation or coverage tools
```

**Parse** SubAgent return:
- Verdict PASS -> proceed to 6c
- Verdict FAIL / BLOCKED -> log, skip iteration, continue

### 6c: Verify All Tests Pass

Run test-quiet command. If FAIL -> run test-detail -> attempt fix (max 2 retries). If still failing -> revert SubAgent's changes for this iteration, log, continue.

### 6d: Re-Measure

Run mutation again (scoped if incremental). Record:

```
Iteration {N}: Mutation {before}->{after}% (+{delta})
  Files: {list}
  Mutants killed: {count}
  Tests strengthened: {count}
```

### 6e: Exit Conditions

| Condition | Action |
|-----------|--------|
| Mutation score >= threshold | **SUCCESS** -> Step 7 |
| `iteration >= max_iterations` | Cap reached -> Step 7 |
| Mutation score improved < 0.5% | `stall_count += 1`; if `stall_count >= 2` -> stuck, break -> Step 7 |
| Otherwise | Reset `stall_count = 0`, `iteration += 1` -> loop to 6a |

## Step 7: Final Verification & Summary

1. Run full test suite (all tests, not scoped)
2. Run full-project mutation — record final metrics

```
## Mutation Retrofit Complete

### Summary
| Metric | Baseline | Final | Threshold | Status |
|--------|----------|-------|-----------|--------|
| Mutation Score | X% | Y% | Z% | PASS/FAIL |
| Mutants Killed | — | N | — | — |
| Equivalent Mutants | — | N | — | — |
| Dead Code Removed | — | N | — | — |
| Tests Strengthened | — | N | — | — |
| Iterations | — | N | N max | — |
| Files Retrofitted | — | N | — | — |

### Mode
{Full scan | Incremental vs <branch> (N changed files)}

### Iteration History
| # | Mutation Score | Mutants Killed | Tests Strengthened | Files |
|---|---------------|----------------|-------------------|-------|
| 1 | X->Y% | N | N | A, B, C |
| ... | | | | |

### Final Verification
| Gate | Result |
|------|--------|
| Full Test Suite | PASS (N tests) |
| Mutation Score | Y% (>= Z%) PASS/FAIL |

### Remaining Mutants (if threshold not fully met)
| File | Surviving | Classification |
|------|-----------|----------------|
| generated/parser.py | 12 | Generated code — skip |
| config/bootstrap.py | 5 | Framework hooks — equivalent mutants documented |
```

If incremental mode, append note: "Incremental mode: only changed files vs `<branch>` were targeted. Run without `--branch` for full-project metrics."

---

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| No test framework detected | STOP with message |
| No mutation tool, cannot install | STOP with BLOCKED + installation instructions from coverage-recipes.md |
| Existing tests fail | STOP — fix first |
| Coverage too low (< 80%) | STOP — run /coverage-retrofit first (or --skip-coverage-check) |
| Already meets threshold | STOP with zero-iteration summary |
| SubAgent fails repeatedly on a file | Skip file, classify as "hard to test", continue |
| Very large codebase (>500 source files) | Chunk to top 3 files per iteration |
| `--branch` + zero changed files | STOP with message |
| `--branch` + `--files` | Intersect: only changed files also in --files list |
| Multi-module project | Run from root; tools handle recursion |

## Rules

- **Only add/strengthen tests or remove dead code** — dead code removal is the sole production code modification allowed
- **All tests must pass** after every iteration
- **Git-safe** — do NOT commit. User reviews and commits.
- **Idempotent** — re-running on a codebase meeting threshold -> zero-iteration summary
- **No pipeline dependency** — does not read feature-list.json or long-task-guide.md

## Integration

**Called by:** User on-demand (standalone)
**Requires:** Source code with test framework + mutation tool (or installable)
**Produces:** Strengthened tests / removed dead code, threshold met (or classified residuals)
**Does NOT chain to:** Any pipeline skill — fully independent
**Reuses (via SubAgent dispatch):**
- `long-task:long-task-mutation-fix` — with inline context override
**References (via symlinks):**
- `coverage-recipes.md` — per-language tool setup
- `iron-law.md` — test quality rules
- `testing-anti-patterns.md` — anti-pattern catalog
