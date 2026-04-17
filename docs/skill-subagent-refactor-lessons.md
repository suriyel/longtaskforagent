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

**规则**：sub-skill 写"怎么做"和"怎么返回"；设计意图放共享引用（如 approval-revise-loop.md 的背景段）或 CLAUDE.md。

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

## 复用到其他 skill 的判断表

| Skill | 是否适合拆分 | 理由 |
|---|---|---|
| `long-task-requirements` | ❌ | 多轮 AskUserQuestion 驱动，拆分后主 agent 要反复跨 SubAgent 边界 |
| `long-task-design` | ⚠️ 部分 | 评审可拆（类似 ats-reviewer），但设计本体仍以主 agent 交互为主 |
| `long-task-work` | ✅ 已拆 | 参考项目：feature-design / tdd / quality / feature-st 已是 SubAgent-per-Step |
| `long-task-hotfix` | ❌ | 复现 + 根因分析强依赖主 agent 的代码理解与交互 |
| `long-task-st` | ⚠️ | ST plan 生成可拆，ST 执行依赖交互；建议仅拆 plan |
| `long-task-finalize` | ❌ | 多为 README/examples 生成，轻量 |
| `long-task-retrospective` | ❌ | 上传逻辑已集中，不复杂 |

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
- 本次 commit：`826ab59`
