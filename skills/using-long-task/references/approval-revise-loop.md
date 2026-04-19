# 审批-返工循环（Approval-Revise Loop · Worker 版）

> Worker phase skill（`long-task-work-design` / `long-task-work-tdd` / `long-task-work-st`）分发各自 SubAgent（feature-design / tdd-red/green/refactor / quality / feature-st）后按本模板处理返回。下表「来源 Step」列标注每个前缀适用的 phase。配合 `skills/using-long-task/references/structured-return-contract.md` 的 5 字段契约使用。

## 主 Agent 循环

```
1. 组装 DISPATCH prompt（仅传动态字段；固定路径由 sub-skill 自行定位）
2. 分发 SubAgent；接收 Structured Return Contract
3. 按 status 分支：

   status = blocked
     → 读 blockers[] 按前缀分流（见下方 Blockers 前缀约定）
     → AskUserQuestion 收集用户裁决
     → 组装 Clarification Addendum
     → 重分发（本轮不计入 revise 上限）
     → 回到步骤 3

   status = fail
     → 读 evidence 定位失败原因
     → 组装 Failure Addendum
     → 重分发（计入 revise 上限）
     → 回到步骤 3

   status = pass
     → 按本 Step 是否需要用户审批关卡分支：
       - feature-design（Step 4）：如 assumption_count == 0，可直接 approve；若 assumption_count > 0，进入审批关卡（用户决定是否接受 assumptions）
       - tdd（Step 5-7）：无审批关卡（契约校验在 Step 10 Inline Check）
       - quality（Step 8）：无审批关卡（pass 即进入 Step 9）
       - feature-st（Step 9）：无审批关卡（pass 即进入 Step 10）

4. 审批关卡（仅 feature-design with assumptions）：
     向用户呈示：
       - artifacts_written 路径（用户可 diff）
       - evidence ≤ 3 行
       - next_step_input 关键字段（assumption_count、test_inventory_count、existing_code_reuse_count）
     AskUserQuestion 四选一：approve / revise / skip-feature / escalate

5. 按审批结果分支：

   approve
     → 按 next_step_input 构造下一 Step 的 DISPATCH 输入
     → 退出循环进入下一 Step

   revise
     → verbatim 拷贝用户反馈至 Revision Addendum
     → 重分发（revise 计数 +1）
     → 回到步骤 3

   skip-feature  (Worker 特有)
     → 将 feature.status 保持 "failing"，在 task-progress.md 记录 skip 原因
     → 跳至下一个可执行 feature；本 feature 回到下次 Worker 循环
     → 退出本循环

   escalate
     → 中止本 feature 循环
     → task-progress.md 记录 escalation + 所有已产出 artifacts 路径
     → AskUserQuestion 让用户手工指引（修订 SRS、运行 long-task-increment、修订 feature 定义等）
```

## Blockers 前缀约定（status = blocked 时的分流）

主 agent 按 blockers[i] 的前缀决定 AskUserQuestion 组装策略：

| 前缀 | 来源 Step | 语义 | 建议 AskUserQuestion 选项 |
|------|-----------|------|--------------------------|
| `[SRS-VAGUE]` | feature-design | SRS 验收准则模糊（"fast" 等无阈值词） | (A) 用建议的具体阈值 / (B) 用户提供新阈值 / (C) 打回 SRS 侧（建议 `long-task-increment`） |
| `[SRS-DESIGN-CONFLICT]` | feature-design | SRS 与 Design §2.N 冲突 | (A) 以 SRS 为准（修设计） / (B) 以 Design 为准（改 SRS） / (C) 打回 |
| `[SRS-MISSING]` | feature-design / feature-st | 验收准则无 Given/When/Then | (A) 用户补齐 / (B) 假设并继续 / (C) 打回 SRS |
| `[ATS-MISMATCH]` | feature-design | ATS 类别要求但特性无可测表面 | (A) 添加该类别可观察行为 / (B) 豁免本 feature 该类别（留痕） / (C) 打回 ATS 侧 |
| `[ATS-BUGFIX-REGRESSION-MISSING]` | feature-design | bugfix feature 无 ATS 回归锚点 | (A) 用户补 ATS 映射行 / (B) 转为 core category 并补 srs_trace / (C) 显式豁免回归（需授权） |
| `[ATS-CATEGORY-MISSING-ST]` | feature-st | ATS 必须类别无对应 ST 用例 | (A) 补 ST 用例 / (B) 豁免本类别（需授权） |
| `[UCD-VAGUE]` | feature-design | UI 视觉要求无具体选择器/颜色 | (A) 用户补 UCD / (B) 假设并继续 |
| `[DEP-AMBIGUOUS]` | feature-design | §4 跨特性契约 schema 不全 | (A) 补 §4 schema（可能需 long-task-increment） / (B) 以本特性 best-guess 前行 |
| `[NFR-GAP]` | feature-design | NFR 无可度量阈值 | (A) 用户补阈值 / (B) 假设并继续 / (C) 打回 |
| `[CONTRACT-DEVIATION]` | feature-design | 发现 §4 契约技术不可行，需变更 | (A) 批准变更（主 agent 更新 Design §4） / (B) 坚持原契约（SubAgent 按原契约继续） |
| `[MANUAL_TEST_REQUIRED]` | feature-st | 需人工测试（缺凭据/物理设备/视觉判断） | 展示测试步骤，由用户手动执行并回报结果 |
| `[INSUFFICIENT_EVIDENCE]` | tdd / quality | SubAgent 无法从环境取得判定证据 | (A) 提供环境诊断 / (B) 转 escalate |
| `[ENV-ERROR]` | tdd / quality / feature-st | 环境/配置故障，已超 SubAgent 自修范围 | 展示故障详情，用户修复后回应"retry" |

> 前缀外的无前缀 blocker 按通用 blocked 处理：直接 AskUserQuestion(blockers[i]) 收集单行回答。

## 返工循环封顶

- **revise 默认上限：2 轮**。第 3 次触发 revise 时自动转为 escalate。
- **blocked 的 Clarification 不计数**（属于输入澄清，不是质量问题）。
- **fail 的 Failure Addendum 计入 revise 上限**（算同一质量闭环的一次返工）。
- **feature-design CLARIFY 子类**：同 blocked，不计数。
- 升级文案：`AskUserQuestion("Revise limit reached after 2 rounds for Step {N}. Switch to manual handling, skip feature, or abort session?", options=[manual, skip-feature, abort])`

## Revision Addendum 组装规则

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

**Blockers you reported**:
| # | 前缀 | 原 blocker | User resolution |
|---|------|-----------|-----------------|
| 1 | [SRS-VAGUE] | "<原文>" | "<用户回答>" (Authority: user-approved / assumed) |
| 2 | ... | ... | ... |

**Instruction**: 使用上述解决作为权威输入继续原任务；不要再以 blocked 状态返回同一阻塞点。若仍有新阻塞，使用新前缀继续返 blocked。
```

## Failure Addendum 组装规则（fail → 重分发）

```
## Failure Addendum (round N)

**Failure evidence**: <evidence 逐行>
**Rework instruction**:
- 定位并修复上述失败；不要推翻已通过的部分。
- 若证据不足以定位，作为 blocked 返回（前缀 [INSUFFICIENT_EVIDENCE]）。
```

## 审批呈现最小格式（feature-design only）

```
**Step 4 result from long-task-feature-design — Feature #{id} ({title})**

Artifacts written:
- docs/features/YYYY-MM-DD-<slug>.md

Evidence (from SubAgent):
- <evidence line 1>
- <evidence line 2>

Assumptions (<K>):
- <assumption 1 summary>
- <assumption 2 summary>

Next-step inputs:
- test_inventory_count: <N>
- existing_code_reuse_count: <M>

→ Please review the design doc (or via git diff), then choose:
  [approve] | [revise (add feedback)] | [skip-feature] | [escalate]
```

## 与 Structured Return Contract 的关系

- 本模板处理 4 个 Worker sub-skill 的 DISPATCH 返回（feature-design / tdd / quality / feature-st）。
- sub-skill **绝不**自行发起 AskUserQuestion —— 全部走 `status: blocked` + blockers[] 前缀约定。
- 本模板只在 pass 后根据 Step 是否需要审批关卡分支；blocked/fail 的通用处理由 `structured-return-contract.md` 定义，本模板补充 Addendum 组装与返工封顶。

## DISPATCH 语法（所有 Worker sub-skill 通用）

```markdown
> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:<sub-skill-name>`
> **input**: <field1>, <field2>, ...
> **expect**: Structured Return Contract (status/artifacts_written/next_step_input/blockers/evidence)
```

- `input` 字段名由 SubAgent 在其 prompt 中直接引用（无需 `=` 赋值；SubAgent 从自己的 prompt 读取实际值）
- 固定路径（`feature-list.json` / `docs/plans/*-design.md` 等）由 sub-skill 内部定位
- 过程量走 `next_step_input`（内存传递）；仅最终落盘文档列入 `artifacts_written`

## 反模式

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| sub-skill 内直接 AskUserQuestion | 破坏返工计数与 Addendum 机制 | 改 `status: blocked` + blockers[] 带前缀 |
| 主 agent 把 blockers 原样抛给用户 | 用户看不懂技术前缀 | 按前缀表组装 A/B/C 选项的 AskUserQuestion |
| 合并多 Step 的审批 | 一次失败回滚所有工作 | 每 Step 独立返回；各自触发自己的审批/返工 |
| CLARIFY 自成一个 status | 契约分叉，主 agent 需双路径处理 | 统一为 `blocked` + 合适前缀 |
| revise 无上限 | 无限循环风险 | 2 轮封顶；第 3 轮 escalate |
| 用户 revise 反馈被主 agent 重写 | 丢失用户原意 | verbatim 拷贝到 Addendum |
| 在 Addendum 中重新描述整个任务 | 上下文污染 | 只附 Addendum 增量；原 DISPATCH 输入保持幂等 |
