# 系统化调试

## 铁律

**未经根因调查，禁止进行任何修复。**

永远不要基于猜测进行修复。始终追溯 bug 的根因，然后修复该根因。

## 适用场景

- TDD Green 或重构阶段的测试失败
- 测试过程中检测到回归
- 功能测试中的运行时错误
- 引导阶段的构建或环境故障
- 实现过程中的任何意外行为

## 四阶段调试流程

### 阶段 1：根因调查

**目标**：理解发生了什么（WHAT）以及在哪里发生（WHERE）。

1. **收集错误证据**：
   - 阅读完整的错误消息（不仅是第一行）
   - 记录堆栈跟踪 -- 哪个文件、哪一行、哪个函数
   - 记录触发错误的确切命令/操作

2. **可靠复现**：
   - 能否稳定触发错误？
   - 最小复现用例是什么？
   - 是单独发生还是仅在与其他功能一起时发生？

3. **检查近期变更**：
   - `git diff` -- 上次正常后改了什么？
   - `git log --oneline -10` -- 做了哪些提交？
   - 在当前变更之前错误就存在吗？

4. **追踪数据流**：
   - 从入口点到错误位置跟踪失败的输入
   - 必要时记录中间值
   - 找出实际行为与预期行为的分歧点

### 阶段 2：模式分析

**目标**：理解为什么（WHY）会发生。

1. **寻找正常工作的示例**：
   - 有类似但正常工作的代码吗？
   - 正常路径和异常路径之间有什么不同？

2. **检查依赖**：
   - 所有依赖是否可用且版本正确？
   - 上游 API 或 schema 是否发生了变化？
   - 环境变量/配置是否正确？

3. **比较上下文**：
   - 本地正常但测试中失败（或反之）？
   - 某个输入正常但另一个输入失败？
   - 是否与时序有关（竞态条件）？

### 阶段 3：假设与验证

**目标**：形成一个假设并验证它。

1. **形成单一假设**：
   - "错误发生是因为 Y 期望 X 非空时 X 为 null"
   - 要具体 -- 模糊的假设导致模糊的修复

2. **设计最小测试**：
   - 能确认或否定假设的最小变更是什么？
   - 能否添加一个有针对性的断言或日志？

3. **验证假设**：
   - 仅做诊断性变更
   - 运行失败的测试
   - 假设是否成立？

4. **如果假设错误**：
   - 记录学到的东西
   - 带着新信息回到阶段 1
   - 不要尝试随机修复

### 阶段 4：实施

**目标**：用经过验证的方案修复根因。

1. **为 bug 编写一个失败的测试**：
   - 测试应因与原始 bug 相同的原因而失败
   - 这可以防止回归

2. **实施单一的、有针对性的修复**：
   - 仅修复阶段 3 中识别的根因
   - 避免"顺便改一下"的变更

3. **验证修复**：
   - 新测试通过
   - 所有现有测试仍然通过
   - 原始错误不再发生

4. **如果 3 次尝试后修复仍失败**：
   - 停下来重新思考根因
   - 可能识别错了根因
   - 考虑向用户寻求帮助或上下文

## 辅助技术

### 根因追踪

沿调用栈反向追踪 bug：

```
Error at line N in file F
  ← Called from line M in file G
    ← Called from line K in file H
      ← Root cause: incorrect value set at line K in file H
```

从错误处反向追踪，找到错误值的引入位置。

### 纵深防御

修复根因后，考虑在多个层次添加验证：

```
Layer 1: Input validation     → Reject bad data early
Layer 2: Function preconditions → Assert expected state
Layer 3: Output verification   → Confirm correct results
```

仅添加有实际意义的验证 -- 不要为不可能的状态添加防御性代码。

### 基于条件的等待（时序 bug）

用条件轮询替代固定超时：

```
# BAD: sleep(5) and hope the server is ready
# GOOD: Poll until condition is met or timeout expires

wait_for("Expected text", timeout=10000)
```

对于非 UI 时序 bug：
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

当一个测试单独运行通过但在整个套件中运行时失败，说明另一个测试正在污染共享状态。

二分查找法：
1. 将失败测试与前半部分套件一起运行 -> 仍然失败？
2. 如果是 -> 污染源在前半部分；继续二分
3. 如果否 -> 污染源在后半部分；继续二分
4. 重复直到找到单个污染测试
5. 修复污染源（清理其共享状态）

## 危险信号（停下来重新思考）

| 危险信号 | 它意味着什么 | 正确做法 |
|----------|-------------|---------|
| "让我快速试一下这个修复" | 跳过了根因分析 | 回到阶段 1 |
| "大概是 X，让我改一下" | 没有证据的猜测 | 形成可验证的假设 |
| "我加个 try/catch 来抑制错误" | 隐藏症状而非修复根因 | 找到并修复根因 |
| "让我重启所有东西再试一次" | 期望问题自行消失 | 先可靠复现 |
| "之前是正常的，不确定改了什么" | 需要检查 git diff | 与上次已知正常状态对比 |
| 第三次修复尝试仍然失败 | 识别了错误的根因 | 停下来，从阶段 1 重新评估 |

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
