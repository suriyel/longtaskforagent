# OpenCode 插件/宿主卡死定位手册

> 受众：AI Agent / 维护者。调试 `~/.config/opencode/` 下插件或 skill 安装导致 opencode 启动卡死时查阅。
> 每节是可执行规则，不是叙事。

---

## § 1. 已知坑：v1.14.19 plugin 目录单复数

| 位置 | 作用 | 版本要求 |
|---|---|---|
| `~/.config/opencode/plugin/` **（单数）** | auto-scan 的用户级插件目录 | v1.14.19 上线 |
| `~/.config/opencode/plugins/` **（复数）** | 历史路径 / 官方 docs 残留 | 此版本会触发卡死 |
| 仓库内 `.opencode/plugins/<file>.js` | 源文件位置，与宿主无关 | 无关，保持仓库既有布局 |

**症状**：`opencode run "..."` 或 TUI 启动后无响应 20~30s，最终在 log 里看到：

```
ERROR service=server-proxy e=setRawMode failed with errno: 5 exception
WARN  service=server-proxy error=Operation timed out after 5000ms worker shutdown failed
```

`errno:5` = EIO，是 TTY raw-mode 失败，但**根因**是前面插件加载阶段的阻塞 —— 不是 TTY 问题。

**修复**：用户侧 symlink 目标 `plugins/` → `plugin/`；仓库侧 `.opencode/plugins/` 源目录**不动**。

---

## § 2. 定位插件卡死的标准流程

### Step 1. 关掉插件验证范围

```bash
mv ~/.config/opencode/plugin/<name>.js /tmp/held && \
  timeout 20 opencode run "echo hi"
```

- **返回 "hi"** → 卡死在插件加载阶段（继续 Step 2）
- **仍然卡死** → 是宿主 / model / MCP 层问题，不是插件

### Step 2. 隔离插件逻辑 vs 加载机制

用 4 行 stub 替换真实插件：

```js
export const StubPlugin = async ({ client, directory }) => {
  return {};
};
```

- **stub 也卡死** → **宿主加载机制本身的 bug**（路径、扫描、bun install、模块解析其一）
- **stub 不卡、真插件卡** → 真插件内部同步代码阻塞（通常是 `execFileSync` / 文件系统深度遍历 / 网络 fetch）

### Step 3. 用 node / bun 裸跑插件

```bash
bun -e "import('~/.config/opencode/plugin/x.js').then(m => m.X({client:null, directory:'/path'}))"
```

计时 ≤ 1s → 插件本身无阻塞；opencode 侧的调用约定/路径是问题。

### Step 4. 查宿主二进制路径约定

```bash
strings ~/.opencode/bin/opencode | grep -oE '\.opencode/[a-z]+/' | sort -u
strings ~/.opencode/bin/opencode | grep -oE '(plugin|skill|agent)[sS]?' | sort -u
```

对比宿主字面量与你 symlink 的目标路径。**复数/单数、单词是否一致** —— 这比翻 docs 更权威（docs 常落后于二进制）。

---

## § 3. 通用原则

1. **docs ≠ 当前二进制行为**：官方 docs 说 `plugins/` 能用，实测 v1.14.19 不行。遇冲突，**信 `strings` 和日志，不信 docs**。
2. **源路径 vs 目标路径不要合并讨论**：仓库里 `.opencode/plugins/xxx.js` 是源文件，用户侧 `~/.config/opencode/plugin/xxx.js` 是 symlink 目标。两套路径各自遵循各自的约定，不要因为对齐"美观"就统一改。修了目标路径不必改源路径。
3. **隔离二分要用 stub，不要改真实插件**：4 行 stub 是最便宜的二分工具；改真插件会把"加载机制问题"和"插件逻辑问题"耦合进同一次改动。
4. **`errno:5 setRawMode failed` 是结果不是根因**：TTY 报错往往是前序阻塞耗尽 startup budget 的**副作用**。不要顺着 TTY 方向排查 —— 回到时间线上一个静默区间。
5. **reference/ 下的第三方 docs 不是权威**：它们描述**那个项目**的约定，不等同于你用的宿主版本的当前实现。引用前先用 strings / 实测核对。

---

## § 4. 本仓库装器约束（固化）

- 用户侧 plugin symlink 目标 = **`~/.config/opencode/plugin/long-task.js`**（单数）
- 用户侧 skills symlink 目标 = **`~/.config/opencode/skills/long-task/`**（复数，和插件不同）
- 仓库内源路径 = **`.opencode/plugins/long-task.js`**（复数，保留）
- install.sh / install.ps1 里 `PLUGIN_DIR` / `$PluginDir` 变量命名**统一去 s**，减少后续误改

改 `install.*` 时自查清单：

- [ ] `PLUGIN_DIR` / `$PluginDir` 指向单数
- [ ] `mkdir` / `New-Item -Path` 目标单数
- [ ] `rm -f` / `del` / `Remove-Item` 旧 symlink 用单数
- [ ] `ln -s` / `mklink` / `New-Item -SymbolicLink` 目标单数
- [ ] 源路径 `.opencode/plugins/xxx.js` 仍为复数（不要动）
