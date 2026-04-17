# 场景走查执行协议（Scenario Walkthrough Execution Protocol）

## 何时运行

Expert track Step E3。由 SKILL.md 在 Problem Framing（E1）与 Enhanced Scope（E2）之后调用。

## 目的

在深入单条 FR 之前，先发现宏观流程的缺口、集成点以及隐含的顺序依赖。逐能力的问答式采集会遗漏跨能力需求 — 走查通过强迫用户叙述完整旅程来暴露它们。

## 走查数量

每个主要工作流一次走查。主要工作流由 Pain Map 的头部条目与 E2 的回答决定。

| Expert Scale | Walkthroughs |
|---|---|
| Small (5–15 FR) | 1–2 |
| Medium (15–50 FR) | 2–3 |
| Large (50–200+ FR) | 3–5（每个 epic / domain 一次） |

## 走查提问（每个工作流一次 AskUserQuestion）

> "带我从头到尾走一遍完整的 [工作流名称]。从你决定 [触发动作] 的那一刻开始。逐步告诉我你会做什么、在每个节点上系统应当显示或执行什么、在哪里停止。包含出错时会发生什么。"

将触发动作改编为具体工作流。示例：
- "…从你需要给新员工 onboarding 的那一刻开始…"
- "…从客户下单的那一刻开始…"
- "…从你在数据里察觉到异常的那一刻开始…"

## LLM 提取（内部，无需用户交互）

对每段叙述性回答，提取并归类：

| Category | What to look for | Example | Action |
|---|---|---|---|
| **Explicit steps** | 直接陈述的期望系统行为 | "I click 'Submit' and the system saves the record" | → 候选 FR |
| **Implicit steps** | 用户一笔带过或视为"理所当然"的动作 | "then I'd log in"（暗示鉴权） | → 候选 FR，标记到追问中确认 |
| **Flow gaps** | 用户跳过机制直接越到下一步 | "then the report appears"（怎么来的？手动触发？自动生成？定时？） | → 针对性追问 |
| **Integration points** | 提到的外部系统、数据源、对其他工具的交接 | "I export it to Salesforce" | → 候选 IFR |
| **Error mentions** | 对失败、异常或恢复的任何提及 | "sometimes the API times out" | → 相关 FR 的候选验收准则 |

## 流程缺口追问（每个工作流单次 AskUserQuestion，若存在缺口）

若提取产生了需要确认的流程缺口或隐式步骤，在一次追问中合并提问：

> "在你的 [工作流] 走查中，我想确认几点：
> 1. 在 [步骤 A] 与 [步骤 B] 之间，[过渡] 是如何发生的 — 用户触发，还是系统自动？
> 2. 你提到了 [模糊步骤] — 那一刻屏幕上具体应当显示什么？
> 3. 当 [错误提及] 发生时，期望的恢复路径是什么？"

依缺口数量调整题目数。若未发现缺口，完全跳过追问。

## 输出

- **候选 FR 列表**（含出处：来自哪一次走查、哪一步、显式 vs 隐式）
- **候选 IFR 列表**（来自集成点）
- **候选验收准则**（来自错误提及）

全部输出喂给 Hypothesis-Correction（E4）— 每个候选 FR 在下一步得到一张 Behavior Hypothesis Table。

## 收敛

本步由以下因素天然有界：
- 主要工作流数量（走查前即已确定，有限）
- 用户叙述长度（有限 — 故事讲完用户就会停）
- 流程缺口追问数量（由提取结果确定，有限）

不提"还有别的吗？"或"我漏了什么吗？"这类开放式问题。走查结构本身对其范围已是穷举的。
