# 对齐校验执行协议（Alignment Validation Execution Protocol）

## 何时运行

Expert track Step E10。由 SKILL.md 在 Classify/Write/Validate/Granularity/Deferral（E9）之后、SRS Reviewer（E11）之前调用。

## 目的

反向校验：给定已写好的 SRS，它是否真的解决了 E1 识别的根因问题？本步用于捕捉最危险的需求失效形态 — 形式上正确但解决错问题的 SRS。

这是一次内部检查。除非发现特定失败需要干预，否则不与用户交互。

## E10a. 根因可追溯性检查

对 Pain Map（来自 E1，存于 Section 1.3）中**每一行**：

1. 在 Section 4 中找到至少一条 EARS 陈述或验收准则能处理此痛点的 FR
2. 若某痛点没有对应 FR → 检查它是否显式出现在 Section 1.2 Out-of-Scope 且给出排除原因
3. 若某痛点既未被处理也未被排除 → 这是**追溯性缺口**

对 5-Whys Root Cause（来自 E1）：

1. 确认至少一条 FR 直接处理根因（不是仅处理症状）
2. 若根因未被处理 → 标记为追溯性缺口

**追溯性缺口处理**：
- 1–2 个缺口：自动解决 — 要么新增一条最小化 FR，要么追加一条显式 Out-of-Scope 条目（择新增采集更少者）
- 3+ 个缺口：使用 `AskUserQuestion`，将缺口表呈现并询问哪些应成为新 FR、哪些应成为显式排除

## E10b. JTBD 结果验证

定位 E1 产生的 JTBD 陈述（存于 Section 1.3）。

检查："如果用户完成 Section 4 中全部 Must 优先级 FR，是否达成了 JTBD 的 'so I can [outcome]'？"

- **YES** → 继续
- **NO** → 识别 JTBD 结果中未覆盖的部分。通过 AskUserQuestion 向用户呈现缺口：
  > "你陈述的目标是 '[JTBD outcome]'。当前需求未完全覆盖 [missing aspect]。是否需要为此新增一条需求，或当前范围已足够？"
  - 用户选择新增 → 创建新 FR，返回 E9 分类
  - 用户确认当前范围足够 → 记为 **PARTIAL**，继续

**关卡**：JTBD 校验阻塞 E11 直至解决。可接受结果：
- **PASS** — JTBD 完全可达
- **PARTIAL** — 用户显式确认尽管 JTBD 覆盖不完整，当前范围已足够

FAIL（未经用户确认的未解决 JTBD 缺口）不可进入 E11。

## E10c. Pre-Mortem

LLM 自我评估（除非发现非平凡项，否则不与用户交互）：

> "如果我们完全按 SRS 写的去建，用户仍可能不满意的是什么？"

对照检查：
- E2 的 workaround probe 回答 — 现有变通流程中每一个令人沮丧的步骤是否都有至少一条 FR 处理？
- E3 的场景走查叙述 — 所有提取到的流程缺口是否都在最终 FR 列表中得到解决？
- E6 隐藏需求探针（PII / 无障碍 / i18n / 安全）— 每个 YES 回答是否都变成了显式 NFR？
- Pain Map 条目 — 是否存在只部分处理的项（变通流程被消除但根因仍在）？

对每个 pre-mortem 发现：
- 应为 FR → 新增（返回 E9 分类）
- 应为 NFR → 新增
- 已知风险但当前不可执行 → 加入 Section 11 Open Questions

## E10d. 孤儿 FR 检测（镀金检查）

对 Section 4 中每条 FR，检查其是否具有可追溯的起源：
- 关联到 Pain Map 的某行（处理某个陈述的痛点）
- 关联到 JTBD 结果（为达成目标所必需）
- 来自走查步骤（E3 提取）
- 来自隐藏需求探针（E6）

若某 FR **无任何可追溯起源**：
- 检查是否有其他 FR 依赖它（基础设施 / 工具类 FR 常无直接痛点关联）
- 若无依赖 → 在 Section 11 Open Questions 中标记：
  > "FR-xxx has no traceable pain point or JTBD link — confirm in scope or defer to a future increment."

**不得**自动移除孤儿 FR。呈现给用户知情就是本步的动作。

## 输出

将对齐校验结果写入 SRS Section 1.3：

```
**Alignment Validation**: PASS / PARTIAL / FAIL
- Root cause coverage: N of M pain points addressed
- JTBD outcome: achieved / partially achieved (user-confirmed) / not achieved
- Pre-mortem findings: N items added / 0 items found
- Orphan FRs flagged: N items in Open Questions / 0
```

**PARTIAL**（经用户确认的 JTBD）可接受，不阻塞 E11。
**FAIL** 于 JTBD（E10b）且未获用户确认时阻塞 E11 直至解决。
