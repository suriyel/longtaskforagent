---
name: long-task-mutation-retrofit
description: "为存量/遗留代码补全变异测试，迭代直至变异分数达标——独立运行，无流水线依赖。支持通过 --branch 进行增量模式。"
---

# 变异测试补全 — 变异测试补全

为存量/遗留代码补充变异测试，迭代度量->修复->验证，直至变异分数达标。

**在开始时宣告：** "I'm using the long-task-mutation-retrofit skill to strengthen tests until mutation score threshold is met."

## 唯一目标

**变异分数 -> 达标。** 检测工具、度量、杀灭存活变异体、验证、重复。

## 调用方式

**独立运行** — 无流水线依赖，不需要 `feature-list.json` / `long-task-guide.md`。可随时调用。

用户在查询中直接提供环境信息（语言、测试命令、变异测试命令等）。Skill 优先使用用户提供的信息；其余自动检测。

---

## 第 1 步：解析参数与用户上下文

| 参数 | 取值 | 默认值 |
|------|------|--------|
| `--path` | 目录路径 | `.` |
| `--files` | 逗号分隔的源文件列表 | 空（全部） |
| `--branch` | 增量模式的分支名 | 空（全量扫描） |
| `--max-iterations` | 整数 1-20 | 20 |
| `--mutation` | 整数 0-100 | 80 |
| `--skip-coverage-check` | 标志 | false |
| `--dry-run` | 标志 | false |

从用户查询中提取明确声明的：语言、测试命令、变异测试命令、测试目录等。这些优先于自动检测。

打印包含所选参数的宣告。

## 第 2 步：规则检查

检查项目编码惯例：

```
IF docs/rules/ does not exist OR is empty:
  Count source files (*.py, *.java, *.js, *.ts, *.c, *.cpp) excluding .git/, node_modules/, venv/, dist/, build/
  IF count > 3:
    Invoke Skill("long-task:long-task-codebase-scanner")
    # Produces docs/rules/{coding-style,coding-constraints,build-and-compilation,README}.md
  ELSE:
    Skip (greenfield / tiny project)
IF docs/rules/ exists:
  Read for later use in SubAgent prompts
```

## 第 3 步：环境检测

优先级：**用户提供 > 自动检测**。

### 3a：用户提供的上下文

如果用户在查询中明确声明了语言、测试命令、变异测试命令等，直接使用。对已提供的项跳过自动检测。

### 3b：自动检测（针对用户未提供的项）

**语言**：按扩展名统计文件数（`*.py`、`*.java`、`*.js`、`*.ts`、`*.c`、`*.cpp`），排除 `.git/`、`node_modules/`、`venv/`、`dist/`、`build/`、`__pycache__/`。主语言 = 最高计数。

**构建系统**：
| 文件 | 系统 |
|------|------|
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python (pip/poetry) |
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |
| `package.json` | npm/yarn |
| `CMakeLists.txt` / `Makefile` | CMake/Make |

**测试框架**：在依赖清单中搜索 `pytest`、`junit`、`jest`、`vitest`、`gtest`、`catch2`。

**覆盖率工具**（用于前置检查）：搜索 `pytest-cov`/`coverage`、`jacoco`、`c8`/`nyc`/`istanbul`、`gcov`/`lcov`。

**变异测试工具**：搜索 `mutmut`、`pitest`、`stryker`、`mull`。

**命令推导**：将检测到的工具名映射到命令模板（完整的按语言参考见 `coverage-recipes.md`）。

**缺失变异测试工具**：如果变异测试工具不存在，读取 `{skill_dir}/references/coverage-recipes.md` 获取安装方法。如果无法安装：**停止** — "No mutation tool detected. Install one first." 并附带工具专属说明。

### 3c：测试惯例检测

识别测试目录和命名模式：
- Python：`tests/test_*.py` 或 `test/test_*.py`
- Java：`src/test/java/**/*Test.java`
- JS/TS：`__tests__/*.test.ts`、`*.spec.ts`、`tests/*.test.js`
- C/C++：`tests/*.cpp`、`test/*.c`

### 3d：检测摘要

打印：

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

如果未检测到测试框架：**停止** — "No test framework detected. Install one first."

如果 `--dry-run`：进入第 5 步（基线度量）后打印结果即停止。

## 第 4 步：增量范围界定

**如果未指定 `--branch` 则跳过此步。**

### 4a：获取变更文件

```bash
git diff <branch>...HEAD --diff-filter=ACMRT --name-only -- '*.py' '*.java' '*.js' '*.ts' '*.c' '*.cpp'
```

仅筛选已检测语言的扩展名。

### 4b：与 --files 取交集

如果同时指定了 `--files`：将变更文件与显式文件列表取交集。

### 4c：推导变更模块

| 语言 | 映射 | 变异测试范围 |
|------|------|-------------|
| Python | `src/foo/bar.py` -> 文件路径 | `--paths-to-mutate=src/foo/bar.py` |
| Java | `src/main/java/com/foo/Bar.java` -> `com.foo` | `-DtargetClasses=com.foo.*` |
| JS/TS | 文件路径直接使用 | `--mutate=src/foo.ts` |

### 4d：校验

如果变更文件数为零：**停止** — "No changed files detected vs branch `<branch>`."

打印：`"Incremental mode: {N} changed files from branch {branch}."`

存储 `changed_files` 供后续步骤使用。

## 第 5 步：前置检查 + 基线度量

### 5a：测试套件健康检查

运行 test-quiet 命令。如果测试**失败**：**停止** — "Existing tests failing. Fix them before retrofitting."

### 5b：覆盖率前置检查

除非设置了 `--skip-coverage-check`：

运行覆盖率（增量模式则限定范围）。如果**行覆盖率 < 80%**：**停止** — "Coverage too low ({X}%). Run `/coverage-retrofit` first to bring coverage above 80%, or use `--skip-coverage-check` to bypass."

原因：对覆盖率不足的代码运行变异测试浪费时间——大多数变异体存活仅仅因为没有测试触及该代码（testing-anti-patterns.md 中的反模式 #13）。

### 5c：变异测试度量

运行变异测试命令（增量模式则限定范围）。

解析变异测试报告：
- **总体**：变异分数 %
- **按文件**：存活变异体列表

使用输出优化协议：
1. 运行静默变异测试 -> 退出码 + 摘要
2. 如果指标不清晰 -> 直接读取报告文件（pitest XML、mutmut results、stryker JSON）

### 5d：基线检查

- 变异分数 >= 阈值：**停止** — "Threshold already met." 打印摘要。
- `--dry-run`：打印基线指标后**停止**。
- 否则：提取**存活变异体**：

```
Surviving Mutants format:  file:line | mutator | description
```

打印：`"Baseline: Mutation {X}%. Surviving mutants: {N} across {M} files."`

## 第 6 步：修复循环

初始化：`iteration = 0`、`stall_count = 0`

### 6a：优先级排序与分块

按存活变异体数量降序排列源文件。如果是增量模式：仅筛选 `changed_files`。选择**前 3-5 个文件**作为本轮迭代目标。

### 6b：变异修复

> **分派** 创建独立 SubAgent（使用 General 或 Agent）— 在 SubAgent 中加载并执行 skill `long-task:long-task-mutation-fix`

**提示必须提供内联上下文**：

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

**解析** SubAgent 返回：
- Verdict PASS -> 进入 6c
- Verdict FAIL / BLOCKED -> 记录日志，跳过本轮迭代，继续

### 6c：验证所有测试通过

运行 test-quiet 命令。如果 FAIL -> 运行 test-detail -> 尝试修复（最多 2 次重试）。如果仍然失败 -> 回滚 SubAgent 本轮的更改，记录日志，继续。

### 6d：重新度量

再次运行变异测试（增量模式则限定范围）。记录：

```
Iteration {N}: Mutation {before}->{after}% (+{delta})
  Files: {list}
  Mutants killed: {count}
  Tests strengthened: {count}
```

### 6e：退出条件

| 条件 | 动作 |
|------|------|
| 变异分数 >= 阈值 | **成功** -> 第 7 步 |
| `iteration >= max_iterations` | 达到上限 -> 第 7 步 |
| 变异分数提升 < 0.5% | `stall_count += 1`；若 `stall_count >= 2` -> 停滞，中断 -> 第 7 步 |
| 其他 | 重置 `stall_count = 0`，`iteration += 1` -> 回到 6a |

## 第 7 步：最终验证与总结

1. 运行完整测试套件（所有测试，非限定范围）
2. 运行全项目变异测试 — 记录最终指标

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

如果是增量模式，追加说明："Incremental mode: only changed files vs `<branch>` were targeted. Run without `--branch` for full-project metrics."

---

## 边界情况

| 条件 | 行为 |
|------|------|
| 未检测到测试框架 | 停止并提示信息 |
| 无变异测试工具且无法安装 | 停止并返回 BLOCKED + coverage-recipes.md 中的安装说明 |
| 现有测试失败 | 停止 — 先修复 |
| 覆盖率过低（< 80%） | 停止 — 先运行 /coverage-retrofit（或使用 --skip-coverage-check） |
| 已达到阈值 | 停止并输出零迭代摘要 |
| SubAgent 对某文件反复失败 | 跳过该文件，归类为"难以测试"，继续 |
| 超大代码库（>500 源文件） | 每轮迭代分块处理前 3 个文件 |
| `--branch` + 零变更文件 | 停止并提示信息 |
| `--branch` + `--files` | 取交集：仅处理同时出现在变更文件和 --files 列表中的文件 |
| 多模块项目 | 从根目录运行；工具自行处理递归 |

## 规则

- **仅添加/增强测试或移除死代码** — 死代码移除是唯一允许的生产代码修改
- 每轮迭代后**所有测试必须通过**
- **Git 安全** — 不要提交。由用户审查并提交。
- **幂等** — 在已达标的代码库上重新运行 -> 零迭代摘要
- **无流水线依赖** — 不读取 feature-list.json 或 long-task-guide.md

## 集成

**调用方：** 用户按需调用（独立运行）
**前置条件：** 具有测试框架 + 变异测试工具（或可安装）的源代码
**产出：** 增强的测试 / 移除的死代码，达到阈值（或已归类的残余项）
**不链接至：** 任何流水线 skill — 完全独立
**复用（通过 SubAgent 分派）：**
- `long-task:long-task-mutation-fix` — 附带内联上下文覆盖
**引用（通过符号链接）：**
- `coverage-recipes.md` — 按语言的工具配置
- `iron-law.md` — 测试质量规则
- `testing-anti-patterns.md` — 反模式目录
