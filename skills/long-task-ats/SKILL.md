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
- 风险驱动的测试优先级完全缺失

ATS 把这些决策前置，使 Init 与 feature-st 有可审计的具体约束。

## Scaling 指南

| 项目规模 | 特性数 | ATS 深度 |
|---|---|---|
| 微型 | 1-5 | **跳过独立 ATS** —— 把简化映射表嵌入设计文档的 Testing Strategy 节（第 7 节）；路由检测到 `*-ats.md` 缺失 + ≤5 特性 → 自动跳到 Init |
| 小型 | 5-15 | 轻量级独立 ATS —— 仅第 1-3 节（范围、映射表、类别策略）；跳过第 4-6 节 |
| 中型 | 15-50 | 完整 ATS 文档——全部 6 节 |
| 大型 | 50-200+ | 完整 ATS + 详细的每个子系统集成矩阵 + 风险热图 |

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

统计 FR-xxx 数量。若 ≤ 5，应用 **微型项目自动跳过** 规则（见上方 Scaling 指南）。

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

### 4. 定义测试类别策略

对每个测试类别，指定策略：

- **FUNC**：每个 FR 必须至少覆盖一个 happy-path + 一个 error-path 场景
- **BNDRY**：每个 FR 的边界值分析 + 等价类划分需求
- **SEC**：输入校验（SQL 注入、XSS、路径穿越）、认证绕过、授权越权、数据泄漏
- **PERF**：NFR 指标阈值 + 负载场景 + 工具规约 + 通过标准
- **UI**：Chrome DevTools MCP 交互链—— navigate → interact → verify → 三层检测

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

**基于 §6.2 派生集成场景：**
对 Design §6.2 Internal API Contracts 的每一行：
1. 创建至少一个覆盖 happy-path 数据流的集成场景（Provider 产出 → Consumer 接收 → Consumer 正确处理）
2. 创建至少一个覆盖 Provider 错误码的错误场景（例如 Provider 返回 404 → Consumer 优雅处理）
3. 若契约涉及共享持久状态（同一 DB 表），创建一致性场景（并发访问、陈旧读）
4. 在场景的 "Data Flow Path" 列引用 Contract ID（IAPI-xxx）

### 7. 风险驱动的测试优先级

按需求评估风险并分配测试深度：

```markdown
| Risk Area | Risk Level | Impact Scope | Test Depth | Rationale |
|-----------|------------|--------------|------------|-----------|
| User authentication | High | System-wide | Deep (SEC+FUNC+BNDRY) | Security boundary |
| Data import | Medium | Feature 3-5 | Standard (FUNC+BNDRY) | Data integrity |
```

### 8. 按章节用户审批

向用户呈现每一节以获取审批（与 design skill 相同模式）：

1. 需求 → 场景映射表（Step 3）
2. 测试类别策略（Step 4）
3. NFR 测试方法矩阵（Step 5）——无带指标的 NFR 则跳过
4. 跨特性集成场景（Step 6）
5. 风险驱动优先级（Step 7）

呈现每一节。等待用户反馈。在进入下一节前纳入更改。

**对小型项目**（5-15 特性）：合并为 2 个审批步骤：(a) 映射表 + 类别，(b) 其他全部。

### 9. Subagent 评审

分发 ATS reviewer subagent 进行独立质量评审：

```
Agent(
  subagent_type="general-purpose",
  prompt="""
  You are an independent ATS reviewer.
  Read the reviewer definition at: agents/ats-reviewer.md

  ## Input Documents
  - ATS document (draft): {ats_content}
  - SRS document: {srs_path} — read it
  - Design document: {design_path} — read it
  - UCD document (if applicable): {ucd_path} — read it

  ## Task
  Execute all review dimensions (R1-R8) defined in agents/ats-reviewer.md.
  Output a structured review report.
  Do NOT suggest improvements beyond defect identification.
  Do NOT read any implementation code — this is a requirements-level review.
  """
)
```

**隔离保证：**
- Subagent 仅读取 ATS + SRS + Design + UCD + reviewer 定义（agents/ats-reviewer.md）
- Subagent 不读取实现代码或测试代码
- Subagent 不修改任何文件——仅返回结构化报告
- 主 skill 处理报告并决定修复

### 10. 处理评审报告

解析 subagent 的评审报告：

1. **0 个 Major 缺陷** → PASS → 进入 Step 10.5
2. **存在 Major 缺陷** → 按缺陷描述修复 ATS 文档 → 重跑 Step 9（最多 2 轮评审）
3. **第三轮仍 FAIL** → 通过 `AskUserQuestion` 向用户呈现完整报告：
   - 显示所有剩余 Major 缺陷
   - 选项：手动修复 / 接受已知缺口 / 终止
   - 如用户接受缺口：在 ATS 页脚节记录缺口

### 10.5 处理交叉引用冲突

如果评审报告包含 `[CROSS-REF CONFLICT]` 项（来自 R8 交叉校验）：

1. 从评审报告的 **Cross-Reference Conflicts** 表收集所有 `[CROSS-REF CONFLICT]` 项
2. 对每个冲突，通过 `AskUserQuestion` 呈现给用户：
   - 源文档值 + 节引用
   - ATS 值 + 节引用
   - 性质：omission / contradiction / distortion
   - 选项：
     - **A**：采用源文档值（修改 ATS）
     - **B**：采用 ATS 值（更新 SRS/Design 以匹配）
     - **C**：两者都不对（用户提供正确值）
3. 把用户决定应用到相关文档
4. 在 ATS 附录（Review Report 节）记录每条决定，格式：
   ```
   | Conflict # | Decision | Applied To | User Rationale |
   ```
5. 若有源文档（SRS/Design）被修改，git commit 变更：
   ```
   docs: resolve ATS cross-reference conflicts per user decision
   ```
6. 进入 Step 11

### 11. 保存 ATS 文档

1. 把已审批 ATS 保存到 `docs/plans/YYYY-MM-DD-<topic>-ats.md`
2. 把最终评审报告作为附录节追加
3. Git 提交：
   ```
   docs: add acceptance test strategy (ATS)

   Maps N requirements to acceptance scenarios
   Categories: FUNC, BNDRY, SEC, PERF, UI
   Reviewed: [PASS / CONDITIONAL PASS with N gaps]
   ```

### 12. 衔接到 Initializer

ATS 文档保存并提交后：

1. 为 Initializer 总结关键输入：
   - **来自 SRS**：需求、验收标准 → features
   - **来自 Design**：技术栈、架构 → 项目骨架
   - **来自 ATS**：类别约束 → feature-st 测试用例类别要求（经由 srs_trace）
2. **必需子 skill：** 调用 `long-task:long-task-init` 为项目打骨架

## 与设计文档 Testing Strategy 的边界

**设计文档**（第 7 节，Testing Strategy）描述*方式*：
- 使用哪些测试类型（unit、integration、E2E）
- 使用哪些工具与框架（pytest、k6、Chrome DevTools MCP）
- 覆盖率目标（line 90%、branch 80%）

**ATS 文档**描述*详细映射*：
- 哪条具体需求得到哪些具体测试类别
- 带精确阈值与负载参数的 NFR 测试方法
- 跨特性集成场景
- 风险驱动测试深度

设计文档的 testing strategy 节**应当**在 ATS 存在后引用它：
```markdown
See `docs/plans/YYYY-MM-DD-<topic>-ats.md` for detailed requirement-to-test-category mapping.
```

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

## 集成

**被调用方：** using-long-task（设计文档存在、无 ATS 文档、无 feature-list.json 时）或 long-task-design（Step 6）
**依赖：** `docs/plans/*-srs.md` 已审批 SRS；`docs/plans/*-design.md` 已审批 Design；可选 `docs/plans/*-ucd.md` 已审批 UCD
**衔接到：** long-task-init（ATS 审批后）
**产出：** `docs/plans/YYYY-MM-DD-<topic>-ats.md`
**下游消费方：**
- `long-task-init` —— 读取 ATS 基于类别分配设置 `ui` 标记
- `long-task-feature-st` —— 读取 ATS 强制类别要求（经由 srs_trace 查询）
- `long-task-st` —— 以 ATS 作为 RTM 校验基线
- `long-task-increment` —— 需求变更时就地更新 ATS
