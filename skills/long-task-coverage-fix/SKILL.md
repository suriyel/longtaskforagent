---
name: long-task-coverage-fix
description: "修复覆盖率缺口——为未覆盖的行/分支补充测试。输入：feature_id。"
---

# 覆盖率修复 — 为未覆盖代码补充测试

从 Worker 提示中接收覆盖率缺口详情，编写测试来消除缺口。

## 你的任务

1. 阅读执行规则：`skills/long-task-coverage-fix/references/coverage-fix-execution.md`
2. 阅读共享规则：`skills/long-task-coverage-fix/references/iron-law.md`
3. 读取 `long-task-guide.md` — 获取测试命令（`[test-quiet]`、`[test-detail]`）
4. 阅读反模式：`skills/long-task-coverage-fix/references/testing-anti-patterns.md`

## 关键约束

- 输入：Agent 提示中传入的 `Coverage Gaps` 段落（file:line-range | type | description）
- 编写测试以覆盖已识别的缺口
- 运行 `[test-quiet]` 确认所有测试通过——不可破坏代码
- **不要运行**覆盖率或变异测试工具——调用方会在你返回后度量
- **不要标记** feature-list.json 中的特性为 "passing"

使用下方的结构化返回契约返回结果。

---

## 结构化返回契约

```markdown
## SubAgent Result: Coverage Fix
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — tests added, gaps addressed]
### Metrics
tests_added=N, gaps_addressed=N/M, all_tests_pass=true/false
### Artifacts
[test files created/modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## 集成

**调用方：** long-task-coverage-retrofit — 分派 SubAgent 并附带覆盖率缺口
**前置条件：** 覆盖率度量返回 FAIL 且包含缺口详情
**产出：** 覆盖已识别缺口的额外测试
