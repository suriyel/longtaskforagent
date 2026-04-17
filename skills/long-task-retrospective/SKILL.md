---
name: long-task-retrospective
description: "Use after ST Go verdict when retrospective records exist and user authorized feedback — consolidate records and POST to REST API"
---

# Retrospective Report —— 汇总并上传 skill 改进记录

由 `long-task-st` Step 12.5 在 Go 判定之后条件性调用：当存在 retrospective 记录且反馈已授权时触发。本 skill 汇总已收集的记录并上传到配置的 REST API endpoint。

**开始时声明：** "I'm using the long-task-retrospective skill. Preparing to report skill improvement records."

**核心原则：** 本 skill 只上报 —— **不会**修改 skill 文件。改进记录被上传以供分析，并可能整合进未来的 skill 发布。

## 清单

### 1. 关卡检查

校验两项条件：

**a) 授权**：
- 阅读 `feature-list.json` —— 检查 `retro_authorized` 字段
- 若缺失或为 `false` → 打印 "Retrospective: not authorized — skipping" → 停止

**b) 服务可达性**：
```bash
python scripts/check_retro_auth.py feature-list.json
```
- exit 0（就绪）→ 继续
- exit 1（不可用）→ 打印 "Retrospective: endpoint unavailable — skipping" → 停止
- exit 2（已禁用）→ 打印 "Retrospective: no endpoint configured — skipping" → 停止

### 2. 读取记录

读取所有 `docs/retrospectives/*.md` 文件（排除 `reported/` 子目录）：

```bash
python scripts/check_retrospective_readiness.py
```

对每条记录校验：
```bash
python scripts/validate_retrospective_record.py docs/retrospectives/<file>.md
```

- 有效记录 → 纳入报告
- 无效记录 → 打 warning 日志，排除出上传

### 3. 汇总

从记录 frontmatter 汇总统计：
- 总条数（仅有效）
- 按严重级别：critical / important / minor
- 按分类：skill-gap / missing-rule / false-assumption / template-defect / process-gap
- 按归类：systemic / one-off

向用户呈现汇总。

### 4. 用户确认

使用 `AskUserQuestion`：
```
"本项目共搜集 {N} 条 Skill 改进记录（critical: {X}, important: {Y}, minor: {Z}）。
 其中系统性问题 {S} 条，一次性问题 {O} 条。是否上报到 {endpoint}？"

Options: "确认上报 (Recommended)" / "跳过本次上报"
```

- 用户选择"跳过" → 打印 "Retrospective: user skipped upload" → 停止
- 用户选择"确认上报" → 继续

### 5. 上传

```bash
python scripts/post_retrospective_report.py --feature-list feature-list.json
```

脚本会：
1. 将 `docs/retrospectives/*.md` 压缩为 `retrospectives.tar.gz`
2. 以 multipart/form-data POST 到配置的 endpoint
3. 附带元数据：项目名、日期、分支、记录数

- exit 0 → 打印 "Retrospective: {N} records uploaded successfully"
- exit 1 → 打印错误，**不要**重试 —— 向用户报告失败

### 6. 清理

- 将已上传记录移动到 `docs/retrospectives/reported/`（审计轨迹）
- Git 提交：`retro: upload {N} skill improvement records`
- 在 `task-progress.md` 追加 retrospective 条目

## 关键规则

- **绝不修改 skill 文件** —— 本 skill 只收集与上报
- **关卡检查不可妥协** —— 授权与可达性都必须通过
- **用户确认必需** —— 没有用户明确同意绝不上传
- **隐私优先** —— 记录中不得含项目源码、业务数据或凭据
- **每个 ST 循环仅上传一次** —— 不在 Worker 会话中上传部分批次
- **失败非阻塞** —— 上传失败不影响 ST 判定
