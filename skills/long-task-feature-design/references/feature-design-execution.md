# 功能级详细设计 -- SubAgent 执行参考

你是功能设计执行 SubAgent。请严格遵循以下规则。完成后，使用本文档底部的**结构化返回契约**返回结果。

---

# 功能级详细设计

为单个功能生成详细设计，衔接系统级设计（§4.N）与 TDD 实现。

系统设计回答"存在哪些类、它们如何交互"。
本技能回答"每个方法内部做什么、可能出什么问题、可以利用哪些现有行为"。

## 输入

在编写任何设计内容之前，请读取以下全部内容：

1. **功能对象** -- 来自 feature-list.json 的 ID、标题、描述、srs_trace、依赖、优先级（如有 verification_steps）
2. **系统设计章节** -- 设计文档中完整的 §4.N（读取整个子章节，不要用 grep）
3. **SRS 需求** -- SRS 文档中完整的 FR-xxx
4. **约束与假设** -- feature-list.json 根级别
5. **现有代码** -- 如果依赖功能已通过，读取其公开接口（导入、类/函数签名）
6. **内部 API 契约**（如 §6.2 存在）-- 来自设计文档第 6.2 节，读取当前功能作为 Provider 或 Consumer 的行。这些定义了跨功能 schema，本功能的接口契约（§3）必须与之对齐。
7. **代码库约定与约束** -- 完整读取设计文档 §11。提取并保持在工作记忆中：
   - §11.1：强制内部库表（领域、库、替代、导入模式）
   - §11.2：禁止 API 表（禁止项、原因、替代方案）
   - §11.3：批准的第三方库（用途、库、版本）
   - §11.5：命名约定表（规则、约定）
   - §11.6：错误处理模式描述
   §11 在设计文档中始终存在。空表意味着该类别无约束。

## 模板

使用 `skills/long-task-feature-design/references/feature-design-template.md` 作为结构模板。复制模板，为目标功能填充每个章节。

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
| `CONSTRAINT-CONFLICT` | §11 代码库约定与功能需求冲突 -- 例如 §11.1 强制使用的内部库缺少功能所需的能力（流式、特定协议、批量大小），或 §11.2 禁止的 API 是功能 SRS 明确要求的 |

**扫描流程：**

1. 对每个 SRS 验收标准（来自 srs_trace 需求）：检查是否包含可衡量、具体、可测试的条件。标记缺少数值阈值或具体行为的模糊语言 → `SRS-VAGUE`
2. 对映射到本功能的每个 SRS 需求：与设计 §4.N 交叉参照。标记接口类型、数据格式、行为或错误处理上的矛盾 → `SRS-DESIGN-CONFLICT`
3. 对每个 SRS 验收标准：验证 Given/When/Then 存在且有明确的预期结果 → `SRS-MISSING`
4. 对本功能作为 Provider 或 Consumer 的 §6.2 契约：检查 schema 是否完整（无缺失字段、无模糊类型） → `DEP-AMBIGUOUS`
5. 对每个非空的 §11.1 行：检查功能需求是否要求超出强制库已知 API 的能力。对每个非空的 §11.2 行：检查功能的 SRS 验收标准是否明确要求被禁止的 API → `CONSTRAINT-CONFLICT`

**对检测到的每个歧义，生成结构化记录：**
```
- Category: [分类代码]
- Source: [文档路径 + 章节/行引用]
- Description: [歧义内容]
- Impact: [哪些设计章节无法在未解决的情况下完成 -- 例如 "§3 接口契约后置条件"、"§7 测试清单预期结果"]
- Suggested interpretation: [SubAgent 基于上下文的最佳猜测（如有）；无合理解释则填 "none"]
- Question for user: [具体、可操作的问题，用于消除歧义]
```

**对于 `category: "bugfix"` 功能**：仅对缺陷的验收标准扫描 `SRS-VAGUE` 和 `SRS-DESIGN-CONFLICT`。

**决策门禁：**
- **未检测到歧义** → 正常进入步骤 2。不增加额外流程。
- **所有歧义都有合理的建议解释，且影响仅限于非关键章节**（不影响接口契约签名、测试清单预期结果或跨功能 §6.2 契约） → 带假设继续。将每个假设记录在设计文档的 `## 澄清附录` 章节，Authority = "assumed"。设置 Verdict 为 `PASS`。在 `### Next Step Inputs` 中包含假设数量。
- **任何歧义具有高影响**（影响接口契约签名、测试清单预期结果或跨功能契约）**或无合理的建议解释** → 设置 Verdict 为 `CLARIFY`。在结构化返回契约中包含完整的歧义表。不要进入步骤 2 -- 协调器将收集用户回答并重新分派。

> **带澄清附录重新分派时**：如果 SubAgent 提示词包含 `## Clarification Addendum (user-approved resolutions)` 章节，将这些决议视为权威约束。不要重新标记为歧义。将它们作为原始 SRS/设计文档的一部分纳入设计。

### 1c. 现有实现发现

**原则 -- 最大化复用**：优先导入现有代码而非编写新代码。重复现有功能是设计缺陷。

加载上下文后、编写设计内容之前，发现所有可复用代码 -- 先通过广泛的代码库探索，再通过精确的依赖扫描。结果合并到统一的 "## 现有代码复用" 章节。

#### 阶段 A：代码库探索（仅限存量项目）

**触发条件**：`docs/rules/` 存在且包含 >=1 个 `.md` 文件，或源文件 > 3。
**跳过条件**：新建项目。标注 "新建项目 -- 无代码库可探索。" 并进入阶段 B。

1. 从功能输入中提取焦点：
   - 功能标题/描述 + SRS 文本 → 领域关键词
   - 设计 §4.N → 架构区域
   - 推断 `--focus`：数据功能 → `dataflow,architecture,deps`；API → `api,architecture,deps`；业务逻辑 → `domain,architecture,deps`；横切关注点 → `architecture,deps`
   - 如果 §4.N 有局部定位，推断 `--path`

2. 确定深度（不要硬编码）：

   | 信号 | 深度 |
   |------|------|
   | <=1 个依赖，单类范围 | quick |
   | 2+ 个依赖或多个 SRS 追踪 | standard |
   | 横切关注点（认证、日志、中间件） | standard |

   有疑问时省略，让基于 LOC 的自动检测决定。

3. 分派：
   > **DISPATCH** 独立 SubAgent -- 加载并执行 `long-task:long-task-explore`
   > Depth: {determined_depth or omit}
   > Focus: {inferred_dimensions}
   > Path: {inferred_path or "."}
   > User question: "Find reusable code for feature: {feature_title}. SRS: {srs_summary}. Look for: utilities, API clients, data access, error helpers, base classes, middleware, factories relevant to this feature."

4. 消费 `docs/explore/codebase-research.md`：
   - 架构 → 基类、工厂、中间件 → EXTEND/PATTERN
   - 领域 → 校验器、业务逻辑 → REUSE
   - 依赖 → API 客户端、服务连接器 → REUSE
   - 数据流 → 模型、流水线 → REUSE/EXTEND

5. 将发现记录在 "## 现有代码复用" 中，标注 REUSE/EXTEND/PATTERN 标签。

**非阻塞** -- 如果 BLOCKED 或无发现，正常进入阶段 A-2。

#### 阶段 A-2：需求相关行为发现

**原则 -- 最大化复用现有相关逻辑**：除了发现可复用的代码模块外，还要理解与本功能 SRS 验收标准相关的现有代码库行为。重复现有行为（即使代码结构不同）也是设计缺陷。

**触发条件**：与阶段 A 相同（存量项目）。如果阶段 A 被跳过（新建项目），也跳过此阶段。

1. 从功能的 SRS 验收标准中提取行为关键词：
   - 解析 srs_trace 需求中的每个 Given/When/Then
   - 识别动作动词（例如 "validate"、"calculate"、"transform"、"authenticate"）
   - 识别领域名词（例如 "user"、"order"、"permission"、"score"）
   - 组合为搜索模式：`{verb}_{noun}`、`{noun}_{verb}`、领域特定术语

2. 在源代码中搜索现有行为：
   - 在源文件中 Grep 行为关键词（排除测试文件、配置、文档）
   - 限制在前 10 个匹配文件以控制 token 预算
   - 对每个匹配：读取周围的函数/类以理解存在什么行为
   - 关注：这段代码做什么？它执行什么业务规则？它处理什么边界情况？

3. 与功能需求交叉参照：
   - 对每个 SRS 验收标准，检查现有代码是否已处理（完全或部分）
   - **完全重叠**：现有代码满足标准 → 标记为 REUSE（可能已在阶段 A 发现中 -- 去重）
   - **部分重叠**：现有代码处理标准的一部分 → 标记为 EXTEND 并进行差距分析
   - **相邻行为**：现有代码处理类似但不同的场景 → 标记为 PATTERN（为一致性提供设计参考，防止矛盾行为）

4. 将发现记录在 "现有代码复用" 章节的 "需求相关现有行为" 子章节中：

   | # | SRS 标准 | 现有行为 | 源文件 | 重叠度 | 设计影响 |
   |---|----------|----------|--------|--------|----------|
   | 1 | [AC 引用] | [现有代码的功能] | [file:line] | [完全/部分/相邻] | [复用/扩展/模式 -- 具体建议] |

**非阻塞** -- 如果未发现重叠行为，标注："本功能需求与现有行为无重叠。" 并继续。

#### 阶段 B：依赖功能扫描

1. 从功能对象的 `dependencies[]` 中，列出所有 `"status": "passing"` 的功能
2. 对每个已通过的依赖功能，读取其实现文件（来自功能设计的项目结构或源码树）并编目（跳过阶段 A 中已发现的项目）：

   | 发现类别 | 查找内容 | 记录 |
   |----------|----------|------|
   | 工具函数 | 共享校验器、格式化器、解析器、类型转换器 | 函数名、文件路径、签名、用途 |
   | API 客户端实现 | HTTP 客户端、SDK 包装器、服务连接器 | 类/模块、文件路径、目标服务、可用方法 |
   | 数据访问模式 | Repository 类、ORM 模型、查询构建器 | 类、文件路径、实体/表、CRUD 方法 |
   | 错误处理辅助 | 自定义异常类、错误中间件、Result 类型 | 类/类型名、文件路径、使用模式 |
   | §11.1 库使用模式 | 强制内部库的实际导入和调用方式 | 导入语句、典型调用点（含 file:line） |

3. 对每个非空行的 §11.1 强制库：在已通过的功能中找到至少一个具体使用示例。记录导入模式和典型调用点。如果尚无使用（第一个需要它的功能），标注："首次使用 -- 按 §11.1 导入模式实现。"

4. 将所有发现记录在 "## 现有代码复用" 章节中。对每个项目，指定以下之一：
   - **REUSE**：直接导入并调用现有代码
   - **EXTEND**：扩展/继承现有代码
   - **PATTERN**：遵循相同的结构模式但创建自己的实现

**如果零个已通过依赖且阶段 A 未返回可复用项**：写入 "未发现可复用代码 -- 所有 §11.1 库使用直接遵循导入模式。" 并继续。

### 2. 组件数据流图

展示本功能的内部组件及运行时数据在它们之间的流动方式。这不是系统设计类图的副本 -- 它是一个**运行时数据流视图**，展示数据如何进入、如何转换、如何输出。

要求：
- Mermaid `graph` 或 `flowchart` 格式
- 用数据类型标注边（组件间流动的内容）
- 将外部依赖显示为虚线边框框
- 每个组件映射到一个待实现的类或模块

> **跳过规则**：如果功能是单类、单方法且无内部组件协作，写入 "N/A -- 单类功能，见下方接口契约"

### 3. 接口契约

对本功能暴露或修改的每个公共方法：

| 方法 | 签名 | 前置条件 | 后置条件 | 异常 |
|------|------|----------|----------|------|
| name | 完整类型签名 | 调用前必须为真的条件 | 调用后保证的条件 | 异常 + 条件 |

规则：
- 前置条件使用 SRS 验收标准中的 Given/When 风格
- 后置条件必须具体且可测试（不是 "返回正确结果"）
- 每个 SRS 验收标准（来自 srs_trace 需求）必须追踪到至少一个方法的后置条件
- 仅在包含非平凡逻辑时才包含内部方法
- **§6.2 对齐规则**：对于产生或消费跨功能数据的方法，方法签名（参数、返回类型）必须与设计文档第 6.2 节定义的 schema 兼容。如果功能是 **Provider**，后置条件必须保证 Response Schema。如果是 **Consumer**，前置条件必须假设 Request Schema 格式。任何偏差需要在设计理由中明确说明，并触发下方的契约偏差协议。
- **§11.5 命名合规**：所有方法、参数和类名必须遵循 §11.5 命名约定。如果 §11.5 记录 `snake_case` 而设计命名方法为 `getUserData`，则改为 `get_user_data`。
- **§11.1 库合规**：对于执行 HTTP 调用、DB 查询、文件 I/O、日志记录或 §11.1 强制库覆盖的其他操作的方法：在 Raises 列后添加 "Uses" 注释 -- 例如 "Uses: @company/http (§11.1)"。方法签名不得假设直接使用被替代的 API（例如，当 §11.1 替代 axios 时，不要类型提示 `axios.Response`）。
- **§11.2 禁止 API 检查**：如果任何方法的前置条件、后置条件或 Raises 引用了 §11.2 禁止列表中的 API，这是设计缺陷。在继续之前替换为 §11.2 指定的替代方案。
- **现有代码复用检查**：对接口契约中的每个方法，交叉检查 "现有代码复用" 章节。如果现有代码提供标记为 REUSE 的等效功能，不要创建新方法 -- 引用现有方法。如果是 EXTEND，将方法设计为现有类的重写/扩展。

### 契约偏差协议

如果在功能设计过程中，发现 §6.2 契约不正确、不充分或技术上不可行：

1. **不要静默偏差** -- 不匹配的契约将导致集成失败
2. **在设计文档的设计理由章节记录偏差**：
   - 契约 ID（例如 IAPI-001）
   - 原始 schema vs. 建议变更
   - 变更的技术原因
   - 对 Consumer 功能的影响（列出受影响的功能 ID）
3. **设置 Verdict 为 BLOCKED**，Issue："契约偏差需要设计更新"
4. 协调器（long-task-work）将通过 AskUserQuestion 上报用户
5. 如果批准：用户更新设计文档中的 §6.2；协调器重新分派 SubAgent
6. 如果拒绝：SubAgent 必须遵守原始契约

### 4. 内部序列图

展示本功能实现内部的方法间调用。与系统设计的序列图（系统级流程）不同，这展示功能自身的类/函数的协作。

要求：
- Mermaid `sequenceDiagram` 格式
- 必须覆盖主要成功路径
- 必须覆盖接口契约中每个 Raises 条目的至少一个错误路径
- 参与者是功能自身的类/函数

> **跳过规则**：如果功能只有一个类且无值得绘图的内部跨方法委托，写入 "N/A -- 单类实现，错误路径记录在算法 §5 错误处理表中"

### 5. 算法 / 核心逻辑

对每个非平凡方法（超出简单委托或 CRUD 的任何方法）：

**a) 流程图**（Mermaid `flowchart TD`）：
- 每个分支条件的决策节点
- 转换的处理节点
- return/raise 的终止节点

**b) 伪代码**：
```
FUNCTION name(param1: Type, param2: Type) -> ReturnType
  // Step 1: [major step]
  // Step 2: [formula or key decision]
  //         e.g., score = Σ 1/(k + rank_i) for each list
  // Step 3: [edge case handling]
  //         IF input_list is empty THEN return []
  RETURN result
END
```

**c) 边界决策表**：

| 参数 | 最小值 | 最大值 | 空/Null | 边界行为 |
|------|--------|--------|---------|----------|
| [param] | [val] | [val] | [行为] | [行为] |

**d) 错误处理表**：

| 条件 | 检测方式 | 响应 | 恢复 |
|------|----------|------|------|
| [条件] | [如何检测] | [异常或默认值] | [调用方操作] |

**e) §11 库使用映射：**

对每个非平凡方法，识别必须使用的 §11.1 强制库和 "现有代码复用" REUSE 项（来自代码库探索和依赖扫描）：

| 方法 | 操作 | 必需库/复用项 | 导入模式 | 替代 |
|------|------|---------------|----------|------|
| [method] | [e.g., HTTP GET to external API] | [e.g., @company/http (§11.1)] | [e.g., `from company.http import get`] | [e.g., requests.get, urllib] |
| [method] | [e.g., validate email format] | [e.g., REUSE: validate_email() from Feature #2] | [e.g., `from src.utils.validators import validate_email`] | [new implementation] |

伪代码中的错误处理：遵循 §11.6 错误处理模式。如果 §11.6 记录 "自定义 Error 子类 + 集中处理器"，伪代码中的 RAISE 语句必须使用项目自定义错误类，而非通用异常。

> **跳过规则**：如果方法无外部 I/O 且无适用的可复用项，写入 "N/A -- 纯计算，无库依赖"

> **跳过规则**：如果方法是纯委托（调用另一个服务、返回结果），写入 "委托给 [X] -- 见功能 #N" 而非完整算法章节。空章节且无明确跳过说明是缺陷。

### 6. 状态图（如适用）

对管理有状态对象（具有生命周期的实体）的功能：

- Mermaid `stateDiagram-v2` 格式
- 所有有效状态和转换
- 转换触发器（事件/方法调用）
- 转换上的守卫条件

> **跳过规则**：如果不存在对象生命周期，写入 "N/A -- 无状态功能"。大多数查询/转换功能是无状态的。

### 7. 测试清单

将此表作为最终设计步骤构建 -- 它将上述所有章节综合为具体的测试场景。

| ID | 类别 | 追踪到 | 输入/设置 | 预期 | 杀死哪个缺陷？ |
|----|------|--------|-----------|------|----------------|
| A  | FUNC/happy | FR-xxx AC-1 | [具体值] | [精确结果] | [错误实现] |
| B  | FUNC/error | §3 Raises 行 | [触发条件] | [异常类型 + 消息] | [缺失分支] |
| C  | BNDRY/edge | §5c 边界表 | [边界值] | [行为] | [偏移错误] |
| D  | FUNC/state | §6 转换 | [前状态 + 事件] | [后状态] | [缺失守卫] |
| E  | INTG/db    | §3 方法 + 外部依赖 | [真实 DB 设置] | [数据持久化 + 可查询] | [连接未建立/错误表] |
| F  | INTG/api   | §4.N 跨服务调用 | [真实 HTTP 端点] | [正确响应 schema] | [错误端点/超时未处理] |

类别格式：`MAIN/subtag`，其中 MAIN 为 `FUNC, BNDRY, SEC, UI, PERF, INTG` 之一，subtag 为自由标签。

规则：
- 每个 SRS 验收标准（来自 srs_trace 需求）至少 1 行
- 负向测试（FUNC/error + BNDRY/*）>= 总行数的 40%
- "追踪到" 引用测试来源的设计章节
- "杀死哪个缺陷？" 指出此测试捕获的具体错误实现

**集成测试行（INTG 类别）：**
- 对有外部依赖（DB、HTTP 服务、文件系统、第三方 SDK）的功能：每种依赖类型至少添加 1 个 `INTG/*` 行
- 来源：与外部系统交互的接口契约（§3）方法 + 设计文档外部依赖规格
- "追踪到" = §3 方法 + 具体外部依赖
- "杀死哪个缺陷？" = 单元 mock 会遗漏的连接/集成故障
- 如果功能是纯计算无外部依赖：写入 "INTG: N/A -- 纯函数，无外部 I/O"（与 TDD 规则 5 豁免一致）

**与 TDD 的关系**：此表是 TDD Red（long-task-tdd 步骤 1）的主要输入。TDD Red 以此表为起点，可能根据其规则 1-5（类别覆盖率、断言质量、真实测试需求）添加测试。测试清单提供设计驱动的场景；TDD 添加编码过程中发现的实现驱动场景。

**设计接口覆盖率门禁（强制 -- 作为最终设计质量检查执行）：**

1. 重新读取系统设计文档的 §4.N
2. 提取所有命名的函数、方法、端点、中间件、校验器和授权检查（例如 `check_repo_access`、`validate_input`）
3. 对每个命名项：确认至少一个测试清单行练习它（在 "追踪到" 或 "输入/设置" 列中匹配）
4. 如果任何设计指定的函数在测试清单中零覆盖率：
   - 添加行 -- 通常是错误/安全类别
   - 设置 "追踪到" = 具体设计章节（例如 "§4.5.3 ACL 检查"）
5. 添加后重新验证负向测试比例 >= 40%

这是防止规格漂移的主要防线。如果设计说 "check_repo_access 执行 ACL" 但没有测试行覆盖它，TDD 阶段将静默跳过 -- 导致后期发现并触发级联的 mock 设置成本。

### 验证检查清单
- [ ] 所有 SRS 验收标准（来自 srs_trace）追踪到接口契约后置条件
- [ ] 所有 SRS 验收标准（来自 srs_trace）追踪到测试清单行
- [ ] 算法伪代码覆盖所有非平凡方法
- [ ] 边界表覆盖所有算法参数
- [ ] 错误处理表覆盖所有 Raises 条目
- [ ] 测试清单负向测试比例 >= 40%
- [ ] 每个跳过的章节有明确的 "N/A -- [原因]"
- [ ] §4.N 中命名的所有函数/方法至少有一个测试清单行
- [ ] 所有方法/类/参数名符合 §11.5 命名约定
- [ ] §11.1 强制库覆盖的所有操作使用这些库（接口契约或算法中无被替代的方案）
- [ ] 现有代码复用章节记录了来自代码库探索和已通过依赖的所有可发现的可复用代码
- [ ] 需求相关行为扫描完成 -- 重叠的现有行为已记录或明确标注为不存在

## 图表质量规则

具体、可验证的规则：

- **组件/流程图**：每条边标注数据类型；每个节点映射到类/模块
- **序列图**：包含所有分支的 alt/opt/loop 块；显示返回类型；参与者名称匹配 §2 中的类名
- **流程图**：每个决策节点恰好 2 个出口；无条件标签的转换不允许存在
- **状态图**：从初始状态可达每个状态；每个终态可达；无孤立状态；模糊转换上的守卫条件
- **增量变更追踪**（当 feature.wave > 0 且存在先前功能设计时）：按设计模板图表变更追踪约定应用可视化变更标记。新节点/状态/参与者使用绿色样式（`classDef newNode fill:#d1fae5,stroke:#2ea043,stroke-width:2px` 或按图表类型等效）；修改的元素使用琥珀色样式（`classDef modNode fill:#fef3c7,stroke:#d4a017,stroke-width:2px`）。在每个受影响的图表前包含图例。移除前一批次的标记。

## 显式跳过规则

每个章节（§2-§6）必须满足以下之一：
- 包含上述要求的完整内容，或
- 标注 "N/A -- [该章节不适用的具体原因]"

空或半填充的章节是阻塞 TDD 的设计缺陷。标注 "N/A" 但无原因也是缺陷。

---

## 结构化返回契约

设计文档完成后，请严格按照以下格式返回结果：

```markdown
## SubAgent Result: Feature Design
### Verdict: PASS | FAIL | BLOCKED | CLARIFY
### Summary
[1-3 sentences — what was designed, key architectural decisions, document completeness]
### Artifacts
- [docs/features/YYYY-MM-DD-<feature-name>.md]: Feature detailed design document
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Sections Complete | N/8 | 8/8 (or N/A justified) | PASS/FAIL |
| Test Inventory Rows | N | ≥ SRS acceptance criteria count (from srs_trace) | PASS/FAIL |
| Negative Test Ratio | N% | ≥ 40% | PASS/FAIL |
| Verification Checklist | N/12 | 12/12 | PASS/FAIL |
| Design Interface Coverage | N/M | M/M | PASS/FAIL |
| §11 Compliance | N checked / M total | All checked | PASS/FAIL |
| Existing Code Reuse Items | N | ≥ 0 | INFO |
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
### Ambiguities (only if CLARIFY)
| # | Category | Source | Description | Impact | Suggested Interpretation | Question |
|---|----------|--------|-------------|--------|--------------------------|----------|
| 1 | [code] | [doc § section] | [what is ambiguous] | [affected design sections] | [best guess or "none"] | [specific question for user] |
### Assumptions Made (only if PASS with assumptions)
| # | Category | Source | Assumption | Rationale |
|---|----------|--------|------------|-----------|
| 1 | [code] | [doc § section] | [what was assumed] | [why this is reasonable] |
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
