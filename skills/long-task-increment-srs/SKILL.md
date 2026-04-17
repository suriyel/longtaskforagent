---
name: long-task-increment-srs
description: "Use when dispatched by long-task-increment Step 6 — update SRS in place, backfill §1.4 ESI, append/modify/deprecate features in feature-list.json, validate"
---

# 增量 SRS 与特性分解

## 步骤

### A. SRS 原地更新

1. 读 `docs/plans/*-srs.md`
2. 对 prompt 中的 `new_reqs` 每条：
   - **新增** → 追加到对应章节（FR / NFR / ...）；ID 连续
   - **修改** → 原地改文本，加注释 `<!-- Wave N: Modified YYYY-MM-DD — <reason> -->`
   - **弃用** → 前缀 `[DEPRECATED - Wave N: <reason>]`；**不删除**
3. 若存在追溯矩阵 → 更新
4. **回填 §1.4 Existing System Context**（依 `skills/long-task-increment/references/brownfield-adaptation.md` §F）：
   - 变更类型分布（NEW/MODIFY/EXTEND/REUSE 数量）
   - ESI 已确立维度 + 复用的横切关注点及其 ASM-xxx ID
   - 1-3 句变更摘要
   - 受影响模块 / 未受影响模块

### B. feature-list.json 更新

1. 读 `feature-list.json`
2. 根据 prompt 中的 `impact_matrix` 与 `new_reqs_needing_features`：

   **新特性**：追加到 `features[]`：
   - `id`：当前最大 + 1（持续递增）
   - `wave`：当前批次号
   - `status`：`"failing"`
   - `srs_trace`：新需求 ID 数组
   - `verification_steps`：可选（来自新验收标准）
   - `dependencies`：按需
   - `ui` / `ui_entry`：按需

   **Hard Impact 特性**（来自 impact_matrix）：
   - `status` 重置为 `"failing"`
   - 更新 `srs_trace` 反映修订后 ID
   - `wave` 更新为当前批次
   - 若出现在 `api_changes[].impact_features` → 在 description 加注 `[Wave N API change — <strategy>]`

   **Soft Impact 特性**：仅更新 `wave` 标识被影响批次；`status` 保持（仅回归）

   **Deprecated 特性**：
   - `deprecated: true`
   - `deprecated_reason: "<reason>"`
   - status 保持

   **替代（弃用 + 新增替代）**：新特性设 `supersedes: <deprecated_feature_id>`

3. 更新根级 `waves[]`：
   ```json
   {"id": N, "date": "YYYY-MM-DD", "description": "<from increment-request.json>"}
   ```
4. 新 CON/ASM 条目 → 更新 `constraints[]` / `assumptions[]`
5. 新配置项 → 更新 `required_configs[]`

### C. 校验

运行 `python scripts/validate_features.py feature-list.json`：
- 退出码 0 → `status: pass`，evidence 附 "validate_features.py: OK"
- 非 0 → `status: fail`，evidence 附完整 stderr，artifacts_written 仍列出已写文件（主 agent 可据此返工）

## 返回

```markdown
## SubAgent Result: long-task-increment-srs

**status**: pass | fail
**artifacts_written**: ["docs/plans/<name>-srs.md", "feature-list.json"]
**next_step_input**: {
  "new_feature_ids": [21, 22],
  "modified_feature_ids": [5],
  "soft_touched_feature_ids": [8],
  "deprecated_feature_ids": [12],
  "wave": 3,
  "esi_backfill_lines": 8
}
**blockers**: []
**evidence**: [
  "SRS: +2 FR, ~1 FR, deprecated 1 FR; §1.4 backfilled (8 lines)",
  "feature-list.json: +2 features, 1 reset to failing, 1 deprecated",
  "validate_features.py: OK"
]
```

## 阻塞 / 失败

- `feature-list.json` schema 违规 → `fail`，evidence 附 validate_features.py stderr
- prompt 中 `impact_matrix` 引用的 feature ID 在 `feature-list.json` 中不存在 → `blocked`
- SRS 中找不到 MODIFY/DEPRECATED 引用的原需求 ID → `blocked`

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 删除弃用需求 / 特性 | 用 `[DEPRECATED]` 标记 + `deprecated: true` 字段保留 |
| 复用已弃用 ID 给新特性 | ID 永远递增 |
| 跳过 §1.4 回填 | 下游 Worker 会把增量当新项目构建；§1.4 是硬要求 |
| 跳过 validate_features.py | 校验失败才能在 fail 状态触发 revise 循环 |
