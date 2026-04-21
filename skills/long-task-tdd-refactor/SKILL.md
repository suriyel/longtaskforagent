---
name: long-task-tdd-refactor
description: "Use when dispatched by long-task-work-tdd Step 3c — clean up while keeping tests green, re-verify §4/§6/§8 alignment, run static analysis gate from env-guide §3"
---

# TDD Refactor — 清理

保持测试为绿的同时清理代码。本步骤**不引入新功能**。

## 输入解析（SubAgent 启动时）

从 prompt 取 `feature_id` / `feature_list_path` / `feature_test_files` / `impl_files`，随后自行完成：

1. 调 `python scripts/feature_paths.py design-doc --feature {feature_id}` → 捕获 stdout 作为 `{feature_design_path}`（slug 规则权威实现，不自行拼路径）
2. 读 `{feature_design_path}` §4 / §6 / §8（与 Green 独立重读，**一致性优先于去重**）
3. Glob `env-guide.md` → §3（静态分析命令列表）

## 重构规则

- 抽取重复、改进命名、简化分支结构
- 每次改动按 `env-guide.md §3` 静默执行，**仅**重跑触及改动文件的测试
- 重构全部完成后跑一次全量套件，确认无回归
- **不新增功能**；新增功能应回到 Red 写新测试驱动

## 设计对齐回查（强制，静态分析之前）

1. 独立重读 `{feature_design_path}` §4 Interface Contract / §6 Implementation Summary / §8 Data Model
2. 列出本次重构改动的**公共符号**：
   - 新增或重命名的方法
   - 改动的参数类型 / 异常类型
   - 跨模块移动的函数
   - 新增或调整的数据字段
3. 对每个改动符号，核对是否仍与 §4 / §6 / §8 对应行字面一致
4. **UML 图合规**（若 `{feature_design_path}` 含 mermaid 图）：
   - `classDiagram`：grep 每个节点名 → 确认类存在；`MODIFIED` 节点 → `git diff` 确认有变更；**未在类图中声明但被修改的类** → 范围蔓延告警
   - `sequenceDiagram`：grep 每条消息的方法名 → 确认在对应类中实现且被调用
   - `stateDiagram-v2`：grep 每个状态名 + 事件名 → 确认出现在代码中
   - `flowchart TD`：AST / grep 每个决策条件 → 确认实现含对应分支；**未在图中声明但存在的额外分支** → 告警
   - 任一告警 → drift-protocol（更新图 OR 回滚改动，同一 commit）
5. 不一致 → 按 `../long-task-work-tdd/references/drift-protocol.md` 处理：
   - 偏离合理 → 更新对应设计节（含 mermaid 图）+ 复查 §7 Test Inventory + 设计与代码**同一 commit**
   - 偏离不合理 → **回滚重构**
   - 无法本地消解 → blocker `[CONTRACT-DEVIATION]`
6. **设计对齐未通过不得进入静态分析**（偏离符号被静态工具忽略将导致后续 Inline Check P2/D3 拦截）

## 静态分析关卡

若 `env-guide.md §3` 列出静态分析命令（Checkstyle / Ruff / Pylint / ESLint / cppcheck 等）：

1. 设计对齐通过且重构全部完成后，按 `env-guide.md §3` 静默执行每个工具
2. 退出码非零 → `grep -E "error|warning" /tmp/static-$$.log` 提取违规
3. **退出重构之前修复全部违规** —— 违规是阻塞性的
4. 工具自行读取配置（`.pylintrc` / `checkstyle.xml` / `eslint.config.js` 等）；**不要**手动解析配置

若 env-guide §3 未列静态分析 → 本关卡 N/A，跳过。

## Structured Return Contract

```markdown
## SubAgent Result: long-task-tdd-refactor

**status**: pass | fail | blocked
**artifacts_written**: [重构中修改的实现/测试文件；如触发 drift-protocol 则含 {feature_design_path}]
**next_step_input**: {
  "static_analysis_ok": true,
  "static_tool": "<checkstyle | ruff | pylint | eslint | ... | N/A>",
  "static_violations": 0,
  "design_alignment_final": {
    "§4": "matches" | "updated(commit:<sha>)",
    "§6": "matches" | "updated(commit:<sha>)",
    "§8": "matches" | "updated(commit:<sha>)" | "N/A",
    "drift": "none" | "resolved"
  },
  "tests_still_pass": true
}
**blockers**: [optional: `[CONTRACT-DEVIATION]` / `[ENV-ERROR]`]
**evidence**: [
  "Refactor: extracted 2 helpers, renamed 3 symbols (User.validate → User.check_valid)",
  "Design alignment re-verified: §4=matches (helper 未进公共面), §6=matches, §8=matches",
  "Static analysis clean (tool=ruff, 0 violations)",
  "Full test suite: <N>/<N> pass (no regression)"
]
```

## 阻塞 / 失败

- 重构引入回归且无法修复 → `fail`
- 静态分析违规无法修复 → `fail`
- 设计偏离无法本地消解 → `blocked` `[CONTRACT-DEVIATION]`
- 静态工具 / 环境故障 → `blocked` `[ENV-ERROR]`
