---
name: long-task-explore
description: "Use for on-demand deep exploration of an existing codebase - analyzes architecture, data flow, domain model, API surface, dependencies, and code health"
---

# 深度代码库探索

探索既有代码库以产出一份结构化理解文档。分发专用 SubAgent 定位关键结构、分析架构与数据流、并测量代码健康度。

**开始时声明：** "I'm using the long-task-explore skill to deeply explore this codebase."

## 调用模式

本 skill 可以**独立**调用，也可以**在流水线阶段内部**（requirements、increment）调用。

- **独立模式**：独立运行 —— 不依赖流水线状态，不链式调用其他 skill
- **流水线模式**：调用方提供聚焦方向和深度；探索结果反馈给调用方

两种模式下：
- **不要**修改任何源码、测试或配置文件
- 若 `docs/rules/` 存在（来自 codebase-scanner），可参考但不依赖

## CRITICAL: DOCUMENT WHAT IS, NOT WHAT SHOULD BE

- **不要**建议改进或变更
- **不要**对实现做批评或指出"问题"
- **不要**建议重构、优化或架构调整
- **仅**描述存在什么、它在哪、如何工作、组件如何交互
- 你是在为既有系统绘制一张技术地图
- 所有主张必须引用 `file:line` 证据
- 只读 —— **绝不**修改源码

## Step 1: 解析参数并声明

解析用户输入的可选参数：

| 参数 | 取值 | 默认 |
|-----------|--------|---------|
| Depth | `quick` / `standard` / `deep` | 按 LOC 自动检测 |
| `--focus` | `architecture` / `dataflow` / `domain` / `api` / `deps` / `health`（逗号分隔） | 6 个维度全覆盖 |
| `--path` | 相对目录路径 | `.`（项目根） |
| 自然语言 | 描述关注区域的任意文本 | 无（全量探索） |

若用户提供自然语言问题（如"帮我理解认证模块"、"how does the payment flow work"），视为聚焦指令 —— SubAgent 应在覆盖所需维度的同时优先处理该区域。

## Step 2: 项目检测

检测项目特征：

1. **语言**：按扩展名统计文件数量（`*.py`、`*.js`、`*.ts`、`*.tsx`、`*.java`、`*.go`、`*.rs`、`*.c`、`*.cpp`、`*.rb`、`*.kt`、`*.swift`），排除 `.git/`、`node_modules/`、`venv/`、`.venv/`、`dist/`、`build/`、`__pycache__/`
2. **框架**：检查依赖清单（`package.json`、`requirements.txt`、`pyproject.toml`、`pom.xml`、`build.gradle`、`Cargo.toml`、`go.mod`、`Gemfile`、`*.csproj`）
3. **LOC 估算**：`find <path> -type f -name "*.{ext}" | head -500 | xargs wc -l`（采样上限 500 文件以提速）
4. **深度自动检测**（用户未指定 `--depth` 时）：

   | LOC 范围 | 默认深度 |
   |-----------|---------------|
   | < 1,000 | `quick` |
   | 1,000 – 10,000 | `standard` |
   | > 10,000 | `deep` |

5. **既有规则**：若 `docs/rules/README.md` 存在，阅读以补充上下文（语言、内部库、构建系统）。作为补充上下文传递给 SubAgent。

构建 **Project Profile** 对象：
```
- root: {project_root or --path value}
- languages: [list with file counts]
- frameworks: [detected from manifests]
- loc_estimate: N
- depth: quick|standard|deep
- focus: [dimensions] or "all"
- user_question: "..." or null
- existing_rules_summary: "..." or null
```

## Step 3: 分发 Locator SubAgent（Phase 1 —— 广度优先扫描）

分发 **codebase-locator** SubAgent 快速识别代码库中的关键结构位置。

```
Agent(
  subagent_type="general-purpose",
  description="Locate codebase structure for [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-locator.md

  ## Project Profile
  {project_profile}

  Execute the full locator process per the agent definition.
  Return the structured location inventory as specified in the Structured Return Contract.
  """
)
```

**等待 locator 返回**再继续。位置清单是 Phase 2 的输入。

若 locator 返回 `BLOCKED`，回退到最小清单：只扫描顶层目录结构与入口点。

## Step 4: 分发 Analyzer + Pattern-Finder（Phase 2 —— 并行深度分析）

基于 locator 的清单，**并行**分发**两个 SubAgent**：

### Quick 模式例外

若深度为 `quick`，跳过 Phase 2。改为直接把 locator 的清单综合成一份简要概览文档（Step 6，quick 格式）。避免为小项目引入不必要的 SubAgent 开销。

### Standard / Deep 模式

按 `--focus` 决定分发哪些 SubAgent：

| Focus 包含 | 分发 |
|----------------|----------|
| `architecture`、`dataflow`、`domain`、`api`（任一） | Analyzer |
| `deps`、`health`（任一） | Pattern-Finder |
| `all`（默认） | 两者都分发 |

```
# Parallel Agent 1: Architecture Analyzer
Agent(
  subagent_type="general-purpose",
  description="Analyze architecture of [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-analyzer.md
  Read the dimension guide at: {plugin_root}/skills/long-task-explore/references/exploration-dimensions.md

  ## Project Profile
  {project_profile}

  ## Location Inventory (from Locator)
  {locator_results}

  ## Dimensions to Analyze
  {filtered_dimensions: architecture, api, dataflow, domain — based on --focus}

  Execute the full analysis process per the agent definition.
  Return the structured analysis as specified in the Structured Return Contract.
  """
)

# Parallel Agent 2: Pattern & Health Finder
Agent(
  subagent_type="general-purpose",
  description="Find patterns and health metrics for [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-pattern-finder.md
  Read the dimension guide at: {plugin_root}/skills/long-task-explore/references/exploration-dimensions.md

  ## Project Profile
  {project_profile}

  ## Location Inventory (from Locator)
  {locator_results}

  ## Dimensions to Analyze
  {filtered_dimensions: deps, health — based on --focus}

  Execute the full analysis process per the agent definition.
  Return the structured analysis as specified in the Structured Return Contract.
  """
)
```

等待两个 SubAgent 都完成。

## Step 5: 综合发现

合并所有 SubAgent（按深度与聚焦 1–3 个）的返回：

1. **收集结构化返回** —— 每个 SubAgent 提供 verdict、指标与内容章节
2. **去重** —— 多个 SubAgent 提到相同文件/模块时合并
3. **交叉引用** —— 将架构发现链接到健康热点（例如："模块 X 既是最复杂也是最高耦合"）
4. **构建 Key Findings Summary** —— 汇总指标：
   - 语言（来自 Project Profile）
   - 架构模式（来自 Analyzer）
   - 入口点数量（来自 Locator）
   - API 端点数量（来自 Locator）
   - 领域实体数量（来自 Analyzer）
   - 外部集成数量（来自 Locator + Pattern-Finder）
   - 复杂度热点 Top 3（来自 Pattern-Finder）
   - 测试/源码比（来自 Pattern-Finder）
   - 技术债标记数量（来自 Pattern-Finder）

## Step 6: 写出输出

创建探索报告：

```bash
mkdir -p docs/explore/
```

使用 `docs/templates/explore-report-template.md` 模板写 `docs/explore/codebase-research.md`。

### 各深度的输出规模

| 深度 | 内容 | 上限 |
|-------|---------|--------|
| Quick | Key Findings Summary + 每节 3–5 条要点 | <= 150 行 |
| Standard | 完整 6 节，含 Mermaid 图与证据表 | <= 400 行 |
| Deep | 完整 6 节 + 详细 Code References 索引 + 完整热点清单 | <= 600 行 |

### 聚焦过滤

若指定了 `--focus`，只包含所需维度的章节。Key Findings Summary 与 Code References **始终**包含。

### 重跑行为

若 `docs/explore/codebase-research.md` 已存在，干净地覆盖。报告永远是一次新快照。

## Step 7: 呈现摘要

以简洁格式向用户呈现 Key Findings Summary：

```
## Exploration Complete

**[project-name]** — [languages] / [frameworks]
Depth: [depth] | Files sampled: [N] / [M total]

### Key Findings
- Architecture: [pattern]
- Entry Points: [N] | API Endpoints: [N] | Domain Entities: [N]
- External Integrations: [N]
- Top Complexity Hotspot: [file:line]
- Test/Source Ratio: [N/M]
- Tech Debt Markers: [N] TODOs, [M] FIXMEs

Full report: docs/explore/codebase-research.md
```

若用户提供了自然语言问题，在展示摘要之前使用综合发现直接作答。

告知用户可以就具体模块或组件提出追问。

## 按深度的行为汇总

| 方面 | Quick | Standard | Deep |
|--------|-------|----------|------|
| 分发的 SubAgent | 1（仅 locator） | 2–3（locator → analyzer + pattern-finder） | 3（全部） |
| 每个 agent 采样文件数 | Top 30 | Top 60 | Top 120 + 全部配置 |
| Mermaid 图 | 0 | 2–3 | 所有适用 |
| 证据引用 | 每类 Top-3 | 每类 Top-5 | 穷举 |
| 输出上限 | 150 行 | 400 行 | 600 行 |

## 聚焦维度参考

| 关键字 | 维度 | 处理者 |
|---------|-----------|------------|
| `architecture` | 架构总览 —— 模块分解、模式、依赖图 | Analyzer |
| `api` | 入口点与 API 表面 —— endpoints、CLI 命令、配置表面 | Analyzer |
| `dataflow` | 数据流与状态管理 —— 模型、流水线、缓存 | Analyzer |
| `domain` | 领域模型与业务逻辑 —— 实体、规则、算法 | Analyzer |
| `deps` | 依赖与集成 —— 依赖清单、耦合、外部服务 | Pattern-Finder |
| `health` | 代码健康与复杂度 —— 热点、测试景观、技术债 | Pattern-Finder |

## 规则

- **只读** —— **不得**修改任何源文件、配置或 git 状态
- **证据驱动** —— 每个结构性主张都需要 `file:line` 示例
- **不做评判** —— 按原样记录模式，即使不一致或过时
- **输出上限** —— 遵守各深度的行数上限
- **流水线隔离** —— **绝不**读写流水线工件（feature-list.json、SRS、设计文档）
- **幂等** —— 重跑始终产出干净、全新的报告
- **SubAgent 效率** —— 文件发现用 Glob，模式匹配用 Grep，文件检查用 Read，仅 git/wc/find 命令用 Bash
