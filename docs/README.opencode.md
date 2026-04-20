# Long-Task Agent for OpenCode

Complete guide for using Long-Task Agent with [OpenCode.ai](https://opencode.ai).

## Quick Install

Both installers default to the `simple` branch (current primary development branch). To install a different branch, set the `BRANCH` environment variable — see [Install from a Specific Branch](#install-from-a-specific-branch).

### macOS / Linux — one command

```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | bash
```

### Windows (PowerShell) — one command

> Requires **Developer Mode** enabled *or* running as Administrator.
> Windows 10: Settings → Update & Security → For developers
> Windows 11: Settings → System → For developers

```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
```

Restart OpenCode after installation.

### Install from a Specific Branch

Override the default (`simple`) with the `BRANCH` env var:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | BRANCH=main bash
```

```powershell
# Windows (PowerShell)
$env:BRANCH="main"; irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
```

The installer performs a shallow clone of the selected branch into `~/.config/opencode/long-task-agent`, replacing any previous installation.

---

## Manual Installation

### Prerequisites

- [OpenCode.ai](https://opencode.ai) installed
- Git installed

### macOS / Linux

```bash
# 1. Clone long-task-agent (or update existing)
if [ -d ~/.config/opencode/long-task-agent ]; then
  cd ~/.config/opencode/long-task-agent && git pull
else
  git clone https://github.com/suriyel/longtaskforagent.git ~/.config/opencode/long-task-agent
fi

# 2. Create directories
mkdir -p ~/.config/opencode/plugins ~/.config/opencode/skills

# 3. Remove old symlinks if they exist
rm -f ~/.config/opencode/plugins/long-task.js
rm -rf ~/.config/opencode/skills/long-task

# 4. Create plugin symlink
ln -s ~/.config/opencode/long-task-agent/.opencode/plugins/long-task.js ~/.config/opencode/plugins/long-task.js

# 5. Create skills symlink
ln -s ~/.config/opencode/long-task-agent/skills ~/.config/opencode/skills/long-task

# 6. Restart OpenCode
```

#### Verify Installation

```bash
ls -l ~/.config/opencode/plugins/long-task.js
ls -l ~/.config/opencode/skills/long-task
```

Both should show symlinks pointing to the long-task-agent directory.

### Windows

**Prerequisites:**
- Git installed
- Either **Developer Mode** enabled OR **Administrator privileges**
  - Windows 10: Settings → Update & Security → For developers
  - Windows 11: Settings → System → For developers

Pick your shell below: [Command Prompt](#command-prompt) | [PowerShell](#powershell) | [Git Bash](#git-bash)

#### Command Prompt

Run as Administrator, or with Developer Mode enabled:

```cmd
:: 1. Clone long-task-agent
git clone https://github.com/suriyel/longtaskforagent.git "%USERPROFILE%\.config\opencode\long-task-agent"

:: 2. Create directories
mkdir "%USERPROFILE%\.config\opencode\plugins" 2>nul
mkdir "%USERPROFILE%\.config\opencode\skills" 2>nul

:: 3. Remove existing links (safe for reinstalls)
del "%USERPROFILE%\.config\opencode\plugins\long-task.js" 2>nul
rmdir "%USERPROFILE%\.config\opencode\skills\long-task" 2>nul

:: 4. Create plugin symlink (requires Developer Mode or Admin)
mklink "%USERPROFILE%\.config\opencode\plugins\long-task.js" "%USERPROFILE%\.config\opencode\long-task-agent\.opencode\plugins\long-task.js"

:: 5. Create skills junction (works without special privileges)
mklink /J "%USERPROFILE%\.config\opencode\skills\long-task" "%USERPROFILE%\.config\opencode\long-task-agent\skills"

:: 6. Restart OpenCode
```

#### PowerShell

Run as Administrator, or with Developer Mode enabled:

```powershell
# 1. Clone long-task-agent
git clone https://github.com/suriyel/longtaskforagent.git "$env:USERPROFILE\.config\opencode\long-task-agent"

# 2. Create directories
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\plugins"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills"

# 3. Remove existing links (safe for reinstalls)
Remove-Item "$env:USERPROFILE\.config\opencode\plugins\long-task.js" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:USERPROFILE\.config\opencode\skills\long-task" -Force -ErrorAction SilentlyContinue

# 4. Create plugin symlink (requires Developer Mode or Admin)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.config\opencode\plugins\long-task.js" -Target "$env:USERPROFILE\.config\opencode\long-task-agent\.opencode\plugins\long-task.js"

# 5. Create skills junction (works without special privileges)
New-Item -ItemType Junction -Path "$env:USERPROFILE\.config\opencode\skills\long-task" -Target "$env:USERPROFILE\.config\opencode\long-task-agent\skills"

# 6. Restart OpenCode
```

#### Git Bash

Note: Git Bash's native `ln` command copies files instead of creating symlinks. Use `cmd //c mklink` instead (the `//c` is Git Bash syntax for `/c`).

```bash
# 1. Clone long-task-agent
git clone https://github.com/suriyel/longtaskforagent.git ~/.config/opencode/long-task-agent

# 2. Create directories
mkdir -p ~/.config/opencode/plugins ~/.config/opencode/skills

# 3. Remove existing links (safe for reinstalls)
rm -f ~/.config/opencode/plugins/long-task.js 2>/dev/null
rm -rf ~/.config/opencode/skills/long-task 2>/dev/null

# 4. Create plugin symlink (requires Developer Mode or Admin)
cmd //c "mklink \"$(cygpath -w ~/.config/opencode/plugins/long-task.js)\" \"$(cygpath -w ~/.config/opencode/long-task-agent/.opencode/plugins/long-task.js)\""

# 5. Create skills junction (works without special privileges)
cmd //c "mklink /J \"$(cygpath -w ~/.config/opencode/skills/long-task)\" \"$(cygpath -w ~/.config/opencode/long-task-agent/skills)\""

# 6. Restart OpenCode
```

#### WSL Users

If running OpenCode inside WSL, use the [macOS / Linux](#macos--linux) instructions instead.

#### Verify Installation (Windows)

**Command Prompt:**
```cmd
dir /AL "%USERPROFILE%\.config\opencode\plugins"
dir /AL "%USERPROFILE%\.config\opencode\skills"
```

**PowerShell:**
```powershell
Get-ChildItem "$env:USERPROFILE\.config\opencode\plugins" | Where-Object { $_.LinkType }
Get-ChildItem "$env:USERPROFILE\.config\opencode\skills" | Where-Object { $_.LinkType }
```

Look for `<SYMLINK>` or `<JUNCTION>` in the output.

#### Troubleshooting Windows

**"You do not have sufficient privilege" error:**
- Enable Developer Mode in Windows Settings, OR
- Right-click your terminal → "Run as Administrator"

**"Cannot create a file when that file already exists":**
- Run the removal commands (step 3) first, then retry

**Symlinks not working after git clone:**
- Run `git config --global core.symlinks true` and re-clone

## Usage

### Starting a Project

After installation, launch OpenCode in your project directory and describe what you want to build:

```
> I want to build a weather query mini-app. Use long task skill.
```

The system automatically enters the **Requirements** phase and guides you through the full workflow:

```
Requirements -> Design -> Init -> Worker cycles
```

### Finding Skills

Use OpenCode's native `skill` tool to list available skills:

```
use skill tool to list skills
```

### Loading a Skill

Use OpenCode's native `skill` tool to load a specific skill:

```
use skill tool to load long-task/long-task-work
```

### Phase Skill Invocations

Invoke each phase skill directly in OpenCode:

| Phase | OpenCode Invocation |
|-------|---------------------|
| Requirements (Phase 0a) | `use skill long-task/long-task-requirements` |
| Design (Phase 0b) | `use skill long-task/long-task-design` |
| Init (Phase 1) | `use skill long-task/long-task-init` |
| Worker (Phase 2) | `use skill long-task/long-task-work` |
| Increment (Phase 1.5) | `use skill long-task/long-task-increment` |

## Auto-Loop (Unattended Development)

The auto-loop script repeatedly runs OpenCode sessions until all features pass.

### Prerequisites

- Python 3.10+
- OpenCode installed and on PATH
- A project with `feature-list.json` (created by the Init phase)

### Basic Usage

```bash
python scripts/auto_loop_opencode.py feature-list.json
```

### Advanced Usage

```bash
# Specify model
python scripts/auto_loop_opencode.py feature-list.json --model anthropic/claude-sonnet-4-6

# Attach to a running opencode serve instance (avoids cold-starting MCP each iteration)
opencode serve --port 4096  # in a separate terminal
python scripts/auto_loop_opencode.py feature-list.json --attach http://localhost:4096

# Custom iteration limits
python scripts/auto_loop_opencode.py feature-list.json --max-iterations 30 --cooldown 10
```

### Permission Configuration

The auto-loop script uses `--yolo` mode. If your OpenCode version does not yet support `--yolo`, configure permissions in `opencode.json`:

```json
{
  "permission": {
    "*": { "*": "allow" },
    "skill": { "*": "allow" }
  }
}
```

### Interrupt Handling

- **1st Ctrl+C**: Graceful — finishes current iteration, then stops
- **2nd Ctrl+C**: Force — kills child process immediately

## Skill Locations

OpenCode discovers skills from these locations (highest priority first):

1. **Project skills** (`.opencode/skills/`) — Highest priority
2. **Personal skills** (`~/.config/opencode/skills/`)
3. **Long-task skills** (`~/.config/opencode/skills/long-task/`) — via symlink

## Tool Mapping

Skills written for Claude Code are automatically adapted via the bootstrap injection. The mapping is:

| Claude Code Tool | OpenCode Equivalent |
|------------------|---------------------|
| `TodoWrite` | `update_plan` |
| `Task` with subagents | `@mention` syntax |
| `Skill` tool | OpenCode's native `skill` tool |
| `Read`, `Write`, `Edit`, `Bash` | Native OpenCode tools |

## Architecture

### Plugin Structure

**Location:** `~/.config/opencode/long-task-agent/.opencode/plugins/long-task.js`

**How it works:**
1. On every session, the plugin injects the `using-long-task` bootstrap router into the system prompt via `experimental.chat.system.transform`
2. The bootstrap includes **phase detection** — it reads project files to determine the current phase (Requirements, Design, Worker, etc.)
3. Tool mapping instructions are injected so the model knows how to translate Claude Code tool references to OpenCode equivalents

### Skills

**Location:** `~/.config/opencode/skills/long-task/` (symlink to `~/.config/opencode/long-task-agent/skills/`)

11 skills are discovered by OpenCode's native skill system. Each skill has a `SKILL.md` file with YAML frontmatter:

| Skill | Phase | Purpose |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Router (auto-injected, do not load manually) |
| `long-task-requirements` | Phase 0a | Requirements elicitation & SRS |
| `long-task-design` | Phase 0b | Design document |
| `long-task-init` | Phase 1 | Project initialization |
| `long-task-work` | Phase 2 | Worker orchestrator |
| `long-task-increment` | Phase 1.5 | Incremental development |
| `long-task-tdd` | Discipline | TDD Red-Green-Refactor |
| *(quality gates)* | Inline | Coverage & mutation gates (Worker Step 6) |


## Updating

Re-run the installer — it removes the existing clone and re-installs the selected branch (defaulting to `simple`):

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/simple/install.ps1 | iex
```

To update manually without re-cloning (preserves any local edits you made):

```bash
cd ~/.config/opencode/long-task-agent && git pull
```

Restart OpenCode to load the updates.

## Troubleshooting

### Plugin not loading

1. Check plugin exists: `ls ~/.config/opencode/long-task-agent/.opencode/plugins/long-task.js`
2. Check symlink: `ls -l ~/.config/opencode/plugins/long-task.js`
3. Check OpenCode logs for errors
4. Verify the `using-long-task` skill exists: `ls ~/.config/opencode/long-task-agent/skills/using-long-task/SKILL.md`

### Skills not found

1. Verify skills symlink: `ls -l ~/.config/opencode/skills/long-task` (should point to `long-task-agent/skills/`)
2. Use OpenCode's `skill` tool to list what's discovered
3. Check skill structure: each skill needs a `SKILL.md` file with valid frontmatter

### Bootstrap not appearing

1. Restart OpenCode after plugin changes
2. Check OpenCode version supports `experimental.chat.system.transform` hook
3. Ask OpenCode: "what phase is this project in?" — if it answers correctly, bootstrap is working

### Windows: Module not found error

- **Cause:** Git Bash `ln -sf` copies files instead of creating symlinks
- **Fix:** Use `mklink /J` directory junctions instead (see Windows installation steps)

## Testing

Verify your installation:

```bash
# Check plugin file syntax
node --check ~/.config/opencode/long-task-agent/.opencode/plugins/long-task.js

# Check skills are discoverable
opencode run "use skill tool to list all skills" 2>&1 | grep -i long-task

# Check bootstrap injection
opencode run "what phase is this project in?"
```

The agent should detect the project phase and be able to list skills from `long-task/`.

## Getting Help

- Report issues: https://github.com/suriyel/longtaskforagent/issues
- Main documentation: https://github.com/suriyel/longtaskforagent
- OpenCode docs: https://opencode.ai/docs/
