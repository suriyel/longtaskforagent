# Feature Design 嵌入 Mermaid UML — 下游 TDD 消费贯通

## Context

`feature-design-template.md` 的"实现摘要/设计对齐/接口契约"等章节用**表格 + 散文**表达流程、状态、类间关系。散文表达此类"关系型信息"是低密度形式，TDD 消费时需"语义理解"，精度低；表格对文件/方法清单密度足够，但对**方法内行为**（状态转移、调用顺序、决策分支）无力。

调研结论：
- 系统级 `docs/templates/design-template.md` 已用 mermaid 画**类/模块层**类图、时序图、流程图（§4.N）
- feature design 层次**当前无图** —— 对应章节是纯提纲（`设计对齐`）+ 方法级自然语言（`实现摘要`）
- TDD sub-skill 消费 feature design 时，Red 能从**测试清单表**直译、Green 能从**接口契约表**直译、但遇到散文形式的"关键设计决策"/"变更描述"需语义理解 → gap
- `skill-subagent-refactor-lessons.md §4.2` 曾剃除"流程图"，理由"AI 不按图分支" —— 必须以**可消费契约**反驳此判决，否则新图就是 token 税

**改动目标**：在 feature design 嵌入 mermaid UML 图（不新建章节，替代/辅助既有散文），并**同步修改 TDD red/green/refactor execution.md 的消费规则**，让图元素成为测试用例和实现骨架的硬触发源。确保 lessons §3.3（权威源重复）+ §4.2（流程图反模式）+ §3.7（跨文件漂移源）三条判据同时过关。

## 评估结论（ROI + 对齐精度）

| 维度 | 结论 |
|---|---|
| 对齐精度 | 仅对**状态机 / 多对象协作 / 复杂分支** feature 有提升；CRUD / 纯计算类无帮助 |
| ROI | **条件正向** — 需触发判据 + 下游消费契约 + 嵌入式集成三者齐备；否则负向 |
| 格式 | mermaid（与 repo 规范统一）；**不用** plantuml |
| lessons §3.3 判据 2 | 通过 — feature design 的图聚焦**方法内**（状态/调用/分支），与系统 §4.N 类/模块层不重叠，无漂移源增加 |
| lessons §4.2 反模式 | 通过 — 消费契约写入 TDD execution.md，图元素与测试/实现直接映射，非装饰 |

## 核心设计原则

1. **集成方式**：UML 图嵌入**既有章节**，替代/强化对应散文。**不新建**`## UML 图示` 类独立章节
2. **主辅关系**：流程/状态/关系类信息 → **图占主，文字辅助说明**；文字仅注解图中非显然的决策理由
3. **命名规则**：节点/参与者/状态/消息必须用**真实标识符**（ClassName、methodName、StateName、EventName）。**禁止** A/B/C 代称
4. **装饰约束**：
   - 类图：**允许**用 classDef 色区分 `NEW` / `MODIFIED` / `EXISTING`（唯一允许的装饰，对齐系统 design-template.md 惯例）
   - sequence / state / flowchart：**禁止**任何色彩、图标、rect 框包裹、皮肤主题、`<<stereotype>>` 修饰等装饰元素
5. **触发判据硬规则**（写入 execution.md，不满足则**不画**）：

   | 信号 | 图类型 | 嵌入位置 |
   |---|---|---|
   | 涉及 ≥2 个类/模块协作（含新增/修改） | classDiagram | §设计对齐 |
   | 涉及 ≥2 个对象/服务的调用顺序 | sequenceDiagram | §设计对齐 |
   | 方法含状态依赖（状态数 ≥2 且有 transition） | stateDiagram-v2 | §接口契约 — 对应方法行下方 |
   | 方法含 ≥3 个决策分支或异常路径 | flowchart TD | §实现摘要 — 对应行下方 |

6. **层次分工**（避免与系统设计 §4.N 重复）：系统 §4.N = 类/模块层；feature design = **方法内细粒度**（方法内调用序、方法内状态转换、方法内分支）

## 下游 TDD 消费契约（硬绑定）

这是让图**不沦为死代码**的决定性改动。每种图必须对应具体的 Red/Green/Refactor 动作：

### classDiagram（NEW/MODIFIED 色标）
- **Green** 消费：每个 `classDef NEW` 节点 → 创建类；每个 `classDef MODIFIED` 节点 → 修改现有类；每条关联/依赖边 → 实现为字段引用或方法参数
- **Refactor** 消费：grep 每个节点名，确认类存在；对 `MODIFIED` 节点，diff 确认有变更；未在类图中声明但被修改的类 → 范围蔓延告警

### sequenceDiagram
- **Red** 消费：每条 `participantA->>participantB: method()` → 至少一个集成/协作测试，断言调用发生且参数匹配。测试清单"追踪到"列引用 `§设计对齐 seq msg#N`
- **Green** 消费：消息顺序 = 实现中方法调用的先后顺序，不得乱序

### stateDiagram-v2
- **Red** 消费：每个 `stateA --> stateB : event` → 一个测试用例：给定 state=A + 触发 event，断言 state=B + 后置条件；每个守卫条件 → 正反两个测试。测试清单"追踪到"列引用 `§接口契约 state A→B`
- **Green** 消费：状态转移表作为实现骨架（switch/match on state + event）

### flowchart TD
- **Red** 消费：每个决策菱形节点（`{...}`）→ 正反两个测试；每个错误路径终点 → 一个错误测试。测试清单"追踪到"列引用 `§实现摘要 flow branch#N`
- **Green** 消费：分支节点 = if/elif 结构骨架；错误路径终点 = raise 语句
- **Refactor** 消费：每个分支在代码中对应一个可达分支；不可达分支 → 告警

## 改动文件清单

### 1. `skills/long-task-feature-design/references/feature-design-template.md`（模板占位 + 示例）

改动点：

- **§设计对齐**（line 26-30）：现有 3 行项目符号扩为"若满足类/时序触发判据，嵌入 mermaid 代码块 + 辅助文字注解"。给 1 个 classDiagram 骨架示例（含 classDef 色标）+ 1 个 sequenceDiagram 骨架示例（无装饰）
- **§接口契约**（line 62-82）：在"边界决策"表前新增一段"若方法含状态依赖，在对应方法行下方嵌入 stateDiagram-v2"。给 1 个 stateDiagram 骨架示例（真实状态名、真实事件名、无装饰）
- **§实现摘要**（line 84-90）：在表格下方新增"若任一行的关键设计决策涉及 ≥3 分支/错误路径，嵌入 flowchart TD 替代散文说明"。给 1 个 flowchart 骨架示例（真实方法名、真实条件、无装饰）
- **§验证检查清单**（line 107-118）：追加 3 条：
  - `[ ] UML 图（若存在）节点/参与者/状态/消息均使用真实标识符，无 A/B/C 代称`
  - `[ ] 非类图不含色彩/图标/rect 等装饰元素`
  - `[ ] 每个图元素（类节点、sequence msg、state transition、flow 分支）在测试清单的"追踪到"列被至少一行引用`

### 2. `skills/long-task-feature-design/references/feature-design-execution.md`（作者指令）

改动点：

- **§2 接口契约**：在状态依赖描述处加"若方法为状态机（状态数 ≥2），在方法行下方嵌入 `stateDiagram-v2`，节点用真实状态名，禁用装饰"
- **§3 实现摘要**：现有"内部分析分支条件/边界值/错误路径"之后加"若方法含 ≥3 决策分支或异常路径，把分析结果以 `flowchart TD` 嵌入表格下方，真实方法名/真实条件文本，不加装饰；此时散文只作图外注解"
- 新增一节 **§2a 设计对齐（UML 嵌入触发）**：显式给出"≥2 类协作 → classDiagram（含 NEW/MODIFIED classDef 色标）；≥2 参与者 → sequenceDiagram（无装饰）"两条触发规则 + 引用 §2b 禁令
- 新增一节 **§2b UML 风格硬约束**（给作者的 DO/DON'T 对照示例）：
  - DO：`class OrderService { +placeOrder(req: OrderRequest): OrderId }`
  - DON'T：`class A { +foo(): B }`
  - DO：`participant OrderService` / `OrderService->>PaymentGateway: charge(amount)`
  - DON'T：`participant A as A` / `A->>B: call()`
  - DO：stateDiagram-v2 直接 `Created --> Paid : paymentConfirmed`
  - DON'T：任何 sequence/state/flowchart 的 `style X fill:#...` / `classDef` / `rect rgb(...)` / 图标
- **§结构化返回契约 Metrics**：新增指标 `UML Element Trace Coverage | N/M | M/M | PASS/FAIL`（M = 图元素总数，N = 在测试清单"追踪到"列被引用的元素数）

### 3. `skills/long-task-tdd-red/references/tdd-red-execution.md`（Red 消费规则）

改动点：**§步骤 2 读取规格** 列表追加第 6 项：

```
6. **功能设计中的 mermaid 图**（若存在）—— 与散文并列消费：
   - sequenceDiagram：每条消息 → 一个协作/集成测试，断言调用与参数
   - stateDiagram-v2：每个 transition → 一个测试（状态+事件+守卫，正反两侧），每个守卫 → 正反两例
   - flowchart TD：每个决策节点 → 正反测试；每个错误终点 → 一个错误测试
   - 测试清单"追踪到"列必须引用对应图元素（如 `§设计对齐 seq msg#3`、`§接口契约 state Created→Paid`、`§实现摘要 flow branch#2`）
```

**§步骤 3 规则表** 加一行：`UML 图覆盖 | 每个 sequence 消息 / state transition / flow 分支 至少一个测试引用`

### 4. `skills/long-task-tdd-green/references/tdd-green-execution.md`（Green 消费规则）

改动点：**§步骤 2 读取实现约束** 列表追加第 4 项：

```
4. **功能设计中的 mermaid 图**（若存在）—— **严格遵从**：
   - classDiagram：每个 `classDef NEW` 节点 → 创建类；`MODIFIED` 节点 → 修改现有类；关联/依赖边 → 字段或参数引用
   - sequenceDiagram：消息顺序 = 方法内调用顺序，不得乱序
   - stateDiagram-v2：状态转移表 = 实现骨架（如 switch/match on (state, event)）
   - flowchart TD：决策节点 = if/elif 结构；错误终点 = raise 语句
```

### 5. `skills/long-task-tdd-refactor/references/tdd-refactor-execution.md`（Refactor 合规）

改动点：**§步骤 4 实现摘要合规** 追加子项 d：

```
d) UML 图合规（若功能设计含 mermaid 图）：
   1. classDiagram：grep 每个节点名 → 确认类存在；`MODIFIED` 节点 → diff 确认有变更；未在图中声明但被修改的类 → 范围蔓延告警
   2. sequenceDiagram：grep 每条消息的方法名 → 确认在对应类中实现且被调用
   3. stateDiagram-v2：grep 每个状态名 + 事件名 → 确认出现在代码中
   4. flowchart TD：AST / grep 每个决策条件 → 确认实现含对应分支；未在图中声明但存在的额外分支 → 告警
```

## 层次分工（与系统设计 §4.N 的关系）

**零重叠**是通过"粒度差异"实现的，不是通过"禁止"：

| 层 | 图粒度 | 示例 |
|---|---|---|
| 系统设计 §4.N（docs/templates/design-template.md）| 类/模块层 | `OrderService` 类与 `PaymentGateway` 类的依赖关系、跨服务调用主线 |
| feature design（本次改动）| 方法内细粒度 | `OrderService.placeOrder` 方法内部的调用序列、订单状态机 `Created→Paid→Shipped`、`validateOrder` 的分支流程 |

作者判断标准：**若图内容已在系统 §4.N 等价表达** → 不重复画，在 §设计对齐 用一行文字引用即可（`"见系统设计 §4.3 类图"`）。lessons §3.3 判据 2 通过。

## 验证（如何测试端到端）

1. **模板语法自测**：`grep -n '```mermaid' skills/long-task-feature-design/references/feature-design-template.md` 确认 3 个示例块存在；人工过一遍示例节点名，确认无 A/B/C 代称、非类图无装饰
2. **下游契约贯通自测**：grep "UML" / "mermaid" / "sequenceDiagram" / "stateDiagram" / "flowchart" 在 red/green/refactor-execution.md 均出现，且各自消费动词（"每条消息 → 一个测试"、"transition → 测试"、"节点 → 创建类"）齐备
3. **幻影引用审计**（lessons §3.6）：
   - grep 所有下游对"§设计对齐 / §接口契约 / §实现摘要"的引用，确认引用的子项（seq msg / state transition / flow branch）在 template 中有对应嵌入位置
   - reviewer 类 agent（若存在）无幻影引用
4. **跨文件漂移源核对**（lessons §3.7）：
   - 系统 design-template.md 的图规范未变
   - feature design 新增图的**粒度声明**（方法内）写入 execution.md §2a 顶部注释，作为分工契约
   - 漂移源 = 1（feature design 的触发判据）+ 0（系统层未变）
5. **真实 feature 试跑**：选 1 个状态机类 feature（若 `feature-list.json` 有），手工按新模板画图 → 跑 TDD Red SubAgent → 确认测试清单生成时"追踪到"列包含 UML 元素引用 → 跑 Green → 确认实现骨架与图一致
6. **负向试跑**：选 1 个 CRUD feature → 按触发判据应**不画图** → 确认 SubAgent 不误触发（验证"不画"路径也覆盖到）

## 关键文件定位

- `skills/long-task-feature-design/references/feature-design-template.md` — 改 §设计对齐 / §接口契约 / §实现摘要 / §验证检查清单 4 处
- `skills/long-task-feature-design/references/feature-design-execution.md` — 改 §2 / §3，新增 §2a / §2b，改 §结构化返回契约 Metrics
- `skills/long-task-tdd-red/references/tdd-red-execution.md` — 改 §步骤 2 / §步骤 3
- `skills/long-task-tdd-green/references/tdd-green-execution.md` — 改 §步骤 2
- `skills/long-task-tdd-refactor/references/tdd-refactor-execution.md` — 改 §步骤 4

**不改**：`docs/templates/design-template.md`（系统层规范维持现状）、`long-task-feature-design/SKILL.md` 骨架（skeleton 无改动必要）、`long-task-work-design/SKILL.md`（orchestrator 无改动）

## 风险与不做项

- **不做**：把 `实现摘要` 表格本身替换为图 — 文件/类/方法变更清单是表格密度最高形式，图反而降维
- **不做**：为所有 feature 强制画图 — 违反触发判据即负 ROI
- **不做**：引入新章节容纳图 — 用户明确反对独立图示章节
- **风险**：作者未遵守"真实标识符 + 无装饰"约束 → 依赖 §验证检查清单 3 条新增项 + execution.md §2b DO/DON'T 示例兜底；Refactor 阶段 grep 合规检查作为最后防线
- **风险**：lessons 文档未同步本次新增规则 → 建议后续追加一节 `§ 5. UML 嵌入条件 + 下游消费硬绑定`（本次不做，留给 lessons 维护者）
