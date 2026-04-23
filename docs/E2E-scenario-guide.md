# Long-Task Agent 端到端操作指导书

> **本指导书会带你做什么**：用一个贯穿的例子——"GitHub 热门项目周报系统"——演示怎么从一句口语化想法出发，让 Claude Code 帮你把它做成一个有需求文档、有设计、有测试、可交付的 Python 小工具。之后再演示怎么修 bug、怎么加新功能。
>
> **面向谁**：想用 Claude Code 认真做点东西、但不想研究 skill 内部机制的使用者。你只需要会对话、会看文档、会判断 "这个对不对"。
>
> **版本**：`longtaskforagent@simple` 分支；宿主可选 Claude Code（推荐）或 OpenCode。

---

## 1. 安装

### 1.1 Claude Code（推荐）

**方式 A：一键脚本（默认 `simple` 分支）**

macOS / Linux：
```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.sh | bash
```

Windows（PowerShell）：
```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.ps1 | iex
```

指定分支：
```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.sh | BRANCH=main bash
```

脚本做了什么：
- `git clone` 仓库到 `~/.claude/plugins/marketplaces/longtaskforagent/`
- 更新 `known_marketplaces.json` 注册该市场

安装完成后，在 Claude Code 中执行：
```
/plugin install long-task@longtaskforagent
```

**方式 B：Claude Code 原生命令**
```
/plugin marketplace add suriyel/longtaskforagent
/plugin install long-task@longtaskforagent
```
> 原生命令默认装 `main` 分支；如需 `simple` 分支请用方式 A。

### 1.2 OpenCode

macOS / Linux：
```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | bash
```

Windows（需开发者模式或管理员权限）：
```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
```

脚本做了什么：
- clone 到 `~/.config/opencode/long-task-agent/`
- 符号链接 `plugin/long-task.js` 与 `skills/long-task/`
- 重启 OpenCode 即可激活

### 1.3 验证安装

任意新建一个空目录，启动 Claude Code，在会话里说：
```
使用 using-long-task skill
```
如看到 Claude 加载 `using-long-task` 并提示开始需求收集，说明安装成功。

---

## 2. 架构速览

你不需要记住所有 skill 的内部名字。理解下面两张图，就够指挥 Long-Task 做事了。

### 2.1 一个项目的生命周期

```
[你有一个想法]
     │
     ▼
  说需求   ──►  批准 SRS  ──►  批准 Design  ──►  项目骨架搭好
                                                     │
                         ┌───────────────────────────┘
                         ▼
                  [Feature 1]   ──►  [Feature 2]  ──► …  ──►  [全部完成 ✓]
                  会话 A 设计
                  会话 B 编码（TDD）
                         │
                         └──  上线后维护  ──►  修 bug / 加功能
```

每一个 "Feature" 都是独立、可交付、已测试的一小块能力。Long-Task 的纪律：**一个 feature 拆成两次会话**——第一次设计、第二次编码——让每一块都看得清、改得动。

### 2.2 你会接触到的产物

这些是随着项目推进自动出现在你项目目录里的文件。**你不用手动写它们**，但要知道它们是什么，因为你会在每个阶段被要求"看一下 / 确认"。

| 文件 | 中文定位 | 何时出现 |
|---|---|---|
| `docs/rules/*.md` | **代码库约定**——存量项目扫描出的编码风格、内部库、构建模式（给新项目一般只有一个占位文件） | 首次扫描代码库时 |
| `docs/plans/*-srs.md` | **需求文档**——你想做什么 | 需求阶段结束时 |
| `docs/plans/*-design.md` | **设计文档**——怎么做（架构 / 接口 / 数据模型） | 设计阶段结束时 |
| `feature-list.json` | **任务清单**——项目被拆成哪些 feature，每个是 passing 还是 failing | 初始化后 |
| `long-task-guide.md` | **项目工具命令参考**——这个项目用什么跑测试、看覆盖率、跑变异测试 | 初始化后 |
| `docs/features/<编号>-<名字>.md` | **功能详细设计**——某个 feature 的接口、伪代码、测试清单 | 进入该 feature 的设计会话后 |
| `task-progress.md` | **会话日志**——每次会话干了什么 | 每次会话结束追加 |
| `RELEASE_NOTES.md` | **变更日志**——项目累积交付的能力 | 每个 feature 通过后更新 |

两个只在运维阶段用到的信号文件：

| 文件 | 用于 |
|---|---|
| `bugfix-request.json` | 告诉 Long-Task 你发现了一个 bug |
| `increment-request.json` | 告诉 Long-Task 你要加新功能或改需求 |

> 💡 这两个 JSON **不需要你手写**。你只管口头描述 bug 或新需求，Claude 会帮你整理成结构化文件并保存，你最后确认一下内容即可。处理完后 Claude 会自动删掉。

### 2.3 你会直接用到的指令

**推进主流程**——每次新会话开始时，对 Claude 说：

> 使用 using-long-task skill

这是唯一的入口指令。Claude 会自动判断项目当前在哪一步，调用对应的阶段 skill 继续推进。

**独立工具**（与主流程无关，什么时候用都行）：

| 命令 | 用途 |
|---|---|
| `/deep-explore` | 给一个陌生代码库做深度摸底 |
| `/static-review` | 推送前做静态分析，自动修到零违规 |
| `/coverage-retrofit` | 给遗留代码补单元测试直到覆盖率达标 |
| `/mutation-retrofit` | 给遗留代码补变异测试 |

> 其它 skill 名字（`long-task-requirements` / `-design` / `-work-tdd` 等）是 Long-Task 内部分工，你不需要手动调用，`using-long-task` 会根据项目当前状态自动选择。

---

## 3. 场景主流程：从零构建周报系统

> **你想做什么**：一个命令行工具 `gh-weekly`。每周跑一下，它自动抓 GitHub 当周热门项目 Top 20，按编程语言分组，生成一份 Markdown 格式的周报丢到本地文件。
>
> **本章带你走完**：从一句口语化的想法 → 拿到一个可用、有测试、可维护的小工具。

### 3.1 准备

```bash
mkdir ~/code/gh-weekly && cd ~/code/gh-weekly
git init
```

在这个空目录下启动 Claude Code。接下来你只跟 Claude 对话，不再敲其它命令。

### 3.2 第一步：把想法说成需求

**你说**：

> 使用 using-long-task skill。我想做一个 GitHub 热门项目周报系统，Python 写，命令行跑。每周抓 Trending 前 20 个仓库，按语言分组，输出 Markdown 周报。

**Claude 会做什么**：它听懂了这是一个"半成品想法"，会反问你几轮——把你没讲清的地方问清楚，然后写成一份规范的需求文档。

**Claude 会问你的典型问题**（不是一次问完，3~5 轮渐进）：

- 数据从哪抓？直接解析 `github.com/trending` 页面，还是用 GitHub 官方 API？要不要登录令牌？
- 什么时候跑？你手动执行，还是挂定时任务？
- 输出到哪？存文件？打印到终端？发邮件？
- 网络断了怎么办？重试几次？要不要缓存昨天的结果？
- 周报长什么样？按语言分组后每组展示啥（名字、描述、stars、链接）？

**你要做什么**：实话实说。不知道的答 "你建议"；Claude 会给出合理默认。

**这一步结束时你会看到**：

1. Claude 把答案整理成一份需求文档，保存为 `docs/plans/2026-04-23-gh-weekly-srs.md`
2. 里面有一个 **功能需求** 列表，类似：
   - `FR-001` 系统应能抓取 GitHub Trending 当周前 20 个仓库
   - `FR-002` 系统应按主语言分组，组内按 stars 数倒序
   - `FR-003` 网络失败时最多重试 3 次，采用指数退避
   - `FR-004` 系统应把结果输出成 Markdown 文件
   - `FR-005` 系统应提供命令行参数 `--limit`、`--output` 等
3. Claude 会让你 **审阅需求文档**

**你要做什么**：打开看一遍。**这份文档决定了后面要做哪些事**，任何遗漏或歧义都会沿着流水线放大。有问题当场告诉 Claude 改；没问题就回复 "确认"。

确认后，Claude 自动进入下一步。

---

### 3.3 第二步：让 Claude 设计方案

这一步你基本是旁观者。Claude 根据上一步的需求，想清楚：

- 代码大致分几个模块？（抓取器、解析器、分组器、渲染器、CLI）
- 模块之间的接口长什么样？
- 数据在模块间怎么流动？
- 用哪些三方库？

**你会看到**：它生成 `docs/plans/2026-04-23-gh-weekly-design.md`——一份带架构图、模块职责、接口签名的设计文档，然后请你审阅。

**你要做什么**：

- 重点看 **架构图** 和 **模块职责**——结构合理吗？能读懂吗？
- 不懂的地方直接问 Claude："为什么要分成三个模块而不是两个？"
- 觉得某处不合适，提出来："抓取器应该内置缓存，你加一下"
- 满意后回复 "确认"

> 💡 **这一步不要走过场**。设计阶段的问题，在后面写代码时会用 10 倍代价暴露。

---

### 3.4 第三步：搭项目骨架

Claude 在项目目录里生成：

```
gh-weekly/
├── src/gh_weekly/        ← 你的代码会在这里
├── tests/                ← 测试会在这里
├── feature-list.json     ← 项目拆成了哪些任务
├── task-progress.md      ← 会话日志
├── RELEASE_NOTES.md      ← 变更日志
├── pyproject.toml        ← 依赖声明
├── init.sh               ← 一键装依赖
└── ...
```

最关键的是 **`feature-list.json`**——它把你的项目拆成了若干独立任务。这个周报项目大概会被拆成 5 个 feature：

| 编号 | 任务 | 状态 |
|---|---|---|
| 1 | HTTP 抓取与重试 | ⏳ 待做 |
| 2 | HTML 解析取 Top 20 | ⏳ 待做 |
| 3 | 按语言分组排序 | ⏳ 待做 |
| 4 | Markdown 周报渲染 | ⏳ 待做 |
| 5 | CLI 入口与参数 | ⏳ 待做 |

**你要做什么**：

1. 结束后**关闭当前会话**（或执行 `/clear`）

> ⚠️ **为什么要关会话**：Long-Task 的规矩是每个 feature 在全新的会话里开始，这样 Claude 的注意力集中、上下文干净。**别省这一步**——省了会导致后面代码质量下降。

---

### 3.5 第四步：逐个 feature 做完——这里是主要工作

从这里开始，你会进入一个循环：**开新会话 → 做完 1 个 feature → 关会话 → 再开新会话 → 做下一个 feature**。每个 feature 需要 **两次** 会话才能做完。

#### Feature 1 ·  会话 A：Claude 给出详细设计

你打开一个新会话，说：

> 使用 using-long-task skill

Claude 会：

1. 自动挑出第一个待做 feature（"HTTP 抓取与重试"）
2. 为它生成一份 **功能详细设计**，保存到 `docs/features/1-http-fetch-retry.md`

这份设计里有：

- 要暴露什么函数 / 类？参数、返回值、异常？
- 实现思路（伪代码级别）
- **测试清单**——应该写哪些测试用例（正常、异常、边界各几条）

**你要做什么**：

- 看一眼。对测试清单尤其注意：**这些测试覆盖得全吗？有没有你担心的场景漏了？**
- 比如你可能发现它没考虑 "HTTP 429 限流" 的情况——告诉 Claude 加上
- 满意后回复 "确认"

Claude 会告诉你：**设计完成，请开新会话继续编码**。

**你要做什么**：关会话，开新会话。

#### Feature 1 ·  会话 B：Claude 按 TDD 写代码

新会话里再说：

> 使用 using-long-task skill

Claude 会严格按照测试驱动开发（TDD）的节奏做三件事：

1. **先写测试（Red）**——按上一步的测试清单，写出所有测试，此时测试全部失败（因为还没实现）
2. **再写实现（Green）**——写出刚够让测试通过的代码，跑测试 → 全绿
3. **重构清理（Refactor）**——改善代码结构、改名、去重复，跑静态检查 → 无问题

全程你能看到：

- 每一步 Claude 做了什么
- 每次跑测试的结果（通过几个、失败几个）
- 最终代码文件和测试文件的位置

**你要做什么**：

- 中间可以不干预。有看不懂的地方问 Claude "这段代码在干嘛"
- 如果某个测试失败反复修不好，Claude 会如实告诉你并停下来——这时候要一起看，通常是需求或设计阶段埋的坑
- 结束时，Claude 会告诉你：**Feature 1 完成 ✓，请开新会话继续下一个**

此时 `feature-list.json` 里 Feature 1 的状态从 "待做" 变成了 "已完成"，`RELEASE_NOTES.md` 也多了一条记录。

#### 后面的 Feature 2 ~ 5：重复同样节奏

每个 feature 都是 **会话 A 设计 → 关会话 → 会话 B 编码 → 关会话**。

全部做完后，你的项目就有了：

- 完整可用的 `gh-weekly` 命令
- 覆盖率和变异测试都达标的测试套件
- 清晰的 `RELEASE_NOTES.md`

#### 时间预算参考

| 每个 feature | 设计会话 | 编码会话 |
|---|---|---|
| 简单（工具函数、数据结构） | 15~30 分钟 | 30~90 分钟 |
| 中等（涉及 IO、解析、状态） | 30~60 分钟 | 1~3 小时 |
| 复杂（涉及多模块协作） | 1~2 小时 | 3~6 小时 |

> 💡 **5 个 feature 一起做完**大概是一两天的工作量。如果你觉得一个个手动推进太累，看 §6 的 Auto-Loop 让它自己跑。

---

## 4. 运维场景：上线之后

项目上线，总会有新情况：用户报 bug、老板要加功能、结构越来越复杂。Long-Task 给你两种常用"上线后操作"，用起来非常简单——**写一个小的 JSON 文件告诉 Claude 发生了什么，剩下的它来处理**。

### 4.1 场景：用户报了一个 bug

**背景**：你的周报工具上线后，用户反馈："有些仓库没写主语言，结果程序直接崩了。"

**你要做的**：

**① 开新会话，把 bug 讲给 Claude 听**

用自然语言说，不用讲究格式。比如：

> 使用 using-long-task skill。我发现一个 bug：跑 `gh-weekly --limit 50` 时，如果当周热榜里有仓库没写主语言，程序会直接崩掉报 KeyError。我期望这类仓库被归到 "Other" 分组。严重程度算 Major（功能可用但会异常退出）。

你只需要尽量讲清楚：

- 现象（它做错了什么）
- 怎么触发（怎么复现）
- 你期望的正确行为
- 严重程度粗略判断：`Critical`（阻塞）/ `Major`（有大影响）/ `Minor`（有小影响）/ `Cosmetic`（外观问题）

即使你只能描述现象、说不清根因，也没关系——Claude 会自己去查。

**② Claude 会帮你整理成结构化的 `bugfix-request.json`，让你确认**

它会把你说的话整理成一份规范的缺陷报告，类似：

```json
{
  "title": "仓库没有主语言时程序崩溃",
  "description": "…",
  "severity": "Major",
  "reproduction_steps": ["…"],
  "expected": "…",
  "actual": "…"
}
```

你扫一眼："对，就这样"——回复确认，Claude 就保存它。

**③ Claude 自动进入处理流程**

它会：

- 打开项目看代码
- 按你给的复现步骤实际跑一遍，真的把 bug 复现出来
- 一步步排查到 **出错的具体代码行**（它不会猜，必须定位到位）
- 把这个 bug 作为一个新的 feature 添加到 `feature-list.json`（标记为 `bugfix` 类别，记录下根因）
- 删掉 `bugfix-request.json`（任务已登记，不需要再触发）

**接下来**：这就是一个新的 feature，按 §3.5 的套路——开新会话让它设计修复方案、再开新会话按 TDD 改代码并补上回归测试。

> 💡 **不用自己改 `feature-list.json`**。如果你直接动手加一条 bug 任务，Long-Task 不会做根因分析，修出来的是"猜的"，不是"确认的"。

---

### 4.2 场景：你要加一个新功能

**背景**：用完一段时间你想："能不能每周自动把周报发到我邮箱？"

**你要做的**：

**① 开新会话，把想加的功能讲给 Claude 听**

> 使用 using-long-task skill。我想给这个项目加一个功能：每次生成的周报自动发送到我配置的邮箱。命令行加一个 `--email` 参数指定收件人，SMTP 配置通过环境变量读取，不要硬编码。

讲清楚三件事就够了：

- **要加什么 / 改什么 / 废弃什么**（可以多条）
- **为什么要加**（可选，有助于 Claude 设计）
- **约束或偏好**（可选，比如"不要引入新的大依赖"）

**② Claude 会整理成 `increment-request.json`，让你确认**

它会把需求结构化成类似这样：

```json
{
  "scope": "新增邮件发送能力",
  "changes": [
    {"type": "add", "description": "生成的周报自动发送到配置的收件人邮箱"},
    {"type": "modify", "description": "命令行新增 --email 参数指定收件人"}
  ],
  "notes": "SMTP 配置通过环境变量读取，不硬编码"
}
```

三种变更类型：

- `add`——全新的能力
- `modify`——改现有功能
- `deprecate`——废弃某个已有功能

你确认无误，Claude 就保存并继续。

**③ Claude 自动进入处理流程**

它会：

- 打开项目大致摸一遍（知道现在 CLI 入口在哪、配置怎么读取）
- **分析影响**：这个新功能会不会改动已有的代码结构？如果会，哪些已完成的 feature 需要重新验证？
- **更新需求文档**：在 `*-srs.md` 里加上对应的新需求
- **更新设计文档**：在 `*-design.md` 里加上新模块（比如一个 `EmailDispatcher`）
- **追加新的 feature 任务** 到 `feature-list.json`
- 删掉 `increment-request.json`

**你会看到的**：

- SRS 和 Design 文档被 Claude 改过了（git log 能看到完整改动）
- `feature-list.json` 里多了几条新任务，标注着它们属于"第 1 波变更"（上线前是第 0 波）
- 如果某些老 feature 因为这次改动需要重测，它们会被重新标为"待做"

**接下来**：照常在新会话里说 "使用 using-long-task skill"——新的 feature 按 §3.5 的设计 + TDD 流程逐个做完。

> 💡 **增量改动会自动维护文档一致性**。你永远不会出现"代码加了新功能但文档没改"的情况。

---

### 4.3 场景：前后端分仓的项目

**背景**：你想做一个更大的东西——"周报管理后台"，前后端在各自独立的 git 仓里。

**目录结构**：

```
~/code/weekly-platform/        ← 这是你的工作根目录（不是 git 仓）
├── backend/                    ← 后端 git 仓
└── frontend/                   ← 前端 git 仓
```

**你要做的**：

**① 在根目录 `weekly-platform/` 启动 Claude Code**

Long-Task 会自动发现下面有两个独立 git 仓，告诉你："这是个多仓库项目，我来帮你协调。"

**② 跟它对话，把整体需求讲清楚**——和 §3.2 一样，只是视角放在 **整个平台**，不是单个仓：

> 使用 using-long-task skill。我要做一个周报管理后台。后端提供 REST API 存取周报，前端是 Vue 的管理页面。

Claude 会：

- 搞清整体需求，生成一份 **全局需求文档**（放在根目录 `docs/plans/`）
- 把全局需求 **拆分** 成"后端该做什么"和"前端该做什么"两份各自的需求文档
- 把每个仓之间的 **接口约定**（比如 REST API 的签名）写清楚，分发到两个仓里

**③ 接下来独立推进每个仓**：

```bash
cd backend && claude
# 按 §3 的主流程走：设计 → 初始化 → feature 循环

cd ../frontend && claude
# 同样的流程
```

每个仓里都已经有自己的需求文档、跨仓接口说明、参考资料，**互不干扰**。

> 💡 **什么时候才用多仓？** 只有当前后端、微服务等 **确实在各自的 git 仓里** 才用。如果你只是想把代码分文件夹组织，用单仓就行了。

---

## 5. 独立工具（非流水线）

这些 skill 不依赖 `feature-list.json`，可在任意代码库随时触发。

### 5.1 `/deep-explore` — 深度摸底

场景：接手一个陌生 Java 后端。

```
/deep-explore standard --focus architecture,api,deps --path ./backend
```

参数：
- `quick|standard|deep` — 对应探索深度（按 LOC 自动推荐）
- `--focus` — 维度子集：`architecture,dataflow,api,domain,deps,health`
- `--path` — 目标目录

产物：`docs/explore/codebase-research.md`（只读，不影响流水线）。

### 5.2 `/static-review` — 推送前静态分析

场景：Java 项目准备推送，先清零 Checkstyle 违规。

```
/static-review --tool checkstyle --max-iterations 10
```

流程：检测工具 → 扫描 → 修复 SubAgent → 重新编译 → 跑 UT → 重扫 → 直到 0 违规。

> 不会自动 commit，用户审阅修改后自己 commit。

### 5.3 `/coverage-retrofit` — 为遗留代码补 UT

场景：接手一个测试稀疏的老项目，需要达到 85% 行覆盖。

全量模式：
```
/coverage-retrofit --line-cov 85 --branch-cov 75
```

增量模式（只管比较基线后变化的代码）：
```
/coverage-retrofit --branch main --line-cov 85
```

其他参数：`--files list`、`--path dir`、`--max-iterations N`、`--dry-run`。

流程：基线测量 → `long-task-coverage-fix` SubAgent 写测试 → 重测 → 循环至达标。

### 5.4 `/mutation-retrofit` — 补变异测试

```
/mutation-retrofit --mutation 80 --branch main
```

> **前置**：需先完成 `/coverage-retrofit`（或 `--skip-coverage-check` 强跳，不推荐）。

---

## 6. Auto-Loop — 不间断推进多 feature

手动逐会话推进 10+ 个 feature 效率低。`scripts/auto_loop.py` 外层循环自动开新会话。

### 6.1 基本用法

```bash
# 标准运行（默认参数）
python scripts/auto_loop.py feature-list.json

# 限制最大迭代次数
python scripts/auto_loop.py feature-list.json --max-iterations 30

# 两次会话间冷却
python scripts/auto_loop.py feature-list.json --cooldown 10

# 自定义触发语
python scripts/auto_loop.py feature-list.json --prompt "使用 using-long-task skill"
```

### 6.2 OpenCode 用户

```bash
python scripts/auto_loop_opencode.py feature-list.json --model anthropic/claude-sonnet-4-6
```

### 6.3 终止条件

- 所有活跃 feature `status: passing`
- 达到 `--max-iterations`
- 连续 N 次迭代 `feature-list.json` 无变化（卡死检测）
- 用户 Ctrl+C

每次迭代的会话日志写在 `logs/session-*.md`，方便事后复盘。

---

## 7. 故障排查

### 7.1 说 "使用 using-long-task skill" 后 Claude 没动、或走错阶段

多数是 `feature-list.json` 结构不对（比如你之前手动改过它）。最简单的办法：

- 让 Claude 自检："帮我检查 `feature-list.json` 的状态，有没有问题"
- 它会告诉你哪里不对，并给出修复建议

### 7.2 Claude 说 "这个 feature 的需求有歧义，无法继续设计"

这意味着需求 / 设计文档里对这块的描述不清楚。Claude 会列出它需要澄清的问题：

- **直接回答这些问题**，它会重新设计
- 如果问题比较多、触及整体设计，用 §4.2 的 **增量流程**（建一个 `increment-request.json`）系统地更新需求和设计

### 7.3 编码阶段测试反复通不过

Claude 会自己重试；如果它告诉你"尝试多次仍失败，需要你介入"：

- 通常是设计阶段埋的坑：接口定义不合理、或者测试用例本身有矛盾
- 不要粗暴地让它"跳过测试"或"降低要求"——这只是把问题往后推
- 正确做法：问 Claude "哪里卡住了？是实现问题还是设计问题？"，它会给出诊断

### 7.4 修 bug 时 Claude 说 "无法定位根因"

Claude 规矩是：**不允许靠猜去修 bug**，必须定位到具体代码位置才会动手。

- 它会告诉你缺什么信息（比如完整的错误日志、更精确的复现条件）
- 补充信息后再让它试
- 实在复现不出来，可以降级：先让它写一个"能复现出这个现象"的测试用例，再基于这个测试去调查

### 7.5 装完 Claude Code 里找不到 long-task skill

- 在 Claude Code 里执行 `/plugin list`，看 `long-task@longtaskforagent` 是否在列表里并且是启用状态
- 如果没在列表：回到 §1 重新跑一次安装脚本
- OpenCode 用户：重启一次 OpenCode

### 7.6 多次会话后感觉 Claude "忘了很多东西"

这是正常的——Long-Task 设计上就是每次会话独立，信息靠项目里的文档（`feature-list.json`、`docs/plans/*.md`、`task-progress.md`）承接。

- 不要靠"在会话里反复强调" 让 Claude 记住。**让它看文档**
- 你可以直接让它 "读一下 task-progress.md，告诉我现在在哪一步"

---

## 8. 速查卡

### 8.1 一分钟上手

```bash
# 1. 安装（Claude Code）
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/claude-code/install.sh | bash
# 在 Claude Code 中：
/plugin install long-task@longtaskforagent

# 2. 新建项目目录
mkdir my-project && cd my-project && git init

# 3. 启动 Claude Code，说：
#    "使用 using-long-task skill。我想做一个 XXX"

# 4. 按 skill 提示进行：SRS → Design → Init → Feature 循环
```

### 8.2 信号文件

| 文件 | 作用 | 怎么产生 |
|---|---|---|
| `bugfix-request.json` | 触发缺陷修复流程 | 你口述 bug，Claude 整理并保存，你确认即可 |
| `increment-request.json` | 触发新增 / 修改 / 废弃需求流程 | 你口述新需求，Claude 整理并保存，你确认即可 |

> 信号文件被 skill 处理后会自动删除（commit 历史保留）。**不要自己手写这两个 JSON**，让 Claude 帮你写。

### 8.3 常用脚本

```bash
# 查看当前阶段
python scripts/phase_route.py --json

# 检查剩余工作量
python scripts/count_pending.py feature-list.json --json

# 校验 feature-list.json
python scripts/validate_features.py feature-list.json

# 获取工具命令（测试 / 覆盖率 / 变异）
python scripts/get_tool_commands.py feature-list.json --json

# 解析 feature 设计文档路径
python scripts/feature_paths.py design-doc --feature 3 --must-exist
```

### 8.4 几个不要做的事

| 不要 | 为什么 |
|---|---|
| 自己手动编辑 `feature-list.json` 的状态 | Claude 依赖这个文件判断进度，你改乱了下次会跑错 |
| 在同一个会话里做完设计又继续写代码 | 两件事分开做，Claude 的注意力才专注，代码质量才稳定 |
| 为了"快点过关"要求 Claude 跳过测试或重构 | 你在给自己挖坑，半年后维护时会还债 |
| 还没修完 bug 就删 `bugfix-request.json` | 删了 Claude 就不处理了；让它自己删才对 |

### 8.5 参考资料

- `README.md` / `README_EN.md` — 项目总览
- `CLAUDE.md` — 仓库工作规范（本指导书的真源）
- `skills/using-long-task/references/architecture.md` — 架构细节
- `skills/long-task-tdd-shared/references/iron-law.md` — TDD 铁律
- `docs/templates/` — SRS / Design / 延后清单模板
- 样例项目：<https://github.com/suriyel/githubtrends>

---

**至此，从安装到上线、从热修到增量的完整操作闭环已覆盖。** 有任何 skill 未在本指导书出现，通常意味着它是流水线内部的 SubAgent，用户不直接触发。
