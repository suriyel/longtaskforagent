# Acceptance Test Strategy (ATS) Template

> This template defines the structure for the global Acceptance Test Strategy document.
> The LLM generates ATS content following this structure.
> Users may override this template via `ats_template_path` in `feature-list.json` (or specify it during the ATS phase).
> Users may also provide a style/language example via `ats_example_path`.

---

## Document Header

```markdown
# 验收测试策略: {project_title}

**SRS 参考**: {srs_path}
**设计文档参考**: {design_path}
**UCD 参考**: {ucd_path or "N/A"}
**日期**: {YYYY-MM-DD}
**状态**: Draft / Approved
**模板版本**: 1.0
```

## Section 1: Test Scope & Strategy Overview

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

## Section 2: Requirement → Acceptance Scenario Mapping (Core)

```markdown
## 2. 需求→验收场景映射

### 2.1 功能需求 (FR)

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 备注 |
|--------|---------|---------|---------|--------|------|
| FR-001 | {摘要} | {场景1/场景2/...} | FUNC,BNDRY,{+其他} | Critical/High/Medium/Low | {选择理由} |
| ... | ... | ... | ... | ... | ... |

### 2.2 非功能需求 (NFR)

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 备注 |
|--------|---------|---------|---------|--------|------|
| NFR-001 | {摘要} | {场景} | PERF | {优先级} | {阈值说明} |
| ... | ... | ... | ... | ... | ... |

### 2.3 接口需求 (IFR)

| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 备注 |
|--------|---------|---------|---------|--------|------|
| IFR-001 | {摘要} | {场景} | FUNC,BNDRY | {优先级} | {协议/格式说明} |
| ... | ... | ... | ... | ... | ... |

### 2.4 覆盖统计

| 类别 | 需求数 |
|------|--------|
| FUNC | N |
| BNDRY | N |
| SEC | N |
| PERF | N |
| UI | N |
| **合计** | **N** |
```

## Section 3: Test Category Strategies

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

## Section 4: NFR Test Method Matrix

```markdown
## 4. NFR 测试方法矩阵

| NFR ID | 测试方法 | 工具 | 通过标准 | 负载参数 | 关联 Feature |
|--------|---------|------|---------|---------|-------------|
| NFR-001 | {方法} | {工具} | {标准} | {参数} | Feature N, M |
| ... | ... | ... | ... | ... | ... |
```

## Section 5: Cross-Feature Integration Scenarios

```markdown
## 5. 跨 Feature 集成场景

| 场景 ID | 场景描述 | 涉及 Features | 数据流路径 | 验证要点 | ST 阶段覆盖 |
|---------|---------|--------------|-----------|---------|------------|
| INT-001 | {描述} | F1, F2, FN | {路径} | {要点} | System ST |
| ... | ... | ... | ... | ... | ... |
```

## Section 6: Risk-Driven Test Priority

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

## Appendix: Review Report

```markdown
## 附录: ATS 审核报告

{审核报告内容 — 由 ats-reviewer subagent 生成，在 ATS 通过审核后附加}
```

---

## Category Definitions (Reference)

| Category | Abbrev | Description | When Required |
|----------|--------|-------------|---------------|
| `functional` | FUNC | Happy-path and error-path verification | Always — every FR |
| `boundary` | BNDRY | Edge cases, limits, empty/max/zero values | Always — every FR |
| `security` | SEC | Injection, authorization, data validation | FR handles user input, auth, or external data |
| `performance` | PERF | Response time, throughput, resource usage | NFR-xxx with performance metrics |
| `ui` | UI | Chrome DevTools MCP interaction + visual verification | Feature has `"ui": true` |

## Minimum Case Count Heuristics (Reference)

| Requirement Complexity | Acceptance Criteria Count | Minimum Cases |
|------------------------|--------------------------|---------------|
| Simple | 1-2 | 3-5 |
| Medium | 3-4 | 5-8 |
| Complex | 5+ | 8-15 |
| NFR with metrics | Any | 3-5 |
