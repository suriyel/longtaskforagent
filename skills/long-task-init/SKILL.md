---
name: long-task-init
description: "Use when ATS doc exists (or auto-skipped) but feature-list.json not yet created - scaffold project artifacts and populate features from Design §6.1"
---

# 初始化 Long-Task 项目

在 SRS 与设计都获批后运行一次。打包所有持久化工件，从 Design §6.1 任务分解（FR 已在需求阶段调整到合适大小）填充特性，并为迭代 Worker 循环准备项目。

**开始时宣告：** "I'm using the long-task-init skill to scaffold the project."

## 输入文档

本 skill 读取 **三份** 已审批文档：

| 文档 | 位置 | 提供 |
|----------|----------|----------|
| **SRS** | `docs/plans/*-srs.md` | 功能需求（FR-xxx）、NFR（NFR-xxx）、约束（CON-xxx）、假设（ASM-xxx）、接口需求（IFR-xxx）、术语表、用户角色、验收标准 |
| **Design** | `docs/plans/*-design.md` | 技术栈、架构、数据模型、API 设计、测试策略 |
| **ATS** | `docs/plans/*-ats.md` | 需求→场景映射、每条需求所需测试类别（通过 srs_trace 查询约束下游 feature-st）|

## Checklist

你必须为每个 step 创建一个 TodoWrite 任务并按顺序完成：

1. **阅读已审批的 SRS、design、ATS 文档**，位于 `docs/plans/`
   - SRS：`docs/plans/*-srs.md` —— 用于需求、约束、假设、NFR、术语表、角色
   - Design：`docs/plans/*-design.md` —— 用于技术栈、架构决策
   - ATS：`docs/plans/*-ats.md` —— 用于需求→类别映射（通过 srs_trace 约束 `ui` 标记与下游 feature-st 类别要求）
2. **运行 `scripts/init_project.py`** 打包确定性工件：
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` —— 来自 SRS 标题
   - `<language>` —— 设计文档技术栈中的 `python|java|typescript|c|cpp` 之一
   - 使用 `--line-cov`、`--branch-cov` 覆盖阈值（默认：90/80）
   - 创建：`feature-list.json`、`CLAUDE.md`（追加）、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`docs/plans/`
   - 自动复制辅助脚本（`validate_features.py`、`check_configs.py`、`check_devtools.py`、`check_real_tests.py`、`validate_guide.py`、`get_tool_commands.py`、`validate_st_cases.py`、`validate_increment_request.py`、`validate_bugfix_request.py`、`check_st_readiness.py`、`check_ats_coverage.py`）到项目 `scripts/`

3. **校验 `feature-list.json` 中的 `tech_stack` 与 `quality_gates`**：
   - 确认 `language`、`test_framework`、`coverage_tool` 与设计文档一致
   - 如需要调整 `quality_gates` 阈值（默认：line 90%、branch 80%）
   - 校验工具命令能正确解析：
     ```bash
     python scripts/get_tool_commands.py feature-list.json
     ```
   - 校验 feature-list.json 中的 `real_test` 配置：
     - `marker_pattern` 匹配项目所选的真实测试识别方法
     - `mock_patterns` 覆盖项目的 mock 框架关键词
     - `test_dir` 指向正确的测试目录
4. **生成 `long-task-guide.md`** —— 创建项目专属的 Worker 会话导航指南（**仅工作流导航——构建/测试/覆盖率命令位于 `env-guide.md` §3**）：
   - 阅读以下文件作为参考：
     - `skills/long-task-work/SKILL.md` —— Worker 工作流
     - `skills/long-task-quality/SKILL.md` —— 校验强制
     - `skills/using-long-task/references/architecture.md` —— TDD 工作流细节
   - **仅当** 项目有 UI 特性（`"ui": true`）时包含 UI 测试节：使用 Chrome DevTools MCP 工具名（`navigate_page`、`click` 等）
   - **必须包含所有必需节**：Orient、Bootstrap、Config Gate、TDD Red、TDD Green、Coverage Gate、TDD Refactor、Verification Enforcement、Inline Compliance Check、Persist、Critical Rules
   - **不要嵌入具体构建/测试/覆盖率命令。** 对每个命令引用，改为附上指引："See `env-guide.md` §3 Build & Execution Commands"。这防止两个文件漂移。
   - **必须包含 `Config Management` 节**：描述如何为本项目新增/更新 config 值（例如，对 dotenv 项目"追加 `KEY=value` 到 `.env`"；对 Spring Boot 项目"在 `application.properties` 设置 `key=value`"；对仅系统环境的项目"export KEY=value"）。Worker Config Gate 在提示用户缺失值时会引用本节。
   - **必须包含 `Real Test Convention` 节**：识别方法（marker/folder/naming，适配项目语言）、**指引** 到 env-guide.md §3 对应仅运行真实测试的命令、本项目技术栈下的真实测试示例
   - **必须包含 `Service Commands` 指引**："See `env-guide.md` §1 Service Lifecycle" —— 不要在此重复 start/stop/restart 命令
   - 校验：
     ```bash
     python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
     ```
5. **生成 `env-guide.md`** —— 为项目创建环境契约的**单一事实源**（六节，用户可编辑，§3 与 §4 受人类审批关卡保护）：

   > 从 `docs/templates/env-guide-template.md` 复制模板，并基于设计文档与存量项目扫描输出（`docs/rules/`）填充各节。初次生成后，frontmatter 中保持 `approved_by: null` —— 这是首次生成豁免；**下次** 编辑 §3 或 §4 时审批变为强制。

   **Frontmatter**（文件顶部）：
   ```yaml
   ---
   version: 1.0
   approved_by: null        # null = first-generation exemption
   approved_date: null
   approved_sections: []
   ---
   ```

   **§1 服务生命周期** —— 从设计文档（服务端口声明、健康检查 URL、服务名）与 `.env.example` 的 `*_PORT=` 变量填充：
   - **Services 表** 带列：Service Name、Port、Start Command、Stop Command、Verify URL
   - **Start All Services** —— 每个服务发出一个带输出捕获的命令：
     ```bash
     # Unix/macOS
     [start command] > /tmp/svc-<slug>-start.log 2>&1 &
     sleep 3
     head -30 /tmp/svc-<slug>-start.log

     # Windows alternative
     cmd /c "start /b [command] > %TEMP%\svc-<slug>-start.log 2>&1"
     timeout /t 3 /nobreak >nul
     powershell "Get-Content $env:TEMP\svc-<slug>-start.log -TotalCount 30"
     ```
   - **Verify Services Running** —— `curl -f http://localhost:<port>/health`
   - **Stop All Services** —— `kill <PID>`（Unix）/ `taskkill /F /PID <PID>`（Windows），端口级兜底 `lsof -ti :<port> | xargs kill -9`
   - **Verify Services Stopped** —— `lsof -i :<port>` 期望空输出
   - **重启协议（4 步）**：Kill → Verify dead（轮询 ≤5s）→ Start + capture → Verify alive（轮询 ≤10s）
   - **复杂启动序列（>2 个 shell 命令）**：抽取到 `scripts/svc-<slug>-start.sh` / `.ps1`；从 §1 引用脚本
   - 仅 CLI / 仅库项目：在此节写 "No server processes — environment activation only"

   **§2 环境配置**：
   - 环境激活命令（例如 `source .venv/bin/activate`、`conda activate <env>`、`nvm use`）
   - 必需环境变量 —— 引用 `.env.example`
   - 配置加载 —— 引用 `scripts/check_configs.py`

   **§3 构建与执行命令** —— 本节是下游流水线（TDD / Quality / Feature-ST）直接读取的节。所有命令使用**静默执行**：
   ```bash
   # Build
   <build-cmd> > /tmp/build-$$.log 2>&1; echo $? > /tmp/build-$$.exit

   # Unit tests
   <test-cmd> > /tmp/ut-$$.log 2>&1; echo $? > /tmp/ut-$$.exit

   # Coverage
   <coverage-cmd> > /tmp/cov-$$.log 2>&1; echo $? > /tmp/cov-$$.exit

   # Static analysis (if docs/rules/coding-constraints.md lists a tool)
   <static-analysis-cmd> > /tmp/static-$$.log 2>&1; echo $? > /tmp/static-$$.exit
   ```
   - 包含**工具版本锁**条目（例如 Python ≥ 3.11、Node ≥ 20）。
   - 包含 **Re-check 协议**：任何失败 → 修复并**仅按名字** 重跑失败的步骤/测试，永不全量重跑。
   - **初次生成后对 §3 的任何修改都需人类审批**（frontmatter `approved_by` / `approved_date` 更新）。

   **§4 存量代码库约束** —— 从 `docs/rules/*.md` 直接提取：
   - §4.1 强制内部库 ← `docs/rules/coding-constraints.md` 的 "Mandatory Internal Libraries" 表
   - §4.2 禁用 API ← `docs/rules/coding-constraints.md` 的 "Prohibited APIs / Libraries" 表
   - §4.3 代码样式基线 ← `docs/rules/coding-style.md`
   - §4.4 构建系统约定 ← `docs/rules/build-and-compilation.md`
   - 若 `docs/rules/coding-constraints.md` 含 "Static Analysis Tools" 表：对应命令写入 §3 静态分析位，不进 §4。
   - **初次生成后对 §4 的任何修改都需人类审批**（Worker Step 0 `check_env_guide_approval.py` 强制）。
   - greenfield（无 `docs/rules/` 或仅含占位）：§4 各表写 "_(empty — greenfield project)_"。

   **§5 测试环境依赖**：
   - 数据库、消息队列、2/3方件 服务本地副本配置
   - Chrome DevTools MCP 启动命令（仅当项目有 UI 特性时）
   - WireMock / MockServer / 测试容器 设置（如适用）

   **§6 人类审批记录**：
   - 审批工作流描述（从模板复制）
   - 历史表带列：Date、Version、Approved By、Change Summary —— 为初次生成预填一行

   **生成后运行**：
   ```bash
   python scripts/validate_env_guide.py env-guide.md
   ```
   必须通过才能继续到 Step 6。

6. **生成 `init.sh` / `init.ps1`** —— 创建真实可运行的 bootstrap 脚本：
   - 阅读 `references/init-script-recipes.md`（在 long-task-init skill 目录）获取每种工具的模板与最佳实践
   - **从设计文档技术栈与项目约束检测环境管理器**：
     - Python：miniconda/conda/mamba、venv、poetry、pipenv、uv、pyenv
     - Node.js：nvm、fnm、volta、corepack
     - Java：sdkman、jenv
     - 通用：devcontainer、docker、nix
   - **必须处理**：环境创建、激活、依赖安装、工具版本校验
   - **必须幂等** —— 可安全重跑而不破坏已有环境
   - **必须跨平台** —— `init.sh` 用于 Unix/macOS，`init.ps1` 用于 Windows
   - **必须包含**：错误处理、版本检查、清晰的成功/失败输出
   - 实际依赖安装命令（不是注释占位）
   - 必须在 `git clone` 后立即可执行
   - **注意**：psutil 不再必需——服务生命周期通过 `env-guide.md` 命令管理，而非 hook
7. **从 SRS 文档填充 `feature-list.json` 的 SRS 字段**：
   - `constraints[]` —— 从 SRS "Constraints" 节复制 CON-xxx 项；每条一个简洁字符串
   - `assumptions[]` —— 从 SRS "Assumptions & Dependencies" 节复制 ASM-xxx 项；每条一个简洁字符串
   - NFR-xxx 行 → 创建 `category: "non-functional"` 特性，带 `srs_trace`（例如 `["NFR-001"]`）与可选的可度量 `verification_steps`；覆盖率关卡不适用于 NFR 特性
8. **从 Design §6.1 填充特性** —— FR 已在需求阶段调整到合适大小（G1-G6 过大 + S1-S4 过小启发式）。设计文档的任务分解表（§6.1）把合适大小的 FR 映射到按依赖排序的优先特性。填充 `feature-list.json` `features[]`：
   - 每个 §6.1 行 → 一个特性。**不要**进一步拆分或合并——粒度已在 SRS 阶段敲定。
   - **FR 直接合并规则**：共享同一模块/实体/角色的相邻 FR 应当已在 Design §6.1 合并为单一特性。若 Design §6.1 仍含碎片化的单 FR 行，在本填充步骤期间优先直接合并——目标是每特性约 1000 LOC（±500）。见 Step 8b 的粒度确认关卡强制此要求。
   - `srs_trace`：复制 "Mapped FRs" 列
   - `title` + `description`：从 §6.1 特性名 + 被分组 FR 的描述派生
   - `priority`：P0/P1 → `"high"`，P2 → `"medium"`，P3 → `"low"`
   - `dependencies`：来自 §6.2 依赖链图
   - `status`：始终为 `"failing"`
   - UI 特性：设 `"ui": true`、`"ui_entry": "/path"`（强制——指定本特性 UI 访问的 URL）；至少包含一个带 `[devtools]` 前缀的校验步断言特性主渲染输出的**正面视觉存在**（不仅是错误缺失）。例：`"[devtools] /game | EXPECT: canvas#game-board with rendered game elements (snake segments, food item, score display), game board grid visible | REJECT: blank canvas, empty game container, 'undefined' in score"`
   - `verification_steps` 是可选的 —— 如提供，把所有映射 FR 的验收标准整合为行为场景（Given/When/Then）：
     - 每一步**必须**是带 Given/When/Then 结构的行为场景，不是简单断言
     - BAD：`"Login page displays correctly"` → 无动作、无断言
     - GOOD：`"[devtools] Navigate /login → EXPECT: email input, password input, 'Sign In' button; fill valid creds → click Sign In → EXPECT: redirect to /dashboard, user name in header; REJECT: console errors, broken images"`
     - GOOD：`"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - 对 `"ui": true` 特性：每个 `[devtools]` 步**必须**描述多步交互链（navigate → interact → verify → interact → verify）
     - 对有后端依赖的特性：至少一步**必须**校验跨依赖边界的真实数据流
     - **最小复杂度**：每个特性**应当**有 ≥ 1 条含 3+ 链式动作的 verification_step
   - **ATS 类别约束**（如 ATS 文档存在）：对每个特性，用 srs_trace 查询 ATS 所需类别。如任何 srs_trace 需求的 ATS 类别含 UI，设 `ui: true`。
   - **后端-前端配对规则**：前端特性（`"ui": true`）**必须**在 `dependencies[]` 列出后端 API 依赖特性。
   - **排序**：遵循 §6.1 行顺序（Design 已按优先级排序并配对 backend/frontend）
   - 每个特性**必须**能独立校验且在一次会话内完成
   - **校验关卡**：填充所有特性后，核对：
     - SRS 的每个 FR-xxx 都出现在至少一个特性的 `srs_trace`（无孤立需求）
     - 每个特性的 `srs_trace` 都至少含一个 FR（无空 trace）

8b. **特性 sizing 与粒度确认**（硬关卡——初次填充后、持久化 `feature-list.json` 之前）：

   从 SRS 验收标准数、接口契约面、测试清单规模估算每个特性的预期 LOC（透明公式见下）。分类每个特性并向用户呈现分布。

   **目标粒度**：每特性约 1000 LOC（±500）。SRS `Single-Round: Yes` 模式（见 8c）允许至多约 2000 LOC。

   **LOC 估算公式**（透明——用户可更正）：
   ```
   est_loc = (sum of AC counts × 80)
           + (interface-contract method count × 100)
           + (test-inventory estimated rows × 30)
   ```
   其中 AC 数来自 SRS `srs_trace` 需求；method/test 数在本阶段是估值（Design §4 作参考）。

   **分类带**（标准模式）：

   | 带 | LOC 区间 | 动作 |
   |------|-----------|--------|
   | 过小 | < 500 | 建议与相邻同模块特性合并 |
   | 合适 | 500–1500 | 接受 |
   | 过大 | > 1500 | 建议拆分为 N 个特性，每个携带共享 `srs_trace` |

   **呈现** —— 使用 `AskUserQuestion`：
   ```
   Feature count: 15
   Estimated LOC distribution:
     - < 500 LOC (too small):  2 features → suggest merge
     - 500-1500 LOC (ok):      11 features ✓
     - > 1500 LOC (too large): 2 features → suggest split
   Adopt current decomposition? [y / auto-fix / manual-adjust]
   ```
   - `y` → 保持现状；进入 Step 9
   - `auto-fix` → 应用合并/拆分建议（保持 srs_trace 可追溯性；拆分时每个结果特性携带父的 `srs_trace`）；重新显示分布；重做关卡
   - `manual-adjust` → 暂停；告诉用户编辑 feature-list.json 草稿并确认，然后重跑本关卡

   **数量边界——上下文预算 sizing**（**不是** 旧的硬编码 10-200 区间）：
   ```
   lower_bound = ceil(total_estimated_LOC / max_feature_LOC)
                 # max_feature_LOC = 1500 (standard) or 2000 (single-round)
   upper_bound = floor(context_budget_tokens / avg_feature_tokens)
                 # typical avg_feature_tokens ≈ 8000-15000 depending on project
   ```
   如果填充数量落在 `[lower_bound, upper_bound]` 之外，作为确认关卡的一部分向用户标注——解释触及了哪条边界及原因。**不要**强加固定数值区间。

8c. **SRS 单轮模式**（可选，来自 SRS frontmatter）：
    若 SRS 文档顶部声明 `Single-Round: Yes`（在需求阶段 Step 10 设置——用户已确认的单次交付），在 `feature-list.json` 根记录 `"single_round": true`（信息性标记）。
    此模式下，Step 8b 接受每特性至多约 2000 LOC（合并带放宽）。下游无其他行为变化——该标记仅表示意图。

9. **填充 `required_configs`** —— 来自 **SRS 文档**（IFR-xxx 接口需求）与设计文档：
   - API key、服务 URL → type `env`
   - 配置文件、证书 → type `file`
   - 通过 `required_by` 关联到特性；提供带设置说明的 `check_hint`
9b. **生成 `scripts/check_configs.py`** —— 项目专属 config 检查器（LLM 生成，不从插件复制）：
    - 基于 `tech_stack.language` 与设计文档分析项目的 config 格式：
      - Python + `.env` 模式 → 使用 `load_dotenv` 风格的 KEY=VALUE 解析
      - Java/Spring → 解析 `src/main/resources/application.properties` 或 `application.yml`
      - Node.js → 读取 `.env` 或 `config/` 目录
      - Go / Rust → 读取 TOML / YAML config 文件，或依赖系统环境
      - 任何纯依赖系统环境变量的项目 → 无需文件加载
    - 生成具备此**标准接口**的脚本：
      - 用法：`python scripts/check_configs.py feature-list.json [--feature <id>]`
      - 从 `feature-list.json` 读取 `required_configs[]`
      - 以项目原生格式加载 config 值（为本项目硬编码）
      - 通过 `os.environ` 检查每个 `env` 类型 config，通过 `os.path.exists` 检查每个 `file` 类型 config
      - 打印每个缺失 config 的 `name` 与 `check_hint`
      - Exit 0 = 所有必需 config 存在；Exit 1 = 一个或多个缺失
    - **无需 `--dotenv` 或格式标志** —— 加载逻辑为本项目内建
    - 插件的 `scripts/check_configs.py` 可作为参考模板
10. **生成 `.env.example`** —— 来自 `required_configs`：
    - 每个 `env` 类型 config 写一行注释模板：
      ```
      # <name> — <description>
      # Hint: <check_hint>
      # Required by features: <required_by ids>
      <KEY>=
      ```
    - 把密钥类 config 文件加入 `.gitignore`（例如 `.env`）；`.env.example` 可安全提交
    - 本模板列出必需环境变量；用户通过项目所用 config 格式加载它们；Worker Config Gate 会提示缺失值
11. **校验**：
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
12. **脚手架项目骨架**（目录、config、依赖清单）—— 基于**设计文档**架构
13. **Git init + 初始提交**
14. **运行 init 脚本并校验环境**：
    - 运行 `init.sh`（或 `init.ps1`），校验环境设置无错误完成
    - 校验测试执行可用：激活环境 → 运行 `long-task-guide.md` 中的测试命令 → 确认测试可执行（此时可能全部失败——这是预期的）
    - 如任何检查失败：诊断根因，修复脚本或配置，重跑
    - **不要**在此启动服务——服务在 ST 测试期间使用 `env-guide.md` 中定义的命令启动
15. **更新 `task-progress.md`** —— 更新 `## Current State` 为初始进度（0/N 特性通过），随后追加 Session 0 条目（包含 SRS + 设计文档引用）
16. **开始首次 Worker 循环** —— **必需子 skill：** 调用 `long-task:long-task-work`

## 服务 Config 维护（Worker 循环）

当 Worker 循环引入新后端服务、改变服务端口或发现实际 start/stop 命令与 env-guide.md 不同时，更新 `env-guide.md`：
- 新增/更新 Services 表行（服务名、端口、start/stop/verify 命令）
- 新增/更新对应的 Start、Verify、Stop、Restart 命令
- 如启动或停止序列需要 >2 个 shell 步骤：抽取到 `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-stop.sh` 并更新 env-guide.md 引用脚本
- 把 env-guide.md 与任何 `scripts/svc-*` 变更与特性同一个 git commit 提交

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
  "quality_gates": {
    "line_coverage_min": 90,
    "branch_coverage_min": 80
  },
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
  "required_configs": [
    {
      "name": "Display name",
      "type": "env|file",
      "key": "ENV_VAR (for env type)",
      "path": "path/to/file (for file type)",
      "description": "What this config is for",
      "required_by": [1, 3],
      "check_hint": "How to set it up"
    }
  ],
  "features": [...]
}
```

每个特性：
```json
{
  "id": 1,
  "category": "core",
  "title": "Feature title",
  "description": "What it does",
  "priority": "high|medium|low",
  "status": "failing|passing",
  "srs_trace": ["FR-001", "FR-002"],
  "verification_steps": ["step 1", "step 2"],
  "dependencies": [],
  "ui": false,
  "ui_entry": "/optional-path"
}
```

## 生成的持久化工件

| 文件 | 用途 |
|------|---------|
| `feature-list.json` | 带状态的结构化任务清单 |
| `CLAUDE.md` | 跨会话导航索引（追加）|
| `task-progress.md` | 逐会话进度日志 |
| `RELEASE_NOTES.md` | 活发布说明（Keep a Changelog 格式）|
| `examples/` | 可运行示例目录 |
| `init.sh` / `init.ps1` | 环境 bootstrap（LLM 生成）|
| `env-guide.md` | 服务生命周期命令—— start/stop/restart/verify 带输出捕获；用户可编辑 |
| `long-task-guide.md` | 带环境激活 + 直接测试命令的 Worker 会话指南（LLM 生成，已校验）|
| `.env.example` | 必需 env config 模板（可安全提交）|

## Retrospective 授权（最后步骤）

所有工件打完骨架且 feature-list.json 创建后：

```bash
python scripts/check_retro_auth.py feature-list.json
```

- **Exit 0**（endpoint 已配置且可达）：使用 `AskUserQuestion` 询问用户：
  > "检测到 Skill 反馈 API 已配置（{endpoint}）。是否授权在本项目中搜集 Skill 改进建议并在项目结束后上报？搜集内容包括：用户反馈修正、技能缺陷分析。不包含项目代码或业务数据。"
  > 选项："授权 (Recommended)" / "不授权"
  - 用户授权 → 在 `feature-list.json` 根设 `"retro_authorized": true`
  - 用户拒绝 → 在 `feature-list.json` 根设 `"retro_authorized": false`
- **Exit 1 或 2**（不可用或禁用）：静默跳过——不询问用户

## 集成

**被调用方：** long-task-ats（Step 12）或 using-long-task（ATS 文档存在、无 feature-list.json 时）
**读取：** `docs/plans/*-srs.md`（需求）+ `docs/plans/*-design.md`（架构）+ `docs/plans/*-ats.md`（测试策略约束）
**衔接到：** long-task-work（初始化完成后）
**产出：** feature-list.json + 上述所有打骨架工件
