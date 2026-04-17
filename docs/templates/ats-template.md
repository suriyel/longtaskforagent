# 验收测试策略（ATS）模板

> 本模板定义全局验收测试策略（Acceptance Test Strategy）文档的结构。
> LLM 按此结构生成 ATS 内容。
> 用户可通过 `feature-list.json` 中的 `ats_template_path` 覆盖此模板（也可在 ATS 阶段指定）。
> 用户还可通过 `ats_example_path` 提供风格/语言参考示例。

---

## 文档头（Document Header）

```markdown
# 验收测试策略: {project_title}

**SRS 参考**: {srs_path}
**设计文档参考**: {design_path}
**UCD 参考**: {ucd_path or "N/A"}
**日期**: {YYYY-MM-DD}
**状态**: Draft / Approved
**模板版本**: 1.0
```

## 第 1 节：测试范围与策略概览（Test Scope & Strategy Overview）

```markdown
## 1. 测试范围与策略概览

### 1.1 测试目标

{本 ATS 的目标 — 确保所有 SRS 需求在 feature-st 阶段有充分的验收测试覆盖}

### 1.2 质量目标

- 每个 FR 至少覆盖 FUNC + BNDRY 类别
- 处理用户输入/认证的 FR 必须覆盖 SEC 类别
- ui:true 的 feature 必须覆盖 UI 类别
- NFR 必须有明确的测试工具和通过标准
- 跨 feature 集成路径必须在 ST 阶段验证

### 1.3 测试级别定义

| 级别 | 描述 | 执行阶段 |
|------|------|---------|
| 单元测试 | TDD Red-Green-Refactor | Worker (long-task-tdd) |
| 特性验收测试 | 黑盒 ST 测试用例 | Worker (long-task-feature-st) |
| 系统测试 | 跨特性集成 + NFR 验证 | ST (long-task-st) |
```

## 第 2 节：需求→验收场景映射（核心）

```markdown
## 2. 需求→验收场景映射

### 2.1 功能需求 (FR)

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 自动化可行性 | 备注 |
|--------|---------|---------|---------|--------|-------------|------|
| FR-001 | {摘要} | {场景1/场景2/...} | FUNC,BNDRY,{+其他} | Critical/High/Medium/Low | Auto | {选择理由} |
| ... | ... | ... | ... | ... | ... | ... |

### 2.2 非功能需求 (NFR)

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 自动化可行性 | 备注 |
|--------|---------|---------|---------|--------|-------------|------|
| NFR-001 | {摘要} | {场景} | PERF | {优先级} | Auto | {阈值说明} |
| ... | ... | ... | ... | ... | ... | ... |

### 2.3 接口需求 (IFR)

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 自动化可行性 | 备注 |
|--------|---------|---------|---------|--------|-------------|------|
| IFR-001 | {摘要} | {场景} | FUNC,BNDRY | {优先级} | Auto | {协议/格式说明} |
| ... | ... | ... | ... | ... | ... | ... |

### 2.4 覆盖统计

| 类别 | 需求数 |
|------|--------|
| FUNC | N |
| BNDRY | N |
| SEC | N |
| PERF | N |
| UI | N |
| Manual | N |
| **合计** | **N** |

> `自动化可行性` 列取值（可选 —— 若省略，所有场景默认为 `Auto`）：
> - `Auto` —— 标准测试工具可执行并验证（CLI、API、Chrome DevTools MCP）
> - `Manual: physical-device` —— 需要硬件访问（USB、打印机、IoT 设备）
> - `Manual: visual-judgment` —— 需要超出自动化截图对比的人工视觉判断
> - `Manual: external-action` —— 需要外部人工动作（接收邮件、拨打电话、在第三方系统审批）
> - `Manual: other: {description}` —— 其他原因
>
> 被标记为 Manual 的场景会向下游 Feature-ST 透传为 `已自动化: No` + `手动测试原因`。
```

## 第 3 节：测试类别策略（Test Category Strategies）

```markdown
## 3. 测试类别策略

### 3.1 功能测试 (FUNC)
- 每个 FR 至少一个正常路径 + 一个异常路径场景
- {项目特定策略}

### 3.2 边界测试 (BNDRY)
- 边界值分析: {具体边界条件}
- 等价类划分: {分类标准}

### 3.3 安全测试 (SEC)
- 输入验证: {SQL注入, XSS, 路径遍历等}
- 认证/授权: {绕过测试, 权限提升}
- 数据泄露: {敏感数据暴露检测}

### 3.4 性能测试 (PERF)
- 测试工具: {k6/locust/ab/JMeter等}
- 负载模型: {并发数, 持续时间, 渐进策略}

### 3.5 UI 测试 (UI)
- 工具: Chrome DevTools MCP
- 交互链: navigate → interact → verify → three-layer detection
- 三层检测模型: Layer 1 (evaluate_script), Layer 2 (EXPECT/REJECT), Layer 3 (list_console_messages)
```

## 第 4 节：NFR 测试方法矩阵（NFR Test Method Matrix）

```markdown
## 4. NFR 测试方法矩阵

| NFR ID | 测试方法 | 工具 | 通过标准 | 负载参数 | 关联 Feature |
|--------|---------|------|---------|---------|-------------|
| NFR-001 | {方法} | {工具} | {标准} | {参数} | Feature N, M |
| ... | ... | ... | ... | ... | ... |
```

## 第 5 节：跨 Feature 集成场景（Cross-Feature Integration Scenarios）

```markdown
## 5. 跨 Feature 集成场景

| 场景 ID | 场景描述 | 涉及 Features | 数据流路径 | 验证要点 | ST 阶段覆盖 |
|---------|---------|--------------|-----------|---------|------------|
| INT-001 | {描述} | F1, F2, FN | {路径} | {要点} | System ST |
| ... | ... | ... | ... | ... | ... |
```

## 第 6 节：风险驱动测试优先级（Risk-Driven Test Priority）

```markdown
## 6. 风险驱动测试优先级

### 6.1 风险评估矩阵

| 风险区域 | 风险级别 | 影响范围 | 测试深度 | 依据 |
|---------|---------|---------|---------|------|
| {区域} | Critical/High/Medium/Low | {范围} | 深度/标准/轻量 | {理由} |
| ... | ... | ... | ... | ... |

### 6.2 测试深度定义

| 深度 | 含义 |
|------|------|
| 深度 | 所有必须类别 + 额外探索性测试 |
| 标准 | 所有必须类别 |
| 轻量 | FUNC + BNDRY 仅 |
```

## 附录：审核报告（Review Report）

```markdown
## 附录: ATS 审核报告

{审核报告内容 — 由 ats-reviewer subagent 生成，在 ATS 通过审核后附加}
```

---

## 类别定义（参考）

| Category | Abbrev | 说明 | 何时必需 |
|----------|--------|-------------|---------------|
| `functional` | FUNC | 正常路径与错误路径验证 | 始终 —— 每个 FR |
| `boundary` | BNDRY | 边界情况、上限、空值/最大值/零值 | 始终 —— 每个 FR |
| `security` | SEC | 注入、授权、数据校验 | FR 涉及用户输入、认证或外部数据时 |
| `performance` | PERF | 响应时间、吞吐、资源占用 | 包含性能指标的 NFR-xxx |
| `ui` | UI | Chrome DevTools MCP 交互与视觉验证 | feature 带 `"ui": true` |

## 最小用例数经验值（参考）

| 需求复杂度 | 验收准则数 | 最小用例数 |
|------------------------|--------------------------|---------------|
| 简单 | 1-2 | 3-5 |
| 中等 | 3-4 | 5-8 |
| 复杂 | 5+ | 8-15 |
| 带指标的 NFR | 任意 | 3-5 |
