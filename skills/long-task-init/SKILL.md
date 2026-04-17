---
name: long-task-init
description: "Use when ATS doc exists (or auto-skipped) but feature-list.json not yet created - scaffold project artifacts and populate features from Design §6.1"
---

# 初始化 Long-Task 项目

在 SRS / Design / ATS 都获批后运行一次。通过 `init_project.py` 打包确定性骨架，分发三个 sub-skill 生成 env-guide.md / init.sh / long-task-guide.md + feature-list.json，然后 git init 并链到 Worker。Step 3/4/5 分发到 SubAgent；主 agent 仅保留 orchestration + 用户交互。

**开始时宣告：** "I'm using the long-task-init skill to scaffold the project."

## 输入文档

| 文档 | 位置 | 提供 |
|----------|----------|----------|
| **SRS** | `docs/plans/*-srs.md` | FR / NFR / CON / ASM / IFR / 术语表 / 角色 / 验收标准 |
| **Design** | `docs/plans/*-design.md` | 技术栈、架构、数据模型、API 设计、§6.1 任务分解、§6.2 依赖链 |
| **ATS** | `docs/plans/*-ats.md`（可选，≤5 FR 时可缺失）| 需求→场景映射、每条需求所需测试类别（通过 srs_trace 约束 `ui` 标记与下游 feature-st 类别要求）|

主 agent 仅读路径定位文件，**不读全文**；各 sub-skill 在独立 SubAgent 上下文中自行加载所需章节。

## 共享资产

- **返回契约**：`skills/long-task-work/references/structured-return-contract.md`
- **审批-返工循环**：`references/approval-revise-loop.md`（approve / revise / escalate；2 轮封顶；sizing 关卡与 env §3/§4 双闸门规则；Addendum 组装）

## 清单

为每步创建 TodoWrite 任务并顺序完成。

### 1. Orient

- 定位 `docs/plans/*-{srs,design,ats}.md` 路径
- SRS 中读取项目名（供 Step 2 `--project-name`）与语言提示（供 Step 2 `--lang`）
- `git log --oneline -10`（若已有 git 历史）

### 2. 运行 `scripts/init_project.py`

```bash
python scripts/init_project.py <project-name> --path . --lang <python|java|typescript|c|cpp>
```
- `<project-name>` 来自 SRS 标题
- `<language>` 来自 Design §1.4 技术栈
- 可选 `--line-cov` / `--branch-cov` 覆盖默认阈值（90 / 80）

本步产出：`feature-list.json` 骨架（空 features 数组）+ CLAUDE.md 追加 + `task-progress.md` + `RELEASE_NOTES.md` + `examples/` + `docs/plans/` + 全套辅助脚本复制到 `scripts/`。

### 3. 生成 env-guide.md

> **DISPATCH** → 启动独立 SubAgent 执行 skill `long-task-init-env`
> **input**: `project_lang`（来自 init_project.py 写入的 feature-list.json.tech_stack）
> **expect**: Structured Return Contract；`artifacts_written=["env-guide.md"]`；`next_step_input` 含 `services[]` / `env_activation_cmd` / `build_cmd` / `test_cmd` / `coverage_cmd` / `tool_version_pins` / `ui_detected`

按 `references/approval-revise-loop.md` 处理。**§3 与 §4 合并在同一关卡审批**——approve 时主 agent 更新 env-guide.md frontmatter `approved_by` / `approved_date` / `approved_sections: ["§3", "§4"]`。

### 4. 生成 init.sh / init.ps1

> **DISPATCH** → 启动独立 SubAgent 执行 skill `long-task-init-bootstrap`
> **input**: （从 feature-list.json.tech_stack + env-guide.md §2 / §3 自行定位）
> **expect**: Structured Return Contract；`artifacts_written=["init.sh", "init.ps1"]`；`next_step_input` 含 `env_manager` / `runtime_version` / `install_commands`；`evidence` 必含 `"bash -n clean"` 与 PowerShell parser 通过记录

零审批直通：确定性输出 + 内置语法自检。`status: pass` 即跳到下一步。`fail` / `blocked` 按 loop 模板处理。

### 5. 生成 long-task-guide.md 与 feature-list.json 特性

> **DISPATCH** → 启动独立 SubAgent 执行 skill `long-task-init-features`
> **input**: （从 SRS / Design / ATS / env-guide.md / feature-list.json.tech_stack 自行定位）
> **expect**: Structured Return Contract；`artifacts_written` 含 `long-task-guide.md` / `feature-list.json` / `.env.example` / `.gitignore` / `scripts/check_configs.py`；`next_step_input` 含 `feature_count` / `loc_distribution` / `feature_summary` / `ui_feature_count` / `config_count`

按 `references/approval-revise-loop.md` 处理。审批关卡**前**先走 **sizing 关卡**（见 loop 模板"Features Sizing 关卡细则"）：
- `y` → approve 通过
- `auto-fix` → Addendum "按 loc_distribution 中 small/large 特性执行合并/拆分；保持 srs_trace" 重分发
- `manual-adjust` → 暂停让用户编辑 `feature-list.json`；resume 后主 agent 只重跑 `python scripts/validate_features.py feature-list.json` 验证

### 6. 脚手架项目骨架

基于设计文档架构创建源码目录（如 `src/`、`tests/`、语言特定子目录）。本步不创建业务代码——仅空目录 + `.gitkeep` 或 README 占位。

### 7. Git init 与初始提交

```bash
git init
git add -A
git commit -m "chore: initialize long-task project scaffold

- feature-list.json with N features
- env-guide.md, long-task-guide.md
- init.sh / init.ps1 bootstrap scripts
- .env.example + scripts/check_configs.py
"
```

### 8. 运行 init 脚本并校验环境

- 运行 `bash init.sh`（Unix）或 `pwsh ./init.ps1`（Windows），确认环境安装无错误
- 激活环境后执行 `env-guide.md` §3 定义的测试命令，确认可执行（此时特性全部 failing 是预期的）
- 任何失败 → 诊断根因，修 `init.sh` / `init.ps1` / `env-guide.md` / `scripts/check_configs.py`，重跑
- **不要**在此启动服务——服务在 Worker / ST 阶段按 `env-guide.md` §1 启动

### 9. 更新 task-progress.md

- `## Current State` 头部：`0/N features passing`、`last event: init scaffold`、`next up: Feature 1`
- 追加 `## Session 0 — Init` 条目：SRS / Design / ATS 路径引用、特性总数、UI 特性数、config 数

### 10. Retrospective 授权

```bash
python scripts/check_retro_auth.py feature-list.json
```
- **Exit 0**（endpoint 已配置且可达）→ AskUserQuestion：
  > "检测到 Skill 反馈 API 已配置（{endpoint}）。是否授权在本项目中搜集 Skill 改进建议并在项目结束后上报？搜集内容包括：用户反馈修正、技能缺陷分析。不包含项目代码或业务数据。"
  > 选项：`授权 (Recommended)` / `不授权`
  - 授权 → feature-list.json 根置 `"retro_authorized": true`
  - 拒绝 → 置 `false`
- **Exit 1 或 2**（不可用或禁用）→ 静默跳过

### 11. 开始首次 Worker 循环

**必需子 skill：** 调用 `long-task:long-task-work`。主 agent 在此保留 handoff 控制权（不在任何 sub-skill 内自动触发）。

## 服务 Config 维护（Worker 循环期间）

当 Worker 循环引入新后端服务、变更服务端口或发现实际 start/stop 命令与 env-guide.md 不一致时，更新 `env-guide.md`：
- 新增/更新 Services 表行（服务名、端口、start/stop/verify 命令）
- 新增/更新对应的 Start / Verify / Stop / Restart 命令
- 启停序列 >2 shell 步 → 抽到 `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-stop.sh` 并更新 env-guide.md 引用
- env-guide.md 与任何 `scripts/svc-*` 变更随特性同一 git commit 提交

**env-guide.md 必须始终反映实际能工作的命令。** 每当一条命令被证实正确（TDD Green 期间或修复失败后），env-guide.md 必须更新以匹配。

## Feature List Schema

根结构：
```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "tech_stack": {
    "language": "python|java|typescript|c|cpp",
    "test_framework": "pytest|junit|vitest|gtest|...",
    "coverage_tool": "pytest-cov|jacoco|c8|gcov|..."
  },
  "quality_gates": {"line_coverage_min": 90, "branch_coverage_min": 80},
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
  "required_configs": [
    {
      "name": "Display name", "type": "env|file",
      "key": "ENV_VAR (env type)", "path": "path/to/file (file type)",
      "description": "...", "required_by": [1, 3], "check_hint": "..."
    }
  ],
  "features": [...]
}
```

每个特性：
```json
{
  "id": 1, "category": "core", "title": "...", "description": "...",
  "priority": "high|medium|low", "status": "failing|passing",
  "srs_trace": ["FR-001"], "verification_steps": ["..."],
  "dependencies": [], "ui": false, "ui_entry": "/optional-path"
}
```

## 关键规则

- **主 agent 不读 SRS / Design / ATS 全文** —— sub-skill 在其 SubAgent 上下文自行加载；主 agent 只按 evidence + next_step_input 做决策
- **env-guide.md frontmatter 审批字段由主 agent 写** —— sub-skill 永不修改 `approved_by` / `approved_date` / `approved_sections`
- **每步 sub-skill 返回都走 approval-revise-loop** —— 统一 approve / revise / escalate 闸门；bootstrap 为零审批快通
- **feature-list.json 单一写者** —— 仅 features sub-skill 写入；env / bootstrap 只读 tech_stack
- **Step 11 handoff 保留在主 agent** —— 任何 sub-skill 不在 evidence 中触发自动链式 Worker 调用

## 集成

- **调用方**：`long-task-ats`（Step 12）或 `using-long-task`（ATS 存在、无 feature-list.json 时）
- **读取**（主 agent 仅路径）：`docs/plans/*-srs.md` / `*-design.md` / `*-ats.md`
- **写入**（经 sub-skill）：`feature-list.json` / `env-guide.md` / `init.sh` / `init.ps1` / `long-task-guide.md` / `.env.example` / `scripts/check_configs.py`
- **下游**：`long-task-work`（Step 11 链接）
- **子 skill**：`long-task-init-env` / `long-task-init-bootstrap` / `long-task-init-features`
