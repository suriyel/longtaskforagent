# Structured Return Contract（统一契约）

> 所有 Worker 内部步骤分发的 SubAgent 必须遵循本契约。主 Agent **只消费契约字段**，不消费 SubAgent 内部 thinking / 详细输出。这是 SubAgent-per-Step 架构的核心 — 让主 Agent 的上下文窗口只保留跨步骤必要的最小状态。

## 为什么存在

Worker 一次 feature cycle 涉及 feature-design → tdd → quality → feature-st 四个独立步骤。若每步的 SubAgent 结果全文灌入主 Agent 上下文，单 feature 就会吃掉数万 token，限制长任务的总规模。本契约定义每步必须返回的**最小字段集**，让主 Agent 只保留跨步骤必需的信息（如 coverage 百分比、artifacts 路径），discard SubAgent 的中间过程。

## 强制字段（所有 SubAgent 必须返回）

每个 SubAgent 返回的文本块必须以下列 5 个顶层字段开始（顺序固定）：

```markdown
## SubAgent Result: <skill-name>

**status**: pass | fail | blocked
**artifacts_written**: [file path 列表，相对项目根]
**next_step_input**: { JSON-like 下一步最小字段集 }
**blockers**: [若 status=blocked 则列出；其他状态留空数组]
**evidence**: [关键断言的最小证据，如测试名 + 结果、覆盖率百分比、契约 ID]
```

## 字段语义

| 字段 | 类型 | 语义 | 主 Agent 用途 |
|---|---|---|---|
| `status` | enum | `pass` / `fail` / `blocked` | 分支决策：下一步 or 升级用户 |
| `artifacts_written` | str[] | 本步产出或修改的持久化文件（`docs/features/*.md`、测试文件、test-cases/*.md 等） | 合并到 git commit；task-progress.md 记录 |
| `next_step_input` | JSON-like object | 下一步 SubAgent 需要的**最小**字段（如 `coverage_line: 94, coverage_branch: 88`） | 构造下一个 SubAgent prompt |
| `blockers` | str[] | 仅在 `blocked` 时填写；每条一句话描述阻塞原因 + 用户需提供的信息 | 组装 `AskUserQuestion` 的输入 |
| `evidence` | str[] | 断言为 pass 的最小证据（例："pytest test_login::test_valid_creds PASSED"；"line coverage 94% ≥ 90%"） | task-progress.md 归档 |

## 示例

### Feature Design SubAgent — pass
```markdown
## SubAgent Result: long-task-feature-design

**status**: pass
**artifacts_written**: ["docs/features/3-login-api.md"]
**next_step_input**: {
  "design_doc": "docs/features/3-login-api.md",
  "test_inventory_rows": 12,
  "interface_contracts": ["POST /api/login", "GET /api/session"],
  "srs_trace": ["FR-003"]
}
**blockers**: []
**evidence**: [
  "Test Inventory: 12 rows covering FUNC/happy, FUNC/error, BNDRY, SEC",
  "Interface Contract: 2 public methods matched to FR-003 acceptance criteria",
  "Internal API Contract §4 cross-checked — this feature is Provider for Contract C-001"
]
```

### TDD SubAgent — fail
```markdown
## SubAgent Result: long-task-tdd

**status**: fail
**artifacts_written**: ["tests/test_login.py", "src/auth/login.py"]
**next_step_input**: {}
**blockers**: []
**evidence**: [
  "pytest — 11 passed, 1 failed",
  "Failed: tests/test_login.py::test_rate_limit — expected 429, got 200"
]
```
主 Agent 看到 `fail`，决定：读 `evidence` 第二行 → 将失败原因传回 tdd SubAgent 请求修复（不整轮重跑）。

### Quality SubAgent — blocked
```markdown
## SubAgent Result: long-task-quality

**status**: blocked
**artifacts_written**: []
**next_step_input**: {}
**blockers**: [
  "coverage tool `pytest-cov` not installed; init.sh did not include it; user must add to pyproject.toml and re-run init"
]
**evidence**: ["pytest --cov exited with 'ModuleNotFoundError: pytest_cov'"]
```
主 Agent 看到 `blocked` + `blockers[0]` → 通过 `AskUserQuestion` 转给用户。

## 主 Agent 消费规则（关键）

1. **读 `status` 做分支决策**；
2. **读 `next_step_input` 构造下一个 SubAgent prompt**；
3. **读 `artifacts_written` 用于 git commit 与 task-progress 归档**；
4. **`evidence` 仅摘要写入 task-progress.md**（≤3 行）；
5. **不读取 SubAgent 返回文本的其他部分**（其他内容可能是 SubAgent 的内部 thinking，应 discard）；
6. **契约字段不存在时视为 `blocked`**（SubAgent 未遵循契约 → 升级用户）。

## DISPATCH 声明式语法

Worker SKILL.md 中所有 SubAgent 分发点统一使用 markdown blockquote 声明式语法，避免绑定特定工具名：

```markdown
> **DISPATCH** → launch independent SubAgent to load and execute `long-task-feature-design`
> **with input**: feature_id=N, srs_trace=["FR-001"], design_path=docs/plans/*-design.md
> **expect**: Structured Return Contract (status, artifacts_written, next_step_input, blockers, evidence)
```

DISPATCH 语义：
- "independent SubAgent" = 新的空上下文，仅加载目标 skill 的 SKILL.md + 引用文档
- "with input" = 组装成 SubAgent prompt 的字段，不是工具参数
- "expect" = 返回必须匹配本契约；不匹配视为 blocked

## 兼容已有 SubAgent

已有 `long-task-feature-design` / `long-task-quality` / `long-task-feature-st` 的 SKILL 已定义各自的 Return Contract（含 Verdict / Metrics 等扩展字段）。这些 SKILL 的契约 **向本统一契约对齐**：
- `Verdict: PASS` ↔ `status: pass`；`FAIL` ↔ `fail`；`BLOCKED` ↔ `blocked`
- 扩展字段（Metrics、Risks、Issues 等）保留，作为 `evidence` 的结构化形态
- 所有 Return Contract 必须声明至少顶层 5 个统一字段（status / artifacts_written / next_step_input / blockers / evidence）

## Resume 支持

会话级 Resume 由 `feature-list.json` 根 `current = {feature_id, phase}` 驱动——下一次会话 Worker Step 1 调 `phase_route.py` 读到 `feature_id` 与相应阶段 skill，从 Step 1 常规流程开始。会话内的子步骤状态不跨会话持久化；SubAgent 大多幂等，重跑会自动接续磁盘上已产出的 artifacts。
