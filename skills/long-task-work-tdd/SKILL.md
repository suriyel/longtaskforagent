---
name: long-task-work-tdd
description: "Use when feature-list.json has a feature with sub_status=tdd_pending - run full TDD Red-Green-Refactor + Quality Gates, then terminate session"
---

# Worker — 阶段 B：TDD + Quality Gates

每会话处理**一个特性**的 TDD 红绿重构循环 + 覆盖率关卡。完成后**翻转 `sub_status: tdd_pending → st_pending`** 并**终止会话**。

**开始时宣告：** "I'm using the long-task-work-tdd skill. Let me orient myself."

**核心原则：** TDD 与 Quality 各自在**独立 SubAgent**中运行（`long-task-tdd` → `long-task-quality`）。主 Agent 仅消费 Structured Return Contract。契约见 `../long-task-work/references/structured-return-contract.md`；返回按 `../long-task-work/references/approval-revise-loop.md` 处理。

**一致性重读（强制，每次本阶段会话启动都要做）：**
1. 读 `feature-list.json` → 按 `sub_status == tdd_pending` 选 lowest-id 特性
2. 读 `docs/features/YYYY-MM-DD-<slug>.md` **全文**（design 阶段产出；本阶段主要规约来源）
3. 读 `docs/plans/*-srs.md` 中 `srs_trace` 指向的 FR/NFR 节
4. 读 `env-guide.md §3`（测试/覆盖率/静态分析命令）+ `§4`（codebase constraints）
5. 读 `docs/plans/*-design.md` 中 `§4` Internal API Contracts 本特性相关行

**允许重复读同一份 feature design** —— TDD SubAgent 内部 R/G/R 各步也会再读；一致性优先，不做缓存优化。

**静默执行协议：** 所有测试 / 覆盖率 / 静态命令都重定向到 `/tmp/<slug>-$$.log` + exit 文件。永不倾倒完整输出。

## Checklist

### 0. env-guide 审批关卡
运行 `python scripts/check_env_guide_approval.py env-guide.md`。Exit 0 继续；Exit 1 阻塞升级；Exit 2 若 env-guide 缺失（CLI-only 项目）则跳过。

### 1. Orient —— 选取 tdd_pending 特性
- 读 `feature-list.json` → 筛 `sub_status == "tdd_pending"` 且 `deprecated != true` 的特性；按优先级 + id 升序挑第一个（`target_feature`）
- **若无匹配** → 终止会话并提示：`No feature has sub_status=tdd_pending. Run: python scripts/count_pending.py feature-list.json; start a new session.`
- 依赖满足检查：`dependencies[]` 中所有 id 必须 `status=passing`。未满足则跳过挑下一个；全部不满足 → AskUserQuestion 升级
- **硬前置**：`docs/features/YYYY-MM-DD-<slug>.md` 必须存在（design 阶段已产出）。若缺失 → BLOCKED：`Feature design doc missing for #<id>; sub_status inconsistent with disk state. Run migrate_sub_status.py --force or resume design phase.`
- 读该特性设计文档**全文**；存为 `{feature_design_path}` 供 SubAgent dispatch 使用
- 读 `docs/plans/*-srs.md` 中 `srs_trace` FR 节；存为 `{srs_section}`
- 读 `env-guide.md §3 + §4`
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

### 3. DISPATCH TDD SubAgent

> **DISPATCH** → 启动独立 SubAgent 加载并执行 `long-task-tdd`
> **input**: `feature_id`, `feature_list_path`, `feature_design_path=docs/features/YYYY-MM-DD-<slug>.md`
> **expect**: Structured Return Contract；`next_step_input` 含 `feature_test_files[]` / `all_tests_pass` / `red_green_refactor_complete` / `test_count`
>
> **重要**：TDD 不拆分——SubAgent 在自己上下文里顺序跑 Red → Green → Refactor。主 Agent 最后收到一个返回，不是三段式。

**返回处理**（按 `../long-task-work/references/approval-revise-loop.md`）：
- `status: fail` → Failure Addendum 重分发（计入 2 轮上限）
- `status: blocked` 带 `[INSUFFICIENT_EVIDENCE]` / `[ENV-ERROR]` / `[SRS-VAGUE]` / `[SRS-DESIGN-CONFLICT]` / `[SRS-MISSING]` → Clarification Addendum 重分发（不计入上限）
- `status: pass` → 进入 Step 4

### 4. DISPATCH Quality Gates SubAgent

> **DISPATCH** → 启动独立 SubAgent 加载并执行 `long-task-quality`
> **input**: `feature_id`, `feature_list_path`, `feature_test_files=<from-TDD-return>`, `working_dir`
> **expect**: Structured Return Contract；`next_step_input` 必须含 `coverage_line` / `coverage_branch` / `srs_trace_coverage.uncovered_fr_ids`

**返回处理**：
- `status: fail`（含 `srs_trace_coverage.uncovered_fr_ids` 非空）→ Failure Addendum 重分发（2 轮）；超限 → AskUserQuestion 呈 A/B/C：扩测 / 修订 feature.srs_trace / escalate
- `status: blocked` 带 `[INSUFFICIENT_EVIDENCE]` / `[ENV-ERROR]` → Clarification Addendum 重分发
- `status: pass` → 进入 Step 5

### 5. Persist & End Session

**5a. 翻转 sub_status**：
编辑 `feature-list.json`，把 `target_feature.sub_status` 从 `tdd_pending` 改为 `st_pending`。`status` 保持 `failing` 不变（ST 未完，总体仍 failing）。

**5b. 更新 task-progress.md**：
```
- TDD: green ✓ (R-G-R complete)
- Quality: line=<N>%, branch=<M>%, srs_trace_coverage=OK
- sub_status: tdd_pending → st_pending
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

- sub_status: tdd_pending → st_pending
- Tests: <test_count> passing; line=<N>%, branch=<M>%
- Next: long-task-work-st in a NEW session (feature ST acceptance)
- Quick status: python scripts/count_pending.py feature-list.json

**Please start a new Claude Code session to continue.**

[End of session — DO NOT proceed to ST in this session]
```

**禁止**：本会话绝不继续调 `long-task-work-st` 或任何后续 skill。

## 关键规则

- **每会话一个特性的一个阶段** —— 本阶段只做 TDD + Quality，不做 Feature-ST 也不做 Persist 到 passing
- **TDD / Quality SubAgent 不可协商** —— 必须通过 Skill 工具分发
- **无新鲜证据不得翻转 sub_status** —— 测试必须实跑绿，覆盖率必须达标
- **feature design 文档必读** —— 缺失即 BLOCKED
- **一致性优先于去重** —— 允许 SubAgent 内部 R/G/R 各自重读 feature design

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "测试通过就翻 sub_status" | 先调 long-task-quality。|
| "覆盖率差一点就凑" | 阈值是硬关卡。扩测或用 `long-task-increment` 修订 srs_trace。|
| "我顺便做了 ST" | 终止。ST 是下一会话的 work-st。|
| "feature design 不对，我自己改一下" | 不改。返 `[SRS-DESIGN-CONFLICT]` 走 Clarification 或建议 `long-task-increment`。|
| "静态分析警告忽略" | 阻塞——Refactor 内部已关卡，此处视为 SubAgent 漏判，重分发。|
