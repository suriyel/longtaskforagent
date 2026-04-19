---
name: long-task-tdd-red
description: "Use when dispatched by long-task-work-tdd Step 3a — write failing tests per feature design §7 test inventory, apply Rule 1-7 (category coverage, negative ratio, assertion quality, wrong-impl challenge, real tests, UI positive render)"
---

# TDD Red — 编写失败测试

针对特性详细设计中测试清单（§7）的每一行编写测试。测试**必须**失败（特性尚未实现）。

## 输入解析（SubAgent 启动时）

从 prompt 取 `feature_id` / `feature_design_path` / `feature_list_path`，随后自行完成：

1. 读 `{feature_list_path}`，取 `features[].id == feature_id` 的 feature 对象；保留 `srs_trace`、`ui`、`category`、根级 `tech_stack` / `quality_gates` / `real_test` / `required_configs`
2. Glob `docs/plans/*-srs.md` → 用 `feature.srs_trace` 定位 FR/NFR/IFR 节，作为 `{srs_section}`
3. Glob `docs/plans/*-design.md` → 按特性名 / `srs_trace` 定位 §2.N（Feature Integration Spec）与 §4.N（Internal API Contracts），作为 `{design_section}`
4. Glob `env-guide.md` → §3（测试命令）+ §4（codebase constraints）
5. 读 `{feature_design_path}` 全文（主要测试来源）

下文占位符均指向以上解析结果。

## 规约输入三源

测试由三大来源驱动：
- **特性详细设计测试清单**（`{feature_design_path}` §7）—— 主要来源；每行映射到一个或多个测试用例
- **SRS 需求章节**（`{srs_section}`）—— 完整 FR-xxx，含 Given/When/Then 验收标准、边界条件、错误路径
- **特性详细设计**（`{feature_design_path}`）—— 接口契约、实现摘要、边界条件、Test Inventory

若 `env-guide.md §4.3` 存在，遵循其中的测试文件命名规范。

## Rule 1 — 分类覆盖（硬性）

测试必须覆盖所有适用分类，用 `MAIN/subtag` 格式（与测试清单一致）：

| 分类 | 测试内容 | 示例 |
|------|---------|------|
| **FUNC/happy** | 正常操作、有效输入 | 合法登录返回 token |
| **FUNC/error** | 已知失败、无效输入 | 错误密码返回 401 |
| **BNDRY/\*** | 边界、空值、最大值、零 | 空字符串；最大长度密码 |
| **SEC/\*** | 注入、授权（如适用） | 用户名中的 SQL 注入 |
| **INTG/\*** | 与真实基础设施交互（DB、API、FS） | DB 连接失败；错误 API 端点；未处理超时 |

不适用时显式注释：
```python
# SEC: N/A — internal utility with no user-facing input
```

## Rule 2 — 负向测试比例 ≥ 40%

```
negative_test_count / total_test_count >= 0.40
```

负向测试：期望异常、错误、失败状态、边界/极端输入、未授权访问、畸形数据。

## Rule 3 — 断言质量：低价值断言 ≤ 20%

```
low_value_count / total_assertion_count <= 0.20
```

低价值断言模式（应避免）：
- 仅 `assert x is not None`
- `assert isinstance(x, SomeType)` 不校验行为
- `assert len(x) > 0` 不验证元素
- `assert "key" in dict` 不检查取值
- `assert bool(x)` / 仅真值断言
- 仅导入测试（`from module import X; assert X is not None`）

## Rule 4 — "错误实现"挑战

对每个测试反问："什么样的错误实现会被这个测试捕捉到？"若"几乎任何错误实现都还能通过" → 用更具体的断言重写。

与特性设计的交互：**§8 Data Model 的边界条件表 + §4 Interface Contract 的 Raises 列** 是事先分析过的错误条件清单——用它们做 Rule 4 的输入，而不是临时凭空想象。

设想 2-3 种错误实现（返回硬编码值 / 字段交换 / off-by-one / 跳过校验 / 返回陈旧缓存），每种情况测试都能 FAIL → 合格；多数不 FAIL → 重写。

## Rule 5 — 测试层级：必须有真实测试

每个特性**必须**同时覆盖两层：

| 层级 | 目的 | Mock 策略 | 最低 |
|-----|------|----------|------|
| **单元测试（UT）** | 单函数/类 | 仅在系统边界处 mock（外部 HTTP / 三方 API / 文件系统 / 时钟）；内部用真实或内存实现 | ≥ 1 个覆盖核心逻辑的真实依赖测试 |
| **集成测试** | 组件 × 真实基础设施 | 主依赖**不得** mock —— 用真实测试 DB / 真实服务 / 真实文件系统 | 每特性 ≥ 1 个接触外部系统的测试 |

**测试清单中 INTG/\* 行** = 集成测试主规约；每行映射一个真实集成测试。

**集成测试豁免**（纯函数、无 I/O）：测试文件显式声明：
```python
# [no integration test] — pure function, no external I/O
```

**按层级标注**：
```python
# [unit] — uses in-memory store
def test_user_validation_logic(): ...

# [integration] — uses real test database
def test_user_persisted_to_db(): ...
```

参考：`../long-task-work-tdd/references/testing-anti-patterns.md` 反模式 #1、#3。

### 测试编写顺序（强制）

1. 分析 §7 测试清单 + `{srs_section}` + `{design_section}`，识别外部依赖
2. **先写 Real Tests**（Rule 5a）—— 验证外部依赖连通性
3. 再写常规 UT（happy / error / boundary / security）
4. 运行全部测试 → 确认全部 FAIL

## Rule 5a — Real Test 独立章节（强制）

每个有外部依赖的特性测试文件必须有可识别的 real test。运行机制由 `long-task-guide.md` Real Test Convention 章节定义；以下不变量强制：

| 不变量 | 说明 |
|-------|------|
| **可发现** | `feature-list.json.real_test.marker_pattern` 可匹配，`check_real_tests.py` 可发现 |
| **可隔离运行** | 能与常规 UT 独立运行（标记过滤 / 目录分离 / 命名规范） |
| **主依赖不 mock** | Real test 主体对主要外部依赖**不得** mock；`real_test.mock_patterns` 定义可检测关键字 |
| **高价值断言** | **不得**仅"无异常"；必须断言实际返回值 / 状态变化 / 数据持久化 |
| **不得静默跳过** | 依赖不可用时**必须**失败，而非 skip / return early；使用 `assert env_var, "..."`，而非 `if not env_var: return` |
| **测试基础设施** | `.env.test` / 测试 DB / localhost 测试服务 —— 绝不用生产资源 |

**每种依赖类型至少 1 个 real test**：

| 依赖类型 | Real test 验证 |
|---------|---------------|
| 配置 / 密钥 | 从真实配置文件 / env 变量读值 |
| 数据库 / 存储 | 连真实测试 DB 执行读写 |
| 文件系统 | 读写真实文件（不仅 `tmp_path`） |
| HTTP / 网络 | 对真实测试服务器发请求 |
| 三方 SDK | 调用 sandbox / 测试环境 API |

**纯函数豁免**：测试文件显式注释 + Gate 0 由 `{design_section}` 确认无外部依赖。

**校验**：`python scripts/check_real_tests.py feature-list.json --feature {feature_id}` —— 机械扫描 + grep；FAIL 则 `status: blocked` 带前缀 `[ENV-ERROR]` 或 `[INSUFFICIENT_EVIDENCE]`。

参考：`../long-task-work-tdd/references/testing-anti-patterns.md` 反模式 #15、#16。

## Rule 6 — UI 错误检测（当 `"ui": true`）

**UI 先决条件（第一个 `[devtools]` 步骤之前）**：

1. 若开发服务器未运行，按 `env-guide.md` 启动，捕获输出：
   ```bash
   [start command from env-guide.md] > /tmp/svc-<slug>-start.log 2>&1 &
   sleep 3
   head -30 /tmp/svc-<slug>-start.log   # 提取 PID + 端口
   ```
   PID 记录到 `task-progress.md`；本会话已记录过则先跑健康检查，已活则跳过重启。
2. `navigate_page` 访问 `ui_entry` URL（或默认 localhost）
3. 连接被拒 / 页面报错（ERR_CONNECTION_REFUSED 等）→ 不要继续 UI 测试，诊断并修复；**绝不跳过** UI 校验

每个 `[devtools]` 步骤使用 EXPECT/REJECT 格式：
```
[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>
```

通过 `evaluate_script()` 执行自动化错误检测；`list_console_messages(types=["error"])` 必须返回 0 错误（除非 `[expect-console-error: <pattern>]`）。

完整检测脚本与集成流程见 `references/ui-error-detection.md`。

## Rule 7 — 正向渲染验证（当 `"ui": true`）

Rule 6 检测 UI **错误**；Rule 7 验证 UI **存在性**。

对 §7 中每行 `UI/render` 行，编写测试：

1. **触发**渲染条件（页面加载、游戏开始、状态变化）
2. `evaluate_script()` **断言正向存在**：
   - **Canvas 2D**：`getImageData()` 校验预期区域非透明像素，或校验渲染函数被以预期参数调用
   - **WebGL**：`readPixels()`（`getImageData()` 仅 Canvas 2D 可用）
   - **DOM**：`querySelector(selector)` 非空；`getBoundingClientRect()` width/height > 0；`getComputedStyle(el).display !== 'none'`
   - **SVG**：元素存在 + 非零包围盒
3. **断言内容正确性**（不仅存在性）：数量匹配状态、内容反映数据源、视觉状态与逻辑状态匹配
4. **断言交互深度**（不仅显示）：若元素设计用于交互，至少一个测试模拟交互并校验渲染输出变化
   - Canvas 游戏：模拟按键 → 校验像素变化
   - 表单：填充输入 → 校验显示值；提交 → 校验响应
   - 组件：点击/拖动 → 校验视觉状态更新
   - **已渲染但不响应的交互 = display-only 缺陷**

零错误空白 canvas **未通过** Rule 7；渲染了但忽略输入的 canvas 是 display-only 缺陷。

**最低**：§7 每行 `UI/render` ≥ 1 个正向渲染测试。

可复用校验脚本见 `references/ui-error-detection.md` § Layer 1b。

## 测试反模式（Top 5 警示）

1. **测试 mock 的行为** —— 验证真实代码，而非 mock 配置
2. **测试实现细节** —— 测行为/输出，不测内部结构
3. **不可能失败的测试** —— 每条断言必须可被证伪
4. **为覆盖率凑数** —— 无断言的测试"执行"但未验证
5. **低价值断言** —— `assertNotNull` / `isinstance` / `len>0`；最多 20%

完整 15 条见 `../long-task-work-tdd/references/testing-anti-patterns.md`。

## 运行测试

按 `../long-task-work-tdd/references/silent-execution.md` 静默执行。**本阶段 exit != 0 是预期**；exit = 0 意味着测试未真正失败（实现已存在 / 断言过弱），必须重写。

确认失败原因正确：`ImportError` / `AttributeError` / 预期值上的 `AssertionError` 均可接受。

## 进入 Green 前的校验

运行 `python scripts/check_real_tests.py feature-list.json --feature {feature_id}`：
- real test 数量 > 0（或已声明纯函数豁免）
- 无 mock 警告（或 LLM 评审确认警告不在主要依赖上）
- FAIL → 停；补齐 real test 再推进

## Structured Return Contract

严格按以下格式返回

```markdown
## SubAgent Result: long-task-tdd-red

**status**: pass | fail | blocked
**artifacts_written**: [测试文件路径，相对项目根]
**next_step_input**: {
  "feature_test_files": [测试文件路径],
  "test_count": <N>
}
**blockers**: [若 status=blocked 则列出]
**evidence**: [
  "All <N> tests FAILED as expected (sample: test_login_valid_creds → ImportError: login)",
  "Rule 1 categories: FUNC/happy, FUNC/error, BNDRY/empty, SEC/injection, INTG/db",
  "Rule 2 negative_ratio=<X> (≥ 0.40)",
  "Rule 3 low_value_ratio=<Z> (≤ 0.20)",
  "Rule 5 real_test_count=<Y> (≥ 1 or pure-function exempt)",
  "check_real_tests.py: OK"
]
```

## 阻塞 / 失败

- §7 测试清单缺失 → `blocked`，blocker 指明须先回 design
- `srs_trace` 引用的 FR 在 SRS 中不存在 → `blocked` `[SRS-MISSING]`
- SRS 验收标准模糊无法形成 Given/When/Then → `blocked` `[SRS-VAGUE]`
- SRS 与 `{design_section}` 冲突 → `blocked` `[SRS-DESIGN-CONFLICT]`
- 任一测试未 FAIL（实现已存在 / 断言过弱）→ `fail`，重写该测试
- `check_real_tests.py` FAIL → `blocked` `[ENV-ERROR]` 或 `[INSUFFICIENT_EVIDENCE]`
- 测试框架 / 工具链不可用 → `blocked` `[ENV-ERROR]`
