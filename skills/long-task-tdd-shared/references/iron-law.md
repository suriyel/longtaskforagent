# TDD 铁律与测试规则

## 铁律

```
NO IMPLEMENTATION CODE WITHOUT A FAILING TEST FIRST
```

先写代码再补测试 → 删掉代码，重新开始。无例外。

## 规则 R1：类别覆盖

每个测试标注 `MAIN/subtag` 分类：

- `MAIN ∈ {FUNC, BNDRY, SEC, INTG}`
- `MAIN=BNDRY` 时 subtag 必取最小子集 `{range, existence, time}`（对应 CORRECT 的 Range/Existence/Time 维度）
- 其余 CORRECT 维度 `{conformance, ordering, reference, cardinality}` 为推荐 subtag，不强制

| MAIN | 测试内容 | 示例 subtag |
|------|---------|------------|
| FUNC | 正常操作 / 已知失败 | `happy`、`error` |
| BNDRY | 边界、空值、极值、时序 | `range`、`existence`、`time` |
| SEC | 注入、授权、越权 | `injection`、`authz` |
| INTG | 真实外部依赖（见 R5） | `db`、`http`、`fs` |

某分类不适用时在测试文件头明确声明：`# SEC: N/A — internal utility, no user-facing input`。

## 规则 R2：负面测试比例 ≥ 40%

```
negative_test_count / total_test_count >= 0.40
```

"负面" 操作定义（任一命中）：
- 测试体含 `pytest.raises` / `assertRaises` / 断言异常类型
- 断言 HTTP 4xx / 5xx 状态码
- 断言返回空集 / None / 拒绝 / 失败状态
- 测试名含 `_error_` / `_rejects_` / `_invalid_` / `_fails_`

## 规则 R3：低价值断言 ≤ 20%

```
low_value_count / total_assertion_count <= 0.20
```

低价值模式（严禁独立出现，可作辅助断言之一）：
- 完全没有断言
- `assert x is not None` / `assertNotNull(x)` 且不检查内容
- `assert isinstance(x, T)` 且不检查行为
- `assert len(x) > 0` 且不验证元素
- `assert "k" in d` 且不检查 `d["k"]` 的值
- `assert bool(x)` / 仅真值性
- 纯导入断言：`from m import X; assert X`

## 规则 R4：错误实现挑战（WRONG_IMPL 留痕）

每个测试函数**紧邻**（签名下方第一行注释）至少 1 行：

```python
# WRONG_IMPL: <一句话描述哪种错误实现会被此测试捕获>
```

示例：
```python
def test_discount_applies_member_rate():
    # WRONG_IMPL: 返回硬编码 0 元折扣；把 member_rate 和 guest_rate 搞反
    ...
```

设想来源：feature.md 的边界决策表 / 错误处理表（§接口契约子表）已预分析可能的错误实现；直接引用。

## 规则 R5：测试层级 — UT + 集成双层

| 层级 | 目的 | Mock 策略 | 最低要求 |
|------|------|----------|---------|
| 单元 `# [unit]` | 单个函数/类 | 仅系统边界（HTTP/时钟/FS/第三方 API）；内部逻辑用真实或内存实现 | ≥1 个使用真实内部依赖 |
| 集成 `# [integration]` | 真实基础设施协作 | 主依赖不可 Mock — 真实测试库 / 真实服务 / 真实 FS | 每个涉及外部系统的功能 ≥1 个 |

集成测试豁免：功能完全无外部依赖（纯计算）时，在测试文件头声明 `# [no integration test] — pure function, no external I/O`。

每个测试用 `# [unit]` 或 `# [integration]` 标注。

## 规则 R6：AAA 结构注释必填

每个测试函数体内必须含三段注释：

```python
def test_add_item_updates_cart():
    # WRONG_IMPL: add 不更新内部计数；add 把 quantity 写成 0
    # arrange
    cart = Cart()
    # act
    cart.add("apple", 2)
    # assert
    assert cart.contains("apple")
    assert cart.quantity_of("apple") == 2
```

## 规则 R7：LLM 退化陷阱自检

| 陷阱 | 判决 |
|------|------|
| 同义反复 `assert result == compute(x)` | 断言具体期望值，禁用产品代码重算 |
| 快乐路径偏向 | 错误/边界先行，happy 最后（由 R2 40% 守底） |
| 过度 mock | 见 `testing-anti-patterns.md` Anti-Pattern 3 |
| 测试镜像实现（复制 if-else） | 按接口契约黑盒写；不读实现代码 |
| 断言漂移（红→改断言） | 只能改实现或删除重写，不改断言迁就实现 |
| Mock 行为即断言（`mock.called`）| 断言 mock 被调用的**参数和次数**，或外部副作用；详见 `testing-anti-patterns.md` Anti-Pattern 1 |

## 规则 R8：测试代码禁用反射

作用域仅测试代码。产品代码（Spring/Jackson/ORM 等框架内部）反射使用不在此限。

| 语言 | 测试代码禁用 |
|------|-------------|
| Java | `java.lang.reflect.*`、`setAccessible(true)`、PowerMock 全家桶（`@PrepareForTest`、`Whitebox.setInternalState`、`MemberModifier`、反射路径的 `mockStatic`）|
| Python | `getattr(obj, '_private')`、`obj.__dict__['_x']`、对下划线属性 `setattr` |
| TS | `(obj as any)._foo`、`@ts-ignore` 绕过可见性 |

替代：构造器/setter 注入、通过公共 API 测试、把需测逻辑提炼为协作者类的公共方法。

## 规则 R9：不针对私有成员写 UT（Chicago school）

禁测：
- Java `private` 方法 / 字段
- Python `_foo` / `__foo` 约定私有成员
- TS `private` / 绕过可见性断言

容忍（**同作用域测试**是关键）：
- Java `package-private` 方法在同包测试
- Python 模块级 `_helper` 在同模块测试
- TS 未 export 辅助在同模块测试

判据：某段私有逻辑复杂到觉得"值得独立测" ⇒ 设计气味 ⇒ 提炼为协作者类（或独立模块）的公共方法，在该协作者的 UT 里测。

## 度量与自证

- R1–R9 由 TDD Red / Refactor SubAgent 在返回契约中走读自证（Summary 段简述对照结果）
- 负面测试比例（R2）、低价值断言比例（R3）等数值目标为**建议**，非机械化门禁
- 测试质量的**客观兜底**：`/coverage-retrofit`（行 + 分支覆盖率）与 `/mutation-retrofit`（变异分）—— 二者独立于 TDD 主链路，按需运行

完整反模式目录见 `testing-anti-patterns.md`。
