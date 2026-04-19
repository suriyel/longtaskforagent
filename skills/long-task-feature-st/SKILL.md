---
name: long-task-feature-st
description: "Use after quality gates pass in a long-task project — independently manages test environment lifecycle (start/cleanup), executes black-box acceptance testing per feature, generates ISO/IEC/IEEE 29119 compliant test case documents"
---

# Feature-ST —— SubAgent 分发

将黑盒验收测试委派给拥有全新上下文的 SubAgent。主 agent 仅负责分发并解析结构化结果 —— 绝不直接阅读 SRS/设计/UCD 章节、测试用例文档或执行输出。

**开始时声明：** "I'm using the long-task-feature-st skill to run acceptance testing via SubAgent."

## Step 1: 收集动态字段（最小输入集）

固定路径 / feature-list 派生数据由 SubAgent 自行解析；主 agent 仅传动态字段：

- `feature_id` —— 当前特性 ID
- `feature_list_path` —— `feature-list.json` 路径
- `feature_design_doc_path` —— `docs/features/YYYY-MM-DD-<slug>.md`（来自 Feature Design 步骤；动态日期）
- `working_dir` —— 项目工作目录

## Step 2: 构建 SubAgent 提示词

```
You are a Feature-ST execution SubAgent for black-box acceptance testing.

## Your Task
1. Read the execution rules: Read {skills_root}/long-task-feature-st/references/feature-st-execution.md
2. Self-resolve fixed inputs:
   a. Read {feature_list_path} → parse JSON; pick features[i] with id == {feature_id} → derive `feature` (含 srs_trace / ui / category) + 根级 `quality_gates` / `tech_stack` / `st_case_template_path` / `st_case_example_path` (optional root fields)
   b. Glob `docs/plans/*-design.md` → `design_doc_path`
   c. Glob `docs/plans/*-srs.md` → `srs_doc_path`
   d. Glob `docs/plans/*-ucd.md` → `ucd_doc_path` (only if feature.ui == true; else skip)
   e. Glob `docs/plans/*-ats.md` → `ats_doc_path` (if no match, proceed without ATS category enforcement but emit a blocker `[ATS-MISSING]` warning if feature requires it)
   f. Glob `env-guide.md` → §1 服务生命周期、§2 激活、§3 命令
3. Follow the checklist exactly (Steps 1-8): Load Context → Load Template → Derive Test Cases → Write Document → Validate → Execute → Visual Assessment (ui:true) → Cleanup
4. Return your result using the Structured Return Contract at the end of the execution rules

## Input Parameters (minimal; derive the rest yourself)
- feature_id: {feature_id}
- feature_list_path: {feature_list_path}
- feature_design_doc_path: {feature_design_doc_path}
- working_dir: {working_dir}

## Key Constraints
- Do NOT mark the feature as "passing" in feature-list.json — only report results
- You MUST manage service lifecycle: start before tests, cleanup after all tests
- UI test cases require browser-based verification — no skip
- If environment cannot start after 3 attempts, set status=blocked with blocker `[ENV-ERROR] ...`
- ALL automated test cases must be executed one by one — no skipping
- Manual test cases (已自动化: No) must NOT be executed by SubAgent — return them as blocker `[MANUAL_TEST_REQUIRED] case_id=... | reason=... | steps_summary=...` entries so the main agent can organize the hand-off to the user
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

- **`**status**: fail`**
  1. 读 evidence 定位代码 bug / 环境问题 —— 这些由 SubAgent 内部修复，不应返 fail；出现 fail 意味着 SubAgent 已超出自修能力或 ST 策略决定上报。
  2. 按 `skills/using-long-task/references/approval-revise-loop.md` 的 Failure Addendum 规则重分发（计入 revise 上限 2 轮）。
  3. 超限 → escalate，AskUserQuestion 收集手工诊断后重分发。

- **`**status**: blocked`**
  1. 读 blockers[]。每条以前缀开头，按 `using-long-task/references/approval-revise-loop.md` 的前缀表分流：
     - `[MANUAL_TEST_REQUIRED]` —— 缺凭据、需物理设备、需人工视觉判断。主 agent 展示测试步骤，AskUserQuestion 等待用户手工完成并回报结果。
     - `[SRS-MISSING]` / `[SRS-VAGUE]` —— 规范缺口，Feature Design 未捕获。主 agent 呈 A/B/C：(A) 补 SRS / (B) 以建议解释作 assumption / (C) 打回 `long-task-increment`。
     - `[ATS-CATEGORY-MISSING-ST]` —— ATS 必须类别无 ST 用例。主 agent 呈 A/B：(A) 扩 ST 用例（Clarification Addendum 重分发） / (B) 豁免该类别（需显式授权，留痕）。
     - `[ENV-ERROR]` —— 环境/服务启动故障超 SubAgent 自修。主 agent 展示故障详情，用户修复后回应 retry。
  2. 按 loop.md 以 Clarification Addendum 重分发（不计入 revise 上限）；同一前缀 3 次仍 blocked → escalate。

**交叉核对（重分发前）**：主 agent 在组装 Clarification Addendum 之前，先读 Feature Design 文档的 `## Clarification Addendum` 章节，过滤已在 Feature Design 阶段解决的同类规范条目——不要重复提问。

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
