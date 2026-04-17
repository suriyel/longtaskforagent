---
name: long-task-quality
description: "Use after TDD cycle in a long-task project - enforces coverage gate and fresh verification evidence before marking features as passing"
---

# 质量关卡 —— SubAgent 分发

将质量关卡执行委派给拥有全新上下文的 SubAgent。主 agent 仅负责分发并解析结构化结果 —— 绝不直接阅读覆盖率报告或测试运行器输出。

**开始时声明：** "I'm using the long-task-quality skill to run quality gates via SubAgent."

## Step 1: 构建 SubAgent 提示词

基于当前会话状态构造提示词。**不要**自行读取任何源码、测试输出或覆盖率报告。

```
You are a Quality Gates execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-quality/references/quality-execution.md
2. Read `env-guide.md` §3 (Build & Execution Commands) for test/coverage/static-analysis commands. Read `env-guide.md` §2 for environment activation. Both are the **single source of truth** — do NOT derive commands from long-task-guide.md (it only navigates; env-guide.md §3 owns commands).
3. Execute all 3 gates in order (Gate 0 → 1 → 2)
   - **Note**: Static analysis tools (listed in `env-guide.md §3` / `docs/rules/coding-constraints.md` "Static Analysis Tools" table) are enforced during TDD Refactor, not here. If `docs/rules/build-and-compilation.md` documents code generation directories, exclude them from coverage measurement in Gate 1.
4. If a gate fails, fix and retry per the rules (max 3 attempts per gate)
5. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates thresholds: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}
- Feature test files: {feature_test_files}  (test files written/modified during TDD for this feature)

## Key Constraint
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- If a tool/environment error cannot be resolved after 1 retry, set Verdict to BLOCKED
```

将 `{skills_root}` 替换为 skills 目录路径（例如项目内的 `skills` 或已安装插件的路径）。

## Step 2: 分发 SubAgent

**Claude Code：** 使用 `Agent` 工具：
```
Agent(
  description = "Quality Gates for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode：** 使用 `@mention` 语法或平台原生的 subagent 机制，提示词内容一致。

## Step 3: 解析结果

读取 SubAgent 返回的文本，定位 `**status**:` 行（统一契约字段）。为向后兼容，可能同时存在遗留的 `### Verdict:` 行，但权威字段是 `**status**`。

- **`**status**: pass`**
  1. 提取 `**next_step_input**`（coverage_line、coverage_branch、all_tests_pass、test_count）
  2. 可选：读取 Metrics 表以补充 task-progress.md 详情
  3. 在 `task-progress.md` 中记录："Quality Gates: PASS (line {X}%, branch {Y}%)"
  4. 进入下一步（Feature-ST）

- **`**status**: fail`**
  1. 阅读 `**evidence**` 与 Issues 表 —— 识别哪个关卡失败及原因
  2. 若 SubAgent 已按 3 次重试规则尝试过修复，通过 `AskUserQuestion` 携带失败细节升级给用户
  3. 若可通过重新分发修复（如环境问题已解决），构造新提示词并再次分发（最多 3 次总分发）

- **`**status**: blocked`**
  1. 阅读 `**blockers**` 数组 —— 识别阻塞原因（工具未安装、环境错误等）
  2. 通过 `AskUserQuestion` 携带阻塞细节与已尝试的动作升级给用户

## 集成

**调用方：** long-task-work（Step 8）
**依赖：** TDD 循环已完成（long-task-tdd 已通过 —— 测试存在并通过）
**产出：** 结构化摘要（覆盖率 %、每个关卡 pass/fail）
**下游：** long-task-feature-st（通过 Work Step 9）
