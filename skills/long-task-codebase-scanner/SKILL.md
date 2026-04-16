---
name: long-task-codebase-scanner
description: "Use before requirements or design in brownfield projects (no docs/rules/) — scan codebase conventions (coding style, constraints, build patterns, commit format)"
---

**LANGUAGE RULE**: You MUST respond in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Code identifiers and JSON field names remain in English.

# Codebase Convention Scanner

Scan an existing project's source code to extract and document established coding conventions, library constraints, build patterns, and commit standards. Output enables downstream skills to produce code that conforms to the project's existing patterns.

**Your bias should be toward discovering constraints.** Especially 2nd-party (internal) library mandates that replace standard library or 3rd-party APIs — missing these causes non-compliant code downstream.

## Invocation Modes

### Pipeline Mode (default)

Invoked by the `using-long-task` router when detection rule 5b or 7b triggers (brownfield project, no existing `docs/rules/`). Receives `--next-skill` argument specifying the downstream skill to chain to:

- Rule 7b (no SRS): `--next-skill long-task-requirements`
- Rule 5b (SRS exists, no design): `--next-skill long-task-design`

After scanning, the skill chains to the specified next skill.

### Standalone Mode

User invokes directly (e.g., to re-scan after codebase changes). No `--next-skill` argument — the skill performs the scan and stops without chaining.

## Design Principles

- **Read-only** — do NOT modify any source files, configs, or git state (except creating `docs/rules/`)
- **Observe, don't prescribe** — document what the project currently does, not what it should do
- **Evidence-based** — every convention claim must cite concrete `file:line` examples
- **Handle mixed conventions** — if the project is inconsistent, report all patterns with their frequency %
- **Respect .gitignore** — do not scan ignored directories
- **Output budget** — each output file MUST be ≤ 200 lines (focus on LLM-consumable summary tables, not exhaustive listings)

## Process

### Step 1: Create Output Directory

```bash
mkdir -p docs/rules/
```

### Step 2: Detect Language, Framework & Scan Depth

Analyze file extensions and dependency manifests (`package.json`, `requirements.txt`, `pom.xml`, `Cargo.toml`, `go.mod`, `*.csproj`). Determine scan depth:

| LOC Range | Depth | Files per Category |
|-----------|-------|--------------------|
| < 1,000 | Lightweight | Top 20 (most recently modified) |
| 1,000–10,000 | Standard | Top 50 (recent + diverse directories) |
| > 10,000 | Deep | Top 100 + all config files (full coverage) |

### Step 3: Sample Selection

Select a representative sample of source files based on scan depth (Step 2). Include files from different directories to capture organizational patterns. Include both implementation and test files.

Pre-filter: exclude `.git/`, `node_modules/`, `venv/`, `dist/`, `build/` directories.

### Step 4: Coding Style Analysis → `docs/rules/coding-style.md`

Analyze and document:

**Naming Conventions** — for each category, detect the dominant pattern:

| Category | What to Detect |
|----------|---------------|
| Variables | camelCase / snake_case / PascalCase / SCREAMING_SNAKE |
| Functions/Methods | camelCase / snake_case / PascalCase |
| Classes/Types | PascalCase / camelCase |
| Constants | SCREAMING_SNAKE / PascalCase / camelCase |
| Files | kebab-case / snake_case / camelCase / PascalCase |
| Directories | kebab-case / snake_case / singular / plural |
| Private members | underscore prefix / no prefix / # prefix |
| Boolean names | is/has/should prefix patterns |

For each: report dominant pattern, consistency % (how many files follow it), 2-3 concrete examples.

**Formatting** — detect:
- Indentation: spaces vs tabs, indent width (2/4/8)
- Line length: P95 measured across sampled files
- Bracket style: same-line (K&R) vs next-line (Allman)
- Trailing commas, semicolons, quote style (JS/TS/Python specific)
- Blank lines between functions/methods

**Formatter Configuration** — check for config files: `.prettierrc`, `.editorconfig`, `.clang-format`, `pyproject.toml [tool.black]`, `rustfmt.toml`, `biome.json`. If found, reference the file path — do NOT open or parse the content (the tool reads its own config).

**File & Directory Organization** — document:
- Top-level directory structure with purpose annotations
- Code organization pattern: by-feature / by-layer / by-type / hybrid
- Test file location: co-located vs separate `tests/` directory
- Test file naming: `test_*.py` / `*.test.ts` / `*_test.go` / `*Test.java`

### Step 5: Coding Constraints Analysis → `docs/rules/coding-constraints.md`

This is the **most critical** output. Focus on constraints that would cause non-compliant code if missed.

**2nd-Party (Internal) Library Detection** — scan import/require statements to identify:
- Internal libraries that wrap or replace standard library APIs (e.g., `@company/http` replacing `fetch`; `internal.logger` replacing `console.log`; custom ORM replacing direct DB queries)
- Detection heuristic: imports from non-public-registry packages (scoped packages like `@company/*`, relative workspace imports, internal module paths that don't map to known npm/PyPI packages)
- For each found: document Domain, Internal Library name, what it Replaces, Import Pattern, usage frequency

**3rd-Party Library Constraints** — analyze dependency manifests:
- Version pinning strategy: exact (`==2.31.0`) vs range (`^7.4`) vs unpinned
- Identify the chosen library for common domains (HTTP, logging, testing, serialization, date/time, validation)
- Flag any deprecated libraries still in use

**Prohibited APIs / Libraries** — detect patterns suggesting certain APIs are banned:
- Standard library APIs that are never used despite being the natural choice (e.g., no `console.log` anywhere, only `logger.info`)
- 3rd-party libraries present in lock files but not imported (replaced by internal alternatives)
- Lint rules that ban specific APIs (detected via config file existence — see Static Analysis Tools below)

**Static Analysis Tools** — detect config files for linters and static analyzers. For each found:
- Record: Tool name, Config file path, Run command (inferred from build scripts or standard invocation)
- **Do NOT open or read the config file contents** — the tool reads its own config at runtime
- Common configs to detect:

| Tool | Config Files | Typical Run Command |
|------|-------------|-------------------|
| ESLint | `.eslintrc*`, `.eslintrc.json`, `eslint.config.*` | `npx eslint .` |
| Prettier | `.prettierrc*` | `npx prettier --check .` |
| Pylint | `.pylintrc`, `pylintrc` | `pylint src/` |
| Flake8 | `.flake8`, `setup.cfg [flake8]` | `flake8 src/` |
| MyPy | `mypy.ini`, `pyproject.toml [tool.mypy]` | `mypy src/` |
| Ruff | `ruff.toml`, `pyproject.toml [tool.ruff]` | `ruff check .` |
| Clippy | `clippy.toml` | `cargo clippy` |
| Checkstyle | `checkstyle.xml` | `mvn checkstyle:check` or `gradle checkstyleMain` |
| Biome | `biome.json` | `npx biome check .` |
| golangci-lint | `.golangci.yml` | `golangci-lint run` |
| SwiftLint | `.swiftlint.yml` | `swiftlint` |
| ktlint | `.editorconfig` | `ktlint` |

**Error Handling Pattern** — identify:
- Dominant pattern: try/catch, Result/Either types, error codes, panic/recover
- Custom Error/Exception classes (names, hierarchy)
- Centralized error handling (middleware, global handler)
- Error logging patterns

**Import Organization** — detect grouping order:
- stdlib → 2nd-party → 3rd-party → local (or other ordering)
- Absolute vs relative imports
- Blank line separators between groups

**Comment/Documentation Style** — detect:
- Docstring format: JSDoc, Google-style, NumPy-style, Javadoc, Rustdoc
- Usage frequency: what % of public functions have docs
- Position: above declaration, inline

**Type Annotations** — detect:
- Strict vs optional vs none
- TypeScript: `strict`, `strictNullChecks`, etc. (from tsconfig presence)
- Python: type hints usage frequency

**Testing Conventions** — detect:
- Test framework (from imports AND config files — see Testing & Quality Tools in Step 6)
- Fixture/setup patterns (shared fixtures, setup/teardown, factory functions)
- Assertion style (assert, expect, should) — with consistency %
- Mock framework (from imports: unittest.mock, Mockito, jest.fn, vi.fn, gmock)
- Test grouping (describe/it, test classes, flat functions)
- Test naming convention: `test_*.py` / `*.test.ts` / `*Test.java` / `*_test.go`
- Test directory structure: co-located vs separate `tests/` / `test/` / `__tests__` / `src/test/java/`

### Step 6: Build & Compilation Analysis → `docs/rules/build-and-compilation.md`

**Build System** — identify:
- Build tool: Makefile, CMake, Gradle, Maven, npm/yarn/pnpm scripts, Cargo, go build, Bazel
- Key commands: build, test, lint, format, clean (extract from scripts/Makefile/package.json)
- Compilation flags and targets

**Packaging** — detect:
- Container: Dockerfile, docker-compose.yml
- Package publishing: setup.py, pyproject.toml, npm publish config, Cargo.toml
- Distribution format

**Pre-commit Hooks** — detect:
- `.pre-commit-config.yaml`, `.husky/`, `lefthook.yml`, `.githooks/`
- List configured hooks

**Environment Management** — detect:
- Dockerfile, devcontainer.json, nix, `.tool-versions`, `.node-version`, `.python-version`
- Package manager: npm/yarn/pnpm/bun (JS); pip/poetry/pipenv/uv (Python); go mod; cargo

**Code Generation** — detect directories/configs for:
- protobuf, OpenAPI/Swagger, GraphQL codegen, database migration generators
- **Mark generated directories** — downstream skills should exclude these from convention checks

**Testing & Quality Tools** — detect config files for test frameworks, coverage tools, and mutation testing tools. For each found:
- Record: Tool name, Category (test-framework / coverage / mutation), Config file path, Run command (inferred from build scripts or standard invocation)
- **Do NOT open or read the config file contents** — the tool reads its own config at runtime
- Additionally detect test runner commands from build scripts (`package.json "scripts.test"`, Makefile `test:` target, `pom.xml` surefire-plugin, etc.)
- Common configs to detect:

| Category | Tool | Config Files | Typical Run Command |
|----------|------|-------------|---------------------|
| Test Framework | pytest | `pyproject.toml [tool.pytest]`, `pytest.ini`, `setup.cfg [tool:pytest]`, `conftest.py` | `pytest` |
| Test Framework | JUnit | `pom.xml (surefire-plugin)`, `build.gradle (test task)` | `mvn test` / `gradle test` |
| Test Framework | Jest | `jest.config.*`, `package.json [jest]` | `npx jest` |
| Test Framework | Vitest | `vitest.config.*`, `vite.config.* [test]` | `npx vitest run` |
| Test Framework | gtest/Catch2 | `CMakeLists.txt (GTest/Catch2)` | `ctest --test-dir build` |
| Coverage | pytest-cov | `pyproject.toml [tool.coverage]`, `.coveragerc` | `pytest --cov=src --cov-branch` |
| Coverage | JaCoCo | `pom.xml (jacoco-maven-plugin)`, `build.gradle (jacoco)` | `mvn test jacoco:report` |
| Coverage | c8 | `package.json [c8]`, `.c8rc.json` | `npx c8 ...` |
| Coverage | nyc/Istanbul | `.nycrc`, `.nycrc.json`, `package.json [nyc]` | `npx nyc ...` |
| Coverage | gcov/lcov | `Makefile (--coverage)`, `CMakeLists.txt (ENABLE_COVERAGE)` | `gcov + lcov` |
| Mutation | mutmut | `pyproject.toml [tool.mutmut]`, `setup.cfg [mutmut]` | `mutmut run` |
| Mutation | pitest/PIT | `pom.xml (pitest-maven)`, `build.gradle (pitest)` | `mvn pitest:mutationCoverage` |
| Mutation | Stryker | `stryker.conf.json`, `stryker.conf.js`, `stryker.conf.mjs` | `npx stryker run` |
| Mutation | Mull | `mull.yml` | `mull-runner ./test-binary` |

**Test Runner Commands** — extract from build scripts:

| Build System | Where to Look | Example |
|-------------|--------------|---------|
| npm/yarn/pnpm | `package.json` → `scripts.test`, `scripts.test:cov`, `scripts.test:mutation` | `"test": "vitest run"` |
| Maven | `pom.xml` → surefire plugin config | `mvn test` |
| Gradle | `build.gradle` → `test` task | `gradle test` |
| Make | `Makefile` → `test:` target | `make test` |
| CMake/CTest | `CMakeLists.txt` → `add_test()` / `enable_testing()` | `ctest --test-dir build` |

### Step 7: Generate Index → `docs/rules/README.md`

Create an index file linking all 3 documents with a scan summary:

```markdown
# Codebase Convention Rules

> Auto-generated by long-task-codebase-scanner on YYYY-MM-DD.
> These documents capture the project's existing conventions.
> Edit freely — downstream skills read these during Design and Worker phases.

## Documents

| Document | Description |
|----------|-------------|
| [coding-style.md](coding-style.md) | Naming, formatting, file organization |
| [coding-constraints.md](coding-constraints.md) | 2/3方件 constraints, static analysis tools, error handling, imports |
| [build-and-compilation.md](build-and-compilation.md) | Build system, packaging, environment |

## Key Findings Summary

- **Languages**: [list]
- **Internal Libraries (2nd-party)**: [count] found — [brief list]
- **Prohibited APIs**: [count] detected
- **Static Analysis Tools**: [list]
- **Test Framework**: [detected name or "none detected"]
- **Coverage Tool**: [detected name or "none detected"]
- **Mutation Tool**: [detected name or "none detected"]
- **Build System**: [name]
```

### Step 8: Validate Results

Verify ≥1 output file exists in `docs/rules/`. If the scan encountered issues and could not produce all files, write minimal stubs for missing files (non-blocking — scan is best-effort).

### Step 10: User Review

Present findings via `AskUserQuestion`:
- Concise summary of key findings (especially 2nd/3rd-party constraints and prohibited APIs)
- Ask user to confirm or edit `docs/rules/` files before continuing

### Step 11: Chain to Next Skill (Pipeline Mode Only)

If `--next-skill` was provided:
- `Skill(skill="long-task:<next_skill>")`

If no `--next-skill` (standalone mode): stop here.

## Output File Format

Each output file follows this structure:

```markdown
# [Title]

> Auto-generated by codebase scan on YYYY-MM-DD. Review and adjust as needed.
> Source: [N files sampled from M total]
> **Priority**: Framework/Design doc requirements > Linter/Formatter config > Source code observations.
> Conflicts with Design doc are marked with "⚠ Override" annotations.

## Section 1
[Content with evidence tables]

## Section N
[Content]

---
*Scanner: long-task-codebase-scanner | Depth: [level] | Files sampled: N*
```

## Multi-Language / Monorepo Handling

- **Multiple languages**: describe conventions per language in separate subsections
- **Monorepo**: identify sub-package boundaries; note convention differences across modules
- **Generated code directories** (protobuf output, codegen, etc.): mark as excluded — do not use as convention source; list in build-and-compilation.md for downstream exclusion

## Rules

- **Read-only** — do NOT modify any source files, configs, or git history
- **No config content reading for static analysis tools** — only detect tool name + config path + run command. The tool reads its own config at runtime.
- **Evidence-based** — every convention claim needs file:line examples
- **Output budget ≤ 200 lines per file** — use summary tables, not exhaustive listings
- **Scan efficiency** — use Glob for file discovery, Grep for pattern matching, Read for file inspection, Bash for git commands
- **Respect .gitignore** — do not scan ignored directories
- **No judgment** — document patterns as-is, even if they seem inconsistent or outdated

## Integration

- **Called by**: `using-long-task` router (when rule 5b or 7b triggers — brownfield, no `docs/rules/`)
- **Reads**: Source files, dependency manifests, git history
- **Chains to**: `long-task-requirements` (rule 7b) or `long-task-design` (rule 5b) — in pipeline mode; nothing in standalone mode
- **Produces**: `docs/rules/coding-style.md`, `docs/rules/coding-constraints.md`, `docs/rules/build-and-compilation.md`, `docs/rules/README.md`
- **Downstream consumers**: Design skill merges rules into Design §11; Init skill cross-checks tech_stack against build-and-compilation.md Testing & Quality Tools table; Worker skill references Design §11 during TDD
