# 代码库约定规则（Codebase Convention Rules）

> 由 codebase-scanner 于 {{date}} 自动生成。
> 这些文档记录项目的既有约定。
> 可自由编辑 —— 下游 skill 在 Design 与 Worker 阶段会读取这些内容。

## 文档清单

| 文档 | 说明 |
|----------|-------------|
| [coding-style.md](coding-style.md) | 命名约定、格式规则、文件与目录组织 |
| [coding-constraints.md](coding-constraints.md) | 2/3方件约束、静态分析工具、错误处理、import 组织 |
| [build-and-compilation.md](build-and-compilation.md) | 构建系统、CI/CD 流水线、打包、环境管理 |
| [commit-conventions.md](commit-conventions.md) | Commit message 格式、分支命名、PR 约定、Tag 与发布 |

## 关键发现摘要

- **语言（Languages）**: {{languages}}
- **内部库（2nd-party）**: 发现 {{internal_lib_count}} 个 —— {{internal_lib_list}}
- **禁用 API（Prohibited APIs）**: 检出 {{prohibited_count}} 项
- **静态分析工具**: {{static_tools}}
- **构建系统**: {{build_system}}
- **CI/CD**: {{ci_platform}}
- **Commit 格式**: {{commit_format}}

## 用途

这些规则在流水线的两个节点被消费：

1. **Design 阶段** —— 合并进设计文档 §13（代码库约定与约束），作为所有新代码的绑定参考
2. **Worker 阶段** —— 在 Orient、TDD、Inline Check 步骤通过 Design §13 引用

重新扫描方法：删除 `docs/rules/` 并开启新会话。router 会重新触发 codebase-scanner。
