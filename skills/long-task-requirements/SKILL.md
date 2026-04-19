---
name: long-task-requirements
description: "Use when no SRS doc and no design doc and no feature-list.json exist - elicit requirements through structured questioning and produce a high-quality SRS document aligned with ISO/IEC/IEEE 29148"
---

# 需求挖掘与 SRS 生成

通过系统化的挖掘、质询与校验，将原始想法转化为结构化、高质量的软件需求规约（SRS）——对齐 ISO/IEC/IEEE 29148 与 EARS 需求句式。

自动适配深度：对范围清晰的项目采用 **Lite 轨道**（3–5 轮），对复杂领域采用 **Expert 轨道**（10–20 轮）。两者都产出同一 SRS 模板输出。

<HARD-GATE>
在你呈现 SRS 并且用户审批通过之前，禁止调用任何设计 skill、实现 skill、写任何代码、脚手架任何项目，或执行任何设计/实现动作。这适用于**每一个**项目，不论感觉它有多简单。
</HARD-GATE>

## 反模式："这太简单不需要 SRS"

每个项目都要走这个流程。一个 todo 列表、一个单函数工具、一次 config 变更——都一样。"简单"项目往往是未经审视的假设造成最多浪费的地方。SRS 可以很短（真正简单的项目用几句话），但你必须呈现它并获得审批。

## Checklist

你必须为下列每一项创建一个 TodoWrite 任务并按顺序完成：

1. **探索项目上下文** —— 阅读已有文档、代码、约束；检测 SRS 模板
2. **复杂度评估** —— 评估 5 个信号，选定 Lite 或 Expert 轨道（内部）
3. **问题与范围挖掘**
   - Lite：L1（聚焦问题与范围，1 轮）
   - Expert：E1（问题框架，参考 `references/problem-framing.md`）+ E2（增强范围）
4. **功能需求挖掘**
   - Lite：L2（扁平能力轮次）
   - Expert：E3（场景走查，参考 `references/scenario-walkthrough.md`）+ E4（假设-纠正，参考 `references/hypothesis-correction.md`）
5. **NFR + 隐藏需求**
   - Lite：L3（合并，1 轮）
   - Expert：E6（NFR + 隐藏需求统一量化）
6. **约束、假设、术语表** —— 两条轨道相同
7. **共享质量流水线（Step 7–11）** —— DISPATCH `long-task-requirements-quality`（分类 / EARS / 图表 / 8 属性校验 / 粒度 / 延后候选）；主 agent 按返回驱动 user-input-required 审批
8. **单轮模式声明（Step 11b）** —— AskUserQuestion 可选标记 `Single-Round: Yes`
9. **[仅 Expert] 一致性校验（E10）** —— DISPATCH `long-task-requirements-alignment`
10. **SRS 合规评审（Step 13）** —— DISPATCH reviewer（加载 `prompts/srs-reviewer-prompt.md`）；关卡：所有检查 PASS
11. **呈现并审批 SRS（Step 14）** —— Lite：单一合并；Expert：按章节逐段
12. **保存（Step 15）** —— DISPATCH `long-task-requirements-finalize`（写 `docs/plans/YYYY-MM-DD-<topic>-srs.md` + 可选 deferred + git commit）
13. **衔接到 UCD（Step 16）** —— **必需子 skill：** 调用 `long-task:long-task-ucd`

**终态是调用 long-task-ucd。** 不要调用任何其他 skill。

## Step 1：探索上下文

1. 完整阅读用户提供的需求文档 / 想法描述
2. 探索项目将基于或集成的已有代码 / 仓库
3. 识别初始约束：技术栈、平台、集成、法规
4. 阅读 `docs/rules/`（如存在且已填充）—— Phase 0-pre scanner 抽取的存量代码库约定：
   - `coding-constraints.md` —— 2/3方件 库约束、禁用 API、强制内部库
   - `build-and-compilation.md` —— 构建系统与 CI/CD 约束
   - 这些约束可能影响需求可行性，应在挖掘期间考虑（例如："这个特性需要 HTTP 调用——项目强制使用内部 HTTP 库，不能用标准 fetch"；"项目 CI 要求所有代码通过 checkstyle——影响验收标准"）
5. 检查 SRS 模板：
   - 如果用户指定了模板路径 → 读取并校验
   - 否则 → 阅读 `docs/templates/srs-template.md`（本 skill 默认模板）
   - **校验**：模板必须是 `.md` 文件且至少包含一个 `## ` 标题

## Step 1.5：复杂度评估（内部——无用户交互）

Step 1 之后，针对用户描述与项目上下文评估 5 个复杂度信号：

| # | 信号 | Lite 指标 | Expert 指标 |
|---|---|---|---|
| S1 | **陈述范围** | 单一目的、边界清晰（"一个做 X 的脚本"）| 模糊/宽泛范围（"一个管理……的平台"、"一个……的系统"）|
| S2 | **角色数量** | 1 个角色或无用户交互 | 提到 2+ 个不同用户角色 |
| S3 | **集成面** | 无外部系统，或 1 个知名 API | 2+ 外部系统、自定义协议 |
| S4 | **领域复杂度** | 开发者工具、实用程序、成熟领域 | 含行话的业务领域、监管暴露、多方利益相关者 |
| S5 | **描述风格** | 方案具体化（"用 Y 构建 X"）| 问题导向或模糊（"我们需要更好的 X"、"用户抱怨 Y"）|

**≥3 个 Expert 信号 → Expert 轨道。否则 → Lite 轨道。**

在内部记录轨道决定。不要询问用户使用哪个轨道。

### 升级触发（Lite → Expert）

Lite 挖掘期间，如出现下列任一，无缝切换至 Expert 轨道：
- 2+ 个需求冲突的不同用户角色
- 3+ 个外部系统集成面
- 提到监管 / 合规要求
- 用户的回答与先前答复矛盾（暗示心智模型不清晰）
- 挖掘后 FR 数量超过 10

升级时：迄今收集的所有 Lite 产物成为 Expert 输入。不要重启或宣布破坏性切换——只是开始问更深的问题（E1 问题框架、E3 走查等）。

### 降档触发（Expert → Condensed，E1/E2 后）

完成 E1+E2 后用新信息重估 5 信号。若降至 <3（典型：JTBD 明确、单角色确认、无监管暴露）：跳过 E3 走查；E4 直接用 Archetype 批处理（见 `references/hypothesis-correction.md`）；E10 保留。目标 7–10 轮。防止 3 信号边界项目被锁死完整 Expert 路径。

## Step 1.6：定向代码库探索（仅存量项目——无用户交互）

**触发条件**（必须全部为真）：
1. `docs/rules/` 存在且至少包含 1 个 `.md` 文件（非全新项目占位）（存量项目）
2. 用户描述提到具体功能、领域区域或特定模块（非过度抽象以至无法定向）

**跳过条件**：全新项目，或用户描述过于模糊无法推导聚焦方向（例如："我想建一个平台"且无具体细节）。

**执行**：
1. 从用户描述中抽取聚焦方向：
   - 识别领域关键词（例如"认证"、"支付"、"API gateway"、"数据管线"）
   - 推断相关的 `--focus` 维度（例如 auth → `api,architecture`；data pipeline → `dataflow,deps`）
   - 如果用户提到特定模块或目录，推断 `--path`
2. 从上下文决定探索深度（不要硬编码）：

   | 信号 | 深度调整 |
   |--------|-----------------|
   | 复杂度档位 = Lite | 倾向 quick（仅 locator，快速）|
   | 复杂度档位 = Expert | 倾向 standard（完整分析）|
   | 用户描述提到单一模块/区域 | 保持当前或降低（范围窄 = 所需深度少）|
   | 用户描述跨多个子系统 | 提升一级（范围广 = 所需上下文多）|
   | 如果 `--path` 聚焦到小子树 | 保持当前或降低 |

   拿不准时，省略 `--depth`，让 explore 的 LOC 自动检测决定（<1K→quick，1K-10K→standard，>10K→deep）。

3. 以上下文驱动的参数分发 `long-task-explore`：

   > **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-explore`
   > **input**: `depth`（由上文档位决定，或省略触发自动检测）, `focus`（推断的维度列表）,
   >   `path`（推断路径或 `.`）, `user_question`（用户描述摘要）
   > **expect**: 仅结构化摘要，含下列 JSON-like keys —
   >   - `modules[]`：与 focus 相关的模块 / 包名
   >   - `integration_points[]`：外部系统 / API / 数据存储
   >   - `architectural_patterns[]`：框架 / 分层 / 约定
   >   - `api_surface[]`：与 focus 相关的公共函数 / 类 / 端点（签名 + 位置）
   >   - `narrative_insights[]`：≤5 条非显而易见的发现
   >
   > 禁止返回完整探索叙述 / 文件倾倒 / 架构图。
4. 如果 explore 返回有用发现 → 引用结构化摘要中的模块/API 为 L1/E1 提问增加精准度（例如："我在 `src/auth/` 发现了基于 JWT 的认证——你是想扩展它还是替换它？"）
5. 如果 explore 返回 BLOCKED 或无可操作发现 → 静默跳过，继续到 L1/E1

**本步骤非阻塞** —— 失败或无有用结果都不应阻止进入挖掘。

---

## Lite 轨道

适用于范围清晰、单一角色、领域成熟的项目。目标：3–5 轮交互。

### L1：聚焦问题与范围（单一 AskUserQuestion，≤4 个问题）

1. "这解决什么问题？它运转良好时的成功形态是什么？"
2. "谁用它？在什么环境（桌面/移动/CLI/API）？"
3. "本版本明确不在范围的是什么？"
4. "任何硬约束——语言、平台、托管、许可证？"

输出：SRS 第 1 节的一句问题陈述、角色列表、范围边界、约束。

如果 Q1 的答复模糊或问题导向 → 升级触发 → 切换到 Expert。

### L2：扁平能力挖掘（1–3 轮，每轮 ≤4 个问题）

对每个能力区域，每轮提问（至多 4 个）：
- 用户做什么？（触发/动作）
- 系统如何响应？（可观察行为）
- 哪些输入会非法，应如何处理？
- 确认一个具体的 Given/When/Then 示例

当相关能力共享工作流时归入同一轮。大能力区域分多轮处理。

### L3：快速 NFR + 隐藏需求检查（单一 AskUserQuestion）

1. "有性能目标吗——响应时间、吞吐量、数据量？"
2. "处理个人数据、面临法规、或需要无障碍支持吗？（如有，哪些？）"
3. "多语言或多时区？"
4. "除基本认证外，有其他安全要求吗？"

Q2 任何 YES → 内联生成 EARS 格式的 NFR 候选。如果 Q2 揭示重大监管暴露 → 升级触发。

### L4–L6：共享质量流水线

Lite 挖掘后，进入 Step 7–11（DISPATCH quality sub-skill）→ Step 11b → Step 13（DISPATCH reviewer，`track=lite` 使 Group P = PASS-SKIPPED）→ Step 14（整段 SRS 单一审批）→ Step 15（DISPATCH finalize）→ Step 16（衔接 UCD）。

**Lite 轨道跳过 E10**（一致性校验仅 Expert）。

---

## Expert 轨道

适用于领域复杂、多角色或范围不清晰的项目。目标：10–20 轮交互。

### E1：问题框架 [仅 Expert]

阅读 `references/problem-framing.md` 并严格执行。

**摘要**：单一 AskUserQuestion（≤4 个问题）—— 5-Whys 种子、JTBD 探针、痛点排序、方案质询。产出：5-Whys 链、JTBD 陈述、Pain Map → 嵌入 SRS 第 1.3 节。

### E2：增强范围轮次 [仅 Expert]

使用 E1 回答腾出的槽位。单一 AskUserQuestion（≤4 个问题）。把 E1 已答的标准 Round 1 问题替换为定向探针：

- **Workaround 探针**："走一遍你在 [Pain Map 中的 workaround] 里最烦的一步。为什么让你挫败——是手工、易错、慢还是不透明？"
  → 用户在当前 workaround 中讨厌的每一步都是候选 FR。

- **环境探针**："这通常在哪里、何时做——桌前大屏、现场移动、时间压力下，还是团队共享？"
  → 揭示 UX、离线、移动优先、多用户和无障碍约束。

以及 E1 未答的其余标准范围问题（不在范围、约束）。

**规则**：问题总数 ≤4。优先使用能浮现新信息的探针，而不是重复 E1 已覆盖的内容。

### E3：场景走查 [仅 Expert]

阅读 `references/scenario-walkthrough.md` 并严格执行。

**摘要**：每个主要工作流一次走查（1–3 个工作流）。用户端到端叙述。LLM 抽取显式步骤、隐式步骤、流程缺口、集成点、错误提及。流程缺口追问（受抽取数约束）。

### E4：假设-纠正 [仅 Expert]

阅读 `references/hypothesis-correction.md` 并严格执行。

**摘要**：每个 FR（或 2–3 个相关 FR 组），呈现带适用维度（按 FR 类型选）的 Behavior Hypothesis Table。用户标 ✓/✗/+。无新纠正即自然收敛。

**智能跳过**：如果 Step 1 上下文明确显示一个纯内部、无 PII、单语言、非监管的开发者工具 → 把全部四个探针折叠为一个确认：
> "这似乎是一个内部工具，无个人数据、无受监管行业暴露、无无障碍要求、无 i18n 需求——对吗？"

### E6–E8：NFR、约束、术语表

结构与标准挖掘相同：

**E6（NFR + 隐藏需求量化）**：先以单次 AskUserQuestion 快速探针隐藏需求（性能目标 / PII 与监管 / 无障碍 / i18n / 额外安全），YES 回答作为预填行纳入下表量化阈值。

| 类别（ISO 25010）| 探针 |
|---|---|
| **性能** | 响应时间目标？吞吐量？并发用户？|
| **可靠性** | 可用性目标？恢复时间？数据丢失容忍？|
| **易用性** | 无障碍要求？可学性标准？|
| **安全性** | 认证方式？授权模型？数据加密？|
| **可维护性** | 模块化约束？测试覆盖率目标？|
| **可移植性** | 平台限制？浏览器支持？|
| **可扩展性** | 当前负载？目标负载？增长时间线？|

明显不相关的类别可跳过。**规则**：每条 NFR 都必须有**可度量标准**。

**E7（约束与接口）**：硬限制、假设、外部系统契约。

**E8（术语表）**：具有潜在歧义的领域术语。

### E9：共享质量流水线

进入 Step 7–11（DISPATCH quality sub-skill；与 Lite 共享）。

### E10：一致性校验 [仅 Expert]

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-requirements-alignment`
> **input**: `pain_map`, `jtbd`, `workarounds`, `walkthrough_findings`, `hidden_reqs_yes_answers`,
>   `fr_list`, `nfr_list`（从 quality 的 `draft_sections` 提取）
> **expect**: Structured Return Contract；`next_step_input` 含 `alignment_report` /
>   `alignment_summary_text` / `new_requirements` / `open_questions`

按 `references/approval-revise-loop.md` 处理返回。`blocked` 时主 agent 按 `blockers` 驱动 AskUserQuestion（≥3 追溯性缺口逐项决策 / JTBD 未覆盖方面选择），Clarification Addendum 重分发。

pass 后：`new_requirements` 并入 SRS FR/NFR 列表；`open_questions` 进 §11；`alignment_summary_text` 待 Step 15 由 finalize 写入 §1.3。

### E11：SRS Reviewer、呈现、保存

进入 Step 13（DISPATCH reviewer，`track=expert`，Group P 激活）→ Step 14（非平凡项目按章节逐段呈现，不使用单一合并审批）→ Step 15（DISPATCH finalize，传入 `alignment_summary_text`）→ Step 16。

---

## Step 7–11：共享质量流水线（两条轨道）

**Step 10.0 —— 选定 sizing 档位（在 DISPATCH 前由主 agent 决定）**：

| 上下文窗口 | 档位 | 每 FR 目标 AC 数 | 单特性实现范围 |
|---|---|---|---|
| ≤ 200K tokens | `standard` | 3-12 | 约 200-600 行代码 + 测试 |
| > 200K tokens | `extended` | 5-20 | 约 500-3000 行代码 + 测试 |

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-requirements-quality`
> **input**: `raw_requirements`, `raw_nfrs`, `roles`, `constraints`, `glossary_terms`,
>   `interfaces`, `exclusions`, `sizing_tier`, `srs_template_path`
> **expect**: Structured Return Contract；`next_step_input` 含 `draft_sections` /
>   `granularity_candidates` / `deferral_candidates` / `quality_report` / `diagrams`

按 `references/approval-revise-loop.md` 处理返回。pass 时由主 agent 驱动下列交互（顺序固定）：

1. `quality_report.user_input_required[]` — 每条模糊项 AskUserQuestion 收澄清 → Revision Addendum 重分发
2. `granularity_candidates.user_input_required[]` — 4+ G/S 候选审批 → Revision Addendum 重分发
3. `deferral_candidates[]` 非空 → AskUserQuestion 确认延后清单

全部裁决完进入 Step 11b。

### Step 11b：单轮模式声明（可选）

通过 `AskUserQuestion` 询问用户：
> "本 SRS 是否作为单轮交付（不计划后续增量）？单轮会放宽 Init 的特性粒度边界——特性可合并至约 2000 LOC（而非约 1500）以减少 Worker 循环数。"
>
> 选项："是——单轮" / "否——预期有增量"

如选"是"：在 SRS frontmatter 添加 `Single-Round: Yes`（紧随 `Status:` 行）。Init Step 8c 会读取并在 `feature-list.json` 记录 `"single_round": true`。

如选"否"（或跳过）：不做任何动作。默认行为生效。

这只是信息性元数据——它不改变 Step 10 应用的粒度启发式；它只向下游 Init 粒度关卡标示意图。

---

## Step 13：SRS 合规评审

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载 `prompts/srs-reviewer-prompt.md` 并执行 reviewer
> **input**: `project_context`, `srs_draft`（来自 quality 的 `next_step_input.draft_sections`），
>   `requirement_id_list`, `track`（`lite` / `expert`，决定 Group P 是否 PASS-SKIPPED）
> **expect**: Structured Return Contract；`evidence` 含 Group R/A/C/S/D/G/Z/P 裁决列表；
>   FAIL 时 `next_step_input` 含 `user_input_items[]` 与 `llm_fixable_items[]` 两类

检查组：Group R (R1-R8 质量属性) / A (A1-A6 反模式) / C (C1-C5 完备性) / S (S1-S4 结构) / D (D1-D4 图表) / G (G1-G3 过大) / Z (Z1-Z3 过小) / P (P1-P4 问题一致性；Lite 轨道 PASS-SKIPPED)。

按 `references/approval-revise-loop.md` 处理返回。`fail` 时双轨解决：

- **Track 1（USER-INPUT）**：对 `user_input_items[]` 用 AskUserQuestion 定向收集（不倾倒完整报告）
- **Track 2（LLM-FIXABLE）**：并行修复 `llm_fixable_items[]`，合并用户澄清后 Revision Addendum 重分发（Cycle 2）

Cycle 2 仍 fail → escalate。

## Step 14–16：呈现、保存、衔接

### Step 14：呈现并审批 SRS

- **Lite 轨道**：整段 SRS 一次呈现。单一审批步骤。
- **Expert 轨道（< 5 FR）**：合并审批步骤。
- **Expert 轨道（≥ 5 FR）**：按章节逐段：
  1. Purpose、Scope、Problem Statement 与 Exclusions
  2. Glossary 与 User Personas
  3. Functional Requirements
  4. Non-Functional Requirements
  5. Constraints、Assumptions 与 Interfaces

呈现每一节。等待用户反馈。在进入下一节前纳入更改。

### Step 15：保存 SRS 文档与延后待办清单

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-requirements-finalize`
> **input**: `approved_srs_sections`（Step 14 审批通过的章节 map）, `deferred_items`（Step 7–11 第 3 步确认的延后清单，可空）, `topic_name`, `single_round_flag`, `alignment_summary_text`（Expert 轨道；Lite 省略）, `srs_template_path`
> **expect**: Structured Return Contract；`artifacts_written` 含 SRS 路径 + 可选 deferred 路径；`next_step_input` 含 `srs_path` / `topic`

按 `references/approval-revise-loop.md` 处理返回。pass 后进 Step 16。

### Step 16：衔接到 UCD

1. 为下一阶段总结关键输入（引用 finalize 返回的 `srs_path`）
2. **必需子 skill：** 调用 `long-task:long-task-ucd`

---

## Scaling 表

| 档位 | 信号 | 典型 FR 数 | 挖掘深度 | 审批 |
|---|---|---|---|---|
| **Lite** | <3 个 Expert 信号 | 1–10 | L1-L3（扁平轮次、合并 NFR）| 合并单一步骤 |
| **Expert (Small)** | ≥3 个 Expert 信号 | 5–15 | E1-E6（1–2 次走查、分组假设）| 2–3 节 |
| **Expert (Medium)** | ≥3 个 Expert 信号 | 15–50 | E1-E6（2–3 次走查、逐 FR 假设）| 逐节 |
| **Expert (Large)** | ≥3 个 Expert 信号 | 50–200+ | E1-E6（3–5 次走查、分批假设）| 逐节 |

## 红旗信号

| 理性化逃避 | 正确响应 |
|---|---|
| "这个简单到不需要 SRS" | Lite 轨道本身就是简单路径。它 3–5 轮产出短 SRS。|
| "用户已经描述了他们想要什么" | 用户描述是原始输入；SRS 增加结构、完备性、可测试性 |
| "我可以在设计期间搞清楚需求" | 需求定义 WHAT；在 HOW 中发现会导致返工 |
| "本项目不涉及 NFR" | 每个项目都至少有隐含的性能/可靠性需求——把它们显化 |
| "术语表很明显" | 对谁明显？把用户和开发者可能有歧义的每个术语都定义清楚 |
| "我先做 happy path 吧" | 错误情况、边界、反例必须**现在**就捕捉 |
| "这个 FR 作为一个大需求就可以" | 应用 6 项过大启发式（G1-G6）——隐藏复杂度会造成超大特性 |
| "这个 FR 小但清晰——留着" | 应用 4 项过小启发式（S1-S4）——琐碎 FR 会把完整流水线会话浪费在固定开销上 |
| "所有需求都属于本轮" | 范围契合评估确保专注——延后较低优先级项 |
| "延后项放到 Out-of-Scope 就行" | Out-of-Scope 是散文；延后待办清单保留 EARS + 验收标准 |
| "这很复杂但我用 Lite 省时间" | 复杂度评估存在是有原因的。若 ≥3 Expert 信号触发，使用 Expert。|
| "跳过走查，我有足够 FR" | 走查能发现逐 FR 提问遗漏的跨能力缺口 |
| "假设表维度太多" | 按 FR 类型选择维度（只读 5 行，数据录入 7 行）。不是全 8 个。|
| "无障碍不适用于本项目" | 任何用户界面都有无障碍含义。WCAG 2.1 AA 是基线。|
| "我们在设计里处理 GDPR/隐私" | 隐私需求必须在 SRS 中。数据模型和同意流依赖它们。|
| "Expert 路径太多轮，跳过一些步骤" | 每个 Expert 步骤都防止下游返工。如果项目真的更简单，它应该走 Lite。|
