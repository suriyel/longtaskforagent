---
name: long-task-work-tdd
description: "Use when router emits next_skill=long-task-work-tdd — run TDD Red-Green-Refactor on current locked feature, mark feature passing, then terminate session"
---

# Worker — 阶段 B：TDD Red / Green / Refactor

每会话处理**一个特性**的 TDD 三段循环。完成后**清空 `current`** 并**把特性标为 `passing`**、**终止会话**。

**启动时宣告：** "我正在使用 long-task-work-tdd skill。让我定位当前状态。"

Red / Green / Refactor 三个独立 SubAgent 由本 skill 直接用 Agent 工具 DISPATCH；各自返回结构化契约后本层汇总并进入 Persist。

**多版 TDD**：若用户想跑另一版，TDD 结束后在新 worktree 手工把 `current` 重置为 `{feature_id: X, phase: "tdd"}` + 对应 feature `status: "failing"`，再开新会话即可。指导见 `../using-long-task/references/worktree-isolation.md`。

## Step 1：Orient

- 调 `python scripts/phase_route.py --json`，读 `next_skill` / `feature_id` / `starting_new` / `ok`
  - `ok == false` → 呈 `errors` 并终止会话
  - `next_skill != "long-task-work-tdd"` → AskUserQuestion 升级
  - `starting_new == true` → AskUserQuestion 升级（TDD 阶段不应是新 feature 的入口；状态机错位）
- `target_feature` = `feature-list.json` 中 `id == feature_id` 的条目
- **硬前置**：调 `python scripts/feature_paths.py design-doc --feature <id> --must-exist`
  - exit 非 0 → BLOCKED：`Feature design doc not on disk for #<id>; current.phase inconsistent with disk state. Resume design phase or reset current.phase to "design".` 终止会话
  - exit 0 → 记录 design_doc_path（**不读全文**，**不向主 agent 传路径**；sub-skill 自调脚本派生）
- `git log --oneline -10` 取最近 commit 上下文
- 在 `task-progress.md` 当前特性标题下记录 `target_feature.id` / `title`

## Step 2：TDD 三段 DISPATCH

**2a. Red — DISPATCH SubAgent**

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-tdd-red`
> **input**：`feature_id`
> **expect**：结构化返回契约；所有测试失败（RED PASS）

**返回处理**：
- 所有测试失败且退出码非零 → 进入 2b
- 任一测试通过或框架错误 → Failure Addendum 重分派一次；仍 FAIL → 呈用户升级

**2b. Green — DISPATCH SubAgent**

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-tdd-green`
> **input**：`feature_id`
> **expect**：结构化返回契约；所有测试通过 + 零回归

**返回处理**：
- PASS → 进入 2c
- FAIL（个别测试仍失败） → Failure Addendum 重分派，累计 2 轮仍未过 → 呈用户
- BLOCKED（契约不可实现等设计侧偏差） → 呈用户裁决：是否回退到 design 阶段

**2c. Refactor — DISPATCH SubAgent**

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-tdd-refactor`
> **input**：`feature_id`
> **expect**：结构化返回契约；静态分析 0 违规 + §11 合规 + 测试仍通过

**返回处理**：
- PASS → 进入 Step 3
- FAIL（静态违规未清） → Failure Addendum 重分派，累计 2 轮仍未过 → 呈用户
- BLOCKED → 呈用户

## Step 3：Persist & End Session

**3a. 翻转 `current` + 标记特性 passing**：
编辑 `feature-list.json`：
- 根 `current` 设为 `null`
- `features[id==<id>].status` 从 `"failing"` 改为 `"passing"`

**3b. 更新 `RELEASE_NOTES.md`**（Keep a Changelog 格式；`category="bugfix"` → `### Fixed`；否则 → `### Added`）

**3c. 更新 `task-progress.md`**：
```
## Current State
Progress: X/Y · Last: Feature #<id> <title> · Next: (see count_pending)

### Feature #<id>: <title> — PASS
- Completed: <YYYY-MM-DD>
- TDD: green ✓ (R-G-R complete)
- current: cleared
```

**3d. 校验**：
```bash
python scripts/validate_features.py feature-list.json
```

**3e. git commit**（测试 + 实现 + feature-list.json + task-progress.md + RELEASE_NOTES.md）：
```bash
git add <test-files> <impl-files> feature-list.json task-progress.md RELEASE_NOTES.md
git commit -m "feat: feature #<id> <slug> — tests green, refactored"
```

**3f. 输出会话终止横幅**：
```
## Phase TDD Complete for Feature #<id> (<title>)

- feature.status: failing → passing
- current: cleared
- Next: new session — router picks next failing feature OR all done
- Quick status: python scripts/count_pending.py feature-list.json

**Please start a new Claude Code session to continue.**

[End of session — DO NOT proceed to next feature in this session]
```

**禁止**：本会话绝不继续挑下一个 feature。每次迭代一个新会话。

## 关键规则

- **每会话一个特性的一个阶段** —— 本阶段只做 R-G-R；完成即终止
- **R / G / R 三个 SubAgent 不可协商** —— 本 skill 必须用 Agent 工具分别 DISPATCH，不在主 agent 内联执行
- **无新鲜证据不得标记 passing** —— 测试必须实跑绿，静态分析必须 0 违规
- **feature design 文档必须存在** —— 缺失即 BLOCKED 终止；主 agent 不读全文、不传路径；sub-skill 自调 `scripts/feature_paths.py` 派生
- **遇错系统化调试** —— 读 `../using-long-task/references/systematic-debugging.md`
- **worktree 多版** —— 读 `../using-long-task/references/worktree-isolation.md`

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "测试通过就推进" | 还要过 Refactor + 静态分析 + §11 合规。|
| "静态分析警告忽略" | Refactor SubAgent 内部已关卡；此处视为漏判，重分派。|
| "feature design 不对，我自己改" | 不改。BLOCKED 呈用户，建议回退 design 或 `long-task-increment`。|
| "顺便挑下一个 feature" | 终止。下一会话由 router 挑。|
| "把三个 SubAgent 合成一个省事" | 不。R/G/R 独立沙箱各返契约；合并污染证据边界。|
