# 审批-返工循环（Approval-Revise Loop · long-task-init）

> 所有 `long-task-init-*` sub-skill 返回 Structured Return Contract 后，主 agent 按本模板统一处理"呈给用户 → 审批 → 返工"。`long-task-init-bootstrap` 是零审批直通（确定性输出），env 与 features 走完整循环。

## 主 Agent 循环

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
       - next_step_input 关键字段
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
     → AskUserQuestion 让用户手工指引下一步
```

## 返工循环封顶

- **revise 默认上限：2 轮**。第 3 次触发 revise 时自动转为 escalate。
- **blocked 的 Clarification 不计数**（属于输入澄清，不是质量问题）。
- **fail 的 Failure Addendum 计入 revise 上限**（算同一质量闭环的一次返工）。
- 升级告知：`AskUserQuestion("Revise limit reached after 2 rounds. Switch to manual handling or retry from scratch?", options=[manual, retry, abort])`

## env-guide.md §3 / §4 双关卡细则（env sub-skill 专用）

- env sub-skill 首次生成 env-guide.md 时，frontmatter `approved_by: null` 为"首次生成豁免"。
- **审批关卡中 §3 与 §4 合并呈现**：
  - 同一次 AskUserQuestion 列出两段 diff（§3 Build & Execution / §4 存量约束）
  - 用户选 approve → 主 agent 更新 frontmatter：`approved_by: <user-name>`、`approved_date: <today>`、`approved_sections: ["§3", "§4"]`
  - 用户选 revise → 走正常 Revision Addendum；frontmatter 保持 `null`
- 后续 increment 修改 §3 / §4 时，同步关卡由 `long-task-increment-design` sub-skill 的 `env-guide-approval-pending` blocker 驱动，不在此模板内重复处理。

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

## Features Sizing 关卡细则（features sub-skill 专用）

`long-task-init-features` 返回 pass 后，主 agent 在审批关卡**之前**插入 sizing 呈示：

```
Feature count: <count>
Estimated LOC distribution:
  - < 500 LOC (too small):  <n> features → suggest merge
  - 500-1500 LOC (ok):      <n> features
  - > 1500 LOC (too large): <n> features → suggest split
Adopt current decomposition? [y / auto-fix / manual-adjust]
```

- `y` → 等同 approve，退出循环
- `auto-fix` → 等同 revise；Addendum 内容："按 loc_distribution 中 band=small/large 的特性执行合并/拆分；保持 srs_trace；拆分时每个结果特性携带父的 srs_trace 子集"。重分发覆盖写 feature-list.json
- `manual-adjust` → 暂停循环，提示用户在编辑器里直接改 `feature-list.json`；用户确认改完 → 主 agent 只重跑 `python scripts/validate_features.py feature-list.json` 验证（**不重分发 sub-skill**，信任用户编辑）；通过则等同 approve

## 审批呈现最小格式

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

## DISPATCH 语法

```markdown
> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:<sub-skill-name>`
> **input**: <field1>, <field2>, ...
> **expect**: Structured Return Contract (status/artifacts_written/next_step_input/blockers/evidence)
```

- `input` 字段名由 SubAgent 在其 prompt 中直接引用（无需 `=` 赋值；SubAgent 从自己的 prompt 读取实际值）
- 固定路径（`feature-list.json` / `docs/plans/*-design.md` / `docs/rules/*.md` 等）由 sub-skill 内部定位，不作为 input 字段
- 过程量走 `next_step_input`（主 agent 在内存中传递）；仅最终落盘文档列入 `artifacts_written`

## 反模式

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| 主 agent 重复读完整文档做审批判断 | 文档读入即抵消 SubAgent 的上下文节省 | 只读 artifacts 路径 + evidence；信任 SubAgent 的 evidence 判断 |
| revise 无上限 | 无限循环风险 | 2 轮封顶；第 3 轮自动 escalate |
| 用户 revise 反馈被主 agent 重写 | 丢失用户原意 | verbatim 拷贝到 Addendum，不加解读 |
| 合并多步 SubAgent 的审批 | 一次失败回滚所有工作 | 每步独立审批；各自回到自己的 SubAgent |
| sub-skill 内部直接修改 env-guide frontmatter `approved_by` | 审批字段归用户 | sub-skill 只生成 §内容；主 agent 在关卡后更新 frontmatter |
| `manual-adjust` 后重分发 sub-skill | 覆盖用户手工编辑 | 只重跑 validate_features.py；信任用户产物 |
