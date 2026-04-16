# SubAgent 驱动开发

## 目的

为每个实现任务分派一个全新的 SubAgent。这可以防止上下文污染（一个任务的细节不会干扰下一个任务），并实现每个任务的独立验证。

## 适用场景

- 包含多个任务的复杂功能
- 上下文污染可能成为问题的功能
- 功能详细设计已完成（通过 `long-task:long-task-feature-design` skill）

对于简单功能（1-2 个任务），自行执行更快且足够。

## 架构

```
Controller (main agent)
  │
  ├─ Dispatch Subagent: Task 1 (implementer)
  │   └─ Returns: code changes + test results
  │
  └─ Repeat for Task 2, Task 3, ...
```

## Controller 职责

主 Agent 充当 Controller，负责：

1. **加载实现计划** -- 来自 `docs/plans/`
2. **为每个任务分派一个 SubAgent** -- 附带完整的任务文本
3. **审查结果** -- 每个任务完成后
4. **跟踪进度** -- 标记任务完成，更新功能状态
5. **处理失败** -- 如果任务失败，为重试提供上下文

## 分派实现者 SubAgent

### 关键规则

1. **提供完整任务文本** -- 将整个任务描述复制到提示词中。不要说"读取文件 X" -- SubAgent 可能没有该上下文。

2. **包含项目上下文** -- 告知 SubAgent：
   - 项目是什么
   - 使用什么技术栈
   - 关键文件在哪里
   - 应遵循什么模式

3. **定义明确的退出标准** -- 告知 SubAgent"完成"的准确含义：
   - 哪些测试必须通过
   - 应创建/修改哪些文件
   - 运行什么验证命令

### 提示词模板

```markdown
You are implementing a task for the [project-name] project.

## Project Context
- Tech stack: [stack]
- Key patterns: [patterns]
- Test framework: [framework]

## Task
[Full task text from the plan, including exact file paths, code, and verification steps]

## Exit Criteria
1. Run [test command] — all tests pass
2. Files created/modified: [list]
3. No regressions: run [full test command] — all pass

## Rules
- Follow TDD: write failing tests first, then implement
- Do not modify files outside the scope of this task
- Commit your changes with a descriptive message
```

## 并行分派（高级）

当多个任务相互独立（无共享文件、无依赖关系）时：

1. 在计划中识别独立任务
2. 使用 Task 工具并行分派实现者 SubAgent
3. 等待全部完成
4. 运行完整测试套件检查冲突
5. 审查每个任务的变更
6. 解决所有冲突

**约束**：
- 仅并行化真正独立的任务
- 并行完成后始终运行完整测试套件
- 如发现冲突，按顺序解决

## 反模式

| 反模式 | 失败原因 | 正确做法 |
|---|---|---|
| 引用文件而非提供完整文本 | SubAgent 可能无法访问或缺少上下文 | 将完整任务文本复制到提示词中 |
| 分派时未定义明确的退出标准 | SubAgent 不知道何时算完成 | 定义准确的验证命令 |
| 并行化有依赖关系的任务 | 竞态条件、变更冲突 | 仅并行化真正独立的任务 |
| 忽略审查反馈 | 质量问题会累积 | 在继续之前修复 Critical/Important 问题 |
