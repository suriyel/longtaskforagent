---
name: long-task-feature-st
description: "Use after quality gates pass in a long-task project — independently manages test environment lifecycle (start/cleanup), executes black-box acceptance testing per feature, generates ISO/IEC/IEEE 29119 compliant test case documents"
---

# Feature-ST —— SubAgent 分发

将黑盒验收测试委派给拥有全新上下文的 SubAgent。主 agent 仅负责分发并解析结构化结果 —— 绝不直接阅读 SRS/设计/UCD 章节、测试用例文档或执行输出。

**开始时声明：** "I'm using the long-task-feature-st skill to run acceptance testing via SubAgent."

## Step 1: 收集路径参数

从当前会话状态中收集文件路径（**不要**自行读取文件内容）：

- `feature_id` —— 当前特性 ID
- `feature_json` —— feature-list.json 中当前的 feature 对象（紧凑 JSON）
- `design_doc_path` —— `docs/plans/*-design.md` 的路径
- `srs_doc_path` —— `docs/plans/*-srs.md` 的路径
- `ucd_doc_path` —— `docs/plans/*-ucd.md` 的路径（仅 `"ui": true` 时；否则省略）
- `ats_doc_path` —— `docs/plans/*-ats.md` 的路径（存在则提供；否则省略）
- `plan_doc_path` —— `docs/features/YYYY-MM-DD-<feature-name>.md` 的路径（来自 Feature Design 步骤）
- `env_guide_path` —— `env-guide.md`（若存在）
- `quality_gates_json` —— feature-list.json 中的 quality_gates 阈值
- `tech_stack_json` —— feature-list.json 中的 tech_stack
- `working_dir` —— 项目工作目录
- `st_case_template_path` —— 来自 feature-list.json 根级（可选）
- `st_case_example_path` —— 来自 feature-list.json 根级（可选）

## Step 2: 构建 SubAgent 提示词

```
You are a Feature-ST execution SubAgent for black-box acceptance testing.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-st/references/feature-st-execution.md
2. Follow the checklist exactly (Steps 1-8): Load Context → Load Template → Derive Test Cases → Write Document → Validate → Execute → Visual Assessment (ui:true) → Cleanup
3. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters
- Feature ID: {feature_id}
- Feature: {feature_json}
- quality_gates: {quality_gates_json}
- tech_stack: {tech_stack_json}
- Working directory: {working_dir}

## Document Paths (read these yourself using the Read tool)
- Design doc: {design_doc_path}
- SRS doc: {srs_doc_path}
- UCD doc: {ucd_doc_path} (omit if not UI)
- ATS doc: {ats_doc_path} (omit if not present)
- Feature design plan: {plan_doc_path}
- Environment guide: {env_guide_path}

## Template/Example (optional)
- ST case template: {st_case_template_path} (omit if not set)
- ST case example: {st_case_example_path} (omit if not set)

## Key Constraints
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- You MUST manage service lifecycle: start before tests, cleanup after all tests
- UI test cases require browser-based verification — no skip
- If environment cannot start after 3 attempts, set Verdict to BLOCKED
- ALL automated test cases must be executed one by one — no skipping
- Manual test cases (已自动化: No) must NOT be executed by SubAgent — mark as PENDING-MANUAL in the traceability matrix and include full case details in the Manual Test Cases section of the return contract
- For `"ui": true` features: after scripted tests, you MUST perform the Exploratory Visual Assessment (Step 8). Navigate the live application yourself via Chrome DevTools MCP, screenshot every page, click every interactive element, and grade against the 4 visual quality criteria. You are an independent QA evaluator, not the developer — be skeptical. A blank canvas with working buttons is a FAIL. "Display-only" elements that render but don't respond to interaction are Major defects.
```

## Step 3: 分发 SubAgent

**Claude Code：** 使用 `Agent` 工具：
```
Agent(
  description = "Feature-ST for feature #{feature_id}",
  prompt = [the constructed prompt above]
)
```

**OpenCode：** 使用 `@mention` 语法或平台原生的 subagent 机制，提示词内容一致。

## Step 4: 解析结果

读取 SubAgent 返回的文本，定位 `**status**:` 行（统一契约字段；为向后兼容可能同时存在遗留的 `### Verdict:` 行）。

- **`**status**: pass`**（遗留：`### Verdict: PASS`）
  1. 提取下一步输入：`st_case_path`、`st_case_count`、`environment_cleaned`
  2. 若特性为 `"ui": true`：提取探索性视觉评估分数。若任一维度分数 ≤ 2 或存在 display-only 缺陷（> 0），按 FAIL 处理（SubAgent 本应已处理，但再次核查）。
  3. 在 `task-progress.md` 中记录："Feature-ST: PASS ({N} cases, all passed)" —— ui:true 时追加视觉评估最低分
  4. 若 `environment_cleaned` 为 false，按 `env-guide.md` 自行执行清理
  5. 进入下一步（Inline Check + Persist）

- **`**status**: fail`** 或 **`**status**: blocked`**（遗留：`### Verdict: FAIL` / `### Verdict: BLOCKED`）
  1. 阅读 Issues 表 —— 识别失败细节
  2. **主 agent 将每个问题归类**为以下两类之一：
     - **需人工手动测试**（立即通过 `AskUserQuestion` 升级）：AI 无法提供的 `required_configs[]` 密钥或凭据缺失；需要物理设备或超出 Chrome DevTools MCP 能力的视觉判断的 UI 校验；需要外部人工动作（第三方审批、手动账号设置、硬件交互）
     - **AI 自行修复**（其他一切）：导致测试失败的代码 bug、环境启动问题、端口冲突、依赖错误、外部服务错误、因实现问题导致的测试执行失败
  3. 对于 AI 自行修复的问题：在 `task-progress.md` 记录，修复代码或环境，重新分发 SubAgent。**无重试次数限制** —— AI 必须持续修复直到解决。
  4. 对于需人工手动测试的问题：通过 `AskUserQuestion` 携带问题细节升级。特性保持 BLOCKED 直到人工响应。
  5. **禁止绕过** —— 每个失败都必须被解决（由 AI 或人工）才能进入 Persist。

- **`**status**: clarify`**（遗留：`### Verdict: CLARIFY`）
  1. 阅读 Specification Gaps 表 —— 提取所有分类问题
  2. **交叉核对**：阅读特性设计文档的 `## Clarification Addendum` 章节（位于 `plan_doc_path`）。过滤掉其中已解决的任何缺口 —— **不要**重复提问。
  3. 对真正新增的缺口：通过 `AskUserQuestion` 呈现给用户：
     ```
     Feature-ST Specification Gap: Feature #{feature_id} ({title})

     While deriving acceptance test cases, {N} specification gap(s) were found
     that prevent writing correct expected results. For each, a suggested interpretation
     is provided — you may accept it, provide a different answer, or say "skip".

     Gap 1 [{category}]: {description}
       Source: {source}
       Impact on test cases: {impact_on_test_cases}
       Suggested: {suggested_interpretation}
       → Your answer (or "accept" / "skip"):

     Gap 2 [{category}]: ...
     ```
  4. 解析用户响应并呈现审批摘要：
     ```
     Specification Gap Summary for Feature #{feature_id}:
     1. [{category}] {description} → Resolution: {answer}

     Proceed with these resolutions? (yes / revise #N)
     ```
  5. 若批准：构造 **Specification Gap Addendum**，携带原提示词 **加上** 以下内容重新分发 SubAgent：
     ```
     ## Specification Gap Addendum (user-approved resolutions)
     | # | Category | Original Gap | Resolution | Authority |
     |---|----------|-------------|------------|-----------|
     | 1 | {category} | {description} | {resolution} | user-approved / assumed |

     Apply these resolutions as authoritative. Derive test case expected results
     from these resolutions. Do NOT re-flag them as gaps.
     ```
  6. 在 `task-progress.md` 中记录："Feature-ST: CLARIFY ({N} gaps resolved) → re-dispatching"
  7. Feature-ST **最多 1 轮澄清**（设计级歧义应已在 Feature Design 阶段捕获；ST 缺口通常较小）。若 SubAgent 收到 addendum 后仍返回 `CLARIFY`，置为 BLOCKED 并升级："Persistent specification gaps in Feature-ST. Consider using `long-task-increment` to update source documents."

### Step 4b: 手工测试评审关卡

解析完 SubAgent 的判定后，检查返回中是否有 `### Manual Test Cases` 章节。

若**没有手工测试用例**：直接跳至 Step 4 的后续处理（上面的 PASS/FAIL/BLOCKED）。

若**存在手工测试用例**：

1. 对每一行手工测试用例，按如下格式调用 `AskUserQuestion`：

   ```
   Manual Test Required: {Case ID}

   Test Objective: {Test Objective from table}
   Reason for manual testing: {Manual Reason from table}

   Preconditions:
   {Preconditions from table}

   Test Steps:
   {Test Steps Summary from table}

   Verification Points:
   {Verification Points from table}

   ---
   Please perform this test and respond with:
   Line 1: PASS or FAIL
   Line 2: What you observed
   Line 3: Evidence (screenshot path, log excerpt, or "none")

   Example response:
   PASS
   Login page renders correctly with all expected form fields
   /tmp/screenshots/login-page.png

   To skip this test temporarily, respond: SKIP {reason}
   ```

2. 解析人工响应：
   - 第 1 行：提取 `PASS`、`FAIL` 或 `SKIP`
   - 若第 1 行无法解析：以如下提示重试**一次**：
     `Could not parse your response. Please respond with PASS, FAIL, or SKIP on the first line.`
   - 若重试后仍无法解析：记为 `BLOCKED`，原始响应作为证据

3. 记录结果：
   - `PASS` → 将追溯矩阵 `结果` 更新为 `MANUAL-PASS`，记录观察
   - `FAIL` → 将追溯矩阵 `结果` 更新为 `MANUAL-FAIL`，记录观察
   - `SKIP {reason}` → 将追溯矩阵 `结果` 更新为 `BLOCKED`，记录原因
     （保留"禁止绕过"原则 —— BLOCKED 被跟踪，而非静默跳过）

4. 收集完所有手工用例后：
   - 更新测试用例文档（`docs/test-cases/feature-{id}-{slug}.md`）：
     - 将每个手工用例追溯矩阵的 `结果` 设为收集到的结果
     - 更新 **Manual Test Case Summary** 章节计数
   - 重新评估特性级判定：
     - 若 SubAgent 判定为 PASS **且** 所有手工用例为 `MANUAL-PASS` → 最终判定 **PASS**
     - 若任一手工用例为 `MANUAL-FAIL` → 最终判定 **FAIL**（与自动化失败同等）
     - 若任一手工用例为 `BLOCKED` → 最终判定 **BLOCKED**

5. 以最终判定进入 Step 4 的后续处理（上面既有 PASS/FAIL/BLOCKED 逻辑）。

## 集成

**调用方：** `long-task-work`（Step 9）
**依赖：** Quality Gates 已通过（long-task-quality 完成）
**产出：** `docs/test-cases/feature-{id}-{slug}.md` 含执行结果 + 结构化摘要
**下游：** Inline Check + Persist（Worker Step 10 + 11）
