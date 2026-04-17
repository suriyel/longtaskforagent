# 假设纠偏执行协议（Hypothesis-Correction Execution Protocol）

## 何时运行

Expert track Step E4。由 SKILL.md 在 Scenario Walkthrough（E3）之后调用。

## 目的

在不提开放式问题的前提下，补齐每条 FR 的边界、错误处理、权限与数据生命周期。LLM 主动从已有上下文推导具体的行为假设交给用户确认/纠正，而不是让用户凭空设想所有边界情况。

## 核心机制

对每条 FR（或 2–3 条相关 FR 为一组），LLM **从全部可用上下文推导出具体的行为假设**（走查叙述、领域知识、Pain Map、Step 1 上下文）。这些假设以结构化的 **Behavior Hypothesis Table** 呈现给用户，供用户确认（✓）、纠正（✗）或补充（+）。

## Behavior Hypothesis Table 格式

通过 AskUserQuestion 呈现：

> "基于你的走查，下面是我对 **[FR 标题]** 的假设。请在每一行做标记：✓ 正确、✗ 错误（请告诉我正确答案），或 + 补充我漏掉的。"

| # | Dimension | My Assumption | ✓/✗/+ |
|---|---|---|---|
| 1 | **Happy path** | When [trigger], the system [action], resulting in [outcome] | |
| 2 | **Invalid input** | If [specific invalid input], the system [assumed error behavior, e.g., shows inline error, rejects silently, auto-corrects] | |
| 3 | **Boundary** | Maximum [N items / file size / characters] is [assumed limit]; beyond that [assumed behavior] | |
| 4 | **Failure path** | If [external dependency] is unavailable, the system [assumed fallback: retry / queue / show error / degrade gracefully] | |
| 5 | **Permission** | Only [assumed roles] can perform this; unauthorized users see [assumed behavior: 403 / hidden button / redirect] | |
| 6 | **Concurrency** | If two users simultaneously [action], [assumed conflict resolution: last-write-wins / lock / merge / queue] | |
| 7 | **Data lifecycle** | Data created by this action is [retained forever / expires after X / user-deletable / admin-archivable] | |
| 8 | **Negative scope** | This FR does NOT [assumed exclusion — something the user might expect but is out of scope] | |

**每条假设都必须具体而明确**，不得笼统。反例："如果输入不合法，系统会报错。" 正例："如果 email 字段不含 @ 符号，系统在该字段下方显示内联错误并阻止提交。"

## FR 类型定义与维度选择

不是所有 8 个维度都适用于每条 FR。按 FR 类型选择：

| FR Type | Definition | Include Dimensions | Skip Dimensions |
|---|---|---|---|
| **Read-only display** | 向用户展示数据而不修改状态 | 1, 3, 4, 5 | 2（无输入）、6（无写入）、7（无数据创建） |
| **Data entry / form** | 用户提交新数据或编辑已有数据 | 1, 2, 3, 4, 5, 7 | 6（除非可能多人编辑） |
| **State-changing action** | 触发状态迁移（审批、取消、发布、删除） | 1, 2, 4, 5, 6, 7 | 3（除非批处理） |
| **Background process** | 无直接用户交互（cron、队列消费者、同步） | 1, 4, 7 | 2, 3, 5, 6（无直接用户交互） |
| **Integration / API** | 与外部系统收发数据 | 1, 3, 4, 8 | 5（除非面向用户）、6、7 |

**对边界在"范围内 / 范围外"之间模糊的复杂 FR，务必包含维度 8（negative scope）**。

## 批处理规则

**默认按 Archetype 批处理**：把 FR 按类型（read-only / data-entry / state-changing / background / integration）分桶。每桶一张规范假设表：用户先对该类型默认行为标 ✓/✗/+，再逐条列桶内 FR 的**偏离点**（仅不同处需展开）。Medium 项目（15–50 FR）可从 15+ 表压至 5–8 表。

**独立呈现条件**：FR 行为与同桶显著不同，或需全部 8 维度（通常是复杂 state-changing）。

**回退**：Archetype 无法清晰分桶时，退回"2–3 条相关 FR 合并呈现"。

**深度优先**：任何呈现都应深挖维度，而非堆叠更多 FR。

## 收敛机制

假设纠偏协议**自收敛**，无需硬上限：

- ✓（确认）→ 假设正确，无需进一步处理
- ✗（纠正）→ LLM 依用户纠正更新 FR
- +（补充）→ 用户补上 LLM 漏掉的维度 → 新增验收准则（若补充描述的是独立能力，则新增一条 FR）

**当所有 FR 都没有新的 ✗ 或 + 时，假设纠偏完成。** 没有开放式追问，没有"还有别的吗？" — 表格结构按设计穷举了行为维度。

若某个 ✗ 纠正揭示了显著的新复杂度（例如"其实审批流根据金额分三种"），将此纠正视为触发器，为新发现的 sub-FR 再跑一轮假设表。

## 每行的输出

| User Mark | Becomes |
|---|---|
| ✓ confirmed happy path | EARS statement for the FR |
| ✓ or ✗ boundary/error/permission/concurrency/lifecycle | Given/When/Then acceptance criterion |
| + added dimension | New acceptance criterion for the FR, or a new candidate FR if it describes a distinct capability |
| ✓ confirmed dimension 8 (negative scope) | EXC-xxx exclusion entry |

## 质量检查

所有假设表完成后，验证：
- 每条 FR 至少有一条错误 / 边界验收准则（满足既有 A6 反模式检查）
- 每条带外部依赖的 FR 都指定了失败路径
- 每条带用户输入的 FR 都指定了非法输入处理
