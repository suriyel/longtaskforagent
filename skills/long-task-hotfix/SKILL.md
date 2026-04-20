---
name: long-task-hotfix
description: "当 bugfix-request.json 存在时使用 - 验证、复现、定位根因，并将用户报告的缺陷作为 category=bugfix 功能入队，然后链接到 Worker 进行 TDD 修复"
---

<EXTREMELY-IMPORTANT>
你正在使用 long-task-hotfix skill。此 skill 处理用户手动测试中发现的缺陷。

你的职责仅限于：验证 → 复现 → 根因分析 → 入队 → 链接到 Worker。
实际修复（TDD）由 Worker 流水线处理 — 不要在此处实现修复。
</EXTREMELY-IMPORTANT>

## 步骤 1：宣告

打印："I'm using the long-task-hotfix skill. Processing bugfix-request.json."

使用 TodoWrite 跟踪你在 8 个步骤中的进度。

---

## 步骤 2：验证信号文件

运行：
```bash
python scripts/validate_bugfix_request.py bugfix-request.json
```

如果验证失败：
- 清晰地打印错误信息
- 通过 `AskUserQuestion` 要求用户修复文件
- 用户响应后重新验证
- 验证通过前不得继续

---

## 步骤 3：定位

按顺序读取以下文件：
1. `bugfix-request.json` — 了解标题、描述、严重性、feature_id、复现步骤
2. `feature-list.json` — 查找关联的功能（如果 `feature_id` 非空），读取 `tech_stack`；确定下一个可用功能 `id`
3. `long-task-guide.md` — 环境激活命令
4. `task-progress.md` 的 `## Current State` 节 — 近期会话历史
6. `git log --oneline -10` — 近期提交上下文

如果 `feature_id` 非空：从 `feature-list.json` 读取关联功能的条目以了解上下文（已有的 `srs_trace`）。

---

## 步骤 4：复现

**目标**：在任何分析之前确认缺陷可复现。

1. 按 `long-task-guide.md` 激活环境
2. 严格按照 `bugfix-request.json` 中的 `reproduction_steps` 执行
3. 运行现有测试套件；记录当前失败的测试
4. 记录：执行的确切命令、观察到的确切输出、确认缺陷已显现

**硬性门禁 — 无法复现：**
如果缺陷无法复现：
- 在 `task-progress.md` 中记录尝试
- 不要删除 `bugfix-request.json`
- 通过 `AskUserQuestion` 请求澄清（更详细的步骤、特定环境、样本数据）
- **在复现确认之前停在此处**

---

## 步骤 5：根因分析

执行 `skills/using-long-task/references/systematic-debugging.md` 中的 **4 阶段系统化调试流程**：

**阶段 1 — 根因调查**：收集完整错误证据，找到最小复现，检查近期 git 变更，从入口点到故障点追踪数据流。

**阶段 2 — 模式分析**：查找类似的正常工作代码路径，比较上下文，检查依赖版本和配置值。

**阶段 3 — 假设与测试**：形成一个具体的可测试假设；做一个最小的诊断性变更来验证或推翻；如果错误，返回阶段 1。

**阶段 4 — 确认根因**：得出单一确认的根因陈述。

**必需输出**：`"Root cause: [一句话陈述]"`

**铁律**：根因确认之前不得创建功能条目。如果经过 3 次阶段 3 迭代仍无法确认根因，通过 `AskUserQuestion` 向用户请求更多上下文。

---

## 步骤 6：作为 Bugfix 功能入队

向 `feature-list.json` 添加新功能条目。确定下一个可用 `id`（现有最大 id + 1）。

**新功能对象：**
```json
{
  "id": <next available>,
  "wave": <current max wave id>,
  "category": "bugfix",
  "title": "Fix: <title from bugfix-request.json>",
  "description": "<actual_behavior from bugfix-request.json> — Root cause: <confirmed root cause>",
  "priority": "<Critical|Major → 'high', Minor → 'medium', Cosmetic → 'low'>",
  "status": "failing",
  "srs_trace": ["<FR-xxx from linked feature, or new FR-xxx if unlinked>"],
  "dependencies": [<fixed_feature_id>],
  "deprecated": false,
  "deprecated_reason": null,
  "supersedes": null,
  "bug_severity": "<severity from bugfix-request.json>",
  "bug_source": "manual-testing",
  "fixed_feature_id": <feature_id from bugfix-request.json, or null>,
  "root_cause": "<confirmed root cause one-sentence>"
}
```

**注意事项：**
- `dependencies`：如果非空则设为 `[fixed_feature_id]`（确保 Worker 在此修复之前处理原始功能）；如果为空则设为 `[]`
- `wave`：使用 `feature-list.json` 的 `waves` 数组中当前最大的 wave id
- 如果 `fixed_feature_id` 非空，将 `srs_trace` 设置为包含关联功能的需求 ID 以确保可追溯性

添加后进行验证：
```bash
python scripts/validate_features.py feature-list.json
```

继续之前修复所有验证错误。

---

## 步骤 7：更新 task-progress.md

在当前 `## Current State` 内容之后追加热修复会话条目：

```markdown
## Hotfix Session — YYYY-MM-DD: <bug title>
- **Severity**: <severity>
- **Bugfix Feature ID**: #<new id>
- **Fixed Feature**: #<fixed_feature_id> <feature title> (or "Unlinked")
- **Root Cause**: <one sentence>
- **Status**: Enqueued — Worker will handle TDD
```

同时更新 `## Current State` 标题以反映新的失败功能。

---

## 步骤 8：收尾

1. 删除 `bugfix-request.json`（这是最终不可逆操作 — 仅在步骤 6 和 7 完成且 `validate_features.py` 通过后执行）
3. 打印：
   ```
   Bug #<id> enqueued as category=bugfix feature.
   Title: Fix: <title>
   Severity: <severity>
   Root cause: <one sentence>
   Worker will handle: TDD
   ```
4. 链接到：下一会话由 `phase_route.py` 路由到 `long-task:long-task-work-design`（新 bugfix 特性 → router 自动挑）

---

## 关键规则

- **任何操作前先验证信号文件** — 步骤 3 之前验证器必须通过
- **分析前必须复现** — "无法复现"是有效的已记录结果；不得在未复现的缺陷上跳到根因分析
- **入队前必须确认根因** — 4 阶段系统化调试流程为强制步骤；不得猜测后入队
- **信号文件最后删除** — 删除是最终不可逆操作；`validate_features.py` 必须先通过
- **如果 `bugfix-request.json` 和 `increment-request.json` 同时存在**：先完整处理此热修复；不要删除 `increment-request.json`；它将在下一个会话中处理
- **此 skill 不实现修复** — Worker 负责 TDD；此 skill 仅验证、诊断和入队
- **此处不做临时代码编辑** — 不要在此 skill 期间编写测试或修复代码；那是 Worker 的工作

## 危险信号

这些想法意味着停下 — 你在自我合理化：

| 想法 | 现实 |
|---------|---------|
| "我能看到代码中的缺陷，让我直接修复" | 先完成 4 阶段根因分析；然后入队；Worker 修复 |
| "我知道根因，跳过阶段 1-3" | 全部 4 个阶段都是强制的；记录它们可防止错误假设 |
| "无法复现但我知道原因" | 无法复现 = 停止；记录到 task-progress.md；询问用户 |
| "我跳过 feature-list.json 条目，直接修复" | 每个修复必须在 feature-list.json 中作为 category=bugfix 可追溯 |
| "信号文件有错误但意图很明确" | 验证器必须通过；要求用户修复文件 |
| "我先删除信号文件，然后再清理" | 信号文件删除是所有验证通过后的最后步骤 |
| "修复很简单，Worker 流水线是大材小用" | Worker 通过 TDD 确保回归测试 — 这是必需的 |

## 集成

此 skill 由 `using-long-task` 路由器在项目根目录存在 `bugfix-request.json` 时调用（最高优先级 — 高于增量）。此 skill 完成后：
- `bugfix-request.json` 已删除
- `feature-list.json` 中新增了一个 `category: "bugfix"` 功能，`status: "failing"`
- 路由器下一次运行（`phase_route.py`）：`feature-list.json` + `current=null` + 有新 bugfix failing 特性 → `long-task-work-design`（starting_new=true，原子写 `current`）
- 两次 Worker 会话（design + tdd）完成此 bugfix 特性
