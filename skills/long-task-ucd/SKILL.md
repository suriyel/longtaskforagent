---
name: long-task-ucd
description: "Use when SRS doc exists but no UCD doc and no design doc and no feature-list.json - generate UI Component Design style guide with text-to-image prompts based on approved SRS"
---

# UI Component Design (UCD) 样式指南生成

以已审批 SRS 为输入。分析 UI 相关需求，定义视觉风格方向，并产出一份包含 text-to-image 模型提示词的 UCD 样式指南——从而让所有前端特性共享统一的视觉语言。

<HARD-GATE>
在你呈现 UCD 样式指南并且用户审批通过之前，禁止调用任何设计 skill、实现 skill、写任何代码、脚手架任何项目，或执行任何实现动作。这适用于**每一个**带 UI 特性的项目。
</HARD-GATE>

## 本阶段何时适用

本阶段在 **SRS 审批之后**、**设计之前**运行。适用条件：
- 已审批的 SRS 含 UI 相关功能需求（FR-xxx 含面向用户的屏幕、页面或组件）
- `docs/plans/` 下不存在 UCD 文档（`*-ucd.md`）

**如果 SRS 无 UI 特性**：宣告 "No UI features detected in SRS — skipping UCD phase"，随即通过 `long-task:long-task-design` 衔接到设计。

## Checklist

你必须为下列每一项创建一个 TodoWrite 任务并按顺序完成：

1. **阅读已审批 SRS** —— 来自 `docs/plans/*-srs.md`
2. **抽取 UI 范围** —— 识别所有 UI 相关需求与用户角色
3. **定义视觉风格方向** —— 提出 2-3 个风格选项与 mood board
4. **生成组件级提示词** —— 每种 UI 组件类型的 text-to-image 提示词
5. **生成页面级提示词** —— 每个关键页面/屏幕的 text-to-image 提示词
6. **定义样式 token** —— 色板、字体、间距、图标风格
7. **呈现并审批 UCD** —— 非平凡项目按章节逐段
8. **保存 UCD 文档** —— `docs/plans/YYYY-MM-DD-<topic>-ucd.md` 并提交
9. **衔接到设计** —— **必需子 skill：** 调用 `long-task:long-task-design`

**终态是调用 long-task-design。** 不要调用任何其他 skill。

## Step 1：阅读 SRS 与抽取 UI 范围

1. 读取 `docs/plans/*-srs.md` 中已审批的 SRS 文档
2. 抽取 UI 相关输入：
   - **用户角色** —— 技术水平、无障碍需求、设备偏好
   - **带 UI 的功能需求** —— 屏幕、页面、表单、仪表盘、数据可视化
   - **NFR 易用性需求** —— 无障碍标准（WCAG 等级）、响应式断点、国际化
   - **约束** —— 品牌指南、平台限制、浏览器支持
   - **接口需求** —— 外部 UI 组件、要集成的设计系统
3. 构建 **UI 清单** —— 列出 SRS 隐含的每一种不同屏幕/页面/组件类型
4. 如果 SRS 缺乏足够 UI 细节 → 在继续之前通过 `AskUserQuestion` 询问用户

## Step 2：定义视觉风格方向

向用户呈现 **2-3 个视觉风格选项**：

```markdown
## Style A: [Name] (e.g., "Clean Corporate", "Bold Modern", "Soft Minimal")
**Mood**: [1-2 sentences describing the visual feel]
**Color direction**: [primary palette tendency — warm/cool/neutral, high/low contrast]
**Typography direction**: [serif/sans-serif, geometric/humanist, density]
**Layout direction**: [card-based/list-based, dense/spacious, fixed/fluid]
**Target persona fit**: [which SRS user personas this serves best]
**Reference style**: [existing design language this draws from — Material, Ant, Apple HIG, etc.]

## Style B: [Name]
...

## Recommendation: Style [X]
**Reason**: [why this fits the SRS personas, constraints, and NFRs best]
```

等用户选择或给出方向。在继续前纳入反馈。

## Step 3：生成样式 Token

定义锚定整套风格系统的具体设计 token：

### 3.1 色板

```markdown
| Token | Hex | Usage | Contrast Ratio |
|-------|-----|-------|----------------|
| --color-primary | #XXXXXX | Primary actions, links, active states | >= 4.5:1 on white |
| --color-primary-hover | #XXXXXX | Hover state for primary | |
| --color-secondary | #XXXXXX | Secondary actions, accents | >= 4.5:1 on white |
| --color-bg-primary | #XXXXXX | Main background | |
| --color-bg-secondary | #XXXXXX | Card/section background | |
| --color-text-primary | #XXXXXX | Body text | >= 4.5:1 on bg-primary |
| --color-text-secondary | #XXXXXX | Captions, hints | >= 3:1 on bg-primary |
| --color-success | #XXXXXX | Success states | |
| --color-warning | #XXXXXX | Warning states | |
| --color-error | #XXXXXX | Error states, destructive actions | |
| --color-border | #XXXXXX | Default borders | |
```

- 所有对比度**必须**至少满足 WCAG AA（普通文本 4.5:1，大文本 3:1）
- 若 SRS 指定 WCAG AAA，则比例须为 7:1 / 4.5:1

### 3.2 字体级阶

```markdown
| Token | Font Family | Size | Weight | Line Height | Usage |
|-------|-------------|------|--------|-------------|-------|
| --font-heading-1 | [family] | [size] | [weight] | [lh] | Page titles |
| --font-heading-2 | [family] | [size] | [weight] | [lh] | Section headings |
| --font-heading-3 | [family] | [size] | [weight] | [lh] | Card titles |
| --font-body | [family] | [size] | [weight] | [lh] | Body text |
| --font-body-small | [family] | [size] | [weight] | [lh] | Captions, hints |
| --font-label | [family] | [size] | [weight] | [lh] | Form labels, buttons |
| --font-code | [family] | [size] | [weight] | [lh] | Code snippets |
```

### 3.3 间距与布局

```markdown
| Token | Value | Usage |
|-------|-------|-------|
| --space-xs | [value] | Tight inner padding |
| --space-sm | [value] | Default inner padding |
| --space-md | [value] | Section gaps |
| --space-lg | [value] | Page section margins |
| --space-xl | [value] | Major layout breaks |
| --radius-sm | [value] | Buttons, inputs |
| --radius-md | [value] | Cards |
| --radius-lg | [value] | Modals, dialogs |
| --shadow-sm | [value] | Subtle elevation |
| --shadow-md | [value] | Cards, dropdowns |
| --shadow-lg | [value] | Modals, overlays |
```

### 3.4 图标与图片

```markdown
- **Icon style**: [outlined/filled/duotone] [rounded/sharp] [stroke weight]
- **Icon library**: [recommended library with version, e.g., Lucide Icons 0.263.0]
- **Illustration style**: [flat/isometric/3D/hand-drawn] [color treatment]
- **Photography treatment**: [if applicable — filters, overlays, cropping rules]
```

## Step 4：生成组件级提示词

对清单中每种 UI 组件类型，产出生成式图像模型（Midjourney、DALL-E、Stable Diffusion 等）可用于可视化该组件的 **text-to-image 提示词**。

### 提示词结构

每个组件提示词遵循此模板：

```markdown
### Component: [Component Name]
**SRS Trace**: [FR-xxx, NFR-xxx]
**Variants**: [list variants — default, hover, active, disabled, error, loading]

#### Base Prompt
> [Detailed text-to-image prompt describing the component's visual appearance in the approved style. Include: layout structure, color tokens by name, typography tokens, spacing, border treatment, shadow, state indicators. Be specific about proportions, alignment, and visual hierarchy.]

#### Variant Prompts
> **Hover state**: [prompt delta from base]
> **Error state**: [prompt delta from base]
> **Loading state**: [prompt delta from base]
> **Dark mode** (if applicable): [prompt delta from base]

#### Style Constraints
- [Constraint 1 — e.g., "Button height must be exactly 40px for touch targets"]
- [Constraint 2 — e.g., "Error text must appear below the input, never as tooltip"]
```

### 必需的组件类型

至少为下列组件类型生成提示词（仅当 UI 清单中确实不含时才跳过）：

| 类别 | 组件 |
|----------|-----------|
| **导航** | Header/navbar、sidebar、breadcrumb、tabs、pagination |
| **输入** | Text input、textarea、select/dropdown、checkbox、radio、toggle、date picker |
| **动作** | Primary button、secondary button、icon button、link button、FAB |
| **反馈** | Alert/toast、modal/dialog、progress bar、skeleton loader、empty state |
| **数据展示** | Table、card、list item、badge/tag、avatar、tooltip |
| **布局** | Page shell、form layout、grid/masonry、divider |

## Step 5：生成页面级提示词

对 UI 清单中识别的每个关键页面/屏幕，产出 **整页 text-to-image 提示词**。

### 页面提示词结构

```markdown
### Page: [Page Name]
**SRS Trace**: [FR-xxx]
**User Persona**: [primary persona for this page]
**Entry Points**: [how users arrive at this page]

#### Layout Description
[Describe the page layout: header placement, content zones, sidebar (if any), footer. Specify grid structure, responsive behavior at key breakpoints.]

#### Full-Page Prompt
> [Detailed text-to-image prompt for the complete page. Reference component names defined in Step 4. Describe spatial relationships, visual hierarchy, content flow, key interactions. Include responsive notes for mobile/tablet if applicable.]

#### Key Interactions
- [Interaction 1 — e.g., "Clicking row in table opens detail panel on right"]
- [Interaction 2 — e.g., "Form validates on blur, shows inline errors"]

#### Responsive Behavior
- **Desktop (>= 1024px)**: [layout description]
- **Tablet (768-1023px)**: [layout changes]
- **Mobile (< 768px)**: [layout changes]
```

## Step 6：呈现并审批 UCD

非平凡项目按章节逐段呈现：

1. **视觉风格方向** —— mood、色彩倾向、字体方向
2. **样式 token** —— 色板、字体级阶、间距、图标
3. **组件提示词** —— 先取一两个代表性组件审批，再生成其余
4. **页面提示词** —— 关键页面审批

呈现每一节。等待用户反馈。在进入下一节前纳入更改。

**对简单项目**（< 3 个 UI 页面）：将所有章节合并为单一审批步骤。

## Step 7：保存 UCD 文档

把已审批的 UCD 样式指南保存到 `docs/plans/YYYY-MM-DD-<topic>-ucd.md`。

文档结构：

```markdown
# <Project Name> — UCD Style Guide

**Date**: YYYY-MM-DD
**Status**: Approved
**SRS Reference**: docs/plans/YYYY-MM-DD-<topic>-srs.md

## 1. Visual Style Direction
[Chosen style, rationale]

## 2. Style Tokens
### 2.1 Color Palette
### 2.2 Typography Scale
### 2.3 Spacing & Layout
### 2.4 Iconography & Imagery

## 3. Component Prompts
### 3.1 [Component Name]
...

## 4. Page Prompts
### 4.1 [Page Name]
...

## 5. Style Rules & Constraints
[Cross-cutting rules: accessibility, animation, responsive, dark mode]
```

## Step 8：衔接到设计

UCD 文档保存并提交后：

1. 为设计阶段总结关键输入：
   - **来自 SRS**：功能需求、NFR、约束
   - **来自 UCD**：样式 token、组件目录、页面布局 → 为设计文档的 UI/UX 节和前端架构提供信息
2. **必需子 skill：** 调用 `long-task:long-task-design` 开始设计

## UCD 阶段的伸缩

| 项目规模 | UI 页面数 | 深度 |
|---|---|---|
| 微型 | 1-3 | 样式 token + 3-5 个核心组件提示词 + 页面提示词；单一审批步骤 |
| 小型 | 3-8 | 完整样式 token + 使用到的组件提示词 + 全部页面提示词 |
| 中型 | 8-20 | 带全部组件变体与响应式页面提示词的完整 UCD |
| 大型 | 20+ | 完整 UCD + 交互态矩阵 + 动效规范 + 暗黑模式变体 |

## 红旗信号

| 理性化逃避 | 正确响应 |
|---|---|
| "UI 很简单，跳过 UCD" | 即便简单 UI 也需要一致的风格——运行轻量级 UCD |
| "我在实现期间再定义样式" | 临时造型会导致跨特性视觉不一致 |
| "用户会挑一个 UI 库，够了" | UI 库需要配置—— UCD 提供这些值 |
| "样式 token 过早" | Token 现在定义比事后跨 20 个组件改造更便宜 |
| "我就直接用 Material/Ant 默认风格" | 默认值是合法起点，但必须作为显式选择记录下来 |
| "SRS 没提到颜色" | SRS 定义 WHAT；UCD 定义视觉 HOW；UI 项目两者都需要 |

## 提示词书写规则

1. **具体而非模糊** —— "a rounded-corner card with 8px radius, 1px solid #E5E7EB border, 16px padding, white background with 0 2px 4px rgba(0,0,0,0.05) shadow" 胜过 "a nice card"
2. **引用 token 而非原始值** —— 在提示词中使用 token 名以便设计变更传播："using --color-primary for the button fill"
3. **包含空间关系** —— "the icon is 16px, positioned 8px left of the label text, vertically centered"
4. **描述状态，不只是默认** —— 每个可交互元素都需要 hover、active、disabled、error 状态
5. **指定响应式意图** —— 组件/页面在每个断点如何适配
6. **锚定到 SRS 角色** —— 提示词应服务定义的用户类型（例如面向移动优先用户的更大触控目标）
