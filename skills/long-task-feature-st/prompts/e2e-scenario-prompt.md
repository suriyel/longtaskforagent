# Chrome DevTools MCP E2E Scenario Derivation Prompt

## Role

You are a test engineer generating per-feature ST cases that will be **executed via Chrome DevTools MCP tools** during TDD. Each UI test step must map to a concrete MCP tool call. The goal is executable E2E scenarios — not paper checklists.

> **IMPORTANT**: UI test cases CANNOT be skipped for any reason. Chrome DevTools MCP is the **mandatory** execution vehicle for UI features. There is no alternative or workaround for UI verification.

## MCP Tool → Test Step Mapping

Every UI test step must specify which Chrome DevTools MCP tool executes it:


| User Action | MCP Tool | Test Step Format |
|------------|----------|-----------------|
| Open page | `navigate_page(url)` | "导航至 {url}" |
| Wait for load | `wait_for(text)` | "等待 '{text}' 出现" |
| Check page state | `take_snapshot()` | "获取快照，验证: EXPECT: {criteria}" |
| Click element | `click(uid)` | "点击 {element description} (uid from snapshot)" |
| Type text | `fill(uid, value)` | "在 {field description} 中填入 '{value}'" |
| Select option | `fill(uid, value)` | "在 {select description} 中选择 '{value}'" |
| Press key | `press_key(key)` | "按 {key} 键" |
| Check errors | `evaluate_script(error_detector)` | "执行 Layer 1 错误检测脚本 → count 必须为 0" |
| Check console | `list_console_messages(["error"])` | "检查控制台错误 → count 必须为 0" |
| Screenshot | `take_screenshot()` | "截图用于视觉验证" |
| Hover | `hover(uid)` | "悬停于 {element description}" |
| Drag | `drag(from_uid, to_uid)` | "将 {source} 拖动至 {target}" |


## E2E Scenario Structure (mandatory for every UI test case)

Every UI category test case MUST follow this execution flow:

```
1. navigate_page → target URL
2. wait_for → page loaded signal (key text or element)
3. evaluate_script(error_detector) → Layer 1: zero errors after page load
4. take_snapshot → verify EXPECT criteria, check REJECT criteria
5. [interaction sequence: click/fill/press_key → take_snapshot → verify EXPECT/REJECT]
   (repeat for each user action in the scenario)
6. evaluate_script(error_detector) → Layer 1 again after all interactions
7. list_console_messages(["error"]) → Layer 3: zero console errors
8. [optional: navigate to result page → verify side effects persisted]
```

**Minimum step count**: Every UI test case MUST have ≥ 5 rows in the test step table. This is a hard minimum — no exceptions for "simple" pages.

## Expansion Rules

### Rule 1: Every UI SRS Acceptance Criterion → Full E2E Scenario

A UI-related SRS acceptance criterion or Feature Design Test Inventory row like:
```
"FR-012: Given user navigates to /orders, When orders exist, Then order list table with columns is displayed"
```
Must expand to a test case with ≥ 5 steps:

| Step | 操作 | 预期结果 |
|------|------|---------|
| 1 | `navigate_page(url='/orders')` | 页面开始加载 |
| 2 | `wait_for(['订单列表'])` → `evaluate_script(error_detector)` | 页面加载完成，Layer 1 检测: count = 0 |
| 3 | `take_snapshot()` | EXPECT: 订单列表表格，列头 (名称, 日期, 金额, 状态)，至少 1 行数据; REJECT: 空表格体, "暂无订单" 提示, 加载中旋转图标卡死 |
| 4 | `click(uid)` 点击第一行订单 | EXPECT: 订单详情面板打开，显示完整订单信息 |
| 5 | `evaluate_script(error_detector)` → `list_console_messages(["error"])` | Layer 1: count = 0; Layer 3: 控制台无 error |

### Rule 2: Backend Integration Steps (非谈判性要求)

For UI features that depend on backend API features:
- Test cases MUST verify **real data from backend** — not hardcoded or mocked data
- Include at least one **data mutation + verification** scenario:
  - Create/Update/Delete via UI → verify backend persisted → refresh page → verify UI reflects change
- Include at least one **error state** scenario:
  - What does the UI show when backend returns 500/503/timeout?
  - Is the error message user-friendly? Is there a retry mechanism?
- Include at least one **empty state** scenario:
  - What does the UI show when backend returns an empty list?
  - Is the empty state visually correct per UCD?

Example multi-step:
```
| Step | 操作 | 预期结果 |
| 1 | navigate_page('/users') → wait_for(['用户列表']) | 页面加载完成 |
| 2 | evaluate_script(error_detector) | Layer 1: count = 0 |
| 3 | take_snapshot() | EXPECT: 用户表格由 GET /api/users 填充，显示至少 1 个用户; REJECT: 硬编码假数据 |
| 4 | click(uid) 点击编辑按钮 → fill(uid, '新名称') → click(uid) 保存 | EXPECT: PUT /api/users/{id} 成功，弹出保存成功提示 |
| 5 | navigate_page(type='reload') → wait_for(['用户列表']) | EXPECT: 刷新后显示更新后的名称; Layer 3: 控制台无 error |
```

### Rule 3: Cross-Page Workflow

If the feature involves navigation between multiple pages:
- Test the **complete workflow**: page A → action → page B → verify → page C → verify
- Do NOT test pages in isolation — the E2E value comes from the transitions
- Each page transition must include Layer 1 error detection on the new page

Example:
```
登录页 → 填写凭据 → 提交 → 仪表盘页 → 验证用户信息 → 点击设置 → 设置页 → 验证表单预填
```

### Rule 4: Three-Layer Detection is Non-Negotiable

Every UI test case MUST include ALL three detection layers:

| Layer | Tool | When | Hard Gate |
|-------|------|------|-----------|
| Layer 1 | `evaluate_script(error_detector)` | After page load AND after each significant interaction | count > 0 = FAIL |
| Layer 2 | EXPECT/REJECT in `take_snapshot()` verification | Every snapshot step | Missing EXPECT = FAIL |
| Layer 3 | `list_console_messages(["error"])` | At end of test case (and optionally after interactions) | count > 0 = FAIL |

**A UI test case missing ANY layer is INCOMPLETE and must be rejected.**

### Rule 5: State Mutation Verification

If the feature creates, updates, or deletes data:
1. Perform the mutation via UI (fill form → submit)
2. Navigate **away** from the current page
3. Navigate **back** (or to a different view that shows the same data)
4. Verify the mutation is reflected — this confirms backend persistence, not just frontend state
5. Check that related views are also updated (e.g., create order → order list shows new order → dashboard counter incremented)

### Rule 6: UCD Compliance in E2E Context

For UI test cases, integrate UCD compliance checks **within** the E2E flow rather than as separate static checks:
- After each `take_snapshot()`, verify that visible elements match UCD style tokens (colors, typography, spacing)
- Reference specific UCD token names in EXPECT clauses: `EXPECT: 主按钮使用 primary-600 色值, 字体为 heading-md`
- This ensures UCD compliance is verified under real rendering conditions, not just CSS inspection

## Self-Audit Checklist

Before finalizing each UI test case, verify:

- [ ] ≥ 5 steps in the test step table
- [ ] Every step specifies which MCP tool executes it
- [ ] Layer 1 (`evaluate_script`) appears at least twice (page load + post-interaction)
- [ ] Layer 2 (EXPECT + REJECT) appears in every snapshot verification step
- [ ] Layer 3 (`list_console_messages`) appears at end of test case
- [ ] At least one step verifies real backend data (not mocked)
- [ ] At least one negative/error path test case exists for this feature
- [ ] Preconditions are concrete (specific data, auth state) — not just "系统正常运行"
- [ ] Expected results are specific and assertable — no "显示正确" or "工作正常"
- [ ] **UI test case CANNOT be skipped** — Chrome DevTools MCP is mandatory for UI verification
