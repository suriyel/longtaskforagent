---
name: long-task-design
description: "当 SRS 存在但无设计文档和 feature-list.json 时使用 — 产出聚焦 HOW 的设计文档"
---

# 设计文档生成

输入：已批准 SRS + 可选 `docs/rules/` + 用户输入中可能已带的实现方案偏好。
动作：合成单一方案（用户指定则校核，未指定则直接推荐），经方案校核表确认偏差 → 内部装配整份草稿 → 落盘 `docs/plans/YYYY-MM-DD-<topic>-design.md`（**状态**: 待审批）→ Step 5c 审阅门批准。

<HARD-GATE>
在收到 Step 5c 审阅门的"批准"回复之前：
- 不可调用任何实现 skill（`long-task-init` / `long-task-ats` / Worker 系列 / 其他下游）
- 不可 `git commit` 设计文档（仅允许写入 `**状态**: 待审批` 草稿）
- 不可编写任何代码、搭建任何项目、运行 init_project.py 或采取任何实现行动

每个项目都适用，无论看起来多简单。
</HARD-GATE>

## Step 0 — 恢复审批

若 `docs/plans/*-design.md` 已存在，读首行元数据：

- `**状态**: 待审批` → 跳 Step 5c
- `**状态**: 已批准` → 终止，提示用户检查 `phase_route.py` 输出（本 skill 不应被触发）

否则继续 Step 1。

## Step 1 — 读 SRS

1. 读 `docs/plans/*-srs.md`
2. 提取设计驱动：FR 数量与优先级、硬性约束、外部接口需求、用户画像
3. **读 SRS 元数据**：提取 `输入档位`（L1 / L2 / L3）。下游 Step 1.6 / Step 2a-2c / Step 5b 按档位分支强度
4. 列出 SRS **§10 待解决问题**。若未解决项影响架构 → Step 2a 前 `AskUserQuestion` 解决

## Step 1.6 — 用户期望二次吸收（内部，不落盘，不与用户交互）

Design 阶段易陷入"只看 SRS 转写、不看原文"的细节断片。本 step 强制读用户原文做二次吸收，
作为方案收敛与 §1 设计驱动因素 / §6.2 内部 API 契约章节填写的依据（硬精确条目 1:1 复现锁定）。**纯认知操作，不落盘。**

1. 读用户输入文档原文（与 Requirements 同一份）
2. 按 Step 1 第 3 点提取的 `输入档位` 决定本 step 强度

### L1 输入：提取 H1-H4

| # | 期望项 | 例 |
|---|--------|---|
| H1 | 系统外观 / 部署形态 | 单机 / SaaS / 嵌入式 / CLI |
| H2 | 交付与运维形态 | Docker / 二进制 / 在线热更新 |
| H3 | 边界条件细节 | 用户原文中的具体数据规模 / 并发数 / 数据保留期 |
| H4 | 与 SRS §1.3 的呼应点 | 用户讲了什么动机，Design §1 必须回应 |

### L2/L3 输入：仅提取 H5

| # | 期望项 | 内容 |
|---|--------|------|
| H5 | 硬精确条目下游传递清单 | 参数名 / 文件路径 / 类型范围 / 默认值 / 枚举集合 — Design §6.2 内部 API 契约必须 1:1 复现，禁"美化" |

3. 笔记驱动 Step 3 方案收敛与 §1 / §3.4 填写。

**反模式**：
- L2/L3 输入花精力提取 H1-H4 — §1 设计驱动因素 / §3 架构概览 等章节在纯规约式增量场景下应整节标 `[不适用]`，H1-H4 无落点
- L1 输入忽略 H1-H4 — Design §1 设计驱动会与用户原意失联
- 任何档位忽视 H5（若有硬精确条目）— Design 用"领域化别名"替换原始参数名 → 实现阶段无法对齐

## Step 2a — 加载设计模板

用户指定路径优先，否则加载 `docs/templates/design-template.md`。验证 `.md` 且含 `## ` 标题。

- 模板含 §0 项目结构 / §1 设计驱动 / §3 架构（3.1-3.5，§3.4 技术栈决策承载单方案关键决策点）/ §4 关键功能设计 / §5 数据模型 / §6 API（6.1 外部 / 6.2 内部 API 契约含 6.2.1/6.2.2/6.2.3）/ §7 第三方依赖 / §8 测试策略 / §10 待解决问题 / §11 代码库约定
- **按需省略规则**：L2/L3 纯规约式增量场景，§1 / §3.1-§3.3 / §5 / §6.1 / §7 / §8 / §10 等可整节标 `[不适用]` + 附一句理由；§6.2 以 6.2.1 / 6.2.2 子表表达即可；**§3.4 技术栈决策（至少含新增/修改决策的替代排除理由）/ §6.2 / §11 永不可省**

## Step 2b — 复用导向存量探索

**触发条件**（全部满足，任一不满足则整步 PASS-SKIPPED，直跳 Step 3）：
1. `docs/rules/` 存在且非仅 `project-state.md` 占位符
2. SRS §1.4 ESI 背景非 `[不适用]` 或 `docs/rules/coding-constraints.md` 非空

**跳过条件**：greenfield 项目；或 SRS 纯参数配置增量（L2/L3 无复用面）。

从 SRS §4 FR 标题 / §6 外部接口 / §1.4 ESI 提取关键模块名与领域词 → 推导 `--focus`（默认 `architecture,domain,deps` — 复用视角）；能从 SRS 推出单一模块子树时推导 `--path`。

> **DISPATCH** 创建独立 SubAgent（使用 Agent 或 General）— 在 subagent 中加载并执行 skill `long-task:long-task-explore`
> Depth: {省略，让 LOC 自检}
> Focus: {推导的维度，默认 architecture,domain,deps}
> Path: {推导路径 or "."}
> User question: "为实现 SRS FR-xxx / FR-yyy / ...，识别存量可直接复用的模块/类/接口/配置；同时标出 SRS 中假定的复用点若与代码实际不符。"

固定路径 **不入 input**（sub-skill 自行 glob）：`docs/plans/*-srs.md`、`docs/rules/`、`docs/explore/codebase-research.md`。

**期望返回**（复用 `long-task-explore` 产物契约 + 本场景补充字段）：
- `status`: `pass` | `blocked`
- `artifacts_written`: `docs/explore/codebase-research.md`
- `next_step_input.reuse_map`: 表格 `{SRS FR ID → 存量符号 file:line → 复用方式 DIRECT|EXTEND|REFACTOR|REPLACE}`
- `blockers`: 可含 `[SRS-CONFLICT] <FR-ID> 假定 <X>，代码实际 <Y>，file:line`

**非阻塞**：explore 返回 `BLOCKED` 或 `reuse_map` 空 → 静默进 Step 2c / Step 3，照常生成新建方案。

## Step 2c — 探索冲突同步到 SRS（仅 Step 2b blockers 含 `[SRS-CONFLICT]` 时执行）

对 Step 2b `blockers` 中每条 `[SRS-CONFLICT]` 前缀项，`AskUserQuestion`（`multiSelect: false`）：

| 选项 | 后续动作 |
|---|---|
| **A 刷 SRS 贴合现状** | 编辑 `docs/plans/*-srs.md` 对应 FR / §1.4 ESI；首行 `**状态**: 已批准` 保留；单独 commit `docs(srs): sync with existing code per design探索 — <FR-ID>` |
| **B 保留 SRS，Design §10 登记** | 笔记到内存，Step 4 §10 章节写入「代码需改造以贴合 <FR-ID>」 |
| **C 重新探索** | 回 Step 2b 重 DISPATCH |

全部项处理完进 Step 3。

**反模式**：不经 AskUserQuestion 单方面改 SRS — SRS 是已批准产物，跨文档改动必须用户裁决。

## Step 3 — 方案收敛（对话内决策，不落盘）

**内部判定**：用户输入是否已指定实现方案（技术栈 / 架构模式 / 关键库）。

- 已指定 → 方案来源 = 用户；填入用户给出的技术栈三件套
- 未指定 → 方案来源 = Agent 推荐；基于 SRS 约束 + Step 1.6 H1-H5 + Step 2b `reuse_map` 直接收敛到**单一最佳方案**（不列举候选，直接决策）

**在对话中呈现校核表**（过程数据，仅用于驱动 AskUserQuestion，不落盘到设计文档）：

```markdown
## 方案校核表（对话内过程数据）

| 维度 | 方案值 | SRS 约束 | ESI 现状 | 复用映射 | 判定 | 备注 |
|------|--------|---------|---------|---------|------|------|
| 语言/运行时 | Python 3.11 | CON-001 | 已有 3.11 | DIRECT | ✓ 对齐 | |
| 主框架 | FastAPI | IFR-002 REST | ESI 未有 | NEW | ✓ 兼容 | 新增 |
| 持久化 | Postgres 15 | — | 已有 Postgres 14 | REFACTOR | ⚠ 偏差 | 升级路径？ |
| ... | ... | ... | ... | ... | ... | ... |
```

判定语义：
- `✓ 对齐` — 方案 ∩ SRS ∩ ESI 三方一致
- `⚠ 偏差` — 与 SRS / ESI 任一冲突或偏差
- `? 模糊` — 数据缺失或用户输入不清
- 复用映射取 Step 2b `next_step_input.reuse_map` 对应行（`DIRECT | EXTEND | REFACTOR | REPLACE | NEW`）；Step 2b PASS-SKIPPED 时整列省略

**一次** `AskUserQuestion`（`multiSelect: false`，合并 ≤4 问）覆盖：
- 所有 `⚠` 和 `?` 项的确认（每项一问）
- 若来源 = Agent 推荐，追加一问：「是否接受本推荐方案？」选项：**接受 / 补充约束返工 / 指定替代方案**

`接受` 或所有 ⚠/? 确认后，记忆每条决策的**替代排除理由**供 Step 4 填入 §3.4 技术栈决策。
`补充约束返工` / `指定替代方案` → 带新约束 / 用户指定方案重执行 Step 3（最多 2 轮；超限中止并报「约束发散，建议澄清 SRS」）。

**落盘边界**：本 Step 只在对话中呈现校核表（⚠/? 审批完归零，属过程数据）。**不生成 §2 方案摘要章节**（已废弃）；决策点在 Step 4 时写入 §3.4 技术栈决策表（含替代排除理由）。

**反模式**：
- 呈现 "Approach A / B / C" 候选对比 —— 本 step 已废弃此模式；单方案 + §3.4 决策点内论证替代的排除理由才是硬要求。
- 把校核表固化到设计文档 —— 校核表是对话内过程数据，审批完归零即弃；§3.4 只承载"决策点 + 替代排除理由"（可追溯价值高）。

## Step 4 — 合成完整草稿（内部）

按 Step 2a 加载的模板 + `输入档位` 分支 + Step 2b `reuse_map`（若有），一次性装配全部章节内容到内存缓冲。不在对话中按章节呈现。

### L1 输入章节填法（全结构填写）

#### §0 项目结构
目标目录树，标记 [existing] / [new] / [modified]。存量项目基于 Step 2b `reuse_map` 标注影响区。

#### §1 设计驱动因素
- 关键 SRS 输入：约束、接口需求、用户画像（L1 输入下 SRS 含 §3 干系人；L2/L3 输入通常整节 `[不适用]`，本项跳过）
- 回应 Step 1.6 笔记 H1-H4（系统形态 / 交付运维 / 边界细节 / SRS §1.3 动机呼应）

#### §3 架构
- **逻辑视图**（Mermaid `graph`）— 层/包/模块依赖方向
- **组件图**（Mermaid `graph`）— 运行时组件与交互
- **§3.4 技术栈决策**（承载 Step 3 收敛到的单方案关键决策点）：表格格式，每行含 `决策维度 | 方案值 | 替代的排除理由 / 唯一可行（附 SRS / ESI 约束编号）`。Step 3 对话内校核表的 ⚠/? 经 AskUserQuestion 审批后，决策点写入此表；校核表本身**不落盘**

#### §4 关键功能设计
每个关键功能或功能组一章。每章必须：
- **类图**（`classDiagram`）— 类/模块、属性、方法、关系
- **一个行为图** — 序列图（`sequenceDiagram`）或流程图（`flowchart`）
- **集成面**（§4.N.6）— Provides/Requires 表引用 §6.2 Contract ID；无跨功能依赖写 "Self-contained"

对功能多的项目（P0/P1 完整；P2/P3 精简），精简 §4.N 只需：Overview + Key Types + Integration Surface。依赖 feature-design SubAgent 在 Worker 阶段生成接口契约、实现摘要、测试清单。

#### §5 数据模型
schema、关系、存储策略。有持久存储必须 Mermaid `erDiagram`。

#### §6 API / 接口
- §6.1 **外部接口** — 端点、契约、协议（追溯到 SRS IFR-xxx）
- §6.2 **内部 API 契约** — 功能间边界；§3.3 组件图每条边必须有对应 §6.2 行，含 Contract ID、请求/响应 schema、错误码

#### §8 测试策略（仅高层）
- 哲学：TDD（Red → Green → Refactor）
- 工具选择：测试框架 + 覆盖率工具（含版本 — 设计决策）
- 阈值：行 ≥ X%，分支 ≥ Y%，变异 ≥ Z%
- 边界："详细测试场景在功能设计和 TDD 阶段定义。"

### L2/L3 输入章节精简填法

基于模板按需省略 — 空洞章节整节标 `[不适用]` + 附一句理由，核心章节聚焦硬精确条目。

#### §1 设计驱动因素
- L2/L3 场景：1-2 句话回应 SRS §1 范围；若已给硬精确规约，整节可标 `[不适用]`

#### §3 架构
- §3.1-§3.3（架构概览 / 逻辑视图 / 组件图）：纯参数配置增量可整节标 `[不适用]`
- **§3.4 技术栈决策不可省**：即使 L2/L3 纯参数配置增量，也至少 1 行"沿用 ESI 技术栈，无新增依赖（附 ESI 约束编号）"；若本次引入新库 / 修改默认值 / 变更枚举集合，逐条登记替代排除理由
- §3.5 影响面：表格列出影响的既有模块 / 文件 + 影响类型 + 改动量估计（L2/L3 场景常用）

#### §4 关键功能设计
- **流程图为主、文字+伪代码辅助**；可引用用户原始需求原文中的参数名 / 文件路径 / 类型范围
- L2/L3 场景 §4.N 子节可精简为：概述 + 流程图 + 伪代码辅助（§4.N.2 类图 / §4.N.3 时序图按需）
- **不列举"关键决策点"**（描述设计要素本身，不记录过程决策）

#### §6.2 内部 API 契约 ★ 核心
- §6.2.1 配置文件 schema：表格列出 SRS §4 FR 中每个硬精确条目（参数名 / 类型 / 范围 / 默认值 / 来源 SRS）
- §6.2.2 任务书 / API / 消息 schema（XML / JSON / protobuf / CLI 参数，按需）
- §6.2.3 运行时合约表：若无组件间运行时调用可标 `[不适用]`
- **关键**：所有标识符 1:1 复制 SRS（笔记 H5 清单），禁"美化"为本地化命名（Step 5b 第 4 条审查）

#### §5 数据模型 / §7 第三方依赖
- 纯参数配置增量无新 schema / 无新依赖 → §5 / §7 整节标 `[不适用]`

**反模式**：把任一章节单独贴入对话等待用户逐章反馈。

## Step 4b — §11 代码库约定

**始终执行**，存量与新建均适用。§11 必须存在于每份设计文档，供下游 skill（feature-design、TDD、Worker）无条件读取。

### 4b.1 存量项目（scanner 已产出 `coding-*.md` / `build-*.md`）

1. 读 `docs/rules/{coding-style,coding-constraints,build-and-compilation}.md`
2. 按模板 §11 结构填入：
   - §11.1：强制内部库（从 `coding-constraints.md`）
   - §11.4：静态分析工具（仅工具名 + 配置路径 + 运行命令）
   - §11.5：关键命名与格式规则（摘要表，来自 `coding-style.md`）
   - §11.6：错误处理模式
   - §11.7：测试与质量工具表（从 `build-and-compilation.md`）
3. **交叉验证**：
   - §6.2（内部 API 契约）使用的库必须符合 §11.1
   - 冲突 → 在 §11 内就地标注"⚠ 设计覆盖：[原因]"，随整份草稿交 Step 5c 审阅门确认

### 4b.2 新建项目（`docs/rules/` 空、不存在，或仅 `project-state.md`）

1. 用空表填充 §11.1、§11.4-§11.7（列头 + 0 行）
2. 通过 **一次 `AskUserQuestion`** 询问："§11 已建空约定表。是否现在补充已知内部库 / 静态分析工具 / 测试阈值？补充项将写入草稿 §11；留空也可继续。"
3. 用户补充 → 合入 §11；留空 → 保留空表

## Step 5 — 草稿落盘（未 commit）

读取 Step 2a 加载的模板（`docs/templates/design-template.md` 或用户自定义）：
1. 保留标题结构
2. 每个标题下替换指导文本为 Step 4 / 4b 合成的章节内容
3. 顶部元数据必须包含：`日期`、**`状态`: 待审批**、`SRS 引用`、`输入档位`（从 SRS 元数据继承）
4. L2/L3 输入下的空洞章节：整节标 `[不适用]` + 附一句理由
5. Step 4 合成内容若无匹配章节：追加为"附加说明"

保存到 `docs/plans/YYYY-MM-DD-<topic>-design.md`。**不执行 `git commit`**。

落盘后输出文本（非 AskUserQuestion）告知用户：文件路径 + 需阅读全文（含 §0-§11 + 文件末尾 `## 待审阅事项`）+ 阅后回对话等 Step 5c。

## Step 5b — 集成一致性检查（写入文件末尾）

Step 5 落盘后立即执行（按 SRS `输入档位` 分支强度）。结果追加到草稿文件末尾 `## 待审阅事项` 章节，每项检查一个 `###` 子标题，0 标记时写 `无标记`（保留本项已跑过的可见性）。

检查项清单：

### 通用检查

1. **契约完整性**：
   - §3.3 组件图存在时，每条边在 §6.2.3 运行时合约表有对应行。缺 → 标记
   - §3.3 组件图整节标 `[不适用]`（L2/L3 纯参数配置场景）→ 本项 PASS-SKIPPED
2. **Schema 一致性**：
   - §6.2.3 每行的 Provider 功能 §4.N 行为图含 Response Schema；Consumer §4.N 引用 Request Schema。不匹配 → 标记
   - §6.2.1 / §6.2.2 子表字段类型与 SRS §4 FR / §5 IFR 一致
2b. **关键决策点替代论证**（始终执行 — 去候选化后 Step 3 的 fail-safe）：
   - §3.4 技术栈决策表每行必须含"替代的排除理由"或"唯一可行（附 SRS / ESI 约束编号）"
   - 0 行决策或某行"替代的排除理由"列为空 → 标记（供 Step 5c 审阅门用户判读）
3. **章节合理省略判定**（L2/L3 输入）：整节标 `[不适用]` 的章节必须附一句理由；空洞无理由 → 标记

### 打磨度回应（按 `输入档位` 分支，Group P 镜像）

4. **打磨度回应**：
   - **L1 输入**：Design §1 设计驱动因素是否回应 SRS §1.3 项目动机（关键词重叠率 ≥ 30% 或人工判读"主题对齐"） → 否则标记
   - **L2/L3 输入**：Design §1 允许标 `[不适用]`；若存在内容则必须回应 SRS §1 范围
   - 所有档位：Design 全文无口语原话引用块（grep 口语词 / 裸 `> ` 引用块） → 否则标记

### 硬精确条目下游传递（L2/L3 强制）

5. **硬精确条目 1:1 传递**（仅 `输入档位 ∈ {L2, L3}`）：
   - SRS §4 FR / §5 IFR 中出现的每个 camelCase / snake_case 标识 / 文件路径 / 类型范围 / 默认值 / 枚举集合，是否在 Design §6.2 内部 API 契约（6.2.1 / 6.2.2 / 6.2.3 任一）中 1:1 出现 → 缺失则标记
   - **完全一致**：标识符大小写、路径分隔符、范围记号 — 不允许"美化"为本地化命名
   - 检查方法：从 SRS 提取 Step 1.6 笔记 H5 清单 → grep Design 文件 → 0 缺失才 PASS

### 复用映射落地（brownfield 强制）

6. **复用映射落地**（仅 Step 2b `status=pass` 时执行）：
   - Step 2b `next_step_input.reuse_map` 每行对应 FR，需在 Design §4 功能设计中出现对应 `file:line` 引用（`DIRECT` / `EXTEND` / `REFACTOR` 路径）或明说「新造」（`NEW` / `REPLACE`）→ 缺失则标记
   - Step 2b `PASS-SKIPPED`（greenfield 或无复用面）→ 本项 PASS-SKIPPED，需附一句 skip 理由

进入 Step 5c。

## Step 5c — 审阅门

`AskUserQuestion` 收集用户决定（`multiSelect: false`）：

| 选项 | 后续动作 |
|---|---|
| **批准** | 执行"批准收尾"，进入 Step 6 |
| **提出修改** | 用户列改动 → 编辑 `docs/plans/*-design.md` → 回 Step 5c |
| **回 Step 3 返工** | 带新约束回 Step 3 → Step 4 → Step 5 → Step 5c |

**修改循环上限**：3 轮。超限 → 中止审阅门并提示"修改分歧较大，建议重新触发 `long-task:long-task-design` 或先澄清需求"。

### 批准收尾

1. 编辑 `docs/plans/YYYY-MM-DD-<topic>-design.md`：
   - 首行 `**状态**: 待审批` → `**状态**: 已批准`
   - 删除文件末尾 `## 待审阅事项` 整段
2. `git commit`

## Step 6 — 过渡到 Init

调用 `long-task:long-task-init`。

**终态：调用 long-task-init。** 不可调用其他实现 skill。

## 图表规则

- 所有架构/设计视图用 **Mermaid** 语法（不用 ASCII 艺术或图片引用）
- 每个图表反映实际批准的设计内容，无占位符
- §3.3 组件图每条边在 §6.2 有 Contract ID

## 反模式

| 合理化 | 正确回应 |
|--------|---------|
| "方案显然，无需论证" | SRS = WHAT，不是 HOW。单方案也须在 §3.4 技术栈决策表每行给出"替代的排除理由"或"唯一可行（附 SRS / ESI 约束编号）"。Step 5b 第 2b 条会机械校验。 |
| "边做边设计" | 前期设计比会话中期修正便宜。 |
| "这里重新澄清需求" | 需求归 SRS。缺失标记为开放问题，设计前解决。 |
| "Design 不需要再读用户原文了，SRS 转写已足够" | Step 1.6 强制读原文做二次吸收。否则细节断片 — 用户在 H1-H5 维度的隐含期望必丢失。 |
| "L2 输入也要硬填 §1 / §3.1-§3.3 / §5 / §6.1 / §7 / §8 / §10" | 这些章节在规约式增量场景下是空洞填充。整节标 `[不适用]` + 附一句理由，不硬凑内容。**§3.4 技术栈决策 / §6.2 / §11 永不可省。** |
| "把 SRS 里的 `UrbanBuildingSearchRadius` 改名为 `urban_building_search_radius` 更符合 Python 风格" | 标识符大小写必须 1:1 与 SRS 一致。Step 5b 第 4 条审查会标记。代码内部命名转换是实现细节，不是设计决策。 |
| "Design Step 2 我自己扫一下存量代码就行，不必 DISPATCH" | 主 agent 上下文会被存量代码淹没；Requirements 1.6 / Increment 3.5 已是 DISPATCH 模式，Design Step 2b 保持一致 — 探索独立 SubAgent，主 agent 只消费 `reuse_map` 结构化返回。 |
| "探索出的假定与 SRS 矛盾，在 Design §10 记一笔就行" | SRS 是下游 reviewer 的判决源；冲突必须经 Step 2c AskUserQuestion 裁决 — 刷 SRS 或显式接受（走 §10 登记为选项 B，且用户知情），不能默默带病进 Design。 |
