---
name: long-task-tdd
description: "已弃用——已拆分为 long-task-tdd-red、long-task-tdd-green、long-task-tdd-refactor。请勿直接调用。"
---

# TDD —— 重定向

本 skill 已拆分为三个阶段 skill：

1. **`long-task:long-task-tdd-red`** —— 编写失败测试（Red 阶段）
2. **`long-task:long-task-tdd-green`** —— 最小实现（Green 阶段）
3. **`long-task:long-task-tdd-refactor`** —— 重构 + 静态分析 + S11 合规（Refactor 阶段）

Worker（`long-task-work`）按步骤 3、4、5 的顺序依次调用它们。

## 共享参考

- `skills/long-task-tdd-shared/references/iron-law.md` —— 铁律 + 测试场景规则
- `skills/long-task-tdd-shared/references/testing-anti-patterns.md` —— 完整反模式目录
- `skills/long-task-tdd/prompts/implementer-prompt.md` —— 实现者 SubAgent 提示词模板（供 TDD Green 使用）
