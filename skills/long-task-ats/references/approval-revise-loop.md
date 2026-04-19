# 审批-返工循环

ats-reviewer SubAgent 返回 Structured Return Contract 后，按本模板处理。

## 主循环

```
1. 组装 DISPATCH prompt 并分发 reviewer
2. 按 status 分支：
   blocked → AskUserQuestion 收 blockers（仅限输入文件不可读场景）→ Clarification Addendum 重分发（不计 revise）
   fail    → 读 evidence → Failure Addendum 重分发（计 revise）
   pass    → 进步骤 3（交叉引用冲突消费）
3. 交叉引用冲突消费（blockers 中所有 `[CROSS-REF CONFLICT]` 条目）：
   对每条冲突逐一 AskUserQuestion：
     A. 采用源文档值（修改 ATS）
     B. 采用 ATS 值（同步更新 SRS/Design）
     C. 两者都不正确（用户提供正确值）
   应用决定到相关文档；若 SRS/Design 被修改，单独 git commit（`docs: resolve ATS cross-reference conflicts per user decision`）
   记录到 ATS 附录表：`| Conflict # | Decision | Applied To | User Rationale |`
4. 审批关卡：向用户呈 ATS 草案（按节） + evidence + 已解决冲突摘要
   AskUserQuestion(approve / revise / escalate)
   approve  → 退出循环，进 Step 11 保存
   revise   → Revision Addendum 重分发 reviewer（计 revise）
   escalate → 中止循环，主 SKILL escalation 接管
```

## 关键差别（与 requirements 版本）

- **blockers 字段双语义**：`[CROSS-REF CONFLICT]` 条目不走 blocked 分支（reviewer 可能 `status: pass` 且 `blockers` 非空），走步骤 3 专用分支
- **纯 blocked 仅用于输入缺失**：SRS/Design/UCD 文件无法读取时 reviewer 才返 blocked
- **审批关卡始终启用**：ATS 是落盘文档，用户必须最终 approve

## revise 封顶

- 2 轮；第 3 次自动 escalate
- `blocked` 的 Clarification 不计数
- `fail` 的 Failure Addendum 计数
- 用户 revise 的 Revision Addendum 计数
- 升级告知：`AskUserQuestion("Revise limit reached after 2 rounds", options=[manual-fix, accept-known-gaps, abort])`
- 用户选 accept-known-gaps → 在 ATS 附录"已知缺口"节记录剩余 Major

## Addendum 组装

**Revision Addendum (round N)**
```
**Previous verdict**: <上一次 next_step_input.review_report_markdown 摘要>
**Why revised**: <用户反馈 verbatim>
**Rework instruction**:
- 仅针对上述反馈修订；保持未受反馈影响的 R 维度不变。
- 重用未被驳回的裁决；不要从零开始重审。
- 返回 Structured Return Contract（5 字段）。
```

**Clarification Addendum (from blocked)**
```
**Blockers you reported**: <blockers 列表>
**User-provided clarifications**:
1. <question>: <answer>
...
**Instruction**: 使用澄清作为权威输入继续评审；不要再以同一阻塞点返回 blocked。
```

**Failure Addendum (round N)**
```
**Failure evidence**: <evidence 逐行>
**Rework instruction**:
- 根据 evidence 的 Major 缺陷列表修复 ATS 对应章节。
- 修复完成后重新返回 Structured Return Contract。
- 证据不足以定位 → 作为 blocked 返回，附 `insufficient_evidence` 标记。
```

## DISPATCH 语法

```markdown
> **DISPATCH** → 创建独立 SubAgent（subagent_type=`long-task:ats-reviewer`），加载 `agents/ats-reviewer.md` 并执行 reviewer
> **input**: `ats_draft`, `srs_path`, `design_path`, `ucd_path`（可选）
> **expect**: Structured Return Contract (status/artifacts_written/next_step_input/blockers/evidence)
```

- `ats_draft`：当前待审 ATS 文档完整文本（未落盘）
- 固定路径（`docs/plans/*-srs.md` / `*-design.md` / `*-ucd.md`）由 reviewer 内部 glob 定位
- reviewer 不修改文件，`artifacts_written` 恒为 `[]`
- `review_report_markdown` 走 `next_step_input`；Step 11 保存时作为附录追加

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 主 agent 读完整 ATS 审核报告做审批 | 只读 `evidence`（3-5 行）+ `next_step_input.major_defect_count` |
| `[CROSS-REF CONFLICT]` 条目被主 agent 自动裁决 | 必须逐条 AskUserQuestion |
| revise 无上限 | 2 轮封顶，第 3 轮 escalate |
| 用户反馈被主 agent 改写 | verbatim 拷贝到 Addendum |
| 多个冲突合并一次 AskUserQuestion | 逐条提问（保留独立证据与决定） |
| 冲突解决后跳过审批关卡 | 冲突消费完仍必须走 approve / revise / escalate |
