# 功能级详细设计 -- SubAgent 执行参考

你是功能设计执行 SubAgent。请严格遵循以下规则。完成后，使用本文档底部的**结构化返回契约**返回结果。

---

# 功能级详细设计

为单个功能生成详细设计，衔接系统级设计（§4.N）与 TDD 实现。

系统设计回答"存在哪些类、它们如何交互"。
本技能回答"具体修改哪些文件/类、接口契约、边界错误条件、如何实现"。

## 输入

在编写任何设计内容之前，请通过以下方式读取上游文档（**一次到位、禁止片段读**）：

1. **派生路径**（单一权威路径工具）：
   - `srs_path  = $(python scripts/feature_paths.py srs-doc)`
   - `dsgn_path = $(python scripts/feature_paths.py system-design-doc)`
   - `out_path  = $(python scripts/feature_paths.py design-doc --feature <id>)`
2. **单次 Read `srs_path` 整份**（不带 offset/limit）— 含 §1 全景 / 全部 FR-xxx / §约束假设
3. **单次 Read `dsgn_path` 整份**（不带 offset/limit）— 含 §3 / §4.N（全部）/ §6.2 / §11.1 / §11.4 / §11.5 / §11.6 / §11.7
4. **功能对象** -- 来自 `feature-list.json` 的 ID、标题、描述、srs_trace、依赖、优先级（如有 verification_steps）；根级 `constraints[]` / `assumptions[]`
5. **现有代码** -- 如果依赖功能已通过，读取其公开接口（导入、类/函数签名）
6. **代码库约定** -- 读取 `docs/rules/*.md`（若存在）

**禁令**：
- 禁止 `Read` 带 `offset/limit` 对 SRS / Design 做片段读
- 禁止 `Grep` SRS / Design 做子串切片
- 上述 2/3 步必须一次完整 Read；工作记忆必须同时持有 SRS 全文与 Design 全文
- §11 在设计文档中始终存在。空表意味着该类别无约束 — 仍需将其沉淀到 feature.md（见 §2c）

SRS / Design 已读入后，从设计文档提取下列章节并保持在工作记忆中（供后续步骤使用）：
- §4.N（本功能对应的系统设计章节）
- §6.2（本功能作为 Provider / Consumer 的行，若该节存在）
- §11.1：强制内部库表（领域、库、替代、导入模式）
- §11.4：静态分析命令（工具、命令、适用范围）
- §11.5：命名约定表
- §11.6：错误处理模式
- §11.7：覆盖率与变异阈值

## 模板

使用 `skills/long-task-feature-design/references/feature-design-template.md` 作为结构模板。复制模板，为目标功能填充每个章节。

**精简规则**：无内容的章节直接省略，不写 N/A。

## 检查清单

你必须按顺序完成每个步骤：

### 1. 加载上下文

读取上述输入中列出的所有输入制品。

### 1a. 项目结构

加载上下文后，填充模板中的"项目结构"章节：
1. 根据设计文档 §4.N 和现有代码（依赖功能），识别本功能将创建或修改的所有文件
2. 标记每个文件为 [existing]、[new] 或 [modified]
3. 仅包含与本功能架构相关的文件 -- 除非直接修改，否则省略测试工具、配置文件

### 1b. 歧义扫描

读取所有输入后、编写任何设计内容之前，扫描可能影响设计正确性的规格歧义。扫描使用以下分类：

| 代码 | 检查内容 |
|------|----------|
| `SRS-VAGUE` | 验收标准包含模糊语言（"快速"、"用户友好"、"适当"、"应处理"），缺少可衡量的阈值或具体行为 |
| `SRS-DESIGN-CONFLICT` | SRS 需求与设计 §4.N 在接口类型、数据格式、行为或错误处理上存在矛盾 |
| `SRS-MISSING` | 验收标准没有 Given/When/Then 或未指定预期结果 |
| `DEP-AMBIGUOUS` | 跨功能接口不清晰 -- 依赖的 §6.2 条目缺失或不完整 |
| `CONSTRAINT-CONFLICT` | §11 代码库约定与功能需求冲突 |

**扫描流程：**

1. 对每个 SRS 验收标准：检查是否包含可衡量、具体、可测试的条件 → `SRS-VAGUE`
2. 对每个 SRS 需求：与设计 §4.N 交叉参照 → `SRS-DESIGN-CONFLICT`
3. 对每个 SRS 验收标准：验证 Given/When/Then 存在且有明确预期结果 → `SRS-MISSING`
4. 对 §6.2 契约：检查 schema 是否完整 → `DEP-AMBIGUOUS`
5. 对 §11.1：检查功能需求是否与约束冲突 → `CONSTRAINT-CONFLICT`

**对于 `category: "bugfix"` 功能**：仅对缺陷的验收标准扫描 `SRS-VAGUE` 和 `SRS-DESIGN-CONFLICT`。

**决策门禁：**
- **未检测到歧义** → 正常进入步骤 2。
- **所有歧义有合理解释且影响非关键** → 带假设继续。记录在 `## 澄清附录`，Authority = "assumed"。Verdict = `PASS`。
- **高影响歧义**（影响接口契约签名、测试清单预期结果或跨功能契约） → Verdict = `CLARIFY`。不进入步骤 2。

> **带澄清附录重新分派时**：用户批准的决议视为权威约束，不重新标记为歧义。

### 1c. 现有实现发现

**原则 -- 最大化复用**：优先导入现有代码而非编写新代码。重复现有功能是设计缺陷。

#### 阶段 A：代码库探索（仅限存量项目）

**触发条件**：`docs/rules/` 存在且包含 >=1 个 `.md` 文件，或源文件 > 3。
**跳过条件**：新建项目。

1. 从功能输入中提取焦点：
   - 功能标题/描述 + SRS 文本 → 领域关键词
   - 设计 §4.N → 架构区域
   - 推断 `--focus`：数据功能 → `dataflow,architecture,deps`；API → `api,architecture,deps`；业务逻辑 → `domain,architecture,deps`；横切关注点 → `architecture,deps`
   - 如果 §4.N 有局部定位，推断 `--path`

2. 确定深度：

   | 信号 | 深度 |
   |------|------|
   | <=1 个依赖，单类范围 | quick |
   | 2+ 个依赖或多个 SRS 追踪 | standard |
   | 横切关注点（认证、日志、中间件） | standard |

3. 分派：
   > **DISPATCH** 独立 SubAgent -- 加载并执行 `long-task:long-task-explore`

4. 消费 `docs/explore/codebase-research.md`，将发现记录在 "## 现有代码复用" 中。

**非阻塞** -- 如果 BLOCKED 或无发现，正常进入阶段 A-2。

#### 阶段 A-2：需求相关行为发现

**触发条件**：与阶段 A 相同。跳过条件相同。

1. 从 SRS 验收标准提取行为关键词（动作动词 + 领域名词）
2. 在源代码中 Grep（排除测试/配置/文档，限前 10 匹配）
3. 与功能需求交叉参照：完全重叠 → REUSE，部分重叠 → EXTEND，相邻行为 → PATTERN
4. 记录在 "现有代码复用" 的 "需求相关现有行为" 子表中

**非阻塞**。

#### 阶段 B：依赖功能扫描

1. 列出 `dependencies[]` 中 `"status": "passing"` 的功能
2. 读取已通过依赖的实现文件，编目可复用项（跳过阶段 A 已发现的）
3. 对 §11.1 强制库：在已通过功能中找具体使用示例
4. 记录在 "## 现有代码复用" 中，标注 REUSE/EXTEND/PATTERN

#### §11 库 & 复用映射

对每个非平凡方法，识别必须使用的 §11.1 强制库和 REUSE 项：

| 方法 | 操作 | 必需库/复用项 | 导入模式 | 替代 |
|------|------|---------------|----------|------|

记录在 "现有代码复用" 章节的 "§11 库 & 复用映射" 子表中。

### 2a. 设计对齐 -- UML 嵌入触发

> 粒度约定：本技能产出的 UML 图聚焦**方法内**细粒度（调用序列 / 状态转换 / 方法内分支）。系统设计 §4.N 已覆盖类/模块层；若内容等价，只写一行文字引用（如"见系统设计 §4.3 类图"），不重复画图。

在 `## 设计对齐` 章节按以下触发规则嵌入 mermaid 代码块（图占主，文字仅注解非显然决策）：

| 触发信号 | 图类型 | 装饰允许 |
|---|---|---|
| 本功能涉及 ≥2 个类/模块协作（含 NEW/MODIFIED） | `classDiagram` | 允许用 classDef 色标区分 NEW/MODIFIED/EXISTING（唯一允许的装饰，对齐 design-template 惯例） |
| ≥2 个对象/服务参与调用顺序 | `sequenceDiagram` | **禁止**任何装饰 |

不满足触发信号 → **不画**。

### 2b. UML 风格硬约束

对本技能产出的所有 mermaid 图（classDiagram / sequenceDiagram / stateDiagram-v2 / flowchart），执行以下规则：

**DO（必须）**：
- `class OrderService { +placeOrder(req: OrderRequest) OrderId }` -- 真实类名 + 真实方法签名
- `participant OrderService` / `OrderService->>PaymentGateway: charge(amount)` -- 真实参与者 + 真实方法调用
- `Created --> Paid : paymentConfirmed` -- 真实状态名 + 真实事件名
- `validateInput{input valid?}` -- 真实方法名 + 真实判定条件

**DON'T（违规，验证检查清单会拦截）**：
- `class A { +foo() B }` -- 代称 A/B/C
- `participant A as A` / `A->>B: call()` -- 代称 + 占位符
- 在 sequence / state / flowchart 中使用 `style X fill:#...` / `classDef` / `rect rgb(...)` / 图标 / 皮肤主题
- `note over` / `loop` / `alt` 等非必要包裹（仅在表达真实并发或异常路径时允许）

**每个图元素必须被测试清单"追踪到"列引用**（见本文件 §4 规则）。未被任何测试引用的图元素视为死代码，Verdict = FAIL。

### 2. 接口契约

对本功能暴露或修改的每个公共方法：

| 方法 | 签名 | 前置条件 | 后置条件 | 异常 |
|------|------|----------|----------|------|

规则：
- 前置条件使用 SRS 验收标准中的 Given/When 风格
- 后置条件必须具体且可测试
- 每个 SRS 验收标准必须追踪到至少一个方法的后置条件
- 仅在包含非平凡逻辑时才包含内部方法
- **§6.2 对齐规则**：签名必须与 §6.2 schema 兼容。Provider 后置条件保证 Response Schema；Consumer 前置条件假设 Request Schema。
- **§11.5 命名合规**：所有方法、参数和类名遵循 §11.5 命名约定
- **§11.1 库合规**：执行 §11.1 覆盖操作的方法添加 "Uses" 注释
- **现有代码复用检查**：REUSE 等效功能不创建新方法，EXTEND 设计为重写/扩展

### 契约偏差协议

发现 §6.2 契约不正确、不充分或技术上不可行时：
1. 在设计理由章节记录偏差（契约 ID、原始 vs 建议、原因、影响）
2. Verdict = `BLOCKED`，Issue："契约偏差需要设计更新"
3. 协调器上报用户

**状态机嵌入规则**（触发：方法含状态依赖，状态数 ≥2 且有 transition）：
- 在对应方法说明之后嵌入 `stateDiagram-v2` mermaid 代码块
- 状态名、事件名使用真实标识符（如 `Created --> Paid : paymentConfirmed`）
- 遵循 §2b 风格硬约束 -- **禁用装饰**
- 每个 transition 必须在测试清单被引用（格式示例：`§接口契约 state Created→Paid`）

**边界决策表**（接口契约每个带范围约束的参数）：

| 参数 | 最小值 | 最大值 | 空/Null | 边界行为 |
|------|--------|--------|---------|----------|

**错误处理表**（接口契约每个 Raises 条目）：

| 条件 | 检测方式 | 响应 | 恢复 |
|------|----------|------|------|

规则：
- 边界表覆盖每个带范围约束的参数
- 错误处理表覆盖每个 Raises 条目
- §11.6 合规：错误处理遵循 §11.6 模式

### 2c. 沉淀章节填充（TDD 硬消费契约）

下游 TDD Red / Green / Refactor SubAgent **仅读 feature.md**，不再回访 SRS / Design。因此必须在此一次性沉淀上游约束。

**(A) §全局约束摘录**（必有；内容按以下规则填充）：

1. **§11.1 强制内部库（仅本特性涉及的领域）**：
   - 对设计文档 §11.1 全表每行，判断该行"领域"是否与本特性 §接口契约 或 §实现摘要 涉及操作有交集
   - 命中行 → 复制到 feature.md `## 全局约束摘录` / `### §11.1 强制内部库（仅本特性涉及的领域）` 表（列：领域 / 强制库 / 被替代方案 / 导入模式）
   - 若本特性不涉及 §11.1 任一领域 → 写 "本特性未触及 §11.1 任一领域。"
   - 若设计文档 §11.1 表为空 → 写 "N/A — design §11.1 empty"

2. **§11.5 命名约定（全表）**：
   - 一字不差摘录设计文档 §11.5 全表（命名规则贯穿所有特性，不做子集裁剪）
   - 若 §11.5 为空 → 写 "N/A — design §11.5 empty"

3. **§11.6 错误处理模式**：
   - 一字不差摘录设计文档 §11.6 全段
   - 若 §11.6 为空 → 写 "N/A — design §11.6 empty"

4. **溯源行**（章节末尾必写）：`> 摘自 Design §11.1 / §11.5 / §11.6 — commit <short-sha>，date YYYY-MM-DD`
   - `<short-sha>` = `git rev-parse --short HEAD`
   - `YYYY-MM-DD` = 今日日期

**(B) §静态分析与质量工具命令**（必有）：

1. **§11.4 静态分析命令**：
   - 复制设计文档 §11.4 每行（工具 / 命令字符串 / 适用范围）
   - 命令字符串必须是可执行完整命令（TDD Refactor 直接运行）
   - 若 §11.4 为空 → 写 "N/A — Design §11.4 为空，无静态分析门禁。"

2. **§11.7 覆盖率与变异阈值**：
   - 复制设计文档 §11.7 每行（指标 / 阈值 / 来源）
   - 若 §11.7 为空 → 写 "N/A — Design §11.7 未指定阈值。"

3. **溯源行**（章节末尾必写）：`> 摘自 Design §11.4 / §11.7 — commit <short-sha>，date YYYY-MM-DD`

**完整性自检**（Verdict 前）：
- §全局约束摘录 三子节（§11.1 / §11.5 / §11.6）均存在（显式 N/A 标注也算存在）→ 否则 Verdict=FAIL
- §静态分析与质量工具命令 两子节（§11.4 / §11.7）均存在 → 否则 Verdict=FAIL
- 两章节末尾各有溯源行 → 否则 Verdict=FAIL

### 3. 实现摘要

从系统设计 §4.N 派生本功能的文件/类变更增量。**本章节是 TDD Red/Green/Refactor 的必读约束**。

| 文件 | 类/模块 | 动作 | 变更描述 | 关键设计决策 |
|------|---------|------|----------|--------------|

规则：
- 每行对应一个文件/类变更，动作为 NEW 或 MODIFY
- 变更描述精确到方法级：添加什么方法、修改什么行为、关键逻辑要点（如算法选择、分支策略、数据转换方式）
- 关键设计决策仅记录非显而易见的决策
- 与项目结构章节交叉验证：每个 [new]/[modified] 文件在此表中有对应行
- 足够具体使 Green 能据此实现，足够精炼避免冗余
- 在生成此表前，内部分析每个非平凡方法的分支条件、边界值和错误路径，分析结果体现在变更描述和上方的边界/错误表中
- **流程图嵌入规则**（触发：任一行的"关键设计决策"涉及 ≥3 个决策分支或异常路径）：在该行之后嵌入 `flowchart TD` mermaid 代码块，节点文本使用真实方法名/真实判定条件；遵循 §2b 风格硬约束 -- **禁用装饰**；此时"关键设计决策"散文只作图外注解（补充守卫含义、依据的 §11.6 模式等），不重述图中已明示的分支
- 每个决策节点必须在测试清单被引用（格式示例：`§实现摘要 flow branch#N`）

### 4. 测试清单

将此表作为最终设计步骤构建 -- 它将上述所有章节综合为具体的测试场景。

| ID | 类别 | 追踪到 | 输入/设置 | 预期 | 杀死哪个缺陷？ |
|----|------|--------|-----------|------|----------------|
| 1  | FUNC/happy | FR-xxx AC-1 | [具体值] | [精确结果] | [错误实现] |
| 2  | FUNC/error | §接口契约 Raises | [触发条件] | [异常类型 + 消息] | [缺失分支] |
| 3  | BNDRY/edge | §接口契约 边界决策 | [边界值] | [行为] | [偏移错误] |
| 4  | FUNC/logic | §实现摘要 | [前置条件 + 输入] | [预期结果] | [缺失逻辑] |
| 5  | INTG/db    | §接口契约 + 外部依赖 | [真实 DB 设置] | [数据持久化 + 可查询] | [连接未建立/错误表] |
| 6  | INTG/api   | §4.N 跨服务调用 | [真实 HTTP 端点] | [正确响应 schema] | [错误端点/超时未处理] |

类别格式：`MAIN/subtag`，其中 MAIN 为 `FUNC, BNDRY, SEC, UI, PERF, INTG` 之一，subtag 为自由标签。

> ID 为排序序号，不作为测试函数名前缀。TDD Red 应从类别+输入列派生描述性测试函数名（如 FUNC/error + "空字符串输入" → `test_validate_input_rejects_empty_string`）。

规则：
- 每个 SRS 验收标准（来自 srs_trace 需求）至少 1 行
- 负向测试（FUNC/error + BNDRY/*）>= 总行数的 40%
- "追踪到" 引用测试来源的设计章节
- "杀死哪个缺陷？" 指出此测试捕获的具体错误实现
- **UML 元素引用（强制）**：若 §设计对齐 / §接口契约 / §实现摘要 嵌入了 mermaid 图，每个图元素必须在"追踪到"列被至少一行引用：
  - sequenceDiagram 每条消息 → 格式 `§设计对齐 seq msg#N`
  - stateDiagram-v2 每条 transition → 格式 `§接口契约 state <From>→<To>`
  - flowchart TD 每个决策节点 → 格式 `§实现摘要 flow branch#N`
  - classDiagram 的 NEW/MODIFIED 节点 → 由 Green 消费（不需要独立测试引用，但 Refactor 会 grep 验证）

**集成测试行（INTG 类别）：**
- 有外部依赖的功能：每种依赖类型至少 1 个 `INTG/*` 行
- 纯计算无外部依赖：写入 "INTG: N/A -- 纯函数，无外部 I/O"

**与 TDD 的关系**：此表是 TDD Red 的主要输入。TDD Red 以此表为起点，可能根据实现发现添加测试。

**设计接口覆盖率门禁（强制）：**

1. 重新读取系统设计文档的 §4.N
2. 提取所有命名的函数、方法、端点、中间件、校验器和授权检查
3. 对每个命名项：确认至少一个测试清单行覆盖它
4. 零覆盖的 → 添加行（通常是错误/安全类别）
5. 添加后重新验证负向测试比例 >= 40%

### 验证检查清单
- [ ] 所有 SRS 验收标准（来自 srs_trace）追踪到接口契约后置条件
- [ ] 所有 SRS 验收标准（来自 srs_trace）追踪到测试清单行
- [ ] 边界决策表覆盖所有接口契约参数
- [ ] 错误处理表覆盖所有 Raises 条目
- [ ] 实现摘要覆盖项目结构中所有 [new]/[modified] 文件
- [ ] 测试清单负向测试比例 >= 40%
- [ ] §4.N 中命名的所有函数/方法至少有一个测试清单行
- [ ] 所有方法/类/参数名符合 §11.5 命名约定
- [ ] §11.1 强制库覆盖的所有操作使用这些库（接口契约中无被替代的方案）
- [ ] 现有代码复用章节记录了来自代码库探索和已通过依赖的所有可发现的可复用代码
- [ ] 需求相关行为扫描完成 -- 重叠的现有行为已记录或明确标注为不存在
- [ ] UML 图（若嵌入）节点/参与者/状态/消息均使用真实标识符，无 A/B/C 等代称
- [ ] 非类图的 UML（sequence / state / flowchart）不含色彩、图标、rect 框、classDef 等装饰
- [ ] 每个 UML 图元素（sequence 消息 / state transition / flow 决策分支）在测试清单"追踪到"列被至少一行引用
- [ ] §全局约束摘录 存在且三子节（§11.1 子集 / §11.5 全表 / §11.6 全段）齐全（空时有显式 N/A 标注）；末尾有溯源行
- [ ] §静态分析与质量工具命令 存在且两子节（§11.4 / §11.7）齐全（空时有显式 N/A 标注）；末尾有溯源行

---

## 结构化返回契约

设计文档完成后，请严格按照以下格式返回结果：

```markdown
## SubAgent Result: Feature Design
### Verdict: PASS | FAIL | BLOCKED | CLARIFY
### Summary
[1-3 sentences — what was designed, key architectural decisions, document completeness]
### Artifacts
- [docs/features/<id>-<slug>.md]: Feature detailed design document (path derived by `scripts/feature_paths.py design-doc --feature <id>`)
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Test Inventory Rows | N | ≥ SRS acceptance criteria count (from srs_trace) | PASS/FAIL |
| Negative Test Ratio | N% | ≥ 40% | PASS/FAIL |
| Verification Checklist | N/16 | 16/16 | PASS/FAIL |
| Design Interface Coverage | N/M | M/M | PASS/FAIL |
| §11 Compliance | N checked / M total | All checked | PASS/FAIL |
| Existing Code Reuse Items | N | ≥ 0 | INFO |
| UML Element Trace Coverage | N/M | M/M (M=0 时 N/A) | PASS/FAIL |
| Global Constraints Excerpt | 3/3 | §11.1 子集 + §11.5 全表 + §11.6 全段（N/A 算存在） | PASS/FAIL |
| QA Tooling Commands Excerpt | 2/2 | §11.4 命令 + §11.7 阈值（N/A 算存在） | PASS/FAIL |
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
### Ambiguities (only if CLARIFY)
| # | Category | Source | Description | Impact | Suggested Interpretation | Question |
|---|----------|--------|-------------|--------|--------------------------|----------|
### Assumptions Made (only if PASS with assumptions)
| # | Category | Source | Assumption | Rationale |
|---|----------|--------|------------|-----------|
### Next Step Inputs
- feature_design_doc: [path to the design document]
- test_inventory_count: [number of test inventory rows]
- ambiguity_count: [number of unresolved ambiguities, 0 if PASS]
- assumption_count: [number of assumptions made, 0 if none]
- constraint_compliance: [PASS/FAIL]
- reuse_items_count: [number of REUSE/EXTEND/PATTERN items]
- requirement_behavior_items: [number of requirement-related behavior discoveries]
```

**重要**：将设计文档写入磁盘的指定输出路径。协调器期望在此 SubAgent 完成后文件存在。
