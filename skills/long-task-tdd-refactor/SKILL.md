---
name: long-task-tdd-refactor
description: "TDD 重构阶段 -- 清理代码、运行静态分析、验证 S11 合规性。输入：feature_id。"
---

# TDD 重构 -- 清理 + 合规

重构代码、运行静态分析并验证代码库合规性。请自行阅读所有文档。

## 你的任务

1. 阅读执行规则：`skills/long-task-tdd-refactor/references/tdd-refactor-execution.md`
2. 阅读规则：`skills/long-task-tdd-shared/references/iron-law.md`、`docs/rules`
3. 读取 `long-task-guide.md` -> 提取测试命令

## 关键约束

**唯一权威源 = feature 设计文档**。单次 Read 整份 feature.md（路径由 `python scripts/feature_paths.py design-doc --feature <id> --must-exist` 派生）。禁止 Glob / Read / Grep `docs/plans/*-srs.md` 或 `docs/plans/*-design.md`。

- **阶段 1：重构** -- 提取重复代码、改善命名、简化逻辑。每次修改后都运行测试。不得添加新功能。
- **阶段 2：静态分析质量门禁** -- 运行 feature.md §静态分析与质量工具命令 / §11.4 静态分析命令 中列出的每个工具命令。修复所有违规项 -- 违规项为阻塞性问题。
- **阶段 3：S11 合规检查**（唯一依据 = feature.md §全局约束摘录）：
  - a) S11.1 合规：对功能变更执行 `git diff --name-only`。对新增/修改的文件 grep 检查 §全局约束摘录 §11.1 表中"被替代方案"列。匹配即违规，必须修复。
  - b) 现有代码复用：对每个 REUSE 项，grep 实现文件查找预期的导入。未导入但重新实现 -> 违规 -> 替换为 REUSE 导入。
  - c) 实现摘要合规：验证实现文件/类/方法与实现摘要一致，未遗漏变更项，未引入摘要外的类。
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
static_analysis=CLEAN|N_violations, section11_compliance=CLEAN|N_violations, tests_pass=true/false, audit_verdict=pass|fail, audit_report_path=docs/reports/test_quality_<id>.json
### Evidence
negative_ratio=<from audit JSON>, low_value_ratio=<from audit JSON>, r4_missing=<n>, r6_missing=<n>, r8_violations=<n>, r9_violations=<n>
### External Sources Read
[whitelist only: feature.md (docs/features/<id>-<slug>.md), feature-list.json, long-task-guide.md, docs/rules/*.md (if any). MUST NOT contain docs/plans/*.md.]
### Artifacts
[files modified, one per line]
### Blockers
[if BLOCKED: "[AUDIT-REGRESSION] <rule>: <before>→<after>" or "[AUDIT-SCRIPT-ERROR] ..." or §11/static issue]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

`audit_verdict` / `Evidence.*` 由 `scripts/test_quality_audit.py` 产物 JSON 复制，禁止手填。
