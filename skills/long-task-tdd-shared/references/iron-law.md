# TDD 铁律与测试规则

所有 TDD 阶段 SubAgent（Red、Green、Refactor）的共享参考。

## 铁律

```
NO IMPLEMENTATION CODE WITHOUT A FAILING TEST FIRST
```

先写代码再补测试？删掉代码，重新开始。无例外。
- 不要保留作为"参考"
- 不要在写测试时"调整"它
- 不要看它
- 删除就是删除

## 测试场景规则（硬性要求）

**规则 1：分类覆盖** — 测试必须覆盖所有适用分类（使用与 Test Inventory 相同的 `MAIN/subtag` 格式）：

| 分类 | 测试内容 | 示例 |
|------|---------|------|
| **FUNC/happy** | 正常操作、有效输入 | 有效登录返回 token |
| **FUNC/error** | 已知失败、无效输入 | 无效密码返回 401 |
| **BNDRY/\*** | 边界、空值、最大值、零值 | 空字符串；最大长度密码 |
| **SEC/\*** | 注入、授权（如适用） | 用户名中的 SQL 注入 |

当某分类不适用时，在注释中明确说明：
```python
# SEC: N/A — internal utility with no user-facing input
```

**规则 2：负面测试比例 >= 40%**

```
negative_test_count / total_test_count >= 0.40
```

"负面"测试指期望异常、错误、失败状态、边界/极端输入、未授权访问或畸形数据的测试。

**规则 3：断言质量 — 低价值断言 <= 20%**

```
low_value_count / total_assertion_count <= 0.20
```

低价值断言模式（应避免）：
- `assert x is not None` 但不检查内容
- `assert isinstance(x, SomeType)` 但不检查行为
- `assert len(x) > 0` 但不验证元素
- `assert "key" in dict` 但不检查值
- `assert bool(x)` / 仅检查真值性
- 仅导入测试（`from module import X; assert X is not None`）

**规则 4："错误实现"挑战**

对每个测试问："哪种错误实现会被此测试捕获？"

如果"几乎任何错误实现都能通过" → 用更具体的断言重写。

功能详细设计文档中的边界矩阵（§5.3）和错误表（§5.4）提供了预分析的边界值和错误条件。将其作为输入 — 它们系统性地识别了"可能的错误实现"。

设想 2-3 种可能的错误实现：
- 返回硬编码值而非计算
- 交换两个字段
- 差一错误
- 跳过某个验证步骤
- 返回过期/缓存数据

测试是否会对每种**失败**？如果大多数不会 → 重写。

**规则 5：测试层级规则 — 必须有真实测试用例**

每个功能的自动化测试必须覆盖两个层级，两者均为必需：

| 层级 | 目的 | Mock 策略 | 最低要求 |
|------|------|----------|---------|
| **单元测试 (UT)** | 单个函数/类 | 仅在系统边界 Mock（外部 HTTP、第三方 API、文件系统、时钟）；内部逻辑使用真实或内存实现 | ≥ 1 个使用真实内部依赖执行核心逻辑的测试 |
| **集成测试** | 组件配合真实基础设施 | 主依赖不可 Mock — 使用真实测试数据库、真实运行服务或真实文件系统 | 每个涉及外部系统的功能 ≥ 1 个测试 |

**集成测试豁免** — 如果功能完全无外部依赖（纯计算，无 IO、无数据库、无网络）：
- 在测试文件中明确声明：
  ```python
  # [no integration test] — pure function, no external I/O
  ```

**按层级标注测试：**
```python
# [unit] — uses in-memory store
def test_user_validation_logic():
    ...

# [integration] — uses real test database
def test_user_persisted_to_db():
    ...
```

完整反模式目录（14 种模式含示例）：同目录下的 `testing-anti-patterns.md`。
