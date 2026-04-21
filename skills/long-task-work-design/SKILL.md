---
name: long-task-work-design
description: "Use when router emits next_skill=long-task-work-design — produce per-feature detailed design document, advance current.phase, then terminate session"
---

# Worker — 阶段 A：Feature Design

每会话处理**一个特性**的详细设计产出。完成后**推进 `current.phase: design → tdd`** 并**终止会话**，等用户开新会话进入 TDD。

**启动时宣告：** "我正在使用 long-task-work-design skill。让我定位当前状态。"

**核心原则**：Feature Design 子步骤在**独立 SubAgent** 中运行（`long-task-feature-design`）。主 agent 仅分发并消费其结构化返回契约。

## Step 1：Orient

- 调 `python scripts/phase_route.py --json`，读 `next_skill` / `feature_id` / `starting_new` / `ok`
  - `ok == false` → 把 `errors` 呈给用户，终止会话
  - `next_skill != "long-task-work-design"` → 用 AskUserQuestion 升级（调用链错位）
  - `feature_id == null` → 终止会话（路由判定无可做特性）
- `target_feature` = `feature-list.json` 中 `id == feature_id` 的条目
- **若 `starting_new == true`**（router 新挑了一个 feature）：**原子写入** `feature-list.json` 的 `current = {"feature_id": <id>, "phase": "design"}`，然后：
  ```
  git add feature-list.json
  git commit -m "chore(current): start feature #<id> design"
  ```
  再进入后续读取。Router 已保证依赖满足，此处不再重复挑选。
- 读取：
  - `docs/rules/*.md`（如存在）—— 代码库约定约束
  - 注：SRS / Design 的**全量读取**由下游 `long-task-feature-design` SubAgent 自调
    `scripts/feature_paths.py srs-doc` / `system-design-doc` / `design-doc` 三子命令
    派生路径后单次全量 Read；主 agent **不读全文、不传片段、不传路径**
- 在 `task-progress.md` 当前特性标题下记录：`target_feature.id` / `title`

## Step 2：DISPATCH Feature Design SubAgent

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-feature-design`
> **input**：`feature_id`
> **expect**：SubAgent 自调 `scripts/feature_paths.py srs-doc / system-design-doc / design-doc --feature <id>` 派生三条路径，分别**单次全量 Read** SRS 与 Design，写入 `docs/features/<id>-<slug>.md`（含 §全局约束摘录 + §静态分析与质量工具命令 两沉淀章节）；返回结构化契约

> **对 `category: "bugfix"` 特性**：feature-design SubAgent 精简模式，聚焦根因记录 + 定向修复 + 回归测试清单。

**返回处理**：
- Verdict `PASS` → 通过 `AskUserQuestion` 请用户审批设计文档（A 批准 / B 修订 / C 放弃）。若 B → Clarification Addendum 重分派一次；累计 2 轮仍未过 → 呈聚合证据给用户升级
- Verdict `FAIL` / `BLOCKED` / `CLARIFY` → 把 SubAgent 的 Issues / Ambiguities 呈给用户，按其回答组装 Clarification Addendum 重分派；同一前缀 3 次 blocked → 自动升级

## Step 3：Persist & End Session

**3a. 推进 `current.phase`**：
编辑 `feature-list.json`，把根 `current.phase` 从 `"design"` 改为 `"tdd"`。保持 `current.feature_id` 与 `target_feature.status: "failing"` 不变。

**3b. 更新 `task-progress.md`**：在当前特性标题下追加：
```
- Design: DONE (docs/features/<id>-<slug>.md)
- current.phase: design → tdd
```

**3c. 校验**：
```bash
python scripts/validate_features.py feature-list.json
```

**3d. git commit**（含设计文档 + feature-list.json + task-progress.md）：
```bash
FDP=$(python scripts/feature_paths.py design-doc --feature <id>)
git add "$FDP" feature-list.json task-progress.md
git commit -m "design: feature #<id> <slug> — current.phase → tdd"
```

**3e. 输出会话终止横幅**（强制格式）：
```
## Phase Design Complete for Feature #<id> (<title>)

- current.phase: design → tdd
- Next: long-task-work-tdd in a NEW session
- Quick status: python scripts/count_pending.py feature-list.json

**Please start a new Claude Code session to continue.**

[End of session — DO NOT proceed to TDD in this session]
```

**禁止**：本会话绝不继续调 `long-task-work-tdd`。`auto_loop.py` 在外部处理跨阶段串联，每次迭代都是新鲜上下文。

## 关键规则

- **每会话一个特性的一个阶段** —— 本阶段只产出设计文档，不做 TDD
- **SubAgent 不可协商** —— `long-task-feature-design` 必须通过 Skill 工具分发
- **推进 `current.phase` 前必须校验** —— `validate_features.py` 必须 PASS
- **SRS/Design 模糊不得假设** —— SubAgent 返 BLOCKED → 组装 Clarification Addendum
- **遇错系统化调试** —— 读 `../using-long-task/references/systematic-debugging.md`；追根因不猜

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "顺便把 TDD 也做了" | 终止会话。TDD 是下一会话的 work-tdd。 |
| "SRS 模糊但我就假设……" | SubAgent 返 BLOCKED → Clarification Addendum |
| "这个特性简单，跳过 Feature Design 直接 TDD" | 不可绕过。每特性都要。 |
| "推进 current.phase 忘了校验" | 先 `validate_features.py`，再 commit。 |
