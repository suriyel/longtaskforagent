# Coverage & Mutation Tool Setup Recipes

Multi-language setup instructions for coverage tracking and mutation testing tools. Read this file when configuring tools for a new project.

## Multi-Language Tool Matrix

| Language | Coverage Tool | Branch Support | Mutation Tool | Incremental Support |
|----------|--------------|----------------|---------------|---------------------|
| Python | pytest-cov (coverage.py) | Yes | mutmut | Yes (`--paths-to-mutate`) |
| Java | JaCoCo | Yes | PIT (pitest) | Yes (`-DtargetClasses`) |
| JavaScript | c8 / nyc (Istanbul) | Yes | Stryker | Yes (`--mutate` glob) |
| TypeScript | c8 / nyc (Istanbul) | Yes | Stryker | Yes (`--mutate` glob) |
| C | gcov + lcov | Yes (`--branch-probabilities`) | Mull | Partial (filter by file) |
| C++ | gcov + lcov / llvm-cov | Yes | Mull | Partial (filter by file) |

---

## Python

**Coverage** — pytest-cov (wraps coverage.py):

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-branch --cov-report=term-missing --cov-fail-under=90"

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
fail_under = 90
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```

**Mutation** — mutmut:

```toml
# pyproject.toml (or setup.cfg)
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=short"
```

> Runtime commands: `python scripts/get_tool_commands.py feature-list.json`

---

## Java

**Coverage** — JaCoCo:

Maven (`pom.xml`):
```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.12</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals><goal>report</goal></goals>
        </execution>
        <execution>
            <id>check</id>
            <phase>verify</phase>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.90</minimum>
                            </limit>
                            <limit>
                                <counter>BRANCH</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

Gradle (`build.gradle`):
```groovy
plugins {
    id 'jacoco'
}

jacocoTestReport {
    reports {
        xml.required = true
        html.required = true
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit { counter = 'LINE';   value = 'COVEREDRATIO'; minimum = 0.90 }
            limit { counter = 'BRANCH'; value = 'COVEREDRATIO'; minimum = 0.80 }
        }
    }
}

test.finalizedBy jacocoTestReport
check.dependsOn jacocoTestCoverageVerification
```

**Mutation** — PIT (pitest):

Maven:
```xml
<plugin>
    <groupId>org.pitest</groupId>
    <artifactId>pitest-maven</artifactId>
    <version>1.17.1</version>
    <configuration>
        <targetClasses><param>com.example.*</param></targetClasses>
        <targetTests><param>com.example.*Test</param></targetTests>
        <mutationThreshold>80</mutationThreshold>
        <outputFormats>
            <outputFormat>HTML</outputFormat>
            <outputFormat>XML</outputFormat>
        </outputFormats>
    </configuration>
</plugin>
```

Gradle:
```groovy
plugins {
    id 'info.solidsoft.pitest' version '1.15.0'
}

pitest {
    targetClasses = ['com.example.*']
    targetTests = ['com.example.*Test']
    mutationThreshold = 80
    outputFormats = ['HTML', 'XML']
    timestampedReports = false
}
```

> Runtime commands: `python scripts/get_tool_commands.py feature-list.json`

---

## JavaScript

**Coverage** — c8 (native V8 coverage, recommended) or nyc (Istanbul):

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:cov": "c8 --branches 80 --lines 90 --reporter=text npx jest",
    "test:cov:nyc": "nyc --branches 80 --lines 90 --reporter=text npx jest"
  }
}
```

```json
// jest.config.json (if using Jest built-in coverage instead of c8)
{
  "collectCoverage": true,
  "coverageDirectory": "coverage",
  "coverageReporters": ["text", "html", "lcov"],
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "lines": 90,
      "functions": 80,
      "statements": 90
    }
  },
  "collectCoverageFrom": ["src/**/*.js", "!src/**/*.test.js"]
}
```

**Mutation** — Stryker:

```json
// stryker.conf.json
{
  "$schema": "https://raw.githubusercontent.com/stryker-mutator/stryker/master/packages/core/schema/stryker-core.schema.json",
  "mutate": ["src/**/*.js", "!src/**/*.test.js", "!src/**/*.spec.js"],
  "testRunner": "jest",
  "reporters": ["clear-text", "html"],
  "thresholds": {
    "high": 90,
    "low": 80,
    "break": 80
  },
  "coverageAnalysis": "perTest"
}
```

> Runtime commands: `python scripts/get_tool_commands.py feature-list.json`

---

## TypeScript

**Coverage** — c8 (native V8 coverage, recommended) or nyc (Istanbul):

```json
// package.json
{
  "scripts": {
    "test": "vitest run",
    "test:cov": "vitest run --coverage",
    "test:cov:c8": "c8 --branches 80 --lines 90 --reporter=text npm test"
  }
}
```

```json
// vitest.config.ts or vitest section
{
  "test": {
    "coverage": {
      "provider": "v8",
      "reporter": ["text", "html", "lcov"],
      "branches": 80,
      "lines": 90,
      "functions": 80,
      "statements": 90,
      "exclude": ["node_modules/", "test/", "**/*.d.ts"]
    }
  }
}
```

**Mutation** — Stryker:

```json
// stryker.conf.json
{
  "$schema": "https://raw.githubusercontent.com/stryker-mutator/stryker/master/packages/core/schema/stryker-core.schema.json",
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.spec.ts"],
  "testRunner": "vitest",
  "reporters": ["clear-text", "html"],
  "thresholds": {
    "high": 90,
    "low": 80,
    "break": 80
  },
  "coverageAnalysis": "perTest"
}
```

> Runtime commands: `python scripts/get_tool_commands.py feature-list.json`

---

## C

**Coverage** — gcov + lcov:

```makefile
# Makefile additions
CFLAGS += --coverage -fprofile-arcs -ftest-coverage
LDFLAGS += --coverage

coverage: test
	gcov -b src/*.c
	lcov --capture --directory . --output-file coverage.info
	lcov --remove coverage.info '/usr/*' 'tests/*' --output-file coverage.info
	lcov --summary coverage.info
	genhtml coverage.info --output-directory coverage-report

clean-coverage:
	find . -name '*.gcda' -o -name '*.gcno' -o -name '*.gcov' | xargs rm -f
	rm -rf coverage.info coverage-report
```

CMake:
```cmake
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()
```

**Mutation** — Mull:

```yaml
# mull.yml
mutators:
  - cxx_add_to_sub
  - cxx_sub_to_add
  - cxx_mul_to_div
  - cxx_div_to_mul
  - cxx_remove_void_call
  - cxx_negate_condition
  - cxx_boundary

timeout: 10000
reporters:
  - Elements
  - SQLite
```

> Runtime commands: `python scripts/get_tool_commands.py feature-list.json`

---

## C++

**Coverage** — gcov + lcov or llvm-cov:

```cmake
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-instr-generate -fcoverage-mapping")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fprofile-instr-generate")
    endif()
endif()
```

> Runtime commands: `python scripts/get_tool_commands.py feature-list.json`

---

---

## Per-Feature Mutation Test Scoping

When the project's active feature count exceeds `mutation_full_threshold`, the Quality Gate scopes mutation testing to the current feature's changed files **and** tests. This avoids running the entire test suite per mutant, which becomes prohibitively slow in large projects.

**Principle**: Mutate only changed source files, run only the feature's tests per mutant. Full mutation runs when the project's active feature count is at or below the threshold.

### Identifying Feature Test Files

- Test files created/modified during the TDD cycle for this feature
- Convention-based: if source is `src/foo.ext`, tests are likely `tests/test_foo.ext`
- Marker-based: if the project uses test markers/tags, filter by feature marker
- The Worker passes feature test file paths to the Quality SubAgent

### Per-Tool Scoping Reference

| Tool | Mutation Target Scoping | Test Scoping Mechanism |
|------|------------------------|------------------------|
| mutmut | `--paths-to-mutate={files}` | `--runner='{test_runner} {test_files}'` |
| pitest | `-DtargetClasses={classes}` | `-DtargetTests={test_classes}` |
| stryker | `--mutate='{files}'` | `--coverageAnalysis perTest` (auto-selects relevant tests) |
| mull | `--filters={files}` | Build feature-specific test binary |

### Tool-Specific Notes

- **mutmut** `--runner`: Provide the full test execution command including framework binary and file paths. The `{test_runner}` placeholder resolves to the project's test runner command (e.g., `python -m pytest -x --tb=short`, `npx vitest run`).
- **pitest** `-DtargetTests`: Accepts comma-separated Java class patterns (e.g., `com.example.UserAuthTest,com.example.UserLoginTest`).
- **Stryker** `--coverageAnalysis perTest`: Stryker automatically determines which tests cover each mutant and runs only those. No explicit test file list needed. Requires Stryker 6+.
- **mull**: Link only feature-relevant test object files when compiling the test binary. This requires building a separate binary per feature scope.
