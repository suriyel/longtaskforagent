# 代码库约定规则

> 由 long-task-codebase-scanner 于 {{date}} 自动生成。
> 这些文档记录了项目的现有约定。
> 可自由编辑 -- 下游技能在设计和工作阶段会读取这些文档。

## 文档列表

| 文档 | 说明 |
|----------|-------------|
| [coding-style.md](coding-style.md) | 命名约定、格式化规则、文件与目录组织 |
| [coding-constraints.md](coding-constraints.md) | 二方库约束、静态分析工具、错误处理、导入组织 |
| [build-and-compilation.md](build-and-compilation.md) | 构建系统、打包、环境管理 |

## 关键发现摘要

- **语言**: {{languages}}
- **内部库（二方）**: 发现 {{internal_lib_count}} 个 -- {{internal_lib_list}}
- **静态分析工具**: {{static_tools}}
- **测试框架**: {{test_framework}}
- **覆盖率工具**: {{coverage_tool}}
- **变异测试工具**: {{mutation_tool}}
- **构建系统**: {{build_system}}

## 使用方式

这些规则在流水线的两个阶段被消费：

1. **设计阶段** -- 合并至设计文档 §11（代码库约定与约束），作为所有新代码的强制参考
2. **工作阶段** -- 在定向、TDD 和内联检查步骤中通过设计文档 §11 引用

如需重新扫描：删除 `docs/rules/` 并启动新会话。路由器将重新触发代码库扫描器。
