---
name: long-task-feature-design
description: "Use before TDD in a long-task project — produce feature-level detailed design with interface contracts, algorithm pseudocode, diagrams, and test inventory"
---

# 特性级详细设计 —— SubAgent 分发

将特性详细设计的生成委派给拥有全新上下文的 SubAgent。主 agent 仅负责分发并解析结构化结果 —— 绝不自行阅读设计文档 / SRS / UCD 的章节，也不直接写入设计文档。

**开始时声明：** "I'm using the long-task-feature-design skill to produce a detailed design via SubAgent."

## 何时运行

- Worker Step 4，TDD（Steps 5-7）之前
- 每一个特性都要运行（`category: "bugfix"` 的特性使用精简版）
- 由 `long-task-work-design` 作为子 skill 调用（路由不会直接调用）

> **对于 `category: "bugfix"` 的特性**：SubAgent 应聚焦于：(1) 根因文档（来自 `root_cause` 字段）；(2) 针对性修复方案；(3) 基于 SRS 验收标准的回归测试清单（通过 `srs_trace`）。除非缺陷直接涉及，否则跳过完整接口契约、数据流图与状态图。

## Step 1: 收集动态字段（最小输入集）

从当前会话状态中收集以下几项。固定路径 / feature-list 派生数据（包括 `output_path`）由 SubAgent 自行解析：

- `feature_id` —— 目标特性 ID
- `feature_list_path` —— `feature-list.json` 的路径
- `design_section` —— `§2.N` 行号起止（来自 Orient Document Lookup）
- `srs_section` —— FR-xxx 行号起止（来自 Orient Document Lookup）
- `ucd_section` —— UCD 行号起止（仅 ui:true；否则 null）
- `working_dir` —— 项目工作目录

## Step 2: 构建 SubAgent 提示词

```
You are a Feature Design execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-design/references/feature-design-execution.md
2. Read the template: Read {skills_root}/long-task-feature-design/references/feature-design-template.md
3. Self-resolve inputs (固定数据源无需主 agent 传入):
   a. Read {feature_list_path} → parse the JSON; pick `features[i]` with `id == {feature_id}`; derive `feature`, `tech_stack`, `quality_gates`, `constraints`, `assumptions`
   b. Glob `docs/plans/*-design.md` (single match expected) → `design_doc_path`
   c. Glob `docs/plans/*-srs.md` (single match expected) → `srs_doc_path`
   d. Glob `docs/plans/*-ucd.md` → `ucd_doc_path` (only if `feature.ui == true`; else skip)
   e. Glob `docs/plans/*-ats.md` → `ats_doc_path` (if no match, proceed without ATS alignment)
   f. Derive output path via the authoritative script:
      `python scripts/feature_paths.py design-doc --feature {feature_id}` → capture stdout as `{output_path}`
      (do NOT hand-roll slug / date-prefix logic — the script is the single source of truth)
4. Read design section: Read {design_doc_path} lines {design_section.start} to {design_section.end}
5. Read SRS section: Read {srs_doc_path} lines {srs_section.start} to {srs_section.end}
6. Read UCD sections: Read {ucd_doc_path} lines {ucd_section.start} to {ucd_section.end} (only if ui:true)
7. Read ATS mapping table: Read {ats_doc_path} (only if ATS doc exists) — locate the mapping rows for the feature's requirement ID(s) (from srs_trace); extract required categories
8. Read internal API contracts: Read {design_doc_path} Section 4 — locate rows where this feature appears as Provider or Consumer. These define the exact schemas this feature must produce or consume.
9. Follow the execution rules to produce the detailed design document
10. Write the document to: {output_path}
11. Return your result using the Structured Return Contract in the execution rules

## Input Parameters (minimal; derive the rest yourself)
- feature_id: {feature_id}
- feature_list_path: {feature_list_path}
- design_section: {design_section}   # { start, end }
- srs_section: {srs_section}         # { start, end }
- ucd_section: {ucd_section}         # { start, end } or null
- working_dir: {working_dir}
- output_path: derived via `scripts/feature_paths.py design-doc --feature {feature_id}` (step 3f)

## Key Constraints
- Write the complete design document to {output_path}
- The output path MUST come from `scripts/feature_paths.py` — do NOT hand-roll a slug or add a date prefix
- Every section must be COMPLETE or have "N/A — [reason]"
- **Step 1c Existing Code Reuse Check is mandatory**: grep the codebase for reusable symbols before finalizing Interface Contract. Populate the Existing Code Reuse table (or state "N/A — searched keywords: [...], no reusable match"). Do NOT reimplement what already exists.
- Test Inventory negative ratio must be >= 40%
- Test Inventory main categories (FUNC/BNDRY/SEC/UI/PERF/INTG) must cover all ATS-required categories for this feature's requirement(s)
- Features with external dependencies must have ≥1 INTG row per dependency type; pure-computation features: "INTG: N/A"
- Features with `"ui": true` MUST have a complete Visual Rendering Contract (§Visual Rendering Contract): all visual elements listed, rendering technology specified, positive rendering assertions defined. "N/A" is only valid for `"ui": false`. For each positive rendering assertion, at least one `UI/render` Test Inventory row must exist. Missing rows → FAIL.
- **Codebase constraints** (if `env-guide.md` §4 exists): Interface Contract method names must follow §4.3 naming conventions. Dependencies must use §4.1 internal libraries where applicable. Do not reference prohibited APIs from §4.2.
- Do NOT start TDD — only produce the design document
```

## Step 3: 分发 SubAgent

**Claude Code：** 使用 `Agent` 工具：
```
Agent(
  description = "Feature Design for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode：** 使用 `@mention` 语法或平台原生的 subagent 机制，提示词内容一致。

## Step 4: 解析结果

读取 SubAgent 返回的文本，定位 `**status**:` 行（统一契约字段）。所有用户裁决一律由主 agent（本 Worker orchestrator）按 `skills/using-long-task/references/approval-revise-loop.md` 处理；本 sub-skill **绝不**自行发起 AskUserQuestion。

- **`**status**: pass`**
  1. 确认设计文档文件已写入 `output_path`
  2. **视觉渲染契约抽查（仅 ui:true）：** 主 agent 读取生成文档中的 `## Visual Rendering Contract` 章节并校验：
     - 至少有一个视觉元素带有具体的 DOM/Canvas 选择器（不能泛化为"the page"或"the UI"）
     - 已指定渲染技术（Canvas 2D / WebGL / DOM / SVG / CSS）
     - 至少有一条正向渲染断言引用了具体的视觉结果（而非仅"element is visible"）
     - 测试清单中 `UI/render` 行数量 ≥ 视觉渲染契约元素数量
     - **任一校验失败**：走 approval-revise-loop 的 `fail` 分支（组装 Failure Addendum 重分发）："Visual Rendering Contract is incomplete — [specific gap]. A blank page that passes Layer 1 error detection is NOT acceptable."
  3. 提取 `next_step_input`：`feature_design_doc`、`test_inventory_count`、`existing_code_reuse_count`、`assumption_count`
  4. `assumption_count == 0` → 无需审批，直接进入 TDD
  5. `assumption_count > 0` → 进入 approval-revise-loop 的审批关卡（approve / revise / skip-feature / escalate）
  6. 在 `task-progress.md` 中记录："Feature Design: PASS ({N} test scenarios, {M} existing-code reuses, {K} assumptions)"

- **`**status**: blocked`**
  1. 读 blockers[] —— 每条以前缀 `[SRS-VAGUE]` / `[SRS-DESIGN-CONFLICT]` / `[SRS-MISSING]` / `[ATS-MISMATCH]` / `[ATS-BUGFIX-REGRESSION-MISSING]` / `[UCD-VAGUE]` / `[DEP-AMBIGUOUS]` / `[NFR-GAP]` / `[CONTRACT-DEVIATION]` 开头
  2. 按 `skills/using-long-task/references/approval-revise-loop.md` 的 Blockers 前缀约定表组装 AskUserQuestion（每个前缀的 A/B/C 选项见该表）
  3. 收集用户裁决 → 组装 Clarification Addendum → 重分发（不计入 revise 上限）
  4. 若同一前缀累计 3 次仍 blocked，升级为 escalate（建议 `long-task-increment` 修订上游 SRS/Design/ATS/UCD）

- **`**status**: fail`**
  1. 读 evidence 定位失败原因（通常是 §章节缺失、Test Inventory 负向占比不达标、Visual Rendering Contract 不完整等）
  2. 按 approval-revise-loop 的 Failure Addendum 规则重分发（计入 revise 上限 2 轮）
  3. 超过上限 → escalate
