---
name: long-task-hotfix
description: "Use when bugfix-request.json exists - validate, reproduce, root-cause, and enqueue a user-reported bug as a category=bugfix feature, then chain to Worker for TDD fix"
---

<EXTREMELY-IMPORTANT>
你正在使用 long-task-hotfix skill。本 skill 处理用户手工测试中发现的缺陷。

你的职责**仅限**：校验 → 复现 → 根因 → 入队 → 交给 Worker。
实际修复（TDD、质量关卡、ST、评审）由 Worker 流水线处理 —— **不要**在此处实施修复。
</EXTREMELY-IMPORTANT>

## Step 1: 声明

打印："I'm using the long-task-hotfix skill. Processing bugfix-request.json."

使用 TodoWrite 跟踪 8 步进度。

---

## Step 2: 校验信号文件

运行：
```bash
python scripts/validate_bugfix_request.py bugfix-request.json
```

若校验失败：
- 清晰打印错误
- 使用 `AskUserQuestion` 请求用户修正文件
- 用户响应后重新校验
- 校验不通过**不得**继续

---

## Step 3: Orient（调取上下文）

按顺序阅读以下文件：
1. `bugfix-request.json` —— 理解 title、description、severity、feature_id、复现步骤
2. `feature-list.json` —— 找到关联的特性（若 `feature_id` 非空），读取 `tech_stack`、`quality_gates`；确定下一个可用的特性 `id`
3. `long-task-guide.md` —— 环境激活命令
4. `env-guide.md`（若存在）—— 服务启动/停止命令
5. `task-progress.md` 的 `## Current State` 章节 —— 近期会话历史
6. `git log --oneline -10` —— 近期提交上下文

若 `feature_id` 非空：从 `feature-list.json` 读取关联特性的条目以理解上下文（其 `ui` 字段、现有 `srs_trace`、`st_case_path`）。

---

## Step 4: 复现

**目标**：在任何分析之前确认缺陷可复现。

1. 按 `long-task-guide.md` 激活环境
2. 若需要服务（从 `env-guide.md` 或 `long-task-guide.md` 判定）：使用 `env-guide.md` Start 命令启动；捕获启动输出的前 30 行；在 `task-progress.md` 中记录 PID
3. **严格**依照 `bugfix-request.json` 中的 `reproduction_steps`
4. 运行既有测试套件；记录当前失败的测试
5. 记录：所运行的确切命令、所观察的确切输出、缺陷重现的确认

**硬关卡 —— 无法复现：**
若缺陷无法复现：
- 在 `task-progress.md` 中记录本次尝试
- 停止本步骤启动的所有服务（使用 `env-guide.md` Stop 命令）
- **不要**删除 `bugfix-request.json`
- 使用 `AskUserQuestion` 请求澄清（更详细的步骤、具体环境、样例数据）
- **此处停止，直到复现确认为止**

---

## Step 5: 根因分析

执行 `skills/using-long-task/references/systematic-debugging.md` 的 **4 阶段系统性调试流程**：

**Phase 1 —— 根因调查**：收集完整错误证据，找到最小复现，检查近期 git 变更，从入口点追踪数据流到失败点。

**Phase 2 —— 模式分析**：找到类似的可工作代码路径，比对上下文，检查依赖版本与配置值。

**Phase 3 —— 假设与验证**：提出 **一条** 具体可验证的假设；做 **一处** 最小诊断性修改以印证或证伪；若错则回到 Phase 1。

**Phase 4 —— 确认根因**：形成单一的根因确认陈述。

**必需输出**：`"Root cause: [one-sentence statement]"`

**铁律**：根因确认前**不得**入队。若 3 轮 Phase 3 迭代后仍无法确认根因，用 `AskUserQuestion` 请求更多上下文。

---

## Step 6: 作为 bugfix 特性入队

在 `feature-list.json` 中新增一条 feature。确定下一个可用 `id`（现有最大 id + 1）。

**新特性对象：**
```json
{
  "id": <next available>,
  "wave": <current max wave id>,
  "category": "bugfix",
  "title": "Fix: <title from bugfix-request.json>",
  "description": "<actual_behavior from bugfix-request.json> — Root cause: <confirmed root cause>",
  "priority": "<Critical|Major → 'high', Minor → 'medium', Cosmetic → 'low'>",
  "status": "failing",
  "sub_status": "design_pending",
  "srs_trace": ["<FR-xxx from linked feature, or new FR-xxx if unlinked>"],
  "dependencies": [<fixed_feature_id>],
  "ui": <copy from linked feature's ui field, or false if feature_id is null>,
  "deprecated": false,
  "deprecated_reason": null,
  "supersedes": null,
  "bug_severity": "<severity from bugfix-request.json>",
  "bug_source": "manual-testing",
  "fixed_feature_id": <feature_id from bugfix-request.json, or null>,
  "root_cause": "<confirmed root cause one-sentence>"
}
```

**说明：**
- `dependencies`：非空则置为 `[fixed_feature_id]`（确保 Worker 先处理原特性再做此修复）；为空则置 `[]`
- `ui`：若 `feature_id` 非空，使用关联特性的 `ui` 字段；否则 `false`
- `wave`：使用 `feature-list.json` `waves` 数组中当前最大的 wave id
- `sub_status`：始终置为 `"design_pending"` —— 即使是 bugfix，`long-task-work-design` 也会产出精简的特性详细设计（根因记录 + 定向修复方式 + 回归测试清单），再进入 TDD
- **ATS 提示**：若 `fixed_feature_id` 非空且 ATS 文档存在（`docs/plans/*-ats.md`），在 ATS 映射表中查找关联特性的需求。将 `srs_trace` 设为包含关联特性的需求 ID，以便下游 feature-st 能从 SRS 验收标准推导所需测试用例

新增后校验：
```bash
python scripts/validate_features.py feature-list.json
```

继续之前修复任何校验错误。

---

## Step 7: 更新 task-progress.md

在当前 `## Current State` 内容之后追加一条 hotfix 会话记录：

```markdown
## Hotfix Session — YYYY-MM-DD: <bug title>
- **Severity**: <severity>
- **Bugfix Feature ID**: #<new id>
- **Fixed Feature**: #<fixed_feature_id> <feature title> (or "Unlinked")
- **Root Cause**: <one sentence>
- **Status**: Enqueued — Worker will handle TDD/Quality/ST/Review
```

同时更新 `## Current State` 头部以反映新的 failing 特性。

---

## Step 8: 收尾

1. 使用 `env-guide.md` Stop 命令停止 Step 4 启动的所有服务；确认已停止
2. 删除 `bugfix-request.json`（这是最终不可逆动作 —— 仅在 Steps 6 和 7 完成且 `validate_features.py` 通过后执行）
3. 打印：
   ```
   Bug #<id> enqueued as category=bugfix feature.
   Title: Fix: <title>
   Severity: <severity>
   Root cause: <one sentence>
   Worker will handle: TDD → Quality → ST → Review
   ```
4. 移交：开新会话；`using-long-task` 会按 `sub_status` 路由到 `long-task-work-tdd`（新入队的 bugfix 特性由 `long-task-init-features` / `validate_features.py` 设为 `sub_status=tdd_pending`，直接进入 TDD 修复循环）

---

## 关键规则

- **任何动作之前先校验信号文件** —— Step 3 之前校验器必须通过
- **分析之前必须复现** —— "Cannot Reproduce" 是有效的已文档化结果；**不要**对未复现的缺陷跳到根因
- **入队之前确认根因** —— 系统性调试 4 阶段流程是强制的；严禁"猜完就入队"
- **信号文件**最后**删除** —— 删除是最终不可逆动作；`validate_features.py` 必须先通过
- **若 `bugfix-request.json` 与 `increment-request.json` 同时存在**：先完整处理本 hotfix；**不要**删除 `increment-request.json`，它会在下一次会话处理
- **交接给 Worker 之前停止所有服务** —— 复现过程中启动的服务必须停止；Worker 管理自己的服务生命周期
- **本 skill 不实施修复** —— Worker 拥有 TDD/Quality/ST/Review 的职责；本 skill 仅校验、诊断并入队
- **此处禁止任何临时代码修改** —— 本 skill 内不得写测试或改代码；那是 Worker 的工作

## 红旗

以下念头意味着**立即停止** —— 你在合理化：

| 想法 | 真相 |
|---------|---------|
| "我在代码里一眼就看到了 bug，直接改掉吧" | 先做 4 阶段根因分析；然后入队；由 Worker 修复 |
| "我知道根因了，跳过 Phase 1-3" | 4 阶段全部强制；记录它们能防止错误假设 |
| "复现不了但我知道原因" | Cannot Reproduce = 停止；在 task-progress.md 记录；问用户 |
| "跳过 feature-list.json 条目，直接修掉" | 每个修复都必须在 feature-list.json 中以 category=bugfix 可追踪 |
| "信号文件有错但意图很清楚" | 校验器必须通过；请用户修文件 |
| "先删除信号文件，再清理" | 信号文件删除是**最后**一步，前提是一切都已校验通过 |
| "修复很简单，Worker 流水线大材小用" | Worker 确保回归测试、覆盖率、ST 用例与评审 —— 全部必要 |
