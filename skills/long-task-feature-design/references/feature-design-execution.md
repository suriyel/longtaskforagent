# Feature-Level Detailed Design — SubAgent 执行参考

你是 Feature Design 执行 SubAgent。严格遵循以下规则。完成后，使用本文件底部的 **Structured Return Contract** 返回结果。

---

# Feature-Level Detailed Design（特性级详细设计）

为单一特性产出详细设计，在系统级设计（§2.N）与 TDD 实现之间搭桥。

系统设计回答 "WHAT classes exist and HOW they interact."
本 skill 回答 "WHAT each method does（签名 + 前置 / 后置条件层面）、WHAT can go wrong、要复用的既有代码，以及 HOW to test it."

**设计哲学 — 务实精简**：本文档不产出 pseudocode 或任务分解；实现细节用散文（"Implementation Summary"）— 代码本身是权威实现来源。TDD 直接读取 Interface Contract + Boundary Conditions + Test Inventory。Mermaid UML（`classDiagram` / `sequenceDiagram` / `stateDiagram-v2` / `flowchart TD`）按 §2a 触发判据**条件嵌入**，每类图与下游 TDD Red/Green/Refactor 消费契约硬绑定；不满足判据则不画（画则是无消费者的 token 税）。图聚焦**方法内细粒度**（调用序 / 状态转换 / 分支流程），与系统设计 §4.N 的类/模块层零重叠。

## 输入

写任何设计内容**之前**先读完以下全部：

1. **Feature 对象**（来自 feature-list.json） — ID、title、description、srs_trace、ui flag、dependencies、priority（如有 verification_steps）
2. **系统设计章节** — 设计文档中完整的 §2.N（读整个子章节，不要用 grep）
3. **SRS 需求** — SRS 文档中完整的 FR-xxx
4. **UCD 章节**（若 `"ui": true`） — UCD 文档中的 component/page 提示词
5. **Constraints & assumptions**（来自 feature-list.json 根）
6. **相关 NFR** — SRS 中可追溯到本特性的 NFR-xxx
7. **存量代码复用候选** — 以签名、方法名模式、行为关键字在 codebase 中 grep 相似函数 / 类（见 §1c 流程）。最大化复用；**不**要重新实现已存在的东西。
8. **Internal API 契约**（若存在 §4） — 读 Design Section 4 中本特性作为 Provider 或 Consumer 出现的行。这些定义了本特性 Interface Contract（§Interface Contract）必须对齐的跨特性 schema。
9. **存量代码库约束** — 若 `env-guide.md §4` 存在，读其中的强制内部库、禁用 API、命名约定、错误处理模式。所有新代码必须合规。

## 模板

使用 `skills/long-task-feature-design/references/feature-design-template.md` 作为结构模板。复制模板，为目标特性填充各章节。

## 检查清单

必须按顺序完成每一步：

### 1. 加载上下文

读取上文 "输入" 中列出的所有输入工件。

### 1b. 歧义扫描

读完全部输入、撰写任何设计内容**之前**，扫描可能影响设计正确性的规格歧义。此扫描使用以下分类：

| Code | What to check |
|------|---------------|
| `SRS-VAGUE` | 验收准则含模糊语言（"fast"、"user-friendly"、"appropriate"、"should handle"）且无可度量阈值或具体行为 |
| `SRS-DESIGN-CONFLICT` | SRS 需求与 Design §2.N 在接口类型、数据格式、行为或错误处理上矛盾 |
| `SRS-MISSING` | 验收准则无 Given/When/Then 或未指定预期结果 |
| `ATS-MISMATCH` | ATS 要求某测试类别（例如 SEC）但特性的可观察行为无对应表面 |
| `ATS-BUGFIX-REGRESSION-MISSING` | `category: "bugfix"` 特性，但 ATS 文档内无任何映射行的 `REQ-ID` 命中本特性 `srs_trace` 的任意 FR/NFR/IFR 编号（bugfix 必须有回归测试策略锚点） |
| `UCD-VAGUE` | 视觉需求不够具体，无法推导 DOM 选择器或可测试断言（仅 ui:true） |
| `DEP-AMBIGUOUS` | 跨特性接口不清晰 — 依赖的 §4 条目缺失或不完整 |
| `NFR-GAP` | 引用的 NFR 无可度量阈值（如 "should scale" 而无数字） |

**扫描流程：**

1. 对每条 SRS 验收准则（来自 srs_trace 需求）：检查是否含可度量、具体、可测试的条件。标记无数值阈值或具体行为的模糊语言 → `SRS-VAGUE`
2. 对映射到本特性的每条 SRS 需求：与 Design §2.N 交叉核对。标记接口类型、数据格式、行为或错误处理上的矛盾 → `SRS-DESIGN-CONFLICT`
3. 对每条 SRS 验收准则：验证 Given/When/Then 存在且显式给出预期结果 → `SRS-MISSING`
4. 对每个 ATS 要求的类别（若提供了 ATS 文档）：检查特性可观察行为是否具备该类别的可测表面 → `ATS-MISMATCH`
4b. 若 `category == "bugfix"` 且 ATS 文档存在：在 ATS 映射表中查找本特性 `srs_trace` 中的任一 FR/NFR/IFR ID。零命中 → `ATS-BUGFIX-REGRESSION-MISSING`。这是硬关卡：bugfix 必须绑定到回归测试策略，否则无法保证同类缺陷不再复现。
5. 对 UCD 章节（若 ui:true）：检查视觉需求是否指定具体颜色、字体、间距或选择器 → `UCD-VAGUE`
6. 对本特性为 Provider 或 Consumer 的 §4 契约：检查 schema 是否完整（无缺失字段、无歧义类型） → `DEP-AMBIGUOUS`
7. 对引用的 NFR：验证是否存在可度量阈值 → `NFR-GAP`

**对每个检测到的歧义，产出结构化记录：**
```
- Category: [code from taxonomy]
- Source: [document path + section/line reference]
- Description: [what is ambiguous]
- Impact: [which design sections cannot be completed without resolution — e.g., "§Interface Contract postcondition", "§Test Inventory expected result"]
- Suggested interpretation: [SubAgent's best guess based on context, if one exists; "none" if no reasonable interpretation]
- Question for user: [specific, actionable question that would resolve the ambiguity]
```

**对 `category: "bugfix"` 特性**：
- 扫描 `SRS-VAGUE`、`SRS-DESIGN-CONFLICT`（同 core 特性）。
- **强制**扫描 `ATS-BUGFIX-REGRESSION-MISSING`（若 ATS 文档存在）—— bugfix 没有回归锚点即违反"同类缺陷不再复现"原则。
- 跳过 `UCD-VAGUE`、`ATS-MISMATCH`（ATS 类别全覆盖）、`NFR-GAP`（bugfix 聚焦根因，而非全量规格覆盖）。

**决策关卡：**
- **未检测到歧义** → 正常进入 Step 1c。无额外摩擦。
- **所有歧义均有合理的建议解释，且影响仅限于非关键章节**（**不**影响 Interface Contract 签名、Test Inventory 预期结果、跨特性 §4 契约） → 以假设继续。将每条假设记录在设计文档的 `## Clarification Addendum` 章节，Authority = "assumed"。`status` 设为 `pass`。在 `next_step_input.assumption_count` 中包含 assumption 数量（主 agent 用该字段决定是否触发审批关卡）。
- **任一歧义有高影响**（影响 Interface Contract 签名、Test Inventory 预期结果或跨特性契约） **或无合理的建议解释** → `status` 设为 `blocked`。为每条高影响歧义追加一条 blockers[] 条目，严格使用前缀约定（见下表）。**不**要进入 Step 1c — orchestrator 会按 `skills/using-long-task/references/approval-revise-loop.md` 收集用户裁决并以 Clarification Addendum 重分发。
- **任一歧义类别为 `ATS-BUGFIX-REGRESSION-MISSING`** → 此类不可以 assumption 绕过。`status` 必须为 `blocked`（不能 `pass`），对应 blocker 的建议解释为 `"none — bugfix regression anchor required"`，主 agent 会呈 A/B/C 选项给用户。

### blockers[] 前缀约定（本 sub-skill）

返 `status: blocked` 时，每条 blockers[i] 应为**单行字符串**，格式：

```
[<PREFIX>] <Source §line>: <one-line description> | Suggested: <best-guess or "none"> | Q: <specific question>
```

| Prefix | 对应扫描类别 |
|--------|-------------|
| `[SRS-VAGUE]` | SRS-VAGUE |
| `[SRS-DESIGN-CONFLICT]` | SRS-DESIGN-CONFLICT |
| `[SRS-MISSING]` | SRS-MISSING |
| `[ATS-MISMATCH]` | ATS-MISMATCH |
| `[ATS-BUGFIX-REGRESSION-MISSING]` | ATS-BUGFIX-REGRESSION-MISSING |
| `[UCD-VAGUE]` | UCD-VAGUE |
| `[DEP-AMBIGUOUS]` | DEP-AMBIGUOUS |
| `[NFR-GAP]` | NFR-GAP |
| `[CONTRACT-DEVIATION]` | 发现 §4 契约技术不可行（Step 2 Contract Deviation Protocol）|

示例：
```
[SRS-VAGUE] SRS §5.1 FR-012: "should be fast" — no numeric threshold for login latency | Suggested: p95 < 500ms | Q: confirm latency budget or provide alternative
[ATS-BUGFIX-REGRESSION-MISSING] ATS mapping: srs_trace=[FR-201,NFR-004] has 0 rows in ATS table | Suggested: none — bugfix regression anchor required | Q: (A) add ATS mapping row / (B) re-categorize as core / (C) waive regression anchor
```

完整的 Ambiguities 扩展表仍输出（见下方 Return Contract），作为主 agent 为 AskUserQuestion 组装 A/B/C 选项时的补充参考，但 **blockers[] 是主 agent 分流的权威字段**。

> **携带 Clarification Addendum 重新分发时**：若 SubAgent 提示词含 `## Clarification Addendum (user-approved resolutions)` 章节，将这些处置视为权威约束。**不**要再把它们标记为歧义。按其已在原 SRS / Design 文档中存在那样纳入设计。

### 1c. 存量代码复用检查（强制 — 最大化复用原则）

**核心原则**：若既有代码已实现本特性所需，**复用**它。不要重实现。

**流程**：

1. 从特性的 Interface Contract 草稿（方法名、参数类型）、SRS 验收准则关键字与特性标题 / 描述中的领域名词推导**复用搜索词**。
2. **Grep 代码库**，每个词使用精确匹配与模糊变体：
   - 方法名：`<verb><Noun>` 与 `<verb>_<noun>` 变体（如 `findUser`、`find_user`）
   - 类名：主领域名词 + 常见后缀（`UserService`、`UserRepository`、`UserManager`）
   - 签名：从草稿 Interface Contract 提取的返回类型 + 参数类型组合
3. 对每个候选匹配：
   - 读取既有函数的签名、docstring / 注释及 5-10 行函数体
   - 判定：**covers** 本特性需求（直接复用） / **close，需扩展**（复用 + 扩展） / **unrelated**（跳过）
4. 在设计文档 **§Implementation Summary — Existing Code Reuse** 表中记录发现：
   - 为每个 `covers` / `close` 匹配填充一行
   - 若搜索 ≥3 个词后无匹配，写 `N/A — searched keywords: [<terms>], no reusable match`

**禁止**：若发现可复用匹配（`covers` 或 `close`），Interface Contract **必须**委托给它。默默重写可复用的 helper 是缺陷（TDD Refactor 的静态分析会捕捉，但在此处提前捕捉更好）。

**存量代码库约束绑定**（若 `env-guide.md §4` 存在）：
- §4.1 强制内部库：新代码**必须**为相应领域（HTTP、日志、配置等）使用这些库
- §4.2 禁用 API：新代码**不得**引用这些；若复用搜索发现禁用 API，不要复用 — 改搜已批准的替代
- §4.3 命名约定：新方法 / 类名必须遵循

### 2. Interface Contract

对本特性暴露或修改的每个**公开**方法：

| Method | Signature | Preconditions | Postconditions | Raises |
|--------|-----------|---------------|----------------|--------|
| name   | 完整带类型签名 | 调用前必须成立 | 调用后被保证 | 异常 + 条件 |

规则：
- Preconditions 使用 SRS 验收准则的 Given/When 风格
- Postconditions 必须具体可测（不是 "returns correct result"）
- 每条 SRS 验收准则（来自 srs_trace 需求）必须追溯到至少一个方法的 postcondition
- `Raises` 列是错误条件的权威来源 — TDD Rule 4 直接读取该列以推导负向测试
- 仅当内部方法含非平凡逻辑时才包含它
- **状态机方法**：若某公开方法行为依赖显式状态（状态数 ≥2 且存在 transition），在方法行下方嵌入 `stateDiagram-v2`；节点用真实状态名 + 真实事件名；遵守 §2b 风格硬约束；每个 transition 与守卫在 Test Inventory 被引用（见 §2a 追溯契约）
- **§4 对齐规则**：对产生或消费跨特性数据的方法，方法签名（参数、返回类型）**必须**与 Design Section 4 中定义的 schema 兼容。若本特性为 **Provider**，postconditions **必须**保证 Response Schema。若为 **Consumer**，preconditions **必须**假定 Request Schema 格式。任何偏离都需要在 Design Rationale 中显式说明并触发下文的 Contract Deviation Protocol。

### Contract Deviation Protocol（契约偏离协议）

若特性设计期间发现某 §4 契约不正确、不充分或技术不可行：

1. **不得**默默偏离 — 不匹配的契约会导致集成失败
2. 在设计文档的 Design Rationale 章节**记录偏离**：
   - Contract ID（如 IAPI-001）
   - 原始 schema vs. 建议变更
   - 变更的技术原因
   - 对 Consumer 特性的影响（列出受影响的 feature ID）
3. `status` 设为 **blocked**；追加 blocker：`[CONTRACT-DEVIATION] §4 <Contract ID>: <原 schema 摘要> → <建议变更> | 影响 Consumer=[<feature IDs>] | Q: (A) approve schema change / (B) keep original and SubAgent will comply`
4. orchestrator（long-task-work-design）按 `skills/using-long-task/references/approval-revise-loop.md` 处理，向用户呈 A/B 选项
5. 若批准：用户（或 orchestrator 在授权下）更新设计文档的 §4；orchestrator 以 Clarification Addendum 重分发 SubAgent
6. 若拒绝：Clarification Addendum 指令 "comply with original §4"，SubAgent 必须遵循原契约

### 2a. Design Alignment — UML 嵌入触发

方法内粒度（调用序 / 状态转换 / 分支流程）与系统设计 §4.N（类 / 模块层）零重叠。若图内容已在系统 §4.N 等价表达 → 在 §Design Alignment 写一行 `"见系统设计 §4.N"`，不重复画。

| 触发信号 | 图类型 | 嵌入位置 |
|---|---|---|
| ≥2 类 / 模块协作（含新增 / 修改） | `classDiagram` | §Design Alignment |
| ≥2 对象 / 服务的调用顺序 | `sequenceDiagram` | §Design Alignment |
| 方法依赖显式状态（状态数 ≥2 有 transition） | `stateDiagram-v2` | §Interface Contract 对应方法行下方 |
| 某方法含 ≥3 决策分支或异常路径 | `flowchart TD` | §Implementation Summary 对应段下方 |

**命名**：节点 / 参与者 / 状态 / 消息必须用真实标识符（`ClassName`、`methodName`、`StateName`、`EventName`）。**禁 A/B/C 代称**。

**Test Inventory 追溯契约**（图不画则无此要求；画了则强制）：
- 每条 `sequenceDiagram` 消息 → 至少一行 Test Inventory 的 `Traces To` 引用 `§Design Alignment seq msg#N`（N 为消息序号）
- 每个 `stateDiagram-v2` transition → 至少一行 `Traces To` 引用 `§Interface Contract state <src>→<dst>`；每个守卫 → 正反两例
- 每个 `flowchart TD` 决策菱形 / 错误终点 → 至少一行 `Traces To` 引用 `§Implementation Summary flow branch#N`

不满足触发判据的 → **不画**。装饰或代称违规 → §Verification Checklist 拦截。

### 2b. UML 风格硬约束 — DO / DON'T

| 主题 | DO | DON'T |
|---|---|---|
| `classDiagram` 节点 | `class OrderService { +placeOrder(req: OrderRequest): OrderId }` | `class A { +foo(): B }` |
| `classDiagram` 装饰 | `classDef NEW fill:#cfc,stroke:#080` + `class OrderService:::NEW`（唯一允许） | 其他 fill / stroke 超出 NEW / MODIFIED / EXISTING |
| `sequenceDiagram` 参与者 | `participant OrderService` | `participant A as A` |
| `sequenceDiagram` 消息 | `OrderService->>PaymentGateway: charge(amount)` | `A->>B: call()` |
| `stateDiagram-v2` 转换 | `Created --> Paid : paymentConfirmed` | `S1 --> S2 : e` |
| 非类图装饰 | 无任何色彩 / 图标 / rect / 皮肤 | `style X fill:#abc` / `classDef` 用在非 classDiagram / `rect rgb(...)` / 图标 / `<<stereotype>>` |
| 跨层重复 | 图内容系统 §4.N 已有 → 写 `"见系统设计 §4.N"` | 重画一份 |

### 2c. Visual Rendering Contract（`"ui": true` 强制）

对 `"ui": true` 的特性，指定用户必须看到的所有视觉元素。本契约是 TDD Rule 7（正向渲染测试）与 Feature-ST（渲染验证）的事实源。

**数据来源**：读取 SRS 需求的 `Visual output` 字段（用户看到的变化）+ UCD 的 component/page 提示词（外观）+ 系统设计 §2.N 的 UI/UX 方案。

**如何填写每列**：
- **Visual Element**：为用户看到的每个独立视觉物命名（如 "贪吃蛇身段"、"game board grid"、"score counter"、"food item"）。**不是**抽象概念如 "the UI" 或 "the page"。
- **DOM/Canvas Selector**：具体 CSS 选择器（`canvas#game-board`、`div.snake-segment`、`#score-display`）或 canvas 元素 ID。必须具体到 `document.querySelector()` 能找到。
- **Rendered When**：让此元素出现的触发器（页面加载、游戏开始、状态变化、用户动作）
- **Visual State Variants**：基于状态的不同外观（alive=green, dead=red；selected=blue border, unselected=grey）
- **Minimum Dimensions**：预期尺寸（每格 20x20px、全视口宽度等）
- **Data Source**：驱动渲染的数据（GameState.segments[]、API response、form input）

**正向渲染断言**：对每个元素，写出触发后**必须**视觉存在的可测陈述。不要写 "element is visible"，而应写 "canvas 在 game board 区域有非透明像素" 或 "div.snake-segment 数量等于 GameState.segments.length"。

**交互深度断言**：对每个交互元素，写出它响应哪种交互及产生的视觉变化。已渲染但不响应设计意图交互的元素即 "display-only" 缺陷。

> **跳过规则**：**仅当** `"ui": false` 才可写 "N/A — backend-only feature"。若 `"ui": true`，本节强制，不能跳过 — 即便特性"大部分偏后端"但 `"ui": true`。

### 3. Implementation Summary

写 **3-5 段散文**描述本特性将如何构建。每段聚焦以下一个方面：

1. **要创建或修改的主要类 / 函数** — 名称与文件，不重复 Interface Contract 签名
2. **调用链** — 运行时谁调谁（如 "HTTP handler → service → repository → DB"）
3. **关键设计决策或非显见约束** — 为何选此方法而非替代、要注意什么陷阱
4. **遗留 / 存量代码交互点** — 本特性触及哪些既有模块、如何与 `env-guide.md §4` 存量代码库约束对齐（强制内部库、禁用 API、命名约定）
5. **§4 Internal API Contract 集成** — 若本特性是 Provider/Consumer，如何满足共享 schema

**散文指南**：目标读者是后续实现代码的人。使用具体文件路径、类名、方法名。**不**包含 pseudocode — 代码本身是权威实现来源。若任一方法含 ≥3 决策分支或异常路径，在段下方嵌入 `flowchart TD`（按 §2a 触发表 + §2b 风格约束）：真实方法名 / 真实条件文本，散文仅保留图外决策理由注解。其余结构契约仍由 Interface Contract + Boundary Conditions + Test Inventory 承载。

### 3a. Boundary Conditions（除非显式 N/A 否则必填）

对每个带数值范围、大小或可空输入参数的方法，填此表：

| Parameter | Min | Max | Empty/Null | At boundary |
|-----------|-----|-----|------------|-------------|
| [param]   | [val] | [val] | [behavior] | [behavior] |

TDD Rule 4 依此表推导可能的错误实现测试。若特性无非平凡参数（按 ID 纯查询、flag 切换等），写 "N/A — no non-trivial boundary parameters"。

### 3b. Existing Code Reuse（来自 Step 1c）

填充 §Implementation Summary 中的 **Existing Code Reuse** 表：

| Existing Symbol | Location (file:line) | Reused Because |
|-----------------|---------------------|----------------|
| `UserRepository.findByEmail` | `src/repos/UserRepository.java:L42` | 既有查询已满足本特性的查找需求 |

若 Step 1c 未找到复用候选，写 "N/A — greenfield feature" 或 "N/A — searched keywords: [<terms>], no reusable match"。

### 4. Test Inventory

作为设计的**最后**一步构建此表 — 它综合 Interface Contract、Boundary Conditions 与 Visual Rendering Contract，形成具体的测试场景。

| ID | Category | Traces To | Input / Setup | Expected | Kills Which Bug? |
|----|----------|-----------|---------------|----------|-----------------|
| A  | FUNC/happy | FR-xxx AC-1 | [具体值] | [精确结果] | [可捕获的错误实现] |
| B  | FUNC/error | §Interface Contract Raises row | [触发] | [异常类型 + 消息] | [缺失分支] |
| C  | BNDRY/edge | §Implementation Summary Boundary Conditions | [边界值] | [行为] | [off-by-one] |
| D  | INTG/db    | §Interface Contract + required_configs | [真实 DB setup] | [数据已持久化且可查询] | [连接未建立 / 错表] |
| E  | INTG/api   | §2.N 跨服务调用 | [真实 HTTP 端点] | [正确响应 schema] | [错误端点 / 未处理 timeout] |

Category 格式：`MAIN/subtag`，MAIN 为 `FUNC, BNDRY, SEC, UI, PERF, INTG` 之一，subtag 为自由标签。

规则：
- 每条 SRS 验收准则（来自 srs_trace 需求）至少 1 行
- 负向测试（FUNC/error + BNDRY/*）>= 总行数 40%
- "Traces To" 引用测试所推导的设计章节
- "Kills Which Bug?" 指明本测试能捕捉的具体错误实现

**ATS 类别对齐**（若提供了 ATS 文档）：ATS 映射表中针对本特性需求列出的每个主要类别，**必须**在 Test Inventory 中至少作为一行 Category 前缀出现。例如，若 ATS 对 FR-005 要求 SEC，至少一行 Test Inventory 的 Category 必须为 `SEC/*`。缺失 ATS 类别 → 在进入 §5 前补充行。

**视觉渲染覆盖**（`"ui": true` 强制）：对 §Visual Rendering Contract 的每条正向渲染断言，至少添加一行 `UI/render` Test Inventory。"Traces To" = §Visual Rendering Contract 中的具体元素行。"Kills Which Bug?" = 本测试能捕捉的渲染失败（如 "render function never called"、"canvas blank"、"DOM element not appended"）。若 Visual Rendering Contract 列出 N 个视觉元素，至少要有 N 行 `UI/render`。

**集成测试行（INTG 类别）：**
- 对有外部依赖（DB、HTTP 服务、文件系统、第三方 SDK）的特性：每类依赖至少 1 行 `INTG/*`
- 来源：Interface Contract 中与外部系统交互的方法 + `required_configs[]` 中连接串类键
- "Traces To" = §Interface Contract 方法 + 具体外部依赖
- "Kills Which Bug?" = 单元 mock 会漏掉的连接 / 集成失败
- 若特性为无外部依赖的纯计算：写 "INTG: N/A — pure function, no external I/O"（与 TDD Rule 5 豁免一致）

**与 TDD 的关系**：本表是 TDD Red（`long-task-tdd-red`，由 `long-task-work-tdd` Step 3a 分发）的**主要输入**。TDD Red 以本表为起点，并可依其自身 Rule 1-5（类别覆盖、断言质量、真实测试要求）添加测试。Test Inventory 提供设计驱动场景；TDD 添加编码过程中发现的实现驱动场景。

**Design Interface Coverage Gate（最终化前强制执行）：**

1. 重新读取系统设计文档 §2.N
2. 提取**所有**具名函数、方法、endpoint、middleware、validator、鉴权检查（如 `check_repo_access`、`validate_input`）
3. 对**每个**具名项：确认至少一行 Test Inventory 使用它
   （在 "Traces To" 或 "Input / Setup" 列中匹配）
4. 若**任何**设计指定的函数无 Test Inventory 覆盖：
   - 添加行 — 通常为 error/security 类别
   - "Traces To" = 具体设计章节（如 "§4.5.3 ACL check"）
5. 补充后重新确认负向测试占比 ≥ 40%

这是对规格漂移的主要防线。若设计说 "check_repo_access enforces ACL" 而无测试行覆盖它，TDD 阶段会默默跳过 — 造成后期发现并引发连锁 mock-setup 成本。

### Verification Checklist
- [ ] 全部 SRS 验收准则（来自 srs_trace）已追溯到 Interface Contract postcondition
- [ ] 全部 SRS 验收准则（来自 srs_trace）已追溯到 Test Inventory 行
- [ ] Interface Contract Raises 列覆盖所有预期错误条件
- [ ] Boundary Conditions 表覆盖所有非平凡参数（或写明 "N/A" 并给出原因）
- [ ] Implementation Summary 为 3-5 段具体散文（含文件路径 + 类名），**非** pseudocode；若含 ≥3 决策分支方法，按 §2a 嵌入 `flowchart TD`
- [ ] Existing Code Reuse 表已填充（或写明 "N/A — greenfield" 并附搜索关键字）
- [ ] Test Inventory 负向占比 >= 40%
- [ ] ui:true 特性的 Visual Rendering Contract 完整（列出全部视觉元素、正向渲染断言已定义、交互深度断言已定义）
- [ ] 每个 Visual Rendering Contract 元素至少 1 行 UI/render Test Inventory
- [ ] UML 图（若存在）节点 / 参与者 / 状态 / 消息均使用真实标识符，无 A/B/C 代称
- [ ] 非类图（`sequenceDiagram` / `stateDiagram-v2` / `flowchart TD`）不含色彩 / 图标 / `rect` / 皮肤等装饰元素
- [ ] 每个图元素（类节点、sequence 消息、state transition、flow 决策分支 / 错误终点）在 Test Inventory "Traces To" 列被至少一行引用
- [ ] 每个跳过章节都写明 "N/A — [reason]"
- [ ] §2.N 中所有函数 / 方法都至少有一行 Test Inventory

## 跳过需显式规则

每个章节必须：
- 按上文要求包含**完整**内容，或
- 写明 "N/A — [具体原因说明为何本节不适用]"

空章或半填的章节是阻塞 TDD 的设计缺陷。只写 "N/A" 而无原因也是缺陷。

---

## Structured Return Contract

与 `skills/using-long-task/references/structured-return-contract.md` 中的统一契约对齐。严格按此格式返回：

```markdown
## SubAgent Result: long-task-feature-design

**status**: pass | fail | blocked
**artifacts_written**: ["docs/features/<id>-<slug>.md"] (omit if status=blocked before any draft was written)
**next_step_input**: {
  "feature_design_doc": "<path to the design document>",
  "test_inventory_count": <number of test inventory rows>,
  "existing_code_reuse_count": <number of reused symbols, 0 if greenfield>,
  "assumption_count": <number of assumptions made, 0 if none>
}
**blockers**: [
  "若 status=blocked：每条为单行字符串，以前缀开头（见上方前缀约定），格式：",
  "[<PREFIX>] <Source §line>: <desc> | Suggested: <best-guess or none> | Q: <question>",
  "若 status≠blocked：空数组"
]
**evidence**: [
  "Test Inventory: N rows covering <categories>",
  "Interface Contract: M public methods matched to <srs_trace> acceptance criteria",
  "Existing Code Reuse: K reused symbols (or 'greenfield feature' if 0)",
  "Internal API Contract §4: this feature is Provider/Consumer for <contract IDs>"
]

### Metrics (extension — for task-progress.md)
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Sections Complete | N/6 | 6/6 (or N/A justified) | PASS/FAIL |
| Test Inventory Rows | N | ≥ SRS acceptance criteria count (from srs_trace) | PASS/FAIL |
| Negative Test Ratio | N% | ≥ 40% | PASS/FAIL |
| Verification Checklist | N/14 | 14/14 | PASS/FAIL |
| Design Interface Coverage | N/M | M/M | PASS/FAIL |
| Existing Code Reuse | K reused / J searched | ≥0 | INFO |
| Visual Rendering Assertions | N | ≥ Visual Rendering Contract element count (ui:true) | PASS/FAIL/N/A |
| UML Element Trace Coverage | N/M | M/M (M = sequence msg + state transition + flow branch 总数；N = Test Inventory "Traces To" 引用数) | PASS/FAIL/N/A |

### Issues (extension — only if fail or blocked)
| # | Severity | Description |
|---|----------|-------------|

### Ambiguities (extension — only if status=blocked with spec-gap prefixes)
Parallel to `blockers[]`; each row corresponds to one blocker entry. Use this table when the one-line blocker string can't carry enough detail for the user. Main agent may include it verbatim in the AskUserQuestion context.

| # | Category | Source | Description | Impact | Suggested Interpretation | Question |
|---|----------|--------|-------------|--------|--------------------------|----------|
| 1 | [code] | [doc § section] | [what is ambiguous] | [affected design sections] | [best guess or "none"] | [specific question for user] |

### Assumptions Made (extension — only if pass with assumptions)
| # | Category | Source | Assumption | Rationale |
|---|----------|--------|------------|-----------|
| 1 | [code] | [doc § section] | [what was assumed] | [why this is reasonable] |
```

**重要**：将设计文档写入磁盘到指定的输出路径。orchestrator 期望此 SubAgent 完成后文件已存在。
