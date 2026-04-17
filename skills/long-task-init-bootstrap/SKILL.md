---
name: long-task-init-bootstrap
description: "Use when dispatched by long-task-init Step 4 — generate init.sh / init.ps1 from init-script-recipes.md + project tech_stack; zero-approval deterministic writer"
---

# 生成 init.sh / init.ps1

创建真实可运行、幂等、跨平台的环境 bootstrap 脚本。本 sub-skill 无审批关卡——输出走 `bash -n` / PowerShell 语法自检，通过即返回 pass。

## 步骤

1. 读 `feature-list.json.tech_stack` 获取 language / test_framework / coverage_tool
2. 读 `docs/plans/*-design.md` §1.4 Tech Stack Decisions：确切依赖版本、运行时版本锁
3. 读 `env-guide.md` §2 环境激活命令、§3 build/test/coverage 命令（若已存在于磁盘）
4. 读 `references/init-script-recipes.md`：查找匹配 tech_stack + env-manager 的模板
5. **检测环境管理器**（从 Design + 项目上下文线索推断）：
   - Python → miniconda / conda / mamba / venv / poetry / pipenv / uv / pyenv
   - Node.js → nvm / fnm / volta / corepack
   - Java → sdkman / jenv
   - C / C++ → CMake / conan / vcpkg
   - 通用 → devcontainer / docker / nix
6. 生成 `init.sh`（bash）+ `init.ps1`（PowerShell）：
   - **幂等** —— 可安全重跑
   - **Fail-fast** —— `set -euo pipefail` / `$ErrorActionPreference = "Stop"`
   - **版本锁** —— 按设计文档依赖表指定确切版本
   - **自诊断** —— 末尾打印检测到的工具版本
   - **无交互** —— 所有回答 `-y` 自动接受
   - **可移植路径** —— `"$(dirname "$0")"` / `$PSScriptRoot`
   - **必需步骤**：运行时版本 → 环境创建 → 激活 → 依赖安装 → dev 工具 → 版本 verify
7. **自检**（硬要求，evidence 必含两条通过记录）：
   ```bash
   bash -n init.sh
   pwsh -NoProfile -Command "& { $ErrorActionPreference='Stop'; [void](Get-Command -Syntax (Get-Content -Raw init.ps1)) }" \
     || pwsh -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseFile('init.ps1', [ref]\$null, [ref]\$null)"
   ```
   若主机无 `pwsh`，用 `powershell` 同义命令；两者均不可用 → 以 `blocked` 返回，blocker `["pwsh-not-available"]` 交主 agent。

## 返回

```markdown
## SubAgent Result: long-task-init-bootstrap

**status**: pass | fail | blocked
**artifacts_written**: ["init.sh", "init.ps1"]
**next_step_input**: {
  "env_manager": "conda",
  "runtime_version": "3.11",
  "install_commands": [
    "conda env create -f environment.yml",
    "conda activate <env>",
    "pip install -e ."
  ]
}
**blockers**: []
**evidence**: [
  "init.sh: 120 lines; bash -n clean",
  "init.ps1: 98 lines; PowerShell parser clean",
  "Detected env manager: conda; runtime pin: python==3.11",
  "Idempotent guards present (existing env reuse)"
]
```

## 阻塞 / 失败

- `references/init-script-recipes.md` 缺失 → `fail`
- `feature-list.json.tech_stack` 的 language 不在 recipes 支持清单（python / java / typescript / c / cpp）→ `blocked`，要求主 agent 确认手工扩展
- `bash -n` 或 PowerShell 语法检查失败 → `fail`，evidence 附报错行号；主 agent 走 Failure Addendum 返工

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 写成注释占位（例如 `# TODO: install deps`）| 真实可运行命令；每步均能即刻执行 |
| 省略 Windows 版本，仅生成 `init.sh` | 必须同时生成 `init.ps1`（逻辑对齐） |
| 依赖 psutil / hook 管理服务生命周期 | 服务由 `env-guide.md` §1 命令管理，不放 init 脚本 |
| 用浮动版本 `latest` 安装依赖 | 按设计文档固定版本（例如 `pytest==8.2.0`） |
| 生成后不做 `bash -n` / PowerShell 语法自检 | 自检是 pass 的硬要求；evidence 必含两条通过记录 |
