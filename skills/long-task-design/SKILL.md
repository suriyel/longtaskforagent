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
3. **提出 2-3 个方案**（对话步骤，不产出独立章节）—— 带权衡与你的推荐；选定后论证写入 §1.4
4. **按章节审批设计** —— §1 架构、§2 Feature Integration Specs、§3 数据模型（条件）、§4 内部 API 契约、§5 外部接口（条件）、§6 任务分解与依赖链
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
   - **接口需求** —— 要集成的外部系统、协议、数据格式（IFR-xxx，驱动 §5）
   - **用户角色** —— 影响 API/UI 设计决策的技术水平
   - **UCD 样式 token**（如 UCD 存在）—— 色板、字体、间距、组件目录 → 驱动前端架构决策（但不在设计文档中重复 UI/UX 方案）
4. 列出 SRS 中任何必须在设计推进前解决的 **Open Questions**
   - 如果未解决的问题影响架构 → 在 Step 2 之前通过 `AskUserQuestion` 询问用户

## Step 2：探索技术上下文

1. 探索项目将基于的已有代码 / 仓库
2. 识别 SRS 之外的技术约束（例如 monorepo 结构、CI/CD 流水线、已有库）
3. 若 `docs/rules/*.md` 存在（brownfield）：阅读以知晓已有约束，使 §1.4 Tech Stack 新选型不与 `docs/rules/coding-constraints.md` 的禁用清单冲突。**不要**把 `docs/rules/` 的内容抄入设计文档任何章节。
4. 检查设计文档模板：
   - 如果用户指定了模板路径 → 读取并校验
   - 否则 → 读取 `docs/templates/design-template.md`（本 skill 默认模板）
   - **校验**：模板必须是 `.md` 文件且至少包含一个 `## ` 标题

## Step 3：提出方案（对话步骤，不落盘）

呈现带明确权衡的 **2-3 个实现方案**：

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]
**NFR impact**: [how this approach affects the SRS NFR thresholds]
**Key dependencies**: [key libraries/frameworks with versions]

## Approach B: [Name]
...

## Recommendation: Approach [X]
**Reason**: [why this fits best given the SRS constraints and NFRs]
```

每个方案必须根据 SRS 约束与 NFR 阈值评估；无法满足 "Must" NFR 的方案淘汰。本步骤不产出独立章节；选中方案的论证抽取进 §1.4 的表格行。

## Step 4：按章节审批

对非平凡项目，将设计拆分为章节，逐节获取审批：

1. **§1 架构** —— 系统组件、逻辑视图、组件图、技术栈决策、NFR 对齐
   - 必须包含 **§1.2 逻辑视图**（Mermaid `graph`）显示层次/包/模块与依赖方向
   - 必须包含 **§1.3 组件图**（Mermaid `graph`）显示运行时组件与交互；每条边标注 Contract ID 引用 §4
   - **§1.4 技术栈决策表** 必须对照 SRS 约束与 NFR 阈值论证每个选择；含精确版本（不得 `latest`）；被淘汰方案一句话带过
   - **§1.5 NFR 对齐摘要** 展示如何满足每个 "Must" NFR

2. **§2 Feature Integration Specs**（每个关键特性或特性组一节）
   - 每个 §2.N 子节**仅**包含：
     - **§2.N.1 Overview**（1-2 句）
     - **§2.N.2 Key Types**（关键类/模块清单，每行一项 + 一句职责）
     - **§2.N.3 Integration Surface**（带 §4 Contract ID 的 Provides/Requires 表；若无跨特性依赖则写 "Self-contained"）
   - **禁止**画类图、时序图、流程图

3. **§3 数据模型**（条件性——无持久化则跳过）
   - 若适用，必须使用 Mermaid ER 图（`erDiagram`）

4. **§4 内部 API 契约**（⭐ 核心产物）
   - §1.3 组件图的每条边都必须在 §4 中有对应一行，带 Contract ID、请求/响应 schema 和错误码
   - Schema 定义块使用项目主语言语法

5. **§5 外部接口**（条件性——SRS 无 IFR 则跳过）
   - 追溯到 SRS IFR-xxx 需求

6. **§6 任务分解与依赖链**
   - §6.1 每一行成为 `feature-list.json` 的一个特性；把相关的合适大小 FR（已由 SRS G+S 启发式校验）归入垂直切片；包含 `Mapped FRs` 列保可追溯
   - §6.2 依赖链图（Mermaid `graph`）标识关键路径；全栈项目必须显式展示后端→前端边

呈现每一节。等待用户反馈。在进入下一节前纳入更改。

**对简单项目**（< 5 特性）：合并所有章节为单一审批步骤，但仍包含要求的图表与依赖版本。

**返工上限**：每节 revise ≤ 2 轮；第 3 轮自动 escalate 到用户手工处理（避免无限返工）。

> **特性 sizing 在上游完成**：FR 已在需求阶段通过双向粒度分析（G1-G6 拆分 + S1-S4 合并）调整到合适大小。§6.1 将这些合适大小的 FR 组合为实现特性。每一行应把 1+ 相关 FR 映射为能高效填满一次 Worker 会话（约 50% 上下文窗口）的垂直切片。

## Step 5：撰写设计文档

把已审批设计保存到 `docs/plans/YYYY-MM-DD-<topic>-design.md`。

### 模板用法

读取 Step 2 找到的模板（用户指定或默认 `docs/templates/design-template.md`）：
1. 保留模板的标题结构
2. 用已审批设计内容替换每个标题下的指引文字
3. 如顶部尚无元数据则添加（`Date`、`Status`、`SRS Reference`、`Template` 路径）
4. 对未覆盖的模板章节：条件性章节写 "[Not applicable]"；否则完成填写
5. 对已审批但无匹配模板章节的内容：追加为 "Additional Notes"

## Step 5b：设计集成一致性检查

衔接到 ATS 前，机械化核对跨特性集成一致性：

1. **契约完备性**：§1.3 组件图的每条边，核对 §4 内部 API 契约中存在对应一行。标记缺失行。
2. **Key Types ↔ Schema 一致**：§4 每一行，核对 Provider 特性的 §2.N.2 Key Types 清单中出现响应 schema 类型或其承载类，且 Consumer 特性的 §2.N.2 包含请求方类型。纯文本对齐即可；§4 的 Schema 定义块是 SSOT。标记不匹配。
3. **依赖完备性**：每一个出现在 §4 "Consumer" 列中的特性，核对其 §6.1 `Dependencies` 列与 §6.2 依赖链中均列出了 Provider 特性 ID。标记缺失的依赖边。

把任何被标记的问题呈现给用户。继续到 ATS 前解决。

## Step 6：衔接到 ATS

设计文档保存并提交后：

1. 为 ATS skill 总结关键输入：
   - **来自 SRS**：所有带验收标准的 FR/NFR/IFR 需求
   - **来自 Design**：§1.4 技术栈（含测试框架选型）、§1 架构风险区域、§4 内部契约（用于派生集成场景）
2. **必需子 skill：** 调用 `long-task:long-task-ats` 生成验收测试策略

## 设计阶段的伸缩

| 项目规模 | 特性数 | 设计深度 |
|---|---|---|
| 微型 | 1-5 | 单段方案 + 1 审批步骤；§1.2 逻辑视图 + 简化 §6 开发计划 |
| 小型 | 5-20 | 2-3 方案选项 + 合并章节审批；§1 全部图 + 每特性 §2.N（3 子节）+ §6 |
| 中型 | 20-50 | 完整多章节审批；全部架构视图 + 逐特性 §2.N + 完整 §6 依赖分析 |
| 大型 | 50-200+ | 完整多章节审批；每特性组 §2.N + 详细 §6 带关键路径标注 |

§2.N 在所有规模下格式不变：Overview + Key Types + Integration Surface。

## 红旗信号

| 理性化逃避 | 正确响应 |
|---|---|
| "SRS 已经暗含了架构" | SRS 描述 WHAT，不描述 HOW。呈现选项。|
| "只有一种造法" | 至少呈现 2 种方案。即便显而易见的选择也会因列出权衡而受益。|
| "我已经知道最佳方案" | 呈现选项，让用户选择 |
| "用户看起来急，跳过设计" | 简要解释其价值，然后高效进行 |
| "边做边设计" | 前置设计比会话中途纠正便宜 |
| "让我在这里重新澄清需求" | 需求属于 SRS。如有缺失，标为 Open Question，在设计前与用户解决。|
| "每特性画类图/时序图更完整" | §2.N 禁止画图。|
| "部署/测试/依赖章节写上以防万一" | 权威源在 env-guide.md / feature-list.json / 包清单；不在本文件写。|

## 图表要求

系统级架构视图**必须**使用 **Mermaid** 语法。这确保：
- 图表与文档一起版本控制（无外部图片文件）
- 图表在 GitHub、GitLab 和大多数 Markdown 查看器中可渲染
- 图表随设计变更保持同步

### 必需的图表类型

| 章节 | 图表类型 | Mermaid 语法 | 必需？ |
|---|---|---|---|
| §1.2 架构逻辑视图 | 分层包图 | `graph TB` | 总是 |
| §1.3 架构组件 | 组件交互（带 Contract ID 标签）| `graph LR` | 总是 |
| §3 数据模型 | ER 图 | `erDiagram` | 如有持久化存储 |
| §6.2 依赖链 | 关键路径 | `graph LR` | 总是 |

### 图表质量 checklist
- [ ] 每张图有清晰标题或紧邻的标题
- [ ] §1.3 组件图的每条边都含引用 §4 的 Contract ID
- [ ] §6.2 依赖链在全栈项目中显式展示后端→前端边
- [ ] 无占位图表——每张图都反映实际已审批设计内容

## §1.4 依赖版本规则

1. 关键依赖指定精确版本或受约束区间（`1.2.3` / `^1.2.0` / `>=1.2,<2.0`）；不得 `latest` 或省略。
2. 每个关键依赖与目标 runtime 版本兼容。
3. 对 copyleft license（GPL/AGPL）必须显式与用户确认。
4. brownfield：新选型不得与 `docs/rules/coding-constraints.md` 的禁用清单冲突；如必须冲突，在 §1.4 "Rejected Alternatives" 列或以 `⚠ Design Override: [reason]` 标注。
