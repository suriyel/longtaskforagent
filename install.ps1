# =============================================================================
# Long-Task Agent Installer for OpenCode (Windows PowerShell)
# =============================================================================
#
# Usage:
#   irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
#
# To install a specific branch:
#   $env:BRANCH="main"; irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
#
# Requirements: Developer Mode enabled -OR- run as Administrator (for symlinks)
#   Windows 10: Settings -> Update & Security -> For developers
#   Windows 11: Settings -> System -> For developers
#

$ErrorActionPreference = "Stop"

# =============================================================================
# Configuration
# =============================================================================

$RepoUrl = "https://github.com/suriyel/longtaskforagent.git"
$Branch  = if ($env:BRANCH) { $env:BRANCH } else { "simple" }

# =============================================================================
# Paths
# =============================================================================

$InstallDir = Join-Path $env:USERPROFILE ".config\opencode\long-task-agent"
$PluginDir  = Join-Path $env:USERPROFILE ".config\opencode\plugin"
$SkillsDir  = Join-Path $env:USERPROFILE ".config\opencode\skills"
$PluginLink = Join-Path $PluginDir "long-task.js"
$SkillLink  = Join-Path $SkillsDir  "long-task"
$PluginSrc  = Join-Path $InstallDir ".opencode\plugins\long-task.js"
$SkillsSrc  = Join-Path $InstallDir "skills"

# =============================================================================
# Helper Functions
# =============================================================================

function Write-Info    { param($Message) Write-Host "ℹ " -ForegroundColor Blue  -NoNewline; Write-Host $Message }
function Write-Success { param($Message) Write-Host "✓ " -ForegroundColor Green -NoNewline; Write-Host $Message }

# =============================================================================
# Pre-flight Check
# =============================================================================

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Error: git is not installed" -ForegroundColor Red
    exit 1
}

# =============================================================================
# Install
# =============================================================================

Write-Info "Installing long-task-agent for OpenCode (branch: $Branch)"

# Remove existing if present
if (Test-Path $InstallDir) {
    Write-Info "Removing existing installation..."
    Remove-Item $InstallDir -Recurse -Force
}

# Clone repository (shallow, specific branch)
Write-Info "Cloning from: $RepoUrl"
$InstallParent = Split-Path -Parent $InstallDir
if (-not (Test-Path $InstallParent)) {
    New-Item -ItemType Directory -Force -Path $InstallParent | Out-Null
}

git clone --depth 1 --branch $Branch $RepoUrl $InstallDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to clone repository" -ForegroundColor Red
    exit 1
}

# Verify plugin source exists on selected branch
if (-not (Test-Path $PluginSrc)) {
    Write-Host "Error: Plugin source not found at $PluginSrc" -ForegroundColor Red
    Write-Host "       (branch '$Branch' may not contain .opencode/plugins/long-task.js)" -ForegroundColor Red
    exit 1
}

# Create link directories
New-Item -ItemType Directory -Force -Path $PluginDir | Out-Null
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

# Remove stale links / old copies
if (Test-Path $PluginLink) { Remove-Item $PluginLink -Force }
if (Test-Path $SkillLink)  { Remove-Item $SkillLink  -Force -Recurse }

# Plugin: SymbolicLink (requires Developer Mode or Admin)
Write-Info "Linking plugin..."
New-Item -ItemType SymbolicLink -Path $PluginLink -Target $PluginSrc | Out-Null

# Skills: Junction (works without special privileges)
Write-Info "Linking skills..."
New-Item -ItemType Junction    -Path $SkillLink  -Target $SkillsSrc | Out-Null

# =============================================================================
# Success
# =============================================================================

Write-Host ""
Write-Success "long-task-agent installed successfully!"
Write-Host ""
Write-Host "  Branch : $Branch"
Write-Host "  Source : $InstallDir"
Write-Host "  Plugin : $PluginLink"
Write-Host "  Skills : $SkillLink"
Write-Host ""
Write-Host "Restart OpenCode to activate."
Write-Host ""
Write-Host "First-start note:" -ForegroundColor Yellow
Write-Host "  OpenCode's first launch fetches the models.dev catalog and runs"
Write-Host "  npm reify into $env:USERPROFILE\.config\opencode\node_modules\."
Write-Host "  On slow or proxied networks this may take several minutes. If it"
Write-Host "  appears stuck for >5 min:"
Write-Host "    1. Verify https://models.dev is reachable."
Write-Host "    2. Check OpenCode's log (TUI's /log command or ~/.local/share/opencode/log/)."
Write-Host "    3. Seeing '[long-task-plugin] init start' means the host finished"
Write-Host "       its own init — any further hang is inside this plugin."
Write-Host "    4. Set `$env:LONG_TASK_DEBUG='1'` before launch for per-step timings."
Write-Host ""
