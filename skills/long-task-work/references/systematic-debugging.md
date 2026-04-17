# 系统性调试（Systematic Debugging）

## 铁律

**没有根因分析之前不得修复。**

绝不基于猜测应用修复。始终先将 bug 追到根因，然后修复该根因。

## 何时适用

- TDD Green 或 Refactor 阶段的测试失败
- smoke 测试期间检测到回归
- Chrome DevTools MCP 功能测试期间的运行时错误
- Bootstrap 阶段的构建或环境失败
- 实现期间出现的任何意料之外的行为

## 四阶段调试流程

### 阶段 1：根因调查

**目标**：理解**发生了什么**以及**发生在哪里**。

1. **收集错误证据**：
   - 读取完整错误信息（不要只看第一行）
   - 记录堆栈跟踪 — 哪个文件、哪一行、哪个函数
   - 记录触发错误的确切命令 / 操作

2. **可靠复现**：
   - 是否能稳定触发该错误？
   - 最小复现用例是什么？
   - 独立出现还是仅与其他特性组合时出现？

3. **检查近期变更**：
   - `git diff` — 自上次正常以来有何变化？
   - `git log --oneline -10` — 做了哪些提交？
   - 该错误在你当前变更之前是否就存在？

4. **追踪数据流**：
   - 沿失败输入从入口点跟到错误位置
   - 必要时记录中间值
   - 识别实际行为在何处偏离期望行为

### 阶段 2：模式分析

**目标**：理解**为什么**会发生。

1. **寻找可用示例**：
   - 是否存在行为正常的相似代码？
   - 正常路径与异常路径有何不同？

2. **检查依赖**：
   - 所有依赖是否可用且版本正确？
   - 上游 API 或 schema 是否发生变更？
   - 环境变量 / 配置是否正确？

3. **比较上下文**：
   - 本地正常但测试失败（或反之）？
   - 一个输入正常但另一个失败？
   - 是否是时序相关（竞态条件）？

### 阶段 3：假设与验证

**目标**：形成**唯一**假设并验证它。

1. **形成单一假设**：
   - "错误发生是因为 Y 期望 X 非空而此时 X 为 null"
   - 具体化 — 模糊的假设导致模糊的修复

2. **设计最小验证**：
   - 能确认或推翻假设的最小改动是什么？
   - 是否可以添加针对性的断言或日志？

3. **测试假设**：
   - 仅做诊断性改动
   - 运行失败的测试
   - 假设是否成立？

4. **若假设为错**：
   - 记录所学
   - 带着新信息返回阶段 1
   - **不要**尝试随机修复

### 阶段 4：实现

**目标**：以经过验证的方案修复根因。

1. **先为该 bug 写一条失败测试**：
   - 该测试应与原始 bug 因同一原因失败
   - 用于防止回归

2. **实现单一、针对性的修复**：
   - 仅修复阶段 3 确认的根因
   - 避免"顺手改一改"的无关改动

3. **验证修复**：
   - 新测试通过
   - 所有既有测试仍通过
   - 原始错误不再出现

4. **若 3 次尝试后修复仍不成功**：
   - 停下重新考虑根因
   - 可能你识别错了
   - 考虑向用户求助或请求上下文

## 支持技术

### 根因回溯

沿调用栈向后追溯 bug：

```
Error at line N in file F
  ← Called from line M in file G
    ← Called from line K in file H
      ← Root cause: incorrect value set at line K in file H
```

从错误处向后找到错误值被引入的位置。

### 纵深防御

修复根因后，考虑在多层添加校验：

```
Layer 1: Input validation     → Reject bad data early
Layer 2: Function preconditions → Assert expected state
Layer 3: Output verification   → Confirm correct results
```

只添加有目的的校验 — 不要为不可能的状态添加防御性代码。

### 基于条件的等待（用于时序 bug）

用条件轮询替代任意 timeout：

```
# BAD: sleep(5) and hope the server is ready
# GOOD: Poll until condition is met or timeout expires

wait_for("Expected text", timeout=10000)
```

对非 UI 时序 bug：
```python
# Poll with backoff
for attempt in range(max_retries):
    result = check_condition()
    if result:
        break
    time.sleep(backoff * attempt)
else:
    raise TimeoutError("Condition not met")
```

### 测试污染检测

当某条测试单跑通过但与套件一起跑失败时，说明另一条测试污染了共享状态。

二分查找法：
1. 失败测试与套件前半部分一起跑 → 仍失败？
2. 是 → 污染者在前半；继续二分
3. 否 → 污染者在后半；继续二分
4. 重复直到找到单条污染测试
5. 修复该污染者（清理其共享状态）

## 红旗（停下重新审视）

| Red Flag | What It Signals | Correct Response |
|----------|----------------|-----------------|
| "Let me just try this quick fix" | 跳过了根因分析 | 回到阶段 1 |
| "It's probably X, let me change it" | 无证据猜测 | 形成可验证的假设 |
| "I'll add a try/catch to suppress the error" | 掩盖症状而非修复原因 | 找到并修复根因 |
| "Let me restart everything and try again" | 寄希望于问题消失 | 先可靠复现 |
| "This worked before, not sure what changed" | 需要查看 git diff | 与上次已知正常态对比 |
| Third fix attempt still failing | 识别了错误的根因 | 停止，从阶段 1 重新评估 |

## 调试决策树

```
Error encountered
  │
  ├─ Can reproduce? ─── No ──→ Add logging, try again
  │                              (make it reproducible first)
  ├─ Yes
  │
  ├─ Recent change caused it? ─── Yes ──→ git diff, focus on changes
  │
  ├─ No / Unknown
  │
  ├─ Trace to root cause ──→ Found cause? ─── Yes ──→ Write test → Fix → Verify
  │
  ├─ No
  │
  ├─ Find working example ──→ Compare differences ──→ Form hypothesis
  │
  └─ Hypothesis holds? ─── Yes ──→ Write test → Fix → Verify
                          No ──→ Record learning → Return to trace
```
