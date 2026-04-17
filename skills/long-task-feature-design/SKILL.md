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
- 由 `long-task-work` 作为子 skill 调用（路由不会直接调用）

> **对于 `category: "bugfix"` 的特性**：SubAgent 应聚焦于：(1) 根因文档（来自 `root_cause` 字段）；(2) 针对性修复方案；(3) 基于 SRS 验收标准的回归测试清单（通过 `srs_trace`）。除非缺陷直接涉及，否则跳过完整接口契约、数据流图与状态图。

## Step 1: 收集路径参数

从当前会话状态中收集以下内容。不要自行阅读文档内容：

- `feature_json` —— feature-list.json 中当前的 feature 对象（紧凑 JSON）
- `quality_gates_json` —— feature-list.json 中的 quality_gates（紧凑 JSON）
- `tech_stack_json` —— feature-list.json 中的 tech_stack（紧凑 JSON）
- `design_doc_path` —— 设计文档路径（`docs/plans/*-design.md`）
- `design_start` / `design_end` —— §2.N 子节的行号范围（来自 Orient Document Lookup）
- `srs_doc_path` —— SRS 文档路径（`docs/plans/*-srs.md`）
- `srs_start` / `srs_end` —— FR-xxx 子节的行号范围（来自 Orient Document Lookup）
- `ucd_doc_path` —— UCD 文档路径（仅当 `"ui": true` 时；否则省略）
- `ucd_start` / `ucd_end` —— 相关 UCD 章节的行号范围（如适用）
- `ats_doc_path` —— ATS 文档路径（`docs/plans/*-ats.md`），若存在；否则省略
- `constraints` —— feature-list.json 根级的 constraints[]
- `assumptions` —— feature-list.json 根级的 assumptions[]
- `output_path` —— 目标文件：`docs/features/YYYY-MM-DD-<feature-name>.md`
- `working_dir` —— 项目工作目录

## Step 2: 构建 SubAgent 提示词

```
You are a Feature Design execution SubAgent.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-design/references/feature-design-execution.md
2. Read the template: Read {skills_root}/long-task-feature-design/references/feature-design-template.md
3. Read design section: Read {design_doc_path} lines {design_start} to {design_end}
4. Read SRS section: Read {srs_doc_path} lines {srs_start} to {srs_end}
5. Read UCD sections: Read {ucd_doc_path} lines {ucd_start} to {ucd_end} (only if ui:true)
5b. Read ATS mapping table: Read {ats_doc_path} (only if ATS doc exists) — locate the mapping rows for the feature's requirement ID(s) (from srs_trace); extract required categories
5c. Read internal API contracts: Read {design_doc_path} Section 4 — locate rows where this feature appears as Provider or Consumer. These define the exact schemas this feature must produce or consume.
6. Follow the execution rules to produce the detailed design document
7. Write the document to: {output_path}
8. Return your result using the Structured Return Contract in the execution rules

## Input Parameters
- Feature: {feature_json}
- quality_gates: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Constraints: {constraints}
- Assumptions: {assumptions}
- ATS doc path: {ats_doc_path} (or "none" if no ATS doc exists)
- Working directory: {working_dir}

## Key Constraints
- Write the complete design document to {output_path}
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

读取 SubAgent 返回的文本，定位 `**status**:` 行（统一契约字段；为向后兼容，可能同时存在遗留的 `### Verdict:` 行）。

- **`**status**: pass`**（遗留：`### Verdict: PASS`）
  1. 确认设计文档文件已写入 `output_path`
  2. **视觉渲染契约抽查（仅 ui:true）：** 主 agent（非 SubAgent）读取生成文档中的 `## Visual Rendering Contract` 章节并校验：
     - 至少有一个视觉元素带有具体的 DOM/Canvas 选择器（不能泛化为"the page"或"the UI"）
     - 已指定渲染技术（Canvas 2D / WebGL / DOM / SVG / CSS）
     - 至少有一条正向渲染断言引用了具体的视觉结果（而非仅"element is visible"）
     - 测试清单中 `UI/render` 行数量 ≥ 视觉渲染契约元素数量
     - **任一校验失败**：携带反馈重新分发 SubAgent："Visual Rendering Contract is incomplete — [specific gap]. A blank page that passes Layer 1 error detection is NOT acceptable. Every visual element the user should see must be listed with a testable selector and assertion."
  3. 提取下一步输入：`feature_design_doc`、`test_inventory_count`、`existing_code_reuse_count`
  4. 在 `task-progress.md` 中记录："Feature Design: PASS ({N} test scenarios, {M} existing-code reuses)"
  5. 若 `assumption_count > 0`：追加写入 `task-progress.md`："({K} assumptions documented in Clarification Addendum)"
  6. 进入 TDD（Steps 5-7）

- **`**status**: clarify`**（遗留：`### Verdict: CLARIFY`）
  1. 读取 Ambiguities 表 —— 提取所有分类问题
  2. 使用 `AskUserQuestion` 以结构化格式向用户呈现：
     ```
     Feature Design Clarification Required: Feature #{id} ({title})

     While analyzing requirements and design documents, {N} ambiguity(ies) were found
     that affect the design. For each, a suggested interpretation is provided —
     you may accept it, provide a different answer, or say "skip" to use the suggestion as an assumption.

     Ambiguity 1 [{category}]: {description}
       Source: {source}
       Impact: {impact}
       Suggested: {suggested_interpretation}
       → Your answer (or "accept" to use suggested, or "skip" to assume):

     Ambiguity 2 [{category}]: ...
     ```
  3. 解析用户回复 —— 对每条歧义记录：
     - "accept" 或具体回答 → Resolution，Authority = "user-approved"
     - "skip" → Resolution = 建议解释，Authority = "assumed"
  4. **审批关卡**：所有回答收集完毕后，通过 `AskUserQuestion` 呈现汇总：
     ```
     Clarification Summary for Feature #{id}:
     1. [{category}] {description} → Resolution: {answer} (Authority: {authority})
     2. ...

     Proceed with these resolutions? (yes / revise #N)
     ```
     - 若批准：进入第 5 步
     - 若用户需要修改：重新询问对应条目，再次呈现汇总
  5. 构建 **Clarification Addendum**，携带原始提示词 **以及** 以下内容重新分发 SubAgent：
     ```
     ## Clarification Addendum (user-approved resolutions)
     | # | Category | Original Ambiguity | Resolution | Authority |
     |---|----------|--------------------|------------|-----------|
     | 1 | {category} | {description} | {resolution} | user-approved / assumed |

     Apply these resolutions as authoritative constraints. Do NOT re-flag these
     as ambiguities. Incorporate them into the design as if they were in the
     original SRS/Design documents.
     ```
  6. 在 `task-progress.md` 中记录："Feature Design: CLARIFY ({N} ambiguities resolved) → re-dispatching"
  7. **最多 2 轮澄清**：若 SubAgent 收到澄清后第二次仍返回 `CLARIFY`，将残留歧义升级给用户：
     "Persistent specification gaps found after 2 clarification rounds. Consider using `long-task-increment` to update the SRS/Design documents."
     - 若用户确认"SRS 需要更新"：在 `task-progress.md` 记录缺口，建议调用 `long-task-increment`，跳至下一个可执行特性
     - 若用户提供最终答复：纳入后再分发最后一次
     - 若仍无法解决：置为 BLOCKED

- **`**status**: fail`**（遗留：`### Verdict: FAIL`）
  1. 读取 Issues 表 —— 识别哪些章节不完整
  2. 如有需要，携带补充上下文重新分发 SubAgent（最多 2 次重试）
  3. 若仍未通过，通过 `AskUserQuestion` 升级给用户

- **`**status**: blocked`**（遗留：`### Verdict: BLOCKED`）
  1. 读取 Issues 表 —— 识别阻塞原因
  2. 通过 `AskUserQuestion` 升级给用户

## 集成

**调用方：** long-task-work（Step 4）
**依赖：** 系统设计文档、SRS、feature-list.json
**产出：** `docs/features/YYYY-MM-DD-<feature-name>.md`（由 SubAgent 写入）
**下游：** long-task-tdd（通过 Work 的 Steps 5-7）
