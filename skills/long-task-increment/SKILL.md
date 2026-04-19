---
name: long-task-increment
description: "Use when increment-request.json exists - collect incremental requirements, perform impact analysis, update design, and decompose new features"
---

# 增量需求开发

在已交付项目中新增/修改/弃用需求。所有变更原地写回既有 SRS/Design/ATS/UCD（git 历史即审计轨迹），新特性以批次元数据追加到 `feature-list.json`。Step 3/4/4b/5/6 分发到 sub-skill SubAgent 执行；主 agent 仅保留 orchestration + 用户交互。

**开始时声明：** "I'm using the long-task-increment skill. Let me orient on the current project state before collecting new requirements."

## 前置条件

- `feature-list.json` 存在
- `increment-request.json` 存在

## 共享资产

- **返回契约**：`skills/using-long-task/references/structured-return-contract.md`
- **审批-返工循环**：`references/approval-revise-loop.md`（approve / revise / escalate；2 轮封顶；Addendum 组装）
- **brownfield 适配**：`references/brownfield-adaptation.md`（§A 在 Step 1；§B/C 在 Step 2；§D/E/F 由 sub-skill 内部加载）

## 清单

为每步创建 TodoWrite 任务并顺序完成。

### 1. Orient

- 读 `increment-request.json` / `feature-list.json` / SRS / Design / ATS / UCD / `task-progress.md`
- `git log --oneline -10`
- 当前批次号 = `max(wave) + 1`（无 wave 默认 1）
- **构建 ESI**：按 `references/brownfield-adaptation.md` §A，证据源 = `docs/explore/codebase-research.md`（若存在）+ `env-guide.md` §4 + Design §4 + 已通过特性。ESI 摘要传给 Step 3 / Step 6。

### 2. 需求 elicitation（主 agent，需多轮 AskUserQuestion）

1. `AskUserQuestion` 按轮次收集（每轮 2-4 题）
2. EARS 模板：Ubiquitous / Event-driven / State-driven / Unwanted / Optional
3. 分配唯一 ID，衔接现有 SRS
4. 每条写 Given/When/Then 验收标准
5. 8 大质量属性校验：Correct、Unambiguous、Complete、Consistent、Ranked、Verifiable、Modifiable、Traceable
6. 归类：**NEW / MODIFY / EXTEND / DEPRECATED**
7. **Brownfield 过滤**（依 §B/§C）：ESI 已确立且用户未要求变更 → 归 REUSE，移出 FR 清单，作为 ASM-xxx 追加到 SRS §1.4

**产出 `new_reqs` 列表**（含 id / ears_stmt / change_type / affects_req_id / acceptance_criteria），作为 Step 3/4/6 输入。

### 3. 影响评估

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-impact`
> **input**: `new_reqs`, `wave`, `brownfield_esi`
> **expect**: Structured Return Contract；`next_step_input` 含 `impact_matrix` / `api_changes` / `hard_impact_ids` / `soft_impact_ids` / `deprecated_ids` / `new_reqs_needing_features` / `breaking_contracts`

按 `references/approval-revise-loop.md` 处理。用户须同时批准 **影响矩阵** 与 **API 影响表**；`next_step_input` 供后续 Step 复用。

### 3.5. 针对性代码库探索（条件触发，非阻塞）

**触发**：`impact_matrix` ≥ 1 条 Hard Impact **且** 项目有源码。
**跳过**：仅新增无代码依赖；或仅弃用。

| 信号 | 深度 |
|---|---|
| 1-2 Hard + 单模块 | quick |
| 3-5 Hard 或跨模块 | standard |
| 6+ Hard 或级联 ≥ 2 层 | deep |

不确定省略 `--depth` 交由 explore 自检。从 Hard Impact 特性提取 `srs_trace` / `dependencies` 作为 focus。explore 返回 BLOCKED 或无发现则正常进入 Step 4。

### 4. 设计修订

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-design`
> **input**: `new_reqs`, `impact_matrix`, `api_changes`, `breaking_contracts`
> **expect**: Structured Return Contract；`next_step_input` 含 `design_sections_changed` / `new_contracts` / `modified_contracts` / `env_guide_touched_sections`；若 env-guide.md §3/§4 被改，`blockers` 含 `env-guide-approval-pending`

按 `references/approval-revise-loop.md` 处理。`blockers` 含 `env-guide-approval-pending` → `AskUserQuestion` 呈 env-guide.md diff，要求用户审阅并更新 frontmatter `approved_by` / `approved_date` / `approved_sections`。批准后 git commit。

### 4b. ATS 修订

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-ats`
> **input**: `new_reqs`, `new_contracts`, `modified_contracts`
> **expect**: Structured Return Contract；`next_step_input` 含 `mapping_rows_added/modified/deprecated` / `new_categories` / `needs_reviewer_rerun`（或 `skipped: true`）

按 `references/approval-revise-loop.md` 处理。`needs_reviewer_rerun: true` 时审批通过后额外触发 `ats-reviewer` SubAgent（`agents/ats-reviewer.md`）。批准后 git commit。

### 5. UCD 修订

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-ucd`
> **input**: `ui_reqs`（从 `new_reqs` 过滤 ui 相关子集）
> **expect**: Structured Return Contract；`next_step_input` 含 `components_added/modified/deprecated` / `tokens_changed`（或 `skipped: true`）

按 `references/approval-revise-loop.md` 处理。批准后 git commit。

### 6. SRS 更新与特性分解

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-srs`
> **input**: `new_reqs`, `impact_matrix`, `api_changes`, `wave`, `brownfield_esi`
> **expect**: Structured Return Contract；`next_step_input` 含 `new_feature_ids` / `modified_feature_ids` / `soft_touched_feature_ids` / `deprecated_feature_ids` / `wave`；`evidence` 须含 `validate_features.py: OK`

按 `references/approval-revise-loop.md` 处理。`status: fail`（通常因 `validate_features.py` 不过）→ revise 循环。批准后 git commit：
```
feat: increment wave N — <scope>

New features: <ids>  Modified: <ids>  Deprecated: <ids>
```

### 7. 更新辅助文件

- `long-task-guide.md`：引入新工具/框架/模式 → 更新；`python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json` 重校验
- `init.sh` / `init.ps1`：新增依赖 → 更新 bootstrap（幂等）
- `.env.example`：新增 `env` 类型 `required_configs` → 追加模板行
- `scripts/check_configs.py`：新增 `required_configs` → 重新生成项目专用检查器

### 8. 收尾

1. 删除 `increment-request.json`
2. 最终校验：`python scripts/validate_features.py feature-list.json`
3. Git commit 所有变更
4. 更新 `task-progress.md`（**不写 `## Current State` 进度条——单一事实源是 `feature-list.json`**）：
   - 追加会话记录：
     ```
     ## Session N — Increment Wave M
     - **Date**: YYYY-MM-DD
     - **Phase**: Increment
     - **Scope**: <from increment-request.json>
     - **Changes**: Added N, modified M, deprecated K
     - **Documents updated**: SRS, Design, [ATS], [UCD]
     ```
5. 在 `RELEASE_NOTES.md` `[Unreleased]` 下更新
6. Git commit 进度文件：
   ```
   chore: update progress for increment wave N
   ```

路由随后检测到 failing 特性，自动进入 Worker 阶段。

## 关键规则

- **任何变更前必须做影响评估** —— 未理解爆炸半径绝不修改特性
- **每个 sub-skill 返回都走 approval-revise-loop** —— 统一 approve / revise / escalate 闸门
- **原地更新文档** —— 不另建 increment 文件；git 历史即审计轨迹
- **ID 连续性** —— 新特性 ID 始终递增，绝不复用已弃用 ID
- **批次跟踪** —— 每个新增/修改特性打当前批次号
- **已弃用特性不可变** —— 一旦弃用不可解除；改用新建特性
- **一次一个信号** —— 完整处理完一个 increment-request.json 再接受下一个

## 红旗

| 借口 | 正确动作 |
|---|---|
| "直接往 JSON 里加特性算了" | 用本 skill 保障可追踪 |
| "既有测试还在过，不用重新验证" | Hard Impact 特性必须重置 failing |
| "我稍后再更新设计" | Step 4 必须在 Step 6 之前 |
| "这次改动很小，跳过影响评估" | Step 3 捕捉隐藏依赖，不可跳过 |
| "我另建一份 SRS 文档" | 原地更新主 SRS；git 跟踪历史 |
| "sub-skill 返回了，直接下一步吧" | 所有 pass 返回都要过审批关卡 |
