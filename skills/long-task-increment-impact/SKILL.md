---
name: long-task-increment-impact
description: "Use when dispatched by long-task-increment Step 3 — build impact matrix and API-compat table from new/modified/deprecated requirements"
---

# 增量影响评估

## 步骤

1. 读 `feature-list.json`，构建反向依赖图 `{feature_id: [consumers]}`
2. 读 `docs/plans/*-design.md` §6.2 Internal API Contracts 表
3. 加载 `skills/long-task-increment/references/brownfield-adaptation.md` §D
4. 对 prompt 中的 `new_reqs` 每条：
   - **NEW**：识别依赖的既有特性（通常无 Hard Impact）
   - **MODIFY / EXTEND**：通过 `affects_req_id` 反查 `srs_trace` 包含该 ID 的特性（直接受影响）
   - **DEPRECATED**：同上反查；这些特性将被 deprecate
5. 传递级联（BFS 深度 ≤ 2）：
   - **Hard**：契约签名变化（Breaking 或 MODIFY §6.2）→ 消费者重新实现
   - **Soft**：契约未变 → 消费者仅回归
6. 构建 API 影响 + 兼容性表（依 brownfield-adaptation.md §D）：
   - 每行含 file:line 或完整签名
   - 变更类型：NEW / MODIFY / EXTEND
   - 兼容策略：Additive / Deprecated / Breaking
   - **Breaking 行的 impact_features 必须全部进入 Hard Impact**
   - 纯新增增量也要填一行 "N/A — 无存量 API 修改"

## 返回

```markdown
## SubAgent Result: long-task-increment-impact

**status**: pass
**artifacts_written**: []
**next_step_input**: {
  "impact_matrix": [
    {"change": "FR-021", "type": "NEW", "affected": [], "action": "Add feature(s)"},
    {"change": "FR-005", "type": "MODIFY", "affected": [{"id": 5, "level": "Hard"}, {"id": 8, "level": "Soft"}], "action": "Feature 5 reset; Feature 8 regression"},
    {"change": "FR-012", "type": "DEPRECATED", "affected": [{"id": 12}], "action": "Mark deprecated"}
  ],
  "api_changes": [
    {"sig": "UserService.findById(id) → findById(id, tenantId)",
     "location": "src/services/UserService.java:L42",
     "change_type": "MODIFY", "strategy": "Breaking",
     "impact_features": [1, 5, 12]}
  ],
  "hard_impact_ids": [5],
  "soft_impact_ids": [8],
  "deprecated_ids": [12],
  "new_reqs_needing_features": ["FR-021"],
  "breaking_contracts": ["C-003"]
}
**blockers**: []
**evidence**: [
  "Reverse dependency graph: 12 nodes, 18 edges",
  "Hard 1 / Soft 1 / Deprecated 1",
  "API changes: 1 Breaking, 0 Additive, 0 N/A"
]
```

## 阻塞 / 失败

- Design §6.2 缺失 → `blocked`，blocker 指明需补 §6.2
- `affects_req_id` 在 SRS 中不存在 → `blocked`
- `feature-list.json` 解析失败 → `fail`，evidence 附解析错误
