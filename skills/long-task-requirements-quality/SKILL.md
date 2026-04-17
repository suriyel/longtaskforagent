---
name: long-task-requirements-quality
description: "Use when dispatched by long-task-requirements Step 7-11 — classify, write EARS, validate quality, size granularity, propose deferrals from raw elicitation outputs"
---

# 需求质量流水线

## 步骤

### A. 分类

把 prompt 中的 `raw_requirements` / `raw_nfrs` / `constraints` / `interfaces` / `exclusions` 分配到下列类别：

| 类别 | ID 前缀 |
|---|---|
| Functional | FR-001 |
| Non-Functional | NFR-001 |
| Constraint | CON-001 |
| Assumption | ASM-001 |
| Interface | IFR-001 |
| Exclusion | EXC-001 |

ID 在本次调用内连续递增。

### B. 用 EARS 模板撰写

对每条 FR 选一个模板：

| 模式 | 模板 |
|---|---|
| Ubiquitous | The system shall `<action>`. |
| Event-driven | When `<trigger>`, the system shall `<action>`. |
| State-driven | While `<state>`, the system shall `<action>`. |
| Unwanted behavior | If `<condition>`, then the system shall `<action>`. |
| Optional | Where `<feature/config>`, the system shall `<action>`. |

为每条 FR 附加：
- **验收标准**：≥1 个 Given/When/Then 场景
- **视觉输出**：UI 面向写"用户所见变化"一句；否则 "N/A — backend-only"
- **优先级**：MoSCoW（Must / Should / Could / Won't）
- **来源**：追溯到用户叙述 / walkthrough 步骤 / hidden-req 探针

对每条 NFR 必须带**可度量阈值**。

### C. 图表

- **Use Case 视图**（§3.1）：`graph LR`；每个角色 `Actor((Name))`；所有 FR 放在 `subgraph System Boundary` 内；按参与关系画有向边
- **流程图**（§4.1）：每个含 3+ 顺序步骤或分支的功能区一张 `flowchart TD`；Start/End 用 `([label])`；判定 `{condition?}` + `-- YES -->` / `-- NO -->`

生成 Mermaid 片段字符串数组，写入 `next_step_input.diagrams`。

### D. 质量校验

**D.1 逐需求 8 属性**

| # | 属性 | 红旗 |
|---|---|---|
| 1 | Correct | 孤立需求（无来源）|
| 2 | Unambiguous | "快"、"健壮"、"用户友好" |
| 3 | Complete | "包括但不限于……" |
| 4 | Consistent | 时序 / 格式冲突 |
| 5 | Ranked | 全部都是"高优先级" |
| 6 | Verifiable | "系统应易于使用" |
| 7 | Modifiable | 跨章节重复 |
| 8 | Traceable | 缺 ID 或孤立 |

**D.2 反模式**

| 反模式 | 修正 |
|---|---|
| 模糊形容词无数字 | 量化 |
| "and" / "or" 连接两项能力 | 拆分 |
| "class" / "table" / "endpoint" | 重写为行为 |
| 被动无主语 | 加入角色 |
| TBD / TBC | 解决或转 Open Question |
| 只规定正向情况 | 加入错误 / 边界 |
| NFR 无阈值 | 加入度量 |

**D.3 完备性交叉检查**

- 每个功能区域 ≥1 错误 / 边界情况
- 所有外部接口有数据格式 + 协议
- 所有 NFR 有度量方法
- 术语表覆盖所有领域术语
- Out-of-Scope 节列出延后特性

自动修复 D.1 / D.2 / D.3 中 LLM-FIXABLE 项（改写措辞、加默认 MoSCoW、补 Given/When/Then 骨架）。修复不了的进入 `quality_report.user_input_required[]`。

### E. 粒度分析

从 prompt 中读 `sizing_tier`：

| tier | 每 FR AC 目标 |
|---|---|
| `standard`（≤200K）| 3–12 |
| `extended`（>200K）| 5–20 |

**E.1 过大检测 G1–G6**：多角色 / CRUD 捆绑 / 场景爆炸（AC 超上限）/ 跨层关注 / 多状态 / 时序耦合 → 拆分候选（子 ID 加 a/b/c 后缀，保持 srs_trace）

**E.2 过小检测 S1–S4**：琐碎新增 / 单一断言 / 纯数据回显 / 仅 config setup → 合并候选（保留主 FR ID，描述注 "Incorporates: [...]"）

**E.3 决策阈值**：

| 候选数 | 动作 |
|---|---|
| 0 | 跳过 |
| 1–3 | 自动应用；rationale 写入 `granularity_candidates.auto_applied[]` |
| 4+ | **不自动应用**；全部进 `granularity_candidates.user_input_required[]`，主 agent 驱动审批 |

合并规则：合并后 AC ≤20（超了重触发 G3 拆分）；合并 FR 须共享主角色与功能区域；同一 FR 同时触发 G 与 S 时 G 优先。

### F. 范围契合与延后

- Must 永不延后
- 依赖完整性：FR-X 依赖 FR-Y → 两者同进退
- 候选延后项进 `deferral_candidates[]`，保留 EARS + AC（供主 agent 后续交给 finalize 写 `*-deferred.md`）

### G. 组装 draft_sections

按 prompt 中 `srs_template_path` 读模板，把 A–F 产物填入对应章节，生成 `next_step_input.draft_sections`（JSON-like：`{section_id: content_markdown}`）。**不落盘**。

## 返回

```markdown
## SubAgent Result: long-task-requirements-quality

**status**: pass | fail | blocked
**artifacts_written**: []
**next_step_input**: {
  "draft_sections": {
    "1.1_purpose": "...",
    "2_scope": "...",
    "4_functional_requirements": "...",
    "5_nfr": "...",
    "6_constraints": "...",
    "7_interfaces": "...",
    "8_glossary": "...",
    "9_exclusions": "..."
  },
  "granularity_candidates": {
    "auto_applied": [
      {"fr": "FR-003", "heuristic": "G3", "action": "split into FR-003a, FR-003b", "rationale": "5 AC across 2 behaviors"}
    ],
    "user_input_required": [
      {"fr": "FR-007", "heuristic": "G1", "proposal": "split by role: admin vs user", "rationale": "..."}
    ]
  },
  "deferral_candidates": [
    {"fr": "FR-012", "priority": "Could", "rationale": "low dependency, non-Must"}
  ],
  "quality_report": {
    "fixed_automatically": 7,
    "user_input_required": [
      {"fr": "FR-005", "issue": "ambiguous threshold: '快速响应'", "prompt": "要求具体毫秒目标"}
    ]
  },
  "diagrams": ["graph LR\n  ...", "flowchart TD\n  ..."],
  "counts": {"fr": 14, "nfr": 6, "con": 3, "asm": 4, "ifr": 2, "exc": 1}
}
**blockers**: []
**evidence**: [
  "Classified 14 FR + 6 NFR from 18 raw items",
  "Quality: 7 fixed automatically, 1 user-input required",
  "Granularity: 1 auto-applied (G3), 1 user-input required (G1); 0 S heuristics",
  "Deferral: 1 candidate (Could priority)"
]
```

## 阻塞 / 失败

- `sizing_tier` 不是 `standard` / `extended` → `blocked`，blocker 指明需主 agent 重传
- `raw_requirements` 为空 或 `roles` 为空 → `blocked`
- `srs_template_path` 无法读取 → `fail`，evidence 附文件系统错误
- FR 数量 > 200 → `fail`，evidence 指示 sizing 不合适，需主 agent 调整输入粒度

## 反模式

| Anti-Pattern | Correct |
|---|---|
| sub-skill 内直接 AskUserQuestion | 全部进 `user_input_required`，主 agent 驱动 |
| 4+ G/S 候选自动应用 | 必须进 `user_input_required` |
| Must 优先级进 `deferral_candidates` | Must 永不延后 |
| draft_sections 写入磁盘 | 过程量，仅 next_step_input；finalize 才落盘 |
| 修改既有 FR ID 编号 | ID 在本次调用内连续递增；不重排 |
