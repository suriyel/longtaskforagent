#!/usr/bin/env bash
# Long-Task Agent installer for OpenCode (macOS / Linux)
# Usage:  curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main/install.sh | bash
set -euo pipefail

INSTALL_DIR="${HOME}/.config/opencode/long-task-agent"
# NOTE: opencode v1.14.19 auto-scans `plugin/` (singular); `plugins/` (plural)
# triggers a startup hang that surfaces as `errno:5 setRawMode failed`.
# Keep repo source path `.opencode/plugins/` (plural) unchanged.
PLUGIN_DIR="${HOME}/.config/opencode/plugin"
SKILLS_DIR="${HOME}/.config/opencode/skills"
REPO_URL="https://github.com/suriyel/longtaskforagent.git"

echo "Installing long-task-agent for OpenCode..."

# Clone or update
if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "  → Updating existing installation..."
  git -C "${INSTALL_DIR}" pull --ff-only
else
  echo "  → Cloning repository..."
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

# Create directories
mkdir -p "${PLUGIN_DIR}" "${SKILLS_DIR}"

# Remove stale symlinks / old copies (including legacy plural `plugins/` target)
rm -f  "${PLUGIN_DIR}/long-task.js"
rm -f  "${HOME}/.config/opencode/plugins/long-task.js"
rm -rf "${SKILLS_DIR}/long-task"

# Create symlinks
ln -s "${INSTALL_DIR}/.opencode/plugins/long-task.js" "${PLUGIN_DIR}/long-task.js"
ln -s "${INSTALL_DIR}/skills"                          "${SKILLS_DIR}/long-task"

echo ""
echo "Done! long-task-agent installed."
echo ""
echo "  Plugin : ${PLUGIN_DIR}/long-task.js"
echo "  Skills : ${SKILLS_DIR}/long-task"
echo ""
echo "Restart OpenCode to activate."
