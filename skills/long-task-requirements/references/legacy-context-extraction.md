# Legacy Context Decisions (LCD) — 抽取协议

requirements Step 2.5 / increment Step 2 按本协议从用户原始需求文档抽取 LCD 填充 SRS §1.4.2。

## 类别枚举（5 种，扫描按序匹配）

| 类别 | 触发信号 | 示例原文片段 |
|------|---------|--------------|
| `BEHAVIOR` | 描述原系统的业务行为、流程分支、默认值、隐式规则 | "分单器现按配送员最短路径合并"；"老接口默认返回 UTF-8 BOM" |
| `COMPAT` | 对外兼容性、接口契约、状态码、字段名、协议版本 | "状态码 200/4xx 保持不变"；"消息格式 v1 继续支持" |
| `DATA` | 字段语义、编码、取值空间、长度/精度、枚举值 | "用户 ID 为 8 位数字字符串"；"价格单位为分" |
| `PERF` | 响应时间、吞吐、并发、资源上限 | "p99 响应 < 200ms"；"单机支持 1k 并发" |
| `RATIONALE` | 仅解释"为什么原来这样"，无执行约束 | "当年选 MySQL 因为运维熟悉" |

**互斥原则**：一条原文片段只归一类。若跨类别，按 BEHAVIOR > COMPAT > DATA > PERF > RATIONALE 优先级取。

## 抽取步骤

1. **逐段扫描**用户原始文档。每段凡含上表触发信号 → 1 条候选 LCD。
2. **提取原文依据**：最小必要引用（≤ 2 句），用 `"<原文>" (§ N ¶ M)` 格式标注出处。
3. **识别澄清决议来源**：
   - 若在 Step 2 gap fill 或 Step 3 AskUserQuestion 中有用户回答覆盖原文 → 决议 = 用户回答；权威 = `RESOLVED`
   - 若用户未澄清 → 决议 = 原文照搬；权威 = `QUOTED`
   - 若用户回答与原文存在二义或冲突且未定 → 权威 = `CONFLICTED`（阻塞 Step 7 审查门）
4. **反向映射 FR / CON**：
   - `BEHAVIOR` / `COMPAT` / `DATA` / `PERF` 通常对应一个或多个 FR-xxx 或 CON-xxx
   - `RATIONALE` 可不映射（仅解释性）
   - 若扫出 LCD 找不到对应 FR，反向触发 gap：检查是否漏提 FR
5. **分配 LCD ID**：`LCD-001` 起递增，三位零填充。DEPRECATED 不复用 ID；increment 追加时 ID 从现有最大值 + 1 起。
6. **填入 §1.4.2 表**。

## 权威分层（必须理解，不重复）

- **§1.4.2 "澄清决议" 列 = 执行权威**。下游 feature-design / TDD 硬读此列。
- **§1.4.3 归档原文 = 证据**。默认不读；仅在 `[LEGACY-DRIFT]` blocker 溯源时回查。
- 若下游发现原文与决议矛盾 → `[LEGACY-CONFLICT]` blocker 回 requirements / increment 补澄清，决议未改动前不得自行解释原文。

## 反模式

| 反模式 | 正确做法 |
|--------|---------|
| LCD 覆盖 FR 内容（"登录流程按三步走"写进 LCD） | FR 写新行为；LCD 只写 legacy 约束 / 原系统既定事实 |
| 整段原文当 LCD 原文依据 | 最小片段 ≤ 2 句；长原文归 `docs/references/` 归档 |
| 把编码约定 / 二方件选择写成 LCD | 归 Design §11；LCD 只管业务语义与兼容性 |
| RATIONALE 类 LCD 给 `lcd_trace` | RATIONALE 不进 `lcd_trace`；不产生执行约束 |
| CONFLICTED 直接上表不阻塞 | CONFLICTED > 0 必须阻塞 Step 7 L3 门禁；未决清零方可继续 |
| 用 "建议"、"推荐" 类措辞写决议 | 决议必须是可执行约束：动词 + 具体对象 + 约束范围；模糊词回退到 CONFLICTED |
| 同一原文被拆成多条 LCD | 归并为一条；若原文跨类别，按类别互斥优先级单选 |

## 与下游的接口契约

- `feature-list.json.features[].lcd_trace: ["LCD-001", ...]` 由 long-task-init Step 6 / long-task-increment Step 5b 基于 Design §4.N.5 与 §1.4.2 反推填充
- `RATIONALE` 类 LCD 不得出现在 `lcd_trace`（校验由 `scripts/check_lcd_wiring.py` 强制）
- DEPRECATED LCD 不得被任何 active feature 引用（同上）
- 下游 SubAgent 硬消费点（execution.md 规定）：
  - feature-design：追踪每条 `lcd_trace[]` 到接口契约 / 边界决策 / 错误表
  - tdd-red：每条 BEHAVIOR/COMPAT/DATA LCD ≥ 1 条断言测试
  - tdd-green：§11 + §1.4.2 lcd_trace 作为实现硬约束
  - tdd-refactor：grep / 测试验证每条 LCD 语义仍保持

## 失败模式

| 扫描结果 | 处置 |
|---------|------|
| 0 条候选 LCD（greenfield 或输入无存量信息） | §1.4.2 保留空表，§1.4.3 省略；放行 Step 7 |
| 有 CONFLICTED 条目 | Step 7 L3 阻塞；回 Step 3 用 AskUserQuestion 定向澄清，改为 RESOLVED 后继续 |
| LCD 找不到对应 FR/CON 且类别非 RATIONALE | Step 2 gap 回查：要么补 FR，要么把该 LCD 降级为 RATIONALE |
