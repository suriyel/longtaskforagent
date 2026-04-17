# ST 测试用例模板 —— ISO/IEC/IEEE 29119-3

> 本模板定义单特性（per-feature）系统测试用例文档的结构。
> LLM 按此结构生成测试用例内容。
> 用户可通过 `feature-list.json` 中的 `st_case_template_path` 覆盖此模板。
> 用户还可通过 `st_case_example_path` 提供风格/语言参考示例。

---

## 文档头（Document Header）

```markdown
# 测试用例集: {feature_title}

**Feature ID**: {feature_id}
**关联需求**: {requirement_ids}  (e.g., FR-001, FR-002, NFR-003)
**日期**: {YYYY-MM-DD}
**测试标准**: ISO/IEC/IEEE 29119-3
**模板版本**: 1.0
```

## 摘要表（Summary Table）

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

## 测试用例块（按用例重复）

每个测试用例必须包含以下全部小节，不允许省略任何一节。

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
- **手动测试原因**: {physical-device / visual-judgment / external-action / other: description} (required when 已自动化: No)
- **测试引用**: {test_file::test_name 或 N/A}
- **Test Type**: Real / Mock
  - Real = executed against a real running environment (real DB, real HTTP service, real browser via Chrome DevTools MCP, real file system)
  - Mock = primary dependency is a mock/stub implementation
```

## 可追溯矩阵（Traceability Matrix）

```markdown
## 可追溯矩阵

| 用例 ID | 关联需求 | verification_step | 自动化测试 | Test Type | 结果 |
|---------|----------|-------------------|-----------|---------|------|
| ST-FUNC-{id}-001 | FR-xxx | verification_step[0] | test_xxx | Real | PENDING |
| ST-FUNC-{id}-002 | FR-xxx | verification_step[1] | test_xxx | Real | PENDING |
| ... | ... | ... | ... | ... | ... |

> 结果 valid values: `PENDING`, `PASS`, `FAIL`, `MANUAL-PASS`, `MANUAL-FAIL`, `BLOCKED`, `PENDING-MANUAL`
> - `MANUAL-PASS` / `MANUAL-FAIL`: result collected via human review gate (for `已自动化: No` cases)
> - `PENDING-MANUAL`: awaiting human review (set by SubAgent, resolved by dispatcher)
```

## Real 测试用例执行摘要（Real Test Case Execution Summary）

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

## 手动测试用例摘要（Manual Test Case Summary）

> 本节仅在文档包含手动测试用例（`已自动化: No`）时出现。

```markdown
## Manual Test Case Summary

| Metric | Count |
|--------|-------|
| Total Manual Test Cases | N |
| Manual Passed (MANUAL-PASS) | N |
| Manual Failed (MANUAL-FAIL) | N |
| Blocked | N |
| Pending (PENDING-MANUAL) | N |

> Manual test cases = test cases with `已自动化: No`. Results collected via human review gate after automated execution.
> Any MANUAL-FAIL blocks the feature from being marked `"passing"` — same as automated FAIL.
```

---

## 类别定义（Category Definitions）

| Category | Abbrev | 说明 | 何时使用 |
|----------|--------|-------------|-------------|
| `functional` | FUNC | 正常路径与错误路径验证 | 始终 —— 每个 feature 都需要 functional 测试 |
| `boundary` | BNDRY | 边界情况、上限、空值/最大值/零值 | 始终 —— 测试输入与状态的边界 |
| `ui` | UI | Chrome DevTools 交互与视觉验证 | 仅当 feature 带 `"ui": true` |
| `security` | SEC | 注入、授权、数据校验 | 当 feature 涉及用户输入、认证或外部数据 |
| `performance` | PERF | 响应时间、吞吐、资源占用 | 仅当可追溯到 NFR-xxx 的性能需求 |

## 用例 ID 格式（Case ID Format）

```
ST-{CATEGORY}-{FEATURE_ID}-{SEQ}
```

- `{CATEGORY}`: FUNC、BNDRY、UI、SEC、PERF 之一
- `{FEATURE_ID}`: 来自 feature-list.json 的 feature ID（以 3 位零填充：001, 002, ...）
- `{SEQ}`: 该 feature 在同一类别内的顺序号（001, 002, ...）

示例：
- `ST-FUNC-005-001` —— feature #5 的第一个 functional 测试用例
- `ST-UI-005-002` —— feature #5 的第二个 UI 测试用例
- `ST-SEC-012-001` —— feature #12 的第一个 security 测试用例

## UI 测试用例要求（强制 —— 不可跳过）

对于 `"ui": true` 的 feature，UI 类别测试用例**必须**生成且**不可跳过**。这些用例通过 Chrome DevTools MCP 验证基于浏览器的 UI 行为。

### Chrome DevTools MCP 要求

**UI 测试用例必须使用 Chrome DevTools MCP 工具**进行验证。测试步骤应编写为能够直接翻译为 MCP 工具调用：

| MCP Tool | 在测试步骤中的用途 |
|----------|---------------------|
| `navigate_page(url)` | 导航到目标 URL |
| `wait_for(text)` | 等待页面加载完成 |
| `take_snapshot()` | 捕获页面状态以便验证 |
| `click(uid)` | 点击交互元素 |
| `fill(uid, value)` | 输入文本或选择选项 |
| `press_key(key)` | 键盘交互 |
| `evaluate_script(error_detector)` | Layer 1：JavaScript 错误检测 |
| `evaluate_script(positive_render_checker, selectors, canvasIds)` | Layer 1b：正向渲染验证 —— 断言预期视觉元素确实存在（而非仅仅无错误） |
| `list_console_messages(["error"])` | Layer 3：控制台错误验证 |
| `take_screenshot()` | 视觉验证截图 |

### UI 测试用例必需元素

1. **导航路径**：跳转的目标 URL 或路由（来自 `ui_entry` 或具体路由）
2. **四层检测**（`ui:true` 必须全部包含）：
   - **Layer 1**：`evaluate_script(error_detector)` —— 页面加载后以及每次交互后的自动 JavaScript 错误检测
   - **Layer 1b**：`evaluate_script(positive_render_checker, selectors, canvasIds)` —— 正向渲染验证：断言预期视觉元素确实存在且可见（而非仅仅无错误）。selectors 与 canvasIds 来自 Feature Design 的 Visual Rendering Contract。`missingCount > 0` 属于硬 FAIL。
   - **Layer 2**：在 `take_snapshot()` 中的 EXPECT/REJECT 条款 —— 显式元素/状态验证
   - **Layer 3**：用例末尾的 `list_console_messages(["error"])` —— 控制台错误关卡
3. **控制台错误关卡**：后置检查 —— `list_console_messages(types=["error"])` 必须返回 0
4. **UCD token 引用**：标注所验证元素所适用的样式 token（颜色、排版、间距）
5. **至少 5 个步骤**：每个 UI 测试用例至少包含 5 个测试步骤

### UI 测试步骤示例（含 MCP 对应）：

```markdown
| Step | 操作 | 预期结果 |
| ---- | ---- | -------- |
| 1 | navigate_page(url='/login') | 页面开始加载 |
| 2 | wait_for(['Sign In']) → evaluate_script(error_detector) | 页面加载完成，Layer 1: count = 0 |
| 3 | take_snapshot() | EXPECT: 邮箱输入框(type=email)、密码输入框(type=password)、登录按钮; REJECT: 任何无 label 的输入框 |
| 4 | fill(uid, 'test@example.com') → fill(uid, 'password123') → click(uid) | EXPECT: 输入框显示内容，登录按钮可用 |
| 5 | wait_for(['/dashboard']) → evaluate_script(error_detector) → list_console_messages(["error"]) | 跳转至 dashboard，Layer 1: count = 0，Layer 3: 控制台无 error |
```

> **重要**：UI 测试用例不得以"浏览器测试太复杂"或类似理由跳过。Chrome DevTools MCP 提供浏览器自动化能力 —— 必须使用。若 Chrome DevTools MCP 不可用，该 feature 进入 BLOCKED 状态直到解决，而非跳过。

## 执行规则（Execution Rules）

1. **环境前置**：服务必须处于运行中。若服务未运行，运行期的测试步骤进入 BLOCKED。
2. **失败即硬关卡（Hard Gate）**：任何用例失败（步骤结果不匹配、验证点未满足、后置检查失败）都将阻断该 feature 被标记为 `"passing"`。通过 `AskUserQuestion` 汇报给用户。
3. **所有 bug 必须修复**：ST 测试期间发现的任何 bug —— 无论前端、后端还是集成 —— **必须**在 feature 标记为 passing 前修复。不存在"非我代码"豁免：
   - 前端 bug（UI 渲染、交互、状态） → 修
   - 后端 bug（API 错误、数据持久化、逻辑） → 修
   - 集成 bug（前后端通信） → 修
4. **不得绕过**：任何理由都不得跳过 ST 执行：
   - "简单 feature" —— 仍需测试用例
   - **"UI 测试太复杂" —— UI 测试用例必须使用 Chrome DevTools MCP，不得跳过**
   - "浏览器测试太复杂" —— UI 测试用例不得跳过
   - "这是前端 bug" —— **所有 bug 必须修复**
   - "这是后端 bug" —— **所有 bug 必须修复**
   - "环境临时不可用" —— BLOCKED，非跳过
   - "用例可能有误" —— 使用 `long-task-increment` skill 修改，不得跳过
   所有失败必须记录进 `task-progress.md`。
5. **环境清理**：测试完成后停止服务。

## 派生规则（Derivation Rules）

从 feature 的 SRS 验收准则（通过 `srs_trace`）派生测试用例时：

1. 每条 `srs_trace` 需求必须**至少**被一个测试用例覆盖
2. 带 `"ui": true` 的 feature 产出 `ui` 类别测试用例
3. 每个 feature 至少有一条 `functional` 与一条 `boundary` 测试用例
4. 若 feature 处理用户输入 → 追加 `security` 测试用例
5. 若 feature 带 `"ui": true` → 追加 `ui` 测试用例
6. **若 feature 带 `"ui": true`，UI 类别测试用例强制必需，不得跳过** —— 这些用例必须使用 Chrome DevTools MCP 进行基于浏览器的验证
7. 若 feature 可追溯到带性能指标的 NFR-xxx → 追加 `performance` 测试用例
8. 测试步骤必须具体可执行（不得使用模糊的"验证是否正常工作"）
9. 预期结果必须明确可断言（不得使用"看起来应该对"）
