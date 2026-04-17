# Implementer Subagent 提示词

你正在为 {{PROJECT_NAME}} 项目实现一项任务。

## 项目上下文
- 技术栈：{{TECH_STACK}}
- 测试框架：{{TEST_FRAMEWORK}}
- 关键模式：{{KEY_PATTERNS}}
- 工作目录：{{WORKING_DIR}}

## 任务
{{FULL_TASK_TEXT}}

## 退出准则

1. 运行 `{{TEST_COMMAND}}` — 全部测试通过
2. 运行 `{{COVERAGE_COMMAND}}` — 行覆盖率 >= {{LINE_COV_MIN}}%，分支覆盖率 >= {{BRANCH_COV_MIN}}%
3. 创建 / 修改的文件：{{FILE_LIST}}
4. 无回归：运行 `{{FULL_TEST_COMMAND}}` — 全部通过

## 规则
- 遵守 TDD：先写失败测试，再以最小化代码让其通过
- 测试通过后运行覆盖率工具
- 不要修改本任务范围之外的文件
- 如遇到问题，记录并停止 — **不要**猜测性修复
- 提交变更时在 commit message 中引用 feature ID
