---
name: long-task-static-review
description: "用于预提交静态分析——自动检测并修复 Checkstyle（Java）违规直到零违规"
---

# 预提交静态分析审查

自动检测静态分析工具配置，迭代扫描并修复违规直到零违规，每次迭代设有质量门禁以防止回归。

**启动时公告：** "我正在使用 long-task-static-review skill 运行静态分析并将所有违规修复到零。"

## 唯一目标

**静态分析违规 -> 0。** 检测工具、扫描、修复、验证质量、重复直到清零。

## 调用

本 skill 是**独立的** —— 不依赖流水线，不需要 `feature-list.json`。可随时调用（预提交、预 PR、按需）。

目前支持：**Checkstyle（Java）**。架构通过 `references/tool-profiles.md` 支持未来扩展更多工具。

---

## 步骤 1：解析参数并公告

解析用户输入的可选参数：

| 参数 | 取值 | 默认值 |
|-----------|--------|---------|
| `--tool` | `checkstyle` / `all` | `all`（自动检测所有支持的工具） |
| `--max-iterations` | 整数 1-20 | 10 |
| `--path` | 目录路径 | `.`（项目根目录） |
| `--dry-run` | 标志 | false（设置时仅检测，不修复） |

打印公告及所选参数。

## 步骤 2：工具检测（只读）

读取 `{plugin_root}/skills/long-task-static-review/references/tool-profiles.md` 中的工具配置文件。对于 `--tool` 过滤器匹配的每个工具配置，执行其检测序列。

### 2a：构建工具检测

检查 `--path` 中的构建系统文件：

| 文件 | 构建系统 |
|------|-------------|
| `pom.xml` | Maven |
| `build.gradle` / `build.gradle.kts` | Gradle |

如果两者都存在：检查两者的 Checkstyle 配置，使用有配置的那个。如果都不存在：打印"未找到支持的构建系统。"并**停止**。

### 2b：Checkstyle 检测（按 tool-profiles.md）

1. **配置文件**：Glob 搜索 `**/checkstyle*.xml` —— 检查标准位置：`checkstyle.xml`、`config/checkstyle/checkstyle.xml`、`src/main/resources/checkstyle.xml`。**不读取**配置文件内容 —— Checkstyle 在运行时自行读取其配置。
2. **Maven 插件**：在 `pom.xml` 中 Grep 搜索 `maven-checkstyle-plugin`。如果找到，检查 `<checkstyle.version>` 属性或插件 `<dependency>` 块中的 `<version>`。
3. **Gradle 插件**：在 `build.gradle` / `build.gradle.kts` 中 Grep 搜索 `id 'checkstyle'` 或 `id("checkstyle")` 或 `apply plugin: 'checkstyle'`。检查 `checkstyle { toolVersion = '...' }`。
4. **运行命令**：Maven -> `mvn checkstyle:check`；Gradle -> `gradle checkstyleMain`。
5. **多模块**：检查 `pom.xml` 中的 `<modules>` 或 `settings.gradle` 中的 `include`。Maven `mvn checkstyle:check` 默认递归运行。

### 2c：流水线集成检查

如果 `docs/plans/*-design.md` 存在且包含 S11.4 章节列出了带运行命令的 Checkstyle，使用该命令作为权威来源（用户在流水线中已批准）。这防止流水线与独立执行之间的偏差。

### 2d：质量命令检测

检测步骤 4 中质量门禁的测试/覆盖率/变异测试命令。优先顺序：

1. **`long-task-guide.md`**（如果项目中存在）：直接读取 `test`、`coverage`、`mutation_feature`、`mutation_full` 命令 —— 这些已被流水线验证
2. **`feature-list.json`**（如果存在）：读取 `tech_stack` 获取测试框架、覆盖率工具、变异测试工具；按 `references/tool-profiles.md` 推导命令
3. **构建工具约定**：Maven -> `mvn test`、`mvn test jacoco:report`；Gradle -> `gradle test`、`gradle jacocoTestReport`。变异测试：Maven -> `mvn org.pitest:pitest-maven:mutationCoverage`；Gradle -> `gradle pitest`
4. **质量阈值**：从 `feature-list.json` -> `quality_gates` 读取（如可用）；否则使用默认值：line_coverage_min=90、branch_coverage_min=80、mutation_score_min=80
5. **不可用的工具**：如果构建配置中未检测到变异测试工具（无 pitest 插件、无 stryker 等），将变异测试记录为"不可用" —— Gate 3 将被跳过并发出警告。测试框架同理 —— 如果缺失，Gate 2 和 Gate 3 都将被跳过。

### 2e：检测摘要

打印摘要：

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

如果未检测到支持的工具：打印"此项目未检测到静态分析工具。"并**停止**。

如果 `--dry-run`：打印检测结果并**停止**（不修复）。

## 步骤 3：基线扫描

运行检测到的工具以建立违规基线。

### 3a：执行

```bash
{run_command} 2>&1 || true
```

`|| true` 防止构建失败退出码中断执行 —— 当存在违规时，Checkstyle 预期会失败。

### 3b：解析违规

读取命令输出并提取违规。按 tool-profiles.md，Checkstyle 格式：

- Maven：`[ERROR] /path/File.java:[line,col]: message [RuleName]`
- Gradle：`build/reports/checkstyle/main.xml` 或控制台 `[ant:checkstyle]` 行

对每个违规提取：**文件路径**、**行号**、**列号**（如有）、**规则名称**、**严重级别**、**消息**。

### 3c：分组并报告

按文件分组违规，每个文件内按行号排序。记录基线：

```
Baseline: N violations in M files
```

如果**零违规**：打印"未发现违规。代码库是干净的。" -> 跳至步骤 6 输出零迭代摘要。

## 步骤 4：扫描-修复循环

**目标：违规 -> 0。**

重复直到零违规或满足退出条件。

### 每次迭代流程

#### 4a：选择文件

按违规数降序排列文件。选择前 5 个文件（如果剩余不足则更少）。优先选择违规最多的文件，以最大化每次迭代的效果。

#### 4b：修复违规

对每个选中的文件：

1. 读取文件
2. 按 `references/tool-profiles.md` 中的修复策略修复每个违规：
   - **安全修复**（无行为风险）：空白、缩进、导入、Javadoc、花括号、行长度、修饰符顺序、编码风格 —— 直接应用
   - **低风险修复**：命名、空块、类设计、魔法数字 —— 谨慎应用，注意反射/序列化依赖
   - **中等风险修复**：方法长度（提取方法） —— 保守应用
   - **无法修复的**：需要复杂重构或设计决策的违规 -> 记录为"需要人工审查"并跳过
3. 将每个文件内的相关修复合并为单次 Edit 操作

**约束：**
- **不修改**任何 Checkstyle/工具配置文件 —— 修复代码以符合现有规则
- 仅做非行为变更：格式化、命名、导入顺序、javadoc、注解位置、花括号、修饰符顺序等
- 修复时遵循每个文件中的主导模式（缩进风格、上下文中的命名约定）
- 不添加之前不存在的新导入或依赖（展开星号导入除外）

#### 4c：质量门禁（强制，按顺序）

本次迭代修复文件后，按顺序运行全部 4 个门禁。每个门禁必须通过后才能进入下一次迭代。

**Gate 1 —— 编译**

```bash
# Maven (3-stage: sed clean → grep keep → tail cap)
mvn compile -B -q 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|BUILD ' | tail -20

# Gradle
gradle compileJava -q 2>&1 | tail -20
```

如果编译失败：修复引入了编译错误。诊断哪个修复导致了问题，回退或纠正该修复，然后重新运行编译。编译通过前不继续。

**Gate 2 —— 增量单元测试**

仅运行本次迭代中修改文件影响的测试：

```bash
# Maven (3-stage: sed clean → grep keep → tail cap)
mvn test -B -q -Dsurefire.redirectTestOutputToFile=true -Dtest={AffectedTest1,AffectedTest2,...} 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<' | tail -30

# Gradle
gradle test --tests "{AffectedTestPattern}" -q 2>&1 | tail -30
```

通过以下方式确定受影响的测试：将源文件名与测试文件命名约定匹配（例如 `Foo.java` -> `FooTest.java`），或运行修改模块范围内的测试。

如果测试失败：诊断修复是否改变了行为（命名更改破坏了反射、导入更改破坏了类路径等）。修复问题 —— 调整源码修复或更新测试。重新运行直到通过。

**Gate 3 —— 增量变异测试**

对本次迭代中修改的文件运行变异测试：

```bash
# Maven (3-stage: sed clean → grep keep → tail cap; ^>> for PIT summary lines)
mvn org.pitest:pitest-maven:mutationCoverage -B -q -DtargetClasses={changed.package.ClassName,...} 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<|^>>' | tail -30

# Gradle (pitest, scoped)
gradle pitest -DtargetClasses={changed.package.ClassName,...} -q 2>&1 | tail -30

# Or use the mutation_feature command from long-task-guide.md with changed files substituted
```

变异测试分数必须满足项目阈值（`quality_gates.mutation_score_min`，默认 80%）。如果低于阈值：为修改的文件添加或强化测试，然后重新运行。

**Gate 4 —— Checkstyle 重新扫描**

```bash
{run_command} 2>&1 || true
```

解析新的违规数量。记录：

```
Iteration N: violations_before → violations_after (delta: -X)
  Fixed files: File1.java (5→0), File2.java (3→1), ...
  Quality gates: Compile ✓ | UT ✓ | Mutation ✓ (score%) | Scan ✓
  Remaining: Y violations in Z files
```

#### 4d：退出条件

- **violations_after == 0**：目标达成 -> 进入步骤 5
- **iteration >= max_iterations**：达到上限 -> 进入步骤 5
- **卡住**：**连续 2 次迭代** violations_after >= violations_before -> 修复在振荡或引入新违规 -> 中断并进入步骤 5

## 步骤 5：最终验证

运行全范围质量验证（非增量）以确认整体项目健康。

### 5a：完整编译

```bash
mvn compile -B -q 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|BUILD ' | tail -20
```

### 5b：完整单元测试

```bash
mvn test -B -q -Dsurefire.redirectTestOutputToFile=true 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<' | tail -30
```

运行完整测试套件，不仅是受影响的测试。如果失败，不带管道重新运行以获取完整详情。

### 5c：完整变异测试

```bash
# Use mutation_full_quiet command from long-task-guide.md, or:
mvn org.pitest:pitest-maven:mutationCoverage -B -q 2>&1 | sed 's/\x1b\[[0-9;]*m//g; /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/d; /^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/d; /^Downloading:/d; /^Downloaded:/d; /^Progress/d' | grep -E '\[ERROR\]|\[WARNING\]|Tests run:|BUILD |<<<|^>>' | tail -30
```

全项目范围变异测试。分数必须满足阈值。

### 5d：最终 Checkstyle 扫描

```bash
{run_command} 2>&1 || true
```

确认最终违规数量。

### 5e：残留分类

如果循环结束后仍有违规，对每个违规分类：

| 分类 | 描述 |
|----------------|-------------|
| **需要人工审查** | 需要人工判断 —— 复杂重构、设计决策、方法拆分 |
| **振荡** | 修复规则 A 引入规则 B 的违规，反之亦然 |
| **新增** | 由先前修复引入（该特定规则净增） |

列出每个残留违规及其分类。

## 步骤 6：摘要报告

打印最终摘要：

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

如果项目中存在 `task-progress.md`，追加一行记录：
```
- Static Review: Checkstyle — {violations_fixed} violations fixed in {iterations} iterations ({files_modified} files), quality gates passed
```

---

## 边界情况

| 条件 | 行为 |
|-----------|----------|
| 无 `pom.xml` 或 `build.gradle` | 停止："未找到支持的构建系统。" |
| 构建中未配置 Checkstyle | 停止："未检测到静态分析工具。" |
| 扫描前构建失败（编译错误） | 诊断并停止。不尝试修复预先存在的构建错误 —— 仅修复样式违规。 |
| 基线零违规 | 以零迭代的清洁摘要停止（步骤 6）。 |
| 达到最大迭代次数仍有违规 | 报告残留违规及其分类。 |
| 卡住（连续 2 次迭代无进展） | 提前中断，将残留报告为振荡/无法修复。 |
| 多模块项目 | 在项目根目录运行；跨所有模块统一追踪违规。 |
| 设计文档 S11.4 存在且有 Checkstyle | 使用 S11.4 运行命令作为权威来源。 |
| `long-task-guide.md` 存在 | 使用其测试/覆盖率/变异测试命令作为质量门禁。 |
| 未配置变异测试工具 | 跳过 Gate 3（变异测试）并发出警告；其他门禁仍然执行。 |
| 未检测到测试框架 | 跳过 Gate 2（单元测试）和 Gate 3（变异测试）并发出警告；编译 + 扫描仍然执行。 |

## 规则

- **配置文件只读** —— 绝不修改 Checkstyle 配置、`pom.xml` 插件配置或 Gradle checkstyle 块。本 skill 修复源代码以符合现有规则。
- **行为保持** —— 修复不得改变程序行为。仅限格式化、命名、导入顺序、javadoc、注解位置、花括号风格、修饰符顺序等非行为变更。
- **质量门禁不可协商** —— 每次迭代必须通过编译 + 单元测试 + 变异测试后才能继续。不走捷径，不"应该没问题"。
- **不添加新依赖** —— 修复不得添加之前不存在的导入或依赖（展开星号导入除外）。
- **对 Git 安全** —— 不提交变更。用户在 skill 完成后审查并提交。
- **幂等性** —— 在已经干净的代码库上重新运行会产生零迭代的清洁摘要。
- **与流水线兼容** —— 与 long-task 流水线配合使用时，以设计文档 S11.4 和 `long-task-guide.md` 作为命令和阈值的权威来源。

## 集成

**调用方：** 用户按需调用（独立）
**前置条件：** 通过 Maven 或 Gradle 配置了 Checkstyle 的 Java 项目
**产出：** 零 Checkstyle 违规的源代码（或已分类的残留违规），所有质量门禁通过
**不链接到：** 任何流水线 skill —— 完全独立
