# 审批-返工循环

sub-skill 返回 Structured Return Contract 后，按本模板处理。

## 主循环

```
1. 组装 DISPATCH prompt 并分发 SubAgent
2. 按 status 分支：
   blocked → AskUserQuestion 收 blockers → Clarification Addendum 重分发（不计 revise）
   fail    → 读 evidence → Failure Addendum 重分发（计 revise）
   pass    → 若本 sub-skill 启用审批关卡，进步骤 3；否则按 next_step_input 进下一步
3. 审批关卡：向用户呈 artifacts_written + evidence + next_step_input 关键字段
   AskUserQuestion(approve / revise / escalate)
   approve  → 退出循环，按 next_step_input 进下一步
   revise   → Revision Addendum 重分发（计 revise）
   escalate → 中止循环，主 SKILL escalation 接管
```

## 审批关卡配置

| Sub-skill | 审批关卡 |
|---|---|
| `long-task-requirements-quality` | 不启用（主 agent 用 next_step_input 的候选清单自行驱动 AskUserQuestion 后进下一步）|
| `long-task-requirements-alignment` | 不启用（alignment_summary_text 由 finalize 写入 SRS §1.3）|
| `long-task-requirements-finalize` | 启用（文档已落盘，审批仅决定 approve / revise / escalate）|

## revise 封顶

- 2 轮；第 3 次自动 escalate
- `blocked` 的 Clarification 不计数
- `fail` 的 Failure Addendum 计数
- 升级告知：`AskUserQuestion("Revise limit reached after 2 rounds", options=[manual, retry, abort])`

## Addendum 组装

**Revision Addendum (round N)**
```
**Previous artifacts / next_step_input**: <上一次产出摘要>
**Why revised**: <用户反馈 verbatim>
**Rework instruction**:
- 仅针对上述反馈修订；保持未受反馈影响的部分不变。
- 重用未被驳回的内容；不要从零开始。
- 返回 Structured Return Contract（5 字段）。
```

**Clarification Addendum (from blocked)**
```
**Blockers you reported**: <blockers 列表>
**User-provided clarifications**:
1. <question>: <answer>
...
**Instruction**: 使用澄清作为权威输入继续；不要再以同一阻塞点返回 blocked。
```

**Failure Addendum (round N)**
```
**Failure evidence**: <evidence 逐行>
**Rework instruction**:
- 定位并修复上述失败；不要推翻已通过的部分。
- 证据不足以定位 → 作为 blocked 返回，附 `insufficient_evidence` 标记。
```

## DISPATCH 语法

```markdown
> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:<name>`
> **input**: <field1>, <field2>, ...
> **expect**: Structured Return Contract (status/artifacts_written/next_step_input/blockers/evidence)
```

- `input` 字段名；SubAgent 从 prompt 读实际值
- 固定路径（`docs/plans/*-srs.md` / `docs/templates/srs-template.md`）由 sub-skill 内部定位，不作 input
- 过程量走 `next_step_input`；仅 finalize 的 SRS / deferred 文档列入 `artifacts_written`

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 主 agent 读完整 SRS 草稿做审批 | 只读 artifacts 路径 + evidence |
| revise 无上限 | 2 轮封顶，第 3 轮 escalate |
| 用户反馈被主 agent 改写 | verbatim 拷贝到 Addendum |
| 合并多步 sub-skill 的审批 | 每步独立处理 |
| Addendum 重述完整任务 | 只附增量；原 prompt 由主 agent 保持幂等 |
