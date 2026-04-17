---
name: long-task-requirements-alignment
description: "Use when dispatched by long-task-requirements Expert E10 — alignment validation: root-cause traceability, JTBD verification, pre-mortem, orphan FR detection"
---

# 一致性校验（Expert E10）

加载 `references/alignment-validation.md` 作为完整执行协议。本 SKILL.md 定义如何把该协议的产物映射为 Structured Return Contract。

## 步骤

### A. 准备输入

从 prompt 读：`pain_map`、`jtbd`、`workarounds`、`walkthrough_findings`、`hidden_reqs_yes_answers`、`fr_list`、`nfr_list`。

### B. 执行 4 项校验

依 `references/alignment-validation.md` §E10a–E10d 顺序执行：

| 阶段 | 名称 | 输出 |
|---|---|---|
| E10a | 根因可追溯性 | 每条 Pain Map 行 + 5-Whys Root Cause 的覆盖状态；缺口清单 |
| E10b | JTBD 结果验证 | PASS / PARTIAL / FAIL 裁决；未覆盖方面清单 |
| E10c | Pre-mortem | 可自解的 FR/NFR 新增项；风险转 Open Questions |
| E10d | 孤儿 FR 检测 | 无来源 FR 清单；不自动移除 |

**sub-skill 禁止发起 AskUserQuestion**。原协议中"用户干预"的分支改为下列返回规则（见步骤 C）。

### C. 分流：自解 vs 阻塞

**自解（生成 `new_requirements[]`）**：
- E10a 追溯性缺口 ≤2 条 → 为每个缺口生成 1 条最小化 FR 或建议 EXC 条目
- E10c Pre-mortem 发现明确属于 FR / NFR 类型的补漏项

**阻塞（status: blocked + blockers[]）**：
- E10a 追溯性缺口 ≥3 条 → blockers 列出缺口表，要求主 agent 让用户决定"每项转 FR 还是转 EXC"
- E10b JTBD 结果 = FAIL 且无法从现有 FR 推导 → blockers 附缺失方面，要求主 agent 让用户决定"新增 FR 还是确认 PARTIAL"

**Open Questions（进 `open_questions[]`，不阻塞）**：
- E10d 孤儿 FR（无依赖者、无可追溯来源）
- E10b PARTIAL 裁决（需主 agent 后续向用户确认后记入 §11）

### D. 生成 alignment_summary_text

组装供 SRS §1.3 "Alignment Validation" 字段使用的字符串：

```
Alignment Validation: PASS | PARTIAL | FAIL
- Root cause coverage: N of M pain points addressed
- JTBD outcome: achieved | partially achieved (user-confirmed) | not achieved
- Pre-mortem findings: N items added | 0 items found
- Orphan FRs flagged: N items in Open Questions | 0
```

**PASS 条件**：E10a 缺口 ≤2 已自解 + E10b 为 PASS 或 PARTIAL（主 agent 已确认）+ E10d 孤儿已进 Open Questions。
**FAIL 条件**：E10b = FAIL 且未经主 agent 确认 → 返回 blocked。

## 返回

```markdown
## SubAgent Result: long-task-requirements-alignment

**status**: pass | blocked
**artifacts_written**: []
**next_step_input**: {
  "alignment_report": {
    "root_cause_coverage": {"addressed": 6, "total": 7, "gaps_resolved": 1},
    "jtbd_verdict": "PASS",
    "pre_mortem_additions": 2,
    "orphan_frs": ["FR-014"]
  },
  "alignment_summary_text": "Alignment Validation: PASS\n- Root cause coverage: 7 of 7 pain points addressed\n- JTBD outcome: achieved\n- Pre-mortem findings: 2 items added\n- Orphan FRs flagged: 1 item in Open Questions",
  "new_requirements": [
    {"type": "FR", "ears": "When X, the system shall Y.", "ac": "Given ... When ... Then ...", "source": "E10a gap: Pain-3", "priority": "Should"}
  ],
  "open_questions": [
    "FR-014 has no traceable pain point or JTBD link — confirm in scope or defer to a future increment."
  ]
}
**blockers**: []
**evidence**: [
  "E10a: 7 pain points checked, 1 gap auto-resolved via new FR",
  "E10b JTBD: PASS — all Must-priority FRs collectively achieve stated outcome",
  "E10c Pre-mortem: 2 additions (1 FR, 1 NFR)",
  "E10d Orphan detection: 1 FR flagged (FR-014), retained in Open Questions"
]
```

## 阻塞 / 失败

- E10a 缺口 ≥3 → `blocked`，blockers 附 gap 表 + 建议选项（转 FR / 转 EXC）
- E10b JTBD = FAIL 且无可推导 → `blocked`，blockers 附未覆盖方面 + 建议选项
- `pain_map` 或 `jtbd` 缺失 → `blocked`，blockers 指明主 agent 需从 E1 产物补齐
- `fr_list` 为空 → `fail`

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 自动移除孤儿 FR | 仅进 `open_questions`，由主 agent / 用户决定 |
| 自解缺口数 ≥3 | ≥3 必须 blocked，让用户决定 |
| sub-skill 内 AskUserQuestion | 所有需用户输入场景转 `blockers` |
| PARTIAL 当作 PASS 返回 | PARTIAL 必须经主 agent 向用户确认；未确认 = FAIL = blocked |
