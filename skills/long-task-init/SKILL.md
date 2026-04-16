---
name: long-task-init
description: "当设计文档存在但 feature-list.json 未创建时使用 — 搭建项目产物并从设计 §9.2 填充功能"
---

**语言规则**：你必须用中文（简体）回复用户。所有生成的文档、报告和面向用户的输出必须用中文编写。Skill 名称、代码标识符和 JSON 字段名保持英文。

# 初始化 Long-Task 项目

在 SRS 和设计均批准后运行一次。搭建所有持久化产物，从设计 §9.2 填充功能（FR 已在需求阶段调整大小），为迭代 Worker 周期做准备。

**启动时宣告：** "我正在使用 long-task-init skill 搭建项目。"

## 输入文档

此 skill 从**两份**已批准文档读取：

| 文档 | 位置 | 提供内容 |
|------|------|---------|
| **SRS** | `docs/plans/*-srs.md` | 功能需求（FR-xxx）、约束（CON-xxx）、假设（ASM-xxx）、接口需求（IFR-xxx）、术语表、用户画像、验收标准 |
| **设计** | `docs/plans/*-design.md` | 技术栈、架构、数据模型、API 设计、测试策略 |

## 检查清单

你必须为每步创建 TodoWrite 任务并按顺序完成：

1. **阅读已批准的 SRS 和设计文档** — 从 `docs/plans/`
   - SRS：`docs/plans/*-srs.md` — 需求、约束、假设、术语表、画像
   - 设计：`docs/plans/*-design.md` — 技术栈、架构决策
2. **运行 `scripts/init_project.py`** 搭建确定性产物：
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` — 来自 SRS 标题
   - `<language>` — 设计文档技术栈中的 `python|java|typescript|c|cpp` 之一
   - 创建：`feature-list.json`、`CLAUDE.md`（追加）、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`docs/plans/`
   - 自动复制辅助脚本（`validate_features.py`、`validate_guide.py`、`get_tool_commands.py`、`validate_increment_request.py`、`validate_bugfix_request.py`）到项目 `scripts/`

3. **验证 `feature-list.json` 中的 `tech_stack`**：
   - 确认 `language`、`test_framework`、`coverage_tool`、`mutation_tool` 与设计文档匹配
   - 若 `docs/rules/build-and-compilation.md` 存在：与扫描文档中的"测试与质量工具"表交叉检查 `tech_stack`：
     - 将 `test_framework` 与检测到的测试框架工具名匹配
     - 将 `coverage_tool` 与检测到的覆盖率工具名匹配
     - 将 `mutation_tool` 与检测到的变异工具名匹配
     - 冲突时优先使用扫描值（实际项目状态）并更新 `feature-list.json`
     - 若工具类别在扫描文档中显示"none detected"，保留设计文档/语言预设值
   - 验证工具命令正确解析：
     ```bash
     python scripts/get_tool_commands.py feature-list.json
     ```
4. **生成 `long-task-guide.md`** — 工具命令参考（非工作流指南）：
   a. **收集配置来源**（优先级顺序）：
      - `docs/rules/build-and-compilation.md`（若存在）— 提取构建命令、测试命令、包管理器
      - `python scripts/get_tool_commands.py feature-list.json` — 获取所有 `[*-quiet]`/`[*-detail]` 配方
   b. **指南内容 — 仅包含以下章节**：
      1. **Test Commands** — `[test-quiet]`、`[test-detail]`、完整测试命令
      2. **UT Style** — 项目特定的 UT 约定（来自 `get_tool_commands.py` 输出）：
         - `[test-framework]` — UT + mock 框架
         - `[mock-style]` — mock 方式
         - `[conventions]` — 固定：编写前探索现有测试+源码；复用 fixture
         - 若 `docs/rules/coding-constraints.md` 存在：用扫描值覆盖 `[test-framework]`/`[mock-style]`
      3. **Caveats** — 项目特定的工具注意事项（**LLM 探查生成，非模板**）：
         - 从 `get_tool_commands.py` 输出的 `## Caveat Prompts` 获取探查维度清单
         - **对每条维度**：读取项目实际配置（pom.xml / package.json / pyproject.toml / CMakeLists.txt / conftest.py 等），回答该维度的问题
         - 若 `docs/rules/coding-constraints.md` 存在：额外检查扫描发现的 mock 框架、断言库、内部库约束
         - **输出规则**：
           - 仅写入有实际发现的条目（无发现则跳过该维度）
           - 每条 ≤ 1 行，格式：`- [类别] 发现 → 结论`
           - 总条目数控制在 3-10 条（精选最影响下游 SubAgent 的）
           - 重点关注：**必须参数**（漏掉会导致失败）、**工具冲突**（版本不兼容）、**项目已有选择**（统一而非引入新方案）
   c. **不要包含**：TDD 工作流、验证规则、关键规则、静态分析、persist 步骤 — 这些在子 skill 文件中
   d. **用户预览** — 向用户呈现指南内容；批准后方可继续
   e. **验证**：
     ```bash
     python scripts/validate_guide.py long-task-guide.md
     ```
5. **填充 `feature-list.json` 中的 SRS 字段** — 从 **SRS 文档**：
   - `constraints[]` — 复制 SRS "约束"章节中的 CON-xxx 项；每项为简洁字符串
   - `assumptions[]` — 复制 SRS "假设与依赖"章节中的 ASM-xxx 项；每项为简洁字符串
6. **从设计 §9.2 填充功能** — FR 已在需求阶段调整大小（G1-G6 过大 + S1-S4 过小启发式）。设计文档的任务分解表（§9.2）将已调整大小的 FR 映射为优先级排序的功能含依赖排序。填充 `feature-list.json` `features[]`：
   - 每个 §9.2 行 → 一个功能。不要进一步拆分或合并 — 粒度已在 SRS 阶段最终确定。
   - `srs_trace`：复制"Mapped FRs"列 — 此功能实现的 FR ID 数组（如 `["FR-003", "FR-004", "FR-005"]`）
   - `title` + `description`：从 §9.2 功能名 + 映射 FR 的描述导出
   - `priority`：P0/P1 → `"high"`，P2 → `"medium"`，P3 → `"low"`
   - `dependencies`：来自 §9.3 依赖链图
   - `status`：始终 `"failing"`
   - `verification_steps` 可选 — 若提供，将所有映射 FR 的验收标准整合为行为场景（Given/When/Then）：
     - 每步必须是含 Given/When/Then 结构的行为场景，非简单断言
     - 错误：`"Login page displays correctly"` → 无动作、无断言
     - 正确：`"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - 对有后端依赖的功能：至少一步必须验证跨依赖边界的真实数据流
     - **最低复杂度**：每个功能应有 ≥ 1 个含 3+ 链式操作的 verification_step
   - **排序**：遵循 §9.2 行顺序（已由设计按优先级排序和后端/前端配对）
   - 每个功能必须可独立验证且在一个会话内完成
   - **验证门禁**：填充所有功能后验证：
     - SRS 中每个 FR-xxx 至少出现在一个功能的 `srs_trace` 中（无孤立需求）
     - 每个功能的 `srs_trace` 至少包含一个 FR（无空追溯）
   - **单轮标志传播**：若 SRS 文档元数据包含 `Single-Round: Yes`，在 `feature-list.json` 根层级设置 `"single_round": true`。这是信息性标志 — 无论此标志如何，所有 Worker 步骤执行其完整标准流程。
7. **验证**：
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
8. **搭建项目骨架**（目录、配置、依赖清单）— 基于**设计文档**架构
9. **更新 `task-progress.md`** — 更新 `## Current State` 为初始进度（0/N features passing），然后追加 Session 0 条目（包含 SRS + 设计文档引用）
10. **开始首个 Worker 周期** — **必需子 SKILL：** 调用 `long-task:long-task-work`

## Feature List Schema

根结构：
```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "tech_stack": {
    "language": "python|java|typescript|c|cpp",
    "test_framework": "pytest|junit|vitest|gtest|...",
    "coverage_tool": "pytest-cov|jacoco|c8|gcov|...",
    "mutation_tool": "mutmut|pitest|stryker|mull|..."
  },
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
  "features": [...]
}
```

每个功能：
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
  "dependencies": []
}
```

## 生成的持久化产物

| 文件 | 用途 |
|------|------|
| `feature-list.json` | 带状态的结构化任务清单 |
| `CLAUDE.md` | 跨会话导航索引（追加） |
| `task-progress.md` | 逐会话进度日志 |
| `RELEASE_NOTES.md` | 持续更新的发布说明（Keep a Changelog 格式） |
| `examples/` | 可运行的示例目录 |
| `long-task-guide.md` | 工具命令参考 — 测试/覆盖率/变异配方（LLM 生成、用户批准、已验证） |

## 集成

**调用者：** long-task-design（Step 6）或 using-long-task（当设计文档存在、无 feature-list.json 时）
**读取：** `docs/plans/*-srs.md`（需求）+ `docs/plans/*-design.md`（架构）
**链接到：** long-task-work（初始化完成后）
**产出：** feature-list.json + 上述所有搭建产物
