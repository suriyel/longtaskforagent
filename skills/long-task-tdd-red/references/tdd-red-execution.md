# TDD Red -- SubAgent 执行参考

你是 TDD Red SubAgent。为所有测试清单行编写失败测试。

## 步骤 1：加载上下文

1. 读取 `feature-list.json` → 按 ID 提取功能对象、`tech_stack`
2. 派生功能设计文档路径：`python scripts/feature_paths.py design-doc --feature <id> --must-exist`
   - exit 0 → **单次 Read 整份文档**（不带 offset/limit）
   - exit 1 → BLOCKED：设计文档缺失，终止（主 orchestrator 已做硬前置，理论上不该在此触发）

**禁令**：本 SubAgent 不得 Glob / Read / Grep `docs/plans/*-srs.md` 或 `docs/plans/*-design.md`。所有上游约束（SRS FR / Design §11）必须从 feature.md §全局约束摘录 + §接口契约 + §实现摘要 读取。若缺失 → 返 BLOCKED，不自行回访上游。

### 步骤 1b：探索相关现有测试

发现与本功能相关模块中的测试约定和可复用测试基础设施。测试是规格 -- 铁律不适用。

1. 从功能设计文档的 **项目结构** + **dependencies[]**（已通过功能），识别本功能涉及的源目录
2. 在这些目录中 Glob 测试文件（模式根据 `tech_stack.test_framework`）
3. 如找到：读取 2-3 个代表性测试文件（优先选择依赖功能的测试）
4. 提取并记录：
   - 断言风格和测试结构
   - 共享 fixtures / 工厂 / 辅助函数（文件路径）
   - 被测代码的导入模式
   - Mock/stub 约定
5. 如果未找到测试文件 → 跳过，进入步骤 2

在步骤 3 中应用发现的约定。§11.5 和测试清单规则优先。
优先级：现有测试中发现的约定 > guide 中的 UT 风格。
如果未找到测试文件，使用 guide 中的 UT 风格作为基线。

## 步骤 2：读取规格

从功能设计文档中按顺序读取：

1. **§测试清单** -- 主要输入。每行映射到一个或多个测试用例。
2. **§接口契约** -- 方法签名、前/后置条件、边界决策表、错误处理表。当注释为 "Uses: [§11.1 library]" 时，测试设置应 mock/stub §11.1 库，而非被替代的方案。
3. **现有代码复用** -- 工具函数、API 客户端、§11 库&复用映射。测试使用相同的导入/模式。
4. **§实现摘要** -- 变更文件/类/方法清单。确保每个变更方法至少有一个测试行覆盖。
5. **§全局约束摘录** -- §11.1 强制库（本特性交集）+ §11.5 命名 + §11.6 错误处理模式。测试断言风格与异常类型以本节为准。
6. **澄清附录**（如存在）-- 用户批准的决议覆盖默认值。
7. **功能设计中的 mermaid 图**（若存在）-- 与散文并列消费，每个图元素硬触发测试：
   - `sequenceDiagram` 每条消息 → 一个协作/集成测试，断言调用发生、参数匹配；测试清单"追踪到"列应引用 `§设计对齐 seq msg#N`
   - `stateDiagram-v2` 每条 transition → 一个测试：给定 state=From + 触发 event，断言 state=To + 后置条件；每个守卫条件（`[guard]`）→ 正反两个测试；测试清单"追踪到"列应引用 `§接口契约 state <From>→<To>`
   - `flowchart TD` 每个决策节点（`{...}`）→ 正反两个测试；每个错误路径终点（`raise*` / `throw*`）→ 一个错误测试；测试清单"追踪到"列应引用 `§实现摘要 flow branch#N`
   - `classDiagram` 本阶段不生成测试（由 Green 按节点创建/修改类、Refactor grep 验证）

## 步骤 3：编写测试

**顺序：**
1. 分析测试清单 + 功能的 `srs_trace` 以识别外部依赖
2. 先写集成测试（验证外部依赖连通性）
3. 再写单元测试（happy/error/boundary/security）

**规则**：按 `iron-law.md` §R1-R9 执行（本文件不重复）。

**UML 图覆盖补充**（iron-law.md 不涵盖；为本 SubAgent 专属约束）：若功能设计含 mermaid 图 — 每条 sequence 消息 / 每条 state transition / 每个 flow 决策节点 至少有一行测试在"追踪到"列引用该图元素。

## 步骤 4：验证全部失败

**在 Red 阶段，退出码 != 0 为成功。退出码 0（全部通过）表示测试有误。**

1. 按 `long-task-guide.md` 激活环境
2. 运行 `[test-quiet]` → 期望退出码 != 0 且摘要显示 0 通过
3. 如果有测试通过 → 运行 `[test-detail]` 识别哪个 → 重写 → 重新运行 `[test-quiet]`
4. 如果工具/环境错误 → 诊断、修复、重新运行。绝不跳过。
5. 修复受阻时，先 grep 项目中类似测试的写法作为参考。

## 总结

按 `SKILL.md` 中的结构化返回契约格式返回。
