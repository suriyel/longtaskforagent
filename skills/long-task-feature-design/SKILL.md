---
name: long-task-feature-design
description: "在 long-task 项目中 TDD 之前使用 -- 生成功能级详细设计，包含接口契约、实现摘要、边界/错误分析、测试清单和现有行为分析"
---

# 功能级详细设计

生成功能详细设计文档。请自行读取所有文档。

> **对于 `category: "bugfix"` 功能**：重点关注：(1) 根因文档，(2) 定向修复方案，(3) 回归测试清单。精简实现摘要，聚焦修复方法和回归测试。

## 你的任务

1. 读取执行规则：`skills/long-task-feature-design/references/feature-design-execution.md`
2. 读取模板：`skills/long-task-feature-design/references/feature-design-template.md`

## 关键约束

- 派生输出路径：`python scripts/feature_paths.py design-doc --feature <id>` → `docs/features/<id>-<slug>.md`；完整设计文档写入该路径
- 无内容的章节直接省略，不写 N/A
- 测试清单负向测试比例 >= 40%
- 测试清单类别应根据 SRS 验收标准覆盖 FUNC、BNDRY、SEC
- §11 合规：命名遵循 §11.5，操作使用 §11.1 库，错误处理遵循 §11.6
- **最大化复用**：步骤 1c 在设计前探索代码库 -- 理解与需求相关的现有行为，优先复用现有逻辑而非编写新代码
- **实现摘要**：精炼描述改哪些类、如何改，Red/Green/Refactor 严格遵从
- 设计输出中不包含 TDD 任务分解 -- TDD 执行由专用子技能处理
- 不要开始 TDD

使用 `feature-design-execution.md` 中的结构化返回契约报告摘要。

---

## 集成

**调用方：** long-task-work-design（Step 2 DISPATCH SubAgent）
**依赖：** 系统设计文档、SRS、feature-list.json
**产出：** `docs/features/<id>-<slug>.md`（路径由 `scripts/feature_paths.py` 派生）
**后续：** 下一会话由 `phase_route.py` 路由到 long-task-work-tdd
