# 对齐校验执行协议

## E10a. 根因可追溯性

对 Pain Map（SRS §1.3）**每一行**：
1. 在 §4 找到至少一条 EARS 或 AC 处理此痛点的 FR
2. 若某痛点无对应 FR → 检查是否显式出现在 §1.2 Out-of-Scope 且给出排除原因
3. 既未处理也未排除 → **追溯性缺口**

对 5-Whys Root Cause：
1. 确认至少一条 FR 直接处理根因（非仅症状）
2. 根因未被处理 → 标记为追溯性缺口

**缺口分流**：
- 1–2 条 → 自解：新增一条最小化 FR **或** 新增显式 Out-of-Scope 条目（择所需变更更小者）→ 写入 `new_requirements`
- ≥3 条 → 阻塞：缺口表进 `blockers`，主 agent 驱动用户决定"逐项转 FR 还是转 EXC"

## E10b. JTBD 结果验证

定位 E1 产生的 JTBD 陈述（SRS §1.3）。

检查："如果用户完成 §4 全部 Must 优先级 FR，是否达成 JTBD 的 'so I can [outcome]'？"

- **YES** → PASS
- **NO** → 识别 JTBD 结果中未覆盖方面 → 阻塞：未覆盖方面进 `blockers`，主 agent 驱动用户选择"新增 FR"或"确认 PARTIAL"

**可接受结果**：
- **PASS** — JTBD 完全可达
- **PARTIAL** — 仅当主 agent 回传用户确认"当前范围足够"时允许；sub-skill 自身不得直接裁定 PARTIAL

**关卡**：裁决非 PASS 且未有用户确认 → `status: blocked`。

## E10c. Pre-Mortem

自我评估："如果我们完全按 SRS 写的去建，用户仍可能不满意的是什么？"

对照检查：
- E2 workaround 回答 — 每个令人沮丧的步骤是否有 FR 处理？
- E3 走查流程缺口 — 所有提取到的缺口是否都在最终 FR 列表中？
- E6 隐藏需求 YES 回答（PII / 无障碍 / i18n / 安全）— 每个是否都变成显式 NFR？
- Pain Map 条目 — 是否存在只部分处理（变通流程被消除但根因仍在）？

对每个 pre-mortem 发现：
- 应为 FR → 新增（写入 `new_requirements`，type=FR）
- 应为 NFR → 新增（写入 `new_requirements`，type=NFR）
- 已知风险但当前不可执行 → 写入 `open_questions`

## E10d. 孤儿 FR 检测

对 §4 每条 FR 检查来源：
- 关联 Pain Map 某行
- 关联 JTBD 结果
- 来自 E3 走查步骤
- 来自 E6 隐藏需求探针

**无任何可追溯来源**的 FR：
- 检查是否有其他 FR 依赖它（基础设施 / 工具类 FR 常无直接痛点关联）
- 无依赖 → 写入 `open_questions`：`"FR-xxx has no traceable pain point or JTBD link — confirm in scope or defer to a future increment."`

**不得**自动移除孤儿 FR。

## 输出

生成 `alignment_summary_text` 字符串（供主 agent 后续写入 SRS §1.3）：

```
Alignment Validation: PASS | PARTIAL | FAIL
- Root cause coverage: N of M pain points addressed
- JTBD outcome: achieved | partially achieved (user-confirmed) | not achieved
- Pre-mortem findings: N items added | 0 items found
- Orphan FRs flagged: N items in Open Questions | 0
```

**PASS / PARTIAL / FAIL 判定**：
- PASS：E10a 缺口全部自解 + E10b JTBD = PASS + E10d 孤儿已进 Open Questions
- PARTIAL：仅在 blocker → 主 agent 获用户确认后重分发时可得
- FAIL：E10b JTBD 未达且无用户确认 → 永远伴随 `status: blocked`，不独立出现
