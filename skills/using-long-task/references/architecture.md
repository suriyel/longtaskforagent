# Long-Task Agent 架构（Architecture）

## 核心概念

长任务超出单个上下文窗口。解决方案：将工作切分为 **Requirements Phase**（SRS）、**UCD Phase**（UI 项目）、**Design Phase**、**ATS Phase**（验收测试策略）、**Initializer Session**（运行一次）与多次 **Worker Sessions**（迭代运行），通过磁盘上的持久化产物相连。

### ATS 下游影响

ATS 文档（`docs/plans/*-ats.md`）将每条 SRS 需求映射到带有必需测试类别（`FUNC, BNDRY, SEC, UI, PERF`）的验收场景。它向下游流动：

- **SRS → ATS**：SRS 中撰写的验收准则（Given/When/Then）驱动 ATS 场景推导。结构良好、含显式边界条件与错误分支的验收准则能产出更强的 ATS 覆盖。
- **UCD → ATS**：UCD 中定义的 UI 组件与页面在 ATS 阶段获得对应的 UI 测试类别。含交互状态与无障碍约束的组件会成为 ATS 测试场景。
- **ATS → Init**：Init 使用 `srs_trace` → ATS 类别查找来设置 `ui` flag 并指导特性分解。
- **ATS → Feature-Design**：Test Inventory（§7）必须覆盖该特性需求所要求的全部 ATS 主类别。
- **ATS → Feature-ST**：硬关卡 — ST 测试用例必须覆盖 ATS 要求的类别。
- **ATS → System-ST**：硬关卡 — `check_ats_coverage.py --strict` 必须退出 0。

## 持久化产物

### 1. `task-progress.md`

跨上下文缺口的会话日志。每次 worker 会话追加一条。

```markdown
# Task Progress Log

## Project: [name]
Created: [date]

---

### Session 1 — [date/time]
**Focus**: User authentication API endpoints
**Completed**:
- POST /auth/login with JWT
- POST /auth/register with validation
- Unit tests for auth module (12/12 passing)
**Issues**: None
**Next Priority**: Password reset flow (feature #5)
**Git Commits**: a1b2c3d, e4f5g6h
```

### 2. `feature-list.json`

结构化任务清单。JSON 格式防止模型意外破坏。同时携带 SRS 派生的项目级上下文（`constraints`、`assumptions`），Worker 在每次 Orient 阶段都读取。

```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "constraints": [
    "Must run offline — no external API calls permitted",
    "Python 3.8+ only — no 3.10+ match syntax"
  ],
  "assumptions": [
    "JWT validation handled by API Gateway; business layer must NOT re-validate",
    "Input data is pre-sanitised before reaching this service"
  ],
  "features": [
    {
      "id": 1,
      "category": "core",
      "title": "User login with JWT",
      "description": "POST /auth/login returns JWT token on valid credentials",
      "priority": "high",
      "status": "passing",
      "srs_trace": ["FR-001"],
      "verification_steps": [
        "Send POST with valid credentials, verify 200 + token",
        "Send POST with invalid credentials, verify 401",
        "Verify token contains correct claims"
      ],
      "dependencies": []
    },
    {
      "id": 2,
      "category": "core",
      "title": "User registration",
      "description": "POST /auth/register creates new user account",
      "priority": "high",
      "status": "failing",
      "srs_trace": ["FR-002"],
      "verification_steps": [
        "Send POST with valid data, verify 201",
        "Send POST with duplicate email, verify 409",
        "Verify password is hashed in DB"
      ],
      "dependencies": []
    }
  ]
}
```

**规则**：
- Status 仅为 `"failing"` 或 `"passing"` — 绝不为 `"partial"` / `"in-progress"`
- `srs_trace` 每个 feature 必填 — 映射到 SRS 需求 ID 用于 ATS 类别查找
- `verification_steps` 可选 — 若存在，提供补充测试上下文
- 标记为 `"passing"` 的 feature 必须在会话开始时复验

### 3. `init.sh` / `init.ps1`

环境启动脚本。**由 LLM 在 Initializer 阶段依据设计文档的技术栈生成** — 并非由 `init_project.py` 硬编码。必须包含真实可运行的命令（非注释残留）。

必须支持项目实际使用的环境管理器（conda/miniconda/mamba、venv、poetry、uv、nvm、fnm、sdkman、docker 等）。按工具模板请见 `skills/long-task-init/references/init-script-recipes.md`。

**要求**：幂等、跨平台（`init.sh` + `init.ps1`）、快速失败、版本锁定、无交互式提示。

Python 项目 + conda 示例：
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_NAME="my-project"
PYTHON_VERSION="3.11"

# Detect conda/mamba
if command -v mamba &>/dev/null; then CONDA_CMD="mamba"
elif command -v conda &>/dev/null; then CONDA_CMD="conda"
else echo "ERROR: conda not found. Install Miniconda."; exit 1; fi

eval "$($CONDA_CMD shell.bash hook 2>/dev/null || true)"

# Create env if not exists (idempotent)
if ! conda env list | grep -q "^${ENV_NAME} "; then
    $CONDA_CMD create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
fi
conda activate "$ENV_NAME"

# Install deps
pip install -r requirements.txt
pip install pytest pytest-cov mutmut

echo "=== Environment Check ==="
echo "python: $(python --version) | pytest: $(pytest --version 2>&1 | head -1)"
echo "Environment ready. Run: conda activate ${ENV_NAME}"
```

Python 项目 + venv 示例：
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ ! -d ".venv" ] && python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Environment ready. Run: source .venv/bin/activate"
```

### 4. `RELEASE_NOTES.md`

跟踪所有用户可见变更的活文档。在**每次 git commit 后**更新，保证发布说明与代码同步。

```markdown
# Release Notes

## [Unreleased]

### Added
- User login with JWT authentication (#1)
- User registration with email validation (#2)

### Changed
- (none yet)

### Fixed
- (none yet)

---

## [0.1.0] — 2025-01-15
### Added
- Initial project scaffold
```

**规则**：
- 使用 [Keep a Changelog](https://keepachangelog.com/) 格式：Added、Changed、Deprecated、Removed、Fixed、Security
- 每条引用 `feature-list.json` 中的 feature ID
- 达到里程碑时将条目从 `[Unreleased]` 移到带版本号的章节
- 每次 git commit 后立即更新 — 绝不延后至会话末尾

### 5. `examples/` 目录

面向外部开发者与 AI Code Agent 的场景化使用示例。在系统测试 Go 判定后，通过 `long-task-finalize` Meta Skill 与 `example-generator` SubAgent 批量生成。

```
examples/
├── README.md                    # Index of all examples with descriptions
├── 01-user-login.py             # Feature #1: login flow demo
├── 02-user-registration.py      # Feature #2: registration demo
├── 05-password-reset.sh         # Feature #5: curl commands for password reset API
└── ui/
    └── 03-dashboard-tour.md     # Feature #3: step-by-step UI walkthrough
```

**规则**：
- 面向场景，而非面向 feature — 一个示例可跨多个 feature
- 示例**必须**可运行或可跟随 — 不是代码片段
- 命名模式：`<NN>-<scenario-name>.<ext>`（如 `01-quick-start.py`）
- `examples/README.md` 索引列出所有示例，附前置条件与运行命令
- 跳过不可外化的特性（基础设施、内部逻辑、配置脚手架）
- 完整生成规则见 `agents/example-generator.md`

### 6. Git 历史

- 每次会话以描述性消息 commit
- 便于回滚损坏变更
- 通过 `git log` 为后续会话提供上下文

### 7. `long-task-guide.md`

Worker 会话指南，**由 LLM 在 Initializer 阶段生成**，针对项目技术栈与特征裁剪。包含每个上下文循环的完整工作流。位于项目根目录。由 `validate_guide.py` 校验结构完备性。

## 需求阶段（Phase 0a）

在设计阶段**之前**运行。产出对齐 ISO/IEC/IEEE 29148 的结构化 SRS。

**硬关卡**：SRS 未批准前不做设计、特性分解、脚手架或编码。

1. **探索上下文** — 读需求文档、既有代码；检测 SRS 模板
2. **结构化采集** — 逐条澄清提问，按 8 项质量属性挑战每条需求（correct、unambiguous、complete、consistent、ranked、verifiable、modifiable、traceable）
3. **需求分类** — functional（FR-xxx）/ NFR（NFR-xxx）/ 约束（CON-xxx）/ 假设（ASM-xxx）/ 接口（IFR-xxx）/ 排除（EXC-xxx）
4. **撰写需求** — 应用 EARS 模板、分配唯一 ID、写 Given/When/Then 验收准则
5. **校验 SRS** — 反模式检测（weasel words、复合需求、设计泄露、不可测 NFR）、完整性交叉核对
6. **逐节审批** — 向用户呈现 SRS，按节获批
7. **保存 SRS 文档** — `docs/plans/YYYY-MM-DD-<topic>-srs.md`

## 设计阶段（Phase 0b）

SRS 批准**之后**、Initializer **之前**运行。以 SRS 为输入，聚焦于 HOW。

**硬关卡**：设计未批准前不做特性分解、脚手架或编码。

1. **读 SRS** — 提取设计驱动（NFR 阈值、约束、接口需求）
2. **探索技术上下文** — 既有代码、框架、部署环境
3. **提出 2-3 种方案** — 显式权衡，按 SRS 约束与 NFR 评估
4. **逐节获批** — 架构、数据模型、API、UI、测试、部署
5. **保存设计文档** — `docs/plans/YYYY-MM-DD-<topic>-design.md`（若提供则使用自定义模板）

## Initializer 会话工作流

Initializer 在 SRS 与设计都批准后**运行一次**。它读取**两份**已批准文档：
- **SRS**（`docs/plans/*-srs.md`） — 功能需求、NFR、约束、假设、词汇表、用户画像
- **Design**（`docs/plans/*-design.md`） — 技术栈、架构、测试策略

其职责：

1. **读取批准的 SRS + 设计文档** — 来自 `docs/plans/`
2. **运行 `init_project.py`** — 搭建确定性产物：`feature-list.json`、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`scripts/`、`docs/plans/`
3. **LLM 生成 `long-task-guide.md`** — 基于 SKILL.md + references + 设计文档的项目裁剪 Worker 指南；只包含项目所用语言的命令；由 `validate_guide.py` 校验
4. **LLM 生成 `init.sh`/`init.ps1`** — 基于设计文档技术栈的真实可运行 bootstrap 脚本；必须支持项目的环境管理器（conda/miniconda/mamba、venv、poetry、uv、nvm、fnm、sdkman、docker 等）；按工具模板见 `skills/long-task-init/references/init-script-recipes.md`；必须幂等、跨平台
5. **填充 `feature-list.json`** — 来自 SRS：`constraints[]`（CON-xxx）、`assumptions[]`（ASM-xxx）、NFR-xxx → 非功能 feature、FR-xxx → 带 `srs_trace`（需求 ID）与可选 `verification_steps` 的功能 feature；来自设计：外部依赖的 `required_configs`
7. **建立项目骨架** — 目录结构、配置文件、package.json / pyproject.toml 等（基于设计文档架构）
8. **初始 git commit** — 建立基线
9. **验证环境** — 运行 init 脚本、确认基本 setup 可用

### 产物生成：脚本 vs LLM

| Artifact | Generated by | Source Document | Rationale |
|----------|-------------|-----------------|-----------|
| `feature-list.json`（schema） | Script | — | 需要确定性结构供校验工具 |
| `task-progress.md` | Script | — | 通用格式模板 |
| `RELEASE_NOTES.md` | Script | — | 通用 Keep a Changelog 模板 |
| `examples/README.md` | Script | — | 通用格式模板 |
| `long-task-guide.md` | **LLM** | Design | 项目裁剪；仅含相关语言 / 工具；由 `validate_guide.py` 校验 |
| `init.sh` / `init.ps1` | **LLM** | Design | 完全项目专属；通用残根无用 |
| `features[]` 内容 | **LLM** | **SRS** | FR-xxx → 带 `srs_trace`（需求 ID）与可选 `verification_steps` 的 feature |
| `constraints[]` 内容 | **LLM** | **SRS** | 从 SRS "Constraints" 节（CON-xxx）提取 |
| `assumptions[]` 内容 | **LLM** | **SRS** | 从 SRS "Assumptions" 节（ASM-xxx）提取 |
| `required_configs[]` | **LLM** | **SRS** + Design | 接口需求（IFR-xxx）+ 设计集成点 |

## Worker 会话工作流（上下文循环）

每个 worker 循环严格按此顺序。

### Phase 1：Orient（理解当前状态）
1. `pwd` — 确认工作目录
2. 读取 `task-progress.md` — 理解此前发生
3. 读取 `feature-list.json` — 找到下一个优先级的 failing feature；记录根层的 `constraints[]` 与 `assumptions[]`
4. `git log --oneline -20` — 查看最近提交
5. `git diff HEAD~3` — 必要时检查最近变更
6. 读取设计文档 **Section 1**（Project Overview） — 全局上下文的架构快照

### Phase 2：Bootstrap（恢复环境）
6. 运行 `init.sh` / `init.ps1` — 启动开发服务器 / 服务
7. 跑冒烟测试 — 确认此前 passing 的特性仍正常

### Phase 2.5：Config Gate（验证必需配置）
7a. 从 `feature-list.json` 读 `required_configs`
7b. 过滤 `required_by` 含当前目标 feature ID 的配置
7c. `env` 类型：检查环境变量已设且非空
7d. `file` 类型：检查 `path` 处文件存在且非空
7e. 若任一缺失：以 name、description、check_hint 报告；通过 `AskUserQuestion` 询问用户；用户应答后复检
7f. 全部 required config 通过才进入 Phase 3
7g. 快捷方式：`python scripts/check_configs.py feature-list.json --feature <id>`

### Phase 3：TDD Red — 先写失败测试
8. 选取依赖全部 `"passing"` 的最高优先级 `"failing"` 特性
9. 写覆盖 Feature Design Test Inventory（§7）的单元测试 — 测试**必须**失败（尚无实现）
   - 遵循测试场景规则（见 [test-scenario-rules.md](test-scenario-rules.md)）：
     - 含 happy path、错误处理、边界、安全场景
     - 确保负向占比 >= 40%
     - 确保低价值断言占比 <= 20%
     - 对每条测试应用 "wrong implementation" 挑战
10. 若特性含 UI：写 Chrome DevTools MCP 功能测试（snapshot、click、fill、screenshot 断言） — 测试**必须**失败
    - 在 `[devtools]` 验证步骤中使用 EXPECT/REJECT 格式
    - 通过 `evaluate_script()` 调用自动化 UI 错误检测脚本
    - 通过 `list_console_messages(types=["error"])` 调用 console error gate
    - 完整规范见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)

### Phase 4：TDD Green — 实现以通过测试
11. 写最小代码使**全部**测试通过（单元 + 功能）
12. 跑完整测试套件 — 确认新测试全绿、无回归

### Phase 4.5：Coverage Gate — 验证测试覆盖率
12a. 跑项目语言的覆盖率工具（见 [../../long-task-quality/coverage-recipes.md](../../long-task-quality/coverage-recipes.md)）
12b. 检查：行覆盖率 >= `quality_gates.line_coverage_min`（默认 90%），分支覆盖率 >= `quality_gates.branch_coverage_min`（默认 80%）
12c. 若低于阈值：写更多测试（回到 Phase 3 补用例）
12d. 将覆盖率报告输出作为证据记录

### Phase 5：TDD Refactor — 清理
13. 在保持测试全绿的前提下重构
14. 再次校验 — **仅当**全部测试通过后才在 `feature-list.json` 中标记为 `"passing"`
15. **验证强制**：执行每条 `verification_step`，读取**完整**输出，确认全绿。若你发现自己在想 "should pass" 或 "probably works" — 停下重跑。见 [verification-enforcement.md](verification-enforcement.md)。

### Phase 5.5：内联合规检查
16. 运行机械式合规检查（接口契约校验、测试清单交叉核对、依赖版本抽查、UI 特性的 UCD token grep）
17. 就地修复发现 — 不分发 SubAgent

### Phase 6：Persist（为下次会话保存状态）
15. `git add` + `git commit`，附描述性消息
16. 更新 `RELEASE_NOTES.md` — 在 `[Unreleased]` 下加入特性标题、ID、变更类型
17. 向 `task-progress.md` 追加会话条目
18. 校验：`python scripts/validate_features.py feature-list.json`
19. 提交更新后的 `task-progress.md`、`feature-list.json` 与 `RELEASE_NOTES.md`

### Phase 7：Continue
20. 若全部特性为 `"passing"` → 宣布项目完成并停止
21. 否则，告诉用户哪个特性已完成、下一个是哪个
22. 若剩余上下文预算足够，进入下一特性的 Phase 1
23. 若上下文耗尽，结束会话

**关键规则**：每循环一个特性。若一特性完成后上下文仍有富余，取下一个。绝不留下损坏代码。

## 上下文连续性流程

```
Requirements → SRS approved → Design → design approved → Initializer → scaffold → populate features → commit → begin first Worker cycle
                                                                                                                        ↓
                                                                                                                ┌─── Worker Cycle ───┐
                                                                                                                │ Orient             │
                                                                                                                │ Bootstrap          │
                                                                                                                │ Implement (1 feat) │
                                                                                                                │ Persist + commit   │
                                                                                                                │ Continue / End     │
                                                                                                                └────────┬───────────┘
                                                                                                                         │
                                                                                                                (repeat until all passing)
```

## 应当避免的反模式

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| 多特性并行尝试 | 实现中途上下文耗尽、连锁失败 | 每循环一个特性 |
| 未测试即宣布胜利 | 看似完成但实际损坏 | 通过实际测试验证每个特性 |
| 先写代码后写测试（跳过 TDD Red） | 测试变为验证实现而非行为；漏掉边界 | 始终先写失败测试，再实现 |
| UI 跳过 Chrome DevTools 功能测试 | UI 可渲染但对用户不工作 | 每个 UI 特性（ui=true）都需 `[devtools]` 验证步骤；规划前跑 DevTools Gate |
| 不更新 RELEASE_NOTES.md | 发布说明与实际状态漂移；后期补救成本高 | 每次 git commit 后更新 |
| 面向用户特性跳过示例 | 用户看不懂如何使用新特性；降低项目价值 | 为每个面向用户的特性添加可运行示例 |
| 删除 srs_trace 条目 | 破坏 ATS 类别可追溯性 | srs_trace 将 feature 映射到 SRS 需求 — 保持完整 |
| 跳过覆盖率检查 | 测试可能漏掉整段代码路径 | 每次 TDD Green 后跑覆盖率 |
| 以无断言测试刷覆盖率 | 覆盖率高但测试无用 | 强化断言；禁止仅存在性 / 真值性检查 |
| 跳过进度文件更新 | 下次会话浪费 token 重新发现状态 | 会话结束前始终更新 |
| 会话结束不 commit | 工作可能丢失、下次会话无法 diff | 始终提交可工作的代码 |
| 用 markdown 做 feature list | 模型倾向于破坏 / 重排 markdown 列表 | 用 JSON 做结构化数据 |
| 把本该真实的配置 mock 了 | 测试通过但接真实服务时失败 | 在 `required_configs` 中声明，规划前关卡 |
| 特性工作前跳过配置检查 | 配置缺失时浪费规划 / TDD 循环 | 对有外部依赖的特性始终跑 Config Gate |
| 跳过需求阶段 | 不完整 / 模糊需求导致返工 | 跑需求采集，先产出批准的 SRS |
| 跳过设计阶段 | 临时设计导致不一致与返工 | SRS 之后跑设计阶段，先获批 |
| 猜测式调试 | 随机修复浪费时间且可能引入新 bug | 遵循系统性调试 — 追根因。见 [systematic-debugging.md](../../long-task-work/references/systematic-debugging.md) |
| 无证据声称 "it works" | 未经校验的声明导致虚假信心 | 标记 passing 前展示实际测试输出。见 [verification-enforcement.md](verification-enforcement.md) |
| 接受低价值断言 | 仅做 None/isinstance/import 的测试零捕 bug 能力 | 强制低价值断言占比 <= 20%。见 [testing-anti-patterns.md](../../long-task-tdd/testing-anti-patterns.md) #14 |
| UI 测试缺 REJECT 子句 | LLM 只确认正向期望，漏掉显而易见的 UI 错误 | 所有 `[devtools]` 步骤要求 EXPECT/REJECT 格式。见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md) |

## 验证策略

### 所有特性通用（TDD 强制）：
1. **Red**：先写失败测试 — 测试定义期望行为
   - 遵循测试场景规则：类别覆盖、负向占比 >= 40%、低价值断言 <= 20%
2. **Green**：写最小实现通过测试
3. **Refactor**：保持测试绿的前提下清理
4. **Quality gates**：Coverage gate（line ≥90%, branch ≥80%）客观校验测试质量

### API / 后端特性：
- 业务逻辑的单元测试（pytest、jest 等）
- 集成测试：发真实 HTTP 请求并检查响应
- 必要时验证数据库状态

### UI / 前端特性（强制 Chrome DevTools MCP）：
- 组件逻辑的单元测试
- **通过 Chrome DevTools MCP 的功能测试**（三层错误检测）：
  - **Layer 1**：通过 `evaluate_script()` 的自动化错误检测脚本 — 发现错误硬 FAIL
  - **Layer 2**：验证步骤的 EXPECT/REJECT 格式 — 强制找错
  - **Layer 3**：`list_console_messages(types=["error"])` 的 console error 关卡 — 有错硬 FAIL
  - 完整规范见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)
- 测试流：navigate → wait → error detection → snapshot → EXPECT/REJECT → interact → error detection → snapshot → console check

### 所有特性通用（Coverage 强制）：
- **Coverage**：运行各语言覆盖率工具，确认行 / 分支阈值
- 每语言工具 setup 与命令见 [../../long-task-quality/coverage-recipes.md](../../long-task-quality/coverage-recipes.md)

### 数据 / 流水线特性：
- 用样本数据运行并校验输出
- 显式检查边界
- 将输出与期望对比

## TDD 工作流细节

```
┌─── Config Gate ──────────┐
│ 0a. Read required_configs │
│ 0b. Check env/file        │
│ 0c. If missing → prompt   │
│     user, block           │
└──────────┬───────────────┘
           ↓
┌─── DevTools Gate ────────┐
│ 0d. If ui=true:           │
│     check_devtools.py     │
│ 0e. If not detected →     │
│     prompt user, block    │
└──────────┬───────────────┘
           ↓
┌─── TDD Red ─────────────┐
│ 1. Read feature spec     │
│ 2. Write unit tests      │
│    (scenario rules:      │
│     40% negative,        │
│     ≤20% low-value)      │
│ 3. Write [devtools]      │
│    tests (if ui=true)    │
│    (EXPECT/REJECT +      │
│     error detection)     │
│ 4. Run tests → ALL FAIL  │
└──────────┬───────────────┘
           ↓
┌─── TDD Green ───────────┐
│ 5. Write minimal code    │
│ 6. Run tests → ALL PASS  │
└──────────┬───────────────┘
           ↓
┌─── Coverage Gate ────────┐
│ 7. Run coverage tool     │
│ 8. Line % >= threshold?  │
│    Branch % >= threshold │
│ 9. If below → more tests │
└──────────┬───────────────┘
           ↓
┌─── TDD Refactor ────────┐
│ 10. Clean up code        │
│ 11. Run tests → STILL    │
│     ALL PASS             │
└──────────┬───────────────┘
           ↓
┌─── Verify & Mark ────────┐
│ 12. All evidence recorded │
│ 13. Mark "passing"        │
└───────────────────────────┘
```

### Chrome DevTools MCP 功能测试模式

**适用于**：`feature-list.json` 中 `"ui": true` 的特性。

**DevTools Gate**：规划 UI 特性前，跑 `check_devtools.py` 确认 MCP 可用：
```
python scripts/check_devtools.py feature-list.json --feature <id>
```

**`[devtools]` 验证步骤格式**：UI 特性可选在 `verification_steps` 中加入以 `[devtools]` 开头的条目，使用 **EXPECT/REJECT 格式**（ST 测试用例通过 `srs_trace` 从 SRS 验收准则派生 UI 场景）：
- `[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>`
- **EXPECT**：必须存在的元素、文本或状态
- **REJECT**：不得存在的条件（强制找错行为）
- 两个子句都必需 — 详见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)
- 示例：`"[devtools] /login | EXPECT: email input, password input, submit button | REJECT: placeholder 'TODO', overlapping elements, console errors"`

每个 `[devtools]` 步骤的**测试序列**：
```
1. Navigate to relevant page:      navigate_page(url)  (use ui_entry if set)
2. Wait for page load:             wait_for(expected_text)
3. Run automated error detection:  evaluate_script(ui_error_detector)  ← HARD FAIL if count > 0
4. Capture initial state:          take_snapshot()
5. Verify EXPECT criteria:         check uid/text presence in snapshot
6. Verify REJECT criteria:         confirm REJECT conditions are NOT present
7. Perform user action:            click(uid) / fill(uid, value)
8. Wait for response:              wait_for(text)
9. Run error detection again:      evaluate_script(ui_error_detector)  ← HARD FAIL if count > 0
10. Capture result state:          take_snapshot() / take_screenshot()
11. Assert expected outcome:       verify EXPECT elements, text, or visual state
12. Check for console errors:      list_console_messages(types=["error"])  ← HARD FAIL if count > 0
```

自动化检测脚本与三层检测模型见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)。

## 多语言工具快速参考

各语言覆盖率命令。完整 setup 配方见 [../../long-task-quality/coverage-recipes.md](../../long-task-quality/coverage-recipes.md)。

| Language | Coverage Command |
|----------|-----------------|
| Python | `pytest --cov=src --cov-branch --cov-report=term-missing` |
| Java | `mvn test jacoco:report` |
| TypeScript | `npx c8 --branches --reporter=text npm test` |
| C/C++ | `gcov -b src/*.c && lcov --capture -d . -o cov.info` |

## Release Notes 维护

### 何时更新 `RELEASE_NOTES.md`：
- **每次**改变功能的 git commit 之后
- 会话结束前（作为 Persist 阶段的一部分）

### 格式（Keep a Changelog）：
```markdown
## [Unreleased]

### Added
- Feature description (feature #ID)

### Changed
- What changed and why (feature #ID)

### Fixed
- Bug description (feature #ID)
```

### 类别：
- **Added**：新特性
- **Changed**：既有功能的变更
- **Deprecated**：即将移除的特性
- **Removed**：已移除的特性
- **Fixed**：bug 修复
- **Security**：漏洞修复

## 示例生成

### 目的
示例为**外部开发者与 AI Code Agent**提供使用文档 — 展示如何与项目集成及如何使用。ST 后由 `long-task-finalize` Meta Skill 经 `example-generator` SubAgent 生成（见 `agents/example-generator.md`）。

### 设计原则
- **面向场景，而非面向特性** — 一个示例可跨多个特性；按使用场景分组
- **精炼集合** — 质优于量；多数项目 3-8 个示例
- **跳过不可外化特性** — 基础设施、内部逻辑、配置脚手架无外部示例
- **可运行或可跟随** — 代码示例必须可执行；UI 示例必须是逐步走查

### 按项目规模的目标示例数

| Project Size | Features | Target Examples |
|---|---|---|
| Tiny (1-5) | 1-5 | 1-2 |
| Small (5-15) | 5-15 | 2-4 |
| Medium (15-50) | 15-50 | 4-6 |
| Large (50+) | 50+ | 6-8 |

### 按场景的示例类型

| Scenario Type | Format | Content |
|---|---|---|
| **API usage** | `.py` / `.sh` / `.js` script | 初始化 client、用样例数据调用 endpoint、打印响应 |
| **Library usage** | `.py` / `.js` / `.ts` code | 导入模块、以样例数据演示关键函数 |
| **CLI usage** | `.sh` / `.ps1` script | 运行命令，预期输出写在注释中 |
| **UI workflow** | `.md` walkthrough | 含动作描述的逐步说明 |
| **Integration** | `.py` / `.js` script | 跨多子系统的端到端工作流 |

### 示例文件结构
```
examples/
├── README.md                           # Index: scenario descriptions + how to run
├── 01-quick-start.py                   # Basic usage workflow
├── 02-data-import.sh                   # Data import pipeline
├── 03-advanced-config.py               # Advanced configuration scenarios
└── data/                               # Shared sample data for examples
    └── sample-input.json
```

### `examples/README.md` 格式
```markdown
# Examples

Usage examples for external developers and AI Code Agents.

## Prerequisites

[List prerequisites: language runtime, dependencies, config setup]

## Examples

| # | Scenario | File | How to run |
|---|----------|------|------------|
| 1 | Quick start | [01-quick-start.py](01-quick-start.py) | `python examples/01-quick-start.py` |
| 2 | Data import | [02-data-import.sh](02-data-import.sh) | `bash examples/02-data-import.sh` |
```

### 示例质量清单
- [ ] 示例可运行（或 UI 走查可跟随）
- [ ] 含简短注释说明演示内容
- [ ] 使用真实但安全的样例数据 — 不用占位 "foo/bar"
- [ ] `examples/README.md` 索引已更新
- [ ] 示例命名遵循模式：`<NN>-<scenario-name>.<ext>`
- [ ] 无密钥 — 使用明显占位符（`YOUR_API_KEY`）
