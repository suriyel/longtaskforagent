---
name: long-task-work
description: "Thin router — reads feature-list.json sub_status and delegates to the correct phase skill (design/tdd/st). Use when user invokes work without knowing which phase is next."
---

# Worker Router

`using-long-task` 已通过 `scripts/phase_route.py` 路由到具体 phase skill；若用户直接入本 skill：

```bash
python scripts/phase_route.py feature-list.json --json
```

按返回字段动作：

1. `ok == false` → 呈 `errors` 给用户停。
2. `needs_migration == true` → 运行 `migrate_sub_status.py` + commit，重跑。
3. `next_skill` 非空 → 用 Skill 工具调用（规则：design_pending>0 → work-design；否则 tdd_pending>0 → work-tdd；否则 st_pending>0 → work-st；否则全 done → `long-task-st`）。
4. `next_skill == null` 且 `counts.total == 0` → 提示用户 feature-list 无活跃特性，可能需要 `long-task-increment`。

> **自 2026-04 重构**：原 11 个 Step 已拆分到 3 个 top-level 阶段 skill（`long-task-work-design` / `long-task-work-tdd` / `long-task-work-st`）。理由：SubAgent 嵌套受限；跨会话 phase 边界天然切断上下文污染；每阶段独立重读 feature design 保证一致性。详见 `docs/skill-subagent-refactor-lessons.md`。
