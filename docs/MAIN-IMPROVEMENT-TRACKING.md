# Main 分支整改任务跟踪

> 分支: `main-improvement`
> 基础: `main`
> 方案: [MAIN-BRANCH-IMPROVEMENT-PLAN.md](MAIN-BRANCH-IMPROVEMENT-PLAN.md)
> 启动日期: 2026-04-17

## 当前会话目标

**阶段 B（架构重构）** — 主题 3 SubAgent-per-Step + 主题 6 env-guide 下沉审批

## 整体进度

| 阶段 | 主题 | 状态 | 备注 |
|---|---|---|---|
| A | 1. 去除用户呈现型报告 | ✅ 完成 | 删除 feature-report 子系统 |
| A | 8. 完全移除变异测试 | ✅ 完成 | schema/skill/template/test 全链路清理 |
| A | 10. 删除自定义 MCP & tool-binding | ✅ 完成 | 保留 Chrome DevTools MCP |
| B | 3. Worker SubAgent-per-Step | ✅ 完成 | DISPATCH 语法 + 统一 Return Contract + Resume 能力 |
| B | 6. rules/guide 下沉到 env-guide.md + 审批 | ✅ 完成 | 六板块 env-guide.md + check_env_guide_approval.py 审批 gate |
| C | 2. Increment 吸收 brownfield 适配 | ⏸ 未开始 | |
| C | 4. 设计/Feature Design 瘦身 | ⏸ 未开始 | |
| C | 7. 编译/UT 静默参数 | ⏸ 未开始 | quiet execution 已纳入 env-guide.md §3 模板 |
| C | 9. FR 合并 + ~1k LOC 颗粒度 | ⏸ 未开始 | |
| D | 5. 中文化 | ⏸ 未开始 | 最后收口 |

状态图例: ⬜ 待开始 · 🟡 进行中 · ✅ 完成 · ⏸ 未启动 · ❌ 阻塞

---

## 阶段 A 任务清单

### 主题 1：去除 Feature Report 子系统

- [x] T1.1 删除 `docs/templates/feature-report-template.md`
- [x] T1.2 `skills/long-task-work/SKILL.md`：移除 Step 11a "Generate Feature Report" 及其依赖
- [x] T1.3 `skills/long-task-work/SKILL.md.template`：同步移除
- [x] T1.4 `skills/long-task-hotfix/SKILL.md`：检查并清理 feature-report 引用
- [x] T1.5 `CLAUDE.md`：从 "Generated Persistent Artifacts" 删除 `docs/report/feature-*-report.md`
- [x] T1.6 验证：`grep -rn "feature-report-template\|docs/report/feature-"` 应为空（除 plan/diff 文档）

### 主题 8：完全移除变异测试

#### 8.1 Schema / 脚本
- [x] T8.1 `scripts/validate_features.py`：删除 mutation 字段校验（`tech_stack.mutation_tool`、`quality_gates.mutation_score_min`、`mutation_full_threshold`）
- [x] T8.2 `skills/long-task-init/scripts/init_project.py`：删除 `--mutation-score` 参数与 mutation_tool 探测逻辑
- [x] T8.3 `scripts/get_tool_commands.py`：删除 mutation 命令输出
- [x] T8.4 `tests/test_validate_features.py`：删除 mutation 用例
- [x] T8.5 `tests/test_init_project.py`：删除 mutation 用例
- [x] T8.6 `tests/test_get_tool_commands.py`：删除 mutation 用例
- [x] T8.7 `scripts/find-polluter.sh`：检查并清理 mutation 引用

#### 8.2 Skill 层
- [x] T8.8 `skills/long-task-quality/SKILL.md`：删除 "Feature-Scoped Mutation Gate" 整章
- [x] T8.9 `skills/long-task-quality/SKILL.md.template`：同步
- [x] T8.10 `skills/long-task-quality/references/quality-execution.md`：删除 mutation 段落
- [x] T8.11 `skills/long-task-quality/coverage-recipes.md`：删除 mutation 内容
- [x] T8.12 `skills/long-task-work/SKILL.md`：Step 9 Quality 仅含覆盖率
- [x] T8.13 `skills/long-task-work/SKILL.md.template`：同步
- [x] T8.14 `skills/long-task-st/SKILL.md`：删除 "ST 期间 mutation 全量跑" 逻辑
- [x] T8.15 `skills/long-task-st/SKILL.md.template`：同步
- [x] T8.16 `skills/long-task-st/references/st-recipes.md`：删除 mutation
- [x] T8.17 `skills/long-task-retrospective/SKILL.md`：删除 mutation 相关记录字段
- [x] T8.18 `skills/long-task-tdd/SKILL.md`：删除 mutation 引用
- [x] T8.19 `skills/long-task-tdd/SKILL.md.template`：同步
- [x] T8.20 `skills/long-task-tdd/testing-anti-patterns.md`：清理 mutation
- [x] T8.21 `skills/long-task-tdd/prompts/implementer-prompt.md`：清理 mutation
- [x] T8.22 `skills/long-task-init/SKILL.md`：清理 mutation
- [x] T8.23 `skills/long-task-init/references/init-script-recipes.md`：清理 mutation
- [x] T8.24 `skills/long-task-feature-st/SKILL.md.template`：清理 mutation
- [x] T8.25 `skills/long-task-feature-st/references/feature-st-execution.md`：清理 mutation
- [x] T8.26 `skills/long-task-feature-design/references/feature-design-execution.md`：清理 mutation
- [x] T8.27 `skills/long-task-feature-design/references/feature-design-template.md`：清理 mutation
- [x] T8.28 `skills/long-task-finalize/SKILL.md`：清理 mutation
- [x] T8.29 `skills/long-task-design/SKILL.md`：清理 mutation
- [x] T8.30 `skills/long-task-ats/SKILL.md`：清理 mutation
- [x] T8.31 `skills/long-task-explore/references/exploration-dimensions.md`：清理 mutation
- [x] T8.32 `skills/using-long-task/SKILL.md`：清理 mutation
- [x] T8.33 `skills/using-long-task/references/architecture.md`：清理 mutation
- [x] T8.34 剩余测试文件清理：test_validate_guide / test_check_real_tests / test_check_retro_auth / test_check_st_readiness

#### 8.3 文档/模板
- [x] T8.35 `docs/templates/design-template.md`：删除 mutation 相关
- [x] T8.36 `docs/templates/srs-template.md`：检查并删除 mutation 相关
- [x] T8.37 `README.md`：清理 mutation
- [x] T8.38 `README_EN.md`：清理 mutation
- [x] T8.39 `CLAUDE.md`：清理 mutation 规则
- [x] T8.40 `agents/codebase-locator.md`：清理 mutation
- [x] T8.41 `docs/README.opencode.md`：清理 mutation

#### 8.4 验证
- [x] T8.42 `git grep -i mutation` 结果仅剩 plan/diff 文档
- [x] T8.43 `pytest tests/` 全绿

### 主题 10：删除自定义 MCP & tool-binding 子系统

#### 10.1 删除脚本与模板
- [x] T10.1 删除 `scripts/apply_tool_bindings.py`
- [x] T10.2 删除 `scripts/check_mcp_providers.py`
- [x] T10.3 删除 `scripts/check_jinja2.py`
- [x] T10.4 评估 `scripts/check_devtools.py`：若仅服务自定义 MCP 删除；若服务 Chrome DevTools 启动探针则保留
- [x] T10.5 删除 `docs/templates/tool-bindings-template.json`
- [x] T10.6 删除 `tests/test_apply_tool_bindings.py`
- [x] T10.7 删除 `tests/test_check_mcp_providers.py`
- [x] T10.8 删除 `tests/test_check_jinja2.py`
- [x] T10.9 `tests/test_check_devtools.py` 按 T10.4 决策同步处理

#### 10.2 Skill 层
- [x] T10.10 `skills/long-task-init/SKILL.md`：删除 tool-bindings.json 生成步骤
- [x] T10.11 `skills/long-task-init/scripts/init_project.py`：删除 tool-bindings 逻辑
- [x] T10.12 `skills/long-task-work/SKILL.md`：删除 "apply tool bindings" 步骤
- [x] T10.13 `skills/long-task-work/SKILL.md.template`：同步
- [x] T10.14 `skills/long-task-feature-st/SKILL.md`：保留 Chrome DevTools MCP，移除自定义 MCP provider 映射段落
- [x] T10.15 `scripts/get_tool_commands.py`：移除 `--bindings` 选项
- [x] T10.16 `scripts/validate_guide.py`：审视并清理 tool-bindings 联动

#### 10.3 Hook
- [x] T10.17 `hooks/chrome-mcp-setup`：保留不动
- [x] T10.18 `hooks/hooks.json`：删除仅服务"自定义 MCP 绑定"的 hook 条目；保留 chrome-mcp-setup
- [x] T10.19 `hooks/session-start`：清理 tool-bindings 引用

#### 10.4 文档
- [x] T10.20 `CLAUDE.md`："Key Commands" 删除相关行；"Architecture" 移除自定义 MCP 子系统描述
- [x] T10.21 `README.md`：清理自定义 MCP 描述
- [x] T10.22 `README_EN.md`：清理自定义 MCP 描述

#### 10.5 验证
- [x] T10.23 `git grep -E "tool-binding|apply_tool_bindings|check_mcp_providers|check_jinja2"` 结果仅剩 plan/diff 文档
- [x] T10.24 `pytest tests/` 全绿

---

## 阶段 A 验收标准

- [x] `git grep -i mutation` 非良性匹配 = 0（GraphQL `type Mutation` 与 state mutation 保留；plan 文档除外）
- [x] `git grep "feature-report"` 仅剩 plan/diff 文档
- [x] `git grep -E "tool-binding|apply_tool_bindings|check_mcp_providers|check_jinja2"` 仅剩 plan/diff 文档
- [x] `python -m pytest tests/` 全绿（328 passed）
- [x] `skills/long-task-work/SKILL.md` 不再含 Step 11a
- [x] Chrome DevTools MCP 相关功能保留（`hooks/chrome-mcp-setup`、`scripts/check_devtools.py`、feature-st/SKILL 内 Chrome DevTools MCP 引用均保留）

---

## 阶段 B 任务清单

### 主题 6：env-guide.md 下沉 + 人工审批

- [x] T6.1 新建 `docs/templates/env-guide-template.md` 六板块模板（§1 服务生命周期 / §2 环境配置 / §3 构建与执行命令 / §4 存量代码库约束 / §5 测试环境依赖 / §6 人工审批记录）
- [x] T6.2 更新 `skills/long-task-init/SKILL.md` Step 5 — 生成六板块 env-guide.md + YAML frontmatter（首次 `approved_by: null` 豁免）
- [x] T6.3 新建 `scripts/check_env_guide_approval.py` — git 历史分析 §3/§4 最近变更 vs approved_date；`tests/test_check_env_guide_approval.py`（11 tests）
- [x] T6.4 新建 `scripts/validate_env_guide.py` — 六板块标题存在性 + frontmatter 格式校验；`tests/test_validate_env_guide.py`（10 tests）
- [x] T6.5 `skills/long-task-init/SKILL.md` Step 4 — long-task-guide.md 瘦身为"工作流导航 only"，build/test/coverage 命令下沉 env-guide.md §3
- [x] T6.6 `skills/long-task-work/SKILL.md` 新增 **Step 0: env-guide Approval Gate** — 调 `check_env_guide_approval.py`，未审批阻断
- [x] T6.7 `skills/long-task-quality/` + `skills/long-task-tdd/SKILL.md` 命令引用下沉到 env-guide.md §3
- [x] T6.8 `skills/long-task-design/SKILL.md` Step 4b — §13 codebase constraints 传播到 env-guide.md §4
- [x] T6.9 `skills/long-task-increment/SKILL.md` — 若 increment 触发 §3/§4 变更，提示用户更新 approval frontmatter
- [x] T6.10 `hooks/session-start` — advisory warning（Worker Step 0 是硬 gate）
- [x] T6.11 `python -m pytest tests/` 全绿（349 passed，含新增 21 tests）

### 主题 3：Worker SubAgent-per-Step 架构

- [x] T3.1 新建 `skills/long-task-work/references/structured-return-contract.md` — 统一契约（status / artifacts_written / next_step_input / blockers / evidence）+ DISPATCH 声明式语法说明 + Resume 协议
- [x] T3.2 Worker SKILL 所有 "REQUIRED SUB-SKILL: Invoke X" 替换为 DISPATCH blockquote 声明（Steps 4、5-7、8、9）
- [x] T3.3 `skills/long-task-tdd/SKILL.md` — 顶部声明 SubAgent Dispatch Mode；末尾追加 Structured Return Contract（TDD 保持单体 skill，不拆分三阶段）
- [x] T3.4 `feature-design` / `quality` / `feature-st` Return Contract 顶层字段对齐（保留 Metrics / Risks / Issues 等 extension 子表）；SKILL parse 逻辑同时接受 `**status**:` 与 legacy `### Verdict:`
- [x] T3.5 Worker Step 1 新增 Resume Check（读 `task-progress.md` `in-progress: step-N` 标记跳转）；Core principle 加 Resume protocol（每步 DISPATCH 前后写/更新标记）
- [x] T3.6 `python -m pytest tests/` 全绿

## 阶段 B 验收标准

- [x] `python -m pytest tests/` 349 passed（含 21 个 Stage B 新增测试）
- [x] `env-guide.md` 成为 build/test/coverage 命令与 codebase 约束的单一事实源
- [x] 未审批的 §3/§4 修改触发 Worker Step 0 阻断
- [x] Worker SKILL 所有 SubAgent 分发点使用 DISPATCH 声明式语法
- [x] 四个 discipline skill（feature-design / tdd / quality / feature-st）全部支持 SubAgent dispatch + Structured Return Contract
- [x] long-task-guide.md 仅含工作流导航；`validate_guide.py` 强制引用 env-guide.md
- [x] TDD 保持单体（单个 SubAgent 跑完 Red → Green → Refactor）

---

## 不采纳清单（重申 — 不实施）

- multi-repo / repos-manifest.json
- long-task-static-review / long-task-coverage-retrofit / long-task-mutation-retrofit 独立 skill
- TDD 拆分为三 skill
- 删除 UCD / ATS / ST / Real-Test / env-guide 子系统
- long-task-guide.md 简化为纯工具命令参考
- 删除 commit-msg hook / 自动提交
