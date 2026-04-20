# Git Worktree 隔离

## 目的

在专用的 git worktree 中隔离功能实现。这可以保持主分支的清洁，支持安全的实验，并提供清晰的合并/丢弃工作流。

## 适用场景

- **推荐** 在 Worker 会话中用于所有功能实现
- **必须** 当可能并行开发多个功能时
- **可选** 对于单功能顺序开发，如果用户偏好直接在分支上工作

## 设置流程

### 步骤 1：检查现有配置

1. 查找已有的 worktree 目录：
   ```bash
   ls -d .worktrees worktrees 2>/dev/null
   ```
2. 检查 CLAUDE.md 或项目文档中的 worktree 偏好设置
3. 如有歧义，询问用户使用哪个目录

### 步骤 2：创建 Worktree

```bash
# Determine base branch
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

# Create worktree for the feature
FEATURE_BRANCH="feature/feature-${FEATURE_ID}-${SHORT_NAME}"
WORKTREE_DIR=".worktrees/${FEATURE_BRANCH}"

git worktree add "${WORKTREE_DIR}" -b "${FEATURE_BRANCH}" "${BASE_BRANCH}"
```

### 步骤 3：安全验证

1. 确保 worktree 目录已加入 `.gitignore`：
   ```bash
   grep -q '.worktrees' .gitignore || echo '.worktrees/' >> .gitignore
   ```

2. 在 worktree 中运行项目设置：
   ```bash
   cd "${WORKTREE_DIR}"
   # Auto-detect and run setup
   [ -f package.json ] && npm install
   [ -f requirements.txt ] && pip install -r requirements.txt
   [ -f Cargo.toml ] && cargo build
   [ -f go.mod ] && go mod download
   ```

3. 运行基线测试以验证初始状态正常：
   ```bash
   # Run full test suite — all must pass before starting work
   ```

### 步骤 4：在 Worktree 中工作

所有 TDD Red -> Green -> Refactor 工作在 worktree 目录内进行。

## 分支命名规范

```
feature/feature-{ID}-{short-name}
```

示例：
- `feature/feature-01-user-login`
- `feature/feature-15-dashboard-charts`

## 完成功能分支

功能标记为"passing"且代码审查完成后，向用户提供四个选项：

### 选项 1：本地合并
```bash
# Switch to base branch
git checkout "${BASE_BRANCH}"

# Merge the feature branch
git merge "${FEATURE_BRANCH}"

# Verify all tests still pass
# [run full test suite]

# Clean up worktree
git worktree remove "${WORKTREE_DIR}"
git branch -d "${FEATURE_BRANCH}"
```

### 选项 2：推送并创建 PR
```bash
# Push the feature branch
git push -u origin "${FEATURE_BRANCH}"

# Create PR
gh pr create --title "Feature #${FEATURE_ID}: ${TITLE}" --body "..."

# Keep worktree alive until PR is merged
echo "Worktree kept at ${WORKTREE_DIR} — remove after PR merge"
```

### 选项 3：保持现状
```bash
# Leave worktree and branch intact
echo "Worktree preserved at ${WORKTREE_DIR}"
echo "Branch: ${FEATURE_BRANCH}"
```

### 选项 4：丢弃
```bash
# SAFETY: Require explicit confirmation
echo "Type 'discard' to confirm deletion of all changes on ${FEATURE_BRANCH}"
# [wait for user input]

# Remove worktree and branch
git worktree remove --force "${WORKTREE_DIR}"
git branch -D "${FEATURE_BRANCH}"
```

## Worktree 生命周期

```
Orient → Select Feature
  │
  ├─ Create worktree + branch
  │
  ├─ Setup environment in worktree
  │
  ├─ Run baseline tests (must pass)
  │
  ├─ TDD Red → Green → Refactor
  │
  ├─ Feature marked "passing"
  │
  └─ Finish: Merge / PR / Keep / Discard
```

## 规则

- 始终验证 `.gitignore` 包含 worktree 目录
- 在新 worktree 中开始工作前始终运行基线测试
- 未经用户确认，禁止强制删除 worktree
- 如果用户拒绝 worktree 隔离，直接在功能分支上工作（仍与 main 隔离）
