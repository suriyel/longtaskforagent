---
name: long-task-work-design
description: "Use when router emits next_skill=long-task-work-design - produce per-feature detailed design document, advance current.phase, then terminate session"
---

# Worker — 阶段 A：Feature Design

每会话处理**一个特性**的详细设计产出。完成后**推进 `current.phase: design → tdd`** 并**终止会话**，等用户开新会话进入 TDD 阶段。

**开始时宣告：** "I'm using the long-task-work-design skill. Let me orient myself."

**核心原则：** Feature Design 子步骤在**独立 SubAgent**中运行（`long-task-feature-design`）。主 Agent 仅分发并消费 **Structured Return Contract** —— 契约与 DISPATCH 语法参见 `../using-long-task/references/structured-return-contract.md`；SubAgent 返回按 `../using-long-task/references/approval-revise-loop.md` 处理。

**一致性重读（允许重复读，一致性优先）：** 启动 5 件事：
1. 调 `python scripts/phase_route.py --json` → 读 `feature_id`（`target_feature`）与 `starting_new`
2. 读 `docs/plans/*-srs.md` 对应 `srs_trace` 的 FR/NFR 节
3. 读 `docs/plans/*-design.md` 对应 `§2.N` 子节
4. 读 `env-guide.md §4`（存量代码库约束，如存在）
5. 读 `docs/plans/*-ucd.md`（仅 ui:true）/ `*-ats.md`（若存在）

**静默执行协议：** 每一次构建、测试、检查命令都重定向到 `/tmp/<slug>-$$.log` + exit 文件。永不向主 agent 倾倒完整输出。

## Checklist

### 0. env-guide 审批关卡
运行 `python scripts/check_env_guide_approval.py env-guide.md`：Exit 0 继续；Exit 1 阻塞并 AskUserQuestion 升级；Exit 2 若无 env-guide.md（pre-init / CLI-only）则跳过。

### 1. Orient —— 读 router 锁定的 target_feature
- 调 `python scripts/phase_route.py --json` 读 `next_skill` / `feature_id` / `starting_new`
  - `next_skill != "long-task-work-design"` → AskUserQuestion 升级（调用链错位）
  - `ok == false` → 呈现 `errors` 并终止会话，不继续
  - `feature_id == null` → 终止会话（路由无可做特性）
- `target_feature` = `feature-list.json` 中 `id == feature_id` 的条目
- **若 `starting_new == true`**（router 新挑了一个 feature）：**原子写入**
  `feature-list.json` 的 `current = {"feature_id": <id>, "phase": "design"}`，
  `git add feature-list.json && git commit -m "chore(current): start feature #<id> design"`，
  再进入后续读取。Router 已保证依赖满足，此处不再重复挑选或检查依赖。
- 读 `docs/plans/*-design.md` § 架构（§1）+ `target_feature` 对应的 `§2.N` 子节（按"文档查询协议"通过 Read offset/limit 定位）
- 读 `docs/plans/*-srs.md` 中 `target_feature.srs_trace` 指向的所有 FR-xxx 子节
- 读 `env-guide.md §4`（如存在）
- 若 `target_feature.ui == true` 且 `docs/plans/*-ucd.md` 存在：读 UCD 样式指南相关章节
- `git log --oneline -10` 取最近 commit 上下文
- 在 `task-progress.md` 当前特性标题下记录：target_feature.id / title / design_section 行号 / srs_section 行号

### 2. Bootstrap
- 按 `env-guide.md §2` 激活项目环境（如存在）
- 若 `init.sh` / `init.ps1` 存在且环境未就绪：运行一次
- **Feature Design 阶段不需要启动业务服务** —— 服务就绪性由 TDD 阶段（work-tdd）关心

### 3. Config Gate（条件性）
仅当 `target_feature.required_configs[]` 含连接串键（URL / URI / DSN / CONNECTION / HOST / PORT / ENDPOINT）时执行；否则跳过。

运行：
```bash
python scripts/check_configs.py feature-list.json --feature <id>
```
缺失 config 处理：用 AskUserQuestion 文本输入收集缺失值 → 写入 `.env` 或项目 config 文件 → 重跑 `python scripts/check_configs.py feature-list.json --feature <id>`，直至通过。设计阶段仍需 config 存在性校验，以便 Feature Design SubAgent 能够准确描述外部接口。

### 4. DISPATCH Feature Design SubAgent

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-feature-design`
> **input**: `feature_id`, `feature_list_path`, `design_section=<行号起止>`, `srs_section=<FR-xxx 行号起止>`, `ucd_section=<仅 ui:true>`, `output_path=docs/features/YYYY-MM-DD-<slug>.md`
> **expect**: Structured Return Contract；`next_step_input.feature_design_path` 必须存在

> **对 `category: "bugfix"`**：feature-design 精简，聚焦根因记录 + 定向修复 + 回归测试清单。

**返回处理**（按 `../using-long-task/references/approval-revise-loop.md`）：
- `status: blocked` → 按 blockers[] 前缀（`[SRS-VAGUE]` / `[SRS-DESIGN-CONFLICT]` / `[ATS-MISMATCH]` / `[ATS-BUGFIX-REGRESSION-MISSING]` / `[UCD-VAGUE]` / `[DEP-AMBIGUOUS]` / `[NFR-GAP]` / `[CONTRACT-DEVIATION]`）组装 AskUserQuestion；收集裁决后以 Clarification Addendum 重分发（不计入 revise 上限）
- `status: fail` → Failure Addendum 重分发（计入 revise 上限 2 轮）
- `status: pass` 且 `next_step_input.assumption_count > 0` → 审批关卡（approve / revise / skip-feature / escalate）让用户确认 assumptions
- `status: pass` 且 `assumption_count == 0` → 进入 Step 5
- 同一前缀 3 次 blocked → 自动 escalate
- 用户选 C（打回 SRS 侧）→ task-progress.md 记录缺口 + 建议 `long-task-increment`，本特性 skip-feature（不推进 current.phase）

### 5. Persist & End Session

**5a. 推进 current.phase**：
编辑 `feature-list.json`，把根 `current.phase` 从 `"design"` 改为 `"tdd"`。保持 `current.feature_id` 不变、`target_feature.status: failing` 不变。

**5b. 更新 task-progress.md**：在当前特性标题下追加：
```
- Design: DONE (docs/features/YYYY-MM-DD-<slug>.md)
- current.phase: design → tdd
```

**5c. 校验**：
```bash
python scripts/validate_features.py feature-list.json
```

**5d. git commit**（含特性设计文档 + feature-list.json + 已更新的 task-progress.md）：
```bash
git add docs/features/YYYY-MM-DD-<slug>.md feature-list.json task-progress.md
git commit -m "design: feature #<id> <slug> — current.phase → tdd"
```

**5e. 输出会话终止横幅**（强制格式）：
```
## Phase Design Complete for Feature #<id> (<title>)

- current.phase: design → tdd
- Next: long-task-work-tdd in a NEW session
- Quick status: python scripts/count_pending.py feature-list.json

**Please start a new Claude Code session to continue.**

[End of session — DO NOT proceed to TDD in this session]
```

**禁止**：本会话绝不继续调 `long-task-work-tdd` 或任何后续阶段 skill。`auto_loop.py` 在外部处理多阶段串联，每次迭代都是新鲜上下文。

## 关键规则

- **每会话一个特性的一个阶段** —— 本阶段只产出设计文档，不做 TDD 也不做 ST
- **SubAgent 不可协商** —— `long-task-feature-design` 必须通过 Skill 工具分发
- **用户裁决一律由主 agent 按 loop.md 组装** —— sub-skill 绝不发 AskUserQuestion
- **推进 current.phase 前必须校验** —— `validate_features.py` 必须 PASS
- **SRS/Design/UCD 模糊不得假设** —— 返 blocked 走 Clarification Addendum

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "我顺便把 TDD 也做了" | 终止会话。TDD 是下一会话的 work-tdd。|
| "SRS 模糊但我就假设……" | SubAgent 返 `[SRS-VAGUE]` → Clarification Addendum |
| "这个特性简单，skip Feature Design 直接做 TDD" | Feature Design 不可绕过。每特性都要。|
| "推进 current.phase 忘了校验" | 先 `validate_features.py`，再 commit。|
