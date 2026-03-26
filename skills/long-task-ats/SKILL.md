---
name: long-task-ats
description: "Use when design doc exists but no ATS doc and no feature-list.json - generate a global Acceptance Test Strategy mapping every requirement to acceptance scenarios with category constraints"
---

# Acceptance Test Strategy (ATS) Generation

Take the approved SRS, Design, and UCD (if applicable) as input. Produce a global Acceptance Test Strategy document that maps every requirement to acceptance scenarios with required test categories — constraining downstream feature-st (test case derivation via srs_trace).

**Announce at start:** "I'm using the long-task-ats skill to generate the Acceptance Test Strategy."

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, run init_project.py, or take any implementation action until the ATS document is approved. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Why ATS Exists

Without a global acceptance test strategy, per-feature ST test cases suffer from:
- Category imbalance (heavy FUNC/BNDRY, near-zero SEC/PERF/UI)
- NFR test methods decided ad-hoc during feature-st
- Cross-feature integration scenarios discovered too late in ST phase
- Risk-based test prioritization missing entirely

ATS front-loads these decisions so Init and feature-st have concrete, auditable constraints.

## Scaling Guide

| Project Size | Features | ATS Depth |
|---|---|---|
| Tiny | 1-5 | **Skip standalone ATS** — embed a simplified mapping table in the design doc's Testing Strategy section (section 7); router detects `*-ats.md` absence + ≤5 features → auto-skip to Init |
| Small | 5-15 | Lightweight standalone ATS — sections 1-3 only (scope, mapping table, category strategies); skip sections 4-6 |
| Medium | 15-50 | Full ATS document — all 6 sections |
| Large | 50-200+ | Full ATS + detailed per-subsystem integration matrices + risk heat map |

**Auto-skip rule for Tiny projects**: If the design document exists and the SRS has ≤ 5 functional requirements (FR-xxx), this skill embeds the ATS mapping table into the design doc's testing strategy section and creates a minimal `docs/plans/*-ats.md` stub containing only a reference to that section. The router then detects the ATS stub and proceeds to Init.

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Read Input Documents

1. Read the approved SRS document from `docs/plans/*-srs.md`
2. Read the approved design document from `docs/plans/*-design.md`
3. Read the approved UCD style guide from `docs/plans/*-ucd.md` (if it exists — only for UI projects)
4. Check for a custom ATS template:
   - If user has specified a template path → read and validate it
   - Else → use default template at `docs/templates/ats-template.md`
5. Check for a custom ATS example:
   - If user has specified an example path → read the example file — adapt style, language, and detail level
6. Check for a custom ATS review template:
   - If user has specified a review template path → read it for use in Step 8
   - Else → use default review template at `docs/templates/ats-review-template.md`

### 2. Extract All Requirements

From the SRS, extract a complete list of:
- **FR-xxx**: Functional Requirements — with acceptance criteria (Given/When/Then)
- **NFR-xxx**: Non-Functional Requirements — with measurable thresholds
- **IFR-xxx**: Interface Requirements — with protocols and data formats
- **CON-xxx**: Constraints — hard limits
- **ASM-xxx**: Assumptions — implicit beliefs

Count FR-xxx requirements. If ≤ 5, apply the **Tiny project auto-skip** rule (see Scaling Guide above).

### 3. Generate Requirement → Acceptance Scenario Mapping

For each FR/NFR/IFR, generate one or more acceptance scenarios with:

```markdown
| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 备注 |
|--------|---------|---------|---------|--------|------|
| FR-001 | 用户登录 | 正常登录/错误密码/账户锁定/会话过期 | FUNC,BNDRY,SEC | Critical | 处理用户输入→SEC必选 |
| NFR-001 | 响应时间<200ms | P95延迟/并发负载/降级/冷启动 | PERF | High | 阈值: P95<200ms @100并发 |
| FR-010 | 搜索结果页 | 搜索/空结果/分页/排序/筛选 | FUNC,BNDRY,UI | High | ui:true→UI必选 |
```

**Category assignment rules:**

| 条件 | 必须类别 |
|------|---------|
| 所有 FR | FUNC + BNDRY（至少） |
| 处理用户输入/认证/授权/外部数据 | + SEC |
| 对应 `ui: true` 的 feature | + UI |
| 关联 NFR-xxx 且有性能指标 | + PERF |

### 4. Define Test Category Strategies

For each test category, specify the strategy:

- **FUNC**: Every FR must cover at least one happy-path + one error-path scenario
- **BNDRY**: Boundary value analysis + equivalence class partitioning requirements per FR
- **SEC**: Input validation (SQL injection, XSS, path traversal), authentication bypass, authorization escalation, data leakage
- **PERF**: NFR metric thresholds + load scenarios + tool specification + pass criteria
- **UI**: Chrome DevTools MCP interaction chains — navigate → interact → verify → three-layer detection

### 5. NFR Test Method Matrix

For each NFR-xxx with measurable thresholds:

```markdown
| NFR ID | 测试方法 | 工具 | 通过标准 | 负载参数 | 关联 feature |
|--------|---------|------|---------|---------|-------------|
| NFR-001 | Load test | k6/locust/ab | P95 < 200ms | 100 concurrent, 60s ramp | Feature 15, 16 |
| NFR-002 | Memory profiling | tracemalloc/heapdump | RSS < 512MB | 10K records | Feature 8 |
```

### 6. Cross-Feature Integration Scenarios

Identify critical data flow paths that span multiple features:

```markdown
| 场景 ID | 场景描述 | 涉及 Features | 数据流路径 | 验证要点 | ST 阶段覆盖 |
|---------|---------|--------------|-----------|---------|------------|
| INT-001 | 用户注册→登录→首次操作 | F1, F2, F5 | POST /register → POST /login → GET /dashboard | 会话传递、数据一致性 | System ST |
```

### 7. Risk-Driven Test Priority

Assess risk per requirement and assign test depth:

```markdown
| 风险区域 | 风险级别 | 影响范围 | 测试深度 | 依据 |
|---------|---------|---------|---------|------|
| 用户认证 | High | 全系统 | 深度 (SEC+FUNC+BNDRY) | 安全边界 |
| 数据导入 | Medium | Feature 3-5 | 标准 (FUNC+BNDRY) | 数据完整性 |
```

### 8. Section-by-Section User Approval

Present each section to the user for approval (same pattern as design skill):

1. Requirement → Scenario mapping table (Step 3)
2. Test category strategies (Step 4)
3. NFR test method matrix (Step 5) — skip if no NFRs with metrics
4. Cross-feature integration scenarios (Step 6)
5. Risk-driven priority (Step 7)

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For Small projects** (5-15 features): Combine into 2 approval steps: (a) mapping table + categories, (b) everything else.

### 9. Subagent Review

Dispatch the ATS reviewer subagent for independent quality review:

```
Agent(
  subagent_type="general-purpose",
  prompt="""
  You are an independent ATS reviewer.
  Read the reviewer prompt at: agents/ats-reviewer.md
  Read the review template at: {review_template_path}

  ## Input Documents
  - ATS document (draft): {ats_content}
  - SRS document: {srs_path} — read it
  - Design document: {design_path} — read it
  - UCD document (if applicable): {ucd_path} — read it

  ## Task
  Execute all review dimensions defined in the review template.
  Output a structured review report.
  Do NOT suggest improvements beyond defect identification.
  Do NOT read any implementation code — this is a requirements-level review.
  """
)
```

**Isolation guarantees:**
- Subagent reads ONLY ATS + SRS + Design + UCD + review template
- Subagent does NOT read implementation code or test code
- Subagent does NOT modify any files — returns structured report only
- Main skill processes the report and decides on fixes

### 10. Process Review Report

Parse the subagent's review report:

1. **0 Major defects** → PASS → proceed to Step 11
2. **Has Major defects** → fix the ATS document per defect descriptions → re-run Step 9 (max 2 review rounds)
3. **Third round still FAIL** → present full report to user via `AskUserQuestion`:
   - Show all remaining Major defects
   - Options: fix manually / accept with known gaps / terminate
   - If user accepts with gaps: document gaps in ATS footer section

### 11. Save ATS Document

1. Save the approved ATS to `docs/plans/YYYY-MM-DD-<topic>-ats.md`
2. Append the final review report as an appendix section
3. Git commit:
   ```
   docs: add acceptance test strategy (ATS)

   Maps N requirements to acceptance scenarios
   Categories: FUNC, BNDRY, SEC, PERF, UI
   Reviewed: [PASS / CONDITIONAL PASS with N gaps]
   ```

### 12. Transition to Initializer

Once the ATS document is saved and committed:

1. Summarize key inputs the Initializer will need:
   - **From SRS**: requirements, acceptance criteria → features
   - **From Design**: tech stack, architecture → project skeleton
   - **From ATS**: category constraints → feature-st test case category requirements (via srs_trace)
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-init` to scaffold the project

## Boundary with Design Doc Testing Strategy

The **design doc** (Section 7, Testing Strategy) describes the *approach*:
- What test types will be used (unit, integration, E2E)
- What tools and frameworks (pytest, k6, Chrome DevTools MCP)
- What coverage targets (line 90%, branch 80%, mutation 80%)

The **ATS document** describes the *detailed mapping*:
- Which specific requirement gets which specific test categories
- NFR test methods with exact thresholds and load parameters
- Cross-feature integration scenarios
- Risk-driven test depth

The design doc testing strategy section SHOULD reference the ATS document once it exists:
```markdown
See `docs/plans/YYYY-MM-DD-<topic>-ats.md` for detailed requirement-to-test-category mapping.
```

## Critical Rules

- **Requirements-driven**: Every mapping row traces to a specific SRS requirement ID
- **No orphan requirements**: Every FR/NFR/IFR must appear in the mapping table
- **Category assignment is auditable**: Every required category has a documented reason
- **Review is mandatory**: ATS reviewer subagent runs before save — no skip
- **Scaling applies**: Tiny projects (≤5 FR) skip standalone ATS; see Scaling Guide
- **Immutable after approval**: Changes to ATS require the `long-task-increment` skill (ATS Revision step)

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "The SRS already has acceptance criteria, ATS is redundant" | SRS has business criteria; ATS maps them to test categories |
| "We'll figure out test categories during feature-st" | Ad-hoc category assignment leads to SEC/PERF gaps |
| "This project is too small for ATS" | Check Scaling Guide — Tiny projects auto-skip; Small projects get lightweight ATS |
| "NFR testing can be decided during ST phase" | NFR test methods must be specified upfront with tools and thresholds |
| "The review is overkill" | Independent review catches coverage gaps the author misses |

## Integration

**Called by:** using-long-task (when design doc exists, no ATS doc, no feature-list.json) or long-task-design (Step 6)
**Requires:** Approved SRS at `docs/plans/*-srs.md`; Approved Design at `docs/plans/*-design.md`; optionally approved UCD at `docs/plans/*-ucd.md`
**Chains to:** long-task-init (after ATS approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-ats.md`
**Downstream consumers:**
- `long-task-init` — reads ATS to set `ui` flags based on category assignment
- `long-task-feature-st` — reads ATS to enforce category requirements (via srs_trace lookup)
- `long-task-st` — uses ATS as baseline for RTM verification
- `long-task-increment` — updates ATS in place when requirements change
