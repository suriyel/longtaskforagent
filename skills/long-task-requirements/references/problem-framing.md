# 问题界定执行协议（Problem Framing Execution Protocol）

## 何时运行

Expert track Step E1。由 SKILL.md 调用。Lite track 中**不要**运行。

## E1a. 从上下文推导（内部，无需用户交互）

在提问前，先从用户的初始描述中推导：
- 起草一句话问题陈述
- 列出若系统建成，哪些 actor 的状态会发生变化
- 假设 2–3 个当前痛点
- 若用户陈述的是**方案**（"帮我造一个 X"）而非**问题**（"我做不到 Y"）→ 打标记；方案锚定的请求必须在 E1b 中被挑战

## E1b. 问题界定轮（单次 AskUserQuestion，≤4 个问题）

措辞按项目上下文调整。若某问题答案已在 Step 1 上下文中明确，则跳过。

1. **5-Whys 种子**："今天缺少这个系统时出错的是什么？带我走一遍最近真实发生的例子 — 发生了什么、你只好怎么办、代价是什么（时间、金钱、错误、沮丧）？"
   - 从回答内部推导 WHY 链（最多 3 层）。在用户回答所支持的最深层原因处停止。**不要**臆造超出陈述或明显暗示的原因。

2. **JTBD 探针**："你最终想实现的结果是什么 — 不是你想要的工具，而是在你的世界里'成功'长什么样？"
   - 目标回答格式："我想 [动机]，这样我就能 [结果]"
   - 若回答仍是方案形态（"我想要一个 dashboard"），追问一次："拥有那个之后，你可以做到什么今天做不到的事？"

3. **痛点排序**："在你描述的问题中，哪一个代价最大 — 发生频率多高？（每天 / 每周 / 每月）"
   - 接受定性排序；**不要**强迫用户给出他没有的数字。

4. **方案挑战** *（仅当用户在原始描述中提出了某个具体方案时提问）*："这是唯一的解决办法吗？还是说只要 [JTBD 结果] 以其他方式实现你也满意？"
   - 目的：检测用户是否锚定在某个具体实现，而更简单的方案其实就能满足 JTBD。
   - 若用户**未**提出具体方案，完全跳过此问题。

## E1c. 构建工件（内部，不再向用户提问）

从回答中产出三份工件，嵌入 SRS Section 1.3：

**5-Whys Chain**：
```
Symptom: [user-stated problem in their words]
Why 1: [first cause]
Why 2: [cause of Why 1]
Why 3: [deepest supported cause — stop here unless answer goes further]
Root Cause: [systemic cause that requirements must address]
```
在用户回答支持的最深层 WHY 处停止。标记停止点。

**JTBD Statement**：
```
When [situation], I want to [motivation], so I can [outcome].
```
依 JTBD 探针的回答构造。尽量沿用用户原话。

**Pain Map**：
| Pain Point | Current Workaround | Frequency | Severity (H/M/L) | Score (F×S) |
|---|---|---|---|---|
| [pain 1] | [what they do today] | Daily/Weekly/Monthly | H/M/L | 3/2/1 × 3/2/1 |

评分：频率（Daily=3, Weekly=2, Monthly=1）× 严重度（H=3, M=2, L=1）。分数最高者 = 最高优先级痛点。

## E1d. 内部检查点

在进入 E2 之前验证：你能否**无须猜测**地陈述系统为何必须存在（WHY）、谁最受当前状态之苦（WHO）、以及构成成功的最小结果是什么（WHAT）？

- **YES** → 进入 E2
- **NO** → 再开启一轮针对性 AskUserQuestion 补齐缺口

## 输出

全部三份工件 → 写入 SRS Section 1.3（Problem Statement）。
它们喂给：
- E2（workaround probe 使用 Pain Map）
- E3（walkthrough 工作流由 Pain Map 推导）
- E10（对齐校验从 Pain Map 与 JTBD 反向检查）
