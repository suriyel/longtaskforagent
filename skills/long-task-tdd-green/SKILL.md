---
name: long-task-tdd-green
description: "TDD Green 阶段 -- 编写最小实现使所有测试通过。输入：feature_id。"
---

# TDD Green -- 最小实现

编写最小代码使所有测试通过。请自行读取所有文档。

## 你的任务

1. 读取执行规则：`skills/long-task-tdd-green/references/tdd-green-execution.md`
2. 读取规则：`skills/long-task-tdd-shared/references/iron-law.md`，`docs/rules`
3. 读取 `long-task-guide.md` → 提取测试命令、完整测试命令
## 实现约束（唯一权威源 = feature 设计文档）

**单次 Read 整份功能设计文档**（路径由 `python scripts/feature_paths.py design-doc --feature <id> --must-exist` 派生）。按顺序定位：

1. §接口契约 -- 方法签名、前/后置条件、§11.1 库注释（"Uses: ..."）
2. §现有代码复用 -- 所有带动作标记的项（REUSE/EXTEND/PATTERN）、§11 库&复用映射
3. §实现摘要 -- **严格遵从**：按指定文件/类/方法实现，遵循变更描述和设计决策
4. §全局约束摘录 -- §11.1 强制库 / §11.5 命名 / §11.6 错误处理模式 是实现硬约束

**禁令**：
- 禁止 Glob / Read / Grep `docs/plans/*-srs.md` 或 `docs/plans/*-design.md`
- 所有 Design §11 约束已由 feature-design SubAgent 沉淀到 feature.md §全局约束摘录；缺失 → 返 BLOCKED，不自行回访上游

## 关键约束

- 从测试出发进行全新实现 -- 绝不引用预删除的代码
- 一次一个测试：从最简单的失败测试开始
- 不做过早优化或额外功能
- §11.1：使用 feature.md §全局约束摘录 §11.1 表中的强制内部库，不使用被替代的方案
- §11.5：遵循 feature.md §全局约束摘录 §11.5 命名约定
- §11.6：遵循 feature.md §全局约束摘录 §11.6 错误处理模式
- REUSE 项：直接导入并调用 -- 不要重新实现
- EXTEND 项：继承或扩展 -- 不要复制粘贴
- PATTERN 项：遵循相同的结构模式
- 所有测试必须通过，零回归
- 测试输出协议：先 `[test-quiet]` → 如果 PASS 完成；如果 FAIL → `[test-detail]` 查看错误

使用下方的结构化返回契约返回结果。

---

## 结构化返回契约

当实现完成且所有测试通过时，请严格按照以下格式返回结果：

```markdown
## SubAgent Result: TDD Green
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — implementation complete, all tests passing, zero regressions]
### Metrics
test_count=N, tests_pass=N, regressions=0
### External Sources Read
[whitelist only: feature.md (docs/features/<id>-<slug>.md), feature-list.json, long-task-guide.md, docs/rules/*.md (if any). MUST NOT contain docs/plans/*.md.]
### Artifacts
[implementation files created/modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## 集成

**调用方：** long-task-work（步骤 4）-- Worker 分派 SubAgent，SubAgent 加载此 Skill 并内联执行
**依赖：** TDD Red 已完成（失败测试已存在）
**产出：** 实现代码 + 通过的测试
**后续：** long-task-tdd-refactor（步骤 5）
