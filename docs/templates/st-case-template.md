# ST Test Case Template — ISO/IEC/IEEE 29119-3

> This template defines the structure for per-feature system test case documents.
> The LLM generates test case content following this structure.
> Users may override this template via `st_case_template_path` in `feature-list.json`.
> Users may also provide a style/language example via `st_case_example_path`.

---

## Document Header

```markdown
# 测试用例集: {feature_title}

**Feature ID**: {feature_id}
**关联需求**: {requirement_ids}  (e.g., FR-001, FR-002, NFR-003)
**日期**: {YYYY-MM-DD}
**测试标准**: ISO/IEC/IEEE 29119-3
**模板版本**: 1.0
```

## Summary Table

```markdown
## 摘要

| 类别 | 用例数 |
|------|--------|
| functional | N |
| boundary | N |
| ui | N |
| security | N |
| performance | N |
| **合计** | **N** |
```

## Test Case Block (repeat per case)

Each test case MUST include ALL of the following sections. No section may be omitted.

```markdown
---

### 用例编号

ST-{CATEGORY}-{FEATURE_ID}-{SEQ}

### 关联需求

{FR-xxx / NFR-xxx}（{需求标题}）

### 测试目标

{本用例验证的具体内容，一句话描述}

### 前置条件

- {前置条件 1}
- {前置条件 2}
- ...

### 测试步骤

| Step | 操作           | 预期结果         |
| ---- | -------------- | ---------------- |
| 1    | {具体操作}     | {明确的预期结果} |
| 2    | {具体操作}     | {明确的预期结果} |
| ...  | ...            | ...              |

### 验证点

- {验证点 1 — 可观测、可断言的检查项}
- {验证点 2}
- ...

### 后置检查

- {后置检查或清理动作}
- ...

### 元数据

- **优先级**: High / Medium / Low
- **类别**: functional / boundary / ui / security / performance
- **已自动化**: Yes / No
- **测试引用**: {test_file::test_name 或 N/A}
- **Test Type**: Real / Mock
  - Real = executed against a real running environment (real DB, real HTTP service, real browser via Chrome DevTools MCP, real file system)
  - Mock = primary dependency is a mock/stub implementation
```

## Traceability Matrix

```markdown
## 可追溯矩阵

| 用例 ID | 关联需求 | verification_step | 自动化测试 | Test Type | 结果 |
|---------|----------|-------------------|-----------|---------|------|
| ST-FUNC-{id}-001 | FR-xxx | verification_step[0] | test_xxx | Real | PENDING |
| ST-FUNC-{id}-002 | FR-xxx | verification_step[1] | test_xxx | Real | PENDING |
| ... | ... | ... | ... | ... | ... |
```

## Real Test Case Execution Summary

```markdown
## Real Test Case Execution Summary

| Metric | Count |
|--------|-------|
| Total Real Test Cases | N |
| Passed | N |
| Failed | N |
| Pending | N |

> Real test cases = test cases with Test Type `Real` (executed against a real running environment, not Mock).
> Any Real test case FAIL blocks the feature from being marked `"passing"` — must be fixed and re-executed.
```

---

## Category Definitions

| Category | Abbrev | Description | When to use |
|----------|--------|-------------|-------------|
| `functional` | FUNC | Happy-path and error-path verification | Always — every feature needs functional tests |
| `boundary` | BNDRY | Edge cases, limits, empty/max/zero values | Always — test boundaries of inputs and states |
| `ui` | UI | Chrome DevTools interaction + visual verification | Only when feature has `"ui": true` |
| `security` | SEC | Injection, authorization, data validation | When feature handles user input, auth, or external data |
| `performance` | PERF | Response time, throughput, resource usage | Only when traceable to NFR-xxx performance requirements |

## Case ID Format

```
ST-{CATEGORY}-{FEATURE_ID}-{SEQ}
```

- `{CATEGORY}`: One of FUNC, BNDRY, UI, SEC, PERF
- `{FEATURE_ID}`: Feature ID from feature-list.json (zero-padded to 3 digits: 001, 002, ...)
- `{SEQ}`: Sequential number within category for this feature (001, 002, ...)

Examples:
- `ST-FUNC-005-001` — First functional test case for feature #5
- `ST-UI-005-002` — Second UI test case for feature #5
- `ST-SEC-012-001` — First security test case for feature #12

## UI Test Case Requirements (MANDATORY — Cannot Be Skipped)

For `"ui": true` features, UI category test cases **MUST** be generated and **CANNOT be skipped**. These test cases verify browser-based UI behavior via Chrome DevTools MCP.

### Chrome DevTools MCP Requirement

**UI test cases MUST use Chrome DevTools MCP tools** for verification. The test steps should be written so they can be directly translated to MCP tool calls:

| MCP Tool | Usage in Test Steps |
|----------|---------------------|
| `navigate_page(url)` | Navigation to target URL |
| `wait_for(text)` | Wait for page load completion |
| `take_snapshot()` | Capture page state for verification |
| `click(uid)` | Click interactive elements |
| `fill(uid, value)` | Input text or select options |
| `press_key(key)` | Keyboard interactions |
| `evaluate_script(error_detector)` | Layer 1: JavaScript error detection |
| `list_console_messages(["error"])` | Layer 3: Console error verification |
| `take_screenshot()` | Visual verification capture |

### Required Elements for UI Test Cases

1. **Navigation path**: The URL or route to navigate to (from `ui_entry` or specific route)
2. **Three-Layer Detection** (all three layers are mandatory):
   - **Layer 1**: `evaluate_script(error_detector)` — automated JavaScript error detection after page load and after each interaction
   - **Layer 2**: EXPECT/REJECT clauses in `take_snapshot()` — explicit element/state verification
   - **Layer 3**: `list_console_messages(["error"])` — console error gate at end of test case
3. **Console error gate**: Post-step check — `list_console_messages(types=["error"])` must return 0
4. **UCD token reference**: Which style tokens (colors, typography, spacing) apply to verified elements
5. **Minimum 5 steps**: Every UI test case MUST have at least 5 test steps

### Example UI Test Step (with MCP mapping):

```markdown
| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | navigate_page(url='/login') | 页面开始加载 |
| 2 | wait_for(['Sign In']) → evaluate_script(error_detector) | 页面加载完成，Layer 1: count = 0 |
| 3 | take_snapshot() | EXPECT: 邮箱输入框(type=email)、密码输入框(type=password)、登录按钮; REJECT: 任何无 label 的输入框 |
| 4 | fill(uid, 'test@example.com') → fill(uid, 'password123') → click(uid) | EXPECT: 输入框显示内容，登录按钮可用 |
| 5 | wait_for(['/dashboard']) → evaluate_script(error_detector) → list_console_messages(["error"]) | 跳转至 dashboard，Layer 1: count = 0，Layer 3: 控制台无 error |
```

> **IMPORTANT**: UI test cases CANNOT be skipped with "browser testing is too complex" or similar excuses. Chrome DevTools MCP provides the browser automation capability — use it. If Chrome DevTools MCP is not available, the feature is BLOCKED until it is resolved, not skipped.

## Execution Rules

1. **Environment prerequisite**: Services must be running. If services are not running, runtime test steps are BLOCKED.
2. **Failure is a Hard Gate**: Any test case failure (step result mismatch, verification point unmet, post-check failure) blocks the feature from being marked `"passing"`. Report to user via `AskUserQuestion`.
3. **ALL bugs must be fixed**: Any bug discovered during ST testing — whether frontend, backend, or integration — MUST be fixed before the feature can be marked as passing. There is no "not my code" exemption:
   - Frontend bug (UI rendering, interaction, state) → fix it
   - Backend bug (API errors, data persistence, logic) → fix it
   - Integration bug (frontend-backend communication) → fix it
4. **No bypass allowed**: Cannot skip ST execution for any reason:
   - "Simple feature" — still needs test cases
   - **"UI tests are too complex" — UI test cases MUST use Chrome DevTools MCP, cannot be skipped**
   - "Browser testing is too complex" — UI test cases CANNOT be skipped
   - "This is a frontend bug" — **ALL bugs must be fixed**
   - "This is a backend bug" — **ALL bugs must be fixed**
   - "Env temporarily unavailable" — BLOCKED, not skipped
   - "Case might be wrong" — use the `long-task-increment` skill to modify, don't skip
   All failures must be recorded in `task-progress.md`.
5. **Environment cleanup**: Services are stopped after testing completes.

## Derivation Rules

When generating test cases from a feature's SRS acceptance criteria (via `srs_trace`):

1. Each `srs_trace` requirement must be covered by **at least one** test case
2. Features with `"ui": true` produce `ui` category test cases
3. Every feature gets at least one `functional` and one `boundary` test case
4. If the feature handles user input → add `security` test cases
5. If the feature has `"ui": true` → add `ui` test cases
6. **If the feature has `"ui": true`, UI category test cases are MANDATORY and CANNOT be skipped** — these test cases must use Chrome DevTools MCP for browser-based verification
7. If the feature traces to an NFR-xxx with performance metrics → add `performance` test cases
8. Test case steps must be concrete and executable (no vague "verify it works")
9. Expected results must be specific and assertable (no "should look correct")
