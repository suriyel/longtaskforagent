# 语言 / Language

**[中文](README.md)** | **[English](README_EN.md)**

---

# 快速开始

> **分支说明**：本仓库有两个主要分支：
> - **`simple`** — 精简版，适合大多数项目（推荐）
> - **`main`** — 完整版，包含全部高级功能

### 1. 安装

#### 方式一：一键安装脚本（推荐）

默认安装 `simple` 分支。

**macOS / Linux：**

```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.sh | bash
```

**Windows（PowerShell）：**

```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.ps1 | iex
```

如需安装其他分支，通过 `BRANCH` 环境变量指定：

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.sh | BRANCH=main bash

# Windows PowerShell
$env:BRANCH="main"; irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.ps1 | iex
```

脚本会自动：
- Clone 指定分支到 `~/.claude/plugins/marketplaces/longtaskforagent/`
- 更新 `known_marketplaces.json` 注册信息

安装完成后，使用 Claude Code 安装插件：

```shell
/plugin install long-task@longtaskforagent
```

切换分支时重新运行安装脚本即可（会自动替换已有安装）。

#### 方式二：Claude Code 原生命令

在 Claude Code 中，首先注册市场：

```bash
/plugin marketplace add suriyel/longtaskforagent
```

然后安装插件：

```shell
/plugin install long-task@longtaskforagent
```

> 注意：此方式默认安装 `main` 分支，如需 `simple` 分支请使用方式一。

#### 方式三：OpenCode 用户

如果您使用 [OpenCode](https://opencode.ai)：

**macOS / Linux：**

```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | bash
```

**Windows（PowerShell，需开发者模式或管理员权限）：**

```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
```

安装完成后重启 OpenCode 即可激活。完整说明请参阅 [OpenCode 安装指南](docs/README.opencode.md)。

### 2. 快速开始

启动 Claude Code 后，只需告诉它您想构建什么：

```
> 我想构建一个GitHub 热门项目周报系统。使用 long task skill。
```

系统将自动进入**需求阶段**，通过结构化提问帮助您完善需求，最终生成标准化的 SRS 文档。后续工作流程完全自动化：

```
需求 → 设计 → 初始化 → 工作循环
```

[点击查看样例项目](https://github.com/suriyel/githubtrends)

![](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260313224154726.png)

---

# Long-Task Agent

**一款 Claude Code 技能插件，将单会话 AI 编码转变为严谨的多会话软件工程工作流。**

大多数 AI 编程助手在一次对话后会丢失上下文。Long-Task Agent 通过实现五阶段架构和持久状态桥接解决了这个问题——使 Claude Code 能够以专业工程团队的纪律，跨无限会话构建复杂项目。
![Hero Banner](images/1.png)

## 为什么选择 Long-Task Agent？

| 问题 | Long-Task Agent 如何解决 |
|---------|-------------------------------|
| AI 在 `/clear` 后忘记所有内容 | 持久化产物（`feature-list.json`、`task-progress.md`、git 历史）自动桥接会话 |
| AI 不理解需求就生成代码 | 符合 ISO/IEC/IEEE 29148 的需求收集在编写任何代码前产生经批准的 SRS |
| AI 跳过测试或编写浅层测试 | 严格的 TDD（红→绿→重构）配合覆盖率门禁（≥90% 行覆盖，≥80% 分支覆盖）和变异测试（≥80% 得分） |
| AI 偏离批准的设计 | 设计接口覆盖门 + 每个功能后内联合规检查 |
| 无法安全地向现有项目添加功能 | 增量技能执行影响分析，就地更新 SRS/设计，用波次跟踪变更 |
| "在我机器上能跑"综合症 | 严格 TDD + 覆盖率门禁 + 变异测试确保代码质量 |

![Problem vs Solution](images/2.png)

## 核心理念

### 1. 需求驱动，而非代码优先

每个项目都从结构化的需求收集开始——而不是编码。SRS 捕获*做什么*，设计文档捕获*怎么做*。两者全部批准后才会编写代码。

### 2. 持久状态桥接会话

十多个持久化产物确保会话间零知识丢失：

| 产物 | 用途 |
|----------|---------|
| `feature-list.json` | 带状态跟踪的结构化任务清单（JSON 防止模型损坏） |
| `task-progress.md` | 逐会话日志，带当前状态标题 |
| `docs/plans/*-srs.md` | 已批准的软件需求规格说明书 |
| `docs/plans/*-design.md` | 已批准的技术设计文档 |
| `long-task-guide.md` | 工作会话指南，含环境激活 + 工具命令 |
| `RELEASE_NOTES.md` | Keep a Changelog 格式的活态变更日志 |
| Git 历史 | 带描述性提交的完整变更历史 |

### 3. 质量不可妥协

每个功能都要通过一系列自动化质量门禁——无例外，无捷径：

- **TDD 红→绿→重构** — 先写测试，总是如此
- **覆盖率门禁** — 行覆盖 ≥90%，分支覆盖 ≥80%
- **变异门禁** — 变异得分 ≥80%（捕获那些通过但实际没测试任何东西的测试）
- **内联合规检查** — 每个功能后机械验证接口契约、测试清单、依赖版本

### 4. 每个周期一个功能

每个工作会话专注于恰好一个功能。这防止上下文耗尽，确保干净的提交，并使每个功能独立可验证。

![Quality Gates](images/3.png)

## 五阶段架构


![Architecture](images/4.png)

### 阶段 0a：需求收集

- 符合 ISO/IEC/IEEE 29148 的结构化提问
- EARS 需求模板（Given/When/Then 验收标准）
- 反模式检测：模糊词、复合需求、设计泄漏
- 产出一份已批准的 **SRS**（`docs/plans/*-srs.md`）

### 阶段 0b：设计

- 提出带有权衡分析的 2-3 种方案
- 每功能的 Mermaid 图（类图、序列图、流程图）
- 第三方依赖版本及兼容性验证
- 产出一份已批准的 **设计文档**（`docs/plans/*-design.md`）

### 阶段 1：初始化

- 读取 SRS + 设计，脚手架项目骨架
- 需求阶段双向粒度分析（G1-G6拆分 + S1-S4合并），确保每个FR适配单次会话上下文预算
- 创建初始 git 提交

### 阶段 2：工作循环

每个循环遵循严格纪律：

```
定位 → 引导 → 开发工具门禁 → 计划
  → TDD 红 → TDD 绿 → 覆盖率门禁
    → TDD 重构 → 变异门禁
      → 内联合规检查
        → 持久化 → 下一个功能
```

### 阶段 1.5：增量（发布后变更）

- 放置 `increment-request.json` 信号文件 → 技能自动检测
- 对现有功能的影响分析
- 就地更新 SRS、设计（git 跟踪历史）
- 带波次元数据追加新功能以实现可追溯性
  ![Worker Cycle](images/5.png)

## 8 技能超能力架构

Long-Task Agent 使用**按需技能加载**模式——只有引导路由器在会话开始时加载；阶段技能按需加载，保持上下文精简。

```
using-long-task (引导路由器 — 始终加载)
   │
   ├─→ long-task-requirements ──→ long-task-design ──→ long-task-init
   │                                                       │
   │                                                       ↓
   ├─→ long-task-increment (如果 increment-request.json 存在)       long-task-work
   │                                                                  │  │
   │                                                           ┌──────┘  └──────┐
   │                                                           ↓                ↓
   │                                                      long-task        long-task
   │                                                        -tdd           -quality
   │                                                           │                │
```

| 技能 | 角色 |
|-------|------|
| `using-long-task` | 引导路由器——检测项目状态，调用正确阶段 |
| `long-task-requirements` | ISO 29148 需求收集 → SRS |
| `long-task-design` | 带权衡分析的技术设计 |
| `long-task-init` | 项目脚手架和功能分解 |
| `long-task-work` | 工作编排器（每周期一个功能） |
| `long-task-tdd` | TDD 红→绿→重构纪律 |
| *(quality gates)* | 覆盖率门禁 + 变异门禁（内联于 Worker Step 8） |
| `long-task-increment` | 带影响分析的发布后功能添加 |

---

## 多语言支持

Long-Task Agent 与语言无关。它通过可配置的工具设置支持任何技术栈：

| 语言 | 测试框架 | 覆盖率 | 变异测试 |
|----------|---------------|----------|------------------|
| Python | pytest | pytest-cov | mutmut |
| Java | JUnit | JaCoCo | PIT (pitest) |
| TypeScript | Vitest / Jest | c8 / istanbul | Stryker |
| C/C++ | Google Test | gcov + lcov | Mull |
| *自定义* | *任意* | *任意* | *任意* |

`feature-list.json` 中的 `tech_stack` 字段驱动所有工具命令——使用 `get_tool_commands.py` 消除每种语言的查找：

```bash
python long-task-agent/scripts/get_tool_commands.py feature-list.json
```

---

## 自动化工作流脚本

### auto_loop.py - 不间断执行保障

`auto_loop.py` 是确保长时间任务能**不间断执行**的核心脚本，通过重复调用 Claude Code 自动化多特性开发流程，直到所有活动特性通过或达到终止条件。

**核心价值：**
- 🔄 **自动化迭代** - 无需手动重复执行，脚本自动推进工作流
- ⏸️ **优雅中断** - 支持两级 Ctrl+C 中断，确保当前工作不丢失
- 🛡️ **错误检测** - 自动识别上下文限制、速率限制等不可恢复错误
- 📊 **状态跟踪** - 实时显示特性通过情况

**使用方法：**
```bash
python scripts/auto_loop.py feature-list.json
python scripts/auto_loop.py feature-list.json --max-iterations 30
python scripts/auto_loop.py feature-list.json --cooldown 10
python scripts/auto_loop.py feature-list.json --prompt "继续"
```

**参数说明：**
- `feature_list`: feature-list.json 的路径（必需）
- `--max-iterations`: 最大迭代次数（默认：50）
- `--cooldown`: 迭代之间的等待秒数（默认：5）
- `--prompt`: 每次迭代发送的提示（默认：继续）

**中断处理：**
- **第1次 Ctrl+C**: 优雅停止 - 完成当前迭代，然后停止
- **第2次 Ctrl+C**: 强制终止 - 立即终止子进程

**退出代码：**
- 0: 所有特性通过
- 1: 错误或达到最大迭代次数
- 2: claude 命令失败
- 3: 检测到不可恢复的错误（上下文限制、速率限制等）
- 130: 用户中断（Ctrl+C）

---

## 验证和安全脚本

插件包含一套验证脚本以防止常见故障：

| 脚本 | 用途 |
|------|------|
| `validate_features.py` | 验证 `feature-list.json` 模式和数据完整性 |
| `validate_guide.py` | 验证 `long-task-guide.md` 结构完整性 |
| `validate_increment_request.py` | 验证增量请求信号文件 |
| `get_tool_commands.py` | 将技术栈映射到 CLI 命令 |

---

## 模板自定义指南

Long-Task Agent 提供可自定义的文档模板，用于生成符合行业标准的需求和设计文档。

### 内置模板

| 模板 | 路径 | 用途 | 填写力度 |
|------|------|------|------|
| SRS 模板 | `docs/templates/srs-template.md` | 软件需求规格说明书（ISO/IEC/IEEE 29148 全章节；空洞章节按 `输入档位` 省略或标 `[不适用]`）| L1 输入：全章节；L2/L3 输入：§1.3 / §3 干系人 / §3.1 用例视图等可标 `[不适用]` |
| 设计模板 | `docs/templates/design-template.md` | 技术设计文档（§0-§11 全结构；§3.5 影响面 / §6.2.1 配置 schema / §6.2.2 消息 schema 子表支持 L2/L3 纯规约式增量；空洞章节可省略）| L1 输入：架构/数据模型全填；L2/L3 输入：§1 设计驱动 / §3.1-§3.4 架构概览 / §5 数据模型 / §7 第三方依赖 可标 `[不适用]` |

> **`输入档位`（L1/L2/L3）由 `long-task-requirements` Step 1.2 自动评定**（基于硬精确标识密度 + 口语词密度），决定章节填写力度。模板只有一份，空洞章节按档位省略。

### 自定义方式

#### SRS 模板自定义

在**需求阶段**（`long-task-requirements`），通过对话指定自定义模板路径：

```
请使用我自定义的 SRS 模板：docs/templates/my-srs-template.md
（无指定时加载默认模板，按 `输入档位` 决定空洞章节省略粒度）
```

**要求**：模板必须是 `.md` 文件，且包含至少一个 `## ` 级别的标题。

#### 设计模板自定义

在**设计阶段**（`long-task-design`），通过对话指定自定义模板路径：

```
请使用我自定义的设计模板：docs/templates/my-design-template.md
（无指定时加载默认模板，按 `输入档位` 决定空洞章节省略粒度）
```

**要求**：模板必须是 `.md` 文件，且包含至少一个 `## ` 级别的标题。

### 模板优先级规则

1. **用户指定路径** > **内置默认模板**
2. 模板文件必须存在，否则回退到默认模板
3. 模板必须通过验证（`.md` 文件 + 至少一个 `## ` 标题）

### 最佳实践

1. **复制内置模板作为起点**：保留原有的章节结构，只修改指导文字
2. **保持标准合规性**：SRS 模板建议保留 ISO 29148 核心章节
3. **版本控制**：将自定义模板提交到 git，便于团队协作

---

## 对比分析

| 能力 | 典型 AI 编程 | Long-Task Agent |
|------------|------------------|-----------------|
| 多会话持久化 | 手动复制粘贴 | 通过 10+ 持久化产物自动完成 |
| 需求流程 | "直接构建" | 符合 ISO 29148 的 SRS，带结构化收集 |
| 设计流程 | 临时性 | 2-3 种方案带权衡，逐节批准 |
| TDD 纪律 | 可选，经常跳过 | 每个功能强制 红→绿→重构 |
| 测试质量验证 | 仅行覆盖（如果有） | 覆盖率 + 变异测试，可配置阈值 |
| 实现后验证 | 无 | 设计接口覆盖门 + 内联合规检查 |
| 发布后添加功能 | 直接编辑代码 | 影响分析、跟踪波次、文档更新 |
| 项目状态可见性 | 读代码 | `task-progress.md` + `feature-list.json` |

---

## 项目结构

```
long-task-agent/
├── skills/                          # 8 个技能（按需加载）
│   ├── using-long-task/             # 引导路由器
│   ├── long-task-requirements/      # 阶段 0a：需求和 SRS
│   ├── long-task-design/            # 阶段 0b：设计
│   ├── long-task-init/              # 阶段 1：初始化
│   ├── long-task-work/              # 阶段 2：工作编排器
│   ├── long-task-tdd/               # TDD 纪律
│   ├── long-task-quality/           # 覆盖率 + 变异门禁（引用文件，非独立技能）
│   └── long-task-increment/         # 增量开发
├── skills/using-long-task/scripts/  # 共享脚本（router + validators + auto_loop）
├── skills/long-task-init/scripts/   # init_project.py（由 hook 拷到消费者项目）
├── tests/                           # 所有脚本的测试套件
├── hooks/                           # SessionStart 钩子配置
├── commands/                        # 用户快捷命令
├── docs/templates/                  # 可自定义的 SRS 和设计模板
└── CLAUDE.md                        # 跨会话导航索引
```

---

## 指导原则

> **"三思而后行。"**

1. **无批准需求就不写代码** — SRS 在隐藏假设变成 bug 之前捕获它们
2. **无批准设计就不实现** — 在承诺一种方案前评估 2-3 种方案
3. **质量不走捷径** — TDD、覆盖率、变异测试和内联合规检查是不可协商的门禁
4. **一个功能，一个周期** — 专注工作防止上下文耗尽并确保干净、原子性的提交
5. **持久化产物胜过短暂记忆** — JSON 状态文件和 git 历史在任何上下文丢失后依然存在
6. **系统化调试胜过猜测修复** — 在任何修复尝试前进行根因分析
7. **不可变的验证步骤** — 一旦设定，标准永不降低


![Principles](images/7.png)

## 路线图

- **并行 Agent 调度** — 识别独立功能并并行调度工作子 agent

---

## 鸣谢

- TDD部分借鉴[superpowers](https://github.com/obra/superpowers)
- long task执行参考自 B站up [数字游牧人](https://b23.tv/UUVywob?share_medium=android&share_source=weixin&bbid=XUD7142DB761960E57CD68EE4E71913CF4699&ts=1773413437129)

## 许可证

[MIT](LICENSE)

---

<p align="center">
  <i>为 Claude Code 构建 — 将 AI 辅助开发转变为 AI 工程化开发。</i>
</p>
