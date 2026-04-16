---
name: long-task-tdd-refactor
description: "TDD 重构阶段 -- 清理代码、运行静态分析、验证 S11 合规性。输入：feature_id。"
---

# TDD 重构 -- 清理 + 合规

重构代码、运行静态分析并验证代码库合规性。请自行阅读所有文档。

## 你的任务

1. 阅读执行规则：`skills/long-task-tdd-refactor/references/tdd-refactor-execution.md`
2. 阅读规则：`skills/long-task-tdd-shared/references/iron-law.md`、`docs/rules`

## 关键约束

- **阶段 1：重构** -- 提取重复代码、改善命名、简化逻辑。每次修改后都运行测试。不得添加新功能。
- **阶段 2：静态分析质量门禁** -- 如果设计文档 S11.4 列出了静态分析工具，运行每个工具的命令。修复所有违规项 -- 违规项为阻塞性问题。
- **阶段 3：S11 合规检查：**
  - a) 依赖版本 (D3)：抽查 `requirements.txt` / `package.json` / `pom.xml` 是否与功能设计 §接口契约/§实现摘要 中指定的库版本匹配。
  - b) S11.1/S11.2 合规：对功能变更执行 `git diff --name-only`。对新增/修改的文件 grep 检查被替换的导入 (S11.1) 和被禁止的 API (S11.2)。匹配即违规，必须修复。
  - c) 现有代码复用：对每个 REUSE 项，grep 实现文件查找预期的导入。未导入但重新实现 -> 违规 -> 替换为 REUSE 导入。
  - d) 实现摘要合规：验证实现文件/类/方法与实现摘要一致，未遗漏变更项，未引入摘要外的类。
- 发现违规时：修复、重新运行测试、重新检查。
- 所有测试必须通过，静态分析零违规，S11 合规检查通过。

使用下方的结构化返回契约返回结果。

---

## 结构化返回契约

重构、静态分析和 S11 合规检查全部完成后，严格按照以下格式返回结果：

```markdown
## SubAgent Result: TDD Refactor
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — refactoring complete, static analysis and §11 compliance results]
### Metrics
static_analysis=CLEAN|N_violations, section11_compliance=CLEAN|N_violations, tests_pass=true/false
### Artifacts
[files modified, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## 集成

**调用方：** long-task-work（步骤 5）-- Worker 分派 SubAgent，SubAgent 加载此 Skill 并内联执行
**前置条件：** TDD Green 已完成（测试通过）
**产出物：** 重构后的代码 + 静态分析通过 + S11 合规
**后续步骤：** 持久化（步骤 6）
