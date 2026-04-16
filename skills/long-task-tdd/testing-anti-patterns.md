# 测试反模式

## 目的

常见测试错误目录，这些错误会产生虚假信心。编写或审查测试质量时参考此文档。

## 反模式目录

### 1. 测试 Mock 行为而非真实行为

**症状**：测试通过但功能实际不工作。

**示例（错误）**：
```python
def test_user_login(mock_db):
    mock_db.get_user.return_value = User(id=1, name="test")
    result = login("test", "password")
    mock_db.get_user.assert_called_once_with("test")  # Testing the mock!
```

**原因**：你在测试代码是否正确调用了 mock，而非登录是否真正有效。

**修复**：尽可能使用真实依赖测试（测试数据库、内存存储）。仅 Mock 无法控制的外部服务。

### 2. 向生产代码添加仅测试方法

**症状**：生产代码中存在 `_test_helper()`、`get_for_testing()` 等方法。

**原因**：生产代码不应感知测试。仅测试方法可能在生产中被调用，造成维护负担和潜在 bug。

**修复**：通过公共接口测试。如果必须通过后门才能测试，说明设计需要重构。

### 3. 不理解依赖就盲目 Mock

**症状**：每个测试 Mock 所有东西，且不确定每个 mock 代表什么。

**原因**：过度 Mock 使测试脆弱（实现变更即失败）且无意义（测试 mock 接线而非行为）。

**修复**：
- 在 Mock 之前理解依赖
- 在边界处 Mock（HTTP 调用、文件系统、时钟），而非内部层
- 对复杂依赖优先使用 fake（内存实现）而非 mock

### 4. 测试实现细节

**症状**：重构行为不变时测试却失败。

**示例（错误）**：
```python
def test_sort():
    result = sort_list([3, 1, 2])
    # Testing that quicksort was used (implementation detail)
    assert mock_quicksort.called
```

**修复**：测试输出，而非计算方式：
```python
def test_sort():
    result = sort_list([3, 1, 2])
    assert result == [1, 2, 3]
```

### 5. 非确定性测试

**症状**：测试时过时不过。

**常见原因**：
- 依赖当前时间/日期
- 无种子的随机值
- 异步代码中的竞态条件
- 测试间共享状态
- 对外部服务的网络调用

**修复**：控制所有非确定性来源。使用固定时间戳、有种子的随机数、正确的异步处理、测试隔离和 mock 网络。

### 6. 不会失败的测试

**症状**：无论实现如何，测试总是通过。

**示例（错误）**：
```python
def test_something():
    try:
        result = do_thing()
        assert result is not None
    except:
        pass  # Swallowing the failure!
```

**修复**：始终先执行 TDD Red — 如果实现前测试就通过，说明测试有问题。

### 7. 单个测试验证过多

**症状**：一个测试有 20+ 个断言覆盖多个行为。

**原因**：失败时无法知道哪个行为出错，增加调试难度。

**修复**：每个测试一个行为。使用描述性测试名称描述被测试的单一行为。

### 8. 测试间共享可变状态

**症状**：测试单独运行通过，一起运行失败。

**原因**：一个测试修改了另一个测试依赖的共享状态。

**修复**：每个测试自行 setup 和 teardown。使用新的 fixture、数据库事务或隔离的测试容器。

### 9. 无断言测试

**症状**：测试运行了代码但不断言任何有意义的结果。

**示例（错误）**：
```python
def test_create_user():
    create_user("test", "test@email.com")
    # No assertion! Just checking it doesn't throw.
```

**修复**：断言可观察的结果：
```python
def test_create_user():
    user = create_user("test", "test@email.com")
    assert user.name == "test"
    assert user.email == "test@email.com"
```

### 10. 复制粘贴测试套件

**症状**：测试被复制且仅有微小变化，使套件难以维护。

**修复**：对变体使用参数化测试。将共享 setup 提取到 fixture。但避免过度抽象 — 测试应无需跳转即可阅读。

### 11. 用无断言测试刷覆盖率

**症状**：覆盖率数字高但测试的断言弱或无断言。

**示例（错误）**：
```python
def test_process_data():
    process_data(sample_input)  # 100% line coverage, 0% verification
```

**原因**：执行代码路径但不验证正确性会产生虚假信心。即使函数返回垃圾数据，测试也不会失败。

**修复**：每个测试必须断言可观察的结果。变异测试可暴露此问题 — 如果变异体存活，说明测试实际未检查结果。

```python
def test_process_data():
    result = process_data(sample_input)
    assert result.status == "success"
    assert result.count == 42
```

### 12. 忽略存活的变异体

**症状**：变异分数低于阈值但功能仍被标记为"passing"。

**原因**：存活的变异体是测试无法捕获的 bug。如果将 `>` 改为 `>=` 而无测试失败，说明边界逻辑未被测试。

**修复**：对每个存活的变异体：
- **真实缺口**：添加能杀死它的测试
- **等价变异体**：记录为何变更产生相同行为（如 `# equivalent mutant: condition is always true due to precondition on line X`）
- **绝不忽略**：每个存活者必须被处理（修复或记录）

### 13. 对未测试代码运行变异测试

**症状**：在达到覆盖率阈值前运行变异测试。许多变异体显示"no coverage"。

**原因**：对未覆盖代码的变异测试产生大量误报存活者且浪费时间 — 根本没有测试能杀死变异体。

**修复**：始终先通过覆盖率门禁再运行变异测试。先覆盖率，后变异。

### 14. 低价值断言（存在性/类型/导入测试）

**症状**：测试断言存在性、类型或导入成功 — 这些只有在语言运行时本身出问题时才会失败，而非实现有 bug。

**示例（全部错误）**：

```python
# BAD: Testing that a function returns something (not WHAT it returns)
def test_get_user():
    result = get_user(1)
    assert result is not None

# BAD: Testing that import works
def test_import():
    from mymodule import MyClass
    assert MyClass is not None

# BAD: Testing type instead of behavior
def test_create_user():
    result = create_user("Alice", "alice@example.com")
    assert isinstance(result, User)

# BAD: Testing that a list has items (but not WHICH items)
def test_list_users():
    result = list_users()
    assert len(result) > 0

# BAD: Testing that a dict has a key (but not WHAT value)
def test_get_profile():
    result = get_profile(1)
    assert "name" in result

# BAD: Testing truthiness instead of value
def test_validate():
    result = validate_email("test@example.com")
    assert bool(result)

# BAD: Testing that no exception is raised (without checking result)
def test_process():
    result = process_data(sample)  # No assertion on result at all
```

**危害**：
- 只要实现返回*任何东西*就通过，不管返回什么
- 用零缺陷发现能力膨胀覆盖率和测试数量
- 变异测试不一定能捕获所有这些 — 某些变异保留类型/存在性
- 排挤有意义的断言，对测试套件质量产生虚假信心

**"错误实现"测试**：对每个断言问：*"哪种错误实现不会被此测试捕获？"* 如果答案是"几乎任何错误实现" → 该断言是低价值的。

示例：`assert result is not None` — 返回 `User(name="WRONG", email="WRONG")` 的函数通过此测试。返回 `42` 的函数通过此测试。返回 `""` 的函数通过此测试。它只捕获一种失败：返回 `None`。

**修复 — 断言具体的可观察结果**：

```python
# GOOD: Assert specific values
def test_get_user():
    result = get_user(1)
    assert result.name == "Alice"
    assert result.email == "alice@example.com"

# GOOD: Assert specific items in collection
def test_list_users():
    result = list_users()
    assert len(result) == 3
    assert result[0].name == "Alice"

# GOOD: Assert specific response structure AND content
def test_get_profile():
    result = get_profile(1)
    assert result["name"] == "Alice"
    assert result["role"] == "admin"

# GOOD: Assert specific boolean outcome for specific input
def test_validate():
    assert validate_email("test@example.com") is True
    assert validate_email("not-an-email") is False

# GOOD: Assert specific error for specific invalid input
def test_create_user_invalid():
    with pytest.raises(ValidationError, match="email is required"):
        create_user(name="test", email="")

# GOOD: Assert specific state change
def test_process():
    result = process_data(sample)
    assert result.status == "completed"
    assert result.processed_count == 42
```

**量化规则**：任何测试套件中，低价值断言与总断言的比例不得超过 **20%**：

```
low_value_count / total_assertion_count <= 0.20
```

低价值断言模式（用于计数）：
- `assert x is not None` / `assert x is None`（测试默认值而非行为时）
- `assert isinstance(x, SomeType)`
- `assert len(x) > 0`（不检查内容）
- `assert "key" in dict`（不检查值）
- `assert bool(x)` / `assert x`（仅真值性）
- `from module import X; assert X is not None`（导入测试）
- 无断言的测试（已被反模式 #9 覆盖）

**与其他反模式的关系**：比 #9（无断言测试）和 #11（刷覆盖率）更具体。测试可以有断言但仍是低价值的 — 如果断言仅验证存在性/类型。变异测试（#12）能捕获部分但非全部低价值断言 — 20% 比例规则在编写测试时提供额外检查。

## 快速参考：测试编写检查清单

标记测试完成前：

- [ ] 测试在无实现时失败（TDD Red 已验证）
- [ ] 测试名称描述被测试的行为
- [ ] 测试有有意义的断言（不只是"无错误"）
- [ ] 测试是确定性的（稳定通过/失败）
- [ ] 测试是独立的（不依赖其他测试的状态）
- [ ] 测试测试行为，而非实现细节
- [ ] 未向生产代码添加仅测试方法
- [ ] Mock 在边界处，而非内部层
- [ ] 无低价值断言（None 检查、isinstance、import、len>0、key-in-dict、真值性）
- [ ] 低价值断言比例 <= 总断言的 20%
- [ ] 每个断言对可能的错误实现会失败（"错误实现"测试）
