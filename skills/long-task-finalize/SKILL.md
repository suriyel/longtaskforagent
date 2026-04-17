---
name: long-task-finalize
description: "Use after ST Go verdict — generate usage examples and finalize release documentation via SubAgent"
---

# Finalize —— ST 后的文档与示例

在系统测试（ST）以 Go / Conditional-Go 判定通过后，生成基于场景的使用示例并完善发布文档。

**开始时声明：** "I'm using the long-task-finalize skill. ST passed — generating examples and finalizing documentation."

**幂等**：ST 缺陷修复循环后可安全重复调用。每次运行都干净地覆盖 `examples/` 内容。

<HARD-GATE>
除非 ST 判定为 Go 或 Conditional-Go，**不要**调用本 skill。若判定为 No-Go，则回到 Worker 进行修复。
</HARD-GATE>

## 清单

必须为每一步创建 TodoWrite 任务并按顺序完成：

### 1. 调取上下文

- 阅读 `feature-list.json` —— 所有通过且非弃用的特性、`tech_stack`、`quality_gates`
- 阅读 SRS 文档（`docs/plans/*-srs.md`）—— 需求描述、用户画像
- 阅读设计文档（`docs/plans/*-design.md`）—— 架构、公共 API 表面
- 阅读 UCD 文档（`docs/plans/*-ucd.md`）—— 仅当存在 UI 特性时
- 阅读 `task-progress.md` —— 供 ST 汇总条目使用的会话历史
- 阅读 `RELEASE_NOTES.md` —— 当前版本条目状态
- 记录路径供 SubAgent 分发使用

### 2. 生成示例（SubAgent）

分发 example-generator SubAgent 生成基于场景的使用示例。

1. 构建 SubAgent 提示词：
   ```
   You are an Example Generator SubAgent.

   ## Your Task
   1. Read the agent definition: Read <skills_root>/../agents/example-generator.md
   2. Follow the process to generate scenario-based usage examples
   3. Return your result using the Structured Return Contract

   ## Input Parameters
   - feature-list.json: <path>
   - SRS: <srs_path>
   - Design: <design_path>
   - UCD: <ucd_path> (or "none")
   - tech_stack: <tech_stack_json>
   - Working directory: <project_root>
   ```

2. 分发：
   ```
   Agent(
     description = "Generate usage examples for all features",
     prompt = [constructed prompt]
   )
   ```

3. 解析返回契约：
   - **PASS**：所有计划场景均已生成并校验
   - **PARTIAL**：部分示例已生成；对缺口打 warning 日志
   - **FAIL**：打 error 日志；仍然继续 —— 示例生成是非阻塞的

在 `task-progress.md` 中记录：
```
- Examples: <verdict> — N scenarios, N examples generated, N features covered
```

### 3. 更新 RELEASE_NOTES.md

添加 ST 完成条目与版本条目（从 ST Persist 迁移而来）：
- 在 `[Unreleased]` 下添加，或按需创建版本化章节
- 包含：ST 判定、日期、测试摘要（执行的分类、发现/修复的缺陷）
- 引用 ST 报告文档路径

### 4. 更新 task-progress.md

添加 ST 会话汇总条目（从 ST Persist 迁移而来）：
- 执行的 ST 分类，通过/失败计数
- 发现并修复的缺陷（含严重级别）
- 最终质量指标
- 示例生成结果（来自 Step 2）

### 5. Persist（持久化）

- Git 提交所有文档工件：
  ```
  git add examples/ RELEASE_NOTES.md task-progress.md
  git commit -m "docs: finalize release — examples, release notes, progress update"
  ```
- 校验：
  ```bash
  python scripts/validate_features.py feature-list.json
  ```

### 6. 总结

输出完成摘要：
> **Finalize — DONE**
>
> Examples: N scenarios generated (N features covered, N skipped)
> RELEASE_NOTES.md: Updated with ST completion
> task-progress.md: Updated with ST session summary

## 关键规则

- **非阻塞** —— 示例生成失败**不会**追溯性地改变 Go 判定
- **幂等** —— 可安全重跑；干净地覆盖 examples/
- **仅示例走 SubAgent** —— RELEASE_NOTES 与 task-progress 由本 skill 直接更新（不由 SubAgent）
- **不新增特性** —— 不得新增、修改或测试任何特性；仅限文档
- **遵循项目约定** —— 示例匹配项目的语言、风格与模式
