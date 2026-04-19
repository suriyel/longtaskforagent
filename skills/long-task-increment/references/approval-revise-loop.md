# 审批-返工循环（Approval-Revise Loop · 共享模板）

> 所有 `long-task-increment-*` sub-skill 返回 Structured Return Contract 后，主 agent 按本模板统一处理"呈给用户 → 审批 → 返工"。本模板复用 `skills/using-long-task/references/structured-return-contract.md` 的 5 字段契约与 DISPATCH 声明式语法。

## 为什么存在

`long-task-increment` 的 Step 3/4/4b/5/6 都遵循相同模式：SubAgent 生成草稿 → 呈给用户 → 用户审批（approve / revise / escalate）→ 若 revise 则带反馈重分发同一 SubAgent。将该模式集中在一处定义，5 个步骤的主 SKILL.md stub 每个只需 15-25 行即可完成编排。

## 主 Agent 循环（所有 sub-skill 通用）

```
1. 组装 DISPATCH prompt（含输入字段）
2. 分发 SubAgent；接收 Structured Return Contract
3. 按 status 分支：

   status = blocked
     → AskUserQuestion(blockers) 收集用户输入
     → 组装 Clarification Addendum
     → 重分发 SubAgent（本轮不计入 revise 上限）
     → 回到步骤 3

   status = fail
     → 读 evidence 定位失败原因
     → 组装 Failure Addendum（附失败证据）
     → 重分发 SubAgent（计入 revise 上限）
     → 回到步骤 3

   status = pass
     → 进入审批关卡（见下方）

4. 审批关卡（仅 status = pass）：
     向用户呈示：
       - artifacts_written 列出的文件路径（用户可自行查看 diff）
       - evidence 摘要（≤ 3 行）
       - next_step_input 关键字段（如 Hard Impact 数、契约变更数）
     AskUserQuestion 三选一：approve / revise / escalate

5. 按审批结果分支：

   approve
     → 主 agent 不再改写产出（SubAgent 已写盘）
     → 按 next_step_input 构造下一步 DISPATCH 输入
     → 退出循环

   revise
     → 收集用户反馈（AskUserQuestion 的 notes 或 Other 文本）
     → 组装 Revision Addendum
     → 重分发 SubAgent（revise 计数 +1）
     → 回到步骤 3

   escalate
     → 中止本 sub-skill 循环
     → 在 task-progress.md 记录 escalation 原因
     → 按主 SKILL.md 的 escalation 策略接管（通常：AskUserQuestion 让用户手工指引下一步）
```

## 返工循环封顶

- **revise 默认上限：2 轮**。第 3 次触发 revise 时自动转为 escalate。
- **blocked 的 Clarification 不计数**（属于输入澄清，不是质量问题）。
- **fail 的 Failure Addendum 计入 revise 上限**（算同一质量闭环的一次返工）。
- 升级告知：`AskUserQuestion("Revise limit reached after 2 rounds. Switch to manual handling or retry from scratch?", options=[manual, retry, abort])`

## Revision Addendum 组装规则

重分发 SubAgent 时在原 DISPATCH prompt 尾部追加：

```
## Revision Addendum (round N)

**Previous artifacts**: <artifacts_written 列表>
**Why revised**: <用户 verbatim 反馈>
**Rework instruction**:
- 仅针对上述反馈修订；保持未受反馈影响的部分不变。
- 重用 previous artifacts 中未被驳回的内容；不要从零开始。
- 本轮仍须返回 Structured Return Contract（5 字段）。
```

## Clarification Addendum 组装规则（blocked → 重分发）

```
## Clarification Addendum (from blocked return)

**Blockers you reported**: <blockers 列表>
**User-provided clarifications**:
1. <question 1>: <user answer 1>
2. <question 2>: <user answer 2>
...

**Instruction**: 使用上述澄清作为权威输入继续原任务；不要再以 blocked 状态返回同一阻塞点。
```

## Failure Addendum 组装规则（fail → 重分发）

```
## Failure Addendum (round N)

**Failure evidence**: <evidence 逐行>
**Rework instruction**:
- 定位并修复上述失败；不要推翻已通过的部分。
- 若证据不足以定位，作为 blocked 返回，附 `insufficient_evidence` 标记。
```

## 审批呈现最小格式（建议）

主 agent 在审批关卡呈给用户的 AskUserQuestion 内容建议：

```
**Step N result from <sub-skill-name>**

Artifacts written:
- <path 1>
- <path 2>

Evidence (from SubAgent):
- <evidence line 1>
- <evidence line 2>

Next-step inputs (summary):
- <key 1>: <value>
- <key 2>: <value>

→ Please review artifacts on disk (or via git diff), then choose:
  [approve] | [revise (add feedback)] | [escalate]
```

## 与 Structured Return Contract 的关系

- 本模板**只**处理 `status = pass` 后的"用户批准"环节。
- `status = blocked / fail` 的通用处理规则由 `structured-return-contract.md` §主 Agent 消费规则定义；本模板只在其基础上补充 Addendum 组装与返工封顶。

## DISPATCH 语法

```markdown
> **DISPATCH** → 启动独立 SubAgent 执行 skill `<sub-skill-name>`
> **input**: <field1>, <field2>, ...
> **expect**: Structured Return Contract (status/artifacts_written/next_step_input/blockers/evidence)
```

- `input` 字段名由 SubAgent 在其 prompt 中直接引用（无需 `=` 赋值；SubAgent 从自己的 prompt 读取实际值）
- 固定路径（`feature-list.json` / `docs/plans/*-design.md` 等）由 sub-skill 内部定位，不作为 input 字段
- 过程量走 `next_step_input`（主 agent 在内存中传递）；仅最终落盘文档列入 `artifacts_written`

## 典型 stub 示例（供主 SKILL.md 参考）

```markdown
### 3. 影响评估

> **DISPATCH** → 启动独立 SubAgent 执行 skill `long-task-increment-impact`
> **input**: `new_reqs`, `wave`, `brownfield_esi`
> **expect**: Structured Return Contract；`next_step_input` 含 `impact_matrix` /
>   `api_changes` / `hard_impact_ids` / `breaking_contracts`

按 `references/approval-revise-loop.md` 处理返回：
- blocked/fail → Addendum 重分发
- pass → 审批关卡 → approve/revise/escalate
- 通过后从 next_step_input 提取后续 Step 4/4b/5/6 的输入
```

## 反模式

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| 主 agent 重复读完整文档做审批判断 | 文档读入即抵消 SubAgent 的上下文节省 | 只读 artifacts 路径 + evidence；信任 SubAgent 的 evidence 判断 |
| revise 无上限 | 无限循环风险 | 2 轮封顶；第 3 轮自动 escalate |
| 用户 revise 反馈被主 agent 重写 | 丢失用户原意 | verbatim 拷贝到 Addendum，不加解读 |
| 合并多步 SubAgent 的审批 | 一次失败回滚所有工作 | 每步独立审批；各自回到自己的 SubAgent |
| 在 Addendum 中重新描述整个任务 | 上下文污染 + 主 agent 重读原 prompt | 只附 Addendum 增量；原 DISPATCH 输入由 SubAgent 自行 recall 或主 agent 保持 prompt 幂等 |
