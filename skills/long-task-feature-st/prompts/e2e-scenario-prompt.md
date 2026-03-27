# UI E2E Scenario — Test Case Derivation Guide

## Role

You are a test engineer generating per-feature ST cases for UI E2E scenarios.
Each UI test case must be concrete, executable, and verifiable — not a paper checklist.

> **IMPORTANT**: For UI features, UI category test cases are **mandatory**. Chrome DevTools MCP
> is the default execution vehicle. Each test step should be specific enough to be
> translated into a browser automation tool call.

## E2E Scenario Structure (mandatory for every UI test case)

Every UI category test case MUST follow this execution flow:

```
1. Navigate to target UI page
2. Wait for page to load / key element to appear
3. Verify initial state — check for absence of errors
4. [Interaction sequence: user action → verify state change]
   (repeat for each user action in the scenario)
5. Verify final state — check for expected outcome
6. Check for absence of errors after all interactions
7. [optional: navigate to result page → verify side effects persisted]
```

**Minimum step count**: Every UI test case MUST have ≥ 5 rows in the test step table.
This is a hard minimum — no exceptions for "simple" pages.

## Expansion Rules

### Rule 1: Every verification_step → Full E2E Scenario

A verification step like:
```
"FR-012: Given user navigates to /orders, When orders exist, Then order list table with columns is displayed"
```
Must expand to a test case with ≥ 5 steps:

| Step | 操作 | 预期结果 |
|------|------|---------|
| 1 | 导航至 /orders 页面 | 页面开始加载 |
| 2 | 等待 '订单列表' 文字出现 | 页面加载完成，无错误 |
| 3 | 验证初始状态：订单列表表格存在，列头包含 名称/日期/金额/状态，至少 1 行数据 | EXPECT: 订单列表表格; REJECT: 空表格体, "暂无订单" 提示 |
| 4 | 点击第一行订单 | EXPECT: 订单详情面板打开，显示完整订单信息 |
| 5 | 验证无错误状态：页面无错误提示 | 最终状态：无 console error，无异常 |

### Rule 2: Backend Integration Steps

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
| 1 | 导航至 /users 页面 | 页面加载完成 |
| 2 | 验证初始状态：用户表格由后端 API 填充，显示至少 1 个用户 | EXPECT: 真实后端数据; REJECT: 硬编码假数据 |
| 3 | 点击编辑按钮 → 修改名称 → 保存 | EXPECT: 保存成功提示 |
| 4 | 刷新页面 → 验证数据已持久化 | EXPECT: 显示更新后的名称 |
| 5 | 验证无错误状态 | 无 error |
```

### Rule 3: Cross-Page Workflow

If the feature involves navigation between multiple pages:
- Test the **complete workflow**: page A → action → page B → verify → page C → verify
- Do NOT test pages in isolation — the E2E value comes from the transitions

Example:
```
登录页 → 填写凭据 → 提交 → 仪表盘页 → 验证用户信息 → 点击设置 → 设置页 → 验证表单预填
```

### Rule 4: Three-Layer Detection is Non-Negotiable

Every UI test case MUST include all three detection layers:

| Layer | What to Check | Hard Gate |
|-------|---------------|-----------|
| Layer 1 | 错误状态检测：页面加载/交互后无异常 | 有错误 = FAIL |
| Layer 2 | EXPECT/REJECT 验证：每一步都有明确的预期和拒绝条件 | 缺少 EXPECT = FAIL |
| Layer 3 | 控制台检查：交互后无 console error | 有 error = FAIL |

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
- After each state verification, check that visible elements match UCD style tokens (colors, typography, spacing)
- Reference specific UCD token names in EXPECT clauses: `EXPECT: 主按钮使用 primary-600 色值, 字体为 heading-md`
- This ensures UCD compliance is verified under real rendering conditions

## Self-Audit Checklist

Before finalizing each UI test case, verify:

- [ ] ≥ 5 steps in the test step table
- [ ] Layer 1 (error state) appears at least twice (page load + post-interaction)
- [ ] Layer 2 (EXPECT + REJECT) appears in every verification step
- [ ] Layer 3 (console error) appears at end of test case
- [ ] At least one step verifies real backend data (not mocked)
- [ ] At least one negative/error path test case exists for this feature
- [ ] Preconditions are concrete (specific data, auth state) — not just "系统正常运行"
- [ ] Expected results are specific and assertable — no "显示正确" or "工作正常"
- [ ] UI test case CANNOT be skipped — UI E2E verification is mandatory
