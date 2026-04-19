---
name: long-task-st
description: "Use when all features in feature-list.json are passing - run comprehensive system testing before release, aligned with IEEE 829 and ISTQB best practices"
---

# 系统测试 —— 发布前的跨特性与系统级校验

在所有特性实现且通过后，运行跨特性与系统级测试。每特性的 ST 测试用例（功能、边界、UI、安全）已在每个 Worker 循环中通过 `long-task-feature-st` 执行。本阶段聚焦逐特性测试**无法**覆盖的内容：跨特性交互、多特性 E2E 工作流、系统级 NFR 校验、兼容性，以及探索性测试。

**开始时宣告：** "I'm using the long-task-st skill. All features are passing — time for cross-feature system testing."

**核心原则：** 逐特性 ST 测试用例证明单个特性满足其需求。系统测试证明整体跨特性边界协同工作。

<HARD-GATE>
禁止跳过任何适用的测试类别。"Go" 裁决需要来自适用于本项目的**每一个**类别的证据。"大概可以" 不是证据。
</HARD-GATE>

<HARD-GATE>
手工测试升级：当 Step 3-8 中任何测试场景无法自动化（需物理设备、人类视觉判断或外部人为动作）时，用 `AskUserQuestion` 向人类呈现测试并收集其裁决。

格式：
```
Manual Verification Required: {test description}
Category: {ST step — e.g., Integration, E2E, NFR, Compatibility}
What to verify: {specific check with acceptance criteria}
Expected result: {threshold or criterion from SRS}

Please report: PASS or FAIL on first line, then what you observed.
To skip: respond SKIP {reason}
```

- 解析响应：首行 `PASS`/`FAIL`/`SKIP`。若无法解析，重提示一次；然后记为 `BLOCKED`。
- 将结果记为 ST 报告中的 `MANUAL-PASS` 或 `MANUAL-FAIL`。
- `MANUAL-FAIL` 的严重性等同自动化失败——对 Critical/Major 项阻塞 Go 裁决。
- `SKIP {reason}` 记为带原因的 `BLOCKED`（不静默跳过）。
</HARD-GATE>

## Checklist

你必须为每个 step 创建一个 TodoWrite 任务并按顺序完成：

### 1. ST 就绪关卡

```bash
python scripts/check_st_readiness.py feature-list.json
```

- 所有特性都 `"status": "passing"` 且根 `current == null` —— 如有 failing 或 current 非空，停止本 ST，开新会话让 `using-long-task` 按 `current` 路由到对应 phase skill
- SRS 文档存在（`docs/plans/*-srs.md`）；Design 文档存在（`docs/plans/*-design.md`）
- 适用时加载 config 值——按 `long-task-guide.md` 激活环境；若项目使用基于文件的 config，在运行检查前确保其已加载
- **启动 ST 运行时服务**：使用 `env-guide.md` 中的命令启动服务（CLI/仅库项目则跳过）
  - 阅读 `env-guide.md` —— 使用 "Start All Services" 节；每条命令都带输出重定向运行：
    ```bash
    [start command] > /tmp/svc-<slug>-start.log 2>&1 &
    sleep 3
    head -30 /tmp/svc-<slug>-start.log
    ```
  - 从首 30 行抽取 PID 和端口
  - 运行 `env-guide.md` 的 "Verify Services Running" 健康检查——必须响应后才能继续
  - 若启动失败：查看日志，诊断根因；尝试更正命令（端口冲突、环境变量、缺失依赖）；一旦确认可用命令，**更新 `env-guide.md`**（Services 表 + Start 命令）；若修复需 >2 步，抽取到 `scripts/svc-<slug>-start.sh` 并从 env-guide.md 引用
  - **记录信息**：在 `task-progress.md` 记录 PID 与端口——Step 11 清理必需
- 读取 `feature-list.json` —— 注意 `tech_stack`、`quality_gates`、`constraints[]`、`assumptions[]`
- 读取 SRS —— 抽取所有 FR-xxx、NFR-xxx、IFR-xxx、CON-xxx 需求；读取 Stakeholders、User Personas 与 Glossary 节
- 读取 Design 文档 —— 抽取架构（§1）、Internal API Contracts（§4）、External Interfaces（§5 若存在）；测试框架与阈值读 `feature-list.json.tech_stack` + `.quality_gates`；依赖版本读包清单文件
- 若存在 UI 特性：读取 UCD 文档（`docs/plans/*-ucd.md`）
- 读取 `task-progress.md` —— 会话历史上下文

### 2. ST Plan

创建 `docs/plans/YYYY-MM-DD-st-plan.md`，包含：

#### 2a. 测试范围

| 类别 | 适用条件 | 跳过条件 |
|----------|-------------|-----------|
| 回归 | 始终 | 永不 |
| 集成 | 2+ 特性共享数据/状态/API | 单一孤立特性 |
| E2E 场景 | SRS 有多步用户工作流 | 纯库/工具项目 |
| 性能 | SRS 有 NFR-xxx 带响应时间 / 吞吐量目标 | 无性能 NFR |
| 安全 | 安全 NFR 或项目处理用户输入 / 认证 / 外部数据 | 孤立的离线工具 |
| 兼容性 | SRS 指定平台 / 浏览器 / runtime 目标 | 单平台 CLI 工具 |
| 探索性 | 始终 | 永不 |

#### 2b. 需求可追溯性矩阵（RTM）

把**每一条** SRS 需求映射到 ST 测试方式。引用 Worker Step 9 的逐特性测试用例文档：

```markdown
| Req ID | Requirement | Feature ST Status | System ST Category | ATS Categories | Test Approach | Priority |
|--------|-------------|-------------------|--------------------|----------------|---------------|----------|
| FR-001 | ... | docs/test-cases/feature-1-xxx.md (PASS) | E2E | FUNC,BNDRY,SEC | Scenario: ... | High |
| NFR-001 | ... | docs/test-cases/feature-5-xxx.md (PASS) | Performance | PERF | Load test: ... | Critical |
| IFR-001 | ... | N/A (cross-feature) | Integration | FUNC,BNDRY | Contract test: ... | High |
```

每个 FR-xxx、NFR-xxx、IFR-xxx 都必须出现在 RTM 中。没有测试方式的需求 = **缺口**。

若任何需求需手工校验（来自 ATS `自动化可行性` 列或 Feature-ST 手工用例），在 RTM 中含 `Manual` 列：

```markdown
| Req ID | ... | Manual | Test Approach | Priority |
|--------|-----|--------|---------------|----------|
| FR-010 | ... | Yes: visual-judgment | Manual visual verification via AskUserQuestion | High |
```

**ATS 合规关卡**（若 ATS 文档存在）：
```bash
python scripts/check_ats_coverage.py docs/plans/*-ats.md --feature-list feature-list.json --strict
```
必须 exit 0。任何 ATS 类别缺口 = 继续前需解决的 finding。

#### 2c. 入口 / 出口标准

**入口**（必须全部为真）：所有特性 passing、环境已准备、所有必需 config 齐备。

**出口**（Go 裁决必须全部为真）：所有回归/集成/E2E 测试通过、所有 NFR 阈值在实测证据下达标、无 Critical 或 Major 缺陷未关闭、RTM 显示 100% 需求覆盖、**ATS 类别合规已校验**（如 ATS 存在：`check_ats_coverage.py --strict` exit 0）。

#### 2d. 风险驱动的优先排序

1. 关键路径——核心用户工作流，业务影响最大
2. 集成边界——跨特性数据流、API 契约
3. NFR 阈值——性能、安全（技术风险最高）
4. 边界情况——边界条件、错误恢复
5. 兼容性——平台/浏览器差异

### 3. 回归测试

1. 使用 `long-task-guide.md` 的命令运行项目完整测试套件

2. 核对所有测试通过——零失败、零错误
3. 核对项目级行/分支覆盖率阈值达标
4. 检查新出现的警告、弃用通知、依赖冲突
5. 任何失败 → **停止** —— 这是回归。继续前先诊断。

**记录：** 总测试数、通过/失败、line/branch 覆盖率 vs 阈值。

### 4. 集成测试

测试跨特性交互。阅读 `references/st-recipes.md` 获取语言相关模式与 real-vs-contract 测试分类。

**术语**（详见 st-recipes.md §1）：
- **Contract test** = 基于 mock，校验调用签名 —— 辅助性，不充分
- **Integration test** = 真实服务，校验实际数据流 —— 每边界必需

<HARD-GATE>
每个内部跨特性边界**必须**至少有一个真实集成测试（真实 DB、真实 HTTP、真实文件系统）。Contract 测试（mock）**不**满足此关卡。

对外部 2/3方件 边界：若 `required_configs` 或环境中有测试凭据，写真实集成测试。否则用 contract 测试并在 Mock Authorization 列记录原因。
</HARD-GATE>

对每对共享数据、状态或 API 边界的特性：
- **数据流**：Feature A 产出数据 → Feature B 消费 → 端到端校验数据完整性；共享 DB/状态 一致性
- **API 契约**：模块间内部 API 调用——校验请求/响应 schema；错误传播；版本兼容
- **依赖链**：走 `feature-list.json` 的 `dependencies[]` 图；按依赖顺序校验特性工作；测试每条依赖边

**分类表**（写入 ST plan）：

| Boundary | Features | Type | Real Tests | Contract Tests | Mock Authorization | Status |
|----------|----------|------|-----------|----------------|-------------------|--------|
| shared DB | F1 → F3 | Internal | 2 | 1 | N/A | PASS |
| REST API | F2 → F4 | Internal | 1 | 0 | N/A | PASS |
| GitHub API | F5 → ext | External | 1 | 0 | N/A (user provided token) | PASS |
| Stripe API | F7 → ext | External | 0 | 2 | User confirmed no sandbox | PASS |

**每个内部边界最低要求：**
- ≥1 条通过真实共享资源读写的真实测试
- 若真实服务无法启动：边界 **BLOCKED**（不是 skipped）—— 通过 env-guide.md 诊断

**外部边界协议：**
1. 检查 `required_configs` 与环境中的测试凭据/沙箱环境
2. 如可用 → 写真实集成测试（优先）
3. 如不可用 → 用 contract 测试；在 Mock Authorization 列记录原因

把集成测试写到 `tests/integration/` 或 `tests/st/`。标记每条测试：
```python
# Integration: Feature A → Feature B (shared DB) [Real]
def test_feature_a_data_consumed_by_feature_b():
    ...

# Contract: Feature C → External API [Contract]
def test_external_api_response_shape():
    ...
```

运行并逐边界记录结果。

### 4b. 全流水线冒烟测试

E2E 场景测试前，校验至少一条贯穿整个系统的完整数据流路径。这捕捉逐边界测试遗漏的集成 bug。

<HARD-GATE>
至少 **一个** 冒烟测试必须仅用真实服务演练一条真实的端到端数据路径（input → processing → storage → retrieval → output）。不使用 mock。
</HARD-GATE>

1. 识别**关键路径** —— 穿越系统的单条最重要数据流（例如 "创建实体 → 存储 → 查询 → 返回"）
2. 写一条冒烟测试，要求：
   - 从外部输入开始（API 调用、CLI 命令、UI 动作）
   - 经过所有中间处理
   - 持久化到真实存储（如适用）
   - 读出并校验已持久化结果
   - 仅使用真实服务—— 无 mock
3. 在运行中的服务（Step 1 启动）上运行冒烟测试
4. 若失败 → **Critical** 级缺陷 —— 在继续到 E2E 前先诊断

**伸缩：**
| 项目规模 | 冒烟测试 |
|---|---|
| 微型 (1-5 特性) | 1 条关键路径 |
| 小型 (5-15) | 1-2 条关键路径 |
| 中型 (15-50) | 2-3 条关键路径 |
| 大型 (50+) | 3-5 条覆盖主要子系统的关键路径 |

**记录：** 冒烟测试描述、使用的真实服务、通过/失败、执行证据。

### 5. 跨特性 E2E 场景测试

测试来自 SRS 验收标准、**跨多个特性** 的完整用户工作流。单特性场景已由逐特性 ST 测试用例覆盖。

对 SRS Stakeholders 中的每个用户角色：
- 抽取**跨越特性边界**的主要工作流
- 创建跨多特性的 E2E 场景（happy path + 错误恢复）
- 对每个场景：设置初始状态 → 执行工作流 → 校验中间与最终状态 → 清理

对每个场景：设置初始状态、逐步执行、校验中间状态与最终结果、清理。

**UI E2E 测试**（仅存在 `"ui": true` 特性时）：使用 Chrome DevTools MCP 进行基于浏览器的 E2E 校验。

把 E2E 测试写到 `tests/e2e/` 或 `tests/st/`。运行并记录结果。

### 6. 系统级 NFR 校验

逐特性 NFR 检查已在 feature-level ST 处理。本步骤聚焦**系统级聚合** NFR 测量。对每个 SRS 中的 NFR-xxx，用**实测证据**校验——非估算。

- **性能**：在预期负载下测量 p50/p95/p99；吞吐量；内存/CPU/磁盘 I/O。基准工具见 `references/st-recipes.md`。记录：测量值 vs SRS 阈值。
- **安全**：输入校验审计（SQL、XSS、命令注入、路径穿越）；认证/会话/权限提升；依赖漏洞扫描（npm audit、pip-audit 等）；OWASP Top 10 checklist；代码/日志中的密钥。记录：逐项 PASS/FAIL 并附证据。
- **可扩展性**（若 SRS 有负载目标）：在 1x、2x、5x 预期负载下运行负载测试；测量降级曲线；识别瓶颈。
- **可靠性**：错误处理产出有意义消息；依赖不可用时优雅降级；错误条件下无数据损坏。

### 7. 兼容性测试

若 SRS 未指定平台/浏览器/runtime 目标则跳过。

- **跨浏览器**（仅 UI）：在每个目标浏览器运行 E2E 场景；通过截图校验视觉一致性；检查浏览器特定 console 错误
- **跨平台**：在每个目标 OS 构建/安装/运行完整测试套件；校验平台相关行为（文件路径、行结束符、权限）
- **Runtime 版本**：对每个目标 runtime 版本运行完整测试套件；校验无版本相关 API 问题

记录：逐平台/浏览器 PASS/FAIL 矩阵。

### 8. 探索性测试

基于 charter 的时间盒会话，找脚本测试遗漏的问题。

每个主要特性区域创建一个 charter：
```
Charter: Explore [feature area]
         with [technique: stress/edge/abuse/workflow variation]
         to discover [bugs/usability issues/undocumented behavior]
```

对每个 charter：时间盒 15-30 分钟；跟随直觉——尝试意外输入、异常序列、快速交互；实时记录观察（Bug / Question / Note 附严重性）。

若某探索性 charter 识别出的问题需物理设备访问或超出 Chrome DevTools MCP 能校验的人类视觉判断：用 `AskUserQuestion` 带 charter 上下文收集测试者的发现。

所有 charter 结束后：整合发现；与 RTM 交叉比对需求缺口；把新缺陷加入 triage 队列。

### 9. 缺陷 Triage

若 Step 3-8 中发现任何缺陷：

| 严重性 | 定义 | 动作 |
|----------|-----------|--------|
| **Critical** | 系统崩溃、数据丢失、安全泄露 | 阻塞发布——立即修 |
| **Major** | 核心工作流破坏、NFR 阈值未达 | 阻塞发布——发布前修 |
| **Minor** | 影响非核心，有 workaround | 记录——现在修或延后（与用户共同决定）|
| **Cosmetic** | 视觉/文本问题，无功能影响 | 记录——延后到下一版 |

**逃逸分析** —— 对每个缺陷，分类它本应在何处被捕获：

| Escaped From | 含义 | 系统性动作 |
|---|---|---|
| Unit | TDD 本应捕获 | 添加单元测试；评审类似缺口的覆盖 |
| Feature-ST | 逐特性验收测试缺口 | 通过 increment skill 添加测试用例 |
| Mock-Leaked | mock 测试通过但真实集成失败 | 用真实集成测试替换 mock |
| Integration | 跨特性边界未测 | 为边界添加集成测试 |
| Spec | 需求模糊或缺失 | 通过 increment skill 澄清 SRS |

在缺陷表中包含 "Escaped From" 列：

| # | Severity | Escaped From | Category | Description | Status | Fix Ref |
|---|----------|-------------|----------|-------------|--------|---------|

**修复循环**（若存在 Critical/Major 缺陷）：
1. 在 `feature-list.json` 将受影响特性标 `"status": "failing"`；若需要返回某个阶段修复，写根 `current = {"feature_id": N, "phase": "tdd"|"design"}`；在 `task-progress.md` 记录
2. 开新会话；`using-long-task` 会按 `current` 路由到对应 phase skill（通常 `long-task-work-tdd`）进行修复
3. 修复后：重跑受影响的 ST 测试类别（不跑完整 ST）
4. 回到 triage —— 重复至无 Critical/Major 剩余

对 Minor/Cosmetic 延后：在 ST 报告记录严重性、描述、workaround。

### 10. ST 报告

撰写前核对：每个 SRS 需求出现在 RTM；每个 NFR 有满足阈值的实测值；每个适用类别都有结果；所有缺陷都已分类。

生成 `docs/plans/YYYY-MM-DD-st-report.md`，含以下节：
1. **Executive Summary** —— 1-3 句：整体质量评估与发布建议
2. **Requirements Traceability Matrix** —— 完整 RTM 表，含 Feature ST 状态、System ST 类别、ATS 类别、结果、证据；覆盖计数（X/Y 需求，Z%）；列出任何缺口；含 ATS 合规检查结果（`check_ats_coverage.py --strict` 输出）
3. **Test Execution Summary** —— 表：类别、跑过数、通过、失败、跳过、备注（Step 2a 的每个类别一行）；含最终行 **Real Test Cases** —— 聚合来自所有特性 ST 文档（`docs/test-cases/feature-*.md` Real Test Case Execution Summary 表）的 `Real` 测试用例计数（总数 / 通过 / 失败）；若存在任何手工测试用例，含 **Manual Test Cases** 行——聚合所有 Feature-ST 文档与 System-ST 执行步骤的手工测试用例计数（总数 / MANUAL-PASS / MANUAL-FAIL / BLOCKED）
4. **Defect Summary** —— 表：严重性、**escaped from**、类别、描述、状态（fixed/deferred）、修复引用；总数；未关闭 Critical/Major 数（Go 必须为 0）；若 ≥2 个缺陷共享同一 "Escaped From" 源，在 Risk Assessment 标为系统性缺口
5. **Quality Metrics** —— 行/分支覆盖率 vs 阈值、总测试数；真实测试用例：总数 / 通过 / 失败（从所有 `docs/test-cases/feature-*.md` Real Test Case Execution Summary 表聚合）
6. **Risk Assessment** —— 剩余风险附可能性、影响、缓解
7. **Recommendations** —— 发布后监控、已知限制、改进建议

### 11. Persist

- Git commit ST 工件（`docs/plans/*-st-plan.md`、`docs/plans/*-st-report.md`、测试文件）
- 校验：`python scripts/validate_features.py feature-list.json`
- **清理（强制）**：停止 Step 1 启动的服务
  - 阅读 `env-guide.md` "Stop All Services" 节 —— 按 PID kill（首选，从 `task-progress.md`）或按端口（兜底）
  - 若 stop 命令失败：尝试端口兜底；一旦确认可用命令，**更新 `env-guide.md`** Stop 命令；若需 >2 步，抽取到 `scripts/svc-<slug>-stop.sh` 并从 env-guide.md 引用
  - 运行 `env-guide.md` "Verify Services Stopped" 命令 —— 端口必须无响应
  - **记录清理结果**：在 `task-progress.md` 记录清理状态

### 12. Verdict

基于出口标准决定 Go/No-Go 裁决。在 ST 报告记录：
- **Go**：所有出口标准达成、无未关闭 Critical/Major 缺陷、RTM 100% 覆盖
- **Conditional-Go**：Minor/Cosmetic 缺陷已延后、所有关键路径已校验
- **No-Go**：存在未关闭 Critical/Major 缺陷、NFR 阈值未达、或 RTM 缺口

裁决时 `MANUAL-FAIL` 结果与自动化 `FAIL` 同等对待。经手工测试发现的 Critical/Major 缺陷阻塞 Go 裁决，与自动化相同。

### 13. Finalize（Go/Conditional-Go 时）

若裁决为 Go 或 Conditional-Go：
- 调用 `long-task:long-task-finalize`
- 等待完成后再结束会话

若 No-Go → 跳过（循环回 Worker 修复；Finalize 在最终 Go 后运行）。

## 按项目规模伸缩 ST

| 项目规模 | 特性数 | ST 深度 |
|---|---|---|
| 微型 (1-5) | 1-5 特性 | 回归 + 轻量级集成 + 1 冒烟测试 + 2-3 E2E 场景 + 1-2 探索性 charter |
| 小型 (5-15) | 5-15 特性 | 完整回归 + 每共享边界集成 + 1-2 冒烟测试 + 每角色 E2E + NFR 抽查 + 3-5 charter |
| 中型 (15-50) | 15-50 特性 | 完整回归 + 系统化集成 + 2-3 冒烟测试 + 全面 E2E + 完整 NFR + 兼容性矩阵 + 5-10 charter |
| 大型 (50+) | 50+ 特性 | 完整回归 + 集成测试套件 + 3-5 冒烟测试 + E2E 自动化 + 完整 NFR 负载测试 + 完整兼容性 + 安全审计 + 10+ charter |

## 关键规则

- **就绪关卡先行** —— 有 failing 特性时永不开始 ST
- **证据导向裁决** —— 每个 PASS 都必须有实测证据；"看着还行" 不是证据
- **RTM 完备性** —— 每个 SRS 需求都必须出现在 RTM；缺口即 finding
- **NFR 阈值是硬关卡** —— 实测值必须满足 SRS 阈值，"接近就行" 不行
- **缺陷严重性不可协商** —— Critical/Major 缺陷阻塞发布；无例外
- **所有 bug 都必须修** —— ST 测试中发现的任何 bug（前端、后端、集成）都**必须**在发布前修复。没有 "不是我的代码" 的豁免。
- **修后重测** —— 永不假定修复有效；重跑受影响的测试类别
- **真实测试用例必须通过** —— ST 报告 Real Test Cases 行中任何失败的 `Real` 测试用例都是阻塞 Go 裁决的未解决缺陷
- **探索性测试强制** —— 脚本测试不能找到所有问题
- **Verdict 前先出 ST 报告** —— 先记录再决定；永不跳过报告
- **ST 期间无新特性** —— ST 按原样测试已集成系统
- **ATS 类别具约束力** —— 若 ATS 存在，`check_ats_coverage.py --strict` 必须 exit 0；每个必需类别都必须有测试覆盖
- **每边界需真实集成测试** —— 内部边界需 ≥1 真实测试；外部边界在有凭据时使用真实测试；不可用时用带成文原因的 contract 测试
- **全流水线冒烟测试强制** —— E2E 场景前至少校验一条真实端到端数据路径
- **缺陷逃逸分析强制** —— 每个缺陷都必须按 "Escaped From" 源分类以识别系统性测试缺口
