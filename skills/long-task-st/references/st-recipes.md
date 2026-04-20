# 系统测试配方（System Testing Recipes）

按语言 / 框架提供每类 ST 测试的配方。依据 `feature-list.json` 中的 `tech_stack` 选择配方。

## 1. 集成测试模式

### Real vs Contract 测试分类

- **Contract test**（契约测试） — 使用 mock/stub（`unittest.mock`、`requests-mock`、`msw`、`gmock`）验证调用签名与数据形状。校验接口但**不**验证真实数据流。
- **Integration test**（集成测试） — 在真实组件之间（真实 DB、真实 HTTP、真实文件系统）验证实际数据流。捕获 mock 所隐藏的契约不一致、类型错误与协议 bug。

**推荐用于真实集成的工具：**
- `testcontainers`（Python、Java、JS/TS） — Docker 中的真实 DB/服务
- `sqlite:///:memory:` — 内存中的真实 SQL 引擎（SQL 集成可接受）
- 对运行中的 server 使用 `httpx` — 内部 API 优先于 `requests-mock`
- 对运行中的 Express/Fastify 使用 `supertest` — 内部 API 优先于 `msw`

**外部第三方服务测试策略（优先级顺序）：**
1. **优先真实测试** — 使用 `required_configs` 或环境中的测试凭据（例如 Stripe test key、GitHub personal token）
2. **若不可用** — 使用契约测试（mock）并记录原因
3. **记录决策** — 在 ST plan Classification 表中注明：`External (credentials unavailable)` 作为 mock 授权依据

**仅在以下情况允许使用 mock：**
- 外部第三方服务（如 Stripe API、GitHub API） 且 `required_configs` 或环境中无可用测试凭据
- 必须在 ST plan 中记录原因作为 mock 授权依据

### Python
```bash
# Directory structure
tests/integration/
  test_feature_a_b_integration.py
  conftest.py  # shared fixtures

# Run with pytest
pytest tests/integration/ -v --tb=short

# With coverage
pytest tests/integration/ --cov=src --cov-report=term-missing
```

**模式：**
- 使用 `pytest` fixture 做共享状态的 setup/teardown
- 数据库集成用 `sqlite:///:memory:` 或 `testcontainers` [Real]
- 内部 API 集成用 `httpx` 对运行中的 server [Real]
- 外部服务边界用 `unittest.mock.patch` 或 `requests-mock` [Contract] — 凭据不可用时须记录原因

### JavaScript / TypeScript
```bash
# Directory structure
tests/integration/
  featureA-featureB.test.ts
  setup.ts  # shared setup

# Run with vitest
npx vitest run tests/integration/ --reporter=verbose

# Run with jest
npx jest tests/integration/ --verbose
```

**模式：**
- 使用 `beforeAll`/`afterAll` 做共享状态
- 数据库集成用 `testcontainers` [Real]
- 内部 API 集成用 `supertest` 对运行中的 Express/Fastify [Real]
- 外部服务边界仅用 `msw`（Mock Service Worker） [Contract] — 凭据不可用时须记录原因

### Java
```bash
# Directory structure
src/test/java/integration/
  FeatureABIntegrationTest.java

# Run with Maven
mvn test -Dtest="integration.*" -pl module-name

# Run with Gradle
./gradlew test --tests "integration.*"
```

**模式：**
- Spring 集成用 `@SpringBootTest` [Real]
- 数据库 / 服务集成用 `Testcontainers` [Real]
- 内部 API 集成用 `RestAssured` 对运行中的 server [Real]；外部边界用 mock server [Contract]
- 测试间状态隔离用 `@DirtiesContext`

### C / C++
```bash
# Integration tests in separate directory
tests/integration/
  test_module_integration.cpp

# Build and run with CMake + CTest
cmake --build build --target integration_tests
ctest --test-dir build -R integration -V
```

**模式：**
- 使用 `gtest` fixture 做共享状态
- 测试模块间 IPC、共享内存、文件 I/O [Real]
- 外部边界用 mock 库（`gmock`、`fff`）[Contract] — 凭据不可用时须记录原因

### Go
```bash
# Directory convention (_test.go next to source, or tests/integration/)
internal/feature/feature_integration_test.go

# Run integration tests (build tag or separate dir)
go test -tags=integration ./... -v
# or run a specific integration directory
go test ./tests/integration/... -v
```

**模式：**
- 使用 `testing.T.TempDir()` / `t.Cleanup()` 做共享状态 setup/teardown
- 数据库 / 服务集成用 `testcontainers-go` [Real]
- 内部 HTTP API 用 `net/http/httptest.NewServer` [Real]
- 外部第三方边界用 `httptest` + interface seam 替换 client [Contract] — 凭据不可用时须记录原因
- 使用 `//go:build integration` build tag 隔离集成测试

---

## 2. E2E 测试工具

### 基于 API 的 E2E

| Language | Tool | Install |
|----------|------|---------|
| Python | `httpx` + `pytest` | `pip install httpx` |
| Python | `requests` + `pytest` | `pip install requests` |
| JS/TS | `supertest` | `npm install supertest` |
| JS/TS | `axios` + `vitest` | `npm install axios` |
| Java | `RestAssured` | Maven: `io.rest-assured:rest-assured` |
| Go | `net/http` + `testing` | stdlib (no install) |

### UI E2E（Chrome DevTools MCP）

对于含 `"ui": true` 特性的项目，使用 Chrome DevTools MCP 工具做浏览器 E2E 验证。可用工具与使用模式参考 Chrome DevTools MCP 文档。

### CLI E2E

| Language | Approach |
|----------|----------|
| Python | `subprocess.run()` in pytest |
| Node.js | `execa` or `child_process` in vitest |
| Java | `ProcessBuilder` in JUnit |
| C/C++ | `system()` or `popen()` in gtest |
| Go | `os/exec` + `testing` |

---

## 3. 性能基准测试

### Python
```bash
# pytest-benchmark (micro-benchmarks)
pip install pytest-benchmark
pytest tests/perf/ --benchmark-only --benchmark-json=benchmark.json

# locust (load testing)
pip install locust
locust -f tests/perf/locustfile.py --headless -u 100 -r 10 --run-time 60s --csv=perf_results

# time module (simple timing)
import time
start = time.perf_counter()
# ... operation ...
elapsed = time.perf_counter() - start
assert elapsed < 0.2, f"Response time {elapsed:.3f}s exceeds 200ms threshold"
```

### JavaScript / TypeScript
```bash
# Vitest bench
npx vitest bench

# k6 (load testing)
k6 run tests/perf/load-test.js --out csv=perf_results.csv

# autocannon (HTTP benchmarking)
npx autocannon -c 100 -d 30 http://localhost:3000/api/endpoint
```

### Java
```bash
# JMH (micro-benchmarks)
mvn exec:exec -Pbenchmark

# Gatling (load testing)
mvn gatling:test
```

### C / C++
```bash
# Google Benchmark
cmake --build build --target benchmarks
./build/benchmarks --benchmark_format=json --benchmark_out=benchmark.json

# Custom timing
#include <chrono>
auto start = std::chrono::high_resolution_clock::now();
// ... operation ...
auto elapsed = std::chrono::duration<double>(std::chrono::high_resolution_clock::now() - start).count();
```

### Go
```bash
# stdlib testing.B (micro-benchmarks)
go test -bench=. -benchmem -run=^$ ./...
go test -bench=BenchmarkX -benchtime=5s -count=3 ./pkg/... > bench.txt

# Load testing: vegeta
echo "GET http://localhost:8080/api/endpoint" | vegeta attack -duration=30s -rate=100 | vegeta report
```

---

## 4. 安全扫描

### 依赖漏洞扫描器

| Language | Tool | Command |
|----------|------|---------|
| Python | `pip-audit` | `pip-audit --strict` |
| Python | `safety` | `safety check` |
| JS/TS | `npm audit` | `npm audit --audit-level=high` |
| JS/TS | `snyk` | `npx snyk test` |
| Java | `OWASP Dependency-Check` | `mvn org.owasp:dependency-check-maven:check` |
| C/C++ | `cve-bin-tool` | `cve-bin-tool ./build/` |
| Go | `govulncheck` | `govulncheck ./...` |
| General | `trivy` | `trivy fs --severity HIGH,CRITICAL .` |

### 静态分析（侧重安全）

| Language | Tool | Command |
|----------|------|---------|
| Python | `bandit` | `bandit -r src/ -f json -o bandit-report.json` |
| JS/TS | `eslint-plugin-security` | `npx eslint --rule 'security/*' src/` |
| Java | `SpotBugs + FindSecBugs` | `mvn spotbugs:check` |
| C/C++ | `cppcheck` | `cppcheck --enable=all --force src/` |
| Go | `golangci-lint` (含 gosec) | `golangci-lint run --enable=gosec ./...` |

### OWASP Top 10 检查清单（人工评审）

| # | Category | What to Check |
|---|----------|---------------|
| A01 | Broken Access Control | 鉴权绕过、权限提升、IDOR |
| A02 | Cryptographic Failures | 硬编码密钥、弱算法、明文敏感数据 |
| A03 | Injection | SQL、XSS、命令、LDAP、模板注入 |
| A04 | Insecure Design | 缺少限流、缺少输入校验 |
| A05 | Security Misconfiguration | Debug 模式、默认凭据、冗长错误 |
| A06 | Vulnerable Components | 过期依赖（运行上表扫描器） |
| A07 | Authentication Failures | 弱密码、缺少 MFA、session fixation |
| A08 | Data Integrity Failures | 未签名更新、不可信反序列化 |
| A09 | Logging Failures | 缺审计日志、日志含敏感数据 |
| A10 | SSRF | 未校验的 URL、内网访问 |

---

## 5. 兼容性测试

### 跨浏览器（UI 项目）

使用 Chrome DevTools MCP 设备模拟做跨浏览器与移动端测试。

### 跨平台（CLI / Library）

在目标平台用可用环境进行验证：
```bash
# Check platform-specific behavior
python -c "import platform; print(platform.system())"

# Verify file path handling
# Verify line ending handling
# Verify permission handling
```

---

## 6. 测试报告指标采集

### 采集覆盖率指标

| Language | Command to Get Summary |
|----------|----------------------|
| Python | `pytest --cov=src --cov-report=term-missing` |
| JS/TS | `npx vitest run --coverage` |
| Java | `mvn jacoco:report` (then read `target/site/jacoco/index.html`) |
| C/C++ | `gcovr --print-summary` |
| Go | `go tool cover -func=coverage.out \| tail -1` |

### 采集测试数量

| Language | Command |
|----------|---------|
| Python | `pytest --tb=no -q` (last line shows counts) |
| JS/TS | `npx vitest run --reporter=verbose` |
| Java | `mvn test` (Surefire report) |
| C/C++ | `ctest --test-dir build -V` |
| Go | `go test -v ./... \| tail -5` (PASS/FAIL + ok summary) or `gotestsum --format=short` |
