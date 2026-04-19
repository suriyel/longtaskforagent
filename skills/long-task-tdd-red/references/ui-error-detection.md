# UI 错误检测（UI Error Detection）

## 目的

为 Chrome DevTools MCP 功能测试期间的 UI 错误识别定义客观、可自动化的准则。这解决了 LLM 在明显 UI 错误存在时仍报告"正确"的问题 — 用客观检测规则替代主观的 LLM 判断。

## 三层检测模型

| Layer | Mechanism | Type | Blocks on |
|-------|-----------|------|-----------|
| **Layer 1** | 通过 `evaluate_script()` 运行自动化 JS 检测脚本 | 客观、自动化 | 任意检测到的错误（count > 0） |
| **Layer 2** | `[devtools]` 验证步骤中的 EXPECT/REJECT 格式 | 半客观、结构化 | 缺失 EXPECT 元素或存在 REJECT 条件 |
| **Layer 3** | 通过 `list_console_messages()` 的 console error 关卡 | 客观、自动化 | error 数 > 0（除非显式预期） |

三层在每次 UI 校验中**依次**执行。任一层失败即 UI 测试失败。

## Layer 1：自动化错误检测脚本

在 UI 测试期间**每个页面**都经 `evaluate_script()` 执行此脚本。返回 `{errors, count}` 对象。`count > 0` 即**硬 FAIL** — 不容 LLM 覆盖。

```javascript
() => {
  const errors = [];

  // 1. Zero-size visible interactive elements
  document.querySelectorAll('button,input,select,textarea,a,img,[role="button"]').forEach(el => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    if (style.display !== 'none' && style.visibility !== 'hidden'
        && style.opacity !== '0' && el.offsetParent !== null
        && (rect.width === 0 || rect.height === 0)) {
      errors.push({
        type: 'ZERO_SIZE',
        element: el.tagName.toLowerCase(),
        id: el.id || null,
        text: el.textContent?.slice(0, 30) || null
      });
    }
  });

  // 2. Interactive elements outside viewport
  document.querySelectorAll('button,input,a,[role="button"],select,textarea').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (el.offsetParent !== null && rect.width > 0 && rect.height > 0
        && (rect.right < 0 || rect.bottom < 0
            || rect.left > window.innerWidth || rect.top > window.innerHeight)) {
      errors.push({
        type: 'OFF_VIEWPORT',
        element: el.tagName.toLowerCase(),
        id: el.id || null,
        text: el.textContent?.slice(0, 30) || null,
        position: { left: rect.left, top: rect.top }
      });
    }
  });

  // 3. Placeholder/error text in page content
  const bodyText = document.body.innerText;
  const badPatterns = [
    { pattern: /\bundefined\b/gi, type: 'undefined' },
    { pattern: /\[object Object\]/g, type: '[object Object]' },
    { pattern: /\bNaN\b/g, type: 'NaN' },
    { pattern: /\bnull\b/gi, type: 'null' },
    { pattern: /\bTODO\b/g, type: 'TODO' },
    { pattern: /\bFIXME\b/g, type: 'FIXME' },
    { pattern: /lorem ipsum/gi, type: 'lorem ipsum' }
  ];
  for (const { pattern, type } of badPatterns) {
    const matches = bodyText.match(pattern);
    if (matches) {
      errors.push({
        type: 'BAD_TEXT',
        text: type,
        occurrences: matches.length
      });
    }
  }

  // 4. Interactive element overlap detection
  const interactiveEls = [...document.querySelectorAll(
    'button,a,input,[role="button"],select,textarea'
  )].filter(el => el.offsetParent !== null);
  for (let i = 0; i < interactiveEls.length; i++) {
    const a = interactiveEls[i].getBoundingClientRect();
    if (a.width === 0 || a.height === 0) continue;
    for (let j = i + 1; j < interactiveEls.length; j++) {
      const b = interactiveEls[j].getBoundingClientRect();
      if (b.width === 0 || b.height === 0) continue;
      const overlap = !(a.right <= b.left || a.left >= b.right
                     || a.bottom <= b.top || a.top >= b.bottom);
      if (overlap) {
        // Calculate overlap area to filter trivial 1px overlaps
        const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        const overlapArea = overlapWidth * overlapHeight;
        const smallerArea = Math.min(a.width * a.height, b.width * b.height);
        if (overlapArea > smallerArea * 0.1) { // >10% overlap
          errors.push({
            type: 'OVERLAP',
            el1: { tag: interactiveEls[i].tagName.toLowerCase(), text: interactiveEls[i].textContent?.slice(0, 20) },
            el2: { tag: interactiveEls[j].tagName.toLowerCase(), text: interactiveEls[j].textContent?.slice(0, 20) },
            overlapPercent: Math.round(overlapArea / smallerArea * 100)
          });
        }
      }
    }
  }

  // 5. Empty containers with layout roles
  document.querySelectorAll(
    'main,[role="main"],section,article,.container,.content,[role="region"],[role="contentinfo"]'
  ).forEach(el => {
    if (el.children.length === 0 && el.textContent.trim() === ''
        && getComputedStyle(el).display !== 'none') {
      errors.push({
        type: 'EMPTY_CONTAINER',
        element: el.tagName.toLowerCase(),
        id: el.id || null,
        className: el.className || null
      });
    }
  });

  // 6. Broken images
  document.querySelectorAll('img').forEach(img => {
    if (img.offsetParent !== null && (!img.complete || img.naturalWidth === 0)) {
      errors.push({
        type: 'BROKEN_IMAGE',
        src: img.src?.slice(0, 100),
        alt: img.alt || null
      });
    }
  });

  return { errors, count: errors.length };
}
```

### 错误类型速查

| Type | Description | Severity | Common Cause |
|------|-------------|----------|--------------|
| `ZERO_SIZE` | 可见的交互元素宽或高为 0 | High | CSS 问题、内容缺失、渲染失败 |
| `OFF_VIEWPORT` | 交互元素完全在可视区域之外 | High | 布局溢出、绝对定位错误 |
| `BAD_TEXT` | 占位符或错误文本对用户可见 | High | 未解析的模板变量、未处理的错误 |
| `OVERLAP` | 交互元素重叠 > 10% | Medium | CSS 定位冲突、响应式断点问题 |
| `EMPTY_CONTAINER` | 布局容器无内容 | Medium | 数据缺失、组件渲染失败 |
| `BROKEN_IMAGE` | 图片加载失败 | Medium | 路径错误、资源缺失、CORS 问题 |

### 集成

在 Worker 的 UI 测试流程中执行：

```
1. navigate_page(url)
2. wait_for(expected_text)             ← wait for page load
3. evaluate_script(error_detector)     ← Layer 1 — HARD FAIL if count > 0
4. take_snapshot()                     ← For EXPECT/REJECT verification
5. [interactions: click, fill, etc.]
6. evaluate_script(error_detector)     ← Layer 1 again after interactions
7. list_console_messages(["error"])    ← Layer 3 — HARD FAIL if count > 0
8. Verify EXPECT/REJECT criteria      ← Layer 2
```

## Layer 2：EXPECT/REJECT 验证步骤格式

### 格式

`feature-list.json` 中的每个 `[devtools]` 验证步骤都必须使用如下结构：

```
[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>
```

### 组成

**EXPECT** — **必须存在**的元素、文本或状态。通过 `take_snapshot()` 输出校验。

**REJECT** — **必须不存在**的条件。迫使 LLM 主动搜索错误，而不是只确认正向期望。

### 示例

```json
"[devtools] /login | EXPECT: form with email input (type=email), password input (type=password), submit button labeled 'Sign In' | REJECT: any input without label, submit button disabled without validation message, placeholder text 'TODO'"
```

```json
"[devtools] /dashboard | EXPECT: welcome message with user name, navigation sidebar with 5+ menu items, data table with column headers | REJECT: empty data table body, 'undefined' in welcome message, console errors, broken images"
```

```json
"[devtools] /settings | EXPECT: profile form pre-filled with current user data, save button enabled | REJECT: form fields showing 'null' or 'undefined', save button visible but zero-size, overlapping form elements"
```

### 为何 REJECT 是强制的

若无 REJECT，LLM 的默认行为是：
1. 检查 EXPECT 条件
2. 全部找到 → PASS

这会漏掉**存在但未显式去找**的错误。REJECT 强制 LLM：
1. 检查 EXPECT 条件
2. **主动寻找** REJECT 条件
3. 仅当 EXPECT 满足且 REJECT 未触发时才 PASS

### 校验

`validate_features.py` 检查：
- 每个 `[devtools]` 步骤同时包含 `EXPECT:` 与 `REJECT:`
- 若缺一则发 warning（非 error） — 允许渐进采用

## Layer 3：Console Error 关卡

### 规则

完成页面 UI 交互后：

```
list_console_messages(types=["error"]) → count must be 0
```

**若 count > 0**：UI 测试**自动 FAIL**。LLM 不得将 console error 合理化为可接受。

### 例外机制

当某验证步骤显式预期会有 console error（例如测试 error boundary 行为）：

```
"[devtools] /error-test | EXPECT: error boundary fallback UI displayed | REJECT: blank page | [expect-console-error: TypeError]"
```

`[expect-console-error: <pattern>]` 后缀允许特定错误模式。仅匹配该模式的错误被豁免；其他错误仍触发 FAIL。

### 实现

```
1. list_console_messages(types=["error"]) → collect errors
2. If verification_step contains [expect-console-error: <pattern>]:
   - Filter out errors matching <pattern>
   - Remaining errors > 0 → FAIL
3. Else:
   - Any errors > 0 → FAIL
```

## Layer 1b：正向渲染校验脚本

Layer 1（错误检测）抓的是**已损坏**的渲染。Layer 1b 抓的是**缺失**的渲染 — 本应存在但不存在的视觉元素。一个零错误的空白画布能通过 Layer 1 但**必定**未通过 Layer 1b。

### 脚本

通过 `evaluate_script()` 执行，参数来自 Feature Design 的 Visual Rendering Contract：

```javascript
async (selectors, canvasIds) => {
  const results = { missing: [], present: [], canvasEmpty: [], missingCount: 0 };

  // --- Retry wrapper for async rendering (requestAnimationFrame) ---
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 500;

  async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    results.missing = [];
    results.present = [];
    results.canvasEmpty = [];

    // 1. Check DOM elements exist and are visible
    for (const sel of (selectors || [])) {
      const el = document.querySelector(sel);
      if (!el) {
        results.missing.push({ type: 'DOM_MISSING', selector: sel });
        continue;
      }
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden'
          || style.opacity === '0' || rect.width === 0 || rect.height === 0) {
        results.missing.push({ type: 'DOM_INVISIBLE', selector: sel,
          width: rect.width, height: rect.height, display: style.display });
      } else {
        results.present.push({ selector: sel, width: rect.width, height: rect.height });
      }
    }

    // 2. Check canvas elements have drawn content
    for (const id of (canvasIds || [])) {
      const canvas = document.getElementById(id);
      if (!canvas || !canvas.getContext) {
        results.canvasEmpty.push({ type: 'CANVAS_MISSING', id });
        continue;
      }

      let hasContent = false;

      // Auto-detect context type.
      // IMPORTANT: This script must run AFTER the application has rendered at least
      // one frame (i.e., after the rendering trigger fires). Calling getContext('2d')
      // on a canvas that hasn't yet acquired a context would lock it to 2D permanently.
      // The retry mechanism (MAX_RETRIES with RETRY_DELAY_MS) handles this by waiting
      // for the application to initialize before checking.
      const ctx2d = canvas.getContext('2d');
      if (ctx2d) {
        // Canvas 2D path
        const imageData = ctx2d.getImageData(0, 0, canvas.width, canvas.height);
        hasContent = imageData.data.some((v, i) => i % 4 === 3 && v > 0); // any non-transparent pixel
      } else {
        // WebGL path (context already acquired as WebGL)
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        if (gl) {
          const pixels = new Uint8Array(canvas.width * canvas.height * 4);
          gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
          hasContent = pixels.some((v, i) => i % 4 === 3 && v > 0); // any non-transparent pixel
        }
      }

      if (!hasContent) {
        results.canvasEmpty.push({ type: 'CANVAS_BLANK', id,
          width: canvas.width, height: canvas.height });
      } else {
        results.present.push({ canvasId: id, width: canvas.width, height: canvas.height });
      }
    }

    results.missingCount = results.missing.length + results.canvasEmpty.length;

    // If all elements found, no need to retry
    if (results.missingCount === 0) break;

    // Wait before retry (except on last attempt)
    if (attempt < MAX_RETRIES) await sleep(RETRY_DELAY_MS);
  }

  return results;
}
```

### 参数

| Parameter | Source | Description |
|-----------|--------|-------------|
| `selectors` | Visual Rendering Contract 中 "DOM/Canvas Selector" 列（DOM 元素） | CSS 选择器数组，例如 `["div.snake-segment", "#score-display", "button#start"]` |
| `canvasIds` | Visual Rendering Contract 中 "DOM/Canvas Selector" 列（canvas 元素） | canvas 元素 ID 数组，例如 `["game-board", "minimap"]` |

### 判定

- `missingCount === 0` → **PASS** — 所有预期视觉元素已渲染
- `missingCount > 0`（3 次重试之后） → **硬 FAIL** — 预期视觉内容未渲染

### 与三层检测的集成

```
1. navigate_page(url)
2. wait_for(expected_text)                      ← wait for page load
3. evaluate_script(error_detector)              ← Layer 1 — errors in existing UI
4. evaluate_script(positive_render_checker,     ← Layer 1b — expected UI is present
     [selectors], [canvasIds])
5. take_snapshot()                              ← Layer 2 — EXPECT/REJECT
6. [interactions: click, fill, etc.]
7. evaluate_script(error_detector)              ← Layer 1 again after interactions
8. evaluate_script(positive_render_checker, ...) ← Layer 1b again after state changes
9. list_console_messages(["error"])             ← Layer 3
10. Verify EXPECT/REJECT criteria              ← Layer 2
```

Layer 1 回答："有任何东西坏了吗？" Layer 1b 回答："每样东西都到位了吗？" 二者必须都通过。

## 与其他文档的关系

| Document | Relationship |
|----------|-------------|
| [test-scenario-rules.md](test-scenario-rules.md) | Rule 5 引用本文件中的 UI 专用规则 |
| [architecture.md](../../using-long-task/references/architecture.md) | Chrome DevTools MCP test pattern 引用本文件 |
| [testing-anti-patterns.md](../testing-anti-patterns.md) | "跳过 Chrome DevTools 功能测试"反模式引用 EXPECT/REJECT |
