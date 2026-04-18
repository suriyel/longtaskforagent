---
name: long-task-work
description: "Thin router — reads feature-list.json sub_status and delegates to the correct phase skill (design/tdd/st). Use when user invokes work without knowing which phase is next."
---

# Worker Router

本 skill 是**薄路由壳**：读取 `feature-list.json` 的子状态分布，决定把用户引导到哪一个阶段 skill。不做任何实际工作，一切由被路由到的 phase skill 在**同一会话**内承接。

> **自 2026-04 重构**：原 `long-task-work` 的 11 个 Step 已拆分到 3 个 top-level 阶段 skill：
> - `long-task-work-design`（Feature Design）
> - `long-task-work-tdd`（TDD + Quality Gates）
> - `long-task-work-st`（Feature-ST + Inline Check + Persist）
>
> 原因：SubAgent 嵌套受限；跨会话 phase 边界天然切断上下文污染；每阶段独立重读 feature design 保证一致性。详见 `docs/skill-subagent-refactor-lessons.md`。

## 路由算法

### 1. Schema 兼容检查
```bash
python scripts/validate_features.py feature-list.json
```
Exit ≠ 0 → 停。要求用户修 feature-list.json。

### 2. 检查 sub_status 是否已迁移
若 `feature-list.json` 中**任一非 deprecated 特性缺 `sub_status` 字段**（或输出含 `no_sub_status=N` 且 N>0）：

```bash
python scripts/count_pending.py feature-list.json
```

若 `no_sub_status > 0` → 运行迁移（幂等，安全）：
```bash
python scripts/migrate_sub_status.py feature-list.json
python scripts/validate_features.py feature-list.json   # 验收迁移
git add feature-list.json
git commit -m "chore: migrate feature-list to sub_status schema"
```

### 3. 按 sub_status 分桶路由

读 `python scripts/count_pending.py feature-list.json --json` 输出。按**以下优先级**选一个 phase skill，用 Skill 工具调用（不是 Agent SubAgent——phase skill 必须在主 agent 上下文运行）：

| 条件 | 路由到 |
|-----|-------|
| `design > 0` | `long-task-work-design` |
| else `tdd > 0` | `long-task-work-tdd` |
| else `st > 0` | `long-task-work-st` |
| else `total == done` 且 `done > 0` | `long-task-st`（系统级 ST）|
| else `total == 0` | 提示用户：feature-list 无活跃特性，检查是否需要 `long-task-increment` 或项目已完成 |

**设计动机（优先级为什么这样排）**：同一批 wave 中，design 阶段通常先于 tdd；优先推进阶段靠前的特性可让 TDD/ST 阶段有更多并行对象。如需按特性 id 而非阶段优先，用户可手动调用具体 phase skill。

### 4. 交接

调用选定的 phase skill（通过 Skill 工具）。phase skill 在**本会话内**完成其职责并在末尾输出会话终止横幅——届时用户看到提示后开启新会话，router 再次选路由。

**禁止**：本 router 不得在一次调用里连串调多个 phase skill。每次调用只路由一次。

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "feature-list.json 没有 sub_status 我就手动填" | 用 `migrate_sub_status.py`。手填违反单源。|
| "我想同时做 design 和 tdd" | 不行。每会话一阶段一特性。|
| "sub_status=done 但 status=failing 我忽略" | `validate_features.py` 会拦下。修复一致性或退回迁移。|
| "这个特性我想跳到 st 阶段" | 手动改 sub_status=st_pending + `validate_features.py`（会报错若 status 不一致）；更安全：回 tdd 补齐。|

## 参考

- 阶段 skill：`skills/long-task-work-design/SKILL.md` / `skills/long-task-work-tdd/SKILL.md` / `skills/long-task-work-st/SKILL.md`
- 结构化返回契约：`references/structured-return-contract.md`（保留给 phase skill 复用）
- 审批循环：`references/approval-revise-loop.md`（保留给 phase skill 复用）
- 系统化调试：`references/systematic-debugging.md`
- SubAgent 开发：`references/subagent-development.md`
- Worktree 隔离：`references/worktree-isolation.md`
- 重构经验：`docs/skill-subagent-refactor-lessons.md`
