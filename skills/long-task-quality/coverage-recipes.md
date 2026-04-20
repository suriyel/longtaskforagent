# Coverage Tool Setup Recipes

Multi-language setup instructions for coverage tracking tools. Read this file when configuring tools for a new project.

## Multi-Language Tool Matrix

| Language | Coverage Tool | Branch Support |
|----------|--------------|----------------|
| Python | pytest-cov (coverage.py) | Yes |
| Java | JaCoCo | Yes |
| JavaScript | c8 / nyc (Istanbul) | Yes |
| TypeScript | c8 / nyc (Istanbul) | Yes |
| C | gcov + lcov | Yes (`--branch-probabilities`) |
| C++ | gcov + lcov / llvm-cov | Yes |
| Go | go test -cover (`go tool cover`) | No — statement coverage only (gocov for branch) |

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

**Commands**:
```bash
# Coverage
pytest --cov=src --cov-branch --cov-report=term-missing
```

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

**Commands**:
```bash
# Coverage
mvn test jacoco:report
# or
gradle test jacocoTestReport
```

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

**Commands**:
```bash
# Coverage (c8)
npx c8 --branches 80 --lines 90 --reporter=text npx jest

# Coverage (Jest built-in)
npx jest --coverage
```

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

**Commands**:
```bash
# Coverage
npx c8 --branches --reporter=text npm test
# or
npx vitest run --coverage
```

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

**Commands**:
```bash
# Coverage
make clean-coverage
make CFLAGS="--coverage" test
gcov -b src/*.c
lcov --capture -d . -o coverage.info
lcov --summary coverage.info
```

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

**Commands**:
```bash
# GCC + gcov + lcov
cmake -DENABLE_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug ..
make && ctest
gcov -b src/*.cpp
lcov --capture -d . -o coverage.info
lcov --remove coverage.info '/usr/*' '*/test/*' -o coverage.info
lcov --summary coverage.info

# Clang + llvm-cov
cmake -DENABLE_COVERAGE=ON -DCMAKE_CXX_COMPILER=clang++ ..
make && ctest
llvm-profdata merge -sparse default.profraw -o coverage.profdata
llvm-cov report ./test-binary -instr-profile=coverage.profdata
llvm-cov show ./test-binary -instr-profile=coverage.profdata --format=html > cov-report.html
```

---

## Go

**Coverage** — `go test -cover` (stdlib) + `go tool cover`:

```bash
# Coverage
go test -coverprofile=coverage.out -covermode=atomic ./...
go tool cover -func=coverage.out       # per-function + total
go tool cover -html=coverage.out -o coverage.html
```

No `go.mod` config required — flags only.

**Branch coverage caveat** — Go's built-in tooling reports **statement coverage only**. Set `quality_gates.branch_coverage_min` equal to `line_coverage_min` (statement % doubles as both metrics) or lower it. For true branch coverage, use [`gocov`](https://github.com/axw/gocov) or [`gocov-html`](https://github.com/matm/gocov-html) externally.

**Threshold check** — parse total from `go tool cover -func`:

```bash
COV=$(go tool cover -func=coverage.out | awk '/^total:/ {gsub(/%/,"",$3); print $3}')
awk -v cov="$COV" -v min=90 'BEGIN { exit (cov+0 >= min+0) ? 0 : 1 }'
```

---

## Language Presets

When using `init_project.py --lang <language>`:

| Language | Test Framework | Coverage Tool |
|----------|---------------|---------------|
| `python` | pytest | pytest-cov |
| `java` | junit | jacoco |
| `javascript` | jest | c8-jest |
| `typescript` | vitest | c8 |
| `c` | ctest | gcov |
| `cpp` / `c++` | gtest | gcov |
| `go` | go-test | go-cover |

## Default Thresholds

| Metric | Default | Rationale |
|--------|---------|-----------|
| Line coverage | >= 90% | Most production code paths must be tested |
| Branch coverage | >= 80% | Conditional logic must be exercised both ways |
