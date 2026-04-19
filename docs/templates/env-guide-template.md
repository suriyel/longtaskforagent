---
version: 1.0
approved_by: null
approved_date: null
approved_sections: []
---

# env-guide.md —— 环境契约（单一事实源）

> **用户可编辑。** Claude 在以下场景读取本文件：服务启停、构建/测试命令、存量代码库约束。
> 本文件是下游流水线（Worker / TDD / Quality / Feature-ST）的**单一事实源**，任何对 §3 或 §4 的修改都必须经过人工审批（更新本文件头的 `approved_by` / `approved_date` / `approved_sections`）。

## 目录
- §1 服务生命周期
- §2 环境配置
- §3 构建与执行命令
- §4 存量代码库约束
- §5 测试环境依赖
- §6 人工审批记录

---

## §1 服务生命周期

> 启停、重启协议、PID/端口约定。CLI-only 或 library-only 项目可写 "No server processes — environment activation only"。

### Services 清单
| Service Name | Port | Start Command | Stop Command | Verify URL |
|---|---|---|---|---|
| _(待填充)_ | | | | |

### 启动全部服务（输出捕获）
```bash
# Unix/macOS
[start command] > /tmp/svc-<slug>-start.log 2>&1 &
sleep 3
head -30 /tmp/svc-<slug>-start.log
# → 从输出提取 PID 与 port；二者均记入 task-progress.md

# Windows alternative
cmd /c "start /b [command] > %TEMP%\svc-<slug>-start.log 2>&1"
timeout /t 3 /nobreak >nul
powershell "Get-Content $env:TEMP\svc-<slug>-start.log -TotalCount 30"
```

### 验证服务在运行
```bash
curl -f http://localhost:<port>/health
```

### 停止全部服务（PID 优先，端口 fallback）
```bash
kill <PID>                              # Unix/macOS
taskkill /F /PID <PID>                  # Windows

# 端口 fallback
lsof -ti :<port> | xargs kill -9        # Unix/macOS
for /f "tokens=5" %a in ('netstat -ano ^| findstr :<port>') do taskkill /F /PID %a  # Windows
```

### 验证服务已停止
```bash
lsof -i :<port>                         # Unix/macOS —— 预期无输出
netstat -ano | findstr :<port>           # Windows —— 预期无输出
```

### 重启协议（Restart Protocol，4 步）
1. **Kill** —— 停止全部服务
2. **Verify dead** —— 执行"验证服务已停止"；最多轮询 5 秒
3. **Start** —— 执行"启动全部服务" + 输出捕获 → `head -30` → 提取 PID/port → 更新 task-progress.md
4. **Verify alive** —— 执行"验证服务在运行"；最多轮询 10 秒

---

## §2 环境配置

> 环境变量清单、.env.example 关联、必需 configs。

### 环境激活命令
```bash
# 例：Python venv
source .venv/bin/activate
# 例：Node.js nvm
nvm use
# 例：Conda
conda activate <env-name>
```

### 必需环境变量
参见 `.env.example`。每个 `env`-type 配置对应 `feature-list.json` `required_configs[]` 一项。

### Config 加载
参见 `scripts/check_configs.py` — 按项目原生格式加载（`.env` / `application.properties` / YAML 等）。

---

## §3 构建与执行命令

> **下游流水线消费区**。TDD Red/Green、Quality Gate、Feature-ST 通过读取本段获取命令。
> 所有命令推荐使用 **quiet execution 协议**（输出重定向到 `/tmp/*.log`，仅在失败时提取）。

### 构建命令
```bash
# quiet 执行
<build-cmd> > /tmp/build-$$.log 2>&1; echo $? > /tmp/build-$$.exit
# 成功：读 /tmp/build-$$.log 最后 30 行
# 失败：读 /tmp/build-$$.log 最后 100 行 + 提取 ERROR/FAILED 行
```

### 单元测试命令
```bash
<test-cmd> > /tmp/ut-$$.log 2>&1; echo $? > /tmp/ut-$$.exit
# 成功：无需读日志
# 失败：读最后 100 行 + 提取 FAIL/ERROR 行
```

### 覆盖率命令
```bash
<coverage-cmd> > /tmp/cov-$$.log 2>&1; echo $? > /tmp/cov-$$.exit
# 提取 line/branch 覆盖率百分比
```

### 静态分析命令
```bash
<static-analysis-cmd> > /tmp/static-$$.log 2>&1; echo $? > /tmp/static-$$.exit
```

### Re-check 协议
- 任何命令失败 → 修复后**仅重跑失败的测试/步骤**（by name），不整轮重跑
- 临时文件清理：`trap 'rm -f /tmp/*-$$.log /tmp/*-$$.exit' EXIT` 或使用 `mktemp`

### 工具/环境故障 Fallback
命令本身异常退出（如 `ModuleNotFoundError` / `mvn: command not found` / 连接测试 DB 超时）：
1. 诊断根因（测试栈未装 / env 未激活 / 服务未启动）
2. 视情况跑 `init.sh` / `init.ps1`，或按 §1 启动依赖服务
3. 重试一次仍失败 → SubAgent 返回 `status: blocked`，evidence 前缀 `[ENV-ERROR]` 附故障摘要；**绝不跳过**测试继续推进

### 工具版本锁定
记录关键工具的最低版本要求（node / python / java / 构建工具）。

---

## §4 存量代码库约束

> **下游流水线消费区**（单一事实源）。Feature Design、TDD、Worker 的新代码必须遵守以下约束。
> **数据源**：`docs/rules/*.md`（由 `codebase-scanner` 扫描填充）。init 阶段直接从 `docs/rules/` 提取关键约束投影到此处；设计文档**不再**镜像这些约束。
> 本段变更必须经人工审批（见 §6）。

### §4.1 强制内部库
| 场景 | 必须使用 | 禁止重新实现 |
|---|---|---|
| _(例：日志)_ | _(例：公司内部 logging 封装)_ | _(例：直接 stdout)_ |

### §4.2 禁用 API
| API / 模式 | 禁用理由 | 替代方案 |
|---|---|---|
| _(例：`eval()`)_ | _(安全风险)_ | _(结构化解析)_ |

### §4.3 代码风格基线
- 命名约定：_(例：snake_case for vars, PascalCase for classes)_
- 文件布局：_(例：`src/<module>/<feature>.py`)_
- 错误处理模式：_(例：raise domain exceptions；never bare `except`)_

### §4.4 构建系统约定
- 构建产物目录：_(例：`dist/`，`target/`)_
- 忽略清单参考：`.gitignore`
- 依赖锁文件：_(例：`poetry.lock`、`package-lock.json`)_

---

## §5 测试环境依赖

> 数据库、消息队列、第三方服务的本地替身配置。

### 数据库
```bash
# 例：启动本地 PostgreSQL
docker compose -f docker-compose.test.yml up -d db
```

### 消息队列
```bash
# 例：启动本地 Redis
docker compose -f docker-compose.test.yml up -d redis
```

### 第三方服务
```bash
# 例：Chrome DevTools MCP（UI 测试项目必需）
# 启动方式参考 hooks/chrome-mcp-setup
```

### 替身配置
- 如使用 WireMock / MockServer，填写配置文件路径与启动命令

---

## §6 人工审批记录

> **任何对 §3 或 §4 的修改必须经过人工审批**。Worker Step 0 读取本段 frontmatter 决定是否阻断启动。

### 审批流程
1. 开发/AI 修改 §3 或 §4
2. 用户审阅 diff
3. 用户更新本文件头 YAML frontmatter：
   ```yaml
   ---
   version: <bump>
   approved_by: <user-handle>
   approved_date: <YYYY-MM-DD>
   approved_sections: ["§3", "§4"]  # 或全部
   ---
   ```
4. `python scripts/check_env_guide_approval.py` 通过 → Worker 可启动

### 首次生成豁免
由 `long-task-init` 首次生成时，`approved_by: null` 表示豁免状态；下次修改 §3/§4 时必须审批。

### 历史记录
| 日期 | 版本 | 审批人 | 变更摘要 |
|---|---|---|---|
| _(例：2026-04-17)_ | 1.0 | _(例：user)_ | _(例：初始生成)_ |
