---
name: long-task-design
description: "Use when SRS doc exists but no design doc and no feature-list.json - take the approved SRS as input and produce an architecture/design document focused on HOW to build it"
---

# 设计文档生成

以已审批 SRS 为输入。提出实现方案、按章节获取设计审批，并产出一份回答 HOW 的设计文档——而 SRS 回答 WHAT。

<HARD-GATE>
在你呈现设计并且用户审批通过之前，禁止调用任何实现 skill、写任何代码、脚手架任何项目、运行 init_project.py 或执行任何实现动作。这适用于**每一个**项目，不论感觉它有多简单。
</HARD-GATE>

## 反模式："SRS 已经够详细可以开始写代码了"

SRS 描述系统必须做什么（WHAT）。设计文档描述怎么做（HOW）。即便需求一清二楚，实现方式（架构、数据模型、技术栈选择）也需要显式决策与用户审批。跳过设计会造成会话中途的纠正与返工。

## Checklist

你必须为下列每一项创建一个 TodoWrite 任务并按顺序完成：

1. **阅读已审批 SRS** —— 来自 `docs/plans/*-srs.md`
2. **探索技术上下文** —— 已有代码、框架、部署环境
3. **提出 2-3 个方案** —— 带权衡与你的推荐
4. **按章节审批设计** —— 架构、数据模型、API、UI、测试、部署
5. **撰写设计文档** —— 保存到 `docs/plans/YYYY-MM-DD-<topic>-design.md` 并提交
6. **衔接到 ATS** —— **必需子 skill：** 调用 `long-task:long-task-ats`

**终态是调用 long-task-ats。** 不要调用任何其他实现 skill。

## Step 1：阅读 SRS 与 UCD 并抽取设计输入

1. 读取 `docs/plans/*-srs.md` 中已审批的 SRS 文档
2. 读取 `docs/plans/*-ucd.md` 中已审批的 UCD 样式指南（如存在——仅 UI 项目会有）
3. 抽取关键设计驱动：
   - **功能范围** —— FR 数量、优先级分布、依赖链
   - **NFR 阈值** —— 影响架构的性能目标、可靠性、可扩展性
   - **约束** —— 限制技术/方案选择的硬限
   - **接口需求** —— 要集成的外部系统、协议、数据格式
   - **用户角色** —— 影响 API/UI 设计决策的技术水平
   - **UCD 样式 token**（如 UCD 存在）—— 色板、字体、间距、组件目录 → 为前端架构与 UI/UX 节提供输入
4. 列出 SRS 中任何必须在设计推进前解决的 **Open Questions**
   - 如果未解决的问题影响架构 → 在 Step 2 之前通过 `AskUserQuestion` 询问用户

## Step 2：探索技术上下文

1. 探索项目将基于的已有代码 / 仓库
2. 识别 SRS 之外的技术约束（例如 monorepo 结构、CI/CD 流水线、已有库）
3. 检查设计文档模板：
   - 如果用户指定了模板路径 → 读取并校验
   - 否则 → 读取 `docs/templates/design-template.md`（本 skill 默认模板）
   - **校验**：模板必须是 `.md` 文件且至少包含一个 `## ` 标题

## Step 3：提出方案

呈现带明确权衡的 **2-3 个实现方案**：

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]
**NFR impact**: [how this approach affects the SRS NFR thresholds]
**Third-party dependencies**: [key libraries/frameworks this approach requires, with versions]

## Approach B: [Name]
...

## Recommendation: Approach [X]
**Reason**: [why this fits best given the SRS constraints and NFRs]
```

**要点**：每个方案必须根据 SRS 约束与 NFR 阈值评估。无法满足 "Must" NFR 的方案被淘汰。

## Step 4：按章节审批

对非平凡项目，将设计拆分为章节，逐节获取审批：

1. **架构** —— 系统组件、逻辑视图、技术栈决策
   - 必须包含 **逻辑视图**（Mermaid `graph`）显示层次/包/模块与依赖方向
   - 必须包含 **组件图**（Mermaid `graph`）显示运行时组件与交互
   - 必须对照 SRS 约束论证技术栈选择
   - 必须展示如何满足 NFR 阈值
2. **关键特性设计** —— 每个关键特性或特性组一章
   - 每个特性章至少必须包含：
     - **类图**（Mermaid `classDiagram`）—— 类/模块、属性、方法、关系
     - **一个行为图**：时序图（Mermaid `sequenceDiagram`）或流程图（Mermaid `flowchart`）
     - **集成面**（§4.N.6）—— 声明带 §6.2 Contract ID 的 Provides/Requires 表；若无跨特性依赖则写 "Self-contained"
   - 对复杂特性，包含全部四视图：类图、时序图、流程图、设计要点
   - 所有图表**必须**使用 **Mermaid** 格式——不接受 ASCII art，不接受图片引用
3. **数据模型** —— schema、关系、存储策略
   - 适用时必须使用 Mermaid ER 图（`erDiagram`）
4. **API / 接口设计**
   - **外部接口**（§6.1）—— 端点、契约、协议（追溯到 SRS IFR-xxx）
   - **内部 API 契约**（§6.2）—— 特性之间的边界；§3.3 组件图的每条边都必须在 §6.2 中有对应一行，带 Contract ID、请求/响应 schema 和错误码
5. **UI/UX 方案**（如适用）—— 布局策略、交互模式
   - 必须回应 SRS User Personas
   - 若 UCD 文档存在：必须引用 UCD 样式 token（颜色、字体、间距）与组件目录
   - 前端架构决策（组件库、状态管理、路由）必须与 UCD 样式 token 兼容
   - 包含映射：UCD 组件提示词 → 具体实现组件
6. **2/3方件（第三方依赖）** —— 所有库/框架带**精确版本号**
   - 必须验证依赖之间的相互兼容性
   - 必须验证与项目目标 runtime 版本的兼容性
   - 必须记录每个依赖的 license 类型
   - 非平凡依赖链必须包含依赖图（Mermaid）
7. **测试策略** —— 仅高层测试方式决策
   - 测试哲学：带覆盖率关卡的 TDD（Red → Green → Refactor → Coverage）
   - 工具选型：测试框架、覆盖率工具（含版本——这些是设计决策）
   - 覆盖率阈值：line >= X%、branch >= Y%
   - **边界**："详细的需求-测试类别映射、NFR 测试方法、跨特性集成场景在 ATS 阶段定义——不在此处。"
8. **部署 / 基础设施**（如适用）—— 托管、CI/CD、环境
9. **开发计划** —— 里程碑、任务分解、优先级排序
   - 必须定义带清晰退出标准的里程碑
   - 必须分解为上下文预算大小的特性（P0-P3）—— §10.2 每一行成为 `feature-list.json` 的一个特性；把相关的合适大小 FR（已由 SRS G+S 启发式校验）归入垂直切片；包含 `Mapped FRs` 列以保证可追溯性
   - 必须显示依赖链（Mermaid `graph`）标识关键路径
   - 必须包含风险评估与缓解策略

> **特性 sizing 在上游完成**：FR 已在需求阶段通过双向粒度分析（G1-G6 拆分 + S1-S4 合并）调整到合适大小。§10.2 将这些合适大小的 FR 组合为实现特性。每一行应把 1+ 相关 FR 映射为能高效填满一次 Worker 会话（约 50% 上下文窗口）的垂直切片。下方 scaling 表中的特性数指最终 §10.2 行数。

呈现每一节。等待用户反馈。在进入下一节前纳入更改。

**对简单项目**（< 5 特性）：合并所有章节为单一审批步骤，但仍包含要求的图表与依赖版本。

## Step 4b：将存量代码库约定合入设计

**如果 `docs/rules/` 不存在或仅含全新项目占位，则跳过本步骤。**

如果 `docs/rules/` 已填充约定扫描结果（来自 Phase 0-pre codebase scanner）：

1. **读取全部 `docs/rules/*.md` 文件** —— `coding-style.md`、`coding-constraints.md`、`build-and-compilation.md`、`commit-conventions.md`
2. **填充设计文档 §13**（存量代码库约定与约束）使用设计模板的 §13 结构：
   - §13.1：从 `coding-constraints.md` 抽取 "Mandatory Internal Libraries" 表
   - §13.2：从 `coding-constraints.md` 抽取 "Prohibited APIs / Libraries" 表
   - §13.3：从 `coding-constraints.md` 抽取 "Approved 3rd-Party Libraries" 表
   - §13.4：从 `coding-constraints.md` 抽取 "Static Analysis Tools" 表（仅工具名 + 配置路径 + 运行命令——不读配置内容）
   - §13.5：从 `coding-style.md` 抽取关键命名与格式规则（摘要表）
   - §13.6：从 `coding-constraints.md` 抽取错误处理模式
   - §13.7：从 `build-and-compilation.md` 抽取构建系统与 CI/CD 摘要
   - §13.8：从 `commit-conventions.md` 抽取 commit 格式与分支命名
3. **交叉校验** —— 检查扫描到的约定与设计决策之间的冲突：
   - §8（2/3方件）：新依赖不得与 §13.2 禁用清单冲突
   - §6.2（内部 API 契约）：使用的库必须符合 §13.1 强制内部库
   - 如存在冲突：标注 "⚠ Design Override: [reason]" 并呈现给用户确认
4. **把 §13 呈现给用户**进行评审（与其他章节相同的审批流程）
5. **传播到 env-guide.md §4** —— 审批后，init 阶段（`long-task-init` Step 5）会把 §13 中具约束力的部分（强制内部库、禁用 API、样式基线、构建约定）复制到 `env-guide.md` §4。下游流水线（TDD Refactor、Feature Design、Quality）直接读取 §4。`docs/rules/` 作为可追溯的扫描记录保留；§13 作为设计层摘要保留；§4 是 Worker 循环的强制源。init 之后对 §4 的任何变更需人类审批（见 Worker Step 0 env-guide 审批关卡）。

## Step 5：撰写设计文档

把已审批设计保存到 `docs/plans/YYYY-MM-DD-<topic>-design.md`。

### 模板用法

读取 Step 2 找到的模板（用户指定或默认 `docs/templates/design-template.md`）：
1. 保留模板的标题结构
2. 用已审批设计内容替换每个标题下的指引文字
3. 如顶部尚无元数据则添加（`Date`、`Status`、`SRS Reference`、`Template` 路径）
4. 对未覆盖的模板章节：标 "[Not applicable]"
5. 对已审批但无匹配模板章节的内容：追加为 "Additional Notes"

## Step 5b：设计集成一致性检查

衔接到 ATS 前，机械化核对跨特性集成一致性：

1. **契约完备性**：§3.3 组件图的每条边，核对 §6.2 内部 API 契约中存在对应一行。标记缺失行。
2. **Schema 一致性**：§6.2 每一行，核对 Provider 特性的 §4.N 类图包含响应 schema 类型，且 Consumer 特性的 §4.N 引用了请求 schema。标记不匹配。
3. **依赖完备性**：每一个出现在 §6.2 "Consumer" 列中的特性，核对其 §11.3 依赖链列出了 Provider 特性 ID。标记缺失的依赖边。

把任何被标记的问题呈现给用户。继续到 ATS 前解决。

## Step 6：衔接到 ATS

设计文档保存并提交后：

1. 为 ATS skill 总结关键输入：
   - **来自 SRS**：所有带验收标准的 FR/NFR/IFR 需求
   - **来自 Design**：测试策略、技术栈、架构风险区域
2. **必需子 skill：** 调用 `long-task:long-task-ats` 生成验收测试策略

## 设计阶段的伸缩

| 项目规模 | 特性数 | 设计深度 |
|---|---|---|
| 微型 | 1-5 | 单段方案 + 1 审批步骤；逻辑视图 + 1 特性图 + 依赖表 + 简化开发计划 |
| 小型 | 5-20 | 2-3 方案选项 + 合并章节审批；逻辑视图 + 关键特性图 + 依赖表 + 里程碑计划 |
| 中型 | 20-50 | 完整多章节审批；全部架构视图 + 逐特性图 + 完整依赖分析 + 详细开发计划 |
| 大型 | 50-200+ | 完整多章节审批；每个特性组的全面图表 + 依赖兼容性矩阵 + 带风险登记册的分期开发计划 |

## §4 深度策略

对多特性项目，§4.N 按不同深度书写以管理上下文窗口约束：

| 项目规模 | 每特性 §4.N 内容 |
|---|---|
| Small (< 20) | 完整：概述 + 类图 + 行为图 + 设计要点 + 集成面 |
| Medium (20-50) | P0/P1 特性完整；P2/P3 特性精简 |
| Large (50+) | 所有特性精简：仅 概述 + 关键类型 + 集成面 |

**精简 §4.N 格式：**

```markdown
### 4.N Feature: <Name> (FR-xxx)
#### 4.N.1 Overview
[1-2 sentences]
#### 4.N.2 Key Types
[List the main classes/types this feature introduces, with one-line purpose each]
#### 4.N.6 Integration Surface
[Provides/Requires tables referencing §6.2]
```

这是安全的，因为 feature-design SubAgent（Worker Step 4）会产出带完整 §6.2 契约访问的完整 类/时序/流程/算法 设计。精简 §4.N 作为**集成规范**，而非完整设计。

## 红旗信号

| 理性化逃避 | 正确响应 |
|---|---|
| "SRS 已经暗含了架构" | SRS 描述 WHAT，不描述 HOW。呈现选项。|
| "只有一种造法" | 至少呈现 2 种方案。即便显而易见的选择也会因列出权衡而受益。|
| "我已经知道最佳方案" | 呈现选项，让用户选择 |
| "用户看起来急，跳过设计" | 简要解释其价值，然后高效进行 |
| "边做边设计" | 前置设计比会话中途纠正便宜 |
| "让我在这里重新澄清需求" | 需求属于 SRS。如有缺失，标为 Open Question，在设计前与用户解决。|

## 图表要求

所有架构与设计视图**必须**使用 **Mermaid** 语法。这确保：
- 图表与文档一起版本控制（无外部图片文件）
- 图表在 GitHub、GitLab 和大多数 Markdown 查看器中可渲染
- 图表随设计变更保持同步

### 必需的图表类型

| 章节 | 图表类型 | Mermaid 语法 | 必需？ |
|---|---|---|---|
| 架构逻辑视图 | 分层包图 | `graph TB` | 总是 |
| 架构组件 | 组件交互 | `graph LR` | 总是 |
| 关键特性——结构 | 类图 | `classDiagram` | 逐特性 |
| 关键特性——行为 | 时序图 | `sequenceDiagram` | 逐特性（至少一个行为图）|
| 关键特性——逻辑 | 流程/判定图 | `flowchart TD` | 逐特性（至少一个行为图）|
| 数据模型 | ER 图 | `erDiagram` | 如有持久化存储 |
| 依赖图 | 依赖树 | `graph LR` | 如 > 3 个 2/3方件依赖 |
| 开发计划 | 关键路径 | `graph LR` | 总是 |

### 图表质量 checklist
- [ ] 每张图有清晰标题或紧邻的标题
- [ ] 类图显示可见性修饰符（`+`/`-`/`#`）与关键方法
- [ ] 时序图显示主成功路径与至少一个错误路径
- [ ] 流程图为所有分支逻辑包含判定节点
- [ ] 无占位图表——每张图都反映实际已审批设计内容
- [ ] §3.3 组件图的每条边都含引用 §6.2 的 Contract ID

## 2/3方件规则

1. **必需精确版本** —— 指定 `1.2.3` 或受约束区间 `^1.2.0` / `>=1.2,<2.0`；不得使用 `latest` 或省略版本
2. **兼容性矩阵** —— 核对每个依赖与下列的兼容性：
   - 目标语言/runtime 版本（例如 Python >= 3.10、Node >= 18）
   - 栈中其他依赖（检查已知冲突）
3. **License 审计** —— 记录每个依赖的 license；标注任何可能与项目要求冲突的 copyleft license（GPL、AGPL）
4. **升级路径** —— 标注任何接近 EOL 或有已知迁移关注的依赖

## 开发计划规则

开发计划节把设计文档桥接到 Init 阶段。**必须**包含：

1. **里程碑** —— 带清晰范围与退出标准的时间盒阶段
   - M1 始终为 "Foundation"（项目骨架、CI、核心抽象）
   - 最后一个里程碑始终为 "Polish & Release"（NFR 验证、文档、示例）
2. **任务分解** —— 特性映射到优先级（P0-P3）并附理由
   - P0：Foundation —— 所有其他特性所需
   - P1：Core value —— 最小可行特性集
   - P2：Extended —— 重要但非发布阻塞
   - P3：Nice-to-have —— 时间紧则延后
3. **依赖链** —— Mermaid 图显示哪些特性阻塞其他
4. **配对特性排序** —— 当项目同时有后端与前端特性时，组织任务分解表使每个后端特性与其对应的前端特性配对。这产生自然的开发流：Backend A → Frontend A → Backend B → Frontend B。Init 阶段使用此配对排序 `feature-list.json` 中的特性。
5. **风险登记册** —— 技术与进度风险及缓解

Init 阶段使用此计划以正确的优先级顺序、配对分组和依赖链填充 `feature-list.json`。

## 集成

**被调用方：** using-long-task（SRS + UCD 存在、无设计文档、无 feature-list.json 时）或 long-task-ucd（Step 8）
**依赖：** `docs/plans/*-srs.md` 中已审批 SRS；可选 `docs/plans/*-ucd.md` 已审批 UCD（UI 项目）；可选 `docs/rules/*.md`（来自 Phase 0-pre 扫描的存量代码库约定）
**衔接到：** long-task-ats（设计审批后）
**产出：** `docs/plans/YYYY-MM-DD-<topic>-design.md`（若 `docs/rules/` 存在则含 §13 存量代码库约定）
