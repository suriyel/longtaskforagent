# Main 分支优化整改方案（基于 Simple 分支选择性回迁）

> 生成日期: 2026-04-17
> 目标分支: `main`
> 参考分支: `simple`
> 前置文档: [SIMPLE-VS-MAIN-DIFF.md](SIMPLE-VS-MAIN-DIFF.md)

---

## 0. 背景与总体策略

### 0.1 Main 分支定位
Main 分支服务于**存量庞大项目**的场景，核心特征：
- 需求多为基于存量代码的**改造/增量开发**
- 需要完整的**端到端（E2E）验证**链路（环境 → UI → 集成）
- 报告/呈现类产物主要是给下游流水线消费，而非交付给外部用户
- 面向中文开发团队

因此 **保留** 以下能力（不从 simple 回迁）：
| 能力 | 理由 |
|---|---|
| UCD / UI 子系统 | 存量项目含 UI，需要视觉契约与 Chrome DevTools MCP 验证 |
| ATS / Real-Test | E2E 验证链路的核心；`required_configs[]` 校验不可缺 |
| env-guide / init 环境子系统 | 端到端验证依赖服务启停、配置、PID/端口等环境契约 |
| Long-Task Guide 多步骤导航 | Worker 按导航执行，不简化为纯工具命令参考 |
| TDD 单体 skill | 不拆分为 red/green/refactor 三 skill |
| 自动 git commit / commit 规范 | 保留（可作为可选） |

**不回迁** 以下能力：
| 能力 | 理由 |
|---|---|
| 多仓库（`long-task-multi-repo` + `repos-manifest.json`） | 当前场景为单仓库存量项目 |
| 独立 `long-task-static-review` skill | 静态分析保留在 TDD Refactor 内联执行 |
| 独立 `long-task-coverage-retrofit` / `long-task-mutation-retrofit` skill | 不需要独立改造入口；覆盖率保留在 quality gate |
| TDD 三阶段拆分 | 保持 `long-task-tdd` 单体 |

### 0.2 本次整改十大主题
| # | 主题 | 类型 | 预估工作量 |
|---|---|---|---|
| 1 | 去除用户呈现型报告类产物 | 精简 | M |
| 2 | 增量 skill 吸收 brownfield 需求/设计适配 | 扩展 | L |
| 3 | Worker 改造为 SubAgent-per-Step 架构 | 重构 | L |
| 4 | 设计 / Feature Design 实用主义瘦身 | 精简 | M |
| 5 | 中文化 | 体验 | M |
| 6 | rules & guide 可变部分下沉到 env-guide.md + 审批 | 重构 | L |
| 7 | 编译/UT 静默执行优化 | 体验 | S |
| 8 | **完全移除变异测试** | 精简 | M |
| 9 | 合并 FR → Feature 的直接合并 + ~1k LOC 颗粒度 | 体验 | M |
| 10 | 删除自定义 MCP & tool-binding 子系统 | 精简 | M |

总体改动预期：**~15 个 SKILL.md 级别文件修改** + **~8 个脚本/测试删除** + **2-3 个新增文件**。

### 0.3 执行顺序建议
```
阶段 A（清理，可先行并行）   → 主题 1、8、10
阶段 B（架构重构，需阶段 A 完成） → 主题 3、6
阶段 C（功能/体验增强）       → 主题 2、4、7、9
阶段 D（本地化，最后收口）     → 主题 5
```

---

## 1. 主题 1：去除"只为呈现给用户"的报告类产物

### 1.1 目标
删除对下游流水线**零消费**的用户呈现型文档，保留下游消费型文档。

### 1.2 识别原则
- **下游消费 → 保留**：feature-list.json、task-progress.md、RELEASE_NOTES.md、docs/plans/*-srs.md、docs/plans/*-design.md、docs/plans/*-ats.md、docs/features/*.md、docs/test-cases/*.md、docs/retrospectives/*.md（用于 API 上报）
- **仅给人看 → 删除**：feature-report（docs/report/feature-*-report.md）

### 1.3 具体动作

#### 1.3.1 删除 Feature Report 子系统
**参考**: simple commit `12ad9c7 "remove Step 10a Generate Feature Report and all dependencies"`

| 文件 | 动作 |
|---|---|
| `docs/templates/feature-report-template.md` | 删除 |
| `skills/long-task-work/SKILL.md` | 移除 Step 11a "Generate Feature Report" 及其依赖 |
| `skills/long-task-work/SKILL.md.template` | 同步移除 |
| `skills/long-task-hotfix/SKILL.md` | 若引用 feature-report，同步清理 |
| `CLAUDE.md` | 从 "Generated Persistent Artifacts" 表中删除 `docs/report/feature-*-report.md` 行 |

#### 1.3.2 保留并简化的项
- **Retrospective**：由于其产物 `docs/retrospectives/*.md` 被 `post_retrospective_report.py` 上报到 REST API（属于下游消费），**保留**；但检查 `SKILL.md` 中是否有纯装饰性输出节，可收敛。
- **task-progress.md 的"呈现段"**：保留会话日志，但如果 SKILL 要求写"华丽总结"的段落，可简化为机读字段。

### 1.4 验证
```bash
# 确认无残留引用
grep -rn "feature-report-template\|docs/report/feature-" skills/ docs/ scripts/ tests/
# 应为空
```

---

## 2. 主题 2：Increment Skill 吸收 Brownfield 需求/设计适配

### 2.1 目标
把 simple 分支专为 brownfield 开发的 **需求 elicitation 适配** 与 **代码探索嵌入** 能力吸收到 main 的 `long-task-increment` skill，而不是引入独立的 brownfield phase。

**理由**：Main 分支场景天然就是存量项目迭代，brownfield 不是"初次接入"的特例，而是"增量开发"的默认形态。

### 2.2 具体动作

#### 2.2.1 吸收 `brownfield-adaptation.md` 的内容
**源**：simple 分支 `skills/long-task-requirements/references/brownfield-adaptation.md`（commit `bb6e680`）

**目标**：复制/合并到 main 的：
- `skills/long-task-increment/references/brownfield-adaptation.md`（新文件）
- 在 `skills/long-task-increment/SKILL.md` 中加入引用：
  ```markdown
  ## Brownfield 适配（强制）
  对每次 increment-request，在 Step 3 前先加载 `references/brownfield-adaptation.md` 对比决策：
  - 需求是否可完全由存量模块实现？（如是 → 直接走内部设计调整）
  - 是否需要引入新内部库 / 新外部依赖？（如是 → §11 约束检查）
  - 是否与现有 FR 冲突？（如是 → 进入变更影响评估分支）
  ```

#### 2.2.2 嵌入 targeted explore
**源**：simple commit `07b4887 "embed targeted explore into requirements and increment phases"`、commit `b755eb1 "context-driven heuristics"`

**目标**：`long-task-increment` 新增 Step 3.5 "Targeted Codebase Explore"
- 触发条件：`increment-request.json` 存在 + `docs/rules/` 存在（说明已扫描过） + 变更涉及 ≥2 个模块
- 调用：`long-task-explore` skill，depth = `quick` 或 `standard`（按 context budget 决定，非硬编码）
- 产物：`docs/explore/increment-<date>-focus.md`（作为 Increment SRS 更新的参考附录）
- **非阻塞**：探索失败不阻断后续流程

#### 2.2.3 Increment 阶段新增"存量 API 影响评估"
**目标**：在 `long-task-increment` 更新 SRS/Design 时，**强制**列出：
- 被修改的存量 API 列表（签名、位置）
- 兼容性策略（向后兼容 / 破坏性 / 弃用）
- 对已有特性（`feature-list.json` 内）的影响清单（形成 `impact_features: [1, 5, 12]` 注解）

**SKILL.md 改动点**：Step 4 "Append new features" 之前增加 Step 3.7 "Back-compat & Impact Assessment"。

### 2.3 与 Requirements skill 的边界
- `long-task-requirements`：仍然面向**首次初始化项目**（greenfield 为主），保持 main 现状
- `long-task-increment`：面向**存量增量**（brownfield 为主），承接本主题所有改进

---

## 3. 主题 3：Worker 改造为 SubAgent-per-Step 架构

### 3.1 目标
用 simple 分支验证过的 **SubAgent-per-Step + 内部执行 skill** 架构替换 main 现有的单一 SubAgent 架构，大幅提升长流水线场景下的上下文窗口利用率。

### 3.2 关键参考 Commit
| Simple Commit | 作用 |
|---|---|
| `a5e3cbc` | Decompose Worker into SubAgent-per-Step architecture |
| `125dd3b` | Convert Feature Design skill from SubAgent dispatch to inline execution |
| `2135b63` | Fix Worker dispatch architecture + convert 5 discipline skills to inline |
| `da358bf` | Fix subagent result handoff: add Structured Return Contracts |
| `e2d51b9` | Replace Agent()/Task() tool-call syntax with declarative DISPATCH blockquotes |
| `c1d3ffc` | Clarify DISPATCH semantics |
| `1ce10c0` | Emphasize independent SubAgent at front of DISPATCH declarations |

### 3.3 具体动作

#### 3.3.1 Worker 步骤分解
**当前 main Worker 流程**（单一大 SubAgent 串跑）：
```
Step 4 Feature Design → Step 6-8 TDD → Step 9 Quality → Step 10 Feature-ST → Step 11 Retro/Report
```

**改造后**（每步独立 SubAgent，每个 SubAgent 内部加载对应 skill）：
```
SubAgent-1(loads long-task-feature-design) → returns Structured Contract
    ↓ (主 agent 仅保留契约摘要)
SubAgent-2(loads long-task-tdd) → returns Structured Contract
    ↓
SubAgent-3(loads long-task-quality) → returns Structured Contract
    ↓
SubAgent-4(loads long-task-feature-st) → returns Structured Contract
    ↓
主 agent Step 11 汇总 → 落盘 feature-list.json 状态更新
```

注意：**TDD 不拆分**（按用户要求 #4），`long-task-tdd` 保持单体，由单个 SubAgent 加载并跑完 Red→Green→Refactor。

#### 3.3.2 Structured Return Contract
**目标**：每个 SubAgent 返回必须是结构化 JSON-like 块，主 agent 只消费字段而不消费 subagent 内部的 thinking/输出。

**模板**（写入 `skills/long-task-work/references/structured-return-contract.md`，新文件）：
```markdown
每个 SubAgent 返回必须包含：

**status**: pass | fail | blocked
**artifacts_written**: [file path 列表]
**next_step_input**: { ... 下一步需要的最小字段集 }
**blockers**: [若 status=blocked 则列出]
**evidence**: [关键断言的最小证据，如测试名 + 结果]

主 agent 读取返回后只保留本结构，discard subagent 内部 thinking。
```

每个 discipline skill（feature-design、tdd、quality、feature-st）在 SKILL.md 末尾加 "Return Contract" 小节，声明本 skill 的返回字段。

#### 3.3.3 DISPATCH 声明式语法
**当前 main**：使用 `Agent(subagent_type=..., prompt=...)` 具名调用。

**改造**：改为 markdown blockquote 声明式，避免绑定特定工具名：
```markdown
> **DISPATCH** → launch independent SubAgent to load and execute `long-task-feature-design`
> **with input**: feature_id=N, srs_trace=[FR-001], rules_path=docs/rules/
> **expect**: Structured Return Contract (status, artifacts_written, next_step_input)
```

在 `skills/long-task-work/SKILL.md` 所有 dispatch 点统一替换为此格式。

#### 3.3.4 Resume 能力
**源**：simple commit `63fe496`

**动作**：Worker SKILL.md Step 1 加入 Resume Check：
```markdown
Step 1: Resume Check
- 读 task-progress.md 的 ## Current State
- 若标识 "in-progress: step-N"，跳到 step-N 重跑（而非从头）
- 若无标识，从 Step 2 开始
```

### 3.4 风险
- SubAgent-per-Step 依赖运行时对 SubAgent 嵌套加载 skill 的支持。若 Claude Code 当前版本有限制，需先验证后再全量改造。
- 建议先在一个 feature 上跑通 PoC（例如选一个小 feature，手工按新流程跑一轮），验证后再改 SKILL.md。

---

## 4. 主题 4：设计 / Feature Design 实用主义瘦身

### 4.1 目标
删除下游零消费的章节，让设计文档聚焦于"下游真正需要的输入"。

### 4.2 具体动作

#### 4.2.1 Feature Design Template 改造
**源**: simple commit `ffe1ad8 "Replace pseudocode/diagrams with implementation summary in feature-design"`、`509af54 "Delete Algorithm/Core Logic section from template"`、`cb50389 "Remove Error Handling section from template"`、`9e52101 "Remove task instructions from feature design template"`

**目标文件**: `docs/templates/feature-design-template.md`（main 上应为 `skills/long-task-feature-design/references/feature-design-template.md`）

**删除章节**：
- `## Algorithm / Core Logic`
- `## Error Handling`
- `## Task Instructions`（如有）
- `## Pseudocode`
- `## Diagrams`（仅保留 API 交互必须的；其他图删除）

**新增章节**：
- `## Implementation Summary`（3-5 段落，说明主要类/函数、调用链、关键决策、与存量代码交互点）

**保留章节**：
- `## Interface Contracts`（下游 TDD 消费）
- `## Test Inventory`（下游 TDD Red 消费）
- `## Dependencies`（下游 quality gate 消费）
- `## SRS Trace`（feature-list.json 字段消费）

#### 4.2.2 Design Template 增强
**源**: simple commit `c40c63f "add §0 Project Structure section"`、`c6302c9 "enhance design phase with internal API contracts (§6.2) and integration coherence"`

**目标文件**: `docs/templates/design-template.md`

**新增章节**：
- `## §0 Project Structure`：存量项目的顶层结构（目录/模块/边界），brownfield 必填
- `## §6.2 Internal API Contracts`：存量与新增模块间的 API 契约，防止集成期返工

**删减章节**：审视当前 design-template，删除下游零消费的章节（建议保留 §1-§11 的主干，详细清单待对照后定）。

#### 4.2.3 Feature Design Step "最大化复用" 原则
**源**: simple commit `8160dba "Add codebase exploration to feature-design Step 1c, enforce maximize-reuse principle"`、`8e8f223 "enforce §13 codebase constraints and existing code reuse in feature-design pipeline"`

**动作**：`skills/long-task-feature-design/SKILL.md` 加入 Step 1c "Existing Code Reuse Check"：
- 强制 grep 存量代码库中的相似实现（方法签名、类名、常量）
- 若存在可复用实现，禁止重新实现
- Design §13（或 §11，按重命名后编号）的"强制内部库"与"禁用 API"约束在本步骤生效

### 4.3 风险
- 删除 pseudocode/diagrams 对 UI 特性影响：UCD 子系统原依赖 diagrams，需同步检查 `long-task-ucd` 是否引用 Feature Design 的图；若引用，UCD 侧保留最小必要图（仅界面流）。

---

## 5. 主题 5：中文化

### 5.1 目标
将 Main 分支 Skill / Agent / Template 的用户可见文本优化为简体中文，但保留代码、字段名、commit message 的英文。

### 5.2 具体动作

#### 5.2.1 范围
- **翻译**：所有 `skills/*/SKILL.md` 的指令文本、所有 `skills/*/references/*.md`、所有 `agents/*.md`、所有 `docs/templates/*.md` 的正文
- **不翻译**：YAML frontmatter 的 `name`、字段名（如 `srs_trace`、`feature_id`）、命令示例、工具名、commit message 示例

#### 5.2.2 实施路径
**参考**: simple commit `ad95f74 "Translate all skill, agent, and template content from English to Chinese"`

**两种可选策略**：

**策略 A（保守，推荐）**：本地化分散到每个 SKILL 文件单独 PR，逐个评审。优点：可回滚，风险低。缺点：周期长。

**策略 B（激进）**：直接 cherry-pick simple 的 `ad95f74` commit，批量替换。优点：快速。缺点：冲突多（因 simple 已删除 UCD/ATS/ST 等文件），需手工清理冲突。

**建议**：**策略 A**。

#### 5.2.3 Session 注入中文规则
**参考**: simple commit `66e4378 "add Chinese (Simplified) language rule to session injection and init template"`

**动作**：
- `hooks/session-start` 中注入：
  ```markdown
  # 语言规则
  回复用户时使用简体中文。代码标识符、命令、字段名保持英文。
  ```
- `skills/long-task-init/scripts/init_project.py` 生成的 `CLAUDE.md` 模板同步加此规则
- **避免**：不要把语言规则写进每个 SKILL.md 的正文里（simple commit `8c90371` 的反向经验）

### 5.3 风险
- 翻译过程中误改代码示例 → 翻译前强制 `grep -n "\`\`\`" file.md` 定位所有代码块，跳过
- 术语不一致 → 建立术语表（FR=功能需求、SRS=软件需求规约、Feature=特性、Gate=关卡，etc.），放在 `docs/templates/glossary.md`（新文件）

---

## 6. 主题 6：Rules 探索 & Guide 可变部分下沉到 env-guide.md + 审批

### 6.1 目标
这是**本次整改最具原创性的一项**。用户要求：
- `docs/rules/` 下的 codebase 扫描产物（存量约束）
- `long-task-guide.md` 中与环境/工具相关的命令（UT 执行、编译命令、端口等）

**下沉合并到 `env-guide.md`**，并为 `env-guide.md` **增加人工审批关卡**。

**理由**：Main 场景下 env-guide.md 是端到端验证的"环境契约单一事实源"，rules 和 guide 中与环境强相关的部分本就应该集中管理，避免三份文件重复漂移。

### 6.2 具体动作

#### 6.2.1 env-guide.md 扩展为六大板块
**当前 main 的 env-guide.md** 主要含：启停、验证、环境变量。

**扩展后**：
```markdown
# env-guide.md（环境契约 — 单一事实源）

## §1 服务生命周期
- 启停、重启协议、PID/端口约定

## §2 环境配置
- 环境变量清单、.env.example 关联、必需 configs

## §3 构建与执行命令（从 long-task-guide.md 下沉）
- 编译命令（含静默参数）
- UT 执行命令（含静默参数）
- 覆盖率命令
- 静态分析命令

## §4 存量代码库约束（从 docs/rules/ 下沉）
- §4.1 强制内部库
- §4.2 禁用 API
- §4.3 代码风格基线
- §4.4 构建系统约定

## §5 测试环境依赖
- 数据库、消息队列、第三方服务的本地替身配置
- Chrome DevTools MCP 启动（如保留 UI 测试）

## §6 人工审批记录
- 日期 / 审批人 / 签名
- 变更摘要
```

#### 6.2.2 `docs/rules/` 处置
**两种方案**：

**方案 A（推荐）**：`docs/rules/*.md` 作为 **过程性产物** 保留，但 `long-task-codebase-scanner`（或等价 SubAgent）在生成后**追加一个合并步骤**：将关键内容 merge 到 `env-guide.md` §4。

**方案 B**：直接废弃 `docs/rules/` 目录，scanner 直接输出到 `env-guide.md` §4。

**选 A**：保留过程性 `docs/rules/` 作为可追溯记录，但约束下游流水线**只读 `env-guide.md`**。

#### 6.2.3 `long-task-guide.md` 瘦身
**改动点**：
- **保留**：多步骤导航（用户要求 #7）、worker session 流程图、skill 切换指引
- **移除（下沉到 env-guide.md §3）**：具体的 build/test/coverage 命令、工具版本要求
- **引用替代**：原命令位置替换为 "详见 `env-guide.md` §3"

**SKILL 改动**：
- `skills/long-task-init/SKILL.md`：init 时同时生成 `long-task-guide.md`（瘦身版）和 `env-guide.md`（扩展版）
- `scripts/validate_guide.py`：调整校验逻辑，不再强制 guide 里有编译命令
- 新增 `scripts/validate_env_guide.py`：校验 env-guide.md 六大板块完整性

#### 6.2.4 人工审批关卡
**目标**：env-guide.md 作为下游流水线"真相源"，任何修改必须经过人工审批，防止 AI 误改导致整条 E2E 链路断裂。

**实现**：
- `env-guide.md` 文件头 YAML frontmatter：
  ```yaml
  ---
  version: 1.0
  approved_by: <user handle>
  approved_date: 2026-04-17
  approved_sections: [§1, §2, §3, §4, §5]
  ---
  ```
- 新增 `scripts/check_env_guide_approval.py`：
  - 对比当前 env-guide.md 与上次 git commit 的 diff
  - 若发现 §4 约束或 §3 命令被修改 → 校验 frontmatter `approved_date` 是否晚于最近 diff commit 日期
  - 否则阻断 Worker 启动
- `hooks/session-start` 调用此校验脚本
- Worker SKILL 启动前 Step 0 增加 "env-guide approval gate"

#### 6.2.5 Skill 流水线改造点
| Skill | 改动 |
|---|---|
| `long-task-init` | 生成 env-guide.md 六板块骨架；首次生成不强制审批 |
| `long-task-design` | §11/§13 codebase constraints 由"内联写进 design.md"改为"引用 env-guide.md §4" |
| `long-task-increment` | Increment 若触及 env 变更，必须更新 env-guide.md 并提示用户审批 |
| `long-task-work` | Step 0 env-guide approval gate |
| `long-task-tdd` | quiet 命令从 env-guide.md §3 读取，不再硬编码 |
| `long-task-quality` | UT/覆盖率命令从 env-guide.md §3 读取 |
| `long-task-feature-st` | 服务启停从 env-guide.md §1 读取（已有） |

### 6.3 风险
- env-guide.md 体量膨胀 → 可能超过 LLM 一次读取的理想长度。缓解：在 §1-§6 文件头加 Table of Contents，Worker 按需 offset 读取。
- 审批流程阻塞开发节奏 → 建议"首次生成免审批、后续变更必审批"。
- `docs/rules/` 与 env-guide §4 双写漂移 → scanner 生成时必须是原子操作（先写 rules，立即 merge 到 env-guide §4，再让用户审批）。

---

## 7. 主题 7：编译/UT 静默参数优化

### 7.1 目标
吸收 simple 分支的"命令静默执行 + 按需提取输出"模式，减少 LLM 上下文污染与 token 消耗。

### 7.2 参考 Commit
- simple commit `10efa9f` — temp file capture + on-demand extraction for build/test/mutation commands
- simple commit `98002fa` — quiet commands 改为 `(cmd, instruction)` 声明式
- simple commit `faf375e` — TDD Red/Green 强制 quiet execution protocol
- simple commit `df7baeb` — 澄清 re-check 流程减少重复执行

### 7.3 具体动作

#### 7.3.1 Quiet 命令声明式
**目标**：所有执行命令改为 `(cmd, instruction)` 声明而非直接 bash：

**改前**（当前 main 常见写法）：
```bash
mvn test 2>&1 | tail -50
```

**改后**：
```markdown
**quiet_cmd**:
- cmd: `mvn test > /tmp/mvn-test-$$.log 2>&1; echo $? > /tmp/mvn-test-$$.exit`
- on_success: 读 `/tmp/mvn-test-$$.log` 最后 30 行
- on_failure: 读 `/tmp/mvn-test-$$.log` 最后 100 行 + 提取 `FAILED` / `ERROR` 行
- instruction: "仅在失败或需要证据时再 extract；成功路径不要把日志灌进上下文"
```

#### 7.3.2 落实位置
| 文件 | 改动 |
|---|---|
| `skills/long-task-tdd/SKILL.md` | Red/Green/Refactor 三子步骤执行协议改为 quiet |
| `skills/long-task-quality/SKILL.md` | 覆盖率/变异测试命令改为 quiet（变异部分按主题 8 删除） |
| `skills/long-task-feature-st/SKILL.md` | 服务启动 / 探针检查改为 quiet |
| `skills/long-task-work/SKILL.md` | 在 Worker 总协议处声明 "所有下游 SubAgent 必须遵循 quiet execution" |
| `skills/long-task-init/SKILL.md` | 生成 `env-guide.md §3` 时，命令模板带 quiet 封装 |

#### 7.3.3 Re-check 协议
**动作**：在 Worker SKILL 加入："若 quality gate 失败 → 修复后 **仅重跑失败的测试**（by name），不要整轮重跑。"

### 7.4 风险
- 临时文件残留 → 模板里用 `trap 'rm -f /tmp/*-$$.log' EXIT` 包裹
- `$$` 在某些 shell 下不可靠 → 改用 `mktemp`

---

## 8. 主题 8：完全移除变异测试

### 8.1 目标
按用户要求 #8，**完全**移除变异测试，以保证开发速度。

### 8.2 具体动作

#### 8.2.1 Feature-list.json schema 变更
**删除字段**：
- `tech_stack.mutation_tool`
- `quality_gates.mutation_score_min`
- `quality_gates.mutation_full_threshold`

**不变字段**：`line_coverage_min`、`branch_coverage_min` 保留。

**动作**：
- `scripts/validate_features.py`：删除 mutation 相关校验
- `skills/long-task-init/scripts/init_project.py`：删除 `--mutation-score` 参数；删除 mutation_tool 探测逻辑
- `scripts/get_tool_commands.py`：删除 mutation 命令输出
- `tests/test_validate_features.py`、`tests/test_init_project.py`、`tests/test_get_tool_commands.py`：删除 mutation 用例

#### 8.2.2 Skill 层清理
| 文件 | 动作 |
|---|---|
| `skills/long-task-quality/SKILL.md` | 删除 "Feature-Scoped Mutation Gate" 整个章节；SKILL 改名为"Coverage Gate"或保持但仅含覆盖率 |
| `skills/long-task-quality/references/quality-execution.md` | 同步删除 mutation 段落 |
| `skills/long-task-quality/SKILL.md.template` | 同步 |
| `skills/long-task-work/SKILL.md` | Step 9 Quality 只含覆盖率；Step 名可改为 "Coverage Gate" |
| `skills/long-task-st/SKILL.md` | "ST 期间 mutation 全量跑" 的逻辑删除 |
| `skills/long-task-retrospective/SKILL.md` | mutation 相关记录字段删除 |
| `CLAUDE.md` | 删除 mutation 相关规则与说明 |

#### 8.2.3 文档/模板清理
- `docs/templates/design-template.md`、`srs-template.md`：删除所有 "mutation score" 提及
- `README.md` / `README_EN.md`：删除 mutation 相关说明
- `long-task-guide.md` 生成模板：删除 mutation 命令

### 8.3 向后兼容
- 已有项目的 `feature-list.json` 可能含 mutation 字段 → 新版 validate 应**忽略**未知字段（warning 而非 error），提供平滑迁移。

### 8.4 风险
- 删除后覆盖率成为唯一测试质量信号 → 建议把行覆盖率阈值从 90% 提到 95%，分支从 80% 提到 85%，部分补偿变异测试丢失的信号强度。

---

## 9. 主题 9：合并 FR 到 Feature 的直接合并 + ~1k LOC 颗粒度

### 9.1 目标
吸收 simple 分支 "FR 直接合并为 Feature + ~1k LOC sizing 目标 + 颗粒度二次确认" 的做法，避免早期按 FR 分组后颗粒度失控（过大或过碎）。

### 9.2 参考
- simple commit `4a7f1e0 "replace FR grouping with direct merge, add ~1k LOC sizing target and Step 10b granularity confirmation"`
- simple commit `9724595 "replace hardcoded 10-200+ feature count with bidirectional context-budget sizing"`

### 9.3 具体动作

#### 9.3.1 Requirements/Init 阶段改造
**当前 main**：SRS 按 FR-XXX 列出需求，Init 阶段 AI 按 FR 分组合并为 feature，但分组策略不透明、易失衡。

**改造后**：
- Init 阶段新增 Step "Feature Sizing & Granularity Confirmation"
- 规则：
  - **目标颗粒度**：每个 feature 预计 ~1000 LOC（±500）
  - **合并策略**：相邻/同模块的 FR 先直接合并，不做 FR 分组
  - **拆分策略**：若一个 FR 实现量预计 >1500 LOC，拆分为 N 个 feature（每个带 `srs_trace: ["FR-001"]` 相同标记）
- **颗粒度确认关卡**（Step 10b）：Init 完成 feature-list 草案后，向用户展示：
  ```
  生成 feature 数：15
  预计 LOC 分布：
    - < 500 LOC: 2 个（过小，建议合并）
    - 500-1500 LOC: 11 个 ✓
    - > 1500 LOC: 2 个（过大，建议拆分）
  是否采纳？[y/n/auto-fix]
  ```

#### 9.3.2 Context-budget Sizing
**动作**：替换当前 main 中"预期 10-200 个 feature"的硬编码，改为双向 context-budget：
- 上界：单轮 Worker 可完成的 feature 数 ≤ context_budget / avg_feature_tokens
- 下界：feature 数 ≥ total_LOC / max_feature_LOC

**落实**：`skills/long-task-init/SKILL.md` 的 sizing 章节。

#### 9.3.3 SRS 单轮模式（附带收益）
**源**: simple commit `33846b6` + `47bbcfe`

若 SRS 标记 `Single-Round: Yes`（Step 10c 用户确认），feature 合并策略更宽松：
- 允许合并到 ~2000 LOC（大需求单轮处理）
- feature-list.json 增加 `single_round: true` 顶层字段（仅信息性）

### 9.4 风险
- LOC 预估不准 → 预估公式必须透明（基于 SRS 字数 + 接口复杂度 + 测试清单长度），便于修正
- 过度拆分破坏功能连贯性 → 拆分后的 feature 必须共享 `srs_trace`，保证可追溯

---

## 10. 主题 10：删除自定义 MCP & Tool-Binding 子系统

### 10.1 目标
删除 main 上"自定义 MCP provider 映射"和 "tool-bindings.json" 子系统。**保留** Chrome DevTools MCP（用于 UI 测试，属于用户要求 #6 的 UI 内容范畴）。

### 10.2 具体动作

#### 10.2.1 删除文件
| 文件 | 动作 |
|---|---|
| `scripts/apply_tool_bindings.py` | 删除 |
| `scripts/check_mcp_providers.py` | 删除 |
| `scripts/check_jinja2.py` | 删除（仅服务 tool-bindings 模板） |
| `scripts/check_devtools.py` | **评估**：若仅服务自定义 MCP 删除；若服务 Chrome DevTools 启动探针则保留重命名为 `check_chrome_devtools.py` |
| `docs/templates/tool-bindings-template.json` | 删除 |
| `tests/test_apply_tool_bindings.py` | 删除 |
| `tests/test_check_mcp_providers.py` | 删除 |
| `tests/test_check_jinja2.py` | 删除 |
| `tests/test_check_devtools.py` | 按上行决策同步 |

#### 10.2.2 Feature-list.json schema 变更
**删除字段**：
- ~无（main 当前字段里 MCP 相关是 `tool-bindings.json` 独立文件，不影响 feature-list.json）~
- 保留 `ats_template_path`、`st_case_template_path`、`retro_api_endpoint` 等（与 MCP 无关）

**动作**：搜索 `feature-list.json` schema 中是否有 `mcp` / `tool_binding` 字段并删除。

#### 10.2.3 Skill 层清理
| Skill / 文件 | 改动 |
|---|---|
| `skills/long-task-init/SKILL.md` | 删除 tool-bindings.json 生成步骤 |
| `skills/long-task-work/SKILL.md` | 删除 "apply tool bindings" 步骤 |
| `skills/long-task-feature-st/SKILL.md` | **保留** Chrome DevTools MCP 启动步骤（UI 测试用），但移除"自定义 MCP provider 映射"段落 |
| `CLAUDE.md` | "Key Commands" 表中删除相关命令行；"Architecture" 中移除 MCP 子系统描述 |

#### 10.2.4 Hook 清理
- `hooks/chrome-mcp-setup`：**保留**（用户要求 #6 保留 UI 内容，Chrome DevTools 属 UI 测试能力）
- `hooks/hooks.json`：审视并删除仅服务"自定义 MCP 绑定"的 hook 条目；保留 chrome-mcp-setup 的调用

### 10.3 风险
- Chrome DevTools MCP 启动本身依赖 MCP 协议，删除"自定义 MCP"时不要误伤
- `check_devtools.py` 需要人工判断其内容边界

---

## 11. 整改执行顺序与里程碑

### 11.1 阶段 A（第 1-2 周）：清理
**可并行的主题**: 1、8、10

**产出**：
- 删除 feature-report、mutation 测试、tool-bindings 子系统
- 相关测试删除
- CLAUDE.md 更新
- 一次合并 PR

### 11.2 阶段 B（第 3-5 周）：架构重构
**主题**: 3、6

**依赖**：阶段 A 完成（避免重构时带着待删的旧代码）

**产出**：
- Worker SubAgent-per-Step 实现
- env-guide.md 六板块 + 审批关卡
- `check_env_guide_approval.py` 脚本
- 一次大 PR（可拆成两个：3 一次、6 一次）

### 11.3 阶段 C（第 6-8 周）：功能增强
**主题**: 2、4、7、9

**产出**：
- Increment skill brownfield 适配
- 设计/Feature Design 模板瘦身
- 编译/UT 静默参数
- FR 合并 + 颗粒度确认
- 三到四个中等 PR

### 11.4 阶段 D（第 9-10 周）：本地化
**主题**: 5

**产出**：
- 全面中文化 PR（按 SKILL 文件拆分多个子 PR）
- session-start 中文规则注入
- 术语表

### 11.5 里程碑检查点
| 检查点 | 门禁标准 |
|---|---|
| A 完成 | `git grep mutation | wc -l` = 0（除历史 commit）；`pytest` 全绿 |
| B 完成 | Worker 能在一个 feature 上完整跑通 SubAgent-per-Step；env-guide 审批 gate 生效 |
| C 完成 | 新 feature 从 Init 到 Worker 端到端一次性跑通；feature-list.json 颗粒度满足 ~1k LOC |
| D 完成 | 所有 SKILL.md 中文化；术语一致性校验通过 |

---

## 12. 验收标准

### 12.1 功能验收
- [ ] 存量项目（≥10 万 LOC）上执行 `increment-request.json` 全流程走通
- [ ] `env-guide.md` 作为单一事实源生效（Worker、TDD、quality 均读取该文件）
- [ ] 未经审批修改 `env-guide.md` 触发 Worker 启动阻断
- [ ] `feature-list.json` 无 mutation 字段，Worker 不执行变异测试
- [ ] Feature Design 含 Implementation Summary 章节
- [ ] Increment skill 自动触发 targeted explore

### 12.2 非功能验收
- [ ] Worker 单 feature 完整执行 token 消耗较改造前下降 ≥30%（受益于 SubAgent-per-Step + quiet execution）
- [ ] 所有 SKILL.md / agents / templates 正文中文比例 ≥95%
- [ ] CI 测试 100% 通过

### 12.3 回归检查
- [ ] ATS、Real-Test、UCD、UI 视觉契约、env-guide 启停协议**全部保留并可用**
- [ ] long-task-guide.md 多步骤导航**保留**
- [ ] TDD 仍为单体 skill（Red→Green→Refactor 串行）
- [ ] 自定义 MCP / tool-bindings 清理后，Chrome DevTools MCP 仍可正常启动

---

## 13. 不采纳清单（重申）

| simple 改动 | 不回迁理由 |
|---|---|
| `long-task-multi-repo` skill | 场景不需要 |
| `repos-manifest.json` + session-start 多仓检测 | 同上 |
| `long-task-static-review` 独立 skill | 静态分析已在 TDD Refactor 内联 |
| `long-task-coverage-retrofit` 独立 skill | 覆盖率在 quality gate 内 |
| `long-task-mutation-retrofit` 独立 skill | 变异测试整体删除 |
| TDD 拆分为 red/green/refactor 三 skill | 保持单体 |
| 删除 UCD 子系统 | 保留 |
| 删除 ATS 子系统 | 保留 |
| 删除 ST 子系统 | 保留 |
| 删除 Real-Test 校验 | 保留 |
| 删除 env-guide / init 环境子系统 | 保留并扩展（主题 6） |
| long-task-guide.md 简化为纯工具命令参考 | 保留多步骤导航 |
| 删除 commit-msg hook / 自动提交 | 保留（可作为可选） |

---

## 附录 A：改动影响文件矩阵

| 文件 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 |
|---|---|---|---|---|---|---|---|---|---|---|
| `CLAUDE.md` | ✓ |  |  |  | ✓ | ✓ |  | ✓ |  | ✓ |
| `skills/long-task-init/SKILL.md` |  |  |  |  | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `skills/long-task-init/scripts/init_project.py` |  |  |  |  |  | ✓ |  | ✓ |  | ✓ |
| `skills/long-task-requirements/SKILL.md` |  |  |  |  | ✓ |  |  |  |  |  |
| `skills/long-task-increment/SKILL.md` |  | ✓ |  |  | ✓ | ✓ |  |  |  |  |
| `skills/long-task-increment/references/brownfield-adaptation.md`（新） |  | ✓ |  |  | ✓ |  |  |  |  |  |
| `skills/long-task-design/SKILL.md` |  |  |  | ✓ | ✓ | ✓ |  |  |  |  |
| `skills/long-task-feature-design/SKILL.md` |  |  | ✓ | ✓ | ✓ |  |  |  |  |  |
| `skills/long-task-feature-design/references/feature-design-template.md` |  |  |  | ✓ | ✓ |  |  |  |  |  |
| `skills/long-task-work/SKILL.md` | ✓ |  | ✓ |  | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| `skills/long-task-tdd/SKILL.md` |  |  | ✓ |  | ✓ |  | ✓ |  |  |  |  |
| `skills/long-task-quality/SKILL.md` |  |  | ✓ |  | ✓ | ✓ | ✓ | ✓ |  |  |
| `skills/long-task-feature-st/SKILL.md` | ✓ |  | ✓ |  | ✓ | ✓ | ✓ |  |  | ✓ |
| `skills/long-task-st/SKILL.md` |  |  |  |  | ✓ |  |  | ✓ |  |  |
| `skills/long-task-ucd/SKILL.md` |  |  |  |  | ✓ |  |  |  |  |  |
| `skills/long-task-ats/SKILL.md` |  |  |  |  | ✓ |  |  |  |  |  |
| `skills/long-task-retrospective/SKILL.md` |  |  |  |  | ✓ |  |  | ✓ |  |  |
| `skills/long-task-finalize/SKILL.md` |  |  |  |  | ✓ |  |  |  |  |  |
| `skills/using-long-task/SKILL.md` |  |  |  |  | ✓ |  |  |  |  |  |
| `docs/templates/design-template.md` |  |  |  | ✓ | ✓ | ✓ |  | ✓ |  |  |
| `docs/templates/srs-template.md` |  |  |  |  | ✓ |  |  | ✓ | ✓ |  |
| `docs/templates/feature-report-template.md` | 删 |  |  |  |  |  |  |  |  |  |
| `docs/templates/tool-bindings-template.json` |  |  |  |  |  |  |  |  |  | 删 |
| `docs/templates/glossary.md`（新） |  |  |  |  | ✓ |  |  |  |  |  |
| `scripts/apply_tool_bindings.py` |  |  |  |  |  |  |  |  |  | 删 |
| `scripts/check_mcp_providers.py` |  |  |  |  |  |  |  |  |  | 删 |
| `scripts/check_jinja2.py` |  |  |  |  |  |  |  |  |  | 删 |
| `scripts/check_env_guide_approval.py`（新） |  |  |  |  |  | ✓ |  |  |  |  |
| `scripts/validate_env_guide.py`（新） |  |  |  |  |  | ✓ |  |  |  |  |
| `scripts/validate_features.py` |  |  |  |  |  |  |  | ✓ |  |  |
| `scripts/validate_guide.py` |  |  |  |  |  | ✓ |  |  |  |  |
| `hooks/session-start` |  |  |  |  | ✓ | ✓ |  |  |  |  |
| `hooks/chrome-mcp-setup` |  |  |  |  |  |  |  |  |  | 保 |
| `agents/*.md` |  |  |  |  | ✓ |  |  |  |  |  |
| `tests/test_validate_features.py` |  |  |  |  |  |  |  | ✓ |  |  |
| `tests/test_init_project.py` |  |  |  |  |  | ✓ |  | ✓ |  |  |
| `tests/test_apply_tool_bindings.py` |  |  |  |  |  |  |  |  |  | 删 |
| `tests/test_check_mcp_providers.py` |  |  |  |  |  |  |  |  |  | 删 |
| `tests/test_check_jinja2.py` |  |  |  |  |  |  |  |  |  | 删 |

（T1-T10 对应主题 1-10；"删"表示删除，"保"表示显式保留）

---

## 附录 B：关键参考 Commit 速查

| 主题 | Simple 分支参考 Commit |
|---|---|
| T1 报告清理 | `12ad9c7` |
| T2 Brownfield 适配 | `bb6e680`、`07b4887`、`b755eb1` |
| T3 SubAgent-per-Step | `a5e3cbc`、`125dd3b`、`2135b63`、`da358bf`、`e2d51b9`、`c1d3ffc`、`1ce10c0`、`63fe496` |
| T4 设计/Feature 瘦身 | `ffe1ad8`、`509af54`、`cb50389`、`9e52101`、`c40c63f`、`c6302c9`、`8160dba`、`8e8f223` |
| T5 中文化 | `ad95f74`、`66e4378`、`fa18dca`、`8c90371`（反向经验） |
| T6 env-guide 下沉 | 无直接 commit（本方案原创）；相关环境能力参考 `39b0b8e` |
| T7 Quiet 命令 | `10efa9f`、`98002fa`、`faf375e`、`df7baeb` |
| T8 变异测试删除 | `9defa46`（work 流水线移除）+ 若干相关 |
| T9 FR 合并 & 颗粒度 | `4a7f1e0`、`9724595`、`33846b6`、`47bbcfe` |
| T10 MCP 清理 | 参考 simple 删除记录（apply_tool_bindings.py 等 6 个文件） |

---

## 附录 C：风险登记册

| 风险 | 影响 | 缓解 |
|---|---|---|
| SubAgent 嵌套加载 skill 的运行时支持不足 | T3 无法落地 | PoC 先行 |
| env-guide.md 体积膨胀导致 LLM 难以一次性消化 | T6 可用性下降 | 按板块 offset 读取 |
| 审批流程阻塞开发 | T6 节奏损失 | 首次免审批 + 局部变更豁免 |
| 中文化引入术语不一致 | T5 可读性下降 | 术语表 + 校验脚本 |
| 变异测试删除导致测试质量信号弱化 | T8 长期风险 | 覆盖率阈值上调 |
| Chrome DevTools MCP 误伤 | T10 UI 验证失效 | 显式保留清单 |
| 已有项目 feature-list.json 含 mutation 字段不兼容 | T8 迁移风险 | Validator 降级为 warning |
| 翻译批量 cherry-pick simple commit 冲突多 | T5 执行成本 | 采用策略 A（保守分 SKILL 翻译） |

---

**整改方案完成**。本方案覆盖用户提出的 10 项吸纳项 + 7 项不采纳项，并给出具体文件级动作、参考 commit、执行阶段与验收标准。建议先启动阶段 A（清理类，风险低），再推进阶段 B（架构类，收益大）。
