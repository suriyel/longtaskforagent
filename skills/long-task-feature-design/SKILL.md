---
name: long-task-feature-design
description: "在 long-task 项目中 TDD 之前使用 -- 生成功能级详细设计，包含接口契约、算法伪代码、图表、测试清单和现有行为分析"
---

# 功能级详细设计

生成功能详细设计文档。请自行读取所有文档。

> **对于 `category: "bugfix"` 功能**：重点关注：(1) 根因文档，(2) 定向修复方案，(3) 回归测试清单。除非缺陷直接涉及相关界面，否则跳过完整图表。

## 你的任务

1. 读取执行规则：`skills/long-task-feature-design/references/feature-design-execution.md`
2. 读取模板：`skills/long-task-feature-design/references/feature-design-template.md`

## 关键约束

- 将完整设计文档写入 `docs/features/YYYY-MM-DD-<feature-name>.md`
- 每个章节（§2-§6）必须完整填写或标注 "N/A — [原因]"
- 测试清单负向测试比例 >= 40%
- 测试清单类别应根据 SRS 验收标准覆盖 FUNC、BNDRY、SEC
- §11 合规：命名遵循 §11.5，操作使用 §11.1 库，错误处理遵循 §11.6
- **最大化复用**：步骤 1c 在设计前探索代码库 -- 理解与需求相关的现有行为，优先复用现有逻辑而非编写新代码
- 设计输出中不包含 TDD 任务分解 -- TDD 执行由专用子技能处理
- 不要开始 TDD

使用 `feature-design-execution.md` 中的结构化返回契约报告摘要。

---

## 集成

**调用方：** long-task-work（步骤 2）-- Worker 分派 SubAgent，SubAgent 加载此 Skill 并内联执行
**依赖：** 系统设计文档、SRS、feature-list.json
**产出：** `docs/features/YYYY-MM-DD-<feature-name>.md`
**后续：** long-task-tdd-red（步骤 3）
