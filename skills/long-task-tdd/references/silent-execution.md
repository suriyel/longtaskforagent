# 静默执行协议

TDD Red / Green / Refactor 三阶段运行测试、覆盖率、静态分析时统一采用本协议：命令输出重定向到 `/tmp`，按退出码决策，**绝不**把完整日志倾倒到主上下文。

## 命令包装

```bash
<cmd> > /tmp/<slug>-$$.log 2>&1; echo $? > /tmp/<slug>-$$.exit
```

`<slug>` 用能区分阶段的短标签：`ut` / `green` / `refactor` / `static` 等。

## 退出码决策表

| 阶段 | exit = 0 | exit != 0 |
|------|----------|-----------|
| **TDD Red**（测试应失败） | **错误**：实现已存在或断言过弱 → 重写失败的那一条测试 | **预期**：取 `tail -30 /tmp/<slug>-$$.log` 确认失败原因是 `ImportError` / `AttributeError` / 预期值上的 `AssertionError` 之类 |
| **TDD Green**（测试应通过） | **预期**：**不倾倒日志**，直接继续 | **错误**：取 `tail -100 /tmp/<slug>-$$.log` + `grep -E "FAIL\|ERROR\|Exception" /tmp/<slug>-$$.log` 诊断 |
| **Refactor**（测试保持绿；静态分析应 0 违规） | **预期**：**不倾倒日志** | 取 `tail -30`；静态分析时额外 `grep -E "error\|warning"` 提取违规项 |

## 修复后重跑协议

**不要**重跑整个测试套件。仅按名称重跑失败的测试，使用项目的过滤语法：

| 栈 | 过滤语法 |
|----|---------|
| Python / pytest | `pytest path::test_name` |
| Java / Maven | `mvn -Dtest=ClassName#methodName test` |
| Java / Gradle | `gradle test --tests "ClassName.methodName"` |
| TypeScript / vitest | `npx vitest run path -t "name"` |
| TypeScript / jest | `npx jest path -t "name"` |

**阶段末做一次全量确认**：TDD Green 结束时、Refactor 结束时各跑一次完整套件，确保无回归。

## 工具 / 环境失败

命令本身异常退出（如 `ModuleNotFoundError: pytest_cov`、`mvn: command not found`、连接测试 DB 超时）：

1. 诊断根因（测试栈未装、env 未激活、服务未启动等）
2. 视情况运行 `init.sh` / `init.ps1`，或按 `env-guide.md` 启动依赖服务
3. 重试一次仍失败 → `status: blocked` 带前缀 `[ENV-ERROR]`，evidence 附故障摘要；**绝不跳过**测试继续推进
