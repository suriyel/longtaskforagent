---
name: long-task-increment-design
description: "Use when dispatched by long-task-increment Step 4 — revise design doc in place for new/modified/deprecated requirements and propagate §6.2 contracts"
---

# 增量设计修订

## 步骤

1. 读 `docs/plans/*-design.md`
2. 加载 `skills/long-task-increment/references/brownfield-adaptation.md` §E
3. 对 prompt 中的 `new_reqs` + `impact_matrix` + `api_changes`：

   **新增需求**：
   - 新增 Key Feature Design 子章节（§4.N+1），含类图、时序图、流程图，及引用 §6.2 Provides/Requires 的 **Integration Surface** (§4.N.6)
   - 对任何新的跨特性边界，在 §6.2 Internal API Contracts 新增对应行
   - 在 §3.3 组件图边上为新交互加 Contract ID 标签
   - 有新依赖关系时更新依赖链 (§11.3) 与任务分解 (§11.2)
   - 新三方依赖加入依赖表

   **修改需求**：
   - 原地更新对应 §4.N；按需更新时序/流程图
   - 影响跨特性接口时更新 §6.2 契约与 §4.N.6 Integration Surface
   - `api_changes` 中 `strategy=Breaking` 行对应的 §6.2 契约必须更新为新签名

   **弃用需求**：
   - 对应 §4.N 加 `[DEPRECATED - Wave N]` 标记；**不要**删除章节

4. **§13 存量约定**（若存在）：保持原样，除非本次增量引入：
   - 新内部库 → 更新 §13.1
   - 新禁用 API → 更新 §13.2
   - 新静态分析工具 → 更新 §13.3

5. **env-guide.md 传播**：
   - §13 变化 → 同步 `env-guide.md` §4
   - 引入新 build/test/coverage 命令 → 更新 `env-guide.md` §3
   - **§3/§4 任意改动**：不要自行改 frontmatter 的 approved_by / approved_date / approved_sections；在返回的 blockers 中列出 `env-guide-approval-pending`，让主 agent 提示用户审批

## 返回

```markdown
## SubAgent Result: long-task-increment-design

**status**: pass | blocked
**artifacts_written**: ["docs/plans/<name>-design.md", "env-guide.md"]  # env-guide.md 仅在被改时列出
**next_step_input**: {
  "design_sections_changed": ["4.5", "4.7", "6.2", "11.3"],
  "new_contracts": [{"id": "C-017", "provider": 7, "consumers": [5, 8]}],
  "modified_contracts": [{"id": "C-003", "breaking": true, "consumers": [5, 12]}],
  "env_guide_touched_sections": ["§3", "§4"]  # 空数组表示未改
}
**blockers**: [
  "env-guide.md §3/§4 modified — user must review diff and update frontmatter approved_by/approved_date/approved_sections before next Worker cycle"
]
**evidence**: [
  "Added 2 new §4.N sections; modified 1; deprecated 1",
  "§6.2: +1 contract, ~1 contract (Breaking), 0 removed",
  "env-guide.md §3 updated: 1 new test command"
]
```

## 阻塞 / 失败

- prompt 中 `api_changes` 的 Breaking 行对应的 §6.2 契约 ID 在现有 §6.2 中找不到 → `blocked`，要求主 agent 补全 contract ID 映射
- 多个新章节编号冲突 → `fail`，evidence 附冲突点

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 删除被弃用章节 | 加 `[DEPRECATED - Wave N]` 标记保留历史 |
| 修改 env-guide.md 的 frontmatter 审批字段 | 只改 §3/§4 内容，审批字段归用户 |
| 新契约不更新 §3.3 组件图 | §3.3 上的 Contract ID 标签必须与 §6.2 同步 |
