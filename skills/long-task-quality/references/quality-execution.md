# Quality Gates — SubAgent 执行参考

你是 Quality Gates 执行 SubAgent。严格遵循以下规则。完成后，使用本文件底部的 **Structured Return Contract** 返回结果。

---

# Quality Gates & Verification（关卡与验证）

四道顺序关卡（Gate 0 → 0.5 → 1 → 2），在特性被标记为 "passing" 之前**必须**全部通过。无捷径，无例外。

## 铁律

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

若本条消息中未运行验证命令，则不得声称它通过。


**工具 / 环境错误处理**：
1. **读取**错误输出 — 识别具体的工具或环境问题
2. **诊断**根因（工具未安装、环境未激活、路径错误、配置缺失）
3. **尝试修复** — 必要时运行 `init.sh`，或安装缺失工具
4. **重跑**一次
5. **若仍失败** → 将 Verdict 设为 BLOCKED，附错误详情
6. **绝不跳过** — 测试是硬关卡；不允许绕过

## Gate 0：真实测试验证（Real Test Verification）

Gate 0 在 coverage 之前运行。当测试套件全是 mock 时，覆盖率数字毫无意义。

### Step 1：运行校验脚本

```bash
python scripts/check_real_tests.py feature-list.json --feature {current_feature_id} --require-for-deps
```

`--require-for-deps` 标志会交叉检查特性的 `required_configs[]` 中是否含有连接串类键（URL、HOST、PORT 等）。若有，真实测试是**强制**的 — 纯函数豁免被阻止。

读取脚本输出：
- **FAIL**（无真实测试） → GATE 0 FAIL，返回 TDD Red 撰写真实测试
- **FAIL** 且 "has external dependencies" → 见下文 Step 1b
- **WARN**（发现 mock 警告） → 进入 Step 2
- **PASS**（发现真实测试，无 mock 警告） → 进入 Step 3

### Step 1b：依赖阻塞 FAIL 的处理

若 Gate 0 FAIL 原因含 "has external dependencies but no real tests"：
1. 这**不是**代码问题 — 是基础设施 / 配置问题
2. 运行：`python scripts/check_configs.py feature-list.json --feature {current_feature_id}`
3. 若配置缺失 → 返 `status: blocked`，追加 blocker `[ENV-ERROR] Feature #{id} requires external dependencies ({config_names}) but configs are not provided | Suggested: none | Q: please provide the listed configs in .env or env-guide §3`。主 agent 按 `skills/using-long-task/references/approval-revise-loop.md` 组装 AskUserQuestion 收集缺失值。
4. 若配置齐备但服务未运行 → 阅读 `env-guide.md`，启动服务，重跑 Gate 0
5. 对有外部依赖的特性**绝不**无真实测试就继续
6. 对含连接串 `required_configs[]` 的特性**绝不**声称纯函数豁免

### Step 2：LLM 采样评审（仅 WARN）

对脚本标记的每条 mock 警告：
1. 阅读对应真实测试函数体
2. 判断：mock 是否针对该真实测试声称要验证的**主要依赖**？
   - 是 → 真实测试无效；重写、重跑脚本
   - 否（mock 在某个不相关的辅助服务上） → 视为合法，继续

### Step 3：运行真实测试（含 skip 检测）

使用 `env-guide.md` §3（`long-task-guide.md` 中的 Real Test Convention 章节指向它）的运行命令单独执行真实测试：
- 所有真实测试**必须通过**
- 任何 FAIL → GATE 0 FAIL，修复后重跑
- **Skip 检测（强制）**：读取测试 runner 的完整输出。若**任一**真实测试被报告为 `skipped`、`pending`、`disabled` 或 `ignored` — 视为 GATE 0 FAIL。真实测试必须执行，不得跳过。
  - 常见 skip 标志：pytest `s` 标记或 "skipped" 计数 > 0；JUnit `@Disabled`；Jest/Vitest "skipped"/"pending" 计数 > 0；gtest "DISABLED_" 前缀
  - 若 skip 源于基础设施缺失 → 服务 / DB 未运行。阅读 `env-guide.md`，启动服务，重跑。
  - 若 skip 源于环境 guard（`if not env: return`） → 改写测试为断言失败（反模式 #16）。真实测试必须高声失败，不得静默通过。

### 所需证据
```
Gate 0 Result:
- Script output: [paste check_real_tests.py output]
- Mock warning review: [for each warning — primary dep / auxiliary service]
- Real test execution: passed N / failed N / skipped N
- Skip verdict: 0 skipped (or: N skipped → FAIL, reason and fix applied)
- Gate 0: PASS/FAIL
```

### Gate 0 FAIL 时
```
GATE 0 FAIL — [reason]
Required action:
1. [Fix missing real tests / rewrite mock-using real tests / set up test infrastructure]
2. Re-run TDD Red verification (real tests must FAIL first, then PASS after Green)
3. Return to Gate 0
Do NOT skip Gate 0 and proceed to coverage.
```

## Gate 0.5：SRS Trace Coverage（需求追溯）

**动机**：覆盖率 100% 不等于"需求被测试锚定"。SRS 验收准则若在迭代中修改而测试未同步补齐，单看覆盖率会静默放行。本关卡强制每个 `srs_trace` 中的需求 ID 都在本 feature 的测试工件（文件名 / 函数名 / docstring / 注释 / 断言字符串）中字面出现。

### Step 1：运行脚本

```bash
python scripts/check_srs_trace_coverage.py {feature_list_path} \
  --feature {feature_id} \
  --test-files {feature_test_files}
```

- `{feature_test_files}` 是 TDD 阶段为本 feature 写入/修改的测试文件清单。传入 `--test-files` 将作用域限定为这些文件；不传则脚本按 `feature_ref_pattern` 自行推导。
- 脚本使用 hyphen↔underscore 等价规则：`FR-001` 会匹配 `test_fr_001_...`、`fr_001`、`FR_001` 与 `FR-001`。
- 需要非字面别名（如 `@srs-login`）时，在 feature-list.json 的 feature 对象添加：
  ```json
  "srs_trace_aliases": { "FR-001": ["@srs-login", "legacy-login-id"] }
  ```

### Step 2：解读退出码

| Exit | 含义 | 动作 |
|------|------|------|
| 0 | 全部 `srs_trace` ID 均有字面命中 | Gate 0.5 PASS，进入 Gate 1 |
| 1 | 至少 1 个 ID 未命中 | Gate 0.5 FAIL，取 `--json` 输出的 `per_feature[0].uncovered_fr_ids`；返回 `status: fail` |
| 2 | 输入错误（feature-list 缺失 / feature id 不存在 / 指定的 test-files 不存在）| 视为 blocked；返回 `status: blocked` |

### Step 3：FAIL 处理

Gate 0.5 FAIL 不回到 TDD Red —— 已有测试在运行，只是**没有锚定 FR-ID**。动作顺序：

1. 读 `uncovered_fr_ids` 列表；
2. 在现有测试里为每个未覆盖 ID 追加字面引用（推荐：写入最相关 test 的 docstring 或注释；或重命名函数为 `test_fr_001_*` 形式）；
3. 重跑脚本（Gate 0.5）；
4. 若 3 次重试仍 FAIL（例如 `srs_trace` 与本 feature 实际测试范围不匹配），返 `status: fail` + `evidence: { uncovered_fr_ids: [...] }` 并由主 agent 以 Clarification Addendum 分流至用户：是扩测还是修订 `srs_trace`。

### Step 4：豁免

feature 的 `srs_trace` 为空时，脚本输出中会记录 "no srs_trace declared"，Gate 0.5 自动 PASS。这对应 `category=bugfix` 尚未完成根因追溯或 srs_trace 尚未回填的早期状态。orchestrator 层应另有断路（不允许空 `srs_trace` 进入 quality），此关卡不承担该职责。

### 所需证据

```
Gate 0.5 Result:
- Script exit: 0 | 1 | 2
- srs_trace count: N
- Uncovered IDs: [FR-xxx, ...] (empty if PASS)
- Gate 0.5: PASS/FAIL
```

## Gate 1：Coverage（覆盖率）

TDD Green 之后（全部测试通过），运行覆盖率工具。

1. **运行**覆盖率工具，采用**静默执行**（按 `env-guide.md` §2 激活环境；从 `env-guide.md` §3 读取 coverage 命令）：
   ```bash
   <coverage-cmd> > /tmp/cov-$$.log 2>&1; echo $? > /tmp/cov-$$.exit
   ```
2. **先读** `/tmp/cov-$$.exit` 的退出码：
   - exit 0 → 仅提取覆盖率摘要行（通常 `grep -E "TOTAL|Coverage|line rate|branch rate" /tmp/cov-$$.log | tail -5`）。**不要**倾倒完整文件。
   - 非零 → 提取最后 100 行；诊断工具错误
3. **验证**：行覆盖率 >= `[thresholds] line_coverage`，分支覆盖率 >= `[thresholds] branch_coverage`
4. **若覆盖率 FAIL**（低于阈值但工具成功运行）：从摘要识别未覆盖行 / 分支 → 增加测试 → 对这些路径重跑 TDD 循环。修复后重跑时，仅作用域到变更的测试文件 — 不要全量。
5. **若 PASS**：进入 Gate 2

**所需证据：**
```
- Coverage summary showing line % and branch %
- Line coverage >= threshold
- Branch coverage >= threshold
- List of uncovered lines (if any, with justification)
```

## Gate 2：Verify & Mark（验证并标记）

将特性标记为 "passing" 前的最后一道关卡。

```

1. IDENTIFY → 从 `env-guide.md` §3 获取 test 与 coverage 命令（单一事实源）

2. RUN → 执行每个命令（在本消息内新鲜执行 — 不复用先前缓存）

3. READ → 逐命令读取输出：
   - 检查退出码（PASS/FAIL）
   - 从输出统计 test 通过 / 失败 / 跳过 数量
   - 从输出读取覆盖率百分比

4. VERIFY → 所有输出是否确证声明？
   - 全部测试通过（0 failures）？
   - 覆盖率 >= 阈值？

5. THEN CLAIM → 现在才：
   - 带证据报告结果

若任一步失败 → STOP。**不要**声称 passing。先修复问题。
```

## 红旗词汇

若你发现自己用了下面任一说法，STOP 并重新验证：

| Red Flag | Required Action |
|----------|----------------|
| "should pass" | 现在就运行测试 |
| "probably works" | 现在就执行并验证 |
| "seems to be working" | 取得具体测试输出 |
| "I believe this is correct" | 运行验证命令 |
| "this looks good" | 运行自动化测试 |
| "based on the implementation" | 测试验证行为，而非代码 |
| "the tests should be green" | 运行测试并读取输出 |
| "I've verified"（未展示输出） | 展示实际输出 |
| "coverage is probably fine" | 现在就运行覆盖率工具 |

## 工具配置

若本项目技术栈尚未配置覆盖率工具，阅读 `skills/long-task-quality/coverage-recipes.md` 获取各语言（Python、Java、JavaScript、TypeScript、C、C++）的完整配置说明。

## 验证时机一览

| Event | What to verify |
|-------|---------------|
| TDD Green + Refactor 之后 | `check_real_tests.py` 输出 PASS，所有真实测试通过 |
| TDD Green 之后 | 完整测试套件输出 |
| Gate 0.5 | `check_srs_trace_coverage.py --feature {id}` 返回 PASS；每个 `srs_trace` ID 至少 1 处字面命中 |
| Coverage Gate 之后 | 覆盖率报告（line% + branch%） |
| TDD Refactor 之后 | 完整测试套件（仍通过） |
| 标记 "passing" 之前 | 上述全部（Gate 0.5 已对 srs_trace 做字面锚定验证）|
| git commit 之前 | 完整测试套件（不提交损坏代码） |

## 反模式

| Anti-Pattern | Correct Approach |
|---|---|
| 写完代码未跑测试就标记 "passing" | 运行测试、读取输出，再标记 |
| 相信重构未破坏任何东西 | 每次重构后重跑完整套件 |
| 只读测试输出的摘要行 | 阅读完整输出 |
| 会话开始不做复检 | 始终对 passing 特性做冒烟 |
| 跳过 Gate 0，"覆盖率会抓到 mock 问题" | 覆盖率对 mock vs real 无感。Gate 0 始终先跑。 |
| 脚本报 WARN 却不审阅直接继续 | 必须审阅每条 mock 警告判断其是否针对主要依赖。 |

---

## Structured Return Contract

与 `skills/using-long-task/references/structured-return-contract.md` 中的统一契约对齐。严格按此格式返回：

```markdown
## SubAgent Result: long-task-quality

**status**: pass | fail | blocked
**artifacts_written**: [file paths created or modified during gate execution, relative to project root]
**next_step_input**: {
  "coverage_line": <actual line coverage %>,
  "coverage_branch": <actual branch coverage %>,
  "all_tests_pass": true | false,
  "test_count": <total test count>,
  "srs_trace_coverage": {
    "total": <len(srs_trace)>,
    "covered": <number of FR-IDs literally referenced in feature test files>,
    "uncovered_fr_ids": [<FR-IDs with zero test references; empty if PASS>]
  }
}
**blockers**: [one-sentence strings if status=blocked; otherwise empty array]
**evidence**: [
  "Gate 0 (Real Test): PASS/FAIL — N real tests executed, 0 skipped",
  "Gate 0.5 (SRS Trace): C/N FR-IDs covered; uncovered=[...]",
  "Line coverage: N% (threshold X%)",
  "Branch coverage: N% (threshold X%)"
]

### Metrics (extension — for task-progress.md)
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Gate 0 (Real Test) | PASS/FAIL | PASS | PASS/FAIL |
| Gate 0.5 (SRS Trace) | C/N covered | N/N | PASS/FAIL |
| Line Coverage | N% | ≥X% | PASS/FAIL |
| Branch Coverage | N% | ≥X% | PASS/FAIL |

### Risks (extension — omit if empty)
<!-- Output even on PASS. Omit this section only if the list is empty. -->
| # | Category | Location | Description |
|---|----------|----------|-------------|
| 1 | Coverage \| Dependency | file:line or metric name | [one-sentence explanation] |

<!-- Category rules:
  Coverage — any metric within +5% of its threshold, or known uncovered boundary
  Dependency — third-party library with a known security patch or breaking change not yet applied -->

### Issues (extension — only if fail or blocked)
| # | Severity | Description |
|---|----------|-------------|
| 1 | Critical/Major/Minor | [what failed, what was attempted] |
```

**重要**：**不要**在 feature-list.json 中将 feature 标记为 "passing" — 那是 orchestrator 的职责。在上述契约中只报告结果。
