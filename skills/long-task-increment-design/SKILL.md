---
name: long-task-increment-design
description: "Use when dispatched by long-task-increment Step 4 — revise design doc in place for new/modified/deprecated requirements and propagate §4 Internal API Contracts"
---

# 增量设计修订

## 步骤

1. 读 `docs/plans/*-design.md`
2. 加载 `skills/long-task-increment/references/brownfield-adaptation.md` §E
3. 对 prompt 中的 `new_reqs` + `impact_matrix` + `api_changes`：

   **新增需求**：
   - 新增 Feature Integration Spec 子章节（§2.N+1），含 Overview、Key Types、Integration Surface（Provides/Requires 表，引用 §4 Contract ID）
   - 对任何新的跨特性边界，在 §4 Internal API Contracts 新增对应行
   - 在 §1.3 组件图边上为新交互加 Contract ID 标签
   - 有新依赖关系时更新 §6.1 任务分解与 §6.2 依赖链
   - 新三方依赖加入 §1.4 Tech Stack Decisions 表

   **修改需求**：
   - 原地更新对应 §2.N 的 Overview / Key Types / Integration Surface
   - 影响跨特性接口时更新 §4 契约行
   - `api_changes` 中 `strategy=Breaking` 行对应的 §4 契约必须更新为新签名

   **弃用需求**：
   - 对应 §2.N 加 `[DEPRECATED - Wave N]` 标记；**不要**删除章节

4. **存量约束更新**（仅当本波引入新规则时）：
   - 新内部库 → 直接更新 `docs/rules/coding-constraints.md` 的 "Mandatory Internal Libraries" 表
   - 新禁用 API → 直接更新 `docs/rules/coding-constraints.md` 的 "Prohibited APIs" 表
   - 新静态分析工具 → 直接更新 `docs/rules/coding-constraints.md` 的 "Static Analysis Tools" 表

5. **env-guide.md 传播**：
   - `docs/rules/` 变化 → 同步 `env-guide.md §4`（§4.1 / §4.2 从 coding-constraints.md 重新抽取；§3 静态分析命令行从 Static Analysis Tools 表重新抽取）
   - 引入新 build/test/coverage 命令 → 更新 `env-guide.md §3`
   - **§3/§4 任意改动**：不要自行改 frontmatter 的 approved_by / approved_date / approved_sections；在返回的 blockers 中列出 `env-guide-approval-pending`，让主 agent 提示用户审批

## 返回

```markdown
## SubAgent Result: long-task-increment-design

**status**: pass | blocked
**artifacts_written**: ["docs/plans/<name>-design.md", "docs/rules/coding-constraints.md", "env-guide.md"]  # 仅列出被改动的文件
**next_step_input**: {
  "design_sections_changed": ["2.5", "2.7", "4", "6.2"],
  "new_contracts": [{"id": "C-017", "provider": 7, "consumers": [5, 8]}],
  "modified_contracts": [{"id": "C-003", "breaking": true, "consumers": [5, 12]}],
  "rules_touched": true,
  "env_guide_touched_sections": ["§3", "§4"]
}
**blockers**: [
  "env-guide.md §3/§4 modified — user must review diff and update frontmatter approved_by/approved_date/approved_sections before next Worker cycle"
]
**evidence**: [
  "Added 2 new §2.N sections; modified 1; deprecated 1",
  "§4: +1 contract, ~1 contract (Breaking), 0 removed",
  "docs/rules/coding-constraints.md: 1 new prohibited API; env-guide.md §4.2 regenerated"
]
```

## 阻塞 / 失败

- prompt 中 `api_changes` 的 Breaking 行对应的 §4 契约 ID 在现有 §4 中找不到 → `blocked`，要求主 agent 补全 contract ID 映射
- 多个新章节编号冲突 → `fail`，evidence 附冲突点

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 删除被弃用章节 | 加 `[DEPRECATED - Wave N]` 标记保留历史 |
| 修改 env-guide.md 的 frontmatter 审批字段 | 只改 §3/§4 内容，审批字段归用户 |
| 新契约不更新 §1.3 组件图 | §1.3 上的 Contract ID 标签必须与 §4 同步 |
| 把约束写入设计文档而非 `docs/rules/` | 约束源是 `docs/rules/`；设计文档不再镜像 |
| 在 §2.N 画类图/时序图/流程图 | §2.N 仅 Overview + Key Types + Integration Surface |
