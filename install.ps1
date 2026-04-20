# Long-Task Agent installer for OpenCode (Windows PowerShell)
# Usage:  irm https://raw.githubusercontent.com/suriyel/longtaskforagent/main/install.ps1 | iex
#
# Requirements: Developer Mode enabled -OR- run as Administrator (for symlinks)
#   Windows 10: Settings → Update & Security → For developers
#   Windows 11: Settings → System → For developers

$ErrorActionPreference = "Stop"

$installDir = "$env:USERPROFILE\.config\opencode\long-task-agent"
# NOTE: opencode v1.14.19 auto-scans `plugin\` (singular); `plugins\` (plural)
# triggers a startup hang that surfaces as `errno:5 setRawMode failed`.
# Keep repo source path `.opencode\plugins\` (plural) unchanged.
$pluginDir  = "$env:USERPROFILE\.config\opencode\plugin"
$skillsDir  = "$env:USERPROFILE\.config\opencode\skills"
$repoUrl    = "https://github.com/suriyel/longtaskforagent.git"

Write-Host "Installing long-task-agent for OpenCode..."

# Clone or update
if (Test-Path (Join-Path $installDir ".git")) {
    Write-Host "  -> Updating existing installation..."
    git -C $installDir pull --ff-only
} else {
    Write-Host "  -> Cloning repository..."
    git clone $repoUrl $installDir
}

# Create directories
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null

# Remove stale links / old copies (including legacy plural `plugins\` target)
$pluginLink       = Join-Path $pluginDir "long-task.js"
$legacyPluginLink = Join-Path "$env:USERPROFILE\.config\opencode\plugins" "long-task.js"
$skillLink        = Join-Path $skillsDir  "long-task"
if (Test-Path $pluginLink)       { Remove-Item $pluginLink       -Force }
if (Test-Path $legacyPluginLink) { Remove-Item $legacyPluginLink -Force }
if (Test-Path $skillLink)        { Remove-Item $skillLink        -Force -Recurse }

# Plugin: SymbolicLink (requires Developer Mode or Admin)
New-Item -ItemType SymbolicLink `
    -Path   $pluginLink `
    -Target (Join-Path $installDir ".opencode\plugins\long-task.js") | Out-Null

# Skills: Junction (works without special privileges)
New-Item -ItemType Junction `
    -Path   $skillLink `
    -Target (Join-Path $installDir "skills") | Out-Null

Write-Host ""
Write-Host "Done! long-task-agent installed."
Write-Host ""
Write-Host "  Plugin : $pluginLink"
Write-Host "  Skills : $skillLink"
Write-Host ""
Write-Host "Restart OpenCode to activate."
