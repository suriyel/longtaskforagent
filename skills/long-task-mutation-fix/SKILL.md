---
name: long-task-mutation-fix
description: "修复存活变异体——通过增强测试或移除死代码来杀灭存活变异体。输入：feature_id。"
---

# 变异修复 — 杀灭存活变异体

从 Worker 提示中接收存活变异体详情，增强测试或移除死代码。

## 你的任务

1. 阅读执行规则：`skills/long-task-mutation-fix/references/mutation-fix-execution.md`
2. 阅读共享规则：`skills/long-task-tdd-shared/references/iron-law.md`、`docs/rules`
3. 阅读反模式：`skills/long-task-tdd-shared/references/testing-anti-patterns.md`

## 关键约束

- 输入：Agent 提示中传入的 `Surviving Mutants` 段落（file:line | mutator | description）
- 对每个变异体分类：等价变异体 -> 记录文档、真实缺口 -> 增强测试、不可达代码 -> 移除死代码
- 运行 `[test-quiet]` 确认所有测试通过——不可破坏代码
- **不要运行**变异测试或覆盖率工具——调用方会在你返回后度量
- **不要标记** feature-list.json 中的特性为 "passing"

使用下方的结构化返回契约返回结果。

---

## 结构化返回契约

```markdown
## SubAgent Result: Mutation Fix
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — mutants addressed]
### Metrics
mutants_addressed=N/M, equivalent_mutants=N, tests_strengthened=N, dead_code_removed=N, all_tests_pass=true/false
### Artifacts
[test/source files modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## 集成

**调用方：** long-task-mutation-retrofit — 分派 SubAgent 并附带存活变异体
**前置条件：** 变异测试度量返回 FAIL 且包含变异体详情
**产出：** 增强的测试 / 移除的死代码
