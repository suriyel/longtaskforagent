#!/usr/bin/env bash
# =============================================================================
# Long-Task Agent Installer for OpenCode (macOS / Linux)
# =============================================================================
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | bash
#
# To install a specific branch:
#   curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | BRANCH=main bash
#
set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

REPO_URL="https://github.com/suriyel/longtaskforagent.git"
BRANCH="${BRANCH:-simple}"

# =============================================================================
# Paths
# =============================================================================

INSTALL_DIR="${HOME}/.config/opencode/long-task-agent"
PLUGIN_DIR="${HOME}/.config/opencode/plugin"
SKILLS_DIR="${HOME}/.config/opencode/skills"
PLUGIN_LINK="${PLUGIN_DIR}/long-task.js"
SKILL_LINK="${SKILLS_DIR}/long-task"
PLUGIN_SRC="${INSTALL_DIR}/.opencode/plugins/long-task.js"
SKILLS_SRC="${INSTALL_DIR}/skills"

# =============================================================================
# Color Output
# =============================================================================

if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN=''
  BLUE=''
  BOLD=''
  RESET=''
fi

info()    { echo -e "${BLUE}ℹ${RESET} $*"; }
success() { echo -e "${GREEN}✓${RESET} $*"; }

# =============================================================================
# Pre-flight Check
# =============================================================================

if ! command -v git &>/dev/null; then
  echo "Error: git is not installed" >&2
  exit 1
fi

# =============================================================================
# Install
# =============================================================================

info "Installing long-task-agent for OpenCode (branch: $BRANCH)"

# Remove existing if present
if [[ -d "$INSTALL_DIR" ]]; then
  info "Removing existing installation..."
  rm -rf "$INSTALL_DIR"
fi

# Clone repository (shallow, specific branch)
info "Cloning from: $REPO_URL"
mkdir -p "$(dirname "$INSTALL_DIR")"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"

# Verify plugin source exists on selected branch
if [[ ! -f "$PLUGIN_SRC" ]]; then
  echo "Error: Plugin source not found at $PLUGIN_SRC" >&2
  echo "       (branch '$BRANCH' may not contain .opencode/plugins/long-task.js)" >&2
  exit 1
fi

# Create link directories
mkdir -p "$PLUGIN_DIR" "$SKILLS_DIR"

# Remove stale symlinks / old copies
rm -f  "$PLUGIN_LINK"
rm -rf "$SKILL_LINK"

# Create symlinks
info "Linking plugin..."
ln -s "$PLUGIN_SRC" "$PLUGIN_LINK"
info "Linking skills..."
ln -s "$SKILLS_SRC" "$SKILL_LINK"

# =============================================================================
# Success
# =============================================================================

echo ""
echo -e "${BOLD}${GREEN}✓ long-task-agent installed successfully!${RESET}"
echo ""
echo "  Branch : $BRANCH"
echo "  Source : $INSTALL_DIR"
echo "  Plugin : $PLUGIN_LINK"
echo "  Skills : $SKILL_LINK"
echo ""
echo "Restart OpenCode to activate."
echo ""
