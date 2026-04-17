---
name: glossary-template
description: Long-task agent 全局术语表（中英对照）
purpose: 保证所有 skill/agent/template/references 文档翻译时术语一致
audience: 所有翻译者、文档作者、reviewer
last_reviewed: 2026-04-17
---

# 术语表（Glossary）

> 本表是 Long-Task Agent 文档中文化的**单一事实源**。翻译时严格按本表统一术语，避免漂移。
>
> 规则：
> 1. **原样保留**（不翻译）：YAML frontmatter 字段名、JSON 字段名、命令示例、工具名、代码块、commit message 示例、文件路径、SRS/FR/ATS/UCD 等已成标识符的缩写。
> 2. **术语统一**（按本表译法）：当英文术语在正文中以自然语言形式出现时，采用本表的中文译法。
> 3. **数字与符号**：保留 ASCII 原样；章节编号保持原样（§1, §6.2, FR-001 等）。

---

## §1 流程与角色

| 英文 | 译法 | 说明 |
|---|---|---|
| Worker | Worker | 专有名词，不译（承担 TDD → Quality → Feature-ST 流水线的主 agent） |
| SubAgent | SubAgent | 不译（运行时嵌套加载 skill 的执行单元） |
| Orchestrator | 主 agent / 调度器 | 语境决定；Worker SKILL 作为 orchestrator 时译"主 agent" |
| Reviewer | 评审 / 评审者 | 人工或独立 subagent 的角色 |
| Phase | 阶段 | 如 "Phase 0a: Requirements" → "阶段 0a：需求" |
| Pipeline | 流水线 | 下游消费侧统称 |
| Gate / Gating | 关卡 / 关卡校验 | 如 "Config Gate" → "配置关卡"；"Coverage Gate" → "覆盖率关卡" |
| Re-entry point | 再入口 | Hotfix / Increment 属于再入口 |
| Router | 路由 | `using-long-task` 的职能 |
| Bootstrap | 引导 | session 启动阶段 |

## §2 工件与文档

| 英文 | 译法 | 说明 |
|---|---|---|
| SRS (Software Requirements Specification) | SRS | 缩写不译；首次出现可注"软件需求规约" |
| FR (Functional Requirement) | FR | 缩写不译；首次出现可注"功能需求" |
| NFR (Non-Functional Requirement) | NFR | 同上，"非功能需求" |
| Design doc | 设计文档 / Design | 首次出现用"设计文档" |
| ATS (Acceptance Test Strategy) | ATS | 缩写不译；首次注"验收测试策略" |
| UCD (UI Compliance Document) | UCD | 缩写不译；首次注"UI 合规文档" |
| ST (System Testing) | 系统测试 / ST | 首次出现用"系统测试（ST）" |
| Feature | 特性 | feature-list.json 中的一条 feature |
| Feature list | 特性清单 | 指代 `feature-list.json` 内容 |
| Feature-ST | Feature-ST | 专有流水线步骤名，不译 |
| Wave | 批次 | increment 引入的批次元数据 |
| Request file | 请求文件 | `bugfix-request.json` / `increment-request.json` |
| Artifact | 产物 / 工件 | 落盘文档 |
| Template | 模板 | `docs/templates/*.md` |
| Guide | 指南 | long-task-guide.md / env-guide.md |
| Backlog | 待办清单 | deferred backlog |
| Retrospective | 回顾 / Retrospective | 语境决定 |

## §3 开发实践

| 英文 | 译法 | 说明 |
|---|---|---|
| TDD (Test-Driven Development) | TDD | 缩写不译；首次注"测试驱动开发" |
| Red / Green / Refactor | 红 / 绿 / 重构 | TDD 三阶段；首次可注英文 |
| Unit Test (UT) | 单元测试 / UT | 首次注英文 |
| Integration Test | 集成测试 | |
| E2E (End-to-End) | 端到端 / E2E | 首次注英文 |
| Acceptance Test | 验收测试 | |
| Coverage | 覆盖率 | |
| Line coverage / Branch coverage | 行覆盖率 / 分支覆盖率 | |
| Static analysis | 静态分析 | |
| Build | 构建 | |
| Quiet execution | 静默执行 | 主题 7 引入的术语 |
| Re-check protocol | Re-check 协议 | 失败后只重跑失败项 |
| Dispatch | 分发 | DISPATCH 声明式语法 |
| Structured Return Contract | Structured Return Contract | 专有名词，不译 |
| Resume / Resume Check | 恢复 / 恢复检查 | Worker Step 1 |

## §4 代码与架构

| 英文 | 译法 | 说明 |
|---|---|---|
| Brownfield / Greenfield | 存量项目 / 全新项目 | 首次注英文 |
| Existing System Inventory (ESI) | 存量系统清单（ESI） | brownfield-adaptation.md 术语 |
| Mandatory internal library | 强制内部库 | §13.1 约束 |
| Prohibited API | 禁用 API | §13.2 约束 |
| Codebase constraints | 存量代码库约束 | Design §13 / env-guide §4 |
| Existing code reuse | 存量代码复用 | Feature Design Step 1c |
| Internal API contract | 内部 API 契约 | Design §6.2 |
| Project structure | 项目结构 | Design §0 |
| Interface contract | 接口契约 | Feature Design 下游消费 |
| Test inventory | 测试清单 | Feature Design → TDD Red 消费 |
| Implementation Summary | 实现摘要 | Feature Design 替代 pseudocode/diagrams |
| Boundary conditions | 边界条件 | |
| Backward compatibility | 向后兼容 | |
| Breaking change | 破坏性变更 | |
| Deprecation | 弃用 | |
| Impact assessment | 影响评估 | Increment §3.7 |

## §5 状态与元数据

| 英文 | 译法 | 说明 |
|---|---|---|
| Passing / Failing | 通过 / 未通过 | feature status |
| Active / Deprecated | 激活 / 弃用 | feature 生命周期 |
| Blocked | 阻塞 | Structured Return Contract status |
| Pending | 待处理 | |
| Approved / Unapproved | 已审批 / 未审批 | env-guide.md approval |
| Required / Optional | 必填 / 可选 | |
| Signal file | 信号文件 | bugfix-request.json / increment-request.json |

## §6 UI / 测试环境

| 英文 | 译法 | 说明 |
|---|---|---|
| Chrome DevTools MCP | Chrome DevTools MCP | 专有名词，不译 |
| Visual Rendering Contract | 视觉渲染契约 | UI feature 必需 |
| Exploratory Visual Assessment | 探索性视觉评估 | Feature-ST 四维度 |
| Rendering Completeness | 渲染完备性 | 评估维度 1 |
| Interactive Depth | 交互深度 | 评估维度 2 |
| Visual Coherence | 视觉一致性 | 评估维度 3 |
| Functional Accuracy | 功能准确性 | 评估维度 4 |
| Service lifecycle | 服务生命周期 | env-guide.md §1 |
| Startup output | 启动输出 | |
| Restart protocol | 重启协议 | 4 步协议 |

## §7 上下文与 Token

| 英文 | 译法 | 说明 |
|---|---|---|
| Context budget | 上下文预算 | sizing 公式 |
| Context window | 上下文窗口 | |
| Token | token | 小写原样 |
| Context pollution | 上下文污染 | Quiet execution 降低目标 |
| On-demand extraction | 按需提取 | Quiet execution 的失败路径 |

## §8 审批与合规

| 英文 | 译法 | 说明 |
|---|---|---|
| Approval gate | 审批关卡 | env-guide.md Step 0 |
| Frontmatter | frontmatter | 不译（YAML 术语） |
| Compliance | 合规 | |
| Traceability | 可追溯性 | srs_trace 职能 |

## §9 常见短语对照

| 英文 | 译法 |
|---|---|
| "Load on-demand via the Skill tool" | "通过 Skill 工具按需加载" |
| "Blocking requirement" | "阻塞性要求" |
| "Non-blocking" | "非阻塞" |
| "Must / Shall" | "必须" |
| "Should" | "应当" |
| "May" | "可以" |
| "Fail fast" | "快速失败" |
| "Single source of truth" | "单一事实源" |
| "Out of scope" | "不在本次范围" |
| "Downstream consumer" | "下游消费方" |
| "Upstream" | "上游" |

---

## 附录 A：不翻译清单（原样保留）

以下内容在文档中一律保留英文原样：

1. YAML frontmatter：`name:` / `description:` 字段值（短英文便于 skill 路由匹配）
2. JSON 字段名：`srs_trace`, `feature_id`, `quality_gates.line_coverage_min`, `tech_stack.language` 等
3. 文件路径：`docs/plans/*-srs.md`、`feature-list.json` 等
4. 命令示例：`python scripts/validate_features.py`、`mvn test` 等
5. 工具名：`Skill`、`Agent`、`Grep`、`Glob`、`Read`、`Edit`、`Write`、`Bash`、`TaskCreate`
6. 架构标识符：`Red → Green → Refactor`、`Step 1a`、`§13.1`、`FR-001`
7. 缩写（首次出现可加中文注释，后续保留缩写）：`SRS`、`FR`、`NFR`、`ATS`、`UCD`、`ST`、`TDD`、`UT`、`E2E`、`ESI`
8. Commit message 示例（保留英文便于自动化）
9. 代码块内全部内容

## 附录 B：可能歧义的取舍

| 场景 | 决定 |
|---|---|
| "skill" vs "Skill" | 代词用"skill"，专名引用用 `Skill`（工具名） |
| "feature" 在概要句子里 | 一律译"特性" |
| "feature-list.json" 提及 | 保留文件名原样 |
| "gate" 单独出现 | "关卡" |
| "gating check" | "关卡校验" |
| "Worker cycle" | "Worker 循环" |
| "session" | "会话" |
| "retry" | "重试" |
| "artifact" vs "output" | "产物"（artifact）/ "输出"（output） |

---

**术语表完成**。翻译前请先阅读 §9（常用短语）与附录 A（不翻译清单）。遇到本表未覆盖的术语 → 在 PR 描述里列出并同步更新本表。
