---
name: long-task-tdd-red
description: "TDD Red 阶段 -- 为功能测试清单编写失败测试。输入：feature_id。"
---

# TDD Red -- 编写失败测试

为所有测试清单行编写失败测试。请自行读取所有文档。

## 你的任务

1. 读取执行规则：`skills/long-task-tdd-red/references/tdd-red-execution.md`
2. 读取规则：`skills/long-task-tdd-shared/references/iron-law.md`，`docs/rules`
3. 读取 `long-task-guide.md` → 提取测试命令、环境激活和 UT 风格（`[test-framework]`、`[mock-style]`、`[conventions]`）
4. 读取反模式：`skills/long-task-tdd-shared/references/testing-anti-patterns.md`

## 规格输入（唯一权威源 = feature 设计文档）

**单次 Read 整份功能设计文档**（路径由 `python scripts/feature_paths.py design-doc --feature <id> --must-exist` 派生）。按顺序在已读入的内容中定位以下章节：

1. §测试清单 -- 主要输入。每行 → 一个或多个测试用例。
2. §接口契约 -- 方法签名、前/后置条件、§11.1 库注释、边界决策表、错误处理表。
3. §现有代码复用 -- 工具函数、API 客户端、§11 库&复用映射。
4. §实现摘要 -- 变更文件/类/方法清单，确保每个变更方法有测试覆盖。
5. **§全局约束摘录** -- §11.1 强制库（本特性交集）+ §11.5 命名 + §11.6 错误处理；测试断言风格与错误类型依据本节。
6. §澄清附录（如存在）-- 用户批准的决议。
7. `long-task-guide.md` 中的 UT 风格 -- UT/mock 框架、mock 风格、探索约定
8. 相关现有测试（步骤 1b）-- 探索依赖功能的测试文件，获取断言风格、fixtures、导入、mock 模式。与 UT 风格不同时以此为准。

**禁令**：
- 禁止 Glob / Read / Grep `docs/plans/*-srs.md` 或 `docs/plans/*-design.md`（任何切片方式皆禁）
- 所有上游约束（SRS FR / Design §11 等）已由 feature-design SubAgent 沉淀到 feature.md §全局约束摘录；若发现缺失 → 返回 BLOCKED，不自行回访上游

## 关键约束

- 先写集成测试，再写单元测试
- 按 `iron-law.md` §R1-R9 执行（本文件不重复）
- 所有测试必须失败（退出码 != 0 为成功）。退出码 0 表示测试有误 — 重写
- 遵循相关现有测试约定（步骤 1b）以保持一致性。§11.5 和测试清单优先
- 测试输出协议：先 `[test-quiet]` → 若 PASS（错误！）重写；若全部 FAIL（正确！）完成。不确定 → `[test-detail]`
- 完成后执行 `tdd-red-execution.md` 步骤 5 跑 `scripts/test_quality_audit.py`，把指标注入返回契约

## 结构化返回契约

```markdown
## SubAgent Result: TDD Red
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — tests written, all confirmed failing (RED)]
### Metrics
test_count=N, all_tests_fail=true/false, audit_verdict=pass|fail, audit_report_path=docs/reports/test_quality_<id>.json
### Evidence
negative_ratio=<from audit JSON>, low_value_ratio=<from audit JSON>, r4_missing=<n>, r6_missing=<n>, r8_violations=<n>, r9_violations=<n>
### External Sources Read
[whitelist only: feature.md (docs/features/<id>-<slug>.md), feature-list.json, long-task-guide.md, docs/rules/*.md (if any). MUST NOT contain docs/plans/*.md.]
### Artifacts
[test files created, one per line]
### Blockers
[if BLOCKED: "[AUDIT-FAIL] <rule>: <detail>" or "[AUDIT-SCRIPT-ERROR] ..." or design-gap reason]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

`Metrics.audit_verdict` / `Evidence.*` 由 `scripts/test_quality_audit.py` 产物 JSON 复制，禁止手填。
