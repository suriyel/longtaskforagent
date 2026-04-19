long-task-increment 骨架化：Step 3/4/4b/5/6 下沉到 SubAgent                                                                                                                                                                  
                                                                                                                                                                                                                              
 Context                                                                                                                                                                                                                      

 skills/long-task-increment/SKILL.md 目前 378 行，单一 skill 同时承载了 8 个阶段的详细执行规则。其中 Step 3（影响评估）、Step 4（Design 修订）、Step 4b（ATS 修订）、Step 5（UCD 修订）、Step 6（SRS 更新 +
 特性分解）每一步都需要读取一份大文档（SRS/Design/ATS/UCD/feature-list.json），直接在主 agent 执行会把这些文档的全文灌入窗口，一次 increment 循环就吃掉数万 token，限制了增量规模。

 本次改造对齐 long-task-work 已落地的 SubAgent-per-Step 模式（见 skills/long-task-work/SKILL.md Step 4/5-7/8/9 的 DISPATCH 块，以及 skills/long-task-work/references/structured-return-contract.md）：

 - 每个"重文档读写"步骤改为独立 SubAgent 加载独立 sub-skill 执行
 - SubAgent 返回 Structured Return Contract（五字段），主 agent 只消费契约字段，不消费 SubAgent 内部 thinking
 - 新增一个统一的"审批-返工循环"共享引用，5 个步骤复用同一模板
 - 主 SKILL.md 退化为 orchestrator，从 378 行缩减到 ~180 行

 预期收益：
 - 主 agent 单次 increment 循环上下文占用下降 60%+（估计）
 - 5 个步骤的审批/返工流程集中在一处维护，避免模式漂移
 - 与 long-task-work 的架构风格对齐，易于未来扩展

 现有可复用资产

 ┌────────────────────────────┬────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────┐
 │            资产            │                              路径                              │                                              用途                                              │
 ├────────────────────────────┼────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ Structured Return Contract │ skills/long-task-work/references/structured-return-contract.md │ 5 字段契约 (status/artifacts_written/next_step_input/blockers/evidence)；新 sub-skill 直接对齐 │
 ├────────────────────────────┼────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ DISPATCH 声明式语法        │ 同上 §DISPATCH 声明式语法                                      │ blockquote 格式 > **DISPATCH** → ... > **with input**: ... > **expect**: ...                   │
 ├────────────────────────────┼────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ 澄清 2 轮上限范式          │ skills/long-task-feature-design/SKILL.md:106-153               │ Clarification Addendum 再分发模式；新 revise 循环借鉴其封顶规则                                │
 ├────────────────────────────┼────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ SubAgent 开发指南          │ skills/long-task-work/references/subagent-development.md       │ Controller 职责、完整任务文本、退出准则                                                        │
 ├────────────────────────────┼────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ brownfield 适配协议        │ skills/long-task-increment/references/brownfield-adaptation.md │ ESI 构建、API 影响表、§1.4 回填 — 由 impact/design/srs 三个新 sub-skill 分别自行加载           │
 └────────────────────────────┴────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘

 实施计划

 1. 新建共享引用 —— 审批-返工循环模板（1 份）

 文件：skills/long-task-increment/references/approval-revise-loop.md（新）

 内容骨架：

 # 审批-返工循环（共享模板）

 ## 使用场景
 所有 long-task-increment-* sub-skill 返回 Structured Return Contract 后，
 主 agent 通过本模板统一处理"呈给用户 → 审批 → 返工"。

 ## 主 Agent 循环（伪代码）
 1. DISPATCH sub-skill SubAgent
 2. 读返回的 status:
    - blocked → AskUserQuestion(blockers) → 收集回答 → 带 Clarification Addendum 重分发
    - fail → 读 evidence → 带失败原因重分发（不升级用户，除非 2 轮未恢复）
    - pass → 进入审批关卡
 3. 审批关卡：
    - 呈 artifacts_written 中的 diff/草稿 + evidence 摘要
    - AskUserQuestion 选项：[approve / revise / escalate]
 4. 分支：
    - approve → 主 agent 按契约的 next_step_input 构造下一步；无需再写文件
      （sub-skill SubAgent 已把草稿写到 artifacts_written 指定路径）
    - revise → 收集用户反馈 → 组装 Revision Addendum → 带反馈重分发该 SubAgent
    - escalate → 中止本 sub-skill；主 agent 主持手动处理

 ## 返工循环封顶
 - 默认上限 2 轮 revise；第 3 次 revise 请求 → 自动升级 escalate
 - blocked 状态的 clarification 不计入 revise 上限（属于输入澄清而非质量问题）
 - 升级走向：AskUserQuestion 告知用户 "2 rounds exhausted; switching to manual"

 ## Revision Addendum 组装规则
 SubAgent 重分发时 prompt 追加：
 Revision Addendum (round N)

 Previous artifact:
 User feedback:
 Rework instruction: 仅针对反馈修订；保持未受反馈影响的部分不变

 ## DISPATCH 模板
 （复用 long-task-work/references/structured-return-contract.md §DISPATCH 声明式语法）

 ## 与 Structured Return Contract 的关系
 本模板只处理 status=pass 时的"用户批准"环节；status=blocked/fail 的处理
 仍遵循 structured-return-contract.md §主 Agent 消费规则。

 为何放在 long-task-increment/references/：主要消费者是 increment 的 5 个新 sub-skill；long-task-feature-design 已有自己的澄清循环（可独立维护）；后续其他 skill 如需复用可 cross-reference 本路径。

 2. 新建 5 个 sub-skill

 每个 sub-skill 结构：
 skills/long-task-increment-<step>/
   SKILL.md
   references/  (可选 — 仅 impact/design/srs 需要，复用 brownfield-adaptation.md 时 cross-reference 不复制)

 每个 SKILL.md 遵循固定模板：
 1. frontmatter：name、description（单行，触发条件明确到"由 long-task-increment 分发"）
 2. 输入契约：列出必须从主 agent prompt 收到的字段
 3. 执行步骤：从原 long-task-increment SKILL.md 对应 Step 切割而来的详细步骤
 4. 输出契约：Structured Return Contract（5 字段）——artifacts_written 指向原地修改的文档；next_step_input 供主 agent 构造下一步
 5. CLARIFY / BLOCKED 处理说明

 2.1 skills/long-task-increment-impact/SKILL.md（Step 3）

 来源：原 SKILL.md L60-101 的"影响评估 + API 影响与兼容性表"
 输入：
 - 新/改/废需求清单（带 EARS 语句与变更类型标签 NEW/MODIFY/EXTEND/DEPRECATED）
 - feature-list.json 路径
 - docs/plans/*-design.md §6.2 路径
 - docs/explore/codebase-research.md 路径（若存在）
 - references/brownfield-adaptation.md §D（API 影响表规则）
 输出：
 - artifacts_written: docs/plans/impact-matrix-wave-N.md（新建临时件，格式同原 Step 3 两表）
 - next_step_input: { hard_impact_ids: [...], soft_impact_ids: [...], api_changes: [...], breaking_contracts: [...] }
 - evidence: 反向依赖图节点数、Hard/Soft 统计、Breaking 行数

 2.2 skills/long-task-increment-design/SKILL.md（Step 4）

 来源：原 SKILL.md L152-182
 输入：
 - 影响矩阵路径（来自 impact SubAgent）
 - docs/plans/*-design.md 路径
 - 新/改/废需求清单
 - env-guide.md 路径（§3/§4 可能被改动）
 - Breaking 契约列表（驱动 §6.2 更新）
 输出：
 - artifacts_written: 原地修改后的 docs/plans/*-design.md、可能的 env-guide.md
 - next_step_input: { design_sections_changed: [...], new_contracts: [...], modified_contracts: [...], env_guide_touched: bool }
 - blockers: 若 env-guide.md §3/§4 被改 → 将其列入 blocker 提醒主 agent 转审批

 主 agent 在审批循环中合并 Design 审批 + env-guide.md §3/§4 审批（因为后者需用户显式更新 frontmatter）。

 2.3 skills/long-task-increment-ats/SKILL.md（Step 4b）

 来源：原 SKILL.md L184-216
 自适应跳过：sub-skill 内部检查 docs/plans/*-ats.md 不存在时返回 status: pass, next_step_input: { skipped: true }；主 agent 无需前置判断。
 输入：
 - docs/plans/*-ats.md 路径
 - 新/改/废需求清单
 - §6.2 契约变更集（来自 design SubAgent）
 输出：
 - artifacts_written: 原地修改后的 ATS 文档
 - next_step_input: { mapping_rows_changed: N, new_categories: [...], needs_reviewer_rerun: bool }
 - evidence: 覆盖率统计表差异、新增 NFR 行数

 needs_reviewer_rerun 为 true 时主 agent 在审批循环外额外触发 ats-reviewer SubAgent（现有 agent，不动）。

 2.4 skills/long-task-increment-ucd/SKILL.md（Step 5）

 来源：原 SKILL.md L218-235
 自适应跳过：无 UI 特性 + 无新 UI 需求时 → status: pass, skipped: true
 输入：
 - docs/plans/*-ucd.md 路径
 - 新/改/废 UI 需求子集
 输出：
 - artifacts_written: 原地修改后的 UCD
 - next_step_input: { components_added: [...], components_modified: [...], components_deprecated: [...] }

 2.5 skills/long-task-increment-srs/SKILL.md（Step 6）

 来源：原 SKILL.md L237-306（同时覆盖 6a SRS 更新 + 6b 特性分解）
 输入：
 - 新/改/废需求清单
 - docs/plans/*-srs.md 路径
 - feature-list.json 路径
 - 影响矩阵（复用特性的 wave/status 更新依据）
 - 当前 wave 号
 - ESI 摘要（来自 impact 或 orient 阶段）
 输出：
 - artifacts_written: 原地修改后的 SRS + feature-list.json
 - next_step_input: { new_feature_ids: [...], modified_feature_ids: [...], deprecated_feature_ids: [...], wave: N }
 - evidence: validate_features.py 通过；§1.4 回填行数

 特殊：该 SubAgent 必须在自己上下文内运行 python scripts/validate_features.py feature-list.json 并把退出码纳入 evidence；未通过 → status: fail，主 agent 触发 revise 循环。

 3. 改造主 SKILL.md（skills/long-task-increment/SKILL.md）

 保留在主 agent 的内容：
 - Step 1 Orient（含加载 brownfield-adaptation.md §A 构建 ESI —— ESI 在主 agent 构建一次，后续传给 impact/srs SubAgent）
 - Step 2 需求 elicitation（必须留在主 agent，因为 AskUserQuestion 多轮）
 - Step 3.5 针对性代码库探索（保持现状 —— 已是 SubAgent 分发）
 - Step 7 更新辅助文件（轻量，不值得拆）
 - Step 8 收尾（git commit + task-progress + RELEASE_NOTES）

 改为薄 orchestrator 的内容：原 Step 3/4/4b/5/6 各自压缩为约 15-25 行 orchestration stub：
 ### 3. 影响评估

 > **DISPATCH** → 创建独立 SubAgent（使用 General 或 Agent），在 subagent 中加载并执行 skill `long-task:long-task-increment-impact`
 > **with input**: new_reqs=<compact-json>, feature_list_path=feature-list.json,
 >   design_doc_path=docs/plans/*-design.md, brownfield_context=<ESI 摘要>,
 >   wave=N
 > **expect**: Structured Return Contract；artifacts_written 含 docs/plans/impact-matrix-wave-N.md

 收到返回后按 `references/approval-revise-loop.md` 处理：
 - pass → AskUserQuestion 呈影响矩阵 + API 影响表 → [approve/revise/escalate]
 - revise → 组装 Revision Addendum 重分发
 - 通过后将 Hard/Soft 影响列表与 API 变更集合传递至 Step 4

 5 个 stub 风格一致；主 SKILL.md 从 378 行 → 约 180 行。

 4. 更新 CLAUDE.md 的架构描述

 CLAUDE.md L? 的 "14-Skill System" 表格需要从 14 更新到 19（14 + 5 新）。新增 sub-skill 归入"Discipline Skills (sub-skills of long-task-increment)"新分类。

 文件结构段落（L300+）同步追加 5 个新目录。

 5. 无需改动的内容

 - scripts/（所有 Python 脚本接口不变，新 sub-skill 内部调用即可）
 - agents/ats-reviewer.md、agents/codebase-scanner.md（不动）
 - skills/long-task-work/（作为现有 SubAgent-per-Step 范本；不动）
 - skills/using-long-task/SKILL.md（路由逻辑不变 —— 仍按 increment-request.json 路由到 long-task-increment；sub-skill 不被路由器直接触发）

 关键文件清单

 新建：
 - skills/long-task-increment/references/approval-revise-loop.md
 - skills/long-task-increment-impact/SKILL.md
 - skills/long-task-increment-design/SKILL.md
 - skills/long-task-increment-ats/SKILL.md
 - skills/long-task-increment-ucd/SKILL.md
 - skills/long-task-increment-srs/SKILL.md

 修改：
 - skills/long-task-increment/SKILL.md（从 378 → ~180 行；Step 3/4/4b/5/6 改为 DISPATCH stub）
 - CLAUDE.md（14-skill 表 + 文件结构段同步）

 不修改：
 - skills/long-task-increment/references/brownfield-adaptation.md（仍由 impact/design/srs sub-skill 各自加载）
 - skills/long-task-work/references/structured-return-contract.md（共享契约 —— 新 sub-skill 复用该 ref）

 验证方案

 端到端验证本改造不破坏 increment 流程：

 1. Schema 校验：每个新 SKILL.md 具备合法 frontmatter；skills/ 目录结构被 Claude Code 正确发现。运行：
 ls skills/long-task-increment-*/SKILL.md
 1. 应列出 5 个文件，每个都有 name/description frontmatter。
 2. 契约一致性自检：新 sub-skill 的 Return Contract 与 structured-return-contract.md 一致（5 字段名、语义）。人工 review。
 3. 主 SKILL.md 精简度：
 wc -l skills/long-task-increment/SKILL.md
 3. 预期 ≤ 200 行。
 4. 脚手架冒烟测试（手动）：在测试目录构造一个已初始化的 long-task 项目 + increment-request.json，触发 long-task-increment。验证：
   - Step 1 Orient 正常
   - Step 2 elicitation 收集到需求后
   - Step 3 DISPATCH long-task-increment-impact → 返回影响矩阵 → AskUserQuestion 审批 → 拒绝一次 → revise 重跑 → approve
   - Step 4/4b/5/6 依次按同样循环执行
   - Step 8 收尾 git commit 无遗漏
 5. 回归测试：
 python -m pytest tests/
 5. 现有测试应全部通过（scripts 接口未变）。
 6. 文档一致性检查：
   - CLAUDE.md 的 skill 计数与实际 skills/ 下目录数一致
   - 新 sub-skill 的 description 满足 Claude Code skill 自动发现规则（第一人称动词 + 触发条件）

 实施顺序

 1. 先写共享引用 approval-revise-loop.md（其他 5 个 skill 都引用它）
 2. 写 5 个 sub-skill SKILL.md（可并行 —— 均引用同一模板）
 3. 改造主 skills/long-task-increment/SKILL.md
 4. 同步 CLAUDE.md
 5. 运行冒烟与回归测试

