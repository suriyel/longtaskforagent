---
name: long-task-work
description: "当 feature-list.json 存在时使用 — 通过完整 TDD 流水线编排功能"
---

# Worker — 每周期一个功能

纯流程控制器。每步启动一个独立 SubAgent 加载并执行对应的学科 Skill，然后解析其结构化返回契约。

**启动时宣告：** "我正在使用 long-task-work skill。让我定位当前状态。"

## Step 1：Orient（内联）

- 在 `feature-list.json` 中 Grep `"status": "failing"` 的功能 — 跳过 `"deprecated": true`
- 按优先级、再按数组位置选取下一个
- **依赖检查**：验证所有 `dependencies[]` 的 `"status": "passing"`。若不满足 → 跳过，选下一个。若无可选功能 → 通过 `AskUserQuestion` 警告用户
- **恢复检查**：读取 `task-progress.md` `## Current State` 中的 `Pipeline:` 标记 — 若为同一 Feature #{id} 且步骤 > 1，跳转到该步骤；否则从 Step 2 开始
- 更新 `task-progress.md` `## Current State` 的流水线标记：
  ```
  Pipeline: Feature #{id} → Step 1 (Orient) → starting
  ```

## Step 2：Feature Design

> **DISPATCH** 创建独立 SubAgent（使用 General 或 Agent）args=`{id}` — 在 subagent 中加载并执行 skill `long-task:long-task-feature-design`

**解析：** 解析 SubAgent 返回文本（结构化返回契约）。
- Verdict PASS → 通过 `AskUserQuestion` 请用户批准设计文档。若有修正 → 重新分派一次。
- Verdict FAIL / BLOCKED / CLARIFY → 上报用户。

更新流水线标记：`Feature #{id} → Step 2 (Feature Design)`

## Step 3：TDD Red

> **DISPATCH** 创建独立 SubAgent（使用 General 或 Agent）args=`{id}` — 在 subagent 中加载并执行 skill `long-task:long-task-tdd-red`

**解析：** 所有测试失败（RED PASS） → 进入 Step 4。任何测试通过或框架错误 → 上报。
更新流水线标记：`Feature #{id} → Step 3 (TDD Red)`

## Step 4：TDD Green

> **DISPATCH** 创建独立 SubAgent（使用 General 或 Agent）args=`{id}` — 在 subagent 中加载并执行 skill `long-task:long-task-tdd-green`

**解析：** 所有测试通过且零回归 → 进入 Step 5。失败 → 上报。
更新流水线标记：`Feature #{id} → Step 4 (TDD Green)`

## Step 5：TDD Refactor

> **DISPATCH** 独立 SubAgent（使用 General 或 Agent）args=`{id}` — 在 subagent 中加载并执行 skill `long-task:long-task-tdd-refactor`

**解析：** 清洁（零违规，§11 合规） → 进入 Step 6。失败 → 上报。
更新流水线标记：`Feature #{id} → Step 5 (TDD Refactor)`

## Step 6：Persist（内联）

- 更新 `RELEASE_NOTES.md`（Keep a Changelog 格式；bugfix → `### Fixed`）
- 更新 `task-progress.md`：
  - `## Current State`：进度计数（X/Y passing），上次完成，下一功能
  - 追加会话条目：
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    ```
- 在 `feature-list.json` 中标记功能 `"status": "passing"`
- 验证：`python scripts/validate_features.py feature-list.json`

## Step 7：End Session

- 输出：**Feature #\<id\> (\<title\>) — DONE。** 下一个：Feature #\<next_id\> (\<next_title\>)
- 若无剩余 failing 且非 deprecated 的功能："所有活跃功能已通过 — 开发完成。"
- 结束会话 — **永远不要回退到 Step 1**

## 关键规则

- **每会话一个功能** — 外部 `scripts/auto_loop.py` 处理多功能
- **严格步骤顺序** — 不跳过、不重排
- **每步 = 启动独立 SubAgent → 加载学科 Skill → 返回结构化结果**
- **无新鲜证据不标记"passing"**
- **仅系统化调试** — 遇错时读 `references/systematic-debugging.md`；追踪根因
- **结束会话前更新进度**
- **永远不留下损坏的代码**

## 集成

**调用者：** using-long-task（当 feature-list.json 存在时）
**分派 SubAgent（严格顺序）：**
1. `long-task:long-task-feature-design`（Step 2）
2. `long-task:long-task-tdd-red`（Step 3）
3. `long-task:long-task-tdd-green`（Step 4）
4. `long-task:long-task-tdd-refactor`（Step 5）
**读写：** feature-list.json, task-progress.md, RELEASE_NOTES.md
