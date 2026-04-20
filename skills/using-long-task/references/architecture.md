# Long-Task Agent 架构

## 核心概念

长期任务超出单次上下文窗口。解决方案：将工作拆分为**需求阶段**（SRS）、**设计阶段**、**初始化会话**（运行一次）和多个 **Worker 会话**（迭代运行），通过磁盘上的持久化产物连接。

## 持久化产物

### 1. `task-progress.md`

桥接上下文断层的会话日志。每个 Worker 会话追加一条记录。

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

结构化任务清单。JSON 格式防止模型意外损坏。同时携带 SRS 衍生的项目级上下文（`constraints`、`assumptions`），使 Worker 在每次 Orient 阶段都能读取。

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
- 状态仅有 `"failing"` 或 `"passing"` — 不允许 `"partial"` 或 `"in-progress"`
- `srs_trace` 为每个功能必填 — 映射到 SRS 需求 ID 以实现可追溯性
- `verification_steps` 可选 — 存在时提供补充测试上下文
- 标记为 `"passing"` 的功能必须在会话开始时重新验证

### 3. `RELEASE_NOTES.md`

持续更新的文档，跟踪所有用户可见的变更。每个功能完成后**立即更新**以确保发布说明与代码同步。

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
- 每条记录引用 `feature-list.json` 中的功能 ID
- 发布切点时将条目从 `[Unreleased]` 移至版本化章节
- 每个功能完成后立即更新 — 绝不延迟到会话结束

### 4. `examples/` 目录

可选目录，用于基于场景的使用示例。在 Init 阶段创建；项目成熟后可手动添加示例。

**规则**：
- 面向场景而非面向功能 — 一个示例可跨越多个功能
- 示例必须可运行或可跟随 — 不仅仅是代码片段
- 命名模式：`<NN>-<scenario-name>.<ext>`（如 `01-quick-start.py`）
- `examples/README.md` 索引列出所有示例及前置条件和运行命令
- 跳过非外部化功能（基础设施、内部逻辑、配置脚手架）

### 5. Git 历史

- 每个会话使用描述性消息提交
- 支持回退有问题的变更
- 通过 `git log` 为后续会话提供上下文

### 6. `long-task-guide.md`

**由 LLM 生成的** Worker 会话指南，在初始化阶段根据项目技术栈和特征定制。包含每个上下文周期的完整工作流。位于项目根目录。由 `validate_guide.py` 验证结构完整性。

## 需求阶段（Phase 0a）

在设计阶段**之前**运行。产出符合 ISO/IEC/IEEE 29148 的结构化 SRS。

**硬性门禁**：SRS 批准前不可进行设计、功能分解、脚手架搭建或编码。

1. **探索上下文** — 阅读需求文档、现有代码；检测 SRS 模板
2. **结构化获取** — 逐个提出澄清问题，对每个需求检验 8 项质量属性（正确、无歧义、完整、一致、有优先级、可验证、可修改、可追溯）
3. **分类需求** — 功能（FR-xxx）/ 约束（CON-xxx）/ 假设（ASM-xxx）/ 接口（IFR-xxx）/ 排除（EXC-xxx）
4. **编写需求** — 应用 EARS 模板，分配唯一 ID，编写 Given/When/Then 验收标准
5. **验证 SRS** — 反模式检测（模糊词、复合需求、设计泄漏），完整性交叉检查
6. **逐章节批准** — 向用户呈现 SRS，逐章节获取批准
7. **保存 SRS 文档** — `docs/plans/YYYY-MM-DD-<topic>-srs.md`

## 设计阶段（Phase 0b）

在 SRS 批准**之后**、初始化**之前**运行。以 SRS 为输入，聚焦于 HOW。

**硬性门禁**：设计批准前不可进行功能分解、脚手架搭建或编码。

1. **阅读 SRS** — 提取设计驱动因素（约束、接口需求）
2. **探索技术上下文** — 现有代码、框架、运行环境
3. **提出 2-3 种方案** — 含明确权衡，对照 SRS 约束评估
4. **逐章节批准** — 架构、数据模型、API、UI、测试
5. **保存设计文档** — `docs/plans/YYYY-MM-DD-<topic>-design.md`（如有自定义模板则使用）

## 初始化会话工作流

初始化在 SRS 和设计均批准后运行**一次**。从**两份**已批准文档读取：
- **SRS**（`docs/plans/*-srs.md`）— 功能需求、约束、假设、术语表、用户画像
- **设计**（`docs/plans/*-design.md`）— 技术栈、架构、测试策略

其职责：

1. **读取已批准的 SRS + 设计文档** — 从 `docs/plans/`
2. **运行 `init_project.py`** — 搭建确定性产物：`feature-list.json`、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`scripts/`、`docs/plans/`
3. **LLM 生成 `long-task-guide.md`** — 基于 SKILL.md + references + 设计文档定制的项目 Worker 指南；仅包含项目语言特定命令；由 `validate_guide.py` 验证
4. **填充 `feature-list.json`** — 从 SRS：`constraints[]`（CON-xxx）、`assumptions[]`（ASM-xxx）、FR-xxx → 带 `srs_trace`（需求 ID）和可选 `verification_steps` 的功能特性
5. **搭建项目骨架** — 目录结构、配置文件、package.json / pyproject.toml 等（基于设计文档架构）

### 产物生成：脚本 vs LLM

| 产物 | 生成方 | 源文档 | 理由 |
|------|--------|-------|------|
| `feature-list.json`（schema） | 脚本 | — | 验证工具需要确定性结构 |
| `task-progress.md` | 脚本 | — | 通用格式模板 |
| `RELEASE_NOTES.md` | 脚本 | — | 通用 Keep a Changelog 模板 |
| `examples/README.md` | 脚本 | — | 通用格式模板 |
| `long-task-guide.md` | **LLM** | 设计 | 项目定制；仅包含相关语言/工具；由 `validate_guide.py` 验证 |
| `features[]` 内容 | **LLM** | **SRS** | FR-xxx → 带 `srs_trace`（需求 ID）和可选 `verification_steps` 的功能 |
| `constraints[]` 内容 | **LLM** | **SRS** | 从 SRS "Constraints" 章节提取（CON-xxx） |
| `assumptions[]` 内容 | **LLM** | **SRS** | 从 SRS "Assumptions" 章节提取（ASM-xxx） |

## Worker 会话工作流

> 拆分为两个阶段 skill，每个一会话，各自 end-session：
> - **`skills/long-task-work-design/SKILL.md`**：Orient → Feature Design SubAgent → 翻 `current.phase: design→tdd` → commit → 终止
> - **`skills/long-task-work-tdd/SKILL.md`**：Orient → TDD Red/Green/Refactor SubAgents → `current=null` + `status=passing` → commit → 终止
>
> 跨会话衔接由 `feature-list.json.current` 锁 + `scripts/phase_route.py` 完成。每特性 2 次会话（design + tdd）；外部 `scripts/auto_loop.py` 处理自动多迭代。多版 TDD：在 worktree 里手工 reset `current.phase=tdd` 重跑（见 `worktree-isolation.md`）。

## 应避免的反模式

| 反模式 | 失败原因 | 正确做法 |
|--------|---------|---------|
| 尝试并行多个功能 | 上下文耗尽，级联失败 | 每周期一个功能 |
| 用 markdown 做功能列表 | 模型倾向于损坏/重新格式化 markdown | 对结构化数据使用 JSON |
| 跳过需求阶段 | 不完整的需求导致返工 | 先运行需求获取，产出已批准的 SRS |
| 跳过设计阶段 | 临时设计导致不一致 | SRS 后运行设计阶段，先获取批准 |
| 跳过进度文件更新 | 下个会话浪费 token 重新发现状态 | 结束会话前务必更新 |
| 猜测式修复调试 | 随机修复浪费时间，可能引入新 bug | 遵循系统化调试 — 追踪根因 |
