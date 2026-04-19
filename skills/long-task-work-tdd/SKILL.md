---
name: long-task-work-tdd
description: "Use when router emits next_skill=long-task-work-tdd - run full TDD Red-Green-Refactor + Quality Gates, advance current.phase, then terminate session"
---

# Worker — 阶段 B：TDD + Quality Gates

每会话处理**一个特性**的 TDD 红绿重构循环 + 覆盖率关卡。完成后**推进 `current.phase: tdd → st`** 并**终止会话**。

**开始时宣告：** "I'm using the long-task-work-tdd skill. Let me orient myself."

Red / Green / Refactor + Quality 共四个独立 SubAgent 由本 skill 直接用 Agent 工具 DISPATCH。契约见 `../using-long-task/references/structured-return-contract.md`；返回按 `../using-long-task/references/approval-revise-loop.md` 处理。

**静默执行协议：** 所有测试 / 覆盖率 / 静态命令都重定向到 `/tmp/<slug>-$$.log` + exit 文件。永不倾倒完整输出。

## Checklist

### 0. env-guide 审批关卡
运行 `python scripts/check_env_guide_approval.py env-guide.md`。Exit 0 继续；Exit 1 阻塞升级；Exit 2 若 env-guide 缺失（CLI-only 项目）则跳过。

### 1. Orient —— 读 router 锁定的 target_feature
- 调 `python scripts/phase_route.py --json` 读 `next_skill` / `feature_id` / `starting_new`
  - `next_skill != "long-task-work-tdd"` → AskUserQuestion 升级
  - `ok == false` → 呈现 `errors` 并终止会话
  - `starting_new == true` → AskUserQuestion 升级（TDD 阶段不应是新 feature 的入口；状态机错位）
- `target_feature` = `feature-list.json` 中 `id == feature_id` 的条目
- **硬前置**：`docs/features/YYYY-MM-DD-<slug>.md` 必须存在（design 阶段已产出）。用 Glob 确认存在——**不读全文**；路径存为 `{feature_design_path}`（仅作为 SubAgent dispatch input）。若缺失 → BLOCKED：`Feature design doc missing for #<id>; current.phase inconsistent with disk state. Resume design phase or reset current.phase to "design".`
- `git log --oneline -10`
- 在 `task-progress.md` 当前特性标题下记录：target_feature.id / title / feature_design_path

### 2. Bootstrap
- 按 `env-guide.md §2` 激活环境
- `init.sh` / `init.ps1` 若未运行过则运行一次
- **服务就绪**（若 `target_feature` 有服务依赖）：
  1. 读 `env-guide.md` "Verify Services Running" 健康检查；若全通过 → 记录 PID/端口
  2. 若失败 → 按 `env-guide.md` "Start All Services" 启动，捕获 `/tmp/svc-<slug>-start.log` 前 30 行取 PID/端口
  3. 阻塞直至健康检查通过
- 冒烟测试：以 `env-guide.md §3` 测试命令跑一次已 passing 特性的测试子集，确认环境 sane
- **服务判定条件**（与原 work Step 1 一致）：
  - `required_configs[]` 含连接串键（URL/URI/DSN/HOST/PORT/CONNECTION/ENDPOINT）
  - `dependencies[]` 引用 DB 建表/迁移/服务初始化特性
  - feature design §6 Implementation Summary 指明外部服务交互

### 3. TDD R-G-R 三段式（本 skill 直接 DISPATCH 三个独立 SubAgent）

**3a. Red — DISPATCH SubAgent**

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-tdd-red`
> **input**: `feature_id`, `feature_list_path`, `feature_design_path`
> **expect**: Structured Return Contract；`next_step_input` 含 `feature_test_files[]` / `test_count`；`evidence` 以 `Rule N <key>=<value>` 形式逐行报告 Rule 1-7 关键指标（categories / negative_ratio / low_value_ratio / real_test_count）

**返回处理**：
- `status: fail` → Failure Addendum 重分发（计入 2 轮上限；超限 → AskUserQuestion 升级）
- `status: blocked` 带 `[ENV-ERROR]` / `[SRS-VAGUE]` / `[SRS-DESIGN-CONFLICT]` / `[SRS-MISSING]` / `[INSUFFICIENT_EVIDENCE]` → Clarification Addendum 重分发（不计入上限）
- `status: pass` → 进入 3b

**3b. Green — DISPATCH SubAgent**

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-tdd-green`
> **input**: `feature_id`, `feature_list_path`, `feature_design_path`, `feature_test_files`（从 3a next_step_input）, `test_count`
> **expect**: Structured Return Contract；`next_step_input` 含 `impl_files[]` / `all_tests_pass` / `design_alignment: {§4, §6, §8, drift}` / `env_guide_synced`

**返回处理**：
- `status: fail` → Failure Addendum 重分发（计入 2 轮上限）
- `status: blocked` 带 `[CONTRACT-DEVIATION]` → AskUserQuestion 裁决（跨 Step 决策，需用户；本地不解决）
- `status: blocked` 带 `[SRS-*]` / `[ENV-ERROR]` → Clarification Addendum 重分发
- `status: pass` → 进入 3c

**3c. Refactor — DISPATCH SubAgent**

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-tdd-refactor`
> **input**: `feature_id`, `feature_list_path`, `feature_design_path`, `feature_test_files`, `impl_files`
> **expect**: Structured Return Contract；`next_step_input` 含 `static_analysis_ok` / `static_tool` / `static_violations` / `design_alignment_final` / `tests_still_pass`

**返回处理**：
- `status: fail` → Failure Addendum 重分发
- `status: blocked` 带 `[CONTRACT-DEVIATION]` → AskUserQuestion 裁决
- `status: blocked` 带 `[ENV-ERROR]` → Clarification Addendum 重分发
- `status: pass` → 进入 3d

**3d. 聚合 TDD 层证据（供 Step 4 Quality Gates 消费）**

三步全部 pass 后，本 skill 在主 agent 内汇总三个子契约的关键字段供 Step 4：

- `feature_test_files` ← 3a.next_step_input
- `impl_files` ← 3b.next_step_input
- `test_count` ← 3a.next_step_input
- `all_tests_pass` ← 3b.next_step_input
- `red_green_refactor_complete` ← true
- 证据摘要（供 Step 5 commit 与 `task-progress.md` 记录）：
  - Red: N tests written, categories=..., negative_ratio=..., all FAILED
  - Green: all N tests PASS after minimal implementation
  - Design alignment: §4=<matches|updated:...>, §6=..., §8=...; drift=<none|resolved>
  - Refactor: static analysis clean (tool=..., 0 violations); tests still green

**任一子步终态 fail（超 2 轮）或 blocked 带 `[CONTRACT-DEVIATION]` 未恢复** → 本 skill 整体停止，向用户呈聚合证据，**不进入 Step 4**；`artifacts_written` 列出至此已产出的文件。

### 4. DISPATCH Quality Gates SubAgent

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-quality`
> **input**: `feature_id`, `feature_list_path`, `feature_test_files=<from-TDD-return>`, `working_dir`
> **expect**: Structured Return Contract；`next_step_input` 必须含 `coverage_line` / `coverage_branch` / `srs_trace_coverage.uncovered_fr_ids`

**返回处理**：
- `status: fail`（含 `srs_trace_coverage.uncovered_fr_ids` 非空）→ Failure Addendum 重分发（2 轮）；超限 → AskUserQuestion 呈 A/B/C：扩测 / 修订 feature.srs_trace / escalate
- `status: blocked` 带 `[INSUFFICIENT_EVIDENCE]` / `[ENV-ERROR]` → Clarification Addendum 重分发
- `status: pass` → 进入 Step 5

### 5. Persist & End Session

**5a. 推进 current.phase**：
编辑 `feature-list.json`，把根 `current.phase` 从 `"tdd"` 改为 `"st"`。`target_feature.status` 保持 `failing` 不变（ST 未完，总体仍 failing）。

**5b. 更新 task-progress.md**：
```
- TDD: green ✓ (R-G-R complete)
- Quality: line=<N>%, branch=<M>%, srs_trace_coverage=OK
- current.phase: tdd → st
```

**5c. 校验**：
```bash
python scripts/validate_features.py feature-list.json
```

**5d. git commit**（含测试代码 + 实现代码 + feature-list.json + 已更新的 task-progress.md；**不**打包 ST 用例——那是下阶段产出）：
```bash
git add <impl/test 文件列表> feature-list.json task-progress.md
git commit -m "tdd: feature #<id> <slug> — tests green, coverage ≥<N>%/<M>%"
```

**5e. 输出会话终止横幅**：
```
## Phase TDD Complete for Feature #<id> (<title>)

- current.phase: tdd → st
- Tests: <test_count> passing; line=<N>%, branch=<M>%
- Next: long-task-work-st in a NEW session (feature ST acceptance)
- Quick status: python scripts/count_pending.py feature-list.json

**Please start a new Claude Code session to continue.**

[End of session — DO NOT proceed to ST in this session]
```

**禁止**：本会话绝不继续调 `long-task-work-st` 或任何后续 skill。

## 关键规则

- **每会话一个特性的一个阶段** —— 本阶段只做 TDD + Quality，不做 Feature-ST 也不做 Persist 到 passing
- **R/G/R / Quality 四个 SubAgent 不可协商** —— 本 skill 必须用 Agent 工具分别 DISPATCH，不在主 agent 内联执行；会话内**不**调任何其它 Skill
- **无新鲜证据不得推进 current.phase** —— 测试必须实跑绿，覆盖率必须达标
- **feature design 文档必须存在** —— 缺失即 BLOCKED；主 agent 不读全文，仅传路径

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "测试通过就推进 current.phase" | 先调 long-task-quality。|
| "覆盖率差一点就凑" | 阈值是硬关卡。扩测或用 `long-task-increment` 修订 srs_trace。|
| "我顺便做了 ST" | 终止。ST 是下一会话的 work-st。|
| "feature design 不对，我自己改一下" | 不改。返 `[SRS-DESIGN-CONFLICT]` 走 Clarification 或建议 `long-task-increment`。|
| "静态分析警告忽略" | 阻塞——Refactor SubAgent 内部已关卡，此处视为漏判，重分发。|
| "把三个 SubAgent 合成一个省事" | 不。R/G/R 独立沙箱各自返契约；合并会污染三步之间的证据边界。|
