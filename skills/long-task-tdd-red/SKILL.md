---
name: long-task-tdd-red
description: "TDD Red 阶段 -- 为功能测试清单编写失败测试。输入：feature_id。"
---

# TDD Red -- 编写失败测试

为所有测试清单行编写失败测试。请自行读取所有文档。

## 你的任务

1. 读取执行规则：`skills/long-task-tdd-red/references/tdd-red-execution.md`
2. 读取规则：`skills/long-task-tdd-shared/references/iron-law.md`，`docs/rules`
3. 读取反模式：`skills/long-task-tdd-shared/references/testing-anti-patterns.md`

## 规格输入（来自功能设计文档）

按顺序读取以下章节：
1. §7 测试清单 -- 主要输入。每行 → 一个或多个测试用例。
2. §3 接口契约 -- 方法签名、前/后置条件、§11.1 库注释。
3. 现有代码复用 -- 工具函数、API 客户端、§11.1 库使用示例。
4. §5 算法 / 核心逻辑 -- 边界矩阵（§5c）、错误表（§5d）。
5. 澄清附录（如存在）-- 用户批准的决议。
6. `long-task-guide.md` 中的 UT 风格 -- UT/mock 框架、mock 风格、探索约定
7. 相关现有测试（步骤 1b）-- 探索依赖功能的测试文件，获取断言风格、fixtures、导入、mock 模式。与 UT 风格不同时以此为准。

## 关键约束

- 先写集成测试，再写单元测试（happy/error/boundary/security）
- 规则 1：类别覆盖率（FUNC/happy、FUNC/error、BNDRY/*、SEC/*）
- 规则 2：负向测试比例 >= 40%
- 规则 3：低价值断言比例 <= 20%
- 规则 4：对每个测试进行"错误实现"挑战
- 规则 5：UT + 集成两层均为强制（除非纯计算）
- 按层标注测试：# [unit] 或 # [integration]
- 所有测试必须失败（退出码 != 0 为成功）。退出码 0 表示测试有误 -- 重写
- 遵循相关现有测试约定（步骤 1b）以保持一致性。§11.5 和测试清单优先。
- 测试输出协议：先 `[test-quiet]` → 如果 PASS（错误！）重写；如果全部 FAIL（正确！）完成。不确定时 → `[test-detail]`

使用下方的结构化返回契约返回结果。

---

## 结构化返回契约

当所有测试编写完毕并验证为失败状态时，请严格按照以下格式返回结果：

```markdown
## SubAgent Result: TDD Red
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-2 sentences — tests written, all confirmed failing (RED)]
### Metrics
test_count=N, negative_ratio=N% (≥40%, PASS/FAIL), all_tests_fail=true/false
### Artifacts
[test files created, one per line]
### Issues
[Omit if PASS. One line per issue: severity (Critical/Major/Minor) | description]
```

---

## 集成

**调用方：** long-task-work（步骤 3）-- Worker 分派 SubAgent，SubAgent 加载此 Skill 并内联执行
**产出：** 失败的测试文件
**后续：** long-task-tdd-green（步骤 4）
