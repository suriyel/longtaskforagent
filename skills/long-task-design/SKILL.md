---
name: long-task-design
description: "当 SRS 存在但无设计文档和 feature-list.json 时使用 — 读 SRS + 存量 + 用户方案偏好，打磨产出聚焦 HOW 的设计文档"
---

# 设计文档生成

输入：已批准 SRS + 可选 `docs/rules/` + 用户输入中可能已带的实现方案偏好。
动作：若用户已指定方案 → 校核+确认；若未指定 → 提 2-3 方案让用户选。
单次合并批准为默认路径；项目大或用户要求时分章节。

<HARD-GATE>
在呈现设计并获得用户批准之前，不可调用任何实现 skill、编写任何代码、搭建任何项目、运行 init_project.py 或采取任何实现行动。每个项目都适用，无论看起来多简单。
</HARD-GATE>

## Step 1 — 读 SRS

1. 读 `docs/plans/*-srs.md`
2. 提取设计驱动：FR 数量与优先级、硬性约束、外部接口需求、用户画像
3. 列出 SRS **待解决问题**（§10）。若未解决项影响架构 → Step 2 前 `AskUserQuestion` 解决

## Step 2 — 探索技术上下文

1. 探索现有代码/仓库。读用户输入中夹带的实现方案偏好（技术栈、库选择、目录组织）
2. 识别 SRS 未涉及的技术约束（monorepo 结构、现有库、CI 工具）
3. 加载设计模板：用户指定路径优先，否则 `docs/templates/design-template.md`。验证 `.md` 且含 `## ` 标题

## Step 3 — 方案决策

**判断用户输入是否已指定实现方案**（技术栈、架构模式、关键库选择）：

### 3a. 用户方案已指定 → 校核模式

呈现 **方案校核表**：

```markdown
## 用户方案校核

| 维度 | 用户输入 | SRS 约束 | ESI 现状 | 判定 | 备注 |
|------|---------|---------|---------|------|------|
| 语言/运行时 | Python 3.11 | CON-001 | 已有 3.11 | ✓ 对齐 | |
| 主框架 | FastAPI | IFR-002 REST | ESI 未有 | ✓ 兼容 | 新增 |
| 持久化 | Postgres 15 | — | 已有 Postgres 14 | ⚠ 偏差 | 升级路径？ |
| ... | ... | ... | ... | ... | ... |
```

标注：
- `✓ 对齐` — 用户方案 ∩ SRS ∩ ESI 三方一致
- `⚠ 偏差` — 与 SRS/ESI 任一冲突或差异
- `? 模糊` — 用户未说清，需追加确认

通过 AskUserQuestion 一次性确认所有 ⚠ 和 ? 项（≤4 问）。确认后跳到 Step 4。

### 3b. 用户方案未指定 → 提案模式

呈现 **2-3 种实现方案**：

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros / Cons**: [bullets]
**Third-party dependencies**: [key libs with versions]

## Approach B: [Name]
...

## Recommendation: [X]
**Reason**: [why this fits given SRS constraints + ESI]
```

每个方案对照 SRS 约束与 ESI 现状评估。用户选定 → 进入 Step 4。

## Step 4 — 章节批准

默认 **单次合并批准**（简单项目 / 方案已清）。项目大（>20 功能）或用户明确要求时分章节呈现。

必需章节：

### §0 项目结构
目标目录树，标记 [existing] / [new] / [modified]。存量项目基于 Step 2 探索标注影响区。

### §1 架构
- **逻辑视图**（Mermaid `graph`）— 层/包/模块依赖方向
- **组件图**（Mermaid `graph`）— 运行时组件与交互
- 技术栈决策对照 SRS 约束论证

### §4 关键功能设计
每个关键功能或功能组一章。每章必须：
- **类图**（`classDiagram`）— 类/模块、属性、方法、关系
- **一个行为图** — 序列图（`sequenceDiagram`）或流程图（`flowchart`）
- **集成面**（§4.N.6）— Provides/Requires 表引用 §6.2 Contract ID；无跨功能依赖写 "Self-contained"

对功能多的项目（P0/P1 完整；P2/P3 精简），精简 §4.N 只需：Overview + Key Types + Integration Surface。依赖 feature-design SubAgent 在 Worker 阶段生成接口契约、实现摘要、测试清单。

### §5 数据模型
schema、关系、存储策略。有持久存储必须 Mermaid `erDiagram`。

### §6 API / 接口
- §6.1 **外部接口** — 端点、契约、协议（追溯到 SRS IFR-xxx）
- §6.2 **内部 API 契约** — 功能间边界；§1 组件图每条边必须有对应 §6.2 行，含 Contract ID、请求/响应 schema、错误码

### §8 第三方依赖
- 精确版本号（不用 `latest`）
- 兼容性矩阵（运行时版本 + 依赖间冲突）
- 许可证标注（GPL/AGPL 等 copyleft 需标出）
- 非平凡依赖链配 Mermaid 依赖图

### §9 开发计划
- **里程碑** — 明确退出标准；M1=Foundation，末=润色与发布
- **§9.2 功能分解** — 每行一个功能（映射 1+ 个 FR），含 P0-P3 优先级与 `Mapped FRs` 列
- **§9.3 依赖链** — Mermaid `graph` 展示关键路径
- **配对排序** — 若同时有后端+前端功能，组织为 Backend A → Frontend A → Backend B 风格
- **风险登记簿**

### §10 测试策略（仅高层）
- 哲学：TDD（Red → Green → Refactor）
- 工具选择：测试框架 + 覆盖率工具（含版本 — 设计决策）
- 阈值：行 ≥ X%，分支 ≥ Y%，变异 ≥ Z%
- 边界："详细测试场景在功能设计和 TDD 阶段定义。"

呈现每章 → 等反馈 → 整合 → 进下一章（或全部一次呈现批准）。

## Step 4b — §11 代码库约定

**始终执行**，存量与新建均适用。§11 必须存在于每份设计文档，供下游 skill（feature-design、TDD、Worker）无条件读取。

### 4b.1 存量项目（`docs/rules/` 已填充）

1. 读 `docs/rules/{coding-style,coding-constraints,build-and-compilation}.md`
2. 按模板 §11 结构填入：
   - §11.1：强制内部库（从 `coding-constraints.md`）
   - §11.2：禁止的 API / 库
   - §11.3：批准的第三方库
   - §11.4：静态分析工具（仅工具名 + 配置路径 + 运行命令）
   - §11.5：关键命名与格式规则（摘要表，来自 `coding-style.md`）
   - §11.6：错误处理模式
   - §11.7：测试与质量工具表（从 `build-and-compilation.md`）
3. **交叉验证**：
   - §8（第三方依赖）不得与 §11.2 禁止列表冲突
   - §6.2（内部 API 契约）使用的库必须符合 §11.1
   - 冲突 → 标"⚠ 设计覆盖：[原因]"呈给用户确认
4. 呈现 §11 给用户审查（与其他章节相同流程）

### 4b.2 新建项目（`docs/rules/` 空或不存在）

1. 用空表填充 §11.1-§11.7（列头 + 0 行）
2. 告知用户："§11 已建空约定表。已知约束现在添加，或留空 — 下游 skill 无条件读取 §11。"
3. 用户添加 → 整合重呈；留空 → 继续

## Step 5 — 保存

读取 Step 2 加载的模板：
1. 保留标题结构
2. 每个标题下替换指导文本为批准内容
3. 顶部元数据若无则加：`Date`、`Status`、`SRS Reference`、`Template` 路径
4. 模板未覆盖章节：标记"[不适用]"
5. 批准内容若无匹配章节：追加为"附加说明"

保存到 `docs/plans/YYYY-MM-DD-<topic>-design.md`。Git commit。

## Step 5b — 集成一致性检查

Init 前机械验证：

1. **契约完整性**：§1 组件图每条边在 §6.2 有对应行。缺 → 标记
2. **Schema 一致性**：§6.2 每行的 Provider 功能 §4.N 类图含 Response Schema；Consumer §4.N 引用 Request Schema。不匹配 → 标记
3. **依赖完整性**：§6.2 每个 Consumer 功能在 §9.3 依赖链中列出 Provider 功能 ID。缺 → 标记

标记项呈给用户。进 Init 前解决。

## Step 6 — 过渡到 Init

调用 `long-task:long-task-init`。

**终态：调用 long-task-init。** 不可调用其他实现 skill。

## 图表规则

- 所有架构/设计视图用 **Mermaid** 语法（不用 ASCII 艺术或图片引用）
- 每个图表反映实际批准的设计内容，无占位符
- 增量更新期间：新增/修改元素用绿色=NEW / 琥珀色=MODIFIED，按模板约定；下批次移除标记
- §1 组件图每条边在 §6.2 有 Contract ID

## 第三方依赖规则

1. **精确版本** — 指定 `1.2.3` 或范围 `^1.2.0` / `>=1.2,<2.0`；不用 `latest`
2. **兼容性矩阵** — 验证每个依赖与目标运行时版本 + 栈内其他依赖兼容
3. **许可证审计** — 记录许可证；标出可能冲突的 copyleft（GPL/AGPL）
4. **升级路径** — 标出接近 EOL 或有已知迁移问题的依赖

## 反模式

| 合理化 | 正确回应 |
|--------|---------|
| "SRS 已暗示架构" | SRS = WHAT，不是 HOW。呈现选项或校核用户方案。 |
| "只有一种构建方式" | 即使是显而易见的选择也需明确权衡 — 校核或提案。 |
| "边做边设计" | 前期设计比会话中期修正便宜。 |
| "这里重新澄清需求" | 需求归 SRS。缺失标记为开放问题，设计前解决。 |
