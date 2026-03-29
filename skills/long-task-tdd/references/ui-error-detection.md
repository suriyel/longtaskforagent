# UI Error Detection

## Purpose

Define objective, automatable criteria for identifying UI errors during Chrome DevTools MCP functional testing. This addresses the problem of LLMs reporting "correct" when obvious UI errors are present — by replacing subjective LLM judgment with objective detection rules.

## Three-Layer Detection Model

| Layer | Mechanism | Type | Blocks on |
|-------|-----------|------|-----------|
| **Layer 1** | Automated JS detection script via `evaluate_script()` | Objective, automated | Any detected error (count > 0) |
| **Layer 2** | EXPECT/REJECT format in `[devtools]` verification steps | Semi-objective, structured | Missing EXPECT element or present REJECT condition |
| **Layer 3** | Console error gate via `list_console_messages()` | Objective, automated | Error count > 0 (unless explicitly expected) |

All three layers execute **in sequence** during every UI verification. Any single layer failing means the UI test fails.

## Layer 1: Automated Error Detection Script

Execute this script via `evaluate_script()` **on every page** during UI testing. It returns an `{errors, count}` object. `count > 0` is a **hard FAIL** — no LLM override.

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

### Error Types Reference

| Type | Description | Severity | Common Cause |
|------|-------------|----------|--------------|
| `ZERO_SIZE` | Visible interactive element with 0 width or height | High | CSS issue, missing content, failed render |
| `OFF_VIEWPORT` | Interactive element fully outside visible area | High | Layout overflow, absolute positioning error |
| `BAD_TEXT` | Placeholder or error text visible to user | High | Unresolved template variable, unhandled error |
| `OVERLAP` | Interactive elements overlap > 10% | Medium | CSS positioning conflict, responsive breakpoint issue |
| `EMPTY_CONTAINER` | Layout container with no content | Medium | Missing data, failed component render |
| `BROKEN_IMAGE` | Image that failed to load | Medium | Wrong path, missing asset, CORS issue |

### Integration

Execute in the Worker UI test flow:

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

## Layer 2: EXPECT/REJECT Verification Step Format

### Format

Every `[devtools]` verification step in `feature-list.json` must use this structure:

```
[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>
```

### Components

**EXPECT** — elements, text, or states that **MUST be present**. Verified via `take_snapshot()` output.

**REJECT** — conditions that **MUST NOT be present**. Forces the LLM to actively search for errors instead of only confirming positive expectations.

### Examples

```json
"[devtools] /login | EXPECT: form with email input (type=email), password input (type=password), submit button labeled 'Sign In' | REJECT: any input without label, submit button disabled without validation message, placeholder text 'TODO'"
```

```json
"[devtools] /dashboard | EXPECT: welcome message with user name, navigation sidebar with 5+ menu items, data table with column headers | REJECT: empty data table body, 'undefined' in welcome message, console errors, broken images"
```

```json
"[devtools] /settings | EXPECT: profile form pre-filled with current user data, save button enabled | REJECT: form fields showing 'null' or 'undefined', save button visible but zero-size, overlapping form elements"
```

### Why REJECT is Mandatory

Without REJECT, the LLM's default behavior is:
1. Check EXPECT conditions
2. All found → PASS

This misses errors that are **present but not explicitly looked for**. REJECT forces the LLM to:
1. Check EXPECT conditions
2. **Actively look for** REJECT conditions
3. Only PASS if EXPECT is satisfied AND REJECT is not triggered

### Validation

`validate_features.py` checks:
- Every `[devtools]` step contains both `EXPECT:` and `REJECT:`
- Emits warning (not error) if either clause is missing — to allow gradual adoption

## Layer 3: Console Error Gate

### Rule

After completing UI interactions on a page:

```
list_console_messages(types=["error"]) → count must be 0
```

**If count > 0**: UI test **automatically FAIL**. The LLM must not rationalize console errors as acceptable.

### Exception Mechanism

When a verification step explicitly expects console errors (e.g., testing error boundary behavior):

```
"[devtools] /error-test | EXPECT: error boundary fallback UI displayed | REJECT: blank page | [expect-console-error: TypeError]"
```

The `[expect-console-error: <pattern>]` suffix allows specific error patterns. Only errors matching the pattern are exempt; other errors still trigger FAIL.

### Implementation

```
1. list_console_messages(types=["error"]) → collect errors
2. If verification_step contains [expect-console-error: <pattern>]:
   - Filter out errors matching <pattern>
   - Remaining errors > 0 → FAIL
3. Else:
   - Any errors > 0 → FAIL
```

## Layer 1b: Positive Rendering Verification Script

Layer 1 (error detection) catches **broken** rendering. Layer 1b catches **missing** rendering — visual elements that should exist but don't. A blank canvas with zero errors passes Layer 1 but MUST FAIL Layer 1b.

### Script

Execute via `evaluate_script()` with parameters from the Feature Design Visual Rendering Contract:

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

### Arguments

| Parameter | Source | Description |
|-----------|--------|-------------|
| `selectors` | Visual Rendering Contract "DOM/Canvas Selector" column (DOM elements) | Array of CSS selectors, e.g. `["div.snake-segment", "#score-display", "button#start"]` |
| `canvasIds` | Visual Rendering Contract "DOM/Canvas Selector" column (canvas elements) | Array of canvas element IDs, e.g. `["game-board", "minimap"]` |

### Verdict

- `missingCount === 0` → **PASS** — all expected visual elements are rendered
- `missingCount > 0` (after 3 retries) → **HARD FAIL** — expected visual content is not rendered

### Integration with Three-Layer Detection

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

Layer 1 answers: "Is anything broken?" Layer 1b answers: "Is everything there?" Both must pass.

## Relationship to Other Documents

| Document | Relationship |
|----------|-------------|
| [test-scenario-rules.md](test-scenario-rules.md) | Rule 5 references this document for UI-specific rules |
| [architecture.md](../../using-long-task/references/architecture.md) | Chrome DevTools MCP test pattern references this document |
| [testing-anti-patterns.md](../testing-anti-patterns.md) | "Skipping Chrome DevTools functional tests" anti-pattern references EXPECT/REJECT |
