# Skill 骨架化重构经验总结

> 以 `long-task-increment` 为例，将单体 skill 拆分为"主 orchestrator + 独立 SubAgent sub-skill"的经验沉淀。适用于 Step 彼此独立、每步读写重文档、需用户审批的长 skill。

## 背景

`long-task-increment/SKILL.md` 原 378 行，单 skill 承载 8 个阶段。其中 Step 3/4/4b/5/6 每步都要读一份大文档（SRS/Design/ATS/UCD/feature-list.json），在主 agent 执行会把文档全文灌入窗口，一次 increment 循环吃掉数万 token。

重构后：主 SKILL.md 162 行（↓57%），5 个新 sub-skill 各 60-100 行；主 agent 只读主 SKILL.md + 审批循环模板，sub-skill 在独立 SubAgent 加载重文档。

## 何时适用本模式

**适合拆分的 skill 特征**（同时满足）：
- 多个独立 Step，彼此之间靠结构化数据（而非自然语言对话）衔接
- 某些 Step 需读取大文档（几百行以上）做改写
- Step 之间有用户审批闸门
- Step 已通过 TodoWrite 明确分段

**不适合拆分**：
- 单一交互循环（如 Requirements elicitation 的多轮对话）—— 拆出去主 agent 要反复跨越 SubAgent 边界
- 主 agent 已经只读路径 + 元数据、不读文档内容（拆了无增益）
- Step 彼此强耦合、中间状态难以结构化 —— 拆了 SubAgent 要传递的 JSON 比原文档还大

## 架构要点

### 1. 主 SKILL.md = orchestration 骨架

每个被拆分的 Step 压缩成 ~15 行 DISPATCH stub：

```markdown
### 3. 影响评估

> **DISPATCH** → 启动独立 SubAgent 执行 skill `long-task-increment-impact`
> **input**: `new_reqs`, `wave`, `brownfield_esi`
> **expect**: Structured Return Contract；`next_step_input` 含 `impact_matrix` / ...

按 `references/approval-revise-loop.md` 处理。通过后 next_step_input 供后续 Step 复用。
```

主 agent 读到 DISPATCH 块 → 组装 prompt 分发 → 收 5 字段契约 → 按 loop 模板审批 → 下一步。

### 2. Sub-skill = 执行步骤 + 返回契约

sub-skill 的 SKILL.md 只写：
- **步骤**（对应原 Step 的详细操作）
- **返回**（Structured Return Contract 样例：status / artifacts_written / next_step_input / blockers / evidence）
- **阻塞/失败条件**
- 必要时的**反模式**

**不写**：
- 输入契约（主 SKILL.md 的 DISPATCH 块是单一事实源；SubAgent 从 prompt 读实际值）
- "为什么拆分"等设计旁白
- "主 agent 只消费契约字段"等其他读者的规则

### 3. 统一审批-返工循环模板

5 个 sub-skill 共享一份 `references/approval-revise-loop.md`，定义：
- `status` 分支处理（blocked / fail / pass 分别怎么走）
- 审批关卡（pass 后：approve / revise / escalate）
- Revision / Clarification / Failure Addendum 组装规则
- 返工封顶（2 轮 revise，第 3 次自动 escalate；blocked 不计入）

主 SKILL.md 每个 DISPATCH stub 只一句 "按 `references/approval-revise-loop.md` 处理"，剩下的不重复。

### 4. 五字段返回契约（复用现有资产）

所有 sub-skill 返回统一格式：

```markdown
## SubAgent Result: <skill-name>

**status**: pass | fail | blocked
**artifacts_written**: [持久化文件路径]
**next_step_input**: { 给下一步的结构化数据 }
**blockers**: [若 blocked 时填]
**evidence**: [关键断言的最小证据]
```

本项目已有 `skills/long-task-work/references/structured-return-contract.md`，直接复用。主 agent 只读这 5 字段，不读 SubAgent 的内部 thinking。

## 实施过程踩的坑

### 坑 1：把固定路径当输入字段传

**错误**：
```
> **input**: new_reqs=<json>, feature_list_path=feature-list.json,
>   design_doc_path=docs/plans/*-design.md, wave=N
```

**正确**：
```
> **input**: `new_reqs`, `wave`, `brownfield_esi`
```

固定路径（`feature-list.json`、`docs/plans/*-<kind>.md`）sub-skill 内部自行 glob 定位。只有主 agent 才知道的动态值（用户输入、上一步 next_step_input 片段）才作为 input。

DISPATCH 块越短越好，主 agent 组装 prompt 的成本才越低。

### 坑 2：过程量落盘成 md

**错误**：Step 3 影响矩阵写到 `docs/plans/impact-matrix-wave-N.md`，主 agent 读回来呈给用户审批。

**正确**：影响矩阵通过 `next_step_input` 直接返回主 agent（JSON-like 结构）。主 agent 拿到数据即可呈给用户，无需二次磁盘 IO。

**判定规则**：
- **持久化产物**（进 git，后续 phase 仍要读）→ `artifacts_written`
- **过程量**（仅驱动本 skill 后续 Step）→ `next_step_input`

本次 5 个 sub-skill 中，只有 impact 是纯过程量（`artifacts_written: []`）；其他 4 个都原地改既有文档。

### 坑 3：输入契约只写在 sub-skill 里

如果输入契约只写在 sub-skill SKILL.md 的"输入"段落，主 agent 根本看不到（SubAgent 才读 sub-skill SKILL.md，主 agent 只读自己的 SKILL.md）。

**正确**：输入契约写在**主 SKILL.md 的 DISPATCH 块 `input:` 行**，作为单一事实源。sub-skill SKILL.md 不重复写输入段。

### 坑 4：过度文档化"为什么"

初稿每个 sub-skill SKILL.md 都有"为什么存在"、"主 agent 只消费..."、"本 SubAgent 不发起 AskUserQuestion"等段落。这些是**设计意图**，不是执行指令，SubAgent 读了也不会据此改行为 —— 删。

**执行路径 vs 开发经验**：判断某段文字该不该留，看读者是谁。

| 读者 | 文档类型 | 是否允许元叙述 |
|---|---|---|
| AI Agent 执行时 | `SKILL.md` + 被 skill 加载的 `references/*.md` | ❌ 只写"怎么做"和"怎么返回" |
| 开发者（人） | `docs/*.md`（本文档这类经验总结）、`CLAUDE.md` | ✅ 可以写背景、拆分逻辑、历史沿革 |

**常见误区**（后续重构 `long-task-requirements` 时踩到过）：把"此次拆分涉及的 sub-skill 清单"、"本模板复用了 X"、"为什么存在"这类元叙述塞进 `references/approval-revise-loop.md`。这份文件在主 agent 每次循环都会被读入执行上下文 —— 元叙述对 AI 的动作没有影响，只是纯消耗 token。

**规则**：
- 执行路径文档里，每一句都应该是 AI 在判断分支 / 组装 prompt / 校验输出时会用到的信息
- 拆分背景、"本次从 X 重构到 Y"、"复用了 Z"这些话只写在开发经验文档（`docs/*-lessons.md`）或 commit message
- 初稿写完后自检：把每段话代入"如果删了这段，AI 行为会不会变？"—— 不会变就删

#### 坑 4 的高发子类：产物索引表 / 流程图 / Schema 总览

骨架化后最容易在主 SKILL.md 里留下一张 **"生成的持久化工件" 表** 或 **"文件产出方→消费方"流程图**。本次 `long-task-init` 重构踩到：主 orchestrator SKILL.md 保留了一张 10 行的产物表（文件 / 产出方 / 用途），审查时发现**零执行消费者**：

- **主 agent**：不读此表做分支。每步产出已写在该步 DISPATCH stub 的 `expect: artifacts_written=...` 里，冗余。
- **sub-skill**：不加载主 SKILL.md。
- **下游 skill**（work / st / hotfix / finalize）：按固定路径读具体文件，从不 grep "产出方" 字段。
- **CLAUDE.md**：已有一份同名 "Generated Persistent Artifacts" 权威表（给人读）。

表放在 SKILL.md 里 = 每次 init 循环都灌入主 agent 上下文，纯 token 消耗。

**反模式集合**（骨架化后 Occam 第二轮审查必查）：

| 反模式 | 典型形态 | 为什么没用 | 正确位置 |
|---|---|---|---|
| 产物索引表 | `\| 文件 \| 产出方 \| 用途 \|` | 每步 DISPATCH 的 `artifacts_written` 已声明；下游按路径直读 | 删；`CLAUDE.md` 给人看的索引已存在 |
| 文件产出→消费流程图 | mermaid / ascii 箭头图 | AI 不按图做分支；执行顺序已由 Step 编号决定 | 删；流程图归 `docs/*-lessons.md` |
| 主 SKILL.md 里的 Feature List Schema 全量 | `features[]` 所有字段枚举 | 只有 sizing 关卡呈现需要数量/band 字段，不需要完整 schema | 保留最小子集或改引 `scripts/validate_features.py` 作权威校验 |
| "Generated Persistent Artifacts" 在 SKILL.md + CLAUDE.md 双写 | 两张同表 | 双源漂移风险 | 留 CLAUDE.md 一份 |
| 下游 skill 清单 / 上游来源清单 | "本 skill 被 X 调用、下游是 Y" 段落 | 执行路径由 Skill Call Graph 决定，不由本文件分支 | 只留最短一行 "集成" 段，或移到 CLAUDE.md |

**执行路径消费者清单**（判断某段内容"有没有执行消费者"用）：

| 候选消费者 | 是否读主 SKILL.md | 是否读 `references/*.md` | 是否读 sub-skill SKILL.md |
|---|---|---|---|
| 主 agent（当前 skill 循环内） | ✅ 全文 | ✅ 按引用加载 | ❌ 不读 |
| 主 agent（下游 skill 会话） | ❌ 只读当时活跃的那个 | ❌ | ❌ |
| sub-skill SubAgent | ❌ | ❌ 除非 sub-skill SKILL.md 主动引用 | ✅ 全文 |
| 开发者阅读 | ✅ | ✅ | ✅ |

**推论**：如果某段内容只有"开发者阅读"这一列命中，它归 `docs/*-lessons.md` 或 `CLAUDE.md`，不归 SKILL.md。

**自检问句**（比坑 4 主问句更具体，适合产物表/流程图场景）：
1. "主 agent 在哪一步会 grep 这张表取值？" 答不出来 → 删。
2. "这张表的字段是否在 DISPATCH stub 的 `expect:` 里已声明？" 是 → 删。
3. "同样的信息在 CLAUDE.md 是否已有权威版？" 是 → 删主 SKILL.md 的那份，避免双源漂移。

### 坑 5：DISPATCH 语法偏离既有约定

初版把 DISPATCH 简化成 `> execute skill xxx`，丢失了"启动独立 SubAgent"的隔离语义。

**正确**：对齐既有 `long-task-work` 的约定：
```
> **DISPATCH** → 启动独立 SubAgent 执行 skill `<name>`
```

"启动独立 SubAgent" 明确表达"新空上下文、不继承主 agent 历史"的核心语义，不能省。

## 拆分前后的数据对比

| 指标 | 前 | 后 |
|---|---|---|
| 主 SKILL.md 行数 | 378 | 162 |
| 主 agent 单次循环必读内容 | 378 行 SKILL.md | 162 行 SKILL.md + 168 行 loop 模板 |
| sub-skill 数 | 0 | 5（平均 77 行） |
| 重文档读入主 agent | SRS/Design/ATS/UCD/feature-list 全量 | 不读（sub-skill 独立加载） |
| 审批模式维护点 | 散落 5 个 Step | 集中 1 份 loop 模板 |
| 总行数 | 378 | 713（分散到 7 文件，各 SubAgent 只加载自己需要的） |

**关键**：总行数变多不是回归 —— 主 agent 单次循环接触的行数才是上下文窗口消耗指标。713 行分散在 7 个文件，主 agent 只读其中 330 行（SKILL.md 162 + loop 168），sub-skill 的 60-100 行在独立 SubAgent 窗口中。

## 保守拆分（交互 vs 非交互）：long-task-requirements 经验

经验文档最初把该 skill 列为 ❌（整体不拆）。重构实践表明整体结论正确，但**拆分粒度可以更细**——按"交互 vs 非交互"分界而不是整体判断：

**保留主 agent**（多轮 AskUserQuestion 密集）：
- Lite L1/L2/L3、Expert E1-E4 / E6-E8 的所有挖掘轮次
- Step 14 章节审批（Expert 逐节呈现）
- Step 11b 单轮模式声明
- quality sub-skill 返回的 user-input-required 候选（粒度 4+ 审批、模糊项澄清、延后清单确认）

**下沉 sub-skill**（纯算法 / 校验 / 落盘）：
- Step 7-11 → `long-task-requirements-quality`（分类 + EARS + 图表 + 8 属性 + G/S 粒度 + 延后候选）
- Expert E10 → `long-task-requirements-alignment`（根因 / JTBD / pre-mortem / 孤儿 FR）
- Step 13 reviewer → DISPATCH 直接加载 `prompts/srs-reviewer-prompt.md`（不新建 sub-skill）
- Step 15 → `long-task-requirements-finalize`（保存 + commit）

**关键设计决策**：
- sub-skill **绝不发起 AskUserQuestion**；需要用户决定的场景统一转 `blockers` 返回，主 agent 按 Clarification Addendum 重分发
- 主 agent 保留 **Step 16 衔接下一 skill 的控制权**；finalize 只返回 `srs_path`，不在 sub-skill 里触发 `long-task-ucd`
- `approval-revise-loop.md` 各自维护一份（不跨 skill 共享）——避免跨 skill 耦合风险

**Step 1.6 代码探索不拆，改返回契约**：原先 explore 返回全文污染主 context；改为要求返回结构化摘要（`modules[] / integration_points[] / architectural_patterns[] / api_surface[] / narrative_insights[]`），主 agent 从摘要引用模块/API 做提问。

## Occam 剃刀：拆分之前先删除（long-task-design 经验）

评估 `long-task-design`（284 行单体）是否适合骨架化时，发现**更优先的问题是"哪些章节根本不应存在"**。对设计模板 13 章做下游消费矩阵后，有 7 章为孤儿或重复源；在此基础上骨架化收益反而下降（负担本身可剔除）。本次**不拆分、仅剪枝**的结果：模板 374 → 194 行（−48%），SKILL.md 284 → 206 行（−27%），13 章 → 6 章。

### 何时优先应用剃刀而非骨架化

单体 skill 前先问三问：
1. **是否存在"OR 路径"的跨 skill 引用？** 例如下游写 "若 Design §X **或** env-guide §Y 存在" —— 这是双源信号，说明其中一个从未被唯一消费，可删。
2. **是否存在"上游产出、下游重生"的章节？** 如设计 §4.N 画类图/时序图/流程图，但 Worker 阶段 feature-design SubAgent 会在 `docs/features/*.md` 中以 Interface Contract + Test Inventory 重新产出——上游图只会被覆盖一次，纯冗余。
3. **是否存在与权威源重复的章节？** 测试策略 vs `feature-list.json.tech_stack`；部署 vs `env-guide.md`；依赖清单 vs 包清单。重复即漂移风险。

三问中任何一个命中，**剃刀先于剪枝**。骨架化适合步骤独立 + 重文档读写；剃刀适合文档冗余 + 多源漂移。

### 剃刀流程（可执行 4 步）

1. **构建消费矩阵** —— 对每个章节 grep 所有下游 skill 的引用：`grep -rn "§N\|第 N 节\|Section N" skills/`。列表即证据。
2. **标注判决**：
   - 消费者 0 处 → **孤儿**，删除。
   - 消费者 N 处但全为 "OR 源 Y" 表达式 → **可删**（Y 是单源）。
   - 消费者 N 处但 Y 源更简单/已是权威 → **可删**。
   - 消费者 N 处且唯一 → **保留**。
3. **预演下游修改**：删前列出每个消费者的替代读取点，确保全部能切换。不能切换的章节**暂缓删除**。
4. **单批次落地**：模板 + SKILL.md + 所有下游引用一次性改，避免中间态留下悬空引用。跑 grep 复核 + 回归测试闭环。

### 剃刀与 SKILL 运行时文档的边界（延续坑 4）

剃刀过程中极易把"被删除章节 → 替代源"表、"Occam 说明"blockquote、"本章是集成规范不是详细设计"定位语塞入**运行时模板**。这些对 AI 执行无增益，是纯 token 消耗。

判定准则：**"如果这段话删了，SubAgent 下一步的动作会变吗？"** 不会变就删。

具体反模式（本次踩到并清理）：

| 反模式 | 出现位置 | 正确做法 |
|---|---|---|
| "已删除章节与替代源对照"表 | `design-template.md` 尾部 | 表写在 `docs/*-lessons.md`；模板文件只写当前章节指引 |
| "Occam 说明"blockquote | `design-template.md` 开头 | 删；模板本身就是当前结构，不需要自我解释 |
| "本章是集成规范，不是详细设计"定位段 | §2 章节开头 | 改为 1 行直接禁令："禁止画类图/时序图/流程图" |
| "选中方案持久化、被淘汰一句话"方法论段 | §1.4 下方 blockquote | 删；表头 "Rejected Alternatives" 列已是执行指令 |
| `SKILL.md` "设计产物边界（Occam 剃刀结果）"表 | 列出 8 项"不产出"及替代源 | 删；每节自身的 "禁止 X" 直接写在该节规则里 |

**通用规则**：模板与 SKILL.md 中的文字应全部是**填表指引**或**行为约束**；任何"为什么现在是这个结构"的解释都属于 lessons 文档。

### 典型判决（供后续复用）

| 判决模式 | 触发信号 | 本次实例 |
|---|---|---|
| **OR 路径即冗余** | 下游 ≥2 处写 "X OR Y" 引用 | `§13 OR env-guide §4` 在 5 处 skill 出现 → 删 §13 |
| **下游重生即冗余** | 上游章节被下游 SubAgent 原样覆盖 | §4.N 类图/时序图/流程图被 feature-design 重新产出 → §2.N 只留 Overview + Key Types + Integration Surface |
| **权威源已存在即冗余** | 章节内容可从 feature-list.json / env-guide / 包清单直接读取 | §8 第三方依赖（→ 包清单 + §1.4 关键版本）；§9 测试策略（→ tech_stack + quality_gates）；§10 部署（→ env-guide §1-§3）；§11.1 里程碑（→ waves[].description）|
| **操作性缺失即删** | 章节写了但无动作触发条件 | §11.4 风险登记、§12 遗留问题 —— 无人读、无流程触发 → 删；真风险应进 task-progress 或阻塞审批 |
| **单源已足够即删** | 中间摘要层无独立价值 | §13（docs/rules/ 到 env-guide §4 的中间摘要）→ 删 §13，init 直读 docs/rules/ 生成 §4 |

### 剃刀收益量化模板

| 维度 | 前 | 后 | 降幅 |
|---|---|---|---|
| 模板行数 | 374 | 194 | −48% |
| SKILL.md 行数 | 284 | 206 | −27% |
| 设计章节数 | 13（其中 7 条件/孤儿） | 6（其中 2 条件） | −54% |
| 每特性强制 Mermaid 图数 | 2–4 | 0（系统级图保留） | −100% |
| "§X OR §Y" 双路径 | 5 处 skill | 0 | −100% |
| 跨 skill 引用漂移风险源 | 3 层（rules / §13 / §4） | 2 层（rules / §4） | −33% |

总行数变化不是核心指标——**跨文件漂移源数量**才是。从 3 层降到 2 层意味着后续每次增量修改只需同步 1 处，而非 2 处。

### 剃刀与骨架化的选择矩阵

| 场景 | 优先动作 |
|---|---|
| 单体文件长、但每节都有唯一下游消费者 | 骨架化（拆 SubAgent） |
| 单体文件长、且下游有 OR 路径或重复源 | 剃刀（先剪章节） |
| 剪枝后仍 >250 行且读重文档 | 再骨架化 |
| 剪枝后 <200 行 | 保持单体，不再拆 |

**本次结论**：`long-task-design` 从 284 行剪到 206 行，单体已足够轻，放弃原计划的 "Layer C 骨架化"——剃刀的连锁红利是"骨架化变得不必要"。

## 复用到其他 skill 的判断表

| Skill | 是否适合拆分 | 理由 |
|---|---|---|
| `long-task-requirements` | ⚠️ 部分（已拆） | 多轮 AskUserQuestion 挖掘留主 agent；尾部 Step 7-11（质量流水线）/ E10（一致性校验）/ Step 15（落盘）可拆，以交互 vs 非交互为分界 |
| `long-task-design` | ❌ 不拆（已剃刀） | 284 → 206 行，6 章骨架；先剃刀后判定骨架化无必要 |
| `long-task-ats` | ❌ 不拆（已剃刀 + reviewer 规范化） | 288 → 218 行；§6 删、§3 压、§1 压；reviewer 对齐五字段契约；见下节 |
| `long-task-work` | ✅ 已拆 | 参考项目：feature-design / tdd / quality / feature-st 已是 SubAgent-per-Step |
| `long-task-hotfix` | ❌ | 复现 + 根因分析强依赖主 agent 的代码理解与交互 |
| `long-task-st` | ⚠️ | ST plan 生成可拆，ST 执行依赖交互；建议仅拆 plan |
| `long-task-finalize` | ❌ | 多为 README/examples 生成，轻量 |
| `long-task-retrospective` | ❌ | 上传逻辑已集中，不复杂 |

## ATS 剃刀 + Reviewer 规范化经验（long-task-ats）

延续 Design 剃刀思路对 `long-task-ats`（288 行单体 + 195 行模板）实施剃刀。关键发现：**Design 剃刀后，下游校验 agent 会遗留幻影 §引用**，这是跨 skill 剃刀需要补的审计动作。

### 消费矩阵判决

| § | 判决 | 触发规则 |
|---|-----|---------|
| §1.2/§1.3 质量目标/测试级别 | **删** | 与 SKILL.md Step 3 类别分配规则重复；下游 0 消费者 |
| §2 映射表 | **保留** | feature-st / init / st / 校验脚本唯一源 |
| §3.1-3.5 prose | **压缩到 1 行** | 类别由 §2 `必须类别` 列驱动；prose 无下游消费者（lessons §剃刀 Q2：上游产出下游重生） |
| §4 NFR 矩阵 | **保留** | 提供 SRS §5 没有的工具/负载参数；唯一源 |
| §5 集成场景 | **保留** | ats-reviewer R6 + st 集成规划消费 |
| §6 风险驱动优先级 | **删** | Design §11.4 已被 Design 剃刀删；§6 失去对齐锚点；ST 从 SRS 优先级直接派生 |

### 新模式 A：上游剃刀 → 下游校验 agent §引用必须同步审计

Design 剃刀把模板从 13 章剪到 6 章，但 `agents/ats-reviewer.md` 仍在 R8 维度里写：
- `Design §3.4 技术栈兼容`（新结构 §3 是"数据模型"，技术栈在 §1.4）
- `Design §9 测试策略`（已无 §9）
- `Design §11.4 风险评估`（已无 §11）

这些**幻影引用**若不修，reviewer 每次跑都产出无意义 Major（R8 条目锚点不存在 → 判 fail）。

**通用规则**：对某 skill 做剃刀时，grep 所有下游 `<SkillName> §N` 形式的引用，对照剪后实际章节号逐条核对。特别关注 reviewer 类 agent——它们是跨文档一致性的最后一道校验。

### 新模式 B：reviewer SubAgent 也必须对齐 Structured Return Contract

ats-reviewer 虽然已在 Step 9 作为独立 SubAgent 分发（lessons 此前误判"已隔离就无需再做"），但输出仍是自由格式自然语言报告：
- `## Summary / ### Issues Found / ### Dimension Results / ...`
- 主 agent 需手工解析 "Verdict: PASS/FAIL"、数 Major 条数、提取 Cross-Reference Conflicts 表

改造后对齐五字段契约：
- `status` 替代 "Verdict: PASS/FAIL"
- `next_step_input.review_report_markdown` 承载完整评审文本（主 agent 只读不解析）
- `next_step_input.major_defect_count` / `minor_defect_count` 供分支决策
- `blockers[]` 专用 `[CROSS-REF CONFLICT]` 条目（双语义：与 status 正交，pass + 非空 blockers 合法）
- `evidence[]` 每维度裁决 + 关键证据（主 agent 摘要入 task-progress）

**规则**：任何独立分发的 SubAgent（包括不升级为 sub-skill 的 reviewer/evaluator/analyzer），输出都必须对齐 `structured-return-contract.md`。"独立分发" ≠ "自由格式"。

### 新模式 C：blockers 字段可承载非阻塞的外部决策

ATS 场景揭示 `blockers[]` 可双用：
1. **传统 blocked**：输入缺失、工具异常 → `status: blocked`
2. **需外部裁决的条目**：如 `[CROSS-REF CONFLICT]` → `status: pass` 也可非空 blockers

主 agent 按前缀分流：无前缀 → 标准 blocked 流程；`[CROSS-REF CONFLICT]` → 逐条 AskUserQuestion A/B/C 选项。这个扩展保持契约字段不变，通过"值约定"承载新语义。

### 收益量化

| 指标 | 前 | 后 | 降幅 |
|------|-----|-----|------|
| ats-template.md | 195 | 137 | −30% |
| long-task-ats/SKILL.md | 288 | 218 | −24% |
| ats-reviewer.md | 295 | 261 | −12% |
| 章节数 | 6 | 5 | −17% |
| **幻影引用**（Design 剃刀后遗） | 4 处 | 0 | **−100%** |
| 审批节循环 | 5 节 | 4 节 | −20% |
| Reviewer dispatch 风格偏离 | 1 | 0 | −100% |
| Reviewer 返回契约偏离 | 1 | 0 | −100% |
| 审批循环模式维护点 | 散落 Step 10/10.5 | 集中 approval-revise-loop.md | 集中化 |

## 回归防护

重构后 349 tests pass；新增防护建议：
- 给 `validate_features.py` 增加 CI 检查（已有）
- 考虑为新 sub-skill 添加 frontmatter schema 校验脚本（目前未做；sub-skill 数增长时值得投入）
- `approval-revise-loop.md` 作为硬约定，若未来要改返工封顶规则（2 轮 → N 轮），只动这一处

## 参考

- 主 SKILL.md：`skills/long-task-increment/SKILL.md`
- 审批循环模板：`skills/long-task-increment/references/approval-revise-loop.md`
- 返回契约（共享）：`skills/long-task-work/references/structured-return-contract.md`
- SubAgent 开发指南（既有）：`skills/long-task-work/references/subagent-development.md`
- 5 个 sub-skill：`skills/long-task-increment-{impact,design,ats,ucd,srs}/SKILL.md`
- Increment 骨架化 commit：`826ab59`
- Design 剃刀骨架：`docs/templates/design-template.md`、`skills/long-task-design/SKILL.md`
- Design 剃刀评审计划：`/home/machine/.claude/plans/long-task-design-roi-melodic-origami.md`
- ATS 剃刀 + reviewer 规范化：`docs/templates/ats-template.md`、`skills/long-task-ats/SKILL.md`、`skills/long-task-ats/references/approval-revise-loop.md`、`agents/ats-reviewer.md`
- ATS 剃刀评审计划：`/home/machine/.claude/plans/long-task-ats-docs-skill-subagent-refac-joyful-codd.md`
