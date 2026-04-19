---
name: long-task-init-features
description: "Use when dispatched by long-task-init Step 5 — generate long-task-guide.md + populate feature-list.json (constraints/assumptions/features/required_configs) + .env.example + scripts/check_configs.py + validate"
---

# 生成 Worker 指南与特性清单

一次性产出 Worker 会话所需的全部协调性工件：workflow 导航指南 + 完整的 feature-list.json 骨架 + 配置检查器 + 校验。主 agent 持有 sizing 关卡。

## 步骤

### A. 生成 `long-task-guide.md`

1. 读 `skills/long-task-work-design/SKILL.md`、`skills/long-task-work-tdd/SKILL.md`、`skills/long-task-work-st/SKILL.md`、`skills/long-task-quality/SKILL.md`、`skills/using-long-task/references/architecture.md`（参考）
2. 读 `feature-list.json.tech_stack` 确认语言与测试框架
3. 读 `env-guide.md`（已存在）确认 §1/§3 指引路径
4. 写项目根 `long-task-guide.md`：**仅工作流导航**，不嵌具体命令
   - 必需节：Orient、Bootstrap、Config Gate、TDD Red、TDD Green、Coverage Gate、TDD Refactor、Verification Enforcement、Inline Compliance Check、Persist、Critical Rules
   - 命令引用一律写 "See `env-guide.md` §3 Build & Execution Commands" / "See `env-guide.md` §1 Service Lifecycle"
   - `Config Management` 节：描述本项目 config 格式（dotenv / Spring properties / 系统 env）下如何新增/更新值
   - `Real Test Convention` 节：识别方法（marker / folder / naming，适配语言）、指引到 env-guide.md §3 对应仅运行真实测试的命令、本技术栈下真实测试示例
   - 仅当项目有 UI 特性时包含 UI 测试节（Chrome DevTools MCP 工具名）
5. 运行 `python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json`

### B. 填充 `feature-list.json` 的 SRS 字段

1. 读 `docs/plans/*-srs.md`
2. `constraints[]` ← SRS "Constraints" 节 CON-xxx 条目（每条一字符串）
3. `assumptions[]` ← SRS "Assumptions & Dependencies" 节 ASM-xxx 条目
4. NFR-xxx 行 → 追加到 `features[]`，`category: "non-functional"`，`srs_trace: ["NFR-xxx"]`，可选可度量 `verification_steps`；覆盖率关卡不适用于 NFR 特性
5. SRS frontmatter 含 `Single-Round: Yes` → `feature-list.json` 根置 `"single_round": true`

### C. 从 Design §6.1 填充核心特性

1. 读 `docs/plans/*-design.md` §6.1 任务分解表 + §6.2 依赖链
2. 读 `docs/plans/*-ats.md`（若存在）用于 srs_trace → 类别映射查询
3. 每 §6.1 行 → 一特性：
   - `srs_trace` ← "Mapped FRs" 列
   - `title` + `description` ← 特性名 + 被分组 FR 描述
   - `priority` ← P0/P1 → `high`，P2 → `medium`，P3 → `low`
   - `dependencies` ← §6.2 依赖链图
   - `status` 始终 `"failing"`（推进到 passing 由 `long-task-work-st` Persist 负责）
   - **不写 `sub_status`**（已废弃）；调度由根 `current` 锁 + router 挑选驱动
   - UI 特性（srs_trace 任一 FR 的 ATS 类别含 UI）→ `ui: true` + `ui_entry: "/path"`；至少 1 条带 `[devtools]` 前缀的 verification_step 断言**正面视觉存在**
   - 前端特性 `dependencies[]` 必须列出后端 API 依赖特性
   - 排序遵循 §6.1 行顺序（Design 已按优先级 + backend/frontend 配对）
4. **根字段 `current`**：始终初始化为 `null`（首次 Worker 会话时 router 会挑第一个依赖就绪的 feature，由 `long-task-work-design` Step 1 原子写入）
5. **校验关卡**（内部）：
   - 每 FR-xxx 必须至少出现在一个特性的 srs_trace（无孤立需求）→ 否则 `blocked`，blockers `["ats-srs-trace-orphan: FR-xxx"]`
   - 每特性 srs_trace 非空 → 否则 `blocked`

### D. LOC 估算与 sizing 带分类

公式（透明可复核）：
```
est_loc = (sum of AC counts × 80) + (interface-contract method count × 100) + (test-inventory estimated rows × 30)
```
- AC 数来自 SRS srs_trace 需求
- method / test 数在本阶段为估值（Design §4 作参考）

分类：
- `< 500` → small
- `500-1500` → ok
- `> 1500` → large
- `single_round: true` 模式下上限放宽到约 2000

**不在 sub-skill 内做合并/拆分决策**：仅计算并落盘本次草稿，将分布 + 每特性估值通过 `next_step_input.loc_distribution` + `feature_summary` 返回，由主 agent 持 sizing 关卡。

### E. `required_configs` + `.env.example` + `scripts/check_configs.py`

1. 读 SRS IFR-xxx 接口需求 + Design：
   - API key / 服务 URL → type `env`
   - 配置文件 / 证书 → type `file`
   - 每条 `required_by` 关联到相应特性 ID 数组
   - `check_hint` 给出设置说明
2. 写 `.env.example`：每 env 类型 config 一块注释模板
   ```
   # <name> — <description>
   # Hint: <check_hint>
   # Required by features: <required_by ids>
   <KEY>=
   ```
3. 把 `.env` 加入 `.gitignore`；`.env.example` 本身可安全提交
4. 生成 `scripts/check_configs.py`——项目专属 config 检查器：
   - 基于 `tech_stack.language` 与设计文档选加载方式（dotenv / Spring properties / YAML / 系统 env）
   - 标准接口：`python scripts/check_configs.py feature-list.json [--feature <id>]`
   - 读 `required_configs[]`，`env` 类型查 `os.environ`，`file` 类型查 `os.path.exists`
   - 打印缺失的 `name` + `check_hint`
   - Exit 0 所有必需存在；Exit 1 缺失任一
   - **不要** `--dotenv` / format 标志；加载逻辑硬编码

### F. 校验

```bash
python scripts/validate_features.py feature-list.json
python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
```
两者均 exit 0 → `status: pass`；任一失败 → `status: fail`，evidence 附 stderr，artifacts_written 仍列出已写文件。

## 返回

```markdown
## SubAgent Result: long-task-init-features

**status**: pass | fail | blocked
**artifacts_written**: [
  "long-task-guide.md",
  "feature-list.json",
  ".env.example",
  ".gitignore",
  "scripts/check_configs.py"
]
**next_step_input**: {
  "feature_count": 15,
  "loc_distribution": {"small": 2, "ok": 11, "large": 2},
  "feature_summary": [
    {"id": 1, "title": "Login API", "est_loc": 1100, "band": "ok", "ui": false, "srs_trace": ["FR-001", "FR-002"]}
  ],
  "ui_feature_count": 3,
  "config_count": 5,
  "nfr_feature_count": 2,
  "single_round": false,
  "validate_guide_ok": true,
  "validate_features_ok": true
}
**blockers**: []
**evidence**: [
  "long-task-guide.md: all required sections present",
  "feature-list.json: 15 features; all FR-xxx mapped; no srs_trace orphans",
  "validate_features.py: OK",
  "validate_guide.py: OK",
  "scripts/check_configs.py generated for python/dotenv loader"
]
```

## 阻塞 / 失败

- `env-guide.md` 不存在（features 依赖其 §3 引用）→ `blocked`，blockers `["env-guide-not-found"]`
- Design §6.1 缺失或为空 → `blocked`，blockers `["design-§6.1-missing"]`
- 任一 SRS FR-xxx 未被任何特性 srs_trace 覆盖 → `blocked`，blockers `["ats-srs-trace-orphan: FR-XXX"]`（逐条列出）
- `validate_features.py` / `validate_guide.py` 失败 → `status: fail`，evidence 附 stderr

## 反模式

| Anti-Pattern | Correct |
|---|---|
| 在 sub-skill 内做合并/拆分决策 | 只计算分布返回；主 agent 持 sizing 关卡 |
| 在 long-task-guide.md 嵌具体 build/test 命令 | 一律引用 `env-guide.md` §3；防双源漂移 |
| 跳过 srs_trace 孤立检查 | 孤立 FR 必须阻塞，不能静默通过 |
| 忘记把 `.env` 加入 `.gitignore` | 密钥泄露风险；`.env.example` 可提交，`.env` 必须忽略 |
| 把插件的 `scripts/check_configs.py` 原样复制 | 必须按项目技术栈**重新生成**，加载逻辑硬编码 |
| 前端特性不列后端 API 依赖 | 前端 `ui: true` 特性的 `dependencies[]` 必须包含其 API 后端特性 |
| 用旧硬编码 10-200 数量区间判定 sizing | 按 `context_budget_tokens` 动态算 upper_bound；小项目允许 < 10 特性 |
