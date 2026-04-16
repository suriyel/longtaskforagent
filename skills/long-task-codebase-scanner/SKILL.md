---
name: long-task-codebase-scanner
description: "在存量项目（无 docs/rules/）中于需求或设计阶段之前使用 -- 扫描代码库约定（编码风格、约束条件、构建模式、提交格式）"
---

**语言规则**：你必须使用简体中文回复。所有生成的文档、报告和面向用户的输出必须使用中文编写。代码标识符和 JSON 字段名保持英文。

# 代码库约定扫描器

扫描已有项目的源代码，提取并记录已建立的编码约定、库约束、构建模式和提交标准。输出使下游 skill 能够生成符合项目既有模式的代码。

**你的倾向应偏向于发现约束条件。** 尤其是替代标准库或第三方 API 的二方（内部）库强制要求 -- 遗漏这些会导致下游代码不合规。

## 调用方式

由 `using-long-task` 路由器调用（存量项目检测规则 4b/5b 触发时），或用户直接调用（例如代码库变更后重新扫描）。扫描完成后停止，不进行链接 — 调用方负责后续路由。

## 设计原则

- **只读** -- 不修改任何源文件、配置或 git 状态（仅创建 `docs/rules/`）
- **观察而非规定** -- 记录项目当前的做法，而非应该怎么做
- **基于证据** -- 每个约定声明必须引用具体的 `file:line` 示例
- **处理混合约定** -- 如果项目不一致，报告所有模式及其频率百分比
- **遵守 .gitignore** -- 不扫描被忽略的目录
- **输出预算** -- 每个输出文件必须 ≤ 200 行（聚焦于 LLM 可消费的摘要表，而非穷举列表）

## 流程

### 步骤 1：创建输出目录

```bash
mkdir -p docs/rules/
```

### 步骤 2：检测语言、框架与扫描深度

分析文件扩展名和依赖清单（`package.json`、`requirements.txt`、`pom.xml`、`Cargo.toml`、`go.mod`、`*.csproj`）。确定扫描深度：

| 代码行数范围 | 深度 | 每类别文件数 |
|-----------|-------|--------------------|
| < 1,000 | 轻量 | 前 20 个（最近修改） |
| 1,000–10,000 | 标准 | 前 50 个（最近 + 多样化目录） |
| > 10,000 | 深度 | 前 100 个 + 所有配置文件（全覆盖） |

### 步骤 3：样本选取

根据扫描深度（步骤 2）选取有代表性的源文件样本。包含来自不同目录的文件以捕获组织模式。同时包含实现文件和测试文件。

预过滤：排除 `.git/`、`node_modules/`、`venv/`、`dist/`、`build/` 目录。

### 步骤 4：编码风格分析 → `docs/rules/coding-style.md`

分析并记录：

**命名约定** -- 对每个类别，检测主导模式：

| 类别 | 检测内容 |
|----------|---------------|
| Variables | camelCase / snake_case / PascalCase / SCREAMING_SNAKE |
| Functions/Methods | camelCase / snake_case / PascalCase |
| Classes/Types | PascalCase / camelCase |
| Constants | SCREAMING_SNAKE / PascalCase / camelCase |
| Files | kebab-case / snake_case / camelCase / PascalCase |
| Directories | kebab-case / snake_case / singular / plural |
| Private members | underscore prefix / no prefix / # prefix |
| Boolean names | is/has/should 前缀模式 |

对每项：报告主导模式、一致性百分比（多少文件遵循该模式）、2-3 个具体示例。

**格式化** -- 检测：
- 缩进：空格 vs 制表符，缩进宽度（2/4/8）
- 行长度：在采样文件中测量的 P95
- 花括号风格：同行（K&R）vs 换行（Allman）
- 尾逗号、分号、引号风格（JS/TS/Python 特定）
- 函数/方法之间的空行

**格式化器配置** -- 检查配置文件：`.prettierrc`、`.editorconfig`、`.clang-format`、`pyproject.toml [tool.black]`、`rustfmt.toml`、`biome.json`。如发现，引用文件路径 -- 不打开或解析内容（工具在运行时读取自身配置）。

**文件与目录组织** -- 记录：
- 顶层目录结构及用途标注
- 代码组织模式：按功能 / 按层 / 按类型 / 混合
- 测试文件位置：共存 vs 独立 `tests/` 目录
- 测试文件命名：`test_*.py` / `*.test.ts` / `*_test.go` / `*Test.java`

### 步骤 5：编码约束分析 → `docs/rules/coding-constraints.md`

这是**最关键**的输出。聚焦于遗漏后会导致不合规代码的约束条件。

**二方（内部）库检测** -- 扫描 import/require 语句以识别：
- 包装或替代标准库 API 的内部库（例如 `@company/http` 替代 `fetch`；`internal.logger` 替代 `console.log`；自定义 ORM 替代直接数据库查询）
- 检测启发式：来自非公共注册表包的导入（作用域包如 `@company/*`、相对工作区导入、无法映射到已知 npm/PyPI 包的内部模块路径）
- 对每个发现：记录领域、内部库名称、它替代了什么、导入模式、使用频率

**第三方库约束** -- 分析依赖清单：
- 版本锁定策略：精确（`==2.31.0`）vs 范围（`^7.4`）vs 未锁定
- 识别常见领域（HTTP、日志、测试、序列化、日期/时间、校验）所选择的库
- 标记仍在使用的已废弃库

**禁止的 API / 库** -- 检测暗示某些 API 被禁用的模式：
- 从未使用但本应是自然选择的标准库 API（例如任何地方都没有 `console.log`，只有 `logger.info`）
- 存在于锁文件但未被导入的第三方库（被内部替代方案取代）
- 禁止特定 API 的 lint 规则（通过配置文件存在来检测 -- 见下方静态分析工具）

**静态分析工具** -- 检测 linter 和静态分析器的配置文件。对每个发现：
- 记录：工具名称、配置文件路径、运行命令（从构建脚本或标准调用推断）
- **不打开或读取配置文件内容** -- 工具在运行时读取自身配置
- 需检测的常见配置：

| Tool | Config Files | Typical Run Command |
|------|-------------|-------------------|
| ESLint | `.eslintrc*`, `.eslintrc.json`, `eslint.config.*` | `npx eslint .` |
| Prettier | `.prettierrc*` | `npx prettier --check .` |
| Pylint | `.pylintrc`, `pylintrc` | `pylint src/` |
| Flake8 | `.flake8`, `setup.cfg [flake8]` | `flake8 src/` |
| MyPy | `mypy.ini`, `pyproject.toml [tool.mypy]` | `mypy src/` |
| Ruff | `ruff.toml`, `pyproject.toml [tool.ruff]` | `ruff check .` |
| Clippy | `clippy.toml` | `cargo clippy` |
| Checkstyle | `checkstyle.xml` | `mvn checkstyle:check` or `gradle checkstyleMain` |
| Biome | `biome.json` | `npx biome check .` |
| golangci-lint | `.golangci.yml` | `golangci-lint run` |
| SwiftLint | `.swiftlint.yml` | `swiftlint` |
| ktlint | `.editorconfig` | `ktlint` |

**错误处理模式** -- 识别：
- 主导模式：try/catch、Result/Either 类型、错误码、panic/recover
- 自定义 Error/Exception 类（名称、层次结构）
- 集中式错误处理（中间件、全局处理器）
- 错误日志模式

**Import 组织** -- 检测分组顺序：
- 标准库 → 二方 → 三方 → 本地（或其他排序）
- 绝对导入 vs 相对导入
- 组间空行分隔

**注释/文档风格** -- 检测：
- 文档字符串格式：JSDoc、Google 风格、NumPy 风格、Javadoc、Rustdoc
- 使用频率：公共函数中有多少百分比有文档
- 位置：声明上方、内联

**类型注解** -- 检测：
- 严格 vs 可选 vs 无
- TypeScript：`strict`、`strictNullChecks` 等（通过 tsconfig 存在判断）
- Python：类型提示使用频率

**测试约定** -- 检测：
- 测试框架（通过 import 和配置文件 -- 见步骤 6 的测试与质量工具）
- Fixture/setup 模式（共享 fixture、setup/teardown、工厂函数）
- 断言风格（assert、expect、should）-- 附一致性百分比
- Mock 框架（通过 import：unittest.mock、Mockito、jest.fn、vi.fn、gmock）
- 测试分组（describe/it、测试类、平铺函数）
- 测试命名约定：`test_*.py` / `*.test.ts` / `*Test.java` / `*_test.go`
- 测试目录结构：共存 vs 独立 `tests/` / `test/` / `__tests__` / `src/test/java/`

### 步骤 6：构建与编译分析 → `docs/rules/build-and-compilation.md`

**构建系统** -- 识别：
- 构建工具：Makefile、CMake、Gradle、Maven、npm/yarn/pnpm scripts、Cargo、go build、Bazel
- 关键命令：build、test、lint、format、clean（从 scripts/Makefile/package.json 提取）
- 编译标志和目标

**打包** -- 检测：
- 容器：Dockerfile、docker-compose.yml
- 包发布：setup.py、pyproject.toml、npm 发布配置、Cargo.toml
- 分发格式

**Pre-commit 钩子** -- 检测：
- `.pre-commit-config.yaml`、`.husky/`、`lefthook.yml`、`.githooks/`
- 列出已配置的钩子

**环境管理** -- 检测：
- Dockerfile、devcontainer.json、nix、`.tool-versions`、`.node-version`、`.python-version`
- 包管理器：npm/yarn/pnpm/bun（JS）；pip/poetry/pipenv/uv（Python）；go mod；cargo

**代码生成** -- 检测以下目录/配置：
- protobuf、OpenAPI/Swagger、GraphQL codegen、数据库迁移生成器
- **标记生成目录** -- 下游 skill 应将这些排除在约定检查之外

**测试与质量工具** -- 检测测试框架、覆盖率工具和变异测试工具的配置文件。对每个发现：
- 记录：工具名称、类别（test-framework / coverage / mutation）、配置文件路径、运行命令（从构建脚本或标准调用推断）
- **不打开或读取配置文件内容** -- 工具在运行时读取自身配置
- 另外从构建脚本中检测测试运行命令（`package.json "scripts.test"`、Makefile `test:` 目标、`pom.xml` surefire-plugin 等）
- 需检测的常见配置：

| Category | Tool | Config Files | Typical Run Command |
|----------|------|-------------|---------------------|
| Test Framework | pytest | `pyproject.toml [tool.pytest]`, `pytest.ini`, `setup.cfg [tool:pytest]`, `conftest.py` | `pytest` |
| Test Framework | JUnit | `pom.xml (surefire-plugin)`, `build.gradle (test task)` | `mvn test` / `gradle test` |
| Test Framework | Jest | `jest.config.*`, `package.json [jest]` | `npx jest` |
| Test Framework | Vitest | `vitest.config.*`, `vite.config.* [test]` | `npx vitest run` |
| Test Framework | gtest/Catch2 | `CMakeLists.txt (GTest/Catch2)` | `ctest --test-dir build` |
| Coverage | pytest-cov | `pyproject.toml [tool.coverage]`, `.coveragerc` | `pytest --cov=src --cov-branch` |
| Coverage | JaCoCo | `pom.xml (jacoco-maven-plugin)`, `build.gradle (jacoco)` | `mvn test jacoco:report` |
| Coverage | c8 | `package.json [c8]`, `.c8rc.json` | `npx c8 ...` |
| Coverage | nyc/Istanbul | `.nycrc`, `.nycrc.json`, `package.json [nyc]` | `npx nyc ...` |
| Coverage | gcov/lcov | `Makefile (--coverage)`, `CMakeLists.txt (ENABLE_COVERAGE)` | `gcov + lcov` |
| Mutation | mutmut | `pyproject.toml [tool.mutmut]`, `setup.cfg [mutmut]` | `mutmut run` |
| Mutation | pitest/PIT | `pom.xml (pitest-maven)`, `build.gradle (pitest)` | `mvn pitest:mutationCoverage` |
| Mutation | Stryker | `stryker.conf.json`, `stryker.conf.js`, `stryker.conf.mjs` | `npx stryker run` |
| Mutation | Mull | `mull.yml` | `mull-runner ./test-binary` |

**测试运行命令** -- 从构建脚本中提取：

| Build System | Where to Look | Example |
|-------------|--------------|---------|
| npm/yarn/pnpm | `package.json` → `scripts.test`, `scripts.test:cov`, `scripts.test:mutation` | `"test": "vitest run"` |
| Maven | `pom.xml` → surefire plugin config | `mvn test` |
| Gradle | `build.gradle` → `test` task | `gradle test` |
| Make | `Makefile` → `test:` target | `make test` |
| CMake/CTest | `CMakeLists.txt` → `add_test()` / `enable_testing()` | `ctest --test-dir build` |

### 步骤 7：生成索引 → `docs/rules/README.md`

创建索引文件，链接所有 3 个文档并附扫描摘要：

```markdown
# Codebase Convention Rules

> Auto-generated by long-task-codebase-scanner on YYYY-MM-DD.
> These documents capture the project's existing conventions.
> Edit freely — downstream skills read these during Design and Worker phases.

## Documents

| Document | Description |
|----------|-------------|
| [coding-style.md](coding-style.md) | Naming, formatting, file organization |
| [coding-constraints.md](coding-constraints.md) | 2/3方件 constraints, static analysis tools, error handling, imports |
| [build-and-compilation.md](build-and-compilation.md) | Build system, packaging, environment |

## Key Findings Summary

- **Languages**: [list]
- **Internal Libraries (2nd-party)**: [count] found — [brief list]
- **Prohibited APIs**: [count] detected
- **Static Analysis Tools**: [list]
- **Test Framework**: [detected name or "none detected"]
- **Coverage Tool**: [detected name or "none detected"]
- **Mutation Tool**: [detected name or "none detected"]
- **Build System**: [name]
```

### 步骤 8：验证结果

验证 `docs/rules/` 中至少存在 1 个输出文件。如果扫描遇到问题且无法生成所有文件，为缺失文件写入最小存根（非阻塞 -- 扫描尽力而为）。

### 步骤 10：用户评审

通过 `AskUserQuestion` 展示发现：
- 关键发现的简明摘要（尤其是二方/三方约束和禁止的 API）
- 请用户确认或编辑 `docs/rules/` 文件后再继续

## 输出文件格式

每个输出文件遵循以下结构：

```markdown
# [Title]

> Auto-generated by codebase scan on YYYY-MM-DD. Review and adjust as needed.
> Source: [N files sampled from M total]
> **Priority**: Framework/Design doc requirements > Linter/Formatter config > Source code observations.
> Conflicts with Design doc are marked with "⚠ Override" annotations.

## Section 1
[Content with evidence tables]

## Section N
[Content]

---
*Scanner: long-task-codebase-scanner | Depth: [level] | Files sampled: N*
```

## 多语言 / Monorepo 处理

- **多语言**：在单独子节中描述每种语言的约定
- **Monorepo**：识别子包边界；记录跨模块的约定差异
- **生成代码目录**（protobuf 输出、codegen 等）：标记为排除 -- 不作为约定来源使用；在 build-and-compilation.md 中列出以供下游排除

## 规则

- **只读** -- 不修改任何源文件、配置或 git 历史
- **不读取静态分析工具的配置内容** -- 仅检测工具名称 + 配置路径 + 运行命令。工具在运行时读取自身配置。
- **基于证据** -- 每个约定声明需要 file:line 示例
- **输出预算 ≤ 200 行/文件** -- 使用摘要表，而非穷举列表
- **扫描效率** -- 使用 Glob 发现文件、Grep 匹配模式、Read 检查文件、Bash 执行 git 命令
- **遵守 .gitignore** -- 不扫描被忽略的目录
- **不做评判** -- 按原样记录模式，即使它们看起来不一致或已过时

## 集成

- **被调用方**：`using-long-task` 路由器（存量项目检测规则 4b/5b 触发时），或用户直接调用
- **读取**：源文件、依赖清单、git 历史
- **链接到**：无 — 扫描完成后停止。调用方负责后续路由。
- **产出**：`docs/rules/coding-style.md`、`docs/rules/coding-constraints.md`、`docs/rules/build-and-compilation.md`、`docs/rules/README.md`
- **下游消费者**：Design skill 将规则合并到设计 §11；Init skill 将 tech_stack 与 build-and-compilation.md 测试与质量工具表交叉检查；Worker skill 在 TDD 期间引用设计 §11
