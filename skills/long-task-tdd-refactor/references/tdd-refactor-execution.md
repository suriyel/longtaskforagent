# TDD 重构 -- SubAgent 执行参考

你是一个 TDD 重构 SubAgent。负责清理代码、通过静态分析、验证 S11 合规性。

## 步骤 1：加载上下文

1. 读取 `feature-list.json` -> 按 ID 提取功能对象及 `tech_stack`、`lcd_trace[]`
2. Glob `docs/plans/*-design.md` -> 读取 S11（代码库约定与约束）
3. 若 `lcd_trace[]` 非空 -> Glob `docs/plans/*-srs.md` -> 读取 SRS §1.4.2 中 `lcd_trace[]` 所指行（执行权威）
4. 派生功能设计文档路径：`python scripts/feature_paths.py design-doc --feature <id> --must-exist` -> 读"现有代码复用"和"实现摘要"章节
5. 读取 `long-task-guide.md` -> 提取测试命令

## 步骤 2：重构

- 提取重复代码、改善命名、简化逻辑
- 每次修改后运行 `[test-quiet]`；失败时运行 `[test-detail]` 查看错误信息
- 本步骤不得添加新功能
- 重构前先 grep 项目中类似模块的结构作为参考

## 步骤 3：静态分析质量门禁

如果设计文档 S11.4 列出了静态分析工具（如 `npx eslint .`、`mvn checkstyle:check`、`mypy src/`）：

1. 运行每个工具的命令
2. 修复所有违规项 -- 违规项为**阻塞性问题**
3. 修复后重新运行测试
4. 工具自行读取配置；不要手动解析配置文件

## 步骤 4：S11 合规检查

**a) S11.1 合规：**
1. 运行 `git diff --name-only` 识别功能的新增/修改文件
2. 读取设计文档 S11.1：对每个非空的"替换"条目，grep 新增/修改的源文件查找被替换的导入模式。匹配即违规，必须修复。

**b) 现有代码复用验证：**
1. 读取功能设计的"现有代码复用"章节
2. 对每个 REUSE 项：grep 实现文件查找预期的导入
3. 如果 REUSE 项未导入但等效功能被重新实现 -> 违规 -> 替换为 REUSE 导入

**c) 实现摘要合规：**
1. 读取功能设计的"实现摘要"
2. 对每行：验证对应文件/类已创建或修改
3. 检查未在摘要中但被修改的源文件 → 标记为潜在范围蔓延

**d) UML 图合规**（若功能设计含 mermaid 图）：
1. `classDiagram`：grep 每个类节点名 → 确认类存在；`classDef MODIFIED` 节点 → `git diff` 确认该类有实际变更；未在图中声明但被修改的类 → 范围蔓延告警
2. `sequenceDiagram`：对每条 `A->>B: method(args)` 消息 → grep `method` 在 `B` 对应类文件中的定义 + grep 调用点在 `A` 对应类文件中存在；缺一即违规
3. `stateDiagram-v2`：grep 每个状态名与事件名 → 确认出现在代码中（如枚举值、常量或状态机框架调用）；缺失即违规
4. `flowchart TD`：对每个决策节点的判定条件 → grep 确认实现中含对应分支；图中未声明但代码含的额外分支 → 告警（可能超出设计范围）

**e) LCD 语义合规**（若 `lcd_trace[]` 非空）：
1. 对每条 `lcd_trace[]` LCD：定位 Red 阶段为此 LCD 建立的测试（类别 `FUNC/legacy` 或 `INTG/compat`，"追踪到"列引用 `SRS §1.4.2 LCD-XXX`）
2. 运行这些测试 → 必须通过；若失败说明 Green 阶段实现违反了 LCD 决议 → 违规
3. 对 `BEHAVIOR/COMPAT/DATA` 类 LCD 的决议列关键字，grep 实现文件：若实现出现原文式反向语义（与决议矛盾的字符串 / 常量 / 分支）→ 返回 `[LEGACY-DRIFT]` blocker
4. 对 `PERF` 类 LCD：检查实现路径是否引入同步阻塞 / N+1 / 未索引扫描等与决议基线冲突的模式

发现任何违规时：修复，重新运行测试以确认无回归，重新检查。违规为 LCD 冲突（无法本地修复）时 → `[LEGACY-CONFLICT]` blocker 回上层。

## 步骤 5：最终验证

运行 `[test-quiet]` -- 所有测试通过，静态分析零违规，S11 合规检查通过。

## 总结

报告：成功/失败、重构数量、修复的静态分析违规数量、S11 合规结果（S11.1、复用、摘要、UML 图）、LCD 合规结果（若 `lcd_trace[]` 非空）。
