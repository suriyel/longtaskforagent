---
name: long-task-explore
description: "用于按需深度探索现有代码库——分析架构、数据流、领域模型、API 接口、依赖关系和代码健康度"
---

# 深度代码库探索

探索现有代码库以生成结构化的理解文档。分派专门的 SubAgent 定位关键结构、分析架构和数据流，并度量代码健康度。

**启动时公告：** "我正在使用 long-task-explore skill 对此代码库进行深度探索。"

## 步骤 1：解析参数并公告

解析用户输入的可选参数：

| 参数 | 取值 | 默认值 |
|-----------|--------|---------|
| Depth | `quick` / `standard` / `deep` | 按代码行数自动检测 |
| `--focus` | `architecture` / `dataflow` / `domain` / `api` / `deps` / `health`（逗号分隔） | 全部 6 个维度 |
| `--path` | 相对目录路径 | `.`（项目根目录） |
| 自然语言 | 任意描述关注领域的文本 | 无（完整探索） |

如果用户提供了自然语言问题（例如"帮我理解认证模块"、"支付流程是怎么运作的"），将其视为关注指令——SubAgent 应优先探索该领域，同时仍覆盖请求的维度。

## 步骤 2：项目检测

检测项目特征：

1. **语言**：按扩展名统计文件数量（`*.py`、`*.js`、`*.ts`、`*.tsx`、`*.java`、`*.go`、`*.rs`、`*.c`、`*.cpp`、`*.rb`、`*.kt`、`*.swift`），排除 `.git/`、`node_modules/`、`venv/`、`.venv/`、`dist/`、`build/`、`__pycache__/`
2. **框架**：检查依赖清单（`package.json`、`requirements.txt`、`pyproject.toml`、`pom.xml`、`build.gradle`、`Cargo.toml`、`go.mod`、`Gemfile`、`*.csproj`）
3. **代码行数估算**：`find <path> -type f -name "*.{ext}" | head -500 | xargs wc -l`（为提高速度，采样上限 500 个文件）
4. **深度自动检测**（如果用户未指定 `--depth`）：

   | 代码行数范围 | 默认深度 |
   |-----------|---------------|
   | < 1,000 | `quick` |
   | 1,000 – 10,000 | `standard` |
   | > 10,000 | `deep` |

5. **已有规则**：如果 `docs/rules/README.md` 存在，读取其上下文（语言、内部库、构建系统），作为补充上下文传递给 SubAgent。

构建**项目概况**对象：
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

## 步骤 3：分派定位器 SubAgent（阶段 1——广度优先扫描）

分派 **codebase-locator** SubAgent，快速识别代码库中的关键结构位置。

> **DISPATCH** independent SubAgent — Locate codebase structure for [project]
> Definition: `{plugin_root}/agents/codebase-locator.md`
> Input: Project Profile (from Step 2)
> Expect: `Verdict` + `Location Inventory`（Modules / Entry Points / API Endpoints / Data Models / Configuration / External Integrations / Test Directories 七张子表）。若 `Verdict=BLOCKED`，按下文"回退到最小清单"分支处理。
> Execute the full locator process. Return structured location inventory.

**等待定位器返回**后再继续。位置清单是阶段 2 的输入。

如果定位器返回 `BLOCKED`，回退到最小清单——仅扫描顶层目录结构和入口点。

## 步骤 4：分派分析器 + 模式发现器（阶段 2——并行深度分析）

根据定位器的清单，**并行分派两个 SubAgent**：

### Quick 模式例外

如果深度为 `quick`，跳过阶段 2。改为直接将定位器的清单综合成简要概览文档（步骤 6，quick 格式）。这避免了小项目不必要的 SubAgent 开销。

### Standard / Deep 模式

根据 `--focus` 确定分派哪些 SubAgent：

| focus 包含 | 分派 |
|----------------|----------|
| `architecture`、`dataflow`、`domain`、`api`（任一） | 分析器 |
| `deps`、`health`（任一） | 模式发现器 |
| `all`（默认） | 两者都分派 |

> **DISPATCH** independent SubAgent — Analyze architecture of [project]
> Definition: `{plugin_root}/agents/codebase-analyzer.md`
> References: `{plugin_root}/skills/long-task-explore/references/exploration-dimensions.md`
> Input: Project Profile + Location Inventory (from Step 3)
> Expect: `Verdict` + `Architecture Overview` / `Entry Points & API Surface` / `Data Flow & State Management` / `Domain Model & Business Logic`（按 Project Profile.focus 过滤）+ `Open Questions`（供 Step 5 聚合）。

> **DISPATCH** independent SubAgent — Find patterns and health metrics for [project]
> Definition: `{plugin_root}/agents/codebase-pattern-finder.md`
> References: `{plugin_root}/skills/long-task-explore/references/exploration-dimensions.md`
> Input: Project Profile + Location Inventory (from Step 3)
> Expect: `Verdict` + `Dependencies & Integrations` / `Code Health`（按 Project Profile.focus 过滤）+ `Open Questions`（供 Step 5 聚合）。

等待两个 SubAgent 全部完成。

## 步骤 5：综合发现

合并所有 SubAgent（根据深度和关注维度，1-3 个）的返回结果：

1. **收集结构化返回** —— 每个 SubAgent 提供判定、指标和内容章节
2. **去重** —— 如果多个 SubAgent 提到相同的文件/模块，合并处理
3. **交叉引用** —— 将架构发现与健康热点关联（例如"模块 X 既是最复杂的，也是耦合度最高的"）
4. **构建关键发现摘要** —— 聚合指标：
   - 语言（来自项目概况）
   - 架构模式（来自分析器）
   - 入口点数量（来自定位器）
   - API 端点数量（来自定位器）
   - 领域实体数量（来自分析器）
   - 外部集成数量（来自定位器 + 模式发现器）
   - 复杂度热点前 3 名（来自模式发现器）
   - 测试与源码比例（来自模式发现器）
   - 技术债务标记数量（来自模式发现器）
5. **聚合 Open Questions** —— 从分析器、模式发现器返回的 `Open Questions` 节合并，去重后保留 3-8 条最高价值问题。每条保留：问题 + 关联 `file:line` + 下游影响 phase（requirements / design / increment 任一或多）。若合并后少于 3 条，可留空段但至少保留本节标题；若多于 8 条，按"影响面广度 × 歧义度"裁剪至 8 条以内。

## 步骤 6：写入输出

创建探索报告：

```bash
mkdir -p docs/explore/
```

使用 `docs/templates/explore-report-template.md` 模板编写 `docs/explore/codebase-research.md`。

### 各深度的输出规模

| 深度 | 内容 | 行数预算 |
|-------|---------|--------|
| Quick | 关键发现摘要 + 每个章节 3-5 个要点 | <= 150 行 |
| Standard | 完整 6 个章节，含 Mermaid 图和证据表 | <= 400 行 |
| Deep | 完整 6 个章节 + 详细代码引用索引 + 完整热点列表 | <= 600 行 |

### 关注维度过滤

如果指定了 `--focus`，仅包含请求的维度章节。始终包含关键发现摘要和代码引用。

### 重新运行行为

如果 `docs/explore/codebase-research.md` 已存在，直接覆盖。报告始终是全新快照。

## 步骤 7：展示摘要

以简洁格式向用户展示关键发现摘要：

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

如果用户提供了自然语言问题，在展示摘要之前使用综合发现直接回答该问题。

告知用户可以针对特定模块或组件提出后续问题。

## 各深度行为汇总

| 方面 | Quick | Standard | Deep |
|--------|-------|----------|------|
| 分派的 SubAgent | 1（仅定位器） | 2-3（定位器 -> 分析器 + 模式发现器） | 3（全部） |
| 每个 agent 采样文件数 | 前 30 | 前 60 | 前 120 + 全部配置文件 |
| Mermaid 图 | 0 | 2-3 | 所有适用的 |
| 证据引用 | 每类前 3 | 每类前 5 | 详尽 |
| 输出预算 | 150 行 | 400 行 | 600 行 |

## 关注维度参考

| 关键词 | 维度 | 处理者 |
|---------|-----------|------------|
| `architecture` | 架构概览——模块分解、模式、依赖图 | 分析器 |
| `api` | 入口点与 API 接口——端点、CLI 命令、配置面 | 分析器 |
| `dataflow` | 数据流与状态管理——模型、流水线、缓存 | 分析器 |
| `domain` | 领域模型与业务逻辑——实体、规则、算法 | 分析器 |
| `deps` | 依赖与集成——依赖清单、耦合度、外部服务 | 模式发现器 |
| `health` | 代码健康度与复杂度——热点、测试全景、技术债务 | 模式发现器 |

## 规则

- **只读** —— 不修改任何源文件、配置或 git 状态
- **基于证据** —— 每个结构性断言需要 `file:line` 示例
- **不作评判** —— 按原样记录模式，即使不一致或过时
- **输出预算** —— 遵循各深度的行数限制
- **流水线隔离** —— 绝不读写流水线工件（feature-list.json、SRS、设计文档）；`docs/rules/` 可只读作为补充上下文（来自 scanner）
- **幂等性** —— 重新运行总是生成干净的全新报告
- **SubAgent 效率** —— 使用 Glob 进行文件发现，Grep 进行模式匹配，Read 进行文件检查，Bash 仅用于 git/wc/find 命令
