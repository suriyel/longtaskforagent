# 存量系统增量适配协议

本文件适用于 **long-task-increment** skill。它指导如何在存量项目的增量开发中：
- 复用已确立的横切关注点（鉴权、错误处理、日志等），避免为已有能力重复定义需求
- 正确分类本次增量的变更类型（NEW / MODIFY / EXTEND / REUSE）
- 强制输出"存量 API 影响 + 兼容性策略"表，防止集成期返工

> 增量开发天然是 brownfield 形态 — 本文件不做"是否适用"判定，所有 increment 都应参考本协议。

---

## §A. 存量系统清单（ESI）构建

在 Step 3（Impact Analysis）前构建 ESI，以便判断新需求与已有能力的关系。

**数据来源**（按优先级）：
1. `docs/explore/codebase-research.md`（如存在，来自之前的 explore 输出）
2. `docs/rules/*.md` / `env-guide.md` §4（存量代码库约束）
3. `docs/plans/*-design.md` §4（Key Feature Designs，存量已实现的特性）
4. `feature-list.json` 已 `passing` 的 features（已在线能力）

**ESI 表格式**：

| 维度 | 现有实现 | 证据来源 | 状态 |
|------|---------|---------|------|
| 鉴权 | JWT, `src/auth/` | explore:api | 已确立 |
| 权限 | RBAC 中间件 | design §4.3 | 已确立 |
| 错误处理 | 全局异常处理器 | rules/error-handling.md | 已确立 |
| 日志 | structured-logger | env-guide §4.2 | 已确立 |
| 数据验证 | Pydantic schemas | design §5 | 已确立 |
| ... | ... | ... | ... |

**状态值**：
- `已确立`：代码中确认存在
- `推断`：仅从文档/结构推断
- `未知`：无足够信息

**标准维度清单**（按需裁剪）：鉴权、权限/RBAC、错误处理、数据验证、并发控制、日志、API 模式、数据模型/ORM、缓存、消息队列、定时任务、文件存储、配置管理。

**降级**：ESI 为空时，后续各节退化为新建行为（按 Phase 0a greenfield 语义处理）。

---

## §B. 需求分类

对 `increment-request.json` 中每条变更，按下表分类：

| 类型 | 含义 | 处理 |
|------|------|------|
| **NEW** | 现有系统中不存在的全新能力 | 正常走 Step 2-6 |
| **MODIFY** | 变更现有 FR 行为（接口、语义、边界） | Step 3 必须列出受影响 API；Step 6 feature 重置 failing |
| **EXTEND** | 扩展现有能力但不改变当前行为（如新增字段、新 endpoint） | Step 3 列出扩展点；Step 6 feature 重置 failing |
| **REUSE** | 原样复用现有能力 | **红旗** — 不应为 FR；转为 SRS §1.4 假设 (ASM-xxx) |

REUSE 类型意味着采集过程将已有能力重复当成新需求。应从候选 FR 中移除或转为假设。

---

## §C. 需求过滤（Step 2 Elicitation 增强）

提问或接收用户输入时，将每项能力区域与 ESI 交叉对比：

- **ESI "已确立"横切关注点**（鉴权/权限/错误处理/日志/数据验证）：不单独立条 FR，除非用户明确要求改变；改为 ASM-xxx 记录假设。
- **已有数据模型**：问"需要新字段或新关系"，而非"数据模型是什么"。
- **已有模式**：问"沿用现有 [X] 模式还是需要不同行为？"

**核心原则**：只采集本次增量涉及的变化，不重新探索已有能力。

---

## §D. 存量 API 影响 + 兼容性策略（Step 3 Impact Analysis 增强）

在 Step 3 输出的 Impact Matrix 之外，**强制**追加"API 影响与兼容性"表：

| # | 修改项 | 位置（file:line 或签名） | 变更类型 | 兼容策略 | 影响的 feature_ids |
|---|--------|-------------------------|---------|---------|-------------------|
| 1 | `UserService.findById(id)` → `findById(id, tenantId)` | `src/services/UserService.java:L42` | Breaking | 旧签名保留 1 版本，加 @Deprecated | [1, 5, 12] |
| 2 | `POST /api/orders` response 增加 `trace_id` 字段 | `src/api/orders.ts:L88` | Additive | 向后兼容 — 消费方按需读取 | [7, 8] |
| 3 | `Order.status` 新增枚举值 `REFUNDING` | `src/model/Order.java` | Additive | 数据库迁移 + 旧消费方降级处理 | [5] |

**兼容策略取值**：
- `Additive`（向后兼容，新字段/新可选参数）
- `Deprecated`（保留旧 API 标记废弃，N 个版本后移除）
- `Breaking`（破坏性，需同步升级所有消费方）

**强制规则**：
- 表中每一行必须列出被修改代码的具体位置（file:line 或签名），不能只写模块名
- `impact_features` 必须是 `feature-list.json` 中真实的 feature id
- 有 `Breaking` 策略的行，其 `impact_features` 必须全部进入 Impact Matrix 的 Hard Impact 分类
- 若本次增量无 API 修改（纯新增无交叉点），显式写 "N/A — 纯新增，无存量 API 修改"

此表是 Step 3.5 Targeted Exploration 的主要输入之一（决定探索路径的 file:line 精度）。

---

## §E. 设计修订存量适配（Step 4 Design Revision 增强）

- **§13 / env-guide §4 约束继承**：如 `env-guide.md` §4 Codebase Constraints 存在，新 feature 的 Interface Contract、Algorithm、Dependencies 均必须遵守（不能引入 §4.2 禁用 API、必须使用 §4.1 强制内部库）。
- **§6.2 Internal API Contracts 更新**：若 §D 表中有 Breaking 策略的 API，必须同步更新 Design §6.2；否则消费方 feature 会在 TDD 阶段发现 contract 不一致。
- **§0 Project Structure 对齐**：若 Design 含 §0，新增模块必须放入现有目录结构；如必须新增顶层目录，需在 §0 更新并经用户审批。

---

## §F. SRS §1.4 回填

在 SRS §1.4 "存量系统上下文"（或 §1 末尾新增此段）填入：

1. **本波变更类型分布**（NEW/MODIFY/EXTEND/REUSE 各 N 条）
2. **ESI 已确立维度**：`[鉴权, 权限, 错误处理, 日志, 数据验证]`（本波遵循现有模式）
3. **变更摘要**：1-3 句话 — 什么变了、什么不变
4. **涉及模块**：本次变更触及的现有模块/目录列表
5. **不涉及模块**：明确列出不受影响的关键模块

此章节防止下游设计/实现将增量 SRS 误读为"从零构建"。
