---
name: long-task-static-review
description: "Use for pre-push static analysis — auto-detect and fix Checkstyle (Java) violations until zero remain"
---

# Pre-Push Static Analysis Review

Auto-detect static analysis tool configuration, iteratively scan and fix violations until zero remain, with quality gates per iteration to prevent regressions.

**Announce at start:** "I'm using the long-task-static-review skill to run static analysis and fix all violations to zero."

## Sole Objective

**Static analysis violations → 0.** Detect tool, scan, fix, verify quality, repeat until clean.

## Invocation

This skill is **standalone** — no pipeline dependency, no `feature-list.json` required. Can be invoked at any time (pre-push, pre-PR, on demand).

Currently supports: **Checkstyle (Java)**. Architecture supports future tool expansion via `references/tool-profiles.md`.

---

## Step 1: Parse Arguments & Announce

Parse user input for optional parameters:

| Parameter | Values | Default |
|-----------|--------|---------|
| `--tool` | `checkstyle` / `all` | `all` (auto-detect all supported tools) |
| `--max-iterations` | integer 1–20 | 10 |
| `--path` | directory path | `.` (project root) |
| `--dry-run` | flag | false (when set, detect only — no fixing) |

Print announcement with selected parameters.

## Step 2: Tool Detection (Read-Only)

Read the tool profiles reference at `{plugin_root}/skills/long-task-static-review/references/tool-profiles.md`. For each tool profile whose `--tool` filter matches, execute its detection sequence.

### 2a: Build Tool Detection

Check for build system files in `--path`:

| File | Build System |
|------|-------------|
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |

If both exist: check both for Checkstyle configuration and use whichever has it. If neither exists: print "No supported build system found." and **stop**.

### 2b: Checkstyle Detection (per tool-profiles.md)

1. **Config file**: Glob for `**/checkstyle*.xml` — check standard locations: `checkstyle.xml`, `config/checkstyle/checkstyle.xml`, `src/main/resources/checkstyle.xml`. Do **NOT** read the config file contents — Checkstyle reads its own config at runtime.
2. **Maven plugin**: Grep `pom.xml` for `maven-checkstyle-plugin`. If found, check for `<checkstyle.version>` property or `<version>` inside the plugin `<dependency>` block.
3. **Gradle plugin**: Grep `build.gradle` / `build.gradle.kts` for `id 'checkstyle'` or `id("checkstyle")` or `apply plugin: 'checkstyle'`. Check for `checkstyle { toolVersion = '...' }`.
4. **Run command**: Maven → `mvn checkstyle:check`; Gradle → `gradle checkstyleMain`.
5. **Multi-module**: Check for `<modules>` in `pom.xml` or `include` in `settings.gradle`. Maven `mvn checkstyle:check` runs recursively by default.

### 2c: Pipeline Integration Check

If `docs/plans/*-design.md` exists and contains a §11.4 section listing Checkstyle with a run command, use that command as authoritative (user-approved in the pipeline). This prevents drift between pipeline and standalone execution.

### 2d: Quality Command Detection

Detect test/coverage/mutation commands for the quality gates in Step 4. Priority order:

1. **`long-task-guide.md`** (if exists in project): read `test`, `coverage`, `mutation_feature`, `mutation_full` commands directly — these are already validated by the pipeline
2. **`feature-list.json`** (if exists): read `tech_stack` for test framework, coverage tool, mutation tool; derive commands per `references/tool-profiles.md`
3. **Build tool convention**: Maven → `mvn test`, `mvn test jacoco:report`; Gradle → `gradle test`, `gradle jacocoTestReport`. For mutation: Maven → `mvn org.pitest:pitest-maven:mutationCoverage`; Gradle → `gradle pitest`
4. **Quality thresholds**: read from `feature-list.json` → `quality_gates` if available; otherwise use defaults: line_coverage_min=90, branch_coverage_min=80, mutation_score_min=80
5. **Unavailable tools**: if no mutation tool is detected in the build config (no pitest plugin, no stryker, etc.), record mutation as "unavailable" — Gate 3 will be skipped with a warning. Same for test framework — if absent, Gate 2 and Gate 3 are both skipped.

### 2e: Detection Summary

Print a summary:

```
## Detected Static Analysis Tools

| Tool | Build System | Config | Version | Run Command |
|------|-------------|--------|---------|-------------|
| Checkstyle | Maven | config/checkstyle/checkstyle.xml | 10.12 | mvn checkstyle:check |

## Quality Gate Commands
| Gate | Command |
|------|---------|
| Compile | mvn compile |
| Test | mvn test |
| Mutation | mvn org.pitest:pitest-maven:mutationCoverage -DtargetClasses=... |
```

If no supported tools detected: print "No static analysis tools detected in this project." and **stop**.

If `--dry-run`: print detection results and **stop** (no fixing).

## Step 3: Baseline Scan

Run the detected tool to establish a violation baseline.

### 3a: Execute

```bash
{run_command} 2>&1 || true
```

The `|| true` prevents the build failure exit code from stopping execution — Checkstyle is expected to fail when violations exist.

### 3b: Parse Violations

Read command output and extract violations. Per tool-profiles.md, Checkstyle formats:

- Maven: `[ERROR] /path/File.java:[line,col]: message [RuleName]`
- Gradle: `build/reports/checkstyle/main.xml` or console `[ant:checkstyle]` lines

For each violation extract: **file path**, **line number**, **column** (if available), **rule name**, **severity**, **message**.

### 3c: Group and Report

Group violations by file, sort by line number within each file. Record baseline:

```
Baseline: N violations in M files
```

If **zero violations**: print "No violations found. Codebase is clean." → skip to Step 6 with zero-iteration summary.

## Step 4: Scan-Fix Loop

**Objective: violations → 0.**

Repeat until zero violations or exit conditions met.

### Per-Iteration Flow

#### 4a: Select Files

Sort files by violation count descending. Select top 5 files (or fewer if less remain). Prioritize files with the most violations for maximum impact per iteration.

#### 4b: Fix Violations

For each selected file:

1. Read the file
2. Apply fixes for each violation, following the fix strategies in `references/tool-profiles.md`:
   - **Safe fixes** (no behavioral risk): Whitespace, Indentation, Imports, Javadoc, Braces, LineLength, ModifierOrder, CodingStyle — apply directly
   - **Low-risk fixes**: Naming, EmptyBlock, ClassDesign, MagicNumber — apply with care, watch for reflection/serialization dependencies
   - **Medium-risk fixes**: MethodLength (extract methods) — apply conservatively
   - **Unfixable**: violations requiring complex refactoring or design decisions → log as "manual review needed" and skip
3. Group related fixes within each file into a single Edit operation

**Constraints:**
- Do **NOT** modify any Checkstyle/tool configuration files — fix code to comply with existing rules
- Only non-behavioral changes: formatting, naming, import order, javadoc, annotation placement, braces, modifiers
- Follow the dominant pattern in each file when fixing (indentation style, naming convention in context)
- Do NOT add new imports or dependencies that did not previously exist (except expanding star imports)

#### 4c: Quality Gates (mandatory, in order)

After fixing files in this iteration, run all 4 gates sequentially. Every gate must pass before proceeding to the next iteration.

**Gate 1 — Compile**

```bash
# Maven (3-stage: sed clean → grep keep → tail cap)
mvn compile -B -q 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|BUILD ' | tail -20

# Gradle
gradle compileJava -q 2>&1 | tail -20
```

If compilation fails: the fix introduced a compile error. Diagnose which fix caused it, revert or correct that fix, and re-run compile. Do not proceed until compile passes.

**Gate 2 — Incremental Unit Tests**

Run only tests affected by the files modified in this iteration:

```bash
# Maven (3-stage: sed clean → grep keep → tail cap)
mvn test -B -q -Dsurefire.redirectTestOutputToFile=true -Dtest={AffectedTest1,AffectedTest2,...} 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<' | tail -30

# Gradle
gradle test --tests "{AffectedTestPattern}" -q 2>&1 | tail -30
```

Determine affected tests by: matching source file name to test file name convention (e.g., `Foo.java` → `FooTest.java`), or running module-scoped tests for the modified module.

If tests fail: diagnose whether the fix changed behavior (naming change broke reflection, import change broke classpath, etc.). Fix the issue — either adjust the source fix or update the test. Re-run until green.

**Gate 3 — Incremental Mutation Testing**

Run mutation testing scoped to the files modified in this iteration:

```bash
# Maven (3-stage: sed clean → grep keep → tail cap; ^>> for PIT summary lines)
mvn org.pitest:pitest-maven:mutationCoverage -B -q -DtargetClasses={changed.package.ClassName,...} 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<|^>>' | tail -30

# Gradle (pitest, scoped)
gradle pitest -DtargetClasses={changed.package.ClassName,...} -q 2>&1 | tail -30

# Or use the mutation_feature command from long-task-guide.md with changed files substituted
```

Mutation score must meet the project threshold (`quality_gates.mutation_score_min`, default 80%). If below threshold: add or strengthen tests for the modified files, then re-run.

**Gate 4 — Checkstyle Re-scan**

```bash
{run_command} 2>&1 || true
```

Parse new violation count. Record:

```
Iteration N: violations_before → violations_after (delta: -X)
  Fixed files: File1.java (5→0), File2.java (3→1), ...
  Quality gates: Compile ✓ | UT ✓ | Mutation ✓ (score%) | Scan ✓
  Remaining: Y violations in Z files
```

#### 4d: Exit Conditions

- **violations_after == 0**: objective achieved → proceed to Step 5
- **iteration >= max_iterations**: cap reached → proceed to Step 5
- **Stuck**: violations_after >= violations_before for **2 consecutive iterations** → the fixes are oscillating or introducing new violations → break and proceed to Step 5

## Step 5: Final Verification

Run full-scope quality verification (not incremental) to confirm overall project health.

### 5a: Full Compile

```bash
mvn compile -B -q 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|BUILD ' | tail -20
```

### 5b: Full Unit Tests

```bash
mvn test -B -q -Dsurefire.redirectTestOutputToFile=true 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<' | tail -30
```

Run the complete test suite, not just affected tests. On FAIL re-run without pipe for full details.

### 5c: Full Mutation Testing

```bash
# Use mutation_full_quiet command from long-task-guide.md, or:
mvn org.pitest:pitest-maven:mutationCoverage -B -q 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<|^>>' | tail -30
```

Full project-scope mutation. Score must meet threshold.

### 5d: Final Checkstyle Scan

```bash
{run_command} 2>&1 || true
```

Confirm final violation count.

### 5e: Residual Classification

If violations remain after the loop, classify each:

| Classification | Description |
|----------------|-------------|
| **Manual review needed** | Requires human judgment — complex refactoring, design decisions, method decomposition |
| **Oscillating** | Fix for rule A introduces violation of rule B and vice versa |
| **New** | Introduced by prior fixes (net negative on that specific rule) |

List each residual violation with its classification.

## Step 6: Summary Report

Print the final summary:

```
## Static Analysis Review Complete

### Summary
| Metric | Value |
|--------|-------|
| Tool | Checkstyle |
| Build System | Maven |
| Checkstyle Version | 10.12 |
| Config | config/checkstyle/checkstyle.xml |
| Initial Violations | 47 |
| Final Violations | 0 |
| Violations Fixed | 47 |
| Iterations | 4 |
| Files Modified | 12 |

### Iteration History
| # | Before | After | Delta | Compile | UT | Mutation | Files |
|---|--------|-------|-------|---------|-----|----------|-------|
| 1 | 47 | 28 | -19 | PASS | PASS | 85% | File1, File2, ... |
| 2 | 28 | 11 | -17 | PASS | PASS | 82% | ... |
| 3 | 11 | 3 | -8 | PASS | PASS | 88% | ... |
| 4 | 3 | 0 | -3 | PASS | PASS | 86% | ... |

### Final Verification
| Gate | Result |
|------|--------|
| Full Compile | PASS |
| Full UT | PASS (N tests) |
| Full Mutation | PASS (score%) |
| Checkstyle | 0 violations |

### Remaining Issues (if any)
| File | Line | Rule | Message | Classification |
|------|------|------|---------|----------------|
| ... | ... | ... | ... | Manual review needed |
```

If `task-progress.md` exists in the project, append a one-line entry:
```
- Static Review: Checkstyle — {violations_fixed} violations fixed in {iterations} iterations ({files_modified} files), quality gates passed
```

---

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| No `pom.xml` or `build.gradle` | Stop: "No supported build system found." |
| Checkstyle not configured in build | Stop: "No static analysis tools detected." |
| Build fails before scan (compilation error) | Diagnose and stop. Do not attempt to fix pre-existing build errors — only style violations. |
| Zero violations on baseline | Stop with clean summary (Step 6, zero iterations). |
| Max iterations reached with violations remaining | Report remaining violations with classification. |
| Stuck (2 consecutive iterations with no progress) | Break early, report remaining as oscillating/unfixable. |
| Multi-module project | Run at project root; violations across all modules tracked together. |
| Design doc §11.4 exists with Checkstyle | Use §11.4 run command as authoritative. |
| `long-task-guide.md` exists | Use its test/coverage/mutation commands for quality gates. |
| No mutation tool configured | Skip Gate 3 (mutation) with warning; other gates still enforced. |
| No test framework detected | Skip Gate 2 (UT) and Gate 3 (mutation) with warning; compile + scan still enforced. |

## Rules

- **Config files are read-only** — never modify Checkstyle config, `pom.xml` plugin config, or Gradle checkstyle block. The skill fixes source code to comply with existing rules.
- **Behavioral preservation** — fixes must not change program behavior. Only formatting, naming, import order, javadoc, annotation placement, brace style, modifier order, and similar non-behavioral changes.
- **Quality gates are non-negotiable** — every iteration must pass compile + UT + mutation before proceeding. No shortcuts, no "probably fine."
- **No new dependencies** — fixes must not add imports or dependencies that did not previously exist (expanding star imports is allowed).
- **Git-safe** — do NOT commit changes. The user reviews and commits after the skill completes.
- **Idempotent** — re-running the skill on an already-clean codebase produces zero-iteration clean summary.
- **Pipeline-compatible** — when used alongside the long-task pipeline, respects Design §11.4 and `long-task-guide.md` as authoritative sources for commands and thresholds.

## Integration

**Called by:** User on-demand (standalone)
**Requires:** Java project with Checkstyle configured via Maven or Gradle
**Produces:** Source code with zero Checkstyle violations (or classified residuals), all quality gates passing
**Does NOT chain to:** Any pipeline skill — fully independent
