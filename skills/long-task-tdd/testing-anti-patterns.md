# Testing Anti-Patterns

## Purpose

Catalog of common testing mistakes that produce false confidence. Reference this when writing tests or reviewing test quality.

## Anti-Pattern Catalog

### 1. Testing Mock Behavior Instead of Real Behavior

**Symptom**: Tests pass but the feature doesn't actually work.

**Example (BAD)**:
```python
def test_user_login(mock_db):
    mock_db.get_user.return_value = User(id=1, name="test")
    result = login("test", "password")
    mock_db.get_user.assert_called_once_with("test")  # Testing the mock!
```

**Why it fails**: You're testing that your code calls the mock correctly, not that the login actually works.

**Fix**: Test with real dependencies when possible (test database, in-memory store). Mock only external services you can't control.

### 2. Adding Test-Only Methods to Production Code

**Symptom**: Production code has `_test_helper()`, `get_for_testing()`, or similar methods.

**Why it fails**: Production code should not know about tests. Test-only methods can be called in production, creating maintenance burden and potential bugs.

**Fix**: Test through public interfaces. If you can't test something without a backdoor, the design needs refactoring.

### 3. Mocking Without Understanding Dependencies

**Symptom**: Every test mocks everything, and you're not sure what each mock represents.

**Why it fails**: Over-mocking makes tests brittle (break when implementation changes) and meaningless (test mock wiring, not behavior).

**Fix**:
- Understand the dependency before mocking it
- Mock at the boundary (HTTP calls, file system, time) not at internal layers
- Prefer fakes (in-memory implementations) over mocks for complex dependencies

### 4. Testing Implementation Details

**Symptom**: Tests break when you refactor without changing behavior.

**Example (BAD)**:
```python
def test_sort():
    result = sort_list([3, 1, 2])
    # Testing that quicksort was used (implementation detail)
    assert mock_quicksort.called
```

**Fix**: Test the output, not how it was computed:
```python
def test_sort():
    result = sort_list([3, 1, 2])
    assert result == [1, 2, 3]
```

### 5. Non-Deterministic Tests

**Symptom**: Tests pass sometimes and fail sometimes.

**Common causes**:
- Depending on current time/date
- Random values without seeds
- Race conditions in async code
- Shared state between tests
- Network calls to external services

**Fix**: Control all sources of non-determinism. Use fixed timestamps, seeded random, proper async handling, test isolation, and mocked network.

### 6. Tests That Can't Fail

**Symptom**: Test always passes regardless of implementation.

**Example (BAD)**:
```python
def test_something():
    try:
        result = do_thing()
        assert result is not None
    except:
        pass  # Swallowing the failure!
```

**Fix**: Always run TDD Red first — if the test passes before implementation, the test is wrong.

### 7. Testing Too Much in One Test

**Symptom**: One test has 20+ assertions covering multiple behaviors.

**Why it fails**: When it fails, you don't know which behavior broke. Makes debugging harder.

**Fix**: One behavior per test. Use descriptive test names that describe the single behavior being tested.

### 8. Shared Mutable State Between Tests

**Symptom**: Tests pass in isolation but fail when run together.

**Why it fails**: One test modifies shared state that another test depends on.

**Fix**: Each test sets up and tears down its own state. Use fresh fixtures, database transactions, or isolated test containers.

### 9. Assertion-Free Tests

**Symptom**: Test runs code but doesn't assert anything meaningful.

**Example (BAD)**:
```python
def test_create_user():
    create_user("test", "test@email.com")
    # No assertion! Just checking it doesn't throw.
```

**Fix**: Assert the observable outcome:
```python
def test_create_user():
    user = create_user("test", "test@email.com")
    assert user.name == "test"
    assert user.email == "test@email.com"
```

### 10. Copy-Paste Test Suites

**Symptom**: Tests are duplicated with minor variations, making the suite hard to maintain.

**Fix**: Use parameterized tests for variations. Extract shared setup into fixtures. But avoid over-abstracting — tests should be readable without jumping through hoops.

### 11. Gaming Coverage with Assert-Free Tests

**Symptom**: High coverage numbers but tests have weak or no assertions.

**Example (BAD)**:
```python
def test_process_data():
    process_data(sample_input)  # 100% line coverage, 0% verification
```

**Why it fails**: Exercising code paths without verifying correctness gives false confidence. Tests will never fail even if the function returns garbage.

**Fix**: Every test must assert observable outcomes. Mutation testing exposes this — if a mutant survives, the test isn't actually checking the result.

```python
def test_process_data():
    result = process_data(sample_input)
    assert result.status == "success"
    assert result.count == 42
```

### 12. Ignoring Surviving Mutants

**Symptom**: Mutation score below threshold but feature is marked as "passing" anyway.

**Why it fails**: Surviving mutants are bugs your tests can't catch. If you change `>` to `>=` and no test fails, your boundary logic is untested.

**Fix**: For each surviving mutant:
- **Real gap**: add a test that kills it
- **Equivalent mutant**: document why the change produces identical behavior (e.g., `# equivalent mutant: condition is always true due to precondition on line X`)
- **Never ignore**: every survivor must be addressed (fixed or documented)

### 13. Running Mutation Tests on Untested Code

**Symptom**: Running mutation tests before achieving coverage threshold. Many mutants show "no coverage".

**Why it fails**: Mutation testing on uncovered code produces many false survivors and wastes time — there's no test to kill the mutant in the first place.

**Fix**: Always pass the coverage gate before running mutation tests. Coverage first, mutation second.

### 14. Low-Value Assertions (Existence/Type/Import Tests)

**Symptom**: Tests assert existence, type, or import success — things that would only fail if the language runtime itself is broken, not if the implementation has a bug.

**Examples (ALL BAD)**:

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

**Why they're harmful**:
- They pass regardless of what the implementation actually returns, as long as it returns *something*
- They inflate coverage and test counts with zero bug-finding ability
- Mutation testing may not catch all of these — some mutations preserve type/existence
- They crowd out meaningful assertions, creating false confidence in test suite quality

**The "Wrong Implementation" Test**: For each assertion, ask: *"What wrong implementation would this test NOT catch?"* If the answer is "almost any wrong implementation" → the assertion is low-value.

Example: `assert result is not None` — a function returning `User(name="WRONG", email="WRONG")` passes this test. A function returning `42` passes this test. A function returning `""` passes this test. It catches exactly one failure: returning `None`.

**Fix — assert specific observable outcomes**:

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

**Quantitative rule**: In any test suite, the ratio of low-value assertions to total assertions must not exceed **20%**:

```
low_value_count / total_assertion_count <= 0.20
```

Low-value assertion patterns (for counting):
- `assert x is not None` / `assert x is None` (when testing defaults, not behavior)
- `assert isinstance(x, SomeType)`
- `assert len(x) > 0` (without checking contents)
- `assert "key" in dict` (without checking value)
- `assert bool(x)` / `assert x` (truthiness only)
- `from module import X; assert X is not None` (import test)
- Tests with no assertion at all (already covered by anti-pattern #9)

**Relationship to other anti-patterns**: This is more specific than #9 (assertion-free tests) and #11 (gaming coverage). A test can have assertions and still be low-value if those assertions only verify existence/type. Mutation testing (#12) catches some but not all low-value assertions — the 20% ratio rule provides an additional check during test writing.

## Quick Reference: Test Writing Checklist

Before marking a test as complete:

- [ ] Test fails without the implementation (TDD Red verified)
- [ ] Test name describes the behavior being tested
- [ ] Test has meaningful assertions (not just "no error")
- [ ] Test is deterministic (passes/fails consistently)
- [ ] Test is independent (doesn't depend on other tests' state)
- [ ] Test tests behavior, not implementation details
- [ ] No test-only methods added to production code
- [ ] Mocks are at boundaries, not internal layers
- [ ] No low-value assertions (None checks, isinstance, import, len>0, key-in-dict, truthiness)
- [ ] Low-value assertion ratio <= 20% of total assertions
- [ ] Each assertion would fail for a plausible wrong implementation ("wrong implementation" test)
- [ ] Coverage meets project thresholds (line >= 90%, branch >= 80%)
- [ ] Mutation score meets threshold (>= 80%) for changed files
- [ ] No surviving mutants without justification
