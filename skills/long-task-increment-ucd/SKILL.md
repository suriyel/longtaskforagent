---
name: long-task-increment-ucd
description: "Use when dispatched by long-task-increment Step 5 — revise UCD style guide in place for new/modified/deprecated UI requirements"
---

# 增量 UCD 修订

## 自适应跳过

任一成立则跳过，返回：
```
**status**: pass
**artifacts_written**: []
**next_step_input**: {"skipped": true, "reason": "<reason>"}
```

- `docs/plans/*-ucd.md` 不存在 → reason: "No UCD document"
- prompt 中的 `ui_reqs` 为空（无新增/修改/弃用 UI 需求） → reason: "No UI requirements in this wave"

## 步骤

1. 读 `docs/plans/*-ucd.md`
2. 对 `ui_reqs` 每条：

   **新增**：
   - 新 UI 组件 → 新增组件提示
   - 新页面 → 新增页面提示
   - 设计语言需扩展 → 更新 style tokens

   **修改**：
   - 原地更新对应组件/页面提示

   **弃用**：
   - 对应提示加 `[DEPRECATED - Wave N]` 标记；**不删除**

## 返回

```markdown
## SubAgent Result: long-task-increment-ucd

**status**: pass
**artifacts_written**: ["docs/plans/<name>-ucd.md"]
**next_step_input**: {
  "components_added": ["OrderSummaryCard", "TraceIdBadge"],
  "components_modified": ["UserProfileHeader"],
  "components_deprecated": ["LegacyLoginForm"],
  "tokens_changed": ["color.trace", "spacing.lg"]
}
**blockers**: []
**evidence**: [
  "UCD components: +2, ~1, deprecated 1",
  "Style tokens: +1 color, ~1 spacing"
]
```

## 阻塞 / 失败

- 新组件名与现有组件重名 → `blocked`，blocker 附重名列表
- UCD markdown 结构损坏 → `fail`
