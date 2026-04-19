# SubAgent 驱动的开发（Subagent-Driven Development）

## 目的

为每个实现任务分发一个全新的 SubAgent。这可防止上下文污染（一个任务的细节不会混淆下一个），并实现任务级独立验证。

## 何时使用

- 包含多个任务的复杂特性
- 担心上下文污染的特性
- 特性详细设计已完成时（经由 `long-task:long-task-feature-design` skill）

对简单特性（1-2 个任务），主 agent 自行执行更快、也已足够。

## 架构

```
Controller (main agent)
  │
  ├─ Dispatch Subagent: Task 1 (implementer)
  │   └─ Returns: code changes + test results
  │
  └─ Repeat for Task 2, Task 3, ...
```

## Controller 的职责

主 agent 作为 controller。其职责：

1. **加载实现计划**（来自 `docs/plans/`）
2. **每个任务分发一个 SubAgent**，附带完整任务文本
3. **任务完成后审阅结果**
4. **跟踪进度** — 标记任务完成、更新特性状态
5. **处理失败** — 若任务失败，为重试提供上下文

## 分发 Implementer SubAgent

### 关键规则

1. **提供完整任务文本** — 将整段任务描述复制到提示词中。**不要**说"读文件 X" — SubAgent 可能没有上下文。

2. **包含项目上下文** — 告知 SubAgent：
   - 项目是什么
   - 使用什么技术栈
   - 关键文件在哪
   - 应遵循的模式

3. **定义明确的退出准则** — 精确告知 SubAgent"完成"的定义：
   - 哪些测试必须通过
   - 应创建 / 修改哪些文件
   - 应运行什么验证命令

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

## 并行分发（进阶）

当多个任务彼此独立（无共享文件、无依赖）时：

1. 在计划中识别独立任务
2. 使用 Task 工具并行分发 implementer SubAgent
3. 等待全部完成
4. 运行完整测试套件检查冲突
5. 审阅每个任务的变更
6. 解决冲突（若有）

**约束**：
- 仅并行化真正独立的任务
- 并行完成后始终运行完整测试套件
- 若发现冲突，串行解决

## 反模式

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| 用文件引用代替完整文本 | SubAgent 可能无访问权限或无上下文 | 将完整任务文本复制到提示词 |
| 分发而无明确退出准则 | SubAgent 不知何时算完成 | 定义精确的验证命令 |
| 对有依赖的任务并行化 | 竞态条件、冲突性修改 | 仅并行化真正独立的任务 |
| 忽略评审反馈 | 复合质量问题 | 在继续前修复 Critical / Important |
