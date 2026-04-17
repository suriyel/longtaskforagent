# Main 分支整改任务跟踪

> 分支: `main-improvement`
> 基础: `main`
> 方案: [MAIN-BRANCH-IMPROVEMENT-PLAN.md](MAIN-BRANCH-IMPROVEMENT-PLAN.md)
> 启动日期: 2026-04-17

## 当前会话目标

**阶段 C（功能/体验增强）** — 主题 2 / 4 / 7 / 9（阶段 A、B 已完成）

## 整体进度

| 阶段 | 主题 | 状态 | 备注 |
|---|---|---|---|
| A | 1. 去除用户呈现型报告 | ✅ 完成 | 删除 feature-report 子系统 |
| A | 8. 完全移除变异测试 | ✅ 完成 | schema/skill/template/test 全链路清理 |
| A | 10. 删除自定义 MCP & tool-binding | ✅ 完成 | 保留 Chrome DevTools MCP |
| B | 3. Worker SubAgent-per-Step | ✅ 完成 | DISPATCH 语法 + 统一 Return Contract + Resume 能力 |
| B | 6. rules/guide 下沉到 env-guide.md + 审批 | ✅ 完成 | 六板块 env-guide.md + check_env_guide_approval.py 审批 gate |
| C | 2. Increment 吸收 brownfield 适配 | ✅ 完成 | brownfield-adaptation.md + ESI + API Impact 表 |
| C | 4. 设计/Feature Design 瘦身 | ✅ 完成 | Feature Design 模板删 Algorithm/Pseudocode/Diagrams + 新增 Implementation Summary + Step 1c Existing Code Reuse Check + design §0 Project Structure |
| C | 7. 编译/UT 静默参数 | ✅ 完成 | Worker Core principle 声明 quiet protocol；TDD/Quality 明确 Re-check 协议 |
| C | 9. FR 合并 + ~1k LOC 颗粒度 | ✅ 完成 | Init Step 8b/8c 颗粒度确认 + Single-Round 模式 + context-budget 替代硬编码 |
| D | 5. 中文化 | ✅ 完成 | 术语表 + session-start 注入 + 57 份文档翻译（整体 CJK 比例 82.3%，不含代码块） |

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

## 阶段 C 任务清单

### 主题 2：Increment 吸收 brownfield 适配

- [x] T2.1 新建 `skills/long-task-increment/references/brownfield-adaptation.md`（ESI 构建、变更分类、API 影响与兼容性策略、§1.4 回填）
- [x] T2.2 `long-task-increment/SKILL.md` Step 1 加载 brownfield-adaptation.md 并构建 ESI
- [x] T2.3 Step 2 增强：按 §B/§C 变更分类（NEW/MODIFY/EXTEND/REUSE）+ REUSE 过滤
- [x] T2.4 Step 3 输出追加 "API 影响与兼容性" 表（file:line 精度 + 兼容策略 + impact_features）
- [x] T2.5 Step 4 §13 传播增强：Breaking API 必须同步更新 Design §6.2
- [x] T2.6 Step 6a 新增 5b 子步骤 — SRS §1.4 Existing System Context 回填
- [x] T2.7 Step 6b 修改 feature — `impact_note` 记录兼容性策略

### 主题 4：设计 / Feature Design 瘦身

- [x] T4.1 `feature-design-template.md` 删除 Component Data-Flow / Internal Sequence / Algorithm (Pseudocode + Flow Diagram) / State Diagram / Tasks 章节
- [x] T4.2 `feature-design-template.md` 新增 Implementation Summary + Boundary Conditions + Existing Code Reuse 章节
- [x] T4.3 `feature-design-execution.md` 同步精简；新增 Step 1c Existing Code Reuse Check（grep 代码库 + Maximize Reuse 原则）
- [x] T4.4 `feature-design/SKILL.md` Step 2 Key Constraints 加入 Step 1c 强制要求 + env-guide §4 约束引用
- [x] T4.5 `feature-design/SKILL.md` Step 4 解析字段更新（test_inventory_count / existing_code_reuse_count）
- [x] T4.6 `docs/templates/design-template.md` 新增 §0 Project Structure（§6.2 Internal API Contracts 已有）
- [x] T4.7 下游 references 同步：TDD SKILL §5.3/§5.4 → Boundary Conditions / Interface Contract Raises；feature-st §5c/§7 → 新章节名；structured-return-contract.md 示例对齐

### 主题 7：编译/UT 静默参数优化

- [x] T7.1 Worker SKILL 顶部 Core principle 新增 "Quiet execution protocol"（临时日志 + 按需提取 + Re-check 协议）
- [x] T7.2 `long-task-tdd/SKILL.md` After Writing Tests 改为详细 quiet 协议（exit file 优先、按需提取、失败回 30/100 行）
- [x] T7.3 TDD Refactor — 每次 change 只跑受影响测试；完成再跑全量
- [x] T7.4 TDD Refactor 静态分析命令改为 quiet 封装
- [x] T7.5 `long-task-quality/references/quality-execution.md` Gate 1 覆盖率命令改为 quiet + summary 提取

### 主题 9：FR 直接合并 + ~1k LOC 颗粒度

- [x] T9.1 `long-task-init/SKILL.md` Step 8 加入 FR 直接合并 rule；目标 ~1000 LOC (±500)
- [x] T9.2 新增 Step 8b Feature Sizing & Granularity Confirmation — 透明 LOC 公式 + 三段分类 + AskUserQuestion 确认
- [x] T9.3 新增 Step 8c Single-Round Mode — 读 SRS `Single-Round: Yes` → `feature-list.json` 根 `single_round: true`；合并带放宽到 ~2000 LOC
- [x] T9.4 Step 8b 显式 Count bounds 公式（context_budget 双向）替代硬编码 10-200
- [x] T9.5 `long-task-requirements/SKILL.md` 新增 Step 11b Single-Round Mode Declaration（可选 AskUserQuestion + SRS 前置 meta）

### 阶段 C 验证

- [x] T-C.1 `python -m pytest tests/` 全绿（349 passed）

## 阶段 C 验收标准

- [x] Increment skill 自动加载 brownfield-adaptation.md 并生成 ESI + API Impact 表
- [x] Feature Design 产物含 Implementation Summary 章节（取代 pseudocode/diagrams）
- [x] Feature Design Step 1c Existing Code Reuse Check 执行并落入 Existing Code Reuse 表
- [x] Design Template §0 Project Structure 可供 brownfield 项目填充
- [x] 所有 build/test/coverage 命令走 quiet 协议（exit-file 优先 + 失败时按需提取）
- [x] Re-check 协议成文（失败后只重跑失败项，最终再跑全量）
- [x] Init 颗粒度确认 gate（8b）在 feature 数超限时按 context-budget 提示用户
- [x] Single-Round 模式流通 SRS → Init → feature-list.json

---

## 阶段 D 任务清单

### 主题 5：中文化（策略 A — 分 SKILL 逐步翻译）

#### 5.1 基础设施
- [x] T5.1 新建 `docs/templates/glossary.md` — 术语表（§1-§9 + 附录 A/B，覆盖流程/工件/开发实践/代码架构/状态元数据/UI/Token/审批 8 大类）
- [x] T5.2 `hooks/session-start` — 注入 SessionStart hook JSON，通过 `additionalContext` 输出中文语言规则
- [x] T5.3 `skills/long-task-init/scripts/init_project.py` — 强化生成 CLAUDE.md 中的语言规则段落，指向 `docs/templates/glossary.md`

#### 5.2 翻译批次
- [x] T5.4 批次 A — 核心 phase SKILL（8 份，2782 行）：`using-long-task`、`long-task-requirements`、`long-task-ucd`、`long-task-design`、`long-task-ats`、`long-task-init`、`long-task-work`、`long-task-st`
- [x] T5.5 批次 B — discipline & 重入口 SKILL（9 份，1866 行）：`long-task-feature-design`、`long-task-tdd`、`long-task-quality`、`long-task-feature-st`、`long-task-increment`、`long-task-hotfix`、`long-task-finalize`、`long-task-retrospective`、`long-task-explore`
- [x] T5.6 批次 C — `skills/*/references/*.md` + `skills/*/prompts/*.md`（22 份；init-script-recipes.md 与 srs-reviewer-prompt.md 在主会话补译）
- [x] T5.7 批次 D — `agents/*.md`（7 份 subagent 规范）
- [x] T5.8 批次 E — `docs/templates/*.md`（9 份，不含 glossary.md）

#### 5.3 翻译规则（恒定）
- **翻译范围**：SKILL 指令正文、references 段落正文、template 段落正文、agents 正文
- **不翻译**：YAML frontmatter 的 `name`/`description` 字段值（description 简短英文便于路由匹配）、字段名（`srs_trace`/`feature_id`/`status` 等）、命令示例、工具名、commit message 示例、代码块
- **术语一致**：严格按 `docs/templates/glossary.md` 统一（Feature=特性；Gate=关卡；Worker=Worker；Hotfix=Hotfix；Wave=批次；SRS=SRS；FR=FR；ATS=ATS；ST=系统测试；UCD=UCD；Increment=增量）
- **数字/符号**：保留原 ASCII；编号保持原样（§1, FR-001）

### 阶段 D 验证
- [x] T-D.1 `python -m pytest tests/` 全绿（349 passed）
- [x] T-D.2 整体正文中文比例 82.3%（扣除代码块），无 <50% 问题文件；抽样 5 个核心 SKILL（using-long-task、long-task-init、long-task-work、tdd、agents/codebase-scanner）目测翻译流畅，YAML frontmatter / 代码块 / 字段名 / 编号均按规则保留英文

## 阶段 D 验收标准

- [x] 所有 SKILL/agents/templates 正文**非代码块**中文覆盖率 ≥ 80%（实际 82.3%，含表格字段名/缩写/编号等必须保留的英文后合理）
- [x] 术语表 `docs/templates/glossary.md` 存在且覆盖 §1–§9 共 9 类核心术语 + 附录 A/B
- [x] `hooks/session-start` 通过 SessionStart hook JSON 注入中文语言规则（`additionalContext`）
- [x] Init 脚本生成的消费项目 CLAUDE.md 语言规则段落强化，指向术语表
- [x] `pytest tests/` 349 passed

---

## 不采纳清单（重申 — 不实施）

- multi-repo / repos-manifest.json
- long-task-static-review / long-task-coverage-retrofit / long-task-mutation-retrofit 独立 skill
- TDD 拆分为三 skill
- 删除 UCD / ATS / ST / Real-Test / env-guide 子系统
- long-task-guide.md 简化为纯工具命令参考
- 删除 commit-msg hook / 自动提交
