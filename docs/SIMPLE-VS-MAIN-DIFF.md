# Simple 分支 vs Main 分支 差异分析

> 本文档用于后续将 simple 分支的改进同步/回迁到 main 分支。
> 生成日期: 2026-04-17
> 基准点: simple 相对 main 领先 129 commit, main 相对 simple 独有 26 commit（大部分已同名 cherry-pick 到 simple）。
>
> **总体定位**: Simple 分支是对 main 的"精简化 + 能力扩展"重构。**精简**方面移除 UI/MCP/UCD/ATS/ST/Retrospective/Tool-Binding 等高耦合子系统，把流水线收敛为 `Requirements → Design → Init → Worker → Finalize`；**扩展**方面新增 brownfield 扫描、multi-repo、retrofit 系列、static-review、TDD 三阶段拆分、targeted-explore 等能力。

---

## 目录

1. [流水线精简（已移除的子系统）](#1-流水线精简已移除的子系统)
2. [Skill 架构重构](#2-skill-架构重构)
3. [新增独立能力（Standalone Skills）](#3-新增独立能力standalone-skills)
4. [Brownfield（存量代码库）能力体系](#4-brownfield存量代码库能力体系)
5. [Multi-Repo（多仓库）能力体系](#5-multi-repo多仓库能力体系)
6. [Retrofit（存量仓库改造）能力体系](#6-retrofit存量仓库改造能力体系)
7. [TDD 三阶段拆分](#7-tdd-三阶段拆分)
8. [Requirements 阶段增强](#8-requirements-阶段增强)
9. [Design 阶段调整](#9-design-阶段调整)
10. [Init / feature-list.json schema 变更](#10-init--feature-listjson-schema-变更)
11. [Worker 架构重构（SubAgent-per-Step）](#11-worker-架构重构subagent-per-step)
12. [Hook 与 Session Start 调整](#12-hook-与-session-start-调整)
13. [脚本（scripts/）清理](#13-脚本scripts清理)
14. [模板（docs/templates/）清理](#14-模板docstemplates清理)
15. [测试（tests/）清理](#15-测试tests清理)
16. [Agent（agents/）清理](#16-agentagents清理)
17. [输出/Token 优化](#17-输出token-优化)
18. [Dispatch 语义演化](#18-dispatch-语义演化)
19. [语言 / 国际化](#19-语言--国际化)
20. [杂项改进](#20-杂项改进)
21. [回迁优先级与风险建议](#21-回迁优先级与风险建议)

---

## 1. 流水线精简（已移除的子系统）

Simple 分支整体将 main 的 `Requirements → UCD → Design → ATS → Init → Worker → ST → Finalize` 七阶段收敛为 `Requirements → Design → Init → Worker → Finalize` 五阶段。

### 1.1 UCD（User-Centered Design）子系统 — 已移除
- 删除 `skills/long-task-ucd/SKILL.md`
- 删除所有 UCD 文档产物（`docs/plans/*-ucd.md`）的引用
- Router 不再检测 UCD 阶段；UI 特性识别、视觉契约、Blank canvas 校验等全部删除
- **回迁评估**: 若 main 仍需保留 UI 项目支持，需决定是将 UCD 彻底下线，还是作为可选的"UI 预处理"独立 skill 保留。

### 1.2 ATS（Acceptance Test Scenarios）子系统 — 已移除
- 删除 `skills/long-task-ats/SKILL.md`
- 删除 `agents/ats-reviewer.md`
- 删除 `scripts/validate_ats.py`、`scripts/check_ats_coverage.py`
- 删除 `docs/templates/ats-template.md`
- 删除 `tests/test_validate_ats.py`、`tests/test_check_ats_coverage.py`
- Feature Design Step "Test Inventory INTG category" 相关逻辑同步简化
- **替代**: 用 `srs_trace` + Feature Design 的 Test Inventory 直接覆盖，不再有独立的 ATS→场景→UI 标志传导链

### 1.3 ST（System Testing）子系统 — 已移除
- 删除 `skills/long-task-st/SKILL.md` 及 `SKILL.md.template`
- 删除 `skills/long-task-st/references/st-recipes.md`
- 删除 `skills/long-task-feature-st/` 整个目录（SKILL.md + template + references/feature-st-execution.md）
- 删除 `scripts/check_st_readiness.py`、`scripts/validate_st_cases.py`
- 删除 `docs/templates/st-case-template.md`
- 删除 `tests/test_check_st_readiness.py`、`tests/test_validate_st_cases.py`
- `long-task-finalize` 合并进 `long-task-st` Step 13 的逻辑（commit f855f10）后续在 `ab91867` 中被整体移除，finalize 相关能力也一并下线
- **影响**: 原本 Worker 完成后进入 ST → Finalize 的链路被打断；simple 分支目前没有"所有特性通过 → 系统级验收 → 发布"这一层

### 1.4 Quality 独立 skill — 已移除
- 删除 `skills/long-task-quality/SKILL.md` 及其 `references/quality-execution.md`
- 合并进 `long-task-work` 作为 inline SubAgent dispatch（commit b8c0559）
- 后续又进一步演化：`e648cb9` 将 quality-gates 拆为 `check + coverage-fix + mutation-fix` 三段 + gate-fix-recheck 循环
- 最新状态（commit 9defa46）已从 work 流水线中移除 quality gate 循环，gate 能力独立成 `coverage-retrofit` / `mutation-retrofit` 两个 standalone skill

### 1.5 Retrospective 子系统 — 已移除
- 删除 `skills/long-task-retrospective/SKILL.md` 及 `prompts/reflection-prompt.md`
- 删除 `agents/reflection-analyst.md`
- 删除 `scripts/check_retro_auth.py`、`scripts/check_retrospective_readiness.py`、`scripts/post_retrospective_report.py`、`scripts/validate_retrospective_record.py`
- 删除 `docs/templates/retrospective-record-template.md`
- 删除对应 4 个测试文件
- `retro_api_endpoint`、`retro_authorized` 字段从 feature-list.json 中删除

### 1.6 MCP / Tool-Binding 子系统 — 已移除
- 删除 `scripts/apply_tool_bindings.py`、`scripts/check_mcp_providers.py`、`scripts/check_devtools.py`、`scripts/check_jinja2.py`
- 删除 `docs/templates/tool-bindings-template.json`
- 删除 `hooks/chrome-mcp-setup`
- 删除对应测试文件
- 意味着 UI 特性 → Chrome DevTools MCP → 视觉渲染契约整条链路下线

### 1.7 UI / Real-Test / env-guide 子系统 — 已移除
- 删除 `skills/long-task-tdd/references/ui-error-detection.md`
- 删除 `scripts/check_real_tests.py` 及 `tests/test_check_real_tests.py`
- 删除 `scripts/check_configs.py` 及测试（`required_configs[]` 整套下线）
- 删除 `init.sh` / `init.ps1` / `.env.example` / `env-guide.md` 生成（commit f3ac925 "Remove NFR, deployment/CI-CD, env-guide, and init environment subsystems"）
- 删除 server startup output 要求（commit 39b0b8e）

### 1.8 自动 git commit / 提交规范子系统 — 已简化
- 删除 auto commit / staging 逻辑（commit ed87037）
- `commit-msg` hook 曾被加入（9677c8d）后又删除（7cd6915）
- 最终 `build_system` 和 `commit_conventions` 作为元数据字段进入 feature-list.json，由 Worker 读取但不再强制

### 1.9 Feature Report 生成 — 已移除
- `docs/templates/feature-report-template.md` 已删除
- `docs/report/feature-*-report.md` 生成逻辑移除（commit 12ad9c7 "remove Step 10a Generate Feature Report and all dependencies"）

### 1.10 Config Gate — 已移除
- `required_configs` 整套 gate 逻辑移除（commit d0dba9b）

---

## 2. Skill 架构重构

### 2.1 Skill 总数与组织
- main: 14 skills（phase 8 + standalone 1 + discipline 4 + meta 2 左右）
- simple: 约 18 skills，按用途重新分组为：**Phase / Standalone / Discipline**

### 2.2 新增 Skills（simple 独有）
| Skill | 类型 | 作用 |
|---|---|---|
| `long-task-codebase-scanner` | Phase 0-pre + Standalone | 存量代码库扫描，生成 `docs/rules/*.md`；从 SubAgent 升级为独立 skill |
| `long-task-multi-repo` | Phase 0-multi | 多仓库探索/拆分/依赖分发 |
| `long-task-explore` | Standalone | 按需深度探索（架构/数据流/领域/API/依赖/代码健康） |
| `long-task-static-review` | Standalone | 推送前静态分析（Checkstyle 等），迭代扫描-修复至 0 违规 |
| `long-task-coverage-retrofit` | Standalone | 存量代码 UT 覆盖率改造（迭代 measure→fix→verify） |
| `long-task-mutation-retrofit` | Standalone | 存量代码变异测试改造 |
| `long-task-coverage-fix` | 内部工具 skill | 被 coverage-retrofit 调用的单轮 fix 子 skill |
| `long-task-mutation-fix` | 内部工具 skill | 被 mutation-retrofit 调用的单轮 fix 子 skill |
| `long-task-tdd-red` | Discipline | TDD Red 独立 skill |
| `long-task-tdd-green` | Discipline | TDD Green 独立 skill |
| `long-task-tdd-refactor` | Discipline | TDD Refactor 独立 skill（含 §11 合规/静态分析） |
| `long-task-tdd-shared` | Shared refs | iron-law / testing-anti-patterns 共享引用 |

### 2.3 被移除 Skills
- `long-task-ucd`、`long-task-ats`、`long-task-st`、`long-task-feature-st`、`long-task-quality`、`long-task-finalize`、`long-task-retrospective`
- `long-task-tdd`（单体 TDD）被拆分为三阶段

### 2.4 Router 重写
`using-long-task/SKILL.md` 从 main 的 8-phase 路由表简化为 5-phase，并新增以下路由分支：
- `repos-manifest.json` 存在 → 直接进入 `long-task-multi-repo`（router 本身只处理单仓库）
- `bugfix-request.json` → hotfix（最高优先级，逻辑保留）
- `increment-request.json` → increment（保留）
- `>3 源文件 + ≥5 commits + 无 docs/rules/` → 先走 `long-task-codebase-scanner`
- **不再依赖 session-start 注入**（commit a21088c `refactor: remove session-start bootstrap injection, rely on native skill discovery`），改为原生 skill description 自发现

---

## 3. 新增独立能力（Standalone Skills）

### 3.1 `/deep-explore` — 深度代码库探索
- 路径：`skills/long-task-explore/`
- 子 SubAgent：`codebase-locator`、`codebase-analyzer`、`codebase-pattern-finder`
- 维度：架构、数据流、领域模型、API 表面、依赖、代码健康/债务
- 触发方式：`/deep-explore [quick|standard|deep] [--focus area] [--path dir]`
- 深度启发式：commit `b755eb1` 将硬编码 depth 替换为 context-driven heuristics
- 产物：`docs/explore/codebase-research.md`

### 3.2 `/static-review` — 推送前静态分析
- 路径：`skills/long-task-static-review/`
- 参考：`references/tool-profiles.md`（预置 Checkstyle profile）
- 自动检测工具 → 扫描 → 修复 → 重编 → UT → 变异 → 复扫 → 循环至 0 违规
- 参数：`--tool checkstyle | --max-iterations N | --path dir | --dry-run`

### 3.3 `/coverage-retrofit` — 存量覆盖率改造
- 路径：`skills/long-task-coverage-retrofit/`
- 流程：`detect env → baseline → long-task-coverage-fix SubAgent → re-measure → repeat until 行/分支 达阈值`
- 支持 `--branch <branch>` 差异模式（仅对该分支增量的代码改造）
- 阈值参数：`--line-cov N | --branch-cov N | --max-iterations N`

### 3.4 `/mutation-retrofit` — 存量变异测试改造
- 路径：`skills/long-task-mutation-retrofit/`
- 与 coverage-retrofit 对称：`detect → baseline → mutation-fix SubAgent → re-measure → 至分数达阈值`
- 支持 `--branch <branch>` 增量模式，支持 `--skip-coverage-check`

### 3.5 共享引用
- `long-task-tdd-shared/references/iron-law.md` 与 `testing-anti-patterns.md` 被上述 retrofit 系列通过 symlink 共享，避免复制漂移

---

## 4. Brownfield（存量代码库）能力体系

### 4.1 `long-task-codebase-scanner`
- 从 main 的 SubAgent（`agents/codebase-scanner.md`）升级为独立 skill
- 产物：`docs/rules/*.md` — 覆盖 coding style、2/3 方件 约束、build 模式、UT 框架等
- 触发条件（rule 7b 与 5b）：`>3 源文件 + ≥5 commits + 无 docs/rules/`
- **关键变化**：
  - 新增 UT framework 自动检测（commit e2447b9）
  - `long-task-guide.md` 新增 "UT Style" 章节与对应校验（commit cab4c93）
  - `--next-skill chaining` 被移除，router 自己负责下一跳（commit b645899）
  - 改为通过 Agent 显式 dispatch 以规避 `subagent_type` 解析失败（commit 73e50d8、3924b69）

### 4.2 Requirements 阶段 brownfield 适配
- 新增 `skills/long-task-requirements/references/brownfield-adaptation.md`
- commit bb6e680 "add brownfield adaptation for requirements elicitation"
- Step 1.6：brownfield 且有具体焦点 → 自动触发 `long-task-explore`（quick/standard），非阻塞

### 4.3 Increment 阶段 brownfield 适配
- Increment Step 3.5：同样自动触发 targeted explore（commit 07b4887）

### 4.4 Design 阶段合并
- Design §11 合并 `docs/rules/` 内容作为 §11.1 必选内部库 / §11.2 禁用 API 约束（替换 main 原 §13）
- 新增 §0 "Project Structure" 章节（commit c40c63f）
- 新增 §6.2 "internal API contracts"（commit c6302c9）

---

## 5. Multi-Repo（多仓库）能力体系

main 完全没有此能力，simple 新增一整套：

### 5.1 检测
- `hooks/session-start` 扫描子目录 git 仓库，生成 `repos-manifest.json`
- commit 链：15f430c（初版）→ 25b9948（验证独立 repo）→ a415034（5 项 review 修复）→ be91339（静默失败修复）→ a29c5ff（trailing comma 修复）→ 73187cb（pwd vs show-toplevel 不一致）→ cf0fe58（Windows `\r` 处理）→ 8c49e6a（移除 show-toplevel 对比）→ 4ae6499（manifest 合并而非覆盖）→ 362c72b（用 skip-if-exists 代替 JSON merge）

### 5.2 独立 skill
- 初期 multi-repo 逻辑混在 requirements 中，commit 0129d8d 将其抽成独立 `long-task-multi-repo` skill
- 路径：`skills/long-task-multi-repo/`
- 复用 requirements 的 references/prompts（通过 symlink）
- 流程：探索所有 repo → 全局 SRS 初稿 → 拆分为 per-repo SRS 携带 IFR 契约 → 依赖文件分发（参考文档、global-srs、deferred backlog、cross-repo deps）

### 5.3 新增产物
- `repos-manifest.json`
- `docs/plans/*-srs.md`（项目根，作为全局 SRS）
- `<repo>/docs/plans/global-srs.md`（子仓副本）
- `<repo>/docs/plans/cross-repo-deps.md`
- `<repo>/docs/references/*`（用户参考文档复制）

### 5.4 子仓 Init 支持
- commit 6d9c469：复制 `init_project.py` 与 plugin-root hint 到每个子仓，支持子仓独立走 Init

### 5.5 规则更新
- `rule 5`（brownfield gate）加上 multi-repo 分支：子仓同样触发 codebase-scanner（commit 88f38c1）
- Single-round 模式跨仓传播 + per-repo LOC sizing（commit fb5738b）

---

## 6. Retrofit（存量仓库改造）能力体系

### 6.1 初始形态
- commit 1451ea6：一个统一 `test-retrofit` skill

### 6.2 拆分
- commit 700e565：拆分为 `coverage-retrofit` + `mutation-retrofit` 两个 standalone skill，对应各自的 fix SubAgent

### 6.3 能力特性
- 迭代收敛至阈值
- 支持 `--branch <branch>` 增量（只对 diff 涉及代码改造），这是 main 不具备的能力
- 共享 `iron-law.md` 与 `testing-anti-patterns.md`（符号链接）

---

## 7. TDD 三阶段拆分

### 7.1 动机
main 的 `long-task-tdd` 是单体 skill。simple 分支拆分目的：
- 每步独立 SubAgent dispatch，避免上下文膨胀
- 每步可独立调用（例如 hotfix 可以只做 Red + Green）
- 每步结构化返回契约，防止 subagent 结果握手错误

### 7.2 新增 skills
- `long-task-tdd-red`：为 Test Inventory 写失败测试
- `long-task-tdd-green`：最小实现让所有测试通过
- `long-task-tdd-refactor`：清理 + 静态分析 + §11 合规（合并原 quality 的静态分析环节）

### 7.3 TDD Red 新能力
- commit a3d8968：Step 1b 探索 feature 相关存量 UT
- commit bfab3ac：为 Red/Green/Refactor 三阶段都加上"先 grep 现有 patterns"提示

### 7.4 保留 redirect
- 旧 `long-task-tdd/SKILL.md` 保留，作为 redirect → 三阶段

### 7.5 Iron Law & Anti-Patterns
- 抽到 `long-task-tdd-shared/references/`，被 3 阶段通过 symlink 共享

---

## 8. Requirements 阶段增强

### 8.1 Tiered deep-dive elicitation
- commit aae2381：分层 deep-dive elicitation（Lite 3-5 轮 / Expert 10-20 轮）

### 8.2 新增 references
- `brownfield-adaptation.md`（新）
- `problem-framing.md`、`scenario-walkthrough.md`、`hypothesis-correction.md`、`alignment-validation.md` 均有大幅内容重写

### 8.3 Single-Round 模式
- commit 33846b6 + 47bbcfe：Step 10c 确认 Single-Round；不限 FR 数量
- 对应 feature-list.json 引入 `single_round` 字段

### 8.4 Context-budget 特性计数
- commit 9724595：用双向 context-budget sizing 替换硬编码 10-200+ 特性数

### 8.5 Hidden needs 与 SRS 结构重构
- commit fe94278：重构 hidden needs 与 SRS 需求结构

### 8.6 Targeted explore 嵌入
- commit 07b4887：requirements/increment 阶段 brownfield 时自动 quick/standard 探索

### 8.7 Caveat 提示
- commit 7fed44c：启发式 guide 生成加 caveat prompts

---

## 9. Design 阶段调整

### 9.1 §0 Project Structure
- commit c40c63f：design-template 与 feature-design-template 增加 §0 章节

### 9.2 §6.2 Internal API contracts
- commit c6302c9：设计阶段新增内部 API 契约与集成一致性检查

### 9.3 §11 Codebase Constraints（原 §13）
- brownfield 场景将 `docs/rules/*.md` 的约束合并进 Design §11：
  - §11.1 强制内部库
  - §11.2 禁用 API
- commit 8e8f223：feature-design 流水线强制执行 §11 + 复用现有代码
- commit 8160dba：feature-design Step 1c 加入 codebase exploration + 最大化复用原则

### 9.4 Visual tracking（Mermaid 图）约定
- commit d31a322：4+1 视图 Mermaid 图的视觉变更跟踪约定

---

## 10. Init / feature-list.json schema 变更

### 10.1 新增字段
| 字段 | 说明 | 引入 commit |
|---|---|---|
| `single_round` | 布尔，来源 SRS `Single-Round: Yes` | 33846b6 / 47bbcfe |
| `build_system` | 元数据（maven/gradle/npm/pip/...） | 7cd6915 |
| `commit_conventions` | 元数据，不再强制 hook | 7cd6915 |
| `quality_gates` | 重新回归（commit 86c8b6a） | 86c8b6a |

### 10.2 删除字段
- `required_configs[]`（随 Config Gate 移除）
- `ats_template_path`、`ats_review_template_path`、`ats_example_path`
- `st_case_template_path`、`st_case_example_path`
- `retro_api_endpoint`、`retro_authorized`
- `mutation_full_threshold`（quality gate 拆分后失去意义）

### 10.3 Feature 对象变更
- `verification_steps` 字段弱化为可选（commit fb213ee：`srs_trace` 替代）
- 新增 `srs_trace: ["FR-001"]` **强制**字段（每个 feature 必须映射至少一个 SRS 需求）
- 新增 `category: "core|bugfix"`，bugfix 时附加 `bug_severity / bug_source / fixed_feature_id / root_cause`
- 新增 `deprecated + deprecated_reason + supersedes`
- 新增 `wave` 引用批次

### 10.4 Init 脚本
- `scripts/init_project.py`（新文件）+ `skills/long-task-init/scripts/init_project.py`（更新）
- 支持 `--lang python|java|typescript`
- `--line-cov / --branch-cov / --mutation-score` 旧参数在 main 存在；simple 保留但 quality gate 逻辑变化

### 10.5 Tech stack
- `tech_stack` 增加 `coverage_tool` / `mutation_tool` 自动检测

---

## 11. Worker 架构重构（SubAgent-per-Step）

### 11.1 核心重构
- commit a5e3cbc：Worker 拆成 SubAgent-per-Step 架构
- commit 2135b63：修复 dispatch 架构 + 将 5 个 discipline skill 转为 inline execution
- commit 125dd3b：Feature Design skill 由 SubAgent dispatch 转为 inline

### 11.2 结构化返回契约
- commit da358bf：TDD discipline skills 增加 Structured Return Contracts，修复 subagent 结果握手错误

### 11.3 Quality gate 循环
- commit e648cb9：拆成 `check + coverage-fix + mutation-fix + gate-fix-recheck loop`
- commit 2c32191：默认 feature-scoped
- commit 6f969ad：移除 full-scope 逻辑，统一 feature-scoped
- commit 9defa46：最终从 work 流水线中**整体移除** quality gate loop，将该能力交给 retrofit 独立 skill

### 11.4 Resume 能力
- commit 63fe496：Worker Step 1 支持从被中断的 step 恢复

### 11.5 Static analysis gate 迁移
- commit 45251d4：静态分析 gate 从 ST 迁到 TDD Refactor

### 11.6 Bootstrap smoke test 移除
- commit 06ee5fd

### 11.7 On Error section 移除
- commit 841e5b4：移除 long-task-work 中冗余 On Error 章节

---

## 12. Hook 与 Session Start 调整

### 12.1 Session Start 重写
- main 的 session-start 含 bootstrap 注入 + MCP setup 触发
- simple：
  - 去除 bootstrap 注入（commit a21088c），依赖 skill 原生自发现
  - 加入 multi-repo 检测（commit 15f430c 及后续一连串 fix）
  - 中文语言规则注入（commit 66e4378、fa18dca）
  - 自适应 commit-msg hook 自装载（commit 9677c8d）→ 后又移除（commit 7cd6915）

### 12.2 `hooks/hooks.json` 修复
- commit a29c5ff：trailing comma 导致 hook 不加载
- commit 7cd6915：移除 commit-msg hook

### 12.3 `hooks/chrome-mcp-setup` 整个删除
- 随 UI / MCP 子系统下线

---

## 13. 脚本（scripts/）清理

### 13.1 已删除
| 脚本 | 原用途 |
|---|---|
| `analyze-tokens.py` | token 统计工具 |
| `apply_tool_bindings.py` | tool-binding 生成 |
| `check_ats_coverage.py` | ATS 覆盖度 |
| `check_configs.py` | required_configs gate |
| `check_devtools.py` | DevTools MCP 校验 |
| `check_jinja2.py` | 模板 jinja2 校验 |
| `check_mcp_providers.py` | MCP 提供方校验 |
| `check_real_tests.py` | Real-test gate |
| `check_retro_auth.py` | 回顾授权 |
| `check_retrospective_readiness.py` | 回顾就绪检查 |
| `check_st_readiness.py` | ST 就绪检查 |
| `find-polluter.sh` | 测试污染定位 |
| `post_retrospective_report.py` | 回顾上报 |
| `validate_ats.py` | ATS 校验 |
| `validate_retrospective_record.py` | 回顾记录校验 |
| `validate_st_cases.py` | ST 用例校验 |

### 13.2 已新增/大幅改动
- `scripts/init_project.py`（新增项目根级副本）
- `scripts/.long-task-plugin-root`（新增占位，供子仓 init 定位 plugin 根）
- `scripts/get_tool_commands.py`（+617/-, 配合新 tech_stack & UT style）
- `scripts/validate_features.py`（-212 行，删除 ATS/ST/retro 字段校验）
- `scripts/validate_guide.py`（-87 行，适配纯工具命令参考）

---

## 14. 模板（docs/templates/）清理

### 14.1 已删除
- `ats-template.md`
- `feature-report-template.md`
- `retrospective-record-template.md`
- `st-case-template.md`
- `tool-bindings-template.json`

### 14.2 已调整
- `design-template.md`：+§0 项目结构、+§6.2 API 契约、§11 合并 rules、内容重构
- `srs-template.md`：single-round 字段、hidden needs 结构、brownfield 章节
- `deferred-backlog-template.md`：微调
- `explore-report-template.md`：对齐 long-task-explore
- `rules-index-template.md`：配合 codebase-scanner 输出

### 14.3 新增
- `feature-design-template.md`（从 init-script-recipes 拆出，放入 `skills/long-task-feature-design/references/`）

---

## 15. 测试（tests/）清理

### 15.1 已删除
对应被移除脚本的测试全部删除（14 个测试文件）。

### 15.2 已调整
- `test_get_tool_commands.py`：+376 行，适配新字段
- `test_init_project.py`：+93 行
- `test_validate_features.py`：-613 行，删除 ATS/ST/retro 字段用例
- `test_validate_guide.py`：-323 行，简化为 tool command 校验

---

## 16. Agent（agents/）清理

### 16.1 已删除
- `agents/ats-reviewer.md`（随 ATS 下线）
- `agents/codebase-scanner.md`（升级为独立 skill）
- `agents/example-generator.md`（不再用于示例生成）
- `agents/reflection-analyst.md`（随 retrospective 下线）

### 16.2 已调整（配合 long-task-explore 与 scanner 升级）
- `codebase-analyzer.md`：-118/+？
- `codebase-locator.md`
- `codebase-pattern-finder.md`

---

## 17. 输出/Token 优化

Simple 分支围绕 "减少 subagent/工具输出污染、降低 token 消耗" 做了一轮系统改造：

| Commit | 说明 |
|---|---|
| `10efa9f` | **核心**：build/test/mutation 命令改为"临时文件捕获 + 按需提取"模式，避免把长输出塞回 LLM 上下文 |
| `98002fa` | quiet commands 由 bash 字符串改为 `(cmd, instruction)` 声明式格式 |
| `faf375e` | TDD Red/Green 阶段：明确 exit 语义，强制 quiet execution protocol |
| `d98b7cf` | 流水线整体精简以减少 token 消耗 |
| `5d05b9b` | Quality Gates SubAgent prompt 简化 |
| `df7baeb` | 澄清 re-check 流程，减少重复执行 |
| `0350131` | architecture.md、init-script-recipes.md 瘦身 -196 行 |
| `d33e784` | 删除未用 utilities（analyze-tokens、find-polluter、roadmap） |
| `39b0b8e` | 移除 server 特性启动输出要求 |

**回迁要点**：这组改动横跨多个 skill 的执行协议，建议作为一个独立主题一次性回迁，而不是挑 cherry。主要入口文件：
- `skills/long-task-work/SKILL.md`
- `skills/long-task-init/SKILL.md`
- `skills/long-task-tdd-red/SKILL.md`、`tdd-green/SKILL.md`、`tdd-refactor/SKILL.md`
- `skills/long-task-feature-design/references/feature-design-execution.md`

---

## 18. Dispatch 语义演化

### 18.1 DISPATCH 声明式引用
- commit `e2d51b9` "Replace Agent()/Task() tool-call syntax with declarative DISPATCH blockquotes for universal LLM compatibility"
- commit `c1d3ffc` "Clarify DISPATCH semantics: launch independent SubAgent to load and execute the Skill"
- commit `1ce10c0` "Emphasize independent SubAgent at front of DISPATCH declarations"
- commit `dc395f6` / `fc792a4` / `9b26d47` / `5b12918` / `a7a7fce` / `ef19cf1` / `aa336fc`：多轮细化

### 18.2 为何重要
main 使用 `Agent()` / `Task()` 具体工具调用，在 OpenCode 等多 LLM 运行时下兼容性差。simple 采用 markdown blockquote 声明 DISPATCH 语义，不绑定特定工具名，可回迁作为 LLM-agnostic 规范。

---

## 19. 语言 / 国际化

### 19.1 中文注入
- commit `66e4378` "add Chinese (Simplified) language rule to session injection and init template"
- commit `fa18dca` "propagate Chinese language rule to pre-init phase skills and agents"
- commit `ad95f74` "Translate all skill, agent, and template content from English to Chinese"
- 后续 commit `8c90371` + `ecf2ff6` 把 language rule 从 SKILL.md 中移除（保留在 session 注入），避免单文件绑定

### 19.2 Session injection
- `hooks/session-start` 注入 `# 语言：简体中文（Simplified Chinese）` 规则

---

## 20. 杂项改进

- commit `2bf62e3` "update init scaffold for UCD phase, UI features, and new helper scripts" — 后被 ab91867 大部分 revert，但 init_project.py 本体保留了对新 feature-list schema 的支持
- commit `fe94278` 重构 SRS hidden needs 结构
- commit `4a7f1e0` — 用直接合并替换 FR 分组；加入 ~1k LOC sizing target 和 Step 10b 颗粒度确认
- commit `3924b69` — Codebase-scanner 通过独立 SubAgent dispatch
- commit `ffe1ad8` — feature-design 用 implementation summary 替换 pseudocode/diagrams
- commit `44881a2` / `8c90371` / `406e560` — 多轮 SKILL.md 清晰化
- commit `7b92187` — 新增 long-task-static-review skill
- commit `d31a322` — 4+1 Mermaid 图视觉变更跟踪
- commit `fb5738b` — single-round 跨仓传播、per-repo LOC sizing、post-split 颗粒度 re-check
- commit `59b6a9e` / `e78a34b` — install 脚本加分支选择，默认 simple
- commit `aae2381` — tiered deep-dive elicitation
- commit `c83f60a` — `.gitignore` 加入临时开发文件（可回迁）
- commit `abd589b` — 视觉渲染验证管线（GAN-inspired）** ← 此 commit 在 main 中也存在（`962f2b0`），属早期共享历史**

---

## 21. 回迁优先级与风险建议

按照 **必须回迁 / 推荐回迁 / 可选 / 不建议** 分级：

### 21.1 必须回迁（架构性改进）
1. **Multi-Repo 支持**（`long-task-multi-repo` skill + 相关 hook 修复）
   - 风险：需配合 `repos-manifest.json` 合约；Windows Git Bash 兼容修复（cf0fe58、8c49e6a）不可遗漏
2. **Brownfield 体系**（codebase-scanner 升级 + brownfield-adaptation.md）
   - 风险：与 main 现有 ATS/ST gate 可能重叠，需决定保留哪套
3. **TDD 三阶段拆分**（red/green/refactor）
   - 风险：main 的 SubAgent 签名与 structured return contract 需同步实现
4. **Targeted explore 嵌入**（requirements Step 1.6、increment Step 3.5）
5. **Retrofit 系列**（coverage-retrofit、mutation-retrofit，含 `--branch` 增量能力）
6. **DISPATCH 声明式语法**（LLM 兼容性）
7. **srs_trace 强制字段**（已经在 main：commit fb213ee 属同源，确认一致即可）

### 21.2 推荐回迁（质量提升）
8. **Single-Round 模式**（feature-list.json `single_round` 字段、Step 10c 确认）
9. **Context-budget sizing** 替代硬编码特性数
10. **Worker Resume**（Step 1 从中断 step 恢复）
11. **Quiet 命令声明式格式**（98002fa）
12. **静态分析 gate 迁移至 TDD Refactor**（45251d4）
13. **`/static-review` 标准化**
14. **`/deep-explore` 标准化**
15. **`.long-task-plugin-root` 定位机制**（多仓 init 需要）

### 21.3 可选回迁（需决策）
16. **UCD/ATS/ST/Retrospective 是否一并下线**
    - 决策依据：main 是否仍面向 UI 项目 / 是否还需要系统级验收
    - 若保留，建议做成"可选 gate"而非强制 phase
17. **MCP / Tool-Binding 子系统是否保留**
    - 决策依据：Chrome DevTools 视觉验证需求是否仍存在
18. **auto commit / commit-msg hook 是否保留**
    - simple 最终采"元数据 + 不强制 hook"的折中方案（commit 7cd6915）
19. **语言规则注入**（中文）：按 main 目标受众决定

### 21.4 不建议回迁
20. **session-start bootstrap 注入移除**（a21088c）
    - 风险：部分 LLM 运行时不支持原生 skill 自发现，强行移除会退化体验
    - 建议 main 保留 bootstrap 注入作为兜底

### 21.5 通用风险点
- `validate_features.py` 与 `validate_guide.py` 大幅瘦身后，无法再校验 ATS/ST/retro 字段。如果 main 保留这些子系统，回迁这两个脚本需用"叠加式"而非"替换式"合并。
- `feature-list.json` schema 的字段增减是破坏性变更。回迁时需考虑历史项目迁移脚本（simple 目前没有迁移脚本）。
- 多处 `symlink` 引用（references 目录）在 Windows 下行为不同；回迁时如果 main 目标环境含 Windows，建议改为脚本 sync 或 `include` 指令。
- `hooks/session-start` 中的 Windows `\r` 处理、pwd vs show-toplevel 等 bugfix 必须整体 cherry-pick，否则 multi-repo 检测会静默失败。

---

## 附录 A：完整新增文件清单（37 个）

```
long-task-agent.skill                                                      (二进制打包产物)
scripts/.long-task-plugin-root                                             (plugin 根定位)
scripts/init_project.py                                                    (项目根副本)
skills/long-task-codebase-scanner/SKILL.md
skills/long-task-coverage-fix/SKILL.md                                     (+ 3 references)
skills/long-task-coverage-retrofit/SKILL.md                                (+ 3 references)
skills/long-task-multi-repo/SKILL.md                                       (+ 1 prompt + 4 references via symlink)
skills/long-task-mutation-fix/SKILL.md                                     (+ 3 references)
skills/long-task-mutation-retrofit/SKILL.md                                (+ 3 references)
skills/long-task-requirements/references/brownfield-adaptation.md
skills/long-task-static-review/SKILL.md                                    (+ 1 reference)
skills/long-task-tdd-green/SKILL.md                                        (+ 1 reference)
skills/long-task-tdd-red/SKILL.md                                          (+ 1 reference)
skills/long-task-tdd-refactor/SKILL.md                                     (+ 1 reference)
skills/long-task-tdd-shared/references/iron-law.md
skills/long-task-tdd-shared/references/testing-anti-patterns.md
```

## 附录 B：完整删除文件清单（58 个）

```
agents/ats-reviewer.md
agents/codebase-scanner.md                       (升级为 skill)
agents/example-generator.md
agents/reflection-analyst.md
docs/templates/ats-template.md
docs/templates/feature-report-template.md
docs/templates/retrospective-record-template.md
docs/templates/st-case-template.md
docs/templates/tool-bindings-template.json
hooks/chrome-mcp-setup
scripts/analyze-tokens.py
scripts/apply_tool_bindings.py
scripts/check_ats_coverage.py
scripts/check_configs.py
scripts/check_devtools.py
scripts/check_jinja2.py
scripts/check_mcp_providers.py
scripts/check_real_tests.py
scripts/check_retro_auth.py
scripts/check_retrospective_readiness.py
scripts/check_st_readiness.py
scripts/find-polluter.sh
scripts/post_retrospective_report.py
scripts/validate_ats.py
scripts/validate_retrospective_record.py
scripts/validate_st_cases.py
skills/long-task-ats/SKILL.md
skills/long-task-feature-st/SKILL.md             (+ template + references/feature-st-execution.md)
skills/long-task-finalize/SKILL.md
skills/long-task-init/references/init-script-recipes.md
skills/long-task-quality/SKILL.md                (+ template + references/quality-execution.md)
skills/long-task-retrospective/SKILL.md          (+ prompts/reflection-prompt.md)
skills/long-task-st/SKILL.md                     (+ template + references/st-recipes.md)
skills/long-task-tdd/SKILL.md.template
skills/long-task-tdd/references/ui-error-detection.md
skills/long-task-ucd/SKILL.md
skills/long-task-work/SKILL.md.template
skills/using-long-task/references/roadmap.md
tests/test_apply_tool_bindings.py
tests/test_check_ats_coverage.py
tests/test_check_configs.py
tests/test_check_devtools.py
tests/test_check_jinja2.py
tests/test_check_mcp_providers.py
tests/test_check_real_tests.py
tests/test_check_retro_auth.py
tests/test_check_retrospective_readiness.py
tests/test_check_st_readiness.py
tests/test_validate_ats.py
tests/test_validate_retrospective_record.py
tests/test_validate_st_cases.py
```

## 附录 C：查看差异速查命令

```bash
# 所有 simple 领先的 commit
git log --oneline main..simple

# 全量 diff 统计
git diff --stat main..simple

# 单个文件对比
git diff main..simple -- path/to/file

# 特定 commit 详情
git show <commit-hash>

# 新增/删除/修改文件分组
git diff --name-status main..simple | sort
```

---

**文档完整性声明**:
本文档覆盖了 `main..simple` 范围的 **129 个 commit**、**37 个新增文件**、**58 个删除文件**、**50 个修改文件** 全部分类；小部分 commit 因内容高度局部（如 SKILL.md 文案润色）被归并到上级主题中。回迁时建议以本文 1-21 节结构为主线，附录 A/B 做 diff 核对清单。

