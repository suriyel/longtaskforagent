---
name: long-task-brownfield-scan
description: "Use when phase_route.py dispatches long-task-brownfield-scan — scan an existing codebase for conventions before requirements elicitation. Do not invoke manually; phase_route gates entry based on source file count + git history."
---

<EXTREMELY-IMPORTANT>
本 skill 由 `scripts/phase_route.py` 在检测到存量项目（源文件 > 3 且 git commits ≥ 5）且无 `docs/rules/` 时分派。

若当前会话**不是**由 phase_route 分派进入（例如用户手动触发），立即退出并返回调用 `using-long-task`。`docs/rules/` 一旦存在（哪怕是占位文件），phase_route 就会直接路由到 `long-task-requirements`，本 skill 不应再被触发。

职责仅限：扫描约定 → 审查 → 提交 → handoff 到 `long-task-requirements`。
</EXTREMELY-IMPORTANT>

## Step 1: 声明

打印："I'm using the long-task-brownfield-scan skill. Scanning codebase conventions before requirements elicitation."

## Step 2: 创建输出目录

```bash
mkdir -p docs/rules/
```

## Step 3: 检测语言与扫描深度

分析文件扩展名和依赖清单（`package.json`、`requirements.txt`、`pom.xml`、`Cargo.toml`、`go.mod`、`*.csproj`），决定扫描深度：

| LOC 范围 | 深度 |
|-----------|-------|
| < 1,000 | lightweight（前 20 个文件）|
| 1,000–10,000 | standard（前 50 个文件）|
| > 10,000 | deep（前 100 + 所有 config） |

## Step 4: 分发 `codebase-scanner` SubAgent

```
Agent(
  subagent_type="general-purpose",
  description="Scan codebase conventions for [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-scanner.md

  ## Scan Parameters
  - Working directory: {working_directory}
  - Primary language(s): {languages}
  - Primary framework(s): {frameworks}
  - Scan depth: {scan_depth}
  - Source file list: {file_list}

  Execute the full codebase scanner process per the agent definition.
  Return structured output per the Structured Return Contract.
  """
)
```

## Step 5: 校验结果

确认 `docs/rules/` 下至少存在 1 个输出文件。若 SubAgent 返回 `BLOCKED`，写入最小占位（非阻塞—扫描是尽力而为）：

```bash
cat > docs/rules/README.md <<'EOF'
# Codebase Convention Rules

> Scan returned BLOCKED. Minimal placeholder — downstream skills proceed without codebase-specific constraints.
EOF
```

## Step 6: 用户评审

通过 `AskUserQuestion`：
- 呈现关键发现摘要（尤其是 2/3方件 约束和禁用 API）
- 请用户在继续前确认或编辑 `docs/rules/` 文件

## Step 7: Git 提交

```bash
git add docs/rules/
git commit -m "docs: add codebase convention rules"
```

## Step 8: Handoff

调用 `long-task:long-task-requirements` skill（通过 Skill 工具）。需求阶段将读取 `docs/rules/*.md` 作为约束输入。

---

## 参考

- Scanner agent 定义：`agents/codebase-scanner.md`
- 路由入口：`scripts/phase_route.py`（brownfield 判定 + 分派）
