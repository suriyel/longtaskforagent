# Skill 重构决策手册

> 受众：AI Agent。在做骨架化 / 跨 phase 拆分 / 剃刀决策时查阅本文档。
> 每一节是可执行规则与判决表，不是叙事。

---

## § 1. SubAgent + Skill 骨架整改

单体 skill 拆成 **主 orchestrator + 独立 SubAgent sub-skill**，把重文档读写、算法 Step 下沉到 sub-skill，主 agent 只读骨架 + 五字段契约。

### 1.1 模式核心

- **主 SKILL.md** = orchestration 骨架；每个拆出的 Step 压成 ~15 行 DISPATCH stub
- **sub-skill SKILL.md** = 步骤 + 返回契约 + 阻塞条件 + 必要反模式
- **审批 / 返工循环** 集中到 `references/approval-revise-loop.md`，主 SKILL.md 每个 DISPATCH 一句"按 `approval-revise-loop.md` 处理"
- 主 agent 只消费五字段契约，不读 SubAgent 内部 thinking

### 1.2 DISPATCH stub 编写规则

```markdown
> **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-impact`
> **input**: `new_reqs`, `wave`, `brownfield_esi`
> **expect**: Structured Return Contract；`next_step_input` 含 `impact_matrix`
```

- "创建独立 SubAgent" 字面不可省 —— 表达"新空上下文、不继承主 agent 历史"
- 固定路径（`feature-list.json`、`docs/plans/*-<kind>.md`）**不入 `input`**；sub-skill 自行 glob 定位
- 仅主 agent 知道的动态值（用户输入、上一步 `next_step_input` 片段）才入 `input`
- stub 越短，主 agent 组装 prompt 的成本越低
- **分层调用**：stub 里 `` skill `long-task:X` `` 指 SubAgent 启动后**内部**用 Skill tool 加载的 skill 名；Agent tool 的 `subagent_type` 填 harness 通用壳 —— Claude Code 用 `Agent`，OpenCode 用 `General`。主 agent 先起壳，壳里再 Skill tool 分发
- **反模式**：把 skill 名（如 `long-task-requirements-quality`）直接作为 Agent tool 的 `subagent_type` —— harness 会报 `Agent type 'xxx' not found`。skill 名走 subagent 内部的 Skill tool；壳名走 Agent tool 的 `subagent_type`，两层不可混

### 1.3 五字段返回契约

```markdown
**status**: pass | fail | blocked
**artifacts_written**: [持久化文件路径]
**next_step_input**: { 给下一步的结构化数据 }
**blockers**: [若 blocked 时填]
**evidence**: [关键断言的最小证据]
```

复用 `skills/using-long-task/references/structured-return-contract.md`。**Reviewer / evaluator / analyzer 类 SubAgent 同样必须返这五字段** —— "独立分发 ≠ 自由格式"。

### 1.4 持久化 vs 过程量

| 类型 | 归属 | 判据 |
|---|---|---|
| 持久化产物 | `artifacts_written` | 进 git、后续 phase 仍要读 |
| 过程量 | `next_step_input` | 仅驱动本 skill 后续 Step，不落盘 |

### 1.5 blockers 前缀约定（承载非阻塞外部决策）

| 前缀 | 语义 | 主 agent 动作 |
|---|---|---|
| 无 | 输入缺失 / 工具异常 → 传统 blocked | 按 loop 模板 Failure Addendum 重分发 |
| `[CROSS-REF CONFLICT]` | 需用户裁决的跨文档冲突；`status: pass` + 非空 blockers 合法 | 逐条 AskUserQuestion A/B/C |
| `[CONTRACT-DEVIATION]` | 跨 Step 设计契约偏离；orchestrator 无裁决权 | 直通 blocked 返上层 |

### 1.6 sub-skill SKILL.md 特别规则

- **不写**输入契约（主 SKILL.md 的 DISPATCH `input:` 是单一事实源）
- **不写**"主 agent 只消费五字段"等其他读者的规则（SubAgent 读了也不改变行为）
- **不写**"为什么存在"等设计旁白
- **只写**：步骤、返回、阻塞 / 失败条件、必要反模式

### 1.7 Skill 分发 vs Prompt 模板分发

| 信号 | 选择 |
|---|---|
| 动态输入 + 静态文档切片定位 | Skill 分发（动态入 input，静态自 glob） |
| 要求返 Structured Return Contract | Skill 分发 |
| 同一模板被多处调用 | 升级为共享 sub-skill |
| 任务本质是一次 LLM prompt 填空（"扩写此段"） | 模板分发可接受 |

反模式：半拉 skill —— 有指令语义但无 frontmatter / 无契约、占位符两处维护。

### 1.8 何时适用

满足时适用：多独立 Step + 结构化数据衔接 + 某些 Step 读大文档 + Step 之间有审批闸门。

不适用：
- 单一交互循环（如 requirements 的多轮 AskUserQuestion）—— 拆了要反复跨 SubAgent 边界
- 主 agent 已只读路径 + 元数据、不读文档内容
- Step 强耦合、中间状态难以结构化（传 JSON 比原文档还大）

### 1.9 嵌套深度约束

SubAgent 嵌套 **深度 ≤ 2**（主 agent → sub-skill，或主 agent → orchestrator → sub-skill）。达到 3 层预期会脆弱，应改走 § 2 跨会话拆分。

---

## § 2. 大颗粒 Workflow 拆多 Skill（跨会话 Phase 拆分）

长流程拆成多个 **top-level phase skill**，通过 `feature-list.json` + 路由脚本串接；每 phase 内可再叠加 § 1 骨架化。

### 2.1 三种形态的选择

| 信号 | 选择 |
|---|---|
| 步骤 ≤5 + JSON 衔接 + 单会话够用 | orchestrator + SubAgent（§ 1） |
| 步骤 ≥3 + 每步重读同份大文档 + 允许会话切断 | top-level phase skill（本节） |
| 用户需在阶段之间显式审视产出 | top-level phase skill |
| SubAgent 嵌套深度 >2 已不可行 | top-level phase skill |
| 剪枝后 <200 行 | 保持单体 |

关键判据：**用户是否愿意"每阶段开一次新会话"**。是 → 跨会话可行；否 → 退回 § 1。

### 2.2 路由：feature-list.json.sub_status

- `sub_status ∈ {design_pending, tdd_pending, st_pending, done}` 是路由的**单一事实源**
- `status ∈ {failing, passing}` 由 sub_status 派生（`done` ↔ `passing`）
- `validate_features.py` 强制两者一致
- 统一路由脚本 `scripts/phase_route.py` 读 sub_status 分发到目标 phase skill；`using-long-task` 仅转发

### 2.3 路由优先级

**阶段靠前优先**（design > tdd > st）。多特性并行时让 TDD / ST 阶段有更多对象可挑，避免全堵在同一阶段。

### 2.4 阶段 skill 的会话契约

每个 phase skill 末尾必须：
1. 翻转 sub_status（`design_pending → tdd_pending → st_pending → done`）
2. Git commit
3. 输出会话终止横幅
4. **不自动推进**下一阶段 —— 用户开新会话由 `using-long-task` → `phase_route.py` 重新路由

### 2.5 重复读是特性不是 bug

一致性保证 > token 效率。跨会话 / 跨 SubAgent 都允许重读同一份文档：
- TDD SubAgent 在 Red / Green / Refactor 各自重读 feature design §4 / §6 / §7 / §8
- ST 阶段再次从磁盘读 feature design 全文

工程上"缓存上一阶段读过的内容"会制造跨会话上下文依赖，违反"会话边界天然切断"的收益前提。

### 2.6 薄路由壳

旧单体拆空后保留 ~77 行薄路由壳接住 muscle memory 直接调用（`/long-task-work`）。壳中**只能**"读 sub_status → 分流"，不能写任何阶段指令，否则退化回 orchestrator 嵌套误区。

### 2.7 Reference 资产归属规则

| 类型 | 归属 | 示例 |
|---|---|---|
| 真·共享基础设施（不随阶段变化） | 留一处，其他 phase 用相对路径引用 | `structured-return-contract.md`, `systematic-debugging.md`, `subagent-development.md`, `worktree-isolation.md` |
| 带阶段差异的 loop / 行为协议 | 各 phase / 各 skill 独立维护 | `approval-revise-loop.md`（同名文件可多份；规则同构但语境不同） |
| 阶段内 TDD / 静态分析等动作协议 | 归该阶段 skill | `drift-protocol.md` 归 TDD，不上移 |
| 项目级运行时命令契约（quiet-exec / re-check / 故障 fallback） | 下沉到 `env-guide.md` 作为用户可编辑单一事实源 | `silent-execution.md` §1/§3 与 env-guide §3 重复 → 整文件删除，§4 吸收为 env-guide §3 fallback 段落 |

### 2.8 跨 phase 拆分后，§ 1 骨架化在每个 phase 内独立应用

Phase skill 本身仍可能长 —— 仍按 § 1 判据决定是否拆 orchestrator + sub-skill。例：TDD phase 内部再拆 red / green / refactor 三个 sub-skill。

---

## § 3. 奥卡姆剃刀 + ROI 消费原则

文档 / 章节 / 指令是否保留，由"是否有执行消费者"决定。**骨架化之前先剃刀** —— 剃掉的章节骨架化也不必处理，连锁红利是"骨架化变得不必要"。

### 3.1 核心判据

两层级联，先粗后细：

1. **段落级** —— **"如果删了这段，AI 下一步的动作会变吗？"** 不变 → 删。
2. **字符级** —— **"每个字符都要有价值"**。通过段落级的保留章节再过一遍字符剃：冗余修饰（"其实"、"实际上"、"一般来说"、"通常情况下"）、同义复述、寒暄过渡、无触发条件的限定句，凡删了不损 AI 决策信息的一律剃。段落级防死代码，字符级防活章节里藏死字符。

运行时文档每轮循环都灌进上下文，字符冗余 = 持续 token 税。

### 3.2 执行路径消费者清单

| 候选消费者 | 读主 SKILL.md | 读 `references/*.md` | 读 sub-skill SKILL.md |
|---|---|---|---|
| 主 agent（当前 skill 循环内） | ✅ 全文 | ✅ 按引用加载 | ❌ |
| 主 agent（下游 skill 会话） | ❌ | ❌ | ❌ |
| sub-skill SubAgent | ❌ | ❌ 除非 sub-skill 主动引用 | ✅ 全文 |
| 开发者阅读 | ✅ | ✅ | ✅ |

推论：**只命中"开发者阅读"一列 → 归 `docs/*-lessons.md` 或 `CLAUDE.md`，不归 SKILL.md**。

### 3.3 三问剃刀

骨架化前先问：
1. 下游是否有 **"X OR Y" 跨 skill 引用**？→ 双源信号，其中一源从未被唯一消费，可删
2. 是否**上游产出、下游重生**？→ 上游是冗余（如 §4.N 类图被 feature-design SubAgent 原样覆盖）
3. 是否与**权威源**重复？→ 测试策略 vs `tech_stack`；部署 vs `env-guide.md`；依赖清单 vs 包清单

命中任一 → **剃刀先于骨架化**。

### 3.4 剃刀 4 步

1. **构建消费矩阵**：`grep -rn "§N\|第 N 节\|Section N" skills/`
2. **标注判决**：
   - 0 消费者 → 孤儿，删
   - 全为 "OR 源 Y" → 可删
   - Y 源更简单 / 已是权威 → 可删
   - 唯一消费者 → 保留
3. **预演下游修改**：列每个消费者的替代读取点；不能切换的**暂缓删除**
4. **单批次落地**：模板 + SKILL.md + 所有下游引用一次性改，grep 复核 + 回归测试闭环

### 3.5 判决模式表

| 模式 | 触发信号 |
|---|---|
| OR 路径即冗余 | 下游 ≥2 处 "X OR Y" |
| 下游重生即冗余 | 上游章节被下游 SubAgent 原样覆盖 |
| 权威源已存在即冗余 | 内容可从 `feature-list.json` / `env-guide.md` / 包清单直读 |
| 操作性缺失即删 | 章节写了但无动作触发条件（风险登记、遗留问题） |
| 单源已足够即删 | 中间摘要层无独立价值 |

**案例**：`silent-execution.md`（4 处 TDD 引用）§1 quiet-exec 模板、§3 Re-check 协议与 `env-guide.md §3` 100% 重复；§2 TDD 三阶段 exit-code 判读表在 R/G/R sub-skill 本地各自一句完整表达（下游重生）；§4 `[ENV-ERROR]` 升级协议 4 行，不够独立文件门槛 → 整文件删除，§4 吸收为 env-guide §3 fallback 段落，跨文件漂移源 2→1。

### 3.6 剃刀后必做：幻影引用审计

剃刀某 skill 后，grep 所有下游 `<SkillName> §N` 引用，对照剪后实际章节号逐条核对。

**reviewer 类 agent 是最高优先级扫描目标** —— 它们是跨文档一致性的最后一道校验，幻影引用（锚点不存在）会使 reviewer 每次跑都产出无意义 Major、把 pass 误判为 fail。

### 3.7 核心指标：跨文件漂移源数量

总行数不是核心指标。**跨文件漂移源数量** 才是 —— 从 3 层降到 2 层意味着后续每次增量修改只需同步 1 处，而非 2 处。

### 3.8 剃刀 vs 骨架化选择矩阵

| 场景 | 动作 |
|---|---|
| 每节都有唯一下游消费者 | 骨架化 |
| 有 OR 路径 / 下游重生 / 权威源重复 | 先剃刀 |
| 剪枝后仍 >250 行且读重文档 | 再骨架化 |
| 剪枝后 <200 行 | 保持单体 |

---

## § 4. 给 AI 写，不给人写

运行时文档（SKILL.md + 被该 skill 加载的 `references/*.md`）每次主 agent 循环都会灌入上下文。每一行都必须是 AI 执行时的决策输入 —— 元叙述、导航索引、历史记述**对 AI 行为零影响**，只是纯 token 消耗。

### 4.1 读者 × 文档矩阵

| 读者 | 文档 | 允许元叙述 |
|---|---|---|
| AI（主 agent 循环内） | 主 SKILL.md + 被加载的 references | ❌ 只写"怎么做"和"怎么返回" |
| AI（下游 skill 会话） | 不读上游 SKILL.md | — |
| SubAgent | 自己的 sub-skill SKILL.md（不读主 SKILL.md） | ❌ |
| 开发者 | `docs/*-lessons.md` / `CLAUDE.md` / commit message | ✅ 背景、历史、拆分逻辑 |

### 4.2 运行时文档反模式清单（必删）

**元叙述类**（开发者视角）：
- "为什么存在" / "本次从 X 重构到 Y" / "复用了 Z"
- "主 agent 只消费五字段"等对其他读者的规则
- "Occam 说明" blockquote
- "本章是集成规范不是详细设计"定位段
- "选中方案持久化、被淘汰一句话"方法论段

**索引尾节类**（零执行消费者）：
- `## 集成` / `## Integration` / `## 调用关系` / `## Caller-Callee`
- `## 下游消费方` / `## Downstream Consumers`
- `## 相关文档` / `## See Also`
- 产物索引表 `| 文件 | 产出方 | 用途 |`（每步 DISPATCH 的 `artifacts_written` 已声明）
- 文件产出 → 消费方 mermaid / ascii 流程图（AI 不按图分支）
- Feature List Schema 全量枚举（改引 `scripts/validate_features.py` 作权威）
- "已删除章节 → 替代源对照"表（归 lessons，不归模板）

权威导航归 `CLAUDE.md`（Phase Workflow Summary / Skill Call Graph / Generated Persistent Artifacts）。

### 4.3 反例：**不要**误删的节

以下节是 AI 执行硬依赖：
- `## Structured Return Contract` / `## Return Schema`
- `## 输入契约`（仅在主 SKILL.md DISPATCH stub 场景）
- `## <Step N>` 步骤主体
- 反模式 / 阻塞条件清单

### 4.4 跨 phase 生命周期错位（最隐蔽）

Skill 生命周期非对称：

| 写指令位置 | 读取时机 | 可规定的行为 |
|---|---|---|
| `long-task-init/SKILL.md` | 仅 init 会话一次 | init 阶段产物与 handoff |
| `long-task-work/SKILL.md` | 每次 Worker 循环 | Worker 阶段编排（路由壳） |
| `long-task-work-{design,tdd,st}/SKILL.md` | 对应 phase 会话 | 本 phase 的启动 / 步骤 / 会话终止 |
| `long-task-{tdd,feature-design,...}` sub-skill | SubAgent 分发时 | 本 sub-skill 的具体算法 |
| `env-guide.md` | 下游按路径读 `§N` | 命令 / 端口 / 约束的运行时权威源（**数据**，不是执行指令） |

**反模式**：
- "Worker 循环期间如何更新 X" 写在 `long-task-init/SKILL.md` → Worker 不读 init → 死代码
- "ST 阶段若遇到 Y 则..." 写在 `long-task-work/SKILL.md` → ST 不读 work → 死代码
- "下次 init 时记得..." 写在 work / increment → init 结束后本文件不再加载，下次用的是最新版 → 死代码
- Phase skill 互相规定对方行为（"为下一阶段准备..."）→ 下一 phase 不读本 phase → 死代码

### 4.5 跨 phase 错位自检

1. 这段指令描述的动作发生在**哪个 skill 的会话里**？不是本 skill → 迁到那个 skill
2. 用户 clear 会话后重进，本指令还能读到吗？不能 → 死代码，迁走
3. 权威版是否已在目标 skill？是 → 删本处避免双源漂移；否 → 迁移而非拷贝

### 4.6 新 skill 模板禁令

- 不加 `## 集成` / `## Integration` 尾节
- 不写"为什么拆分"设计旁白
- 集成语义若需运行时消费，写进触发它的那一个 Step，不写事后索引
- 开发者导航需求由 `CLAUDE.md` + `docs/*-lessons.md` 承担
