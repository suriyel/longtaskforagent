---
name: using-long-task
description: "在 long-task 项目中启动会话时使用 — 通过 scripts/phase_route.py 路由到正确的阶段 skill"
---

<EXTREMELY-IMPORTANT>
你正处于 long-task 多会话项目中。你必须在任何响应或操作之前（包括澄清问题）调用正确的阶段 skill。

如果某个阶段 skill 适用，你没有选择。你必须使用它。

这不可协商。不是可选的。你无法通过合理化来绕过它。
</EXTREMELY-IMPORTANT>

## 如何路由

```bash
python scripts/phase_route.py --json
```

按返回字段动作：

1. `ok == false` → 呈 `errors` 给用户停（常见：依赖环、`current` 校验失败，需人工修 `feature-list.json`）
2. `next_skill` 非空 → 用 Skill 工具直接调用对应 skill（Worker 阶段 skill 会自行重调 router 拿 `feature_id` 与 `starting_new`，无需透传参数）
3. `next_skill == null` 且 `counts.total == 0` → 提示用户 feature-list 无活跃特性，可能需要 `long-task-increment`
4. `next_skill == null` 且 `counts.passing == counts.total` → 所有活跃特性已 passing，项目开发完成

**Fallback**（`phase_route.py` 因任何原因不可用时，按顺序 glob 命中即路由）：
- `bugfix-request.json` → `long-task-hotfix`
- `increment-request.json` → `long-task-increment`
- `feature-list.json` → 读根 `current`：`phase=design` → `long-task-work-design`；`phase=tdd` → `long-task-work-tdd`；`current=null` 且有 failing → 告诉用户修复 `phase_route.py`（需 router 挑下一个 feature）；`current=null` 且全 passing → 项目完成
- `docs/plans/*-design.md` → `long-task-init`
- `docs/plans/*-srs.md` → `long-task-design`
- `docs/rules/*.md` → `long-task-requirements`
- 否则 → `long-task-requirements`（若源文件 > 3 且 git 提交 ≥ 5，先 `long-task-codebase-scanner`）

## 如何访问 Skill

使用 `Skill` 工具按名称调用 skill（如 `long-task:long-task-work-tdd`）。调用后 skill 内容会加载并呈现给你 — 直接遵循即可。永远不要用 Read 工具读取 skill 文件。

## Skill 目录

### 阶段 Skill（由 router 决策调用）

| Skill | 阶段 | 触发 |
|-------|-----|-----|
| `long-task:long-task-hotfix` | 热修复 | `bugfix-request.json` 存在（最高优先级） |
| `long-task:long-task-increment` | Phase 1.5 | `increment-request.json` 存在 |
| `long-task:long-task-codebase-scanner` | Phase 0-pre | 存量项目无 `docs/rules/` |
| `long-task:long-task-requirements` | Phase 0a | 无 SRS 且无设计 |
| `long-task:long-task-design` | Phase 0b | 有 SRS 无设计 |
| `long-task:long-task-init` | Phase 1 | 有设计无 feature-list.json |
| `long-task:long-task-work-design` | Phase 2a | `current.phase=design` 或 router 新挑特性 |
| `long-task:long-task-work-tdd` | Phase 2b | `current.phase=tdd` |

### 学科 Skill（由 work-design / work-tdd 作为 SubAgent 调用）

| Skill | 用途 |
|-------|-----|
| `long-task:long-task-feature-design` | 接口契约 + 实现摘要 + 测试清单 |
| `long-task:long-task-tdd-red` | 为测试清单写失败测试 |
| `long-task:long-task-tdd-green` | 最小实现使测试通过 |
| `long-task:long-task-tdd-refactor` | 清理 + 静态分析 + §11 合规 |

### 独立 Skill（无流水线依赖）

| Skill | 触发 |
|-------|-----|
| `long-task:long-task-explore` | `/deep-explore [quick\|standard\|deep]` |
| `long-task:long-task-coverage-retrofit` | `/coverage-retrofit [options]` |
| `long-task:long-task-mutation-retrofit` | `/mutation-retrofit [options]` |

## 关键文件（共享契约）

| 文件 | 角色 |
|------|------|
| `docs/plans/*-srs.md` | 已批准的 SRS — WHAT |
| `docs/plans/*-deferred.md` | 延迟需求积压 — 下轮通过 increment 拾取 |
| `docs/plans/*-design.md` | 已批准的设计 — HOW |
| `feature-list.json` | 任务清单 + 根级 `current` 锁 — 核心共享状态 |
| `task-progress.md` | `## Current State` + 逐会话日志 |
| `long-task-guide.md` | 项目专属 Worker 指南 |
| `RELEASE_NOTES.md` | 持续更新的变更日志 |
| `bugfix-request.json` | 信号文件 — 触发热修复（处理后删除） |
| `increment-request.json` | 信号文件 — 触发增量需求（处理后删除） |
| `docs/rules/*.md` | 代码库约定 — 仅存量项目 |
| `docs/features/<id>-<slug>.md` | 每特性详细设计（由 `scripts/feature_paths.py` 派生路径） |

## Feature List Schema

```json
{
  "project": "name",
  "created": "YYYY-MM-DD",
  "tech_stack": { "language": "...", "test_framework": "...", "coverage_tool": "...", "mutation_tool": "..." },
  "single_round": false,
  "waves": [{ "id": 0, "date": "YYYY-MM-DD", "description": "..." }],
  "constraints": ["..."],
  "assumptions": ["..."],
  "current": { "feature_id": 3, "phase": "design" } | null,
  "features": [
    {
      "id": 1, "wave": 0, "category": "core|bugfix",
      "title": "...", "description": "...", "priority": "high|medium|low",
      "status": "failing|passing",
      "srs_trace": ["FR-001"],
      "dependencies": [],
      "deprecated": false,
      "bug_severity": "...", "root_cause": "...", "fixed_feature_id": null
    }
  ]
}
```

**`current` 语义**：
- `current=null` + 有 failing 特性 → router 挑下一个 dep-ready 特性，work-design 原子写入 `current`
- `current={feature_id, phase: "design"|"tdd"}` → router 锁定该特性的该阶段，分发对应 phase skill
- `current=null` + 全部 passing → 项目开发完成

## 危险信号

| 想法 | 现实 |
|------|------|
| "让我先看看代码" | 先调 router。它告诉你如何定向。 |
| "我知道该做哪个功能" | Worker skill 自己调 router 锁。遵循它。 |
| "这个功能很简单，跳过 TDD" | work-tdd 不可协商。 |
| "测试通过了，可以标记完成" | Refactor 必须先通过。 |
| "我记得工作流" | Skill 会演进。通过 Skill 工具加载当前版本。 |
| "需求很明显，跳到设计" | long-task-requirements 能捕获你遗漏的。 |
| "我直接在 JSON 里加功能就行" | 调 `long-task-increment`。 |
| "我直接快速修这个 bug" | 调 `long-task-hotfix`。 |
| "work-design 后顺便做 TDD" | 终止会话。TDD 是新会话的 work-tdd。 |
| "手工改 `current` 跳过 design" | `feature_paths.py --must-exist` 会让 work-tdd BLOCKED；老实走 design。 |

## 共享 References

- `references/architecture.md` — 阶段流水线全景
- `references/systematic-debugging.md` — 系统化调试（phase skill 引用）
- `references/subagent-development.md` — SubAgent 开发指南（phase skill 引用）
- `references/worktree-isolation.md` — worktree 多版 TDD 指导（work-tdd 引用）
