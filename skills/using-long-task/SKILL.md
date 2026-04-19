---
name: using-long-task
description: "Use when starting any session in a long-task project - routes to the correct phase skill based on project state"
---

<EXTREMELY-IMPORTANT>
你正处于一个 long-task 多会话项目中。在任何响应或行动之前（包括澄清问题），你必须先调用正确的阶段 skill。

如果某个阶段 skill 适用，你没有选择。你必须使用它。

这不可谈判。这不是可选的。你无法通过任何理性化来逃避它。
</EXTREMELY-IMPORTANT>

## 如何访问 Skill

```bash
python scripts/phase_route.py --json
```

按返回字段动作：

1. `ok == false` → 呈 `errors` 给用户停。
2. `needs_migration == true` → 先运行：
   ```bash
   python scripts/migrate_sub_status.py feature-list.json
   git add feature-list.json && git commit -m "chore: migrate feature-list to sub_status schema"
   ```
   然后重跑 `phase_route.py`。
3. `next_skill` 非空 → 用 Skill 工具直接调用对应 skill。
4. `next_skill == null` 且 `counts.total == 0` → 提示用户 feature-list 无活跃特性，可能需要 `long-task-increment`。

**Fallback**（`phase_route.py` 因任何原因不可用时）：按顺序 glob，命中即路由：
- `bugfix-request.json` → `long-task-hotfix`
- `increment-request.json` → `long-task-increment`
- `feature-list.json` → 读 `features[*].sub_status`，按最小 id 活跃特性取阶段：`design_pending` → `long-task-work-design`；`tdd_pending` → `long-task-work-tdd`；`st_pending` → `long-task-work-st`；全部 `done` → `long-task-st`
- `docs/plans/*-ats.md` → `long-task-init`
- `docs/plans/*-design.md` → `long-task-ats`
- `docs/plans/*-ucd.md` → `long-task-design`
- `docs/plans/*-srs.md` → `long-task-ucd`
- `docs/rules/*.md` → `long-task-requirements`
- 否则 → `long-task-requirements`（若源文件 > 3 且 git commits ≥ 5，先 `long-task-brownfield-scan`）

## 红旗信号

出现这些想法意味着停下——你在理性化逃避：

| 想法 | 现实 |
|---------|---------|
| "先看一下代码吧" | 先调用阶段 skill。它会告诉你如何定位。|
| "我知道该做哪个特性" | Worker skill 有 Orient 步骤。照着走。|
| "这个特性简单，跳过 TDD" | long-task-tdd 不可协商。|
| "测试通过了，可以标记完成" | 必须先通过 long-task-quality 关卡。|
| "我记得工作流" | Skill 在演化。通过 Skill 工具加载当前版本。|
| "我需要先获取更多上下文" | Skill 检查先于探索。|
| "先做这一件事再说" | 做任何事之前先检查。|
| "需求很明显，直接到设计" | long-task-requirements 会捕捉你会遗漏的内容。|
| "测试分类可以在 feature-st 期间决定" | 临时指派会导致 SEC/PERF 缺口。先运行 ATS。|
| "ATS 对这个项目来说过头了" | 查阅 Scaling Guide —— 微型项目会自动跳过 ATS。|
| "SRS 已经暗含了设计" | SRS = WHAT，design = HOW。两者都必需。|
| "UI 样式可以在编码期间决定" | 临时造型会导致不一致。先运行 UCD。|
| "这个 UI 太简单不需要样式指南" | 即便简单 UI 也需要 token。UCD 可以很轻量。|
| "所有特性都过了，可以发布" | 特性测试 ≠ 系统测试。先运行 ST 阶段。|
| "系统测试过头了" | 集成 bug、NFR 失败、工作流缺口会藏到 ST 才暴露。|
| "我直接往 JSON 里加特性就行了" | 调用 `long-task-increment` skill 进行可追踪、可审计的变更。|
| "需求变更很小，不需要影响评估" | Increment skill 会捕捉隐藏依赖。|
| "我直接把这个小 bug 修了吧" | 调用 `long-task-hotfix` —— bug 会被记录到 feature-list.json 为 category=bugfix，并走完整 Worker 流水线修复。|
| "Worker 期间生成示例吧" | 示例在 ST 之后通过 long-task-finalize 生成。|
| "我已经了解项目的约定了" | 运行 codebase-scanner（由 `long-task-brownfield-scan` 分派）。隐性知识不跨会话持久化。2/3方件约束很容易被漏掉。|
