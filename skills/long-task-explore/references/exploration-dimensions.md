# 探索维度 — 执行指南（Exploration Dimensions Execution Guide）

本文件为 6 个探索维度分别提供详细分析说明。SubAgent（codebase-analyzer、codebase-pattern-finder）参考本指南以确保一致、基于证据的分析。

**核心原则**：记录**现状**，而非**应然**。每条主张都必须引用 `file:line`。

---

## 维度 1：架构概览（Architecture Overview）

**负责**：codebase-analyzer

### 分析内容

**模块分解**
- 按目录结构识别顶层模块 / 包
- 对每个模块：名称、目录路径、大致文件数、主要职责（1 句话）
- 检测组织模式：按功能 / 按层 / 按类型 / 混合

**架构模式检测**

| Pattern | Detection Signals |
|---------|-------------------|
| MVC | 目录名为 `models/`、`views/`、`controllers/` 或框架等价物（Django views、Rails controllers、Spring @Controller） |
| Layered | 清晰分为 `presentation/`、`business/`/`service/`、`data/`/`repository/` 目录 |
| Hexagonal/Clean | `ports/`、`adapters/`、`domain/`、`infrastructure/` 目录；接口在领域边界 |
| Microservices | 多个独立的 `service-*/` 目录，各自有依赖清单 |
| Event-driven | 事件总线 / emitter 模式、消息队列消费者 / 生产者、pub-sub |
| Monolith | 单一部署单元、共享数据库、无服务边界 |
| Plugin | 插件注册、hook 系统、扩展点 |

用证据报告**主导模式**。若混合，报告主要 + 次要。

**模块依赖图**
- 追踪模块间 import（一个模块从另一个模块导入）
- 产出 Mermaid `graph TD` 展示模块到模块的依赖
- 识别最高 fan-in（被最多依赖）与最高 fan-out（依赖最多）的模块

**设计模式实例**
- 扫描常见模式：Factory、Strategy、Observer、Repository、Singleton、Builder、Decorator、Middleware
- 对每一项：模式名称、file:line、简短证据（例如 "Factory method `createUser()` at `src/factories/user.ts:15`"）
- 仅报告具有清晰结构证据的模式；不要臆测

### 输出格式

```markdown
## Architecture Overview

### Module Decomposition
| Module | Path | Files | Responsibility |
|--------|------|-------|----------------|

### Architecture Pattern
**Primary**: [pattern] — [evidence summary]
**Secondary**: [pattern, if any] — [evidence summary]

### Module Dependency Graph
```mermaid
graph TD
  A[module-a] --> B[module-b]
  ...
```

### Design Patterns Found
| Pattern | Location | Evidence |
|---------|----------|----------|
```

---

## 维度 2：入口点与 API 表面（Entry Points & API Surface）

**负责**：codebase-analyzer

### 分析内容

**应用入口点**

| Language | Detection Pattern |
|----------|-------------------|
| Python | `if __name__ == "__main__"`、`@click.command`、`@app.command`、`def main()`、setup.py/pyproject.toml 中的 `entry_points` |
| JavaScript/TypeScript | package.json 中的 `"main"` / `"bin"`、Express/Fastify 的 `app.listen()`、Next.js 的 `pages/` 或 `app/` |
| Java | `public static void main(String[])`、Spring `@SpringBootApplication`、`@RestController` |
| Go | `func main()`、`http.ListenAndServe`、Cobra 命令 |
| Rust | `fn main()`、`#[tokio::main]`、Actix/Axum router 配置 |
| C/C++ | `int main()`、`WinMain` |

每个入口点：file:line、类型（CLI/HTTP/worker/scheduled）、简短描述。

**公共 API 表面**

| Framework | Endpoint Detection |
|-----------|-------------------|
| Express/Fastify/Koa | `app.get/post/put/delete()`、`router.*()` |
| Django | `urlpatterns`、`@api_view` |
| Flask | `@app.route`、`@blueprint.route` |
| Spring | `@GetMapping`、`@PostMapping`、`@RequestMapping` |
| FastAPI | `@app.get/post`、`@router.*` |
| gRPC | `.proto` 文件中的 `service` 定义 |
| GraphQL | `type Query`、`type Mutation`、resolver 文件 |
| Go net/http | `http.HandleFunc`、`mux.Handle`、Gin/Chi 路由注册 |

每个端点：method、路径 / 名称、handler file:line、鉴权（若可检测）。

**配置表面**
- 环境变量读取：`os.getenv`、`process.env.*`、`os.Getenv`、`std::env`
- 配置文件：`.env`、`config.yaml`、`application.properties`、`settings.py`
- Feature flag：任何开关 / flag 模式

**插件 / 扩展点**
- Middleware 链、事件 hook、插件注册表

### 输出格式

```markdown
## Entry Points & API Surface

### Entry Points
| Type | Location | Description |
|------|----------|-------------|

### API Endpoints
| Method | Path | Handler | Auth |
|--------|------|---------|------|

### Configuration
| Source | Key/File | Location | Description |
|--------|----------|----------|-------------|
```

---

## 维度 3：数据流与状态管理（Data Flow & State Management）

**负责**：codebase-analyzer

### 分析内容

**数据模型**

| ORM/Framework | Detection Pattern |
|---------------|-------------------|
| SQLAlchemy | `class X(Base)`、`class X(db.Model)` |
| Django ORM | `class X(models.Model)` |
| TypeORM | `@Entity()`、`@Column()` |
| Prisma | `schema.prisma` 中的 `model X { ... }` |
| Mongoose | `new Schema({...})`、`mongoose.model()` |
| GORM | 带 `gorm` tag 的 struct |
| Protobuf | `.proto` 中的 `message X { ... }` |
| GraphQL | schema 文件中的 `type X { ... }` |

每个模型：名称、file:line、关键字段（前 5 个）、与其他模型的关系。

**数据流路径**
- 至少追踪 1-2 条代表性请求路径：入口 → 校验 → 业务逻辑 → 持久化 → 响应
- 为最重要的流生成 Mermaid `flowchart LR`

**状态管理**
- 前端：Redux、Zustand、MobX、Vuex/Pinia、Svelte stores、React Context
- 后端：session 存储、内存缓存、无状态设计
- 数据库：SQL、NoSQL、key-value、文件型

**外部数据集成**
- API 客户端（HTTP、gRPC）、消息队列生产者 / 消费者、文件 I/O、云服务 SDK

### 输出格式

```markdown
## Data Flow & State Management

### Data Models
| Model | File | Key Fields | Relationships |
|-------|------|------------|---------------|

### Key Data Flow
```mermaid
flowchart LR
  A[Entry] --> B[Validation] --> C[Logic] --> D[Persistence]
```

### State Management
[Pattern description with evidence]

### External Data Integrations
| Integration | Type | File | Description |
|-------------|------|------|-------------|
```

---

## 维度 4：领域模型与业务逻辑（Domain Model & Business Logic）

**负责**：codebase-analyzer

### 分析内容

**核心领域实体**
- 区分实体（含标识、可变）与值对象（无标识、不可变）
- 识别聚合根（若存在 DDD 模式）
- 为实体关系生成 Mermaid `classDiagram`

**业务规则与不变量**
- 强制业务约束的校验逻辑（非单纯类型校验）
- 与业务规则相关的鉴权 / 权限检查
- 计算逻辑（定价、评分、调度算法）
- 状态机迁移（订单状态、工作流步骤）

**业务逻辑热点**
- 业务逻辑最密集的文件 / 函数（条件语句占比最高）
- 启发式：domain / business / service 层中 `if/switch/case` 块较多的文件

**关键算法**
- 任何非平凡算法（排序、匹配、调度、优化）
- 每项：名称 / 用途、file:line、方法简述

### 输出格式

```markdown
## Domain Model & Business Logic

### Domain Entities
```mermaid
classDiagram
  class User {
    +id: string
    +email: string
  }
  User --> Order
```

### Business Rules
| Rule | Location | Description |
|------|----------|-------------|

### Key Algorithms
| Algorithm | File | Approach |
|-----------|------|----------|
```

---

## 维度 5：依赖与集成（Dependencies & Integrations）

**负责**：codebase-pattern-finder

### 分析内容

**直接依赖清单**
- 解析依赖清单（package.json、requirements.txt、pyproject.toml、pom.xml、go.mod、Cargo.toml）
- 每个依赖：名称、版本 / 约束、用途分类（HTTP、日志、测试、ORM、鉴权、校验、工具）
- 统计：总依赖数、dev 依赖数

**内部模块耦合**
- 对每个模块目录统计：
  - **Fan-in**：多少其他模块从它导入
  - **Fan-out**：它从多少其他模块导入
- 识别：耦合最高的模块（高 fan-in + fan-out）、最孤立的模块

**外部服务集成**
- HTTP 客户端：base URL、API 客户端、SDK 实例化
- 数据库连接：连接串、连接池配置
- 消息队列：生产者 / 消费者配置
- 云服务：AWS/GCP/Azure SDK 使用

**依赖注入模式**
- DI 容器（Spring、Inversify、dig、wire）
- 手动装配（构造器注入、factory 函数）
- 全局单例

### 输出格式

```markdown
## Dependencies & Integrations

### Dependency Summary
| Category | Count | Notable |
|----------|-------|---------|
| Runtime | N | [top 3 by importance] |
| Dev | N | [test framework, linter] |

### Internal Coupling
| Module | Fan-in | Fan-out | Coupling |
|--------|--------|---------|----------|

### External Services
| Service | Type | File | Connection |
|---------|------|------|------------|
```

---

## 维度 6：代码健康度与复杂度（Code Health & Complexity）

**负责**：codebase-pattern-finder

### 分析内容

**文件大小分布**
- 统计范围内所有源文件的每文件行数
- 报告：P50、P90、P99、max
- 列出最大的 5 个文件

**函数 / 方法长度**
- 启发式：统计函数 / 方法声明之间的行数
- 报告：P50、P90 估计
- 列出最长的 5 个函数

**复杂度热点**
- 启发式：每文件统计分支关键字（`if`、`else`、`elif`、`else if`、`for`、`while`、`switch`、`case`、`try`、`catch`、`except`、`&&`、`||`、`?:`、`match`）
- 按文件长度归一化：每 100 行的分支数
- 列出最复杂的 5 个文件

**测试覆盖情况**
- 每个源目录的测试文件数
- 测试 / 源文件比（按目录与全局）
- 识别零测试覆盖的目录
- 从 import 检测测试框架

**重复信号**
- 查找名字或结构非常相似的文件（例如形态一致的 `userController.ts` / `orderController.ts`）
- 查找重复代码块（相同函数签名或结构出现 3+ 次）
- 以观察形式报告，不作评论

**技术债标记**
- 搜索：`TODO`、`FIXME`、`HACK`、`XXX`、`WORKAROUND`、`TEMP`、`DEPRECATED`
- 每项：关键字、file:line、上下文（注释文本）
- 按关键字统计总数

### 输出格式

```markdown
## Code Health

### File Size Distribution
| Percentile | Lines |
|------------|-------|
| P50 | N |
| P90 | N |
| P99 | N |
| Max | N ([file]) |

### Complexity Hotspots
| File | Branches | Lines | Density |
|------|----------|-------|---------|

### Test Landscape
| Directory | Source Files | Test Files | Ratio |
|-----------|-------------|------------|-------|

### Technical Debt Markers
| Keyword | Count | Top Locations |
|---------|-------|---------------|
```
