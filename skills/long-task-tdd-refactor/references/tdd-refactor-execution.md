# TDD 重构 -- SubAgent 执行参考

你是一个 TDD 重构 SubAgent。负责清理代码、通过静态分析、验证 S11 合规性。

## 步骤 1：加载上下文

1. 读取 `feature-list.json` -> 按 ID 提取功能对象及 `tech_stack`
2. 派生功能设计文档路径：`python scripts/feature_paths.py design-doc --feature <id> --must-exist` -> **单次 Read 整份文档**（不带 offset/limit）；工作记忆需同时持有：
   - §现有代码复用（REUSE/EXTEND/PATTERN 验证依据）
   - §实现摘要（变更文件/类/方法合规依据）
   - §全局约束摘录（§11.1 / §11.5 / §11.6 合规依据）
   - §静态分析与质量工具命令（§11.4 静态分析门禁依据 + §11.7 阈值）
3. 读取 `long-task-guide.md` -> 提取测试命令

**禁令**：本 SubAgent 不得 Glob / Read / Grep `docs/plans/*-srs.md` 或 `docs/plans/*-design.md`。Design §11 / §11.4 / §11.7 所有信息已沉淀到 feature.md 两沉淀章节；缺失 → 返 BLOCKED。

## 步骤 2：重构

- 提取重复代码、改善命名、简化逻辑
- 每次修改后运行 `[test-quiet]`；失败时运行 `[test-detail]` 查看错误信息
- 本步骤不得添加新功能
- 重构前先 grep 项目中类似模块的结构作为参考

## 步骤 3：静态分析质量门禁

依据 feature.md §静态分析与质量工具命令 / §11.4 静态分析命令（若非 "N/A"）：

1. 运行表中每行的命令字符串（如 `npx eslint .`、`mvn checkstyle:check`、`mypy src/`）
2. 修复所有违规项 -- 违规项为**阻塞性问题**
3. 修复后重新运行测试
4. 工具自行读取配置；不要手动解析配置文件
5. 不得回访 `docs/plans/*-design.md`；若本章节显式 N/A → 跳过阶段 3

## 步骤 4：S11 合规检查

**a) S11.1 合规：**
1. 运行 `git diff --name-only` 识别功能的新增/修改文件
2. 从 feature.md §全局约束摘录 §11.1 表（本特性交集子集）读取每行的"被替代方案"列；对每个非空条目，grep 新增/修改的源文件查找被替代的导入模式。匹配即违规，必须修复。
3. 不得回访 `docs/plans/*-design.md` 的原始 §11.1 全表 — 若 feature.md 摘录缺失 → 返 BLOCKED。

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

发现任何违规时：修复，重新运行测试以确认无回归，重新检查。

## 步骤 5：最终验证

运行 `[test-quiet]` -- 所有测试通过，静态分析零违规，S11 合规检查通过。

## 总结

按 `SKILL.md` 中的结构化返回契约格式返回。
