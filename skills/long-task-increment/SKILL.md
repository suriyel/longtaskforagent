---
name: long-task-increment
description: "当 increment-request.json 存在时使用 - 收集增量需求，执行影响分析，更新设计，并分解新功能"
---

# 增量需求开发

在已运行的项目中添加新需求、修改现有需求或废弃功能。所有变更直接写回现有 SRS/设计文档（通过 git 历史追踪），新功能追加到 `feature-list.json` 并附带批次元数据。

**启动时宣告：** "I'm using the long-task-increment skill. Let me orient on the current project state before collecting new requirements."

## 前提条件

- `feature-list.json` 已存在（项目已初始化）
- 项目根目录存在 `increment-request.json`（用户创建的信号文件）

## 检查清单

你必须为每个步骤创建 TodoWrite 任务并按顺序完成：

### 1. 定位

- 读取 `increment-request.json` — 了解此次增量的原因和范围
- 读取 `feature-list.json` — 记录所有功能、状态、批次历史、约束、假设
- 读取已批准的 SRS（`docs/plans/*-srs.md`）— 当前需求基线
- 读取已批准的设计（`docs/plans/*-design.md`）— 当前架构
- 如果存在：读取延期积压（`docs/plans/*-deferred.md`）— 可拾取的预获取需求（对已有完整 EARS + 验收标准的条目跳过重新获取）
- 读取 `task-progress.md` — 会话历史
- 运行 `git log --oneline -10` — 近期上下文
- 确定当前批次编号：`max(wave for all features) + 1`（如果不存在 wave 字段则默认为 1）

### 2. 增量需求获取

通过结构化获取收集新增/变更需求（与 Phase 0a 同等严格度）：

1. 使用 `AskUserQuestion` 分轮收集需求（每轮 2-4 个相关问题）
2. 对每个需求应用 EARS 模板：
   - **普遍型**：The system shall...
   - **事件驱动型**：When \<trigger\>, the system shall...
   - **状态驱动型**：While \<state\>, the system shall...
   - **异常行为型**：If \<condition\>, then the system shall...
   - **可选型**：Where \<feature\>, the system shall...
3. 从现有 SRS 继续分配唯一 ID（如最后一个 FR 是 FR-020，新增从 FR-021 开始）
4. 为每个需求编写 Given/When/Then 验收标准
5. 按 8 项质量属性验证：正确、无歧义、完整、一致、已排序、可验证、可修改、可追溯
6. 将变更分为三类：
   - **新增**：全新的 FR 需求
   - **修改**：对现有 FR 的变更（注明被修改的原始 ID）
   - **废弃**：不再需要的现有需求（注明被移除的 ID）

**输出**：带 ID、EARS 陈述和验收标准的新增/修改/废弃需求结构化列表。

### 3. 影响分析

将新需求与现有功能集进行对比：

1. 对每个**新增**需求 → 识别依赖的现有功能（如有）
2. 对每个**修改**需求 → 识别 `srs_trace` 引用了原始需求 ID 的现有功能；这些功能需要重新验证
3. 对每个**废弃**需求 → 识别实现了该需求的功能；这些将被标记为废弃
4. **传递性影响级联** — 对每个直接受影响的功能，遍历其反向依赖图以找到所有传递性依赖方：
   - 构建反向依赖映射：对每个功能 F，收集所有在 `dependencies[]` 中列出了 F.id 的功能
   - 对每个直接受影响的功能，BFS 遍历反向依赖图（深度限制：2 层）
   - 分类影响：
     - **硬影响**（重置为 failing）：功能直接实现了被修改的需求，或其 Section 6.2 契约发生变更
     - **软影响**（标记待重新验证）：功能是传递性依赖方；可能需要也可能不需要变更，取决于其消费的契约是否实际发生了变更
   - 在影响矩阵中同时包含硬影响和软影响以供用户批准

**输出**：向用户展示的影响矩阵以获取批准：

```
| Change | Type | Affected Features | Action |
|--------|------|-------------------|--------|
| FR-021 | New | (none) | Add feature(s) |
| FR-005 (modified) | Modified | Feature 5, Feature 8 | Reset to failing, update srs_trace |
| FR-012 (deprecated) | Deprecated | Feature 12 | Mark deprecated |
```

**硬性门禁**：用户必须在继续之前批准影响矩阵。

### 3.5. 定向代码库探索（条件触发 — 无用户交互）

**触发条件**（全部满足）：
1. 影响矩阵包含至少一个**硬影响**功能（需要代码变更）
2. 项目有源代码（非纯文档项目）

**跳过条件**：仅有无现有代码依赖的新功能，或仅有无需理解代码的废弃操作。

**执行**：
1. 从已批准的影响矩阵中提取硬影响功能的 `srs_trace` ID 和 `dependencies`
2. 定位受影响的代码区域：
   - 使用功能标题/描述作为搜索关键词
3. 根据影响范围确定探索深度（不要硬编码）：

   | 信号 | 深度调整 |
   |--------|-----------------|
   | 1-2 个硬影响功能，局限于单个模块 | 倾向 quick（定位器即可） |
   | 3-5 个硬影响功能，或跨模块影响 | 倾向 standard（需要依赖 + 流程分析） |
   | 6+ 个硬影响功能，或传递级联深度 ≥2 | 倾向 deep（全面分析） |
   | 受影响功能共享单个 `--path` 子树 | 维持当前或降低（窄范围） |
   | 受影响功能分散在不相关目录 | 提升一级（宽范围） |

   不确定时省略 `--depth`，让 explore 的基于 LOC 的自动检测决定。

4. 分派 `long-task-explore`：
   > **DISPATCH** independent SubAgent(use General or Agent) — load and execute `long-task:long-task-explore`
   > Depth: {determined_depth or omit for auto-detect}
   > Focus: 存量相关架构,数据流,依赖,代码
   > Path: {inferred_path_from_affected_features or "."}
   > User question: "Understand modules affected by: {increment_scope_summary}. Affected features: {hard_impact_feature_titles}."
5. 使用探索输出指导步骤 4（设计修订）：
   - 模块依赖图揭示哪些设计章节需要更新
   - 数据流分析展示可能中断的集成点
   - 依赖分析凸显增量的耦合风险

**此步骤不阻塞** — 如果 explore 返回 BLOCKED 或无可操作发现，正常进入步骤 4。

### 4. 设计修订

**原地**更新现有设计文档中受影响的部分：

1. 读取 `docs/plans/*-design.md`
2. 对**新增**需求：
   - 添加关键功能设计子节（section 4.N+1），包含类图、序列图、流程图和**集成面**（Section 4.N.6），其中 Provides/Requires 引用 Section 6.2
   - 在 Section 6.2 内部 API 契约中为任何新的跨功能边界添加对应行
   - 为新交互更新 Section 3.3 组件图边，添加 Contract ID 标签
   - 如果新功能有依赖，更新依赖链（section 11.3）
   - 更新任务分解（section 11.2）中的新优先级
   - 将任何新的第三方依赖添加到依赖表
   - 对新节中的所有图表应用**绿色（NEW）**可视化变更标记（见子步骤 5b）
3. 对**修改**需求：
   - 原地更新对应的关键功能设计节（4.N）
   - 根据需要更新序列图/流程图
   - 如果修改变更了跨功能接口，更新 Section 6.2 契约和 Section 4.N.6 集成面
   - 对受影响图表中的变更元素应用**琥珀色（MODIFIED）**可视化变更标记（见子步骤 5b）
4. 对**废弃**需求：
   - 在对应设计节添加 `[DEPRECATED - Wave N]` 标记
   - 不要删除该节（保留历史上下文）
5. **Section 11 代码库规约**（如存在）：除非出现新约束，否则原样保留。如果增量引入了新的内部库、禁用了额外 API 或添加了静态分析工具，更新相应的 Section 11 子节。如果自原始扫描以来代码库规约已发生实质性变化，考虑重新扫描（删除 `docs/rules/` 并在新会话中重新运行）。
5b. **在图表中应用可视化变更追踪** — 在本批次触及的每个 Mermaid 图表中标记新增/修改元素。**首先**，移除前一批次的任何变更标记，使每个图表仅显示当前批次的标记。

   **标准 classDef 块**（在 `graph`/`flowchart`/`stateDiagram-v2` 的图表声明后添加）：
   ```
   classDef newNode fill:#d1fae5,stroke:#2ea043,stroke-width:2px
   classDef modNode fill:#fef3c7,stroke:#d4a017,stroke-width:2px
   ```

   **各图表类型语法：**

   | 图表类型 | 新增元素 | 修改元素 | 边标记 |
   |---|---|---|---|
   | `graph`/`flowchart` | `Node[Label]:::newNode` | `Node[Label]:::modNode` | `A -->\|"label 🟢"\| B` / `🟡` |
   | `classDiagram` | `<<NEW - Wave N>>` 注解 | `<<MODIFIED - Wave N>>` 注解 | N/A |
   | `sequenceDiagram` | `rect rgb(209,250,229)` 包裹 + `Note: 🟢 NEW` | `rect rgb(254,243,199)` 包裹 + `Note: 🟡 MODIFIED` | 用 `rect` 包裹 |
   | `erDiagram` | `ENTITY["NEW EntityName"]` 别名 | `ENTITY["MOD EntityName"]` 别名 | N/A |
   | `stateDiagram-v2` | `State:::newNode` | `State:::modNode` | 标签含 `🟢`/`🟡` |

   **范围 — 对以下内容应用标记：**
   - **新增** Section 4.N+1 节中的所有图表（所有元素为绿色）
   - **修改** Section 4.N 节中的变更元素（变更元素为琥珀色，未变更元素不标记）
   - 本批次更新的**架构图表**中的新增/修改元素：Section 3.2 逻辑视图、Section 3.3 组件图、Section 5 数据模型、Section 7.2 依赖图、Section 9.3 依赖链

   **图例** — 在每个包含变更标记的图表前添加 Markdown 注释：
   `> **Change Legend (Wave N):** 🟢 = NEW | 🟡 = MODIFIED`

6. 逐节获取用户批准
7. Git 提交设计更新，附描述性消息：
   ```
   docs: update design for wave N — <brief scope>

   New: FR-021 (feature title), FR-022 (feature title)
   Modified: FR-005 (what changed)
   Deprecated: FR-012 (reason)
   ```

### 5. SRS 更新与功能分解

更新 SRS 并分解为功能：

**5a. 原地更新 SRS：**

1. 读取 `docs/plans/*-srs.md`
2. 对**新增**需求：
   - 追加到适当的节（功能需求、约束等）
   - 保持 ID 连续性
3. 对**修改**需求：
   - 原地更新需求文本
   - 添加变更注释：`<!-- Wave N: Modified YYYY-MM-DD — <reason> -->`
4. 对**废弃**需求：
   - 添加 `[DEPRECATED - Wave N: <reason>]` 前缀标记
   - 不要删除（保留可追溯性）
5. 如果存在则更新可追溯矩阵
6. Git 提交：
   ```
   docs: update SRS for wave N — <brief scope>

   Added: FR-021, FR-022
   Modified: FR-005
   Deprecated: FR-012
   ```

**5b. 分解为功能：**

1. **新功能**：追加到 `feature-list.json` 的 `features[]`：
   - `id`：现有最大 ID + 1（持续递增）
   - `wave`：当前批次编号 N
   - `status`：`"failing"`
   - `srs_trace`：新 SRS 需求 ID 数组（如 `["FR-021"]`）
   - `verification_steps`：可选 — 来自新的验收标准（Given/When/Then）
   - `dependencies`：根据需要引用现有功能 ID

2. **修改功能**：对每个受影响的现有功能：
   - 将 `status` 重置为 `"failing"`（需要重新实现/重新验证）
   - 更新 `srs_trace` 以反映修订后的需求 ID
   - 可选更新 `verification_steps`（如存在）
   - 可选将 `wave` 设为 N（标明修改发生的批次）

3. **废弃功能**：对每个废弃的功能：
   - 设置 `deprecated: true`
   - 设置 `deprecated_reason: "<reason>"`
   - 状态保持不变（已从所有计数中排除）

4. **替代功能**（废弃 + 新替代时）：
   - 新功能设置 `supersedes: <deprecated_feature_id>`

5. 更新根级 `waves[]` 数组：
   ```json
   {
     "id": N,
     "date": "YYYY-MM-DD",
     "description": "Brief description from increment-request.json"
   }
   ```

6. 如果有新的 CON/ASM 条目，更新 `constraints[]` 和 `assumptions[]`

7. 验证：
   ```bash
   python scripts/validate_features.py feature-list.json
   ```

### 6. 更新辅助文件

根据需要更新支持文件：

- **`long-task-guide.md`**：仅包含工具命令配方 — 仅在 `tech_stack` 变更（新的测试/覆盖率/变异测试工具）时更新；用 `python scripts/validate_guide.py long-task-guide.md` 重新验证

### 7. 收尾

1. 删除 `increment-request.json`（信号文件已消费）
2. 最终验证：
   ```bash
   python scripts/validate_features.py feature-list.json
   ```
3. Git 提交所有变更：
   ```
   feat: increment wave N — <scope from increment-request.json>

   New features: <ids>
   Modified features: <ids>
   Deprecated features: <ids>
   Total features: X (Y active, Z deprecated)
   ```
4. 更新 `task-progress.md`：
   - 更新 `## Current State` 标题：进度计数（X/Y 个活跃功能通过），最近事件（增量批次 M，日期），下一步（第一个失败功能）
   - 追加会话条目：
     ```
     ## Session N — Increment Wave M
     - **Date**: YYYY-MM-DD
     - **Phase**: Increment
     - **Scope**: <from increment-request.json>
     - **Changes**: Added N features, modified M features, deprecated K features
     - **Documents updated**: SRS, Design
     ```
5. 更新 `RELEASE_NOTES.md` 的 `[Unreleased]` 节
6. Git 提交进度文件：
   ```
   chore: update progress for increment wave N
   ```

路由器现在将检测到 `feature-list.json` 中的失败功能，并自动路由到 Worker 阶段。

## 关键规则

- **任何变更前先做影响分析** — 不了解影响范围就不得修改功能
- **每个阶段都需用户批准** — 影响矩阵、设计修订、SRS 更新都需要明确批准
- **原地更新文档** — 不要创建单独的增量文件；直接更新现有 SRS/设计；git 历史提供审计追踪
- **ID 连续性** — 新功能 ID 总是从现有最大值递增；永不重用已废弃的 ID
- **批次追踪** — 每个新增/修改的功能都标记当前批次编号
- **废弃功能不可变** — 一旦废弃，永不取消废弃；创建新功能代替
- **每个信号一次增量** — 完整处理一个 increment-request.json 后才接受下一个

## 危险信号

| 合理化借口 | 正确做法 |
|---|---|
| "我直接在 JSON 里加功能就行" | 使用此 skill 进行有追踪、有审计的变更。 |
| "现有测试仍然通过，不需要重新验证" | 修改的功能必须重置为 failing。 |
| "我稍后再更新设计" | 设计修订在功能分解之前完成。 |
| "这个变更很小，跳过影响分析" | 影响分析能发现隐藏的依赖关系。 |
| "我创建一个单独的 SRS 文档" | 原地更新主 SRS；git 追踪历史。 |

## 集成

**调用方：** using-long-task（当 increment-request.json 存在时）
**读取：** SRS、设计、feature-list.json、increment-request.json
**写入：** SRS（原地）、设计（原地）、feature-list.json（追加/修改）
**链接到：** long-task-work（增量完成后，通过路由器检测到失败功能）
