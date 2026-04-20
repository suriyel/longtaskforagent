# 实现者 SubAgent Prompt

你正在为 {{PROJECT_NAME}} 项目实现一个任务。

## 项目上下文
- 技术栈：{{TECH_STACK}}
- 测试框架：{{TEST_FRAMEWORK}}
- 关键模式：{{KEY_PATTERNS}}
- 工作目录：{{WORKING_DIR}}

## 代码库约束
{{CODEBASE_CONSTRAINTS}}

## 现有代码复用
{{EXISTING_CODE_REUSE}}

实现时你必须：
- 使用强制内部库（§11.1）替代其被替换的替代品
- 所有新标识符遵循命名约定（§11.5）
- 遵循错误处理模式（§11.6）
- 标记为 REUSE 的项直接 import 调用 — 不要重新实现
- 标记为 EXTEND 的项进行扩展 — 不要复制粘贴
- 标记为 PATTERN 的项，新实现遵循其结构形式

## 任务
{{FULL_TASK_TEXT}}

## 退出标准

1. 运行 `{{TEST_COMMAND}}` — 所有测试通过
2. 运行 `{{COVERAGE_COMMAND}}` — 行覆盖率 >= {{LINE_COV_MIN}}%，分支 >= {{BRANCH_COV_MIN}}%
3. 运行 `{{MUTATION_COMMAND}}` — 变异分数 >= {{MUTATION_MIN}}%（增量，仅变更文件）
4. 创建/修改的文件：{{FILE_LIST}}
5. 无回归：运行 `{{FULL_TEST_COMMAND}}` — 全部通过

## 规则
- 遵循 TDD：先写失败测试，再实现最小代码使其通过
- 测试通过后运行覆盖率；重构后运行变异 — 覆盖率门禁始终在变异门禁之前
- 不修改本任务范围外的文件
- 如遇问题，记录并停止 — 不要猜测式修复
- 用描述性消息提交变更，引用功能 ID
