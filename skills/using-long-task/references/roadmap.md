# Roadmap — 未来增强

## P2：并行 Agent 分发（R8）

**状态**：已文档化，尚未实现

**目标**：实现独立特性实现的并行分发。

**需求**：
- R8.1：识别相互无依赖、可并行执行的特性
- R8.2：使用 Task 工具并行分发 implementer SubAgent
- R8.3：合并结果、检测冲突、并行完成后跑完整测试套件

**设计说明**：
- 仅并行化真正独立的任务（无共享文件、无依赖）
- 并行完成后始终运行完整测试套件
- 若发现冲突，串行解决
- 参考 `subagent-development.md` 的并行分发章节

## P2：插件发现系统（R12）

**状态**：已文档化，尚未实现

**目标**：支持 skill 发现、frontmatter 元数据与优先级覆盖。

**需求**：
- R12.1：SKILL.md 的 YAML frontmatter 支持 skill 名称与触发条件
- R12.2：支持 skill 优先级覆盖（项目级 > 用户级 > 默认）
- R12.3：考虑用于 marketplace 分发的 `.claude-plugin` 打包格式

**设计说明**：
- 当前 SKILL.md 已有 frontmatter — 扩展发现元数据
- 覆盖机制允许用户在不 fork 的情况下定制工作流
- Marketplace 格式支持一键安装

## P2：自动更新机制（R13）

**状态**：已文档化，尚未实现

**目标**：skill 加载时检查新版本。

**需求**：
- R13.1：在 SKILL.md frontmatter 或 VERSION 文件中加入版本号
- R13.2：skill 加载时检查远程仓库的较新版本
- R13.3：如有更新提示用户（绝不自动更新）

**设计说明**：
- 基于 git 的检查：对 origin 执行 `git ls-remote`
- 比较本地与远端 HEAD 或 tag
- 仅通知用户 — 绝不自动应用更新

## P3：多平台支持（R18）

**状态**：未来考虑

**目标**：支持 Codex（OpenAI）与 OpenCode 平台。

**需求**：
- R18.1：评估 Codex 适配（通过 symlink 的原生 skill 发现）
- R18.2：评估 OpenCode 适配（JS 插件系统）
- R18.3：创建各平台专属 README 文档

**设计说明**：
- Codex：symlink 到 `~/.agents/skills/long-task-agent/`
- OpenCode：JavaScript 插件包装
- 核心工作流与平台无关；仅 skill 发现机制不同

## P2：集成测试（R16）

**状态**：已文档化，尚未实现

**目标**：在真实 Claude Code 会话中测试 skill 工作流本身。

**需求**：
- R16.1：创建 `tests/` 目录含 skill 工作流集成测试
- R16.2：加入 token 使用分析工具
- R16.3：加入会话 transcript 验证（验证 skill 调用、subagent 分发）

**设计说明**：
- 测试框架应运行真实 Claude Code 会话
- 验证：skill 加载、各阶段按序执行、产物被创建
- Token 分析有助于优化提示词大小
