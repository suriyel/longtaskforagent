#!/usr/bin/env bash
# Long-Task Agent installer for OpenCode (macOS / Linux)
# Usage:  curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main-improvement/install.sh | bash
set -euo pipefail

INSTALL_DIR="${HOME}/.config/opencode/long-task-agent"
PLUGINS_DIR="${HOME}/.config/opencode/plugins"
SKILLS_DIR="${HOME}/.config/opencode/skills"
REPO_URL="https://github.com/suriyel/longtaskforagent.git"
REPO_BRANCH="main-improvement"

echo "Installing long-task-agent for OpenCode..."

# Clone or update
if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "  → Updating existing installation..."
  git -C "${INSTALL_DIR}" fetch origin "${REPO_BRANCH}"
  git -C "${INSTALL_DIR}" checkout "${REPO_BRANCH}"
  git -C "${INSTALL_DIR}" pull --ff-only origin "${REPO_BRANCH}"
else
  echo "  → Cloning repository (branch: ${REPO_BRANCH})..."
  git clone --branch "${REPO_BRANCH}" "${REPO_URL}" "${INSTALL_DIR}"
fi

# Create directories
mkdir -p "${PLUGINS_DIR}" "${SKILLS_DIR}"

# Remove stale symlinks / old copies
rm -f  "${PLUGINS_DIR}/long-task.js"
rm -rf "${SKILLS_DIR}/long-task"

# Create symlinks
ln -s "${INSTALL_DIR}/.opencode/plugins/long-task.js" "${PLUGINS_DIR}/long-task.js"
ln -s "${INSTALL_DIR}/skills"                          "${SKILLS_DIR}/long-task"

echo ""
echo "Done! long-task-agent installed."
echo ""
echo "  Plugin : ${PLUGINS_DIR}/long-task.js"
echo "  Skills : ${SKILLS_DIR}/long-task"
echo ""
echo "Restart OpenCode to activate."
