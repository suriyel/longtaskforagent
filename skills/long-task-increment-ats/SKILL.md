---
name: long-task-increment-ats
description: "Use when dispatched by long-task-increment Step 4b — revise ATS mapping table in place for new/modified/deprecated requirements and §6.2 contract changes"
---

# 增量 ATS 修订

## 自适应跳过

若 `docs/plans/*-ats.md` 不存在 → 直接返回：
```
**status**: pass
**artifacts_written**: []
**next_step_input**: {"skipped": true, "reason": "No ATS document exists"}
**evidence**: ["ATS skip: file not found"]
```

## 步骤

1. 读 `docs/plans/*-ats.md`
2. 对 prompt 中的 `new_reqs` 每条：

   **新增**：
   - 新增映射表行（需求 ID、场景、所需分类）
   - 应用分类规则：所有 FR → FUNC+BNDRY；输入/鉴权 +SEC；`ui:true` +UI；有指标 NFR +PERF
   - 更新覆盖率统计（§2.4）
   - 新 NFR → 在 NFR Test Method Matrix (§4) 新增行
   - 新跨特性交互 → 在集成场景 (§5) 新增行

   **修改**：
   - 原地更新映射表行（场景、分类）
   - 阈值变化 → 调整 NFR 测试方法
   - 数据流变化 → 更新集成场景

   **弃用**：
   - 映射表行加 `[DEPRECATED - Wave N]` 标记；**不删除**
   - 覆盖率统计从总量中排除已弃用行

3. 对 prompt 中的 `new_contracts` / `modified_contracts`：
   - 新契约：每条至少 1 happy-path + 1 error 集成场景
   - 修改契约：更新对应集成场景
4. 风险画像变化 → 更新 Risk-Driven Test Priority

## 再评审判定

在返回前判定 `needs_reviewer_rerun`：
- 变更影响 >3 行映射表行 → true
- 引入此前不存在的新测试分类 → true
- 否则 false

## 返回

```markdown
## SubAgent Result: long-task-increment-ats

**status**: pass
**artifacts_written**: ["docs/plans/<name>-ats.md"]
**next_step_input**: {
  "mapping_rows_added": 4,
  "mapping_rows_modified": 2,
  "mapping_rows_deprecated": 1,
  "new_categories": ["PERF"],
  "new_integration_scenarios": 3,
  "needs_reviewer_rerun": true
}
**blockers**: []
**evidence**: [
  "Coverage statistics updated: 20 → 23 active reqs, 1 deprecated",
  "NFR Test Method Matrix: +1 PERF row (FR-022 latency ≤ 200ms)",
  "Integration scenarios: +3 for C-017, ~1 for C-003 Breaking"
]
```

## 阻塞 / 失败

- prompt 中的契约 ID 在 §5 找不到对应集成场景位置 → `blocked`
- 映射表 markdown 结构损坏（列数不匹配） → `fail`

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 删除弃用行 | 加 `[DEPRECATED - Wave N]` 保留可追溯性 |
| 跳过新契约的 error 场景 | 每契约至少 happy + error 两场景 |
| 主 agent 前置判断 ATS 存在 | sub-skill 内部自适应跳过 |
