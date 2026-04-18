# Implementer Subagent 提示词

你正在为 {{PROJECT_NAME}} 项目实现一项任务。

## 项目上下文
- 技术栈：{{TECH_STACK}}
- 测试框架：{{TEST_FRAMEWORK}}
- 关键模式：{{KEY_PATTERNS}}
- 工作目录：{{WORKING_DIR}}

## 设计契约（实现必须字面一致）

以下节原文摘自 `docs/features/YYYY-MM-DD-<slug>.md`（Feature Design），是本任务的**硬性一致性来源**。实现的公共符号（方法名、参数、返回类型、抛出异常、模块职责、数据结构字段）**必须**与以下内容逐字匹配。若发现冲突，**不得**在实现端悄悄改签名——返回 blocker `[CONTRACT-DEVIATION]`。

### §4 Interface Contract
{{FEATURE_DESIGN_INTERFACE_CONTRACT}}

### §6 Implementation Summary（模块职责与调用链）
{{FEATURE_DESIGN_IMPLEMENTATION_SUMMARY}}

### §8 Data Model（数据结构字段与类型）
{{FEATURE_DESIGN_DATA_MODEL}}

## 任务
{{FULL_TASK_TEXT}}

## 退出准则

1. 运行 `{{TEST_COMMAND}}` — 全部测试通过
2. 运行 `{{COVERAGE_COMMAND}}` — 行覆盖率 >= {{LINE_COV_MIN}}%，分支覆盖率 >= {{BRANCH_COV_MIN}}%
3. 创建 / 修改的文件：{{FILE_LIST}}
4. 无回归：运行 `{{FULL_TEST_COMMAND}}` — 全部通过
5. **设计对齐自检**：列出本次实现的所有公共方法签名、参数类型、异常类型、数据结构字段，逐条核对 §4/§6/§8；不一致则走"契约—实现漂移协议"（更新设计 OR 修实现，同一 commit）

## 规则
- 遵守 TDD：先写失败测试，再以最小化代码让其通过
- 测试通过后运行覆盖率工具
- 不要修改本任务范围之外的文件
- **实现的公共接口签名必须与 §4 字面一致**；模块/类划分必须与 §6 调用链一致；数据结构必须与 §8 字段对齐
- 如遇到问题，记录并停止 — **不要**猜测性修复
- 提交变更时在 commit message 中引用 feature ID
