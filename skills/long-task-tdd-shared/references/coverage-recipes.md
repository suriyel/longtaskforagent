# 覆盖率与变异测试工具配置指南

多语言覆盖率跟踪和变异测试工具的配置说明。为新项目配置工具时阅读此文件。

## 多语言工具矩阵

| 语言 | 覆盖率工具 | 分支支持 | 变异工具 | 增量支持 |
|------|-----------|---------|---------|---------|
| Python | pytest-cov (coverage.py) | 是 | mutmut | 是（`--paths-to-mutate`） |
| Java | JaCoCo | 是 | PIT (pitest) | 是（`-DtargetClasses`） |
| JavaScript | c8 / nyc (Istanbul) | 是 | Stryker | 是（`--mutate` glob） |
| TypeScript | c8 / nyc (Istanbul) | 是 | Stryker | 是（`--mutate` glob） |
| C | gcov + lcov | 是（`--branch-probabilities`） | Mull | 部分（按文件过滤） |
| C++ | gcov + lcov / llvm-cov | 是 | Mull | 部分（按文件过滤） |
| Scala | scoverage-maven-plugin | 是（statement + branch） | — | — |

---

## Python

**覆盖率** — pytest-cov（封装 coverage.py）：

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

**变异** — mutmut：

```toml
# pyproject.toml (or setup.cfg)
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=short"
```

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## Java

**覆盖率** — JaCoCo：

Maven（`pom.xml`）：
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

Gradle（`build.gradle`）：
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

**变异** — PIT (pitest)：

Maven：
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

Gradle：
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

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## JavaScript

**覆盖率** — c8（原生 V8 覆盖率，推荐）或 nyc (Istanbul)：

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

**变异** — Stryker：

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

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## TypeScript

**覆盖率** — c8（原生 V8 覆盖率，推荐）或 nyc (Istanbul)：

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

**变异** — Stryker：

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

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## C

**覆盖率** — gcov + lcov：

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

CMake：
```cmake
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()
```

**变异** — Mull：

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

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## C++

**覆盖率** — gcov + lcov 或 llvm-cov：

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

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## Scala

**覆盖率** — scoverage-maven-plugin（对齐 Java preset 走 mvn，不引入 sbt）：

```xml
<!-- pom.xml -->
<properties>
  <scala.version>2.13.14</scala.version>
  <scala.compat.version>2.13</scala.compat.version>
</properties>

<build>
  <plugins>
    <plugin>
      <groupId>net.alchim31.maven</groupId>
      <artifactId>scala-maven-plugin</artifactId>
      <version>4.9.2</version>
      <executions>
        <execution>
          <goals><goal>compile</goal><goal>testCompile</goal></goals>
        </execution>
      </executions>
    </plugin>
    <plugin>
      <groupId>org.scoverage</groupId>
      <artifactId>scoverage-maven-plugin</artifactId>
      <version>2.0.4</version>
      <configuration>
        <scalaVersion>${scala.version}</scalaVersion>
        <minimumCoverage>90</minimumCoverage>
        <minimumCoverageBranchTotal>80</minimumCoverageBranchTotal>
        <failOnMinimumCoverage>true</failOnMinimumCoverage>
      </configuration>
    </plugin>
  </plugins>
</build>

<dependencies>
  <dependency>
    <groupId>org.scalatest</groupId>
    <artifactId>scalatest_${scala.compat.version}</artifactId>
    <version>3.2.19</version>
    <scope>test</scope>
  </dependency>
</dependencies>
```

`maven-surefire-plugin` 自动发现 ScalaTest `Suite` 子类（需在 pom 加 `WildcardSuite` 或 ScalaTest 自带的 runner 配置）。

运行：`mvn clean org.scoverage:scoverage-maven-plugin:report`

报告：`target/site/scoverage/{index.html, scoverage.xml}`；XML 根元素属性 `statement-rate` / `branch-rate` 可供脚本解析。

> 运行时命令：`python scripts/get_tool_commands.py feature-list.json`

---

## 按功能变异测试范围限定

当项目活跃功能数超过 `mutation_full_threshold` 时，质量门禁将变异测试范围限定为当前功能变更的文件**及**测试。这避免了对大项目中每个变异体运行整个测试套件（速度极慢）。

**原则**：仅变异已变更的源文件，每个变异体仅运行该功能的测试。当项目活跃功能数等于或低于阈值时运行完整变异测试。

### 识别功能测试文件

- 本功能 TDD 周期中创建/修改的测试文件
- 基于约定：如源文件为 `src/foo.ext`，测试可能为 `tests/test_foo.ext`
- 基于标记：如果项目使用测试标记/标签，按功能标记过滤
- Worker 将功能测试文件路径传递给 Quality SubAgent

### 各工具范围限定参考

| 工具 | 变异目标范围限定 | 测试范围限定机制 |
|------|-----------------|-----------------|
| mutmut | `--paths-to-mutate={files}` | `--runner='{test_runner} {test_files}'` |
| pitest | `-DtargetClasses={classes}` | `-DtargetTests={test_classes}` |
| stryker | `--mutate='{files}'` | `--coverageAnalysis perTest`（自动选择相关测试） |
| mull | `--filters={files}` | 构建功能专用测试二进制文件 |

### 各工具特别说明

- **mutmut** `--runner`：提供完整的测试执行命令，包括框架二进制文件和文件路径。`{test_runner}` 占位符解析为项目的测试运行器命令（如 `python -m pytest -x --tb=short`、`npx vitest run`）。
- **pitest** `-DtargetTests`：接受逗号分隔的 Java 类模式（如 `com.example.UserAuthTest,com.example.UserLoginTest`）。
- **Stryker** `--coverageAnalysis perTest`：Stryker 自动确定哪些测试覆盖每个变异体并仅运行那些测试。无需显式测试文件列表。需要 Stryker 6+。
- **mull**：编译测试二进制文件时仅链接功能相关的测试目标文件。这要求按功能范围构建单独的二进制文件。
