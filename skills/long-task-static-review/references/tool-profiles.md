# Static Analysis Tool Profiles

Each profile defines how to **detect**, **run**, and **parse** a specific static analysis tool. The main skill reads this document during Step 2 (Tool Detection). Adding a new tool means adding a new profile section following the template below.

**Core principle:** Detect config existence and infer run commands. Do **NOT** read config file contents — tools read their own configs at runtime.

---

## Profile Template

```
## Tool: <name>

### Detection
- Config files: [paths to check]
- Build integration: [how tool is integrated into Maven/Gradle/npm/etc.]
- Version detection: [how to determine tool version from build config]

### Build Systems
| Build System | Plugin/Dependency | Run Command |
|-------------|-------------------|-------------|

### Output Format
- Success indicator: [what output looks like when no violations]
- Violation line format: [pattern per build system]

### Fix Strategies
| Rule Category | Examples | Fix Approach | Behavioral Risk |
|--------------|----------|-------------|-----------------|
```

---

## Tool: Checkstyle

### Detection

**Config files** (check in order, use first found):

| Priority | Path | Notes |
|----------|------|-------|
| 1 | `config/checkstyle/checkstyle.xml` | Maven convention with configLocation |
| 2 | `checkstyle.xml` | Project root default |
| 3 | `src/main/resources/checkstyle.xml` | Classpath resource |
| 4 | Glob `**/checkstyle*.xml` | Fallback broad search |

Do **NOT** read the config file contents. Record the path only.

**Build integration:**

- **Maven**: Grep `pom.xml` for `maven-checkstyle-plugin` within `<plugins>` or `<pluginManagement>`
- **Gradle**: Grep `build.gradle` / `build.gradle.kts` for:
  - `id 'checkstyle'` or `id("checkstyle")`
  - `apply plugin: 'checkstyle'`

**Version detection:**

- **Maven** (check in order):
  1. Property: `<checkstyle.version>X.Y</checkstyle.version>` in `<properties>`
  2. Plugin dependency: `<dependency>` with `<artifactId>checkstyle</artifactId>` inside `maven-checkstyle-plugin` `<dependencies>` — read its `<version>`
  3. Plugin version: `<version>` on the `maven-checkstyle-plugin` itself (this is the plugin version, not Checkstyle version — note the distinction)
- **Gradle**:
  1. `checkstyle { toolVersion = 'X.Y' }` or `checkstyle { toolVersion 'X.Y' }`
  2. `checkstyleVersion = 'X.Y'`

If version cannot be determined: record as "unknown (using build tool default)".

### Build Systems

| Build System | Plugin | Run Command | Compile Command |
|-------------|--------|-------------|-----------------|
| Maven | `maven-checkstyle-plugin` | `mvn checkstyle:check` | `mvn compile -q` |
| Maven (multi-module) | `maven-checkstyle-plugin` | `mvn checkstyle:check` | `mvn compile -q` |
| Gradle | `id 'checkstyle'` | `gradle checkstyleMain` | `gradle compileJava -q` |
| Gradle (multi-module) | `id 'checkstyle'` | `gradle checkstyleMain` | `gradle compileJava -q` |

**Multi-module detection:**
- Maven: `<modules>` element in root `pom.xml`
- Gradle: `include` statements in `settings.gradle` / `settings.gradle.kts`

Maven `mvn checkstyle:check` runs recursively across modules by default. Gradle `gradle checkstyleMain` also runs across sub-projects.

### Output Format

**Maven — Success:**
```
[INFO] BUILD SUCCESS
```
No `[ERROR]` lines matching the Checkstyle violation pattern.

**Maven — Violations:**
```
[ERROR] src/main/java/com/example/Foo.java:[42,15] (whitespace) WhitespaceAround: 'if' is not followed by whitespace.
[ERROR] src/main/java/com/example/Foo.java:[58] (javadoc) MissingJavadocMethod: Missing a Javadoc comment.
```

Pattern: `[ERROR] <path>:[<line>(,<col>)] (<category>) <RuleName>: <message>`

Alternative pattern (older versions): `[ERROR] <path>:[<line>,<col>]: <message> [<RuleName>]`

**Gradle — Success:**
```
BUILD SUCCESSFUL
```

**Gradle — Violations:**
Console shows summary. Detailed violations in XML report:
- `build/reports/checkstyle/main.xml`
- `build/reports/checkstyle/test.xml`

Use `--console=plain` for parseable console output. Alternatively read the XML report.

### Violation Parsing

**From Maven output:**
- Each `[ERROR]` line following Checkstyle pattern
- File path: text between `[ERROR] ` and `:[line`
- Line number: first integer after `:`
- Column: second integer after `,` (optional)
- Rule name: text after `) ` before `:` (e.g., `WhitespaceAround`)
- Message: text after rule name and `: `

**From Gradle XML report:**
```xml
<file name="/absolute/path/Foo.java">
  <error line="42" column="15" severity="error" message="..." source="com.puppycrawl.tools.checkstyle.checks.whitespace.WhitespaceAroundCheck"/>
</file>
```
- File: `name` attribute on `<file>`
- Line: `line` attribute on `<error>`
- Column: `column` attribute
- Rule: last segment of `source` attribute (strip `Check` suffix)
- Message: `message` attribute

### Fix Strategies

| Rule Category | Example Rules | Fix Approach | Behavioral Risk |
|--------------|---------------|-------------|-----------------|
| **Whitespace** | `WhitespaceAround`, `WhitespaceAfter`, `NoWhitespaceBefore`, `NoWhitespaceAfter`, `GenericWhitespace`, `SingleSpaceSeparator` | Add or remove whitespace characters | None |
| **Indentation** | `Indentation`, `CommentsIndentation` | Adjust leading whitespace to match configured indent level | None |
| **Imports** | `AvoidStarImport`, `UnusedImports`, `RedundantImport`, `ImportOrder`, `CustomImportOrder`, `IllegalImport` | Expand star imports to explicit; remove unused/redundant; reorder per convention | None |
| **Naming** | `MethodName`, `MemberName`, `ParameterName`, `LocalVariableName`, `ConstantName`, `TypeName`, `PackageName` | Rename identifier to comply with pattern | **Low** — can break reflection, serialization, JNI, or external API contracts |
| **Javadoc** | `JavadocMethod`, `JavadocType`, `JavadocVariable`, `MissingJavadocMethod`, `MissingJavadocType`, `JavadocStyle`, `SummaryJavadoc` | Add or fix Javadoc comments | None |
| **Braces** | `NeedBraces`, `LeftCurly`, `RightCurly` | Add braces to single-line blocks; adjust brace placement | None |
| **Line length** | `LineLength` | Break long lines at logical points (after commas, operators) | None |
| **Modifier order** | `ModifierOrder`, `RedundantModifier` | Reorder modifiers per JLS order; remove redundant (e.g., `public` on interface methods) | None |
| **Empty blocks** | `EmptyBlock`, `EmptyCatchBlock` | Add descriptive comment or TODO in empty catch; for other empty blocks, add logic or comment | **Low** |
| **Magic numbers** | `MagicNumber` | Extract numeric literal to named `static final` constant | **Low** — changes class structure but not behavior |
| **Method length** | `MethodLength` | Extract logical sub-sections into private helper methods | **Medium** — structural change, may affect stack traces and debugging |
| **Class design** | `FinalClass`, `HideUtilityClassConstructor`, `OneTopLevelClass`, `VisibilityModifier` | Add `final`; add private constructor; adjust visibility | **Low** |
| **Coding style** | `OneStatementPerLine`, `MultipleVariableDeclarations`, `ArrayTypeStyle`, `UpperEll`, `FallThrough` | Split statements/declarations; fix array bracket placement; use `L` suffix; add `// fall through` | None |
| **Annotations** | `AnnotationLocation`, `AnnotationUseStyle`, `MissingOverride` | Move annotations; add `@Override` | None |

**Risk handling:**
- **None**: Apply without hesitation
- **Low**: Apply but check if the file uses reflection (`Class.forName`, `getMethod`, `getDeclaredField`), serialization (`Serializable`, `@JsonProperty`, `@Column`), or JNI. If so, skip the specific rename and log as "manual review needed"
- **Medium**: Apply conservatively. If the method is >100 lines over the limit, extract only the most obvious logical sub-sections. If unclear, log as "manual review needed"

---

## Tool: ESLint [STUB — Not Yet Implemented]

### Detection
- Config files: `.eslintrc`, `.eslintrc.js`, `.eslintrc.json`, `.eslintrc.yml`, `eslint.config.js`, `eslint.config.mjs`, `eslint.config.ts`
- Build integration: `eslint` in `devDependencies` of `package.json`
- Version detection: `node_modules/eslint/package.json` → `version` field; or `npx eslint --version`
- Run command: `npx eslint . --format stylish`
- Auto-fix command: `npx eslint . --fix` (ESLint has built-in auto-fix for many rules)

### Notes
This profile is a placeholder for future implementation. ESLint's `--fix` flag handles many violations automatically, so the scan-fix loop may be simpler.

---

## Tool: Pylint [STUB — Not Yet Implemented]

### Detection
- Config files: `.pylintrc`, `pylintrc`, `pyproject.toml [tool.pylint]`, `setup.cfg [pylint]`
- Build integration: `pylint` in `requirements-dev.txt`, `pyproject.toml [tool.poetry.group.dev.dependencies]`, or `setup.cfg [options.extras_require]`
- Version detection: `pylint --version`
- Run command: `pylint src/` or `pylint {package_name}/`

### Notes
This profile is a placeholder. Pylint violations range from style (easily fixable) to design (requires human judgment). Consider pairing with `autopep8` or `black` for formatting-only fixes.

---

## Tool: Ruff [STUB — Not Yet Implemented]

### Detection
- Config files: `ruff.toml`, `pyproject.toml [tool.ruff]`
- Build integration: `ruff` in dev dependencies
- Version detection: `ruff version`
- Run command: `ruff check .`
- Auto-fix command: `ruff check . --fix` (Ruff has built-in auto-fix for many rules)

### Notes
This profile is a placeholder. Ruff is extremely fast and has auto-fix for ~300 rules, making the scan-fix loop potentially very efficient.

---

## Tool: Biome [STUB — Not Yet Implemented]

### Detection
- Config files: `biome.json`, `biome.jsonc`
- Build integration: `@biomejs/biome` in `devDependencies` of `package.json`
- Version detection: `npx biome --version`
- Run command: `npx biome check .`
- Auto-fix command: `npx biome check . --apply` (Biome has built-in formatter and linter fixes)

### Notes
This profile is a placeholder. Biome combines formatting + linting and has extensive auto-fix support.
