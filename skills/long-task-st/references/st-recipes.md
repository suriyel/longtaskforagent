# System Testing Recipes

Per-language/framework recipes for each ST test category. Select recipes based on `tech_stack` in `feature-list.json`.

## 1. Integration Test Patterns

### Real vs Contract Test Classification

- **Contract test** — verifies call signatures and data shapes using mocks/stubs (`unittest.mock`, `requests-mock`, `msw`, `gmock`). Validates interfaces but does NOT verify real data flow.
- **Integration test** — verifies actual data flow between real components (real DB, real HTTP, real file system). Catches contract mismatches, type errors, and protocol bugs that mocks hide.

**Preferred tools for real integration:**
- `testcontainers` (Python, Java, JS/TS) — real DB/service in Docker
- `sqlite:///:memory:` — real SQL engine, in-memory (acceptable for SQL integration)
- `httpx` against running server — preferred over `requests-mock` for internal APIs
- `supertest` against running Express/Fastify — preferred over `msw` for internal APIs

**External third-party service testing strategy (priority order):**
1. **Prefer real tests** — use test credentials from `required_configs` or environment (e.g., Stripe test key, GitHub personal token)
2. **If unavailable** — use contract tests (mocks) and record the reason
3. **Record decision** — note in ST plan Classification table: `External (credentials unavailable)` as mock authorization

**Mocks are allowed ONLY when:**
- External third-party service (e.g., Stripe API, GitHub API) AND test credentials are not available in `required_configs` or environment
- Must record reason in ST plan as mock authorization basis

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

**Patterns:**
- Use `pytest` fixtures for shared state setup/teardown
- Use `sqlite:///:memory:` or `testcontainers` for database integration [Real]
- Use `httpx` against running server for internal API integration [Real]
- Use `unittest.mock.patch` or `requests-mock` for external service boundaries only [Contract] — requires documented reason when credentials unavailable

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

**Patterns:**
- Use `beforeAll`/`afterAll` for shared state
- Use `testcontainers` for database integration [Real]
- Use `supertest` against running Express/Fastify app for internal API integration [Real]
- Use `msw` (Mock Service Worker) for external service boundaries only [Contract] — requires documented reason when credentials unavailable

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

**Patterns:**
- Use `@SpringBootTest` for Spring integration [Real]
- Use `Testcontainers` for database/service integration [Real]
- Use `RestAssured` against running server for internal API integration [Real]; against mock server for external boundaries [Contract]
- Use `@DirtiesContext` for state isolation between tests

### C / C++
```bash
# Integration tests in separate directory
tests/integration/
  test_module_integration.cpp

# Build and run with CMake + CTest
cmake --build build --target integration_tests
ctest --test-dir build -R integration -V
```

**Patterns:**
- Use `gtest` fixtures for shared state
- Test IPC, shared memory, file I/O between modules [Real]
- Use mock libraries (`gmock`, `fff`) for external boundaries only [Contract] — requires documented reason when credentials unavailable

---

## 2. E2E Test Tools

### API-Based E2E

| Language | Tool | Install |
|----------|------|---------|
| Python | `httpx` + `pytest` | `pip install httpx` |
| Python | `requests` + `pytest` | `pip install requests` |
| JS/TS | `supertest` | `npm install supertest` |
| JS/TS | `axios` + `vitest` | `npm install axios` |
| Java | `RestAssured` | Maven: `io.rest-assured:rest-assured` |

### UI E2E (Chrome DevTools MCP)

For projects with `"ui": true` features, use Chrome DevTools MCP tools for browser-based E2E verification. Refer to the Chrome DevTools MCP documentation for available tools and usage patterns.

### CLI E2E

| Language | Approach |
|----------|----------|
| Python | `subprocess.run()` in pytest |
| Node.js | `execa` or `child_process` in vitest |
| Java | `ProcessBuilder` in JUnit |
| C/C++ | `system()` or `popen()` in gtest |

---

## 3. Performance Benchmarking

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

---

## 4. Security Scanning

### Dependency Vulnerability Scanners

| Language | Tool | Command |
|----------|------|---------|
| Python | `pip-audit` | `pip-audit --strict` |
| Python | `safety` | `safety check` |
| JS/TS | `npm audit` | `npm audit --audit-level=high` |
| JS/TS | `snyk` | `npx snyk test` |
| Java | `OWASP Dependency-Check` | `mvn org.owasp:dependency-check-maven:check` |
| C/C++ | `cve-bin-tool` | `cve-bin-tool ./build/` |
| General | `trivy` | `trivy fs --severity HIGH,CRITICAL .` |

### Static Analysis (Security-Focused)

| Language | Tool | Command |
|----------|------|---------|
| Python | `bandit` | `bandit -r src/ -f json -o bandit-report.json` |
| JS/TS | `eslint-plugin-security` | `npx eslint --rule 'security/*' src/` |
| Java | `SpotBugs + FindSecBugs` | `mvn spotbugs:check` |
| C/C++ | `cppcheck` | `cppcheck --enable=all --force src/` |

### OWASP Top 10 Checklist (Manual Review)

| # | Category | What to Check |
|---|----------|---------------|
| A01 | Broken Access Control | Auth bypass, privilege escalation, IDOR |
| A02 | Cryptographic Failures | Hardcoded secrets, weak algorithms, plaintext sensitive data |
| A03 | Injection | SQL, XSS, command, LDAP, template injection |
| A04 | Insecure Design | Missing rate limiting, missing input validation |
| A05 | Security Misconfiguration | Debug mode, default credentials, verbose errors |
| A06 | Vulnerable Components | Outdated dependencies (run scanner above) |
| A07 | Authentication Failures | Weak passwords, missing MFA, session fixation |
| A08 | Data Integrity Failures | Unsigned updates, untrusted deserialization |
| A09 | Logging Failures | Missing audit logs, sensitive data in logs |
| A10 | SSRF | Unvalidated URLs, internal network access |

---

## 5. Compatibility Testing

### Cross-Browser (UI Projects)

Use Chrome DevTools MCP device emulation for cross-browser and mobile testing.

### Cross-Platform (CLI/Library)

Verify on target platforms using available environment:
```bash
# Check platform-specific behavior
python -c "import platform; print(platform.system())"

# Verify file path handling
# Verify line ending handling
# Verify permission handling
```

---

## 6. Test Report Metrics Collection

### Collecting Coverage Metrics

| Language | Command to Get Summary |
|----------|----------------------|
| Python | `pytest --cov=src --cov-report=term-missing` |
| JS/TS | `npx vitest run --coverage` |
| Java | `mvn jacoco:report` (then read `target/site/jacoco/index.html`) |
| C/C++ | `gcovr --print-summary` |

### Collecting Test Counts

| Language | Command |
|----------|---------|
| Python | `pytest --tb=no -q` (last line shows counts) |
| JS/TS | `npx vitest run --reporter=verbose` |
| Java | `mvn test` (Surefire report) |
| C/C++ | `ctest --test-dir build -V` |

---

## 7. Full Mutation Regression

Full-codebase mutation testing during ST phase. Complements per-feature mutation from Worker cycles — verifies mutation score holds project-wide with the full test suite.

### Per-Tool Commands

| Tool | Full Mutation Command | Results Command | Score Extraction |
|------|----------------------|-----------------|------------------|
| mutmut | `mutmut run` | `mutmut results` | "Killed N out of M mutants" line |
| pitest | `mvn pitest:mutationCoverage` | `cat target/pit-reports/*/mutations.xml` | `mutationScore` attribute in XML |
| stryker | `npx stryker run` | `cat reports/mutation/mutation.json` | `.thresholds.high` in JSON |
| mull | `mull-runner ./test-binary` | `cat mull-report.json` | killed/survived counts in JSON |

### Interpreting Results

- **Score >= threshold** → PASS
- **Score < threshold** with equivalent mutants documented → may PASS if adjusted score (excluding equivalents) >= threshold
- **Score < threshold** with real gaps → FAIL (Major severity defect — add tests to kill surviving mutants, then re-run)

### Relationship to Per-Feature Mutation

- During Worker cycles, projects with active features ≤ `mutation_full_threshold` already run full mutation per-feature — this step re-confirms project-wide
- Projects with active features > `mutation_full_threshold` ran feature-scoped mutation during Worker — this step is the first full-suite mutation run and may surface cross-feature mutation gaps
