---
name: long-task-work-st
description: "Use when feature-list.json has a feature with sub_status=st_pending - run feature-level ST acceptance + inline compliance + final persist, then terminate session"
---

# Worker — 阶段 C：Feature-ST + Inline Check + Persist

每会话处理**一个特性**的黑盒 ST 验收测试 + 内联合规扫描 + 最终落盘。完成后**翻转 `sub_status: st_pending → done`** 并同步 `status: failing → passing`，然后**终止会话**。

**开始时宣告：** "I'm using the long-task-work-st skill. Let me orient myself."

**核心原则：** Feature-ST 子步骤在**独立 SubAgent**（`long-task-feature-st`）中运行；Inline Check 与 Persist 直接在主 agent 执行（无 SubAgent）。契约见 `../using-long-task/references/structured-return-contract.md`；返回按 `../using-long-task/references/approval-revise-loop.md` 处理。

**一致性重读（强制）：**
1. 读 `feature-list.json` → 按 `sub_status == st_pending` 选 lowest-id 特性
2. 读 `docs/features/YYYY-MM-DD-<slug>.md` **全文**（用于 ST 用例生成 + Inline 契约/测试清单交叉检查）
3. 读 `docs/plans/*-srs.md` 中 `srs_trace` 指向的 FR/NFR 节（ST 用例验收标准来源）
4. 读 `docs/plans/*-ats.md`（如存在）—— ATS 类别约束 ST 必须覆盖哪些场景
5. 读 `env-guide.md §1 服务生命周期` + `§3 测试命令` + `§4 codebase constraints`

**静默执行协议：** 与其他 phase skill 一致。

## Checklist

### 0. env-guide 审批关卡
运行 `python scripts/check_env_guide_approval.py env-guide.md`。行为与 work-design/work-tdd 一致。

### 1. Orient —— 选取 st_pending 特性
- 读 `feature-list.json` → 筛 `sub_status == "st_pending"` 且 `deprecated != true`；按优先级 + id 升序挑第一个（`target_feature`）
- **若无匹配** → 终止会话并提示：`No feature has sub_status=st_pending. If all features done → run long-task-st for system-wide testing. Start a new session.`
- **硬前置**：
  - `docs/features/YYYY-MM-DD-<slug>.md` 必须存在
  - `target_feature.git_sha`（若已设置，说明前阶段异常打包）或依赖测试文件存在
- 读该特性 feature design **全文**
- 读 `srs_section`（FR 节）
- 读 `docs/plans/*-ats.md` 中 `target_feature.srs_trace` 的 category 映射行
- 读 `env-guide.md §1 + §3 + §4`
- `git log --oneline -10`

### 2. Bootstrap
- 按 `env-guide.md §2` 激活环境
- 服务就绪：Feature-ST SubAgent **自管理**服务生命周期（启动/重启/清理），主 agent 仅确认 env-guide.md 可用即可

### 3. DISPATCH Feature-ST SubAgent

> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-feature-st`
> **input**: `feature_id`, `feature_list_path`, `feature_design_doc_path=docs/features/YYYY-MM-DD-<slug>.md`, `working_dir`
> **expect**: Structured Return Contract；`artifacts_written` 必须含 `docs/test-cases/feature-<id>-<slug>.md`

**硬关卡**：
- **不可绕过** —— 任何原因都不能跳过 ST
- AI 可自修的问题（代码 bug、环境问题）→ SubAgent 内部自动修复，无重试上限（不返 fail）
- 需要人类介入的问题 → `status: blocked` 带前缀 blocker：
  - `[MANUAL_TEST_REQUIRED]`（缺凭据/物理设备/视觉判断）
  - `[SRS-MISSING]`（规范缺口）
  - `[ATS-CATEGORY-MISSING-ST]`（ATS 必须类别无 ST 用例）

主 agent 按 `../using-long-task/references/approval-revise-loop.md` 前缀表组装 AskUserQuestion，收集裁决后 Clarification Addendum 重分发。

### 4. Inline 合规检查（无 SubAgent）

机械化检查，直接在主 agent 跑。读 Step 3 完成后的磁盘状态与特性设计文档。

**a) 接口契约校验（P2）**：设计文档 Interface Contract 表中每个 PUBLIC 方法 grep 实现文件确认签名匹配。
**b) Test Inventory ↔ 测试文件交叉（T2）**：每行测试用 `grep -q "{test_function_name}" {test_file}` 确认存在。
**c) 2/3方件 版本（D3）**：若 Interface Contract / Implementation Summary 引用版本，抽查 `requirements.txt` / `package.json` / `pom.xml`。
**d) UCD 抽查（U1，仅 ui:true）**：grep CSS/样式文件找不在 UCD 色板 token 中的硬编码颜色。
**e) ST 文档完整性**：确认 `validate_st_cases.py` 在 Feature-ST 内已通过（返回 evidence 里应有）。
**e2) ATS 类别覆盖卫生**（若有 `docs/plans/*-ats.md`）：
```bash
python scripts/check_ats_coverage.py docs/plans/*-ats.md --feature-list feature-list.json --feature <id>
```
退出 0 通过；退出 1 → FAIL，回 Step 3 以 `[ATS-CATEGORY-MISSING-ST]` 触发扩 ST 用例。

**f) §4 存量约定全差异扫描**（若有 `env-guide.md §4`）：
```bash
git diff HEAD~1 --name-only  # 本次 st 阶段的累计变更
```
对每个源文件核查 §4.1（强制内部库）/ §4.2（禁用 API）/ §4.3（命名）—— 违规就地修复。

任意检查失败：a/b/c/d/e2/f 就地修复重校；e 必须回 Step 3。

在 `task-progress.md` 记录：
```
- Inline Check: PASS (P2: N/N methods, T2: N/N tests, D3: OK, ATS Category: N/N, §4: N files 0 violations)
```

### 5. Persist —— 最终落盘

**5a. git commit**（实现 + 测试 + ST 测试用例文档）：
- Commit 格式：若 `docs/rules/commit-conventions.md` 存在按其格式；否则默认 `feat: <title>` 或 `fix: <title> (#<fixed_feature_id>)`（bugfix）
```bash
git add <all-feature-files> docs/test-cases/feature-<id>-<slug>.md
git commit -m "<commit-msg>"
```
抓取 SHA：`git rev-parse --short HEAD` → 存为 `{commit_sha}`

**5b. 更新 RELEASE_NOTES.md**（Keep a Changelog）：
- 一般特性 → `### Added`
- bugfix → `### Fixed`，条目格式：`- [<bug_severity>] <title> (fixes #<fixed_feature_id>) — <root_cause>`

**5c. 翻转 feature-list.json**：
- `target_feature.sub_status`: `st_pending` → `done`
- `target_feature.status`: `failing` → `passing`
- 设置 `target_feature.git_sha = {commit_sha}`
- 设置 `target_feature.st_case_path = "docs/test-cases/feature-<id>-<slug>.md"`
- 设置 `target_feature.st_case_count = <from Feature-ST next_step_input>`

**5d. 校验**：
```bash
python scripts/validate_features.py feature-list.json
```

**5e. 更新 task-progress.md**：
- `## Current State` 头部：进度计数（X/Y passing）、上个完成特性、下一个特性；**移除任何 `in-progress: step-N` 标记**
- 日志分隔线下追加 session 条目：
```
### Feature #<id>: <title> — PASS
- Completed: YYYY-MM-DD
- TDD: green ✓
- Quality Gates: N% line, N% branch
- Feature-ST: N cases, all PASS
- Inline Check: PASS
- Git: {commit_sha} <commit-type>: <title>
#### Risks                        ← 仅当有风险时
- ⚠ [Mutant] file:line — reason
- ⚠ [Coverage] metric N% — thin margin
- ⚠ [Dependency] lib==ver — patch pending
```
**收集风险**：从前阶段 Quality `### Risks` + 本阶段 Feature-ST `### Risks`（如有）合并。

**5f. 再次 git commit**（进度文件）：
```bash
git add feature-list.json task-progress.md RELEASE_NOTES.md
git commit -m "chore: update progress — feature #<id> passing (sub_status=done)"
```

### 6. End Session

**6a. 输出会话终止横幅**：
```
## Phase ST Complete for Feature #<id> (<title>) — DONE

- sub_status: st_pending → done
- status: failing → passing
- Git: {commit_sha}
```

**6b. 若无剩余 `sub_status != done` 的非弃用特性**：
```
All active features sub_status=done → next session begins system-wide testing via long-task-st.
```
否则：
```
Next: long-task-work-<phase> in a NEW session (check: python scripts/count_pending.py feature-list.json)

**Please start a new Claude Code session to continue.**
```

**6c. 停止任何本会话 Inline 检查或 Persist 阶段启动的临时服务**（Feature-ST SubAgent 管理自己的服务生命周期，已清理）。

**禁止**：本会话绝不继续调其他 phase skill 或 `long-task-st`。

## 关键规则

- **每会话一个特性的一个阶段** —— 本阶段只做 Feature-ST + Inline + Persist
- **ST 不可绕过** —— AI 可修的内部修；人类介入的 blocked
- **Inline Check 全绿才 Persist** —— §4 违规必须就地修复
- **翻转 sub_status=done 同步 status=passing** —— 两者必须一致，`validate_features.py` 强制校验
- **RELEASE_NOTES.md 与 Git SHA 在同一轮 Persist 内更新** —— 避免漂移

## 红旗信号

| 逃避 | 正确动作 |
|---|---|
| "ST 环境炸了，我跳过" | BLOCKED，不是 skipped。Feature-ST SubAgent 内部修；真不可自修才升级。|
| "Inline Check P2 不匹配但代码对" | 更新 feature design（§4 契约扩展协议）或回 work-tdd 修代码。|
| "忘了 git commit SHA 就翻 sub_status" | 严禁。先 commit，抓 SHA，再翻 sub_status。|
| "ATS 类别缺 ST 用例，我就把 ATS 改小点" | 不行。回 Step 3 扩 ST 用例，或通过 `long-task-increment` 正式修订 ATS。|
| "全部 passing 了我顺便跑系统级 ST" | 终止。system-wide ST 是 `long-task-st`，下一会话。|
