---
name: long-task-increment
description: "Use when increment-request.json exists - collect incremental requirements, perform impact analysis, update design, and decompose new features"
---

# 增量需求开发

在已交付项目中新增需求、修改现有需求或弃用特性。所有变更直接写回到既有 SRS/Design/UCD 文档（通过 git 历史追踪），新特性以批次元数据追加到 `feature-list.json`。

**开始时声明：** "I'm using the long-task-increment skill. Let me orient on the current project state before collecting new requirements."

## 前置条件

- `feature-list.json` 存在（项目已初始化）
- 项目根目录存在 `increment-request.json`（由用户创建的信号文件）

## 清单

必须为每一步创建 TodoWrite 任务并按顺序完成：

### 1. Orient（调取上下文）

- 阅读 `increment-request.json` —— 理解本次增量的原因和范围
- 阅读 `feature-list.json` —— 记录所有特性及其状态、批次历史、constraints、assumptions
- 阅读已批准的 SRS（`docs/plans/*-srs.md`）—— 当前需求基线
- 阅读已批准的设计文档（`docs/plans/*-design.md`）—— 当前架构
- 若存在：阅读 ATS 文档（`docs/plans/*-ats.md`）—— 当前测试策略基线
- 若为 UI 项目：阅读 UCD 样式指南（`docs/plans/*-ucd.md`）
- 若存在：阅读待办清单（`docs/plans/*-deferred.md`）—— 可直接采用的已预先 elicitation 的需求（含完整 EARS + 验收标准的条目可跳过再次 elicitation）
- 阅读 `task-progress.md` —— 会话历史
- 运行 `git log --oneline -10` —— 近期上下文
- 确定当前批次号：`max(wave for all features) + 1`（若无 wave 字段默认为 1）
- **加载 brownfield 适配协议（强制）**：阅读 `references/brownfield-adaptation.md`。使用 `docs/explore/codebase-research.md`（若存在）、`env-guide.md` §4、设计 §4 与已通过的特性作为证据来源，按 §A 构建 ESI（Existing System Inventory，存量系统清单）表。ESI 将约束 Step 2（过滤已存在的能力）与 Step 3（API 影响表）。

### 2. 增量需求 elicitation

使用结构化 elicitation 收集新增/变更需求（严格度与 Phase 0a 一致）：

1. 使用 `AskUserQuestion` 按轮次收集需求（每轮 2-4 个相关问题）
2. 对每条需求应用 EARS 模板：
   - **Ubiquitous**: The system shall...
   - **Event-driven**: When \<trigger\>, the system shall...
   - **State-driven**: While \<state\>, the system shall...
   - **Unwanted behavior**: If \<condition\>, then the system shall...
   - **Optional**: Where \<feature\>, the system shall...
3. 分配唯一 ID，衔接现有 SRS（如最后一条 FR 为 FR-020，新增从 FR-021 开始）
4. 为每条需求写 Given/When/Then 验收标准
5. 按 8 大质量属性校验：Correct、Unambiguous、Complete、Consistent、Ranked、Verifiable、Modifiable、Traceable
6. 将变更归入三类：
   - **新增（New）**：全新的 FR/NFR 需求
   - **修改（Modified）**：对既有 FR/NFR 的变更（注明被修改的原 ID）
   - **弃用（Deprecated）**：不再需要的既有需求（注明被移除的 ID）
7. **Brownfield 过滤**（依据 `references/brownfield-adaptation.md` §B/§C）：对每个候选 FR，交叉比对 Step 1 的 ESI 表：
   - 若该能力在 ESI 中已"已确立"且用户未明确要求变更 → 归类为 `REUSE`，从 FR 列表中移除，作为 ASM-xxx 追加到 SRS §1.4
   - 为剩余每条需求打上变更类型标签：`NEW` / `MODIFY` / `EXTEND`（REUSE 的行已在上一步过滤）
   - 本过滤防止把既有的横切关注（鉴权、日志、错误处理）重复声明为新 FR。

**输出**：一份结构化的新增/修改/弃用需求清单，包含 ID、EARS 语句、验收标准与变更类型标签（NEW/MODIFY/EXTEND）。

### 3. 影响评估

将新需求与既有特性集作比较：

1. 对每条**新增**需求 → 识别其依赖的既有特性（如有）
2. 对每条**修改**需求 → 识别 `srs_trace` 中引用原需求 ID 的既有特性；这些特性需要重新验证
3. 对每条**弃用**需求 → 识别实现它的特性；这些特性将被标记为 deprecated
4. **传递影响级联** —— 对每个直接受影响的特性，遍历其反向依赖图以发现所有传递依赖方：
   - 构建反向依赖映射：对每个特性 F，收集所有在 `dependencies[]` 中列出 F.id 的特性
   - 对每个直接受影响特性，在反向依赖图上 BFS（深度上限：2 层）
   - 对影响分类：
     - **Hard impact（重置为 failing）**：特性直接实现了被修改的需求 **或** 其 §6.2 契约发生变化
     - **Soft impact（标记为需重新验证）**：特性是传递依赖方；是否需要改动取决于其消费的契约是否真的变了
   - 将 Hard 与 Soft 影响一并列入影响矩阵供用户审批

**输出 1 —— 影响矩阵**（高层的特性粒度视图）：

```
| Change | Type | Affected Features | Action |
|--------|------|-------------------|--------|
| FR-021 | New | (none) | Add feature(s) |
| FR-005 (modified) | Modified | Feature 5, Feature 8 | Reset to failing, update srs_trace |
| FR-012 (deprecated) | Deprecated | Feature 12 | Mark deprecated |
```

**输出 2 —— API 影响与兼容性表**（依据 `references/brownfield-adaptation.md` §D 强制）：

即使是纯新增增量也要构建此表 —— 仅填一行 "N/A — 纯新增，无存量 API 修改"。

```
| # | 修改项 | 位置（file:line 或签名） | 变更类型 | 兼容策略 | impact_features |
|---|--------|-------------------------|---------|---------|-----------------|
| 1 | UserService.findById(id) → findById(id, tenantId) | src/services/UserService.java:L42 | Breaking | 旧签名保留 1 版本 + @Deprecated | [1, 5, 12] |
| 2 | POST /api/orders response 新增 trace_id | src/api/orders.ts:L88 | Additive | 向后兼容 | [7, 8] |
```

- `变更类型`：NEW / MODIFY / EXTEND（与 Step 2 的变更类型标签一致）
- `兼容策略`：Additive / Deprecated / Breaking
- 策略为 `Breaking` 的行**必须**把对应的 `impact_features` 作为 Hard Impact 列入影响矩阵
- 每行必须含具体的 `file:line` 或完整方法签名（不得只写模块名）

**硬关卡**：用户必须同时批准两张表（影响矩阵 + API 影响与兼容性）后方可继续。

### 3.5. 针对性代码库探索（条件触发 —— 无用户交互）

**触发条件**（全部成立）：
1. 影响矩阵中至少有一条 **Hard Impact** 特性（需要改代码）
2. 项目有源码（非纯文档项目）

**跳过条件**：仅新增无既有代码依赖的特性；**或**仅弃用、无需理解代码。

**执行**：
1. 从已批准的影响矩阵中，提取 Hard Impact 特性的 `srs_trace` ID 与 `dependencies`
2. 定位受影响的代码区域：
   - 使用受影响特性的 `git_sha`（若已设置），通过 `git show --stat` 查找相关文件
   - 以特性标题/描述作为搜索关键字
3. 根据影响范围决定探索深度（**不要硬编码**）：

   | 信号 | 深度调整 |
   |--------|-----------------|
   | 1-2 个 Hard Impact 特性，局限于单模块 | 优先 quick（locator 即可） |
   | 3-5 个 Hard Impact 特性，或跨模块影响 | 优先 standard（需要依赖 + 流分析） |
   | 6+ 个 Hard Impact 特性，或传递级联深度 ≥ 2 | 优先 deep（综合分析） |
   | 受影响特性共享同一 `--path` 子树 | 保持当前或降一级（窄范围） |
   | 受影响特性跨越不相关目录 | 升一级（宽范围） |

   不确定时省略 `--depth`，交由 explore 的 LOC 自动检测决定。

4. 以上下文驱动的参数分发 `long-task-explore`：
   ```
   Agent(
     subagent_type="general-purpose",
     description="Targeted codebase exploration for increment impact",
     prompt="""
     Invoke the long-task:long-task-explore skill with these parameters:
     - Depth: {determined_depth or omit for auto-detect}
     - Focus: architecture,dataflow,deps
     - Path: {inferred_path_from_affected_features or "."}
     - User question: "Understand modules affected by: {increment_scope_summary}. 
       Affected features: {hard_impact_feature_titles}."
     Execute the skill and return the exploration results.
     """
   )
   ```
5. 将探索输出用于指导 Step 4（设计修订）：
   - 模块依赖图揭示哪些设计章节需要更新
   - 数据流分析显示可能被破坏的集成点
   - 依赖分析凸显增量的耦合风险

**本步骤非阻塞** —— 若 explore 返回 BLOCKED 或无可用发现，正常进入 Step 4。

### 4. 设计修订

**原地**更新既有设计文档的受影响章节：

1. 阅读 `docs/plans/*-design.md`
2. 对**新增**需求：
   - 新增 Key Feature Design 子章节（section 4.N+1），含类图、时序图、流程图，以及引用 §6.2 的 Provides/Requires 的 **Integration Surface**（§4.N.6）
   - 对任何新的跨特性边界，在 §6.2 Internal API Contracts 中新增对应行
   - 在 §3.3 组件图的边上为新交互添加 Contract ID 标签
   - 若新特性有依赖关系，更新依赖链（section 11.3）
   - 更新任务分解（section 11.2）的优先级
   - 将任何新的三方依赖加入依赖表
3. 对**修改**需求：
   - 原地更新相应的 Key Feature Design 章节（4.N）
   - 按需更新时序/流程图
   - 若修改影响跨特性接口，更新 §6.2 契约与 §4.N.6 Integration Surface
4. 对**弃用**需求：
   - 在相应设计章节加 `[DEPRECATED - Wave N]` 标记
   - **不要**删除该章节（保留历史上下文）
5. **§13 存量代码库约定**（若存在）：保持原样，除非出现新约束。若增量引入了新的内部库、禁用了更多 API，或新增了静态分析工具，就更新对应的 §13 子节。若存量代码约定自上次扫描以来发生了实质变化，可以考虑重新扫描（删除 `docs/rules/` 并在新会话中重跑）。按 brownfield-adaptation.md §E：对 Step 3 API 影响表中每一行标记为 `Breaking` 的，确认设计 §6.2 内部 API 契约已更新为新签名 —— 否则下游消费特性会在 TDD 阶段发现不一致而需要返工。**若 §13 变化，同步传播到 `env-guide.md` §4**；若增量引入新的 build/test/coverage 命令（如构建中新增了一个服务），也要更新 `env-guide.md` §3。**§3/§4 的变更都需要人工审批** —— 修改后向用户提示：
   > "env-guide.md §3/§4 was modified by this increment. Please review the diff, then update the frontmatter `approved_by` / `approved_date` / `approved_sections` before the next Worker cycle (Worker Step 0 enforces)."

   在增量结束时运行 `python scripts/check_env_guide_approval.py env-guide.md` 校验新状态；若未审批则阻塞直至用户提交审批。
6. 逐节获取用户批准
7. 以描述性 message 提交设计更新：
   ```
   docs: update design for wave N — <brief scope>

   New: FR-021 (feature title), FR-022 (feature title)
   Modified: FR-005 (what changed)
   Deprecated: FR-012 (reason)
   ```

### 4b. ATS 修订

**跳过本步骤**：若不存在 ATS 文档（`docs/plans/*-ats.md`）。

**原地**更新既有 ATS 文档的受影响需求：

1. 阅读 `docs/plans/*-ats.md`
2. 对**新增**需求：
   - 新增映射表行，含需求 ID、场景、所需分类
   - 应用分类分配规则（所有 FR 需 FUNC+BNDRY；输入/鉴权 +SEC；ui:true +UI；有指标的 NFR +PERF）
   - 更新覆盖率统计表（Section 2.4）
   - 若有新 NFR：在 NFR Test Method Matrix（Section 4）中新增行
   - 若有新跨特性交互：在集成场景（Section 5）中新增行
3. 对**修改**需求：
   - 原地更新相应映射表行（场景、分类）
   - 若阈值变化，调整 NFR 测试方法
   - 若数据流变化，更新集成场景
4. 对**弃用**需求：
   - 在相应映射表行添加 `[DEPRECATED - Wave N]` 标记
   - **不要**删除该行（保留可追溯性）
   - 更新覆盖率统计（从总量中排除已弃用行）
5. 对**新增** §6.2 契约：按 §6.2 驱动推导规则新增集成场景（每条契约行至少 1 个 happy-path + 1 个 error 场景）。对**修改** §6.2 契约：更新对应集成场景。
6. 若风险画像变化，更新 Risk-Driven Test Priority 章节
6. 获取 ATS 变更的用户批准
7. Git commit：
   ```
   docs: update ATS for wave N — <brief scope>

   New: <req_ids added>
   Modified: <req_ids changed>
   Deprecated: <req_ids deprecated>
   ```
8. **ATS 再评审检查**：若 ATS 变更影响 >3 行映射表行 **或** 引入此前不存在的新测试分类，在继续前询问用户是否需要再评审。若是，向用户说明变更与理由以供批准。

### 5. UCD 修订（仅 UI 项目）

**跳过本步骤**：若项目没有 UI 特性 **且** 新增需求均不涉及 UI。

1. 阅读 `docs/plans/*-ucd.md`
2. 对新增 UI 需求：
   - 为新 UI 组件新增组件提示
   - 为新页面新增页面提示
   - 若设计语言需要扩展，更新 style tokens
3. 对修改的 UI 需求：
   - 原地更新相应组件/页面提示
4. 对弃用的 UI 需求：
   - 在相应提示上添加 `[DEPRECATED - Wave N]` 标记
5. 获取用户批准
6. Git commit：
   ```
   docs: update UCD style guide for wave N — <brief scope>
   ```

### 6. SRS 更新与特性分解

更新 SRS 并分解为特性：

**6a. 原地更新 SRS：**

1. 阅读 `docs/plans/*-srs.md`
2. 对**新增**需求：
   - 追加到相应章节（Functional Requirements、NFRs 等）
   - 保持 ID 连续
3. 对**修改**需求：
   - 原地更新需求文本
   - 加一条变更注释：`<!-- Wave N: Modified YYYY-MM-DD — <reason> -->`
4. 对**弃用**需求：
   - 以 `[DEPRECATED - Wave N: <reason>]` 前缀标记
   - **不要**删除（保留可追溯性）
5. 若存在追溯矩阵则更新
5b. **回填 SRS §1.4 Existing System Context**（依据 `references/brownfield-adaptation.md` §F）：记录变更类型分布（NEW/MODIFY/EXTEND/REUSE 数量）、ESI 已确立维度（列出复用的横切关注点与其 ASM-xxx ID）、1-3 句变更摘要、受影响模块、未受影响模块。本节可防止下游设计/特性 SubAgent 误把增量当作全新项目构建。
6. Git commit：
   ```
   docs: update SRS for wave N — <brief scope>

   Added: FR-021, FR-022
   Modified: FR-005
   Deprecated: FR-012
   ```

**6b. 分解为特性：**

1. **新增特性**：追加到 `feature-list.json` 的 `features[]`：
   - `id`：现有最大 ID + 1（持续递增）
   - `wave`：当前批次号 N
   - `status`：`"failing"`
   - `srs_trace`：新 SRS 需求 ID 数组（如 `["FR-021"]`）
   - `verification_steps`：可选 —— 来自新验收标准（Given/When/Then）
   - `dependencies`：按需引用既有特性 ID
   - `ui`、`ui_entry`：按需设置

2. **修改的特性**：对每个受影响的既有特性：
   - 将 `status` 重置为 `"failing"`（需要重新实现/重新验证）
   - 更新 `srs_trace` 以反映修订后的需求 ID
   - 可选：若存在则更新 `verification_steps`
   - 可选：将 `wave` 设为 N（标识修改发生的批次）
   - 若该特性出现在 Step 3 API 影响表的 `impact_features` 中：添加 `impact_note: "Wave N API change — <compat strategy>"` 以记录向后兼容计划（若 feature-list.json schema 原生不支持，则作为 metadata 注释存入 feature description）

3. **弃用的特性**：对每个被弃用的特性：
   - 置 `deprecated: true`
   - 置 `deprecated_reason: "<reason>"`
   - 状态保持不变（它已被排除在所有统计之外）

4. **替代特性**（弃用 + 新增替代）：
   - 新特性设置 `supersedes: <deprecated_feature_id>`

5. 更新根级 `waves[]` 数组：
   ```json
   {
     "id": N,
     "date": "YYYY-MM-DD",
     "description": "Brief description from increment-request.json"
   }
   ```

6. 若有新的 CON/ASM 条目，更新 `constraints[]` 与 `assumptions[]`

7. 若有新配置项，更新 `required_configs[]`

8. 校验：
   ```bash
   python scripts/validate_features.py feature-list.json
   ```

### 7. 更新辅助文件

按需更新配套文件：

- **`long-task-guide.md`**：若引入了新工具、框架或模式 → 重新生成或更新相关章节；用 `python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json` 重新校验
- **`init.sh` / `init.ps1`**：若新增了依赖 → 更新 bootstrap 脚本（保持幂等）
- **`.env.example`**：若新增了 `env` 类型的 `required_configs` → 追加模板行（无论项目实际配置格式如何，这里都是规范的环境变量模板参考）
- **`scripts/check_configs.py`**：若新增了 `required_configs` → 重新生成或更新项目专用检查器以包含新配置

### 8. 收尾

1. 删除 `increment-request.json`（信号文件已消费）
2. 最终校验：
   ```bash
   python scripts/validate_features.py feature-list.json
   ```
3. Git commit 所有变更：
   ```
   feat: increment wave N — <scope from increment-request.json>

   New features: <ids>
   Modified features: <ids>
   Deprecated features: <ids>
   Total features: X (Y active, Z deprecated)
   ```
4. 更新 `task-progress.md`：
   - 更新 `## Current State` 头部：进度计数（X/Y 个激活特性通过）、last event（Increment Wave M，日期）、next up（首个 failing 特性）
   - 追加一条会话记录：
     ```
     ## Session N — Increment Wave M
     - **Date**: YYYY-MM-DD
     - **Phase**: Increment
     - **Scope**: <from increment-request.json>
     - **Changes**: Added N features, modified M features, deprecated K features
     - **Documents updated**: SRS, Design, [UCD]
     ```
5. 在 `RELEASE_NOTES.md` 的 `[Unreleased]` 章节下更新
6. Git commit 进度文件：
   ```
   chore: update progress for increment wave N
   ```

路由随后会检测到 `feature-list.json` 中的 failing 特性，自动路由到 Worker 阶段。

## 关键规则

- **任何变更前必须做影响评估** —— 未理解爆炸半径绝不修改特性
- **每个阶段都需要用户批准** —— 影响矩阵、设计修订、SRS 更新都要显式批准
- **原地更新文档** —— **不要**另建 increment 文件；直接更新既有 SRS/Design/UCD；git 历史即为审计轨迹
- **ID 连续性** —— 新特性 ID 始终从现有最大值递增；绝不复用已弃用 ID
- **批次跟踪** —— 每个新增/修改特性都打上当前批次号
- **已弃用特性不可变** —— 一旦弃用绝不解除；改用新建特性
- **一次一个信号** —— 完整处理完一个 increment-request.json 再接受下一个

## 红旗

| 合理化借口 | 正确动作 |
|---|---|
| "直接往 JSON 里加特性算了" | 使用本 skill 以获得可追踪、可审计的变更。 |
| "既有测试还在过，不用重新验证" | 被修改的特性必须重置为 failing。 |
| "我稍后再更新设计" | 设计修订必须**在**特性分解之前。 |
| "这次改动很小，跳过影响评估" | 影响评估能捕捉隐藏依赖。 |
| "我另建一份 SRS 文档" | 原地更新主 SRS；由 git 跟踪历史。 |

## 集成

**调用方：** using-long-task（当 increment-request.json 存在时）
**读取：** SRS、Design、ATS、UCD、feature-list.json、increment-request.json
**写入：** SRS（原地）、Design（原地）、ATS（原地）、UCD（原地）、feature-list.json（追加/修改）
**下游：** long-task-work（增量完成后，由路由检测到 failing 特性触发）
