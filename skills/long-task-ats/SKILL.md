---
name: long-task-ats
description: "Use when design doc exists but no ATS doc and no feature-list.json - generate a global Acceptance Test Strategy mapping every requirement to acceptance scenarios with category constraints"
---

# 验收测试策略（ATS）生成

以已审批的 SRS、Design，以及适用时的 UCD 为输入。产出一份全局验收测试策略文档，把每一条需求映射到带类别约束的验收场景——以约束下游 feature-st（通过 srs_trace 派生测试用例）。

**开始时宣告：** "I'm using the long-task-ats skill to generate the Acceptance Test Strategy."

<HARD-GATE>
在 ATS 文档获批之前，禁止调用任何实现 skill、写任何代码、脚手架任何项目、运行 init_project.py 或执行任何实现动作。这适用于**每一个**项目，不论感觉它有多简单。
</HARD-GATE>

## 为什么需要 ATS

没有全局验收测试策略，逐特性的 ST 测试用例会出现：
- 类别失衡（FUNC/BNDRY 过重，SEC/PERF/UI 几近为零）
- NFR 测试方法在 feature-st 期间临时决定
- 跨特性集成场景在 ST 阶段过晚才发现

ATS 把这些决策前置，使 Init 与 feature-st 有可审计的具体约束。

## Scaling 指南

| 项目规模 | 特性数 | ATS 深度 |
|---|---|---|
| 微型 | 1-5 | **跳过独立 ATS** —— 每特性的简化映射直接写入 `feature-list.json` 各特性的 `verification_steps[]`；路由检测到 `*-ats.md` 缺失 + ≤5 特性 → 自动跳到 Init |
| 小型 | 5-15 | 轻量级独立 ATS —— 仅第 1-3 节（范围、映射表、类别策略）；跳过第 4-5 节 |
| 中型 | 15-50 | 完整 ATS 文档——全部 5 节 |
| 大型 | 50-200+ | 完整 ATS + 详细的每个子系统集成矩阵 |

**微型项目自动跳过规则**：如果设计文档存在且 SRS 的功能需求（FR-xxx）≤ 5，本 skill 会把 ATS 映射表嵌入设计文档的 testing strategy 节，并创建一份仅引用该节的最小 `docs/plans/*-ats.md` 占位。路由随后检测到 ATS 占位并进入 Init。

## Checklist

你必须为每个 step 创建一个 TodoWrite 任务并按顺序完成：

### 1. 阅读输入文档

1. 读取 `docs/plans/*-srs.md` 中已审批 SRS 文档
2. 读取 `docs/plans/*-design.md` 中已审批设计文档
3. 读取 `docs/plans/*-ucd.md` 中已审批 UCD 样式指南（如存在——仅 UI 项目）
4. 检查自定义 ATS 模板：
   - 如果用户指定了模板路径 → 读取并校验
   - 否则 → 使用默认模板 `docs/templates/ats-template.md`
5. 检查自定义 ATS 示例：
   - 如果用户指定了示例路径 → 读取示例文件——借鉴风格、语言、细节层级

### 2. 抽取所有需求

从 SRS 抽取完整列表：
- **FR-xxx**：功能需求——带验收标准（Given/When/Then）
- **NFR-xxx**：非功能需求——带可度量阈值
- **IFR-xxx**：接口需求——带协议与数据格式
- **CON-xxx**：约束——硬限
- **ASM-xxx**：假设——隐含信念

统计 FR-xxx 数量。若 ≤ 5，应用 **微型项目自动跳过** 规则：为每条 FR 生成精简验收场景直接写入 `feature-list.json` 对应特性的 `verification_steps[]`，然后写一份仅含占位 + "See feature-list.json verification_steps" 指针的 `docs/plans/YYYY-MM-DD-<topic>-ats.md`。

### 3. 生成需求 → 验收场景映射

对每个 FR/NFR/IFR，生成一个或多个验收场景：

```markdown
| Req ID | Requirement Summary | Acceptance Scenarios | Required Categories | Priority | Notes |
|--------|---------------------|----------------------|---------------------|----------|-------|
| FR-001 | User login | Normal login/wrong password/account lockout/session expiry | FUNC,BNDRY,SEC | Critical | Handles user input→SEC required |
| NFR-001 | Response time<200ms | P95 latency/concurrent load/degradation/cold start | PERF | High | Threshold: P95<200ms @100 concurrent |
| FR-010 | Search results page | Search/empty results/pagination/sorting/filtering | FUNC,BNDRY,UI | High | ui:true→UI required |
```

**类别分配规则：**

| 条件 | 必需类别 |
|-----------|---------------------|
| 所有 FR | FUNC + BNDRY（至少）|
| 处理用户输入/认证/授权/外部数据 | + SEC |
| 对应 `ui: true` 特性 | + UI |
| 关联到带性能指标的 NFR-xxx | + PERF |

**自动化可行性评估（可选列 `自动化可行性`）：**

对每个验收场景，评估其能否用项目技术栈完全自动化：
- `Auto`（默认）—— 标准测试工具能执行和验证（CLI、API、Chrome DevTools MCP）
- `Manual: physical-device` —— 需硬件访问（USB、打印机、IoT 设备）
- `Manual: visual-judgment` —— 需超出自动截图比对的人工视觉评估
- `Manual: external-action` —— 需外部人为动作（收邮件、打电话、在第三方系统审批）
- `Manual: other: {description}` —— 其他原因

本列向下游传播：Feature-ST 读取它以在派生测试用例上设置 `已自动化: No` + `手动测试原因`。Feature-ST 执行期间会通过 `AskUserQuestion` 中断人类执行并汇报手工测试结果。

**保守标注**：仅在自动化真正不可能时才标 `Manual`，而非仅仅困难。Chrome DevTools MCP 覆盖大多数 UI 测试；mock 服务覆盖大多数外部依赖。把 `Manual` 留给真正的缺口。

### 4. 测试类别策略（压缩）

类别语义由 §2 映射表的 `必须类别` 列 + 模板末尾「类别定义（参考）」表承载，本节不重复 prose。按类别一行写具体执行约束：

- **FUNC**：每个 FR 至少一个 happy-path + 一个 error-path 场景
- **BNDRY**：每个带上限/尺寸/计数的 FR 必须显式列边界值场景
- **SEC**：处理用户输入/认证/外部数据的 FR 覆盖注入、授权绕过、数据泄漏
- **PERF**：NFR 指定工具（如 k6/locust/ab）+ 量化阈值 + 负载参数
- **UI**：Chrome DevTools MCP 交互链 navigate → interact → verify → 三层检测

### 5. NFR 测试方法矩阵

对每个带可度量阈值的 NFR-xxx：

```markdown
| NFR ID | Test Method | Tool | Pass Criteria | Load Parameters | Related Feature |
|--------|---------|------|---------|---------|-------------|
| NFR-001 | Load test | k6/locust/ab | P95 < 200ms | 100 concurrent, 60s ramp | Feature 15, 16 |
| NFR-002 | Memory profiling | tracemalloc/heapdump | RSS < 512MB | 10K records | Feature 8 |
```

### 6. 跨特性集成场景

识别跨多个特性的关键数据流路径：

```markdown
| Scenario ID | Description | Features Involved | Data Flow Path | Verification Points | ST Phase Coverage |
|-------------|-------------|-------------------|----------------|---------------------|-------------------|
| INT-001 | User register → login → first action | F1, F2, F5 | POST /register → POST /login → GET /dashboard | Session propagation, data consistency | System ST |
```

**基于 Design §4 派生集成场景：**
对 Design §4 Internal API Contracts 的每一行：
1. 创建至少一个覆盖 happy-path 数据流的集成场景（Provider 产出 → Consumer 接收 → Consumer 正确处理）
2. 创建至少一个覆盖 Provider 错误码的错误场景（例如 Provider 返回 404 → Consumer 优雅处理）
3. 若契约涉及共享持久状态（同一 DB 表），创建一致性场景（并发访问、陈旧读）
4. 在场景的 "Data Flow Path" 列引用 Contract ID（IAPI-xxx）

### 7. 按章节用户审批

向用户呈现每一节以获取审批（与 design skill 相同模式）：

1. 需求 → 场景映射表（Step 3）
2. 测试类别策略（Step 4）
3. NFR 测试方法矩阵（Step 5）——无带指标的 NFR 则跳过
4. 跨特性集成场景（Step 6）

呈现每一节。等待用户反馈。在进入下一节前纳入更改。

**对小型项目**（5-15 特性）：合并为 2 个审批步骤：(a) 映射表 + 类别，(b) NFR + 集成。

### 8. ATS 合规评审

> **DISPATCH** → 创建独立 SubAgent（subagent_type=`long-task:ats-reviewer`），加载 `agents/ats-reviewer.md` 并执行 reviewer
> **input**: `ats_draft`, `srs_path`, `design_path`, `ucd_path`（可选）
> **expect**: Structured Return Contract；`evidence` 含 R1-R6 + R8 裁决列表；`blockers` 含 `[CROSS-REF CONFLICT]` 条目（若有）；`next_step_input` 含 `major_defect_count` / `minor_defect_count` / `review_report_markdown`

按 `references/approval-revise-loop.md` 处理。循环退出后 `next_step_input.review_report_markdown` 即最终评审报告文本，供 Step 9 追加到 ATS 附录。

### 9. 保存 ATS 文档

1. 把已审批 ATS 保存到 `docs/plans/YYYY-MM-DD-<topic>-ats.md`
2. 把 `next_step_input.review_report_markdown` 作为附录节追加
3. 若 Step 8 循环中 `[CROSS-REF CONFLICT]` 用户裁决产生了对 SRS/Design 的修改，已由 loop 模板单独 git commit
4. Git 提交 ATS：
   ```
   docs: add acceptance test strategy (ATS)

   Maps N requirements to acceptance scenarios
   Categories: FUNC, BNDRY, SEC, PERF, UI
   Reviewed: [PASS / CONDITIONAL PASS with N gaps]
   ```

### 10. 衔接到 Initializer

ATS 文档保存并提交后：

1. 为 Initializer 总结关键输入：
   - **来自 SRS**：需求、验收标准 → features
   - **来自 Design**：技术栈、架构 → 项目骨架
   - **来自 ATS**：类别约束 → feature-st 测试用例类别要求（经由 srs_trace）
2. **必需子 skill：** 调用 `long-task:long-task-init` 为项目打骨架

## 与其他文档的边界

| 关注点 | 权威源 |
|--------|--------|
| 测试框架、覆盖率阈值 | `feature-list.json.tech_stack` + `.quality_gates` |
| 每条需求的测试类别映射 | 本 ATS 文档 |
| 每特性 Test Inventory | Worker 阶段 `docs/features/*.md`（由 feature-design SubAgent 产出）|
| 跨特性集成场景 | 本 ATS 文档 §5 |
| 风险优先级 | SRS 需求 `priority` 字段 + Design §2 Feature Integration Specs |

## 关键规则

- **需求驱动**：每一行映射都追溯到特定 SRS 需求 ID
- **无孤立需求**：每个 FR/NFR/IFR 都必须出现在映射表中
- **类别分配可审计**：每个必需类别都有成文理由
- **评审强制**：保存前运行 ATS reviewer subagent——不得跳过
- **Scaling 适用**：微型项目（≤5 FR）跳过独立 ATS；见 Scaling 指南
- **审批后不可变**：对 ATS 的变更需使用 `long-task-increment` skill（ATS Revision 步骤）

## 红旗信号

| 理性化逃避 | 正确响应 |
|---|---|
| "SRS 已有验收标准，ATS 多余" | SRS 有业务标准；ATS 把它们映射到测试类别 |
| "测试类别在 feature-st 时决定就行" | 临时类别分配会导致 SEC/PERF 缺口 |
| "本项目太小不需要 ATS" | 查 Scaling 指南——微型项目自动跳过；小型项目得到轻量 ATS |
| "NFR 测试在 ST 阶段决定" | NFR 测试方法必须前置指定工具与阈值 |
| "评审太过头" | 独立评审能捕捉作者漏看的覆盖缺口 |
