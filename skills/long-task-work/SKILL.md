---
name: long-task-work
description: "Use when feature-list.json exists - orchestrate features through the full TDD pipeline with quality gates and code review"
---

# Worker —— 每循环一个特性

通过每循环实现一个特性来执行多会话软件项目。每个循环遵循严格流水线：Orient → Gate → Plan → TDD → Quality → ST Acceptance → Inline Check → Persist。

**开始时宣告：** "I'm using the long-task-work skill. Let me orient myself."

**核心原则：** 每个子步在**独立 SubAgent**中运行，SubAgent 自己加载 skill。主 Agent 仅分发并消费 **Structured Return Contract** —— 永不读取 SubAgent 的内部输出。契约与 DISPATCH 语法参见 `references/structured-return-contract.md`。

**静默执行协议（所有 SubAgent 与 inline 检查强制）：** 每一次构建、测试、覆盖率、静态分析命令都**必须**把输出重定向到 `$$`-作用域的临时文件（`<cmd> > /tmp/<slug>-$$.log 2>&1; echo $? > /tmp/<slug>-$$.exit`）。成功路径仅读取 exit 文件。失败路径提取最后 100 行 + 匹配 `FAIL|ERROR|Exception` —— 永不向主 agent 倾倒完整输出。权威命令（带静默封装）位于 `env-guide.md` §3；SubAgent 从那里读取命令，而不是就地拼接。**Re-check 协议**：任何失败时，修复具体问题并**仅按名字重跑失败步骤或失败测试**（不跑完整套件）。完整重跑保留给最终校验步骤。

**Resume 协议：** 每次 DISPATCH（Step 4、5-7、8、9）前，向 `task-progress.md` `## Current State` 写入 `in-progress: step-<N>`。SubAgent 返回 pass 后，覆盖为 `completed: step-<N>`。下一次 Worker 循环，Step 1 Resume Check 读取此标记，若前一循环未到达 Step 11 Persist，则跳到 pending 步骤。

## Checklist

你必须为每个 step 创建一个 TodoWrite 任务并按顺序完成：

### 0. env-guide 审批关卡

**硬关卡——每次 Worker 循环前运行。** 下游步骤（TDD、Quality、Feature-ST）直接从 `env-guide.md` §3/§4 读取构建/测试/覆盖率命令与存量代码库约束。对这些节的任何无人类审批的编辑都可能悄无声息地破坏整条流水线。

运行：
```bash
python scripts/check_env_guide_approval.py env-guide.md
```

- **Exit 0** → 已审批；进入 Step 1。
- **Exit 1** → §3 或 §4 在当前 `approved_date` 之后被修改（或 `approved_by` 为 null 且有编辑历史）。阻塞并通过 `AskUserQuestion` 升级给用户：
  1. 显示 diff：`git log -1 --patch env-guide.md`（尾 ~50 行）
  2. 请用户审阅变更，更新 `env-guide.md` frontmatter（`approved_by`、`approved_date`），提交审批，然后重跑 Worker。
  3. **禁止继续** —— 审批不可协商。
- **Exit 2** → `env-guide.md` 缺失或格式错误。若项目处于 init 状态（无 env-guide.md），本步骤不适用；否则升级以修复文件。

**跳过条件**：如 `env-guide.md` 不存在（pre-init 项目、init 期间明确标记 "No server processes" 的 CLI-only 项目），在 `task-progress.md` 记录 "env-guide gate skipped — not applicable" 并继续。

### 1. Orient
- **Resume Check**：读取 `task-progress.md` `## Current State`。若含形如 `in-progress: step-<N>` 的行（前一循环 dispatched 了 SubAgent 但未完成 Step 11 Persist），**以磁盘已有工件作为输入直接跳到 Step `<N>`**。若无此标记，从下一项起按正常流程继续。在 `task-progress.md` 当前特性标题下记录 resume 决定。
- 适用时加载 config 值——按 `env-guide.md` §2 激活项目环境；若项目使用基于文件的 config（例如 `.env`），在运行检查前确保其已加载以便必需环境变量设置
- 读取 `task-progress.md` `## Current State` 节——进度统计、上个完成特性、下一个特性
- 读取 `feature-list.json` —— 注意 `constraints[]`、`assumptions[]`、`required_configs[]`、特性状态
- 读取 `long-task-guide.md` —— 项目专属工作流指引
- 读取 `env-guide.md`（如存在）——注意服务名、端口、健康检查 URL；若目标特性有服务依赖则必需
- **判定服务依赖**：若下列任一为真，特性即有服务依赖：
  1. 其 `required_configs[]` 含连接串键（键包含 `URL`、`URI`、`DSN`、`CONNECTION`、`HOST` 或 `PORT` —— 例如 `DATABASE_URL`、`REDIS_HOST`）
  2. 其 `dependencies[]` 含引用数据库建表、schema 迁移或服务初始化的特性
  3. 设计节（`{design_section}`）指明外部服务交互（DB 查询、对自有服务的 HTTP 调用、消息队列操作）

  在 `task-progress.md` 当前特性标题下记录判定（yes/no + 哪些服务）。本判定驱动 Bootstrap Step 2 与 Config Gate Step 3。
- 读取设计文档 **§1 架构**（`docs/plans/*-design.md`）—— 项目概要与架构全局快照
- 读取 `env-guide.md §4`（存量代码库约束，如存在）—— 强制内部库（§4.1）、禁用 API（§4.2）、代码样式基线（§4.3）、构建约定（§4.4）。这些对所有新代码具约束力；静态分析命令位于 `env-guide.md §3`。
- 运行 `git log --oneline -10` —— 最近 commit 上下文
- 按优先级、再按 `features[]` 数组位置挑选下一个 `"status": "failing"` 特性（第一个符合条件的胜出）—— **跳过 `"deprecated": true` 的特性**
- **依赖满足检查**：选中候选特性后，核对其 `dependencies[]` 中所有特性 ID 在 `feature-list.json` 中都是 `"status": "passing"`。若任何依赖仍 `"failing"`：
  - 记录："Feature #{id} ({title}) skipped — unsatisfied deps: #{dep1}, #{dep2}"
  - 挑下一个依赖都已满足的符合条件 `"failing"` 特性（按优先级 + 依赖顺序）
  - 若**无** 特性的所有依赖都已满足 → 通过 `AskUserQuestion` 警告用户："All remaining features have unsatisfied dependencies. Circular or over-constrained dependency graph detected." → 让用户选择强制启动哪个特性（绕过依赖检查）
  - 在 `task-progress.md` 记录被跳过的特性与原因
- 若目标特性 `"ui": true` 且 UCD 文档存在（`docs/plans/*-ucd.md`），阅读 UCD 样式指南——引用样式 token、组件提示词和页面提示词以确保前端实现匹配已审批的视觉风格

**文档查询协议（Step 5、10、11 使用）：**

当你需要某特性的设计节或 SRS 需求时，**不要** grep 特性标题。改为：

1. **设计文档**（`docs/plans/*-design.md`）：
   - 读取设计文档**第 2 节标题区**（使用 Read 工具搭配 offset/limit 扫描 section 2 标题——查找匹配 `### 2.N Feature:` 的行）
   - 通过匹配特性标题或 FR-ID 识别哪个 `### 2.N` 子节对应目标特性
   - 读取**整段子节**，从 `### 2.N` 到 `### 2.(N+1)` 前一行（或第 2 节结尾）—— 包含 Overview、Key Types、Integration Surface
   - 存为 `{design_section}` 供 Plan（Step 5）与 ST Acceptance（Step 9）使用

2. **SRS 文档**（`docs/plans/*-srs.md`）：
   - 读取 SRS **第 4 节（功能需求）** 标题区，找到匹配目标特性的 `### FR-xxx` 子节
   - 读取**整段 FR-xxx 子节**，包含 EARS 语句、优先级、验收标准、Given/When/Then 场景
   - 存为 `{srs_section}` 供 Plan 使用

3. **UCD 文档**（`docs/plans/*-ucd.md`，仅 `"ui": true` 特性）：
   - 读取 UCD 的目录或章节标题
   - 找到引用目标特性 UI 组件或页面的章节
   - 读取**完整相关章节**，含样式 token、组件提示词、页面提示词

**为什么重要：** Grep 返回孤立匹配行而无周围上下文。设计节的 Integration Surface 含 Contract ID、Provides/Requires schema——这些对正确实现与 inline 合规检查都是必需的。

### 2. Bootstrap
- **开发环境就绪**：检查环境是否已设置
  - 若 `init.sh` / `init.ps1` 存在且环境未就绪：运行一次
  - 若执行了脚本，在 `task-progress.md` 记录决定
- **确认测试命令可用**：按 `long-task-guide.md` 激活环境，并核对技术栈的测试/覆盖率命令正确；在循环全程直接使用这些命令（不使用封装脚本）
- **服务就绪**（条件性——基于 Orient 服务依赖判定）：
  - **无服务依赖**：跳过服务启动。Feature-ST（Step 10）为验收测试管理服务。
  - **有服务依赖**：真实测试（TDD 规则 5a）需运行中的基础设施。确保可用性：
    1. 读取 `env-guide.md` → 定位 "Verify Services Running" 健康检查
    2. 运行健康检查。若全通过 → 在 `task-progress.md` 记录 PID/端口；继续
    3. 若健康检查失败 → 通过 `env-guide.md` "Start All Services" 带输出捕获启动：
       ```bash
       [start command] > /tmp/svc-<slug>-start.log 2>&1 &
       sleep 3
       head -30 /tmp/svc-<slug>-start.log
       ```
    4. 重跑健康检查——阻塞直至通过
    5. 若启动失败 → 按 `env-guide.md` 诊断；无法解决则通过 `AskUserQuestion` 升级
    6. 在 `task-progress.md` 记录运行中的服务、PID、端口
  - Feature-ST（Step 10）负责重启/清理。此处启动的服务在 TDD 与 Quality Gates 期间保持运行。
- 冒烟测试先前 passing 的特性（按 `long-task-guide.md` 激活环境 → 直接运行测试命令）

### 3. Config Gate
```bash
python scripts/check_configs.py feature-list.json --feature <id>
```
`<id>` = Step 1 中选定的特性 ID。生成的 `check_configs.py` 自动以项目原生格式加载 config 值。

**如 config 缺失——提示文本输入并保存到项目 config：**

1. 对每个缺失的 `env` 类型 config，用 `AskUserQuestion` 请用户**键入值** —— **不要**提供预定义选项按钮。用 config 的 `name`、`description` 和 `check_hint` 包装问题，让用户知道该提供什么。
   - 例："Please enter the value for `OPENAI_API_KEY` (OpenAI API key for LLM integration). Hint: Get it from https://platform.openai.com/api-keys"
2. 对每个缺失的 `file` 类型 config，请用户提供文件路径或手动创建文件。
3. 收到所有值后，**按项目 config 格式保存 env 类型 config** —— 参阅 `long-task-guide.md` 的 `Config Management` 节了解具体方式（例如追加到 `.env`、在 `application.properties` 设置、导出为系统环境变量）。
4. 重跑检查确认：
   ```bash
   python scripts/check_configs.py feature-list.json --feature <id>
   ```
5. 如密钥 config 文件尚未在 `.gitignore` 中，确保添加。
6. **阻塞直至所有 config 通过。**
7. **连通性校验**（仅有服务依赖的特性）：
   config 键通过存在性检查后，校验连接串 config 实际能连上：
   - 对每个键匹配连接串模式（`DATABASE_URL`、`REDIS_URL` 等）的 `env` 类型 config：运行 `env-guide.md` "Verify Services Running" 中对应的健康检查
   - 如健康检查失败：config 值存在但服务不可达——按上方 Bootstrap 服务就绪协议启动服务
   - **阻塞直至连通性确认** —— 指向死服务的 config 等同缺失

**Config Gate 对有外部依赖的特性不可协商。** 如 config 缺失：
- **必须**使用 `AskUserQuestion` 向用户索取值
- **不得**在所有 config 未解决前进入 TDD
- **不得**对 `required_configs[]` 含连接串键（URL、HOST、PORT、DSN、URI、CONNECTION、ENDPOINT）的特性声称 "纯函数豁免"
- Quality Gates（Gate 0）通过 `check_real_tests.py --require-for-deps` 机械化强制此要求

### 4. Feature 详细设计

> **DISPATCH** → 启动独立 SubAgent 加载并执行 `long-task-feature-design`
> **with input**: feature_id=<id>, feature=<compact-json>, design_doc_path=<docs/plans/*-design.md §2.N>, srs_doc_path=<docs/plans/*-srs.md FR-xxx>, ucd_doc_path=<docs/plans/*-ucd.md> (if ui:true), ats_doc_path=<docs/plans/*-ats.md> (if exists), quality_gates=<compact-json>, tech_stack=<compact-json>, constraints=<list>, assumptions=<list>, output_path=`docs/features/YYYY-MM-DD-<feature-name>.md`
> **expect**: Structured Return Contract (`status` / `artifacts_written` / `next_step_input` / `blockers` / `evidence`) 按 `references/structured-return-contract.md`

Feature Design SubAgent 在自己的新鲜上下文中读取 design/SRS/UCD 文档节并写详细设计文档。主 Agent **不** 读文档节或草稿内容——只消费结构化返回。

> **对 `category: "bugfix"` 特性**：feature-design 精简。SubAgent 聚焦：(1) 根因记录、(2) 定向修复方式、(3) 回归测试清单。除非 bug 直接触达相关面，否则跳过完整图表。

需向前传递的上下文（仅路径——SubAgent 自己读内容）：
- Feature 对象（紧凑 JSON）
- `quality_gates` 与 `tech_stack`（紧凑 JSON）
- 文件路径 + 节行区间：设计文档（§2.N）、SRS 文档（FR-xxx）、UCD 文档（如 ui:true）
- ATS 文档路径：`docs/plans/*-ats.md`（如存在）—— SubAgent 用 ATS 映射对齐 Test Inventory 类别
- 设计文档 §4 路径 —— SubAgent 读取本特性为 Provider 或 Consumer 的 Internal API Contracts 行
- feature-list.json 根的 constraints 与 assumptions
- 输出路径：`docs/features/YYYY-MM-DD-<feature-name>.md`

输出：`docs/features/YYYY-MM-DD-<feature-name>.md`（由 SubAgent 写）—— 特性详细设计文档，含 Interface Contract、Visual Rendering Contract（ui:true）、Implementation Summary（散文 + Boundary Conditions + Existing Code Reuse）、Test Inventory。

**契约偏离处理**：如 SubAgent 返回 `BLOCKED` 且 issue 含 "Contract deviation"：
1. 通过 `AskUserQuestion` 向用户呈现偏离细节（Contract ID、原 schema vs 提议 schema、理由）
2. 如审批通过：更新设计文档 §4 以反映新契约，然后重新分发 feature-design SubAgent
3. 传播影响：从 §4 Consumer 列识别可能受影响的 Consumer 特性；如任何已 `"passing"`，警告用户可能需要重新校验

**歧义澄清处理**：如 Feature Design SubAgent 返回 `CLARIFY`：
- feature-design skill 的 CLARIFY handler 在内部管理完整澄清循环（AskUserQuestion → 收集回答 → 审批关卡 → 带 Clarification Addendum 重分发）
- Worker 不需要单独处理—— feature-design skill 解决 CLARIFY 并返回 PASS（已解决）或 BLOCKED（2 轮后无法解决）
- 若澄清揭示 SRS 缺陷（用户说 "SRS needs updating"）：
  1. 在 `task-progress.md` 记录缺口："SRS gap identified during Feature Design for #{id} — user directed to long-task-increment"
  2. 向用户建议："Consider placing an `increment-request.json` to update the SRS before continuing with this feature"
  3. 如用户同意：跳过此特性，进入下一个符合条件的特性（或无则结束会话）
  4. 如用户说 "proceed with current interpretation"：用已解决的澄清继续
- **同一模式适用于 Feature-ST**（Step 9）：feature-st skill 的 CLARIFY handler 管理自己的循环（最多 1 轮）；Worker 看到 PASS 或 BLOCKED。

### 5-7. TDD 循环（Red → Green → Refactor）

> **DISPATCH** → 启动独立 SubAgent 加载并执行 `long-task-tdd`
> **with input**: feature_id=<id>, feature=<compact-json>, quality_gates=<compact-json>, tech_stack=<compact-json>, feature_design_path=`docs/features/YYYY-MM-DD-<feature-name>.md` (from Step 4), srs_section_path=`docs/plans/*-srs.md#FR-xxx`, design_section_path=`docs/plans/*-design.md#4.N`, env_guide_path=`env-guide.md` (§2 activation + §3 test commands)
> **expect**: Structured Return Contract 按 `references/structured-return-contract.md` —— TDD 保持为单个 skill（Red → Green → Refactor 在 SubAgent 内顺序运行，不拆为三个 SubAgent）

**重要—— TDD 不拆分**：SubAgent 加载 `long-task-tdd` 并在自己的新鲜上下文中运行完整 Red → Green → Refactor 循环。主 Agent 在最后收到一个结构化返回，而非逐阶段返回。

### 8. Quality Gates

> **DISPATCH** → 启动独立 SubAgent 加载并执行 `long-task-quality`
> **with input**: feature_id=<id>, quality_gates=<compact-json>, tech_stack=<compact-json>, working_dir=<path>, feature_test_files=<paths-from-TDD-return>, env_guide_path=`env-guide.md` (§3 coverage + test commands)
> **expect**: Structured Return Contract 按 `references/structured-return-contract.md` —— `next_step_input` 必须含 `coverage_line` 与 `coverage_branch` 百分比

Quality SubAgent 在自己的新鲜上下文中运行所有 3 个关卡（Real Test → Coverage → Verify）。主 Agent **不** 读覆盖率报告或测试 runner 输出——只消费结构化返回。

### 9. ST 验收测试用例

> **DISPATCH** → 启动独立 SubAgent 加载并执行 `long-task-feature-st`
> **with input**: feature_id=<id>, feature=<compact-json>, quality_gates=<compact-json>, tech_stack=<compact-json>, design_doc_path, srs_doc_path, ucd_doc_path (if ui:true), ats_doc_path (if exists), feature_design_doc_path (from Step 4), env_guide_path=`env-guide.md` (§1 service lifecycle), working_dir=<path>, st_case_template_path (if set), st_case_example_path (if set)
> **expect**: Structured Return Contract 按 `references/structured-return-contract.md` —— `artifacts_written` 必须含 `docs/test-cases/feature-{id}-{slug}.md`

Feature-ST SubAgent 在 TDD 与 quality gates 通过**之后** 执行黑盒验收测试：在自己的新鲜上下文中读取 SRS/Design/UCD/ATS，生成 ISO/IEC/IEEE 29119 合规测试用例，执行它们，并管理服务生命周期。主 Agent 仅消费结构化返回。

**硬关卡：**
- **不可绕过** —— 任何原因都不能跳过 ST
- 主 Agent 按 feature-st SKILL.md 分类失败：AI 可自修的问题（代码 bug、环境问题）自主解决，无重试上限；只有需要人类手工测试的问题（缺凭据、物理设备、视觉判断）通过 `AskUserQuestion` 升级

### 10. Inline 合规检查（无 SubAgent）

直接运行这些机械化检查——不需要 SubAgent 分发。
读取 Step 4 产出的特性设计文档（`docs/features/YYYY-MM-DD-<feature-name>.md`）。

**a) 接口契约校验（P2 等价）：**
从特性设计文档读取 Interface Contract 表。对每个列出的 PUBLIC 方法，grep 实现文件确认该方法以匹配签名（名称、参数、返回类型）存在。标记缺失或不匹配的方法。

**b) Test Inventory ↔ 测试文件交叉检查（T2 等价）：**
从特性设计文档读取 Test Inventory 表。对每一行测试，确认对应测试函数存在于测试文件：
```bash
grep -q "{test_function_name}" {test_file}
```
若找不到任何测试函数，搜索相似名并修复 ST 文档 traceability 矩阵引用。

**c) 设计依赖版本（D3 等价）：**
若 Interface Contract 或 Implementation Summary 引用 2/3方件 库版本，抽查 `requirements.txt` / `package.json` / `pom.xml` 是否匹配。标记不匹配。

**d) UCD 抽查（U1 等价，仅 ui:true）：**
grep CSS/样式文件查找不在 UCD 色板 token 中的硬编码颜色 hex 值。

**e) ST 文档完整性：**
确认 `validate_st_cases.py` 已在 Feature-ST（Step 9）通过。
无需重校验—— Feature-ST Step 5b + Step 6 已覆盖 T1。

**f) 存量约定抽查（建议性、非阻塞——若无 `env-guide.md §4` 则跳过）：**
抽查 2-3 个新/修改文件对照 `env-guide.md §4`：
- §4.1：新 import 在有内部库替代时不使用禁用的标准/2/3方件 API
- §4.3：命名约定匹配成文模式（变量/函数/类名）
如发现偏离：作为建议性注记记录到 `task-progress.md`。**非阻塞关卡** —— 设计 / 框架约定优先于 scanner 观察。

若所有检查通过 → 进入 Persist。
若任何检查失败 → 就地修复，重新校验。不分发 SubAgent。

在 `task-progress.md` 记录：
```
- Inline Check: PASS (P2: N/N methods verified, T2: N/N tests found, D3: OK)
```

### 11. Persist
- Git commit（包含实现、测试、**测试用例文档**）
  > **Commit 格式**：若 `docs/rules/commit-conventions.md` 存在，遵循该格式。否则用下方默认。
  > **对 `category: "bugfix"` 特性**：用 commit 前缀 `"fix:"` 而非 `"feat:"`。
  > 格式：`fix: <feature title without the "Fix: " prefix> (#<fixed_feature_id>)`
- commit 后立即抓取 commit SHA：
  ```bash
  git rev-parse --short HEAD
  ```
  把此值存为 `{commit_sha}` —— 接下来两个步骤使用。
- 更新 `RELEASE_NOTES.md`（Keep a Changelog 格式）
  > **对 `category: "bugfix"` 特性**：在 `### Fixed` 下添加条目（不在 `### Added`）：
  > `- [<bug_severity>] <title without "Fix: "> (fixes #<fixed_feature_id>) — <root_cause one-line>`
- 更新 `task-progress.md`：
  - 更新 `## Current State` 头部：进度计数（X/Y passing）、上个完成特性（#id title，date）、下一个特性（#id title），并**移除任何 `in-progress: step-N` 标记**（循环成功完成）
  - 在日志分隔线下追加 session 条目；session 条目格式：
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    - Quality Gates: N% line, N% branch
    - Feature-ST: N cases, all PASS
    - Inline Check: PASS
    - Git: {commit_sha} feat: title
    #### Risks                        ← include only if any risks were reported
    - ⚠ [Mutant] file:line — reason
    - ⚠ [Coverage] metric N% — thin margin / uncovered boundary
    - ⚠ [Dependency] lib==ver — known patch / breaking change pending
    ```
  - **`{commit_sha}` 必须是实际抓取值** —— 不得是占位符。这确保 `task-progress.md` 与 `feature-list.json` 携带同一已核实 SHA。
  - **收集风险**：Step 8（Quality）与 Step 9（Feature-ST）完成后，从其 `### Risks` 表抽取每一行；合并为单一列表；若列表非空则作为 `#### Risks` bullet 追加
- 在 `feature-list.json` 标记特性 `"status": "passing"`
- 在 `feature-list.json` 特性对象上设置 `"st_case_path"`、`"st_case_count"`、`"git_sha": "{commit_sha}"`
- 校验：
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- 再次 git commit（进度文件）：
  ```bash
  git add feature-list.json task-progress.md RELEASE_NOTES.md
  git commit -m "chore: update progress — feature #{id} passing"
  ```

### 11.5 Session 反思（条件性）

若 `feature-list.json` 中 `retro_authorized` 为 `true`：
1. 读取 `skills/long-task-retrospective/prompts/reflection-prompt.md`
2. 填充模板变量：特性 ID/标题、阶段、本会话 `task-progress.md` 条目、任何用户纠正 skill 输出的 `AskUserQuestion` 交互
3. 通过 `Agent(run_in_background=true)` 分发 Reflection SubAgent —— **不要**等待完成
4. 立即进入 End Session

若 `retro_authorized` 缺失或 `false` → 完全跳过（无输出、无分发）。

### 12. End Session
- 停止任何你在本循环期间直接启动的服务（Step 10 ST 验收测试期间启动的服务由 `long-task-feature-st` 停止）
- 输出简洁完成摘要：
  > **Feature #\<id\> (\<title\>) — DONE**
  >
  > Next: Feature #\<next_id\> (\<next_title\>)
- 若**无剩余未 passing 的非弃用特性**：
  > All active features passing — next session begins System Testing.
- 结束会话 —— **永不循环回 Step 1**

auto-loop 脚本（`scripts/auto_loop.py`）在外部处理多特性自动化——每次调用都是新鲜上下文。

## 关键规则

- **每会话一个特性** —— 完成一个特性后结束会话；多特性自动化由外部 auto-loop 脚本（`scripts/auto_loop.py`）处理
- **严格 step 顺序** —— 不跳过、不重排
- **子 skill 不可协商** —— ST Test Cases、TDD、Quality **必须**通过 Skill 工具调用
- **Config 关卡在计划前** —— 必需 config 缺失时永不计划或编码
- **无新鲜证据不得标 "passing"** —— 先跑测试读输出，再标记
- **仅系统化调试** —— 出错时阅读 `references/systematic-debugging.md`；追根因，永不猜测修复
- **每次 git commit 后更新 RELEASE_NOTES.md**
- **结束会话前总是 commit + 更新进度** —— 弥补上下文缺口
- **永不留下坏代码** —— 回退未完成工作

## 红旗信号

| 理性化逃避 | 正确动作 |
|---|---|
| "这个 config 我稍后 mock" | 运行 Config Gate。需要真实 config。|
| "这个特性太小，跳过测试用例" | 调用 long-task-feature-st。每个特性都要。|
| "这个特性太小，跳过 TDD" | 调用 long-task-tdd。每个特性都要。|
| "测试通过就标完成" | 先调用 long-task-quality。|
| "覆盖率接近就行" | 阈值是硬关卡。跑工具。|
| "让我快速试一下这个修复" | 先系统化调试。|
| "Worker 期间生成示例" | 示例在 ST 后通过 long-task-finalize。|
| "最后再更新 release notes" | 每次 commit 后更新。|
| "UI 我看起来对" | 跑自动化检测 + EXPECT/REJECT。|
| "ST 测试用例失败但代码没问题" | 不可绕过。AI 必须修代码并重分发——无重试上限。若测试规格错误，用 `long-task-increment` 修改。仅当问题真的需要人类手工测试时才升级。|
| "端口被占用，我手动杀" | 用 env-guide.md "Stop All Services"（端口兜底）杀掉，再通过 env-guide.md Start 重启——若命令需更正则更新 env-guide.md。|
| "环境挂了，跳过 ST 用例" | BLOCKED，不是 skipped。修环境或问用户。|
| "这个弃用特性还要做" | 跳过。弃用特性被排除。|
| "后端没好但我先 mock" | 依赖检查存在是有原因的。先做后端特性。|
| "这次跳过依赖检查" | 永不跳过。重排特性让依赖满足。|
| "SRS 模糊但我就假设……" | SubAgent 应标 CLARIFY。关键路径（Interface Contract、Test Inventory expected results、跨特性契约）上的假设会造成后期返工。只有低影响歧义可假设。|

## 出错时

遵循系统化调试流程—— **永不猜测修复**：
1. 收集证据（错误消息、堆栈、git diff）
2. 复现问题
3. 追踪根因（阅读 `references/systematic-debugging.md` 获取详细流程）
4. 为 bug 写失败测试
5. 用单一定向变更修复
6. 3 次尝试后放弃 → 升级给用户
