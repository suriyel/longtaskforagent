# 静态分析工具配置

每个配置定义了如何**检测**、**运行**和**解析**特定静态分析工具。主 skill 在步骤 2（工具检测）期间读取本文档。添加新工具意味着按照下方模板添加新的配置章节。

**核心原则：** 检测配置是否存在并推断运行命令。**不读取**配置文件内容 —— 工具在运行时自行读取其配置。

---

## 配置模板

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

### 检测

**配置文件**（按顺序检查，使用首个找到的）：

| 优先级 | 路径 | 说明 |
|----------|------|-------|
| 1 | `config/checkstyle/checkstyle.xml` | Maven 约定，配合 configLocation |
| 2 | `checkstyle.xml` | 项目根目录默认 |
| 3 | `src/main/resources/checkstyle.xml` | Classpath 资源 |
| 4 | Glob `**/checkstyle*.xml` | 回退广泛搜索 |

**不读取**配置文件内容。仅记录路径。

**构建集成：**

- **Maven**：在 `pom.xml` 的 `<plugins>` 或 `<pluginManagement>` 中 Grep 搜索 `maven-checkstyle-plugin`
- **Gradle**：在 `build.gradle` / `build.gradle.kts` 中 Grep 搜索：
  - `id 'checkstyle'` 或 `id("checkstyle")`
  - `apply plugin: 'checkstyle'`

**版本检测：**

- **Maven**（按顺序检查）：
  1. 属性：`<properties>` 中的 `<checkstyle.version>X.Y</checkstyle.version>`
  2. 插件依赖：`maven-checkstyle-plugin` 的 `<dependencies>` 中 `<artifactId>checkstyle</artifactId>` 的 `<dependency>` —— 读取其 `<version>`
  3. 插件版本：`maven-checkstyle-plugin` 本身的 `<version>`（这是插件版本，非 Checkstyle 版本 —— 注意区分）
- **Gradle**：
  1. `checkstyle { toolVersion = 'X.Y' }` 或 `checkstyle { toolVersion 'X.Y' }`
  2. `checkstyleVersion = 'X.Y'`

如果无法确定版本：记录为"未知（使用构建工具默认值）"。

### 构建系统

| 构建系统 | 插件 | 运行命令 | 编译命令 |
|-------------|--------|-------------|-----------------|
| Maven | `maven-checkstyle-plugin` | `mvn checkstyle:check` | `mvn compile -q` |
| Maven（多模块） | `maven-checkstyle-plugin` | `mvn checkstyle:check` | `mvn compile -q` |
| Gradle | `id 'checkstyle'` | `gradle checkstyleMain` | `gradle compileJava -q` |
| Gradle（多模块） | `id 'checkstyle'` | `gradle checkstyleMain` | `gradle compileJava -q` |

**多模块检测：**
- Maven：根 `pom.xml` 中的 `<modules>` 元素
- Gradle：`settings.gradle` / `settings.gradle.kts` 中的 `include` 语句

Maven `mvn checkstyle:check` 默认递归跨模块运行。Gradle `gradle checkstyleMain` 也跨子项目运行。

### 输出格式

**Maven —— 成功：**
```
[INFO] BUILD SUCCESS
```
无匹配 Checkstyle 违规模式的 `[ERROR]` 行。

**Maven —— 违规：**
```
[ERROR] src/main/java/com/example/Foo.java:[42,15] (whitespace) WhitespaceAround: 'if' is not followed by whitespace.
[ERROR] src/main/java/com/example/Foo.java:[58] (javadoc) MissingJavadocMethod: Missing a Javadoc comment.
```

模式：`[ERROR] <path>:[<line>(,<col>)] (<category>) <RuleName>: <message>`

替代模式（旧版本）：`[ERROR] <path>:[<line>,<col>]: <message> [<RuleName>]`

**Gradle —— 成功：**
```
BUILD SUCCESSFUL
```

**Gradle —— 违规：**
控制台显示摘要。详细违规在 XML 报告中：
- `build/reports/checkstyle/main.xml`
- `build/reports/checkstyle/test.xml`

使用 `--console=plain` 获取可解析的控制台输出。也可以读取 XML 报告。

### 违规解析

**从 Maven 输出：**
- 每个匹配 Checkstyle 模式的 `[ERROR]` 行
- 文件路径：`[ERROR] ` 和 `:[line` 之间的文本
- 行号：`:` 后的第一个整数
- 列号：`,` 后的第二个整数（可选）
- 规则名称：`) ` 后 `:` 前的文本（例如 `WhitespaceAround`）
- 消息：规则名称和 `: ` 后的文本

**从 Gradle XML 报告：**
```xml
<file name="/absolute/path/Foo.java">
  <error line="42" column="15" severity="error" message="..." source="com.puppycrawl.tools.checkstyle.checks.whitespace.WhitespaceAroundCheck"/>
</file>
```
- 文件：`<file>` 上的 `name` 属性
- 行号：`<error>` 上的 `line` 属性
- 列号：`column` 属性
- 规则：`source` 属性的最后一段（去掉 `Check` 后缀）
- 消息：`message` 属性

### 修复策略

| 规则类别 | 示例规则 | 修复方法 | 行为风险 |
|--------------|---------------|-------------|-----------------|
| **空白** | `WhitespaceAround`、`WhitespaceAfter`、`NoWhitespaceBefore`、`NoWhitespaceAfter`、`GenericWhitespace`、`SingleSpaceSeparator` | 添加或删除空白字符 | 无 |
| **缩进** | `Indentation`、`CommentsIndentation` | 调整前导空白以匹配配置的缩进级别 | 无 |
| **导入** | `AvoidStarImport`、`UnusedImports`、`RedundantImport`、`ImportOrder`、`CustomImportOrder`、`IllegalImport` | 展开星号导入为显式导入；删除未使用/冗余导入；按约定重新排序 | 无 |
| **命名** | `MethodName`、`MemberName`、`ParameterName`、`LocalVariableName`、`ConstantName`、`TypeName`、`PackageName` | 重命名标识符以符合模式 | **低** —— 可能破坏反射、序列化、JNI 或外部 API 契约 |
| **Javadoc** | `JavadocMethod`、`JavadocType`、`JavadocVariable`、`MissingJavadocMethod`、`MissingJavadocType`、`JavadocStyle`、`SummaryJavadoc` | 添加或修复 Javadoc 注释 | 无 |
| **花括号** | `NeedBraces`、`LeftCurly`、`RightCurly` | 为单行块添加花括号；调整花括号位置 | 无 |
| **行长度** | `LineLength` | 在逻辑断点处换行（逗号、运算符后） | 无 |
| **修饰符顺序** | `ModifierOrder`、`RedundantModifier` | 按 JLS 顺序重排修饰符；删除冗余修饰符（例如接口方法上的 `public`） | 无 |
| **空块** | `EmptyBlock`、`EmptyCatchBlock` | 在空 catch 中添加描述性注释或 TODO；对其他空块添加逻辑或注释 | **低** |
| **魔法数字** | `MagicNumber` | 将数字字面量提取为命名的 `static final` 常量 | **低** —— 改变类结构但不改变行为 |
| **方法长度** | `MethodLength` | 将逻辑子段提取为私有辅助方法 | **中等** —— 结构性变更，可能影响堆栈跟踪和调试 |
| **类设计** | `FinalClass`、`HideUtilityClassConstructor`、`OneTopLevelClass`、`VisibilityModifier` | 添加 `final`；添加私有构造函数；调整可见性 | **低** |
| **编码风格** | `OneStatementPerLine`、`MultipleVariableDeclarations`、`ArrayTypeStyle`、`UpperEll`、`FallThrough` | 拆分语句/声明；修复数组括号位置；使用 `L` 后缀；添加 `// fall through` | 无 |
| **注解** | `AnnotationLocation`、`AnnotationUseStyle`、`MissingOverride` | 移动注解；添加 `@Override` | 无 |

**风险处理：**
- **无**：毫不犹豫地应用
- **低**：应用但检查文件是否使用了反射（`Class.forName`、`getMethod`、`getDeclaredField`）、序列化（`Serializable`、`@JsonProperty`、`@Column`）或 JNI。如果是，跳过该特定重命名并记录为"需要人工审查"
- **中等**：保守应用。如果方法超出限制 100 行以上，仅提取最明显的逻辑子段。如果不确定，记录为"需要人工审查"

---

## Tool: ESLint [桩 —— 尚未实现]

### 检测
- 配置文件：`.eslintrc`、`.eslintrc.js`、`.eslintrc.json`、`.eslintrc.yml`、`eslint.config.js`、`eslint.config.mjs`、`eslint.config.ts`
- 构建集成：`package.json` 的 `devDependencies` 中的 `eslint`
- 版本检测：`node_modules/eslint/package.json` -> `version` 字段；或 `npx eslint --version`
- 运行命令：`npx eslint . --format stylish`
- 自动修复命令：`npx eslint . --fix`（ESLint 内置了许多规则的自动修复）

### 说明
此配置是未来实现的占位符。ESLint 的 `--fix` 标志可自动处理许多违规，因此扫描-修复循环可能更简单。

---

## Tool: Pylint [桩 —— 尚未实现]

### 检测
- 配置文件：`.pylintrc`、`pylintrc`、`pyproject.toml [tool.pylint]`、`setup.cfg [pylint]`
- 构建集成：`requirements-dev.txt`、`pyproject.toml [tool.poetry.group.dev.dependencies]` 或 `setup.cfg [options.extras_require]` 中的 `pylint`
- 版本检测：`pylint --version`
- 运行命令：`pylint src/` 或 `pylint {package_name}/`

### 说明
此配置是占位符。Pylint 违规从样式（易修复）到设计（需要人工判断）不等。考虑配合 `autopep8` 或 `black` 仅做格式化修复。

---

## Tool: Ruff [桩 —— 尚未实现]

### 检测
- 配置文件：`ruff.toml`、`pyproject.toml [tool.ruff]`
- 构建集成：开发依赖中的 `ruff`
- 版本检测：`ruff version`
- 运行命令：`ruff check .`
- 自动修复命令：`ruff check . --fix`（Ruff 内置了约 300 条规则的自动修复）

### 说明
此配置是占位符。Ruff 速度极快且约 300 条规则支持自动修复，使得扫描-修复循环可能非常高效。

---

## Tool: Biome [桩 —— 尚未实现]

### 检测
- 配置文件：`biome.json`、`biome.jsonc`
- 构建集成：`package.json` 的 `devDependencies` 中的 `@biomejs/biome`
- 版本检测：`npx biome --version`
- 运行命令：`npx biome check .`
- 自动修复命令：`npx biome check . --apply`（Biome 内置了格式化和检查修复）

### 说明
此配置是占位符。Biome 结合了格式化 + 代码检查，且有广泛的自动修复支持。
