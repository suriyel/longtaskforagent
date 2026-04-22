# Language / 语言

**[English](README_EN.md)** | **[中文](README.md)**

---

# Quick Start

### 1. Installation

#### Option 1: Claude Code Native Command (Recommended)

In Claude Code, register the marketplace first:

```bash
/plugin marketplace add suriyel/longtaskforagent
```

Then install the plugin from this marketplace:

```shell
/plugin install long-task@longtaskforagent
```

#### Option 2: One-line Installer Script

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/main/claude-code/install.ps1 | iex
```

The script automatically:
- Clones the repository to `~/.claude/plugins/marketplaces/longtaskforagent/`
- Updates `known_marketplaces.json` registration

After installation, use Claude Code to install plugins:

```shell
/plugin install long-task@longtaskforagent
```

#### Option 3: OpenCode Users

If you use [OpenCode](https://opencode.ai):

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/suriyel/longtaskforagent/main/install.sh | bash
```

**Windows (PowerShell — requires Developer Mode or Administrator):**

```powershell
irm https://raw.githubusercontent.com/suriyel/longtaskforagent/main/install.ps1 | iex
```

Restart OpenCode after installation. See the [OpenCode Installation Guide](docs/README.opencode.md) for full details.

### 2. Quick Start

After launching Claude Code, simply tell it what you want to build:

```
> I want to build a GitHub trending projects weekly report system. use `long task skill`.
```

The system will automatically enter the **Requirements phase**, helping you refine requirements through structured questioning and ultimately generate a standardized SRS document. The subsequent workflow is fully automated:

```
Requirements → Design → Init → Worker cycles
```

[View sample project](https://github.com/suriyel/githubtrends)

![](http://gitee.com/null_161_0561/picpic/raw/master/2021/image-20260313224154726.png)

---

# Long-Task Agent

**A Claude Code skill plugin that turns single-session AI coding into a rigorous, multi-session software engineering workflow.**

Most AI coding assistants lose context after one conversation. Long-Task Agent solves this by implementing a five-phase architecture with persistent state bridging — enabling Claude Code to build complex projects across unlimited sessions with the discipline of a professional engineering team.
![Hero Banner](images/1.png)

## Why Long-Task Agent?

| Problem | How Long-Task Agent Solves It |
|---------|-------------------------------|
| AI forgets everything after `/clear` | Persistent artifacts (`feature-list.json`, `task-progress.md`, git history) bridge sessions automatically |
| AI generates code without understanding requirements | ISO/IEC/IEEE 29148-aligned requirements elicitation produces an approved SRS before any code is written |
| AI skips testing or writes shallow tests | Strict TDD (Red→Green→Refactor) with coverage gates (≥90% line, ≥80% branch) and mutation testing (≥80% score) |
| AI drifts from the approved design | Design interface coverage gate + inline compliance check after every feature |
| No way to add features to an existing project safely | Increment skill performs impact analysis, updates SRS/Design in place, tracks changes with waves |
| "Works on my machine" syndrome | Strict TDD + coverage gates + mutation testing ensure code quality |

![Problem vs Solution](images/2.png)

## Core Philosophy

### 1. Requirements-Driven, Not Code-First

Every project starts with structured requirements elicitation — not coding. The SRS captures the *what* and the design document captures the *how*. No code is written until both are approved.

### 2. Persistent State Bridges Sessions

Ten+ persistent artifacts ensure zero knowledge loss between sessions:

| Artifact | Purpose |
|----------|---------|
| `feature-list.json` | Structured task inventory with status tracking (JSON prevents model corruption) |
| `task-progress.md` | Session-by-session log with current state header |
| `docs/plans/*-srs.md` | Approved Software Requirements Specification |
| `docs/plans/*-design.md` | Approved technical design document |
| `long-task-guide.md` | Worker session guide with env activation + tool commands |
| `RELEASE_NOTES.md` | Living changelog in Keep a Changelog format |
| Git history | Full change history with descriptive commits |

### 3. Quality is Non-Negotiable

Every feature passes through a gauntlet of automated quality gates — no exceptions, no shortcuts:

- **TDD Red→Green→Refactor** — tests are written before code, always
- **Coverage Gate** — line ≥90%, branch ≥80%
- **Mutation Gate** — mutation score ≥80% (catches tests that pass without actually testing anything)
- **Inline Compliance Check** — mechanical verification of interface contracts, test inventory, dependency versions after every feature

### 4. One Feature Per Cycle

Each worker session focuses on exactly one feature. This prevents context exhaustion, ensures clean commits, and keeps every feature independently verifiable.

![Quality Gates](images/3.png)

## Five-Phase Architecture


![Architecture](images/4.png)

### Phase 0a: Requirements Elicitation

- Structured questioning aligned with ISO/IEC/IEEE 29148
- EARS requirement templates (Given/When/Then acceptance criteria)
- Anti-pattern detection: weasel words, compound requirements, design leakage
- Produces an approved **SRS** (`docs/plans/*-srs.md`)

### Phase 0b: Design

- Proposes 2-3 approaches with trade-offs
- Per-feature Mermaid diagrams (class, sequence, flow)
- Third-party dependency versions with compatibility verification
- Produces an approved **Design Document** (`docs/plans/*-design.md`)

### Phase 1: Initialization

- Reads SRS + Design, scaffolds project skeleton
- Bidirectional granularity analysis at requirements phase (G1-G6 split + S1-S4 merge) ensures each FR fits a single-session context budget
- Scaffolds initial project files

### Phase 2: Worker Cycles

Each cycle follows a strict discipline:

```
Orient → Bootstrap → DevTools Gate → Plan
  → TDD Red → TDD Green → Coverage Gate
    → TDD Refactor → Mutation Gate
      → Inline Compliance Check
        → Persist → Next Feature
```

### Phase 1.5: Increment (Post-Launch Changes)

- Place an `increment-request.json` signal file → the skill auto-detects it
- Impact analysis against existing features
- Updates SRS, Design in place (git tracks history)
- Appends new features with wave metadata for traceability
  ![Worker Cycle](images/5.png)

## 8-Skill Superpowers Architecture

Long-Task Agent uses an **on-demand skill loading** pattern — only the bootstrap router is loaded at session start; phase skills are loaded as needed, keeping context lean.

```
using-long-task (bootstrap router — always loaded)
   │
   ├─→ long-task-requirements ──→ long-task-design ──→ long-task-init
   │                                                        │
   │                                                        ↓
   ├─→ long-task-increment (if increment-request.json exists)         long-task-work
   │                                                                    │  │
   │                                                             ┌──────┘  │
   │                                                             ↓         ↓
   │                                                        long-task  long-task
   │                                                          -tdd     -quality
   │                                                             │          │
```

| Skill | Role |
|-------|------|
| `using-long-task` | Bootstrap router — detects project state, invokes correct phase |
| `long-task-requirements` | ISO 29148 requirements elicitation → SRS |
| `long-task-design` | Technical design with trade-off analysis |
| `long-task-init` | Project scaffolding and feature decomposition |
| `long-task-work` | Worker orchestrator (one feature per cycle) |
| `long-task-tdd` | TDD Red→Green→Refactor discipline |
| *(quality gates)* | Coverage gate + mutation gate (inline in Worker Step 8) |
| `long-task-increment` | Post-launch feature additions with impact analysis |

---

## Multi-Language Support

Long-Task Agent is language-agnostic. It supports any tech stack through configurable tool settings:

| Language | Test Framework | Coverage | Mutation Testing |
|----------|---------------|----------|------------------|
| Python | pytest | pytest-cov | mutmut |
| Java | JUnit | JaCoCo | PIT (pitest) |
| TypeScript | Vitest / Jest | c8 / istanbul | Stryker |
| C/C++ | Google Test | gcov + lcov | Mull |
| *Custom* | *Any* | *Any* | *Any* |

The `tech_stack` field in `feature-list.json` drives all tool commands — use `get_tool_commands.py` to eliminate per-language lookup:

```bash
python long-task-agent/scripts/get_tool_commands.py feature-list.json
```

---

## Automated Workflow Scripts

### auto_loop.py - Uninterrupted Execution Guarantee

The `auto_loop.py` script is the core component for **ensuring uninterrupted execution** of long-task workflows. It automates multi-feature development by repeatedly calling Claude Code until all active features pass or a termination condition is met.

**Core Value:**
- 🔄 **Automated Iteration** - No manual repetition needed, the script automatically advances the workflow
- ⏸️ **Graceful Interruption** - Supports two-level Ctrl+C interruption, ensuring current work is not lost
- 🛡️ **Error Detection** - Automatically identifies unrecoverable errors like context limits and rate limits
- 📊 **Status Tracking** - Real-time display of feature pass status

**Usage:**
```bash
python scripts/auto_loop.py feature-list.json
python scripts/auto_loop.py feature-list.json --max-iterations 30
python scripts/auto_loop.py feature-list.json --cooldown 10
python scripts/auto_loop.py feature-list.json --prompt "continue"
```

**Parameters:**
- `feature_list`: Path to feature-list.json (required)
- `--max-iterations`: Maximum number of iterations (default: 50)
- `--cooldown`: Seconds to wait between iterations (default: 5)
- `--prompt`: Prompt to send each iteration (default: 继续)

**Interrupt Handling:**
- **1st Ctrl+C**: Graceful stop - finish current iteration, then stop
- **2nd Ctrl+C**: Force kill - terminate child process immediately

**Exit Codes:**
- 0: All features passing
- 1: Error or max iterations reached
- 2: claude command failed
- 3: Unrecoverable error detected (context limit, rate limit, etc.)
- 130: Interrupted by user (Ctrl+C)

---

## Validation & Safety Scripts

The plugin includes a suite of validation scripts to prevent common failures:

| Script | Purpose |
|--------|---------|
| `validate_features.py` | Validate `feature-list.json` schema and data integrity |
| `validate_guide.py` | Validate `long-task-guide.md` structural integrity |
| `validate_increment_request.py` | Validate increment request signal file |
| `get_tool_commands.py` | Map tech stack to CLI commands |

---

## Template Customization Guide

Long-Task Agent provides two customizable document templates for generating standards-compliant requirements and design documents.

### Built-in Templates

| Template | Path | Purpose | Filling Intensity |
|----------|------|---------|----------|
| SRS Template | `docs/templates/srs-template.md` | Full SRS aligned with ISO/IEC/IEEE 29148 (empty sections marked `[N/A]` per `Input Maturity Level`) | L1: all sections; L2/L3: §1.3 / §3 personas / §3.1 use-case view may be marked `[N/A]` |
| Design Template | `docs/templates/design-template.md` | Full technical design (§0-§11 with §3.5 impact surface / §6.2.1 config schema / §6.2.2 message schema subtables for L2/L3 incremental specs; empty sections omittable) | L1: architecture + data model filled; L2/L3: §1 drivers / §3.1-§3.4 architecture / §5 data model / §7 3rd-party deps may be marked `[N/A]` |

> **`Input Maturity Level` (L1/L2/L3) is auto-evaluated by `long-task-requirements` Step 1.2** (based on hard-identifier density + colloquial-word density); level determines section filling intensity. One template set, empty sections omitted per level.

### Customization Methods

#### SRS Template Customization

During the **Requirements Phase** (`long-task-requirements`), specify a custom template path via conversation:

```
Please use my custom SRS template: docs/templates/my-srs-template.md
(when unspecified, the default template is loaded; section omission granularity follows `Input Maturity Level`)
```

**Requirements**: Template must be a `.md` file containing at least one `## ` heading.

#### Design Template Customization

During the **Design Phase** (`long-task-design`), specify a custom template path via conversation:

```
Please use my custom design template: docs/templates/my-design-template.md
(when unspecified, the default template is loaded; section omission granularity follows `Input Maturity Level`)
```

**Requirements**: Template must be a `.md` file containing at least one `## ` heading.

### Template Priority Rules

1. **User-specified path** > **Built-in default template**
2. Template file must exist, otherwise falls back to default
3. Template must pass validation (`.md` file + at least one `## ` heading)

### Best Practices

1. **Copy built-in templates as a starting point**: Preserve existing section structure, only modify guidance text
2. **Maintain standards compliance**: SRS templates should retain ISO 29148 core sections
3. **Version control**: Commit custom templates to git for team collaboration

---

## How It Compares

<!-- ILLUSTRATION: Comparison Matrix
![Comparison](images/6.png)

> **Text-to-image prompt**: A feature comparison matrix rendered as a clean infographic table. Rows represent capabilities: "Multi-session persistence", "Requirements elicitation", "TDD enforcement", "Coverage gates", "Mutation testing", "UI style consistency", "Inline compliance check", "System testing", "Incremental development". Columns compare "Typical AI Coding" (mostly red X marks) vs "Long-Task Agent" (all green checkmarks). The Long-Task Agent column glows with a subtle highlight. Clean table design with alternating row colors, professional fonts. Landscape, 1200×800px.
-->

| Capability | Typical AI Coding | Long-Task Agent |
|------------|------------------|-----------------|
| Multi-session persistence | Manual copy-paste | Automatic via 10+ persistent artifacts |
| Requirements process | "Just build it" | ISO 29148-aligned SRS with structured elicitation |
| Design process | Ad-hoc | 2-3 approaches with trade-offs, section-by-section approval |
| TDD discipline | Optional, often skipped | Mandatory Red→Green→Refactor for every feature |
| Test quality verification | Line coverage only (if any) | Coverage + mutation testing with configurable thresholds |
| Post-implementation verification | None | Design interface coverage gate + inline compliance check |
| Adding features post-launch | Edit code directly | Impact analysis, tracked waves, document updates |
| Project state visibility | Read the code | `task-progress.md` + `feature-list.json` |

---

## Project Structure

```
long-task-agent/
├── skills/                          # 8 skills (on-demand loaded)
│   ├── using-long-task/             # Bootstrap router
│   ├── long-task-requirements/      # Phase 0a: Requirements & SRS
│   ├── long-task-design/            # Phase 0b: Design
│   ├── long-task-init/              # Phase 1: Initialization
│   ├── long-task-work/              # Phase 2: Worker orchestrator
│   ├── long-task-tdd/               # TDD discipline
│   ├── long-task-quality/           # Coverage + mutation gates (reference files, not standalone skill)
│   └── long-task-increment/         # Incremental development
├── skills/using-long-task/scripts/  # Shared scripts (router + validators + auto_loop)
├── skills/long-task-init/scripts/   # init_project.py (hook-copied to consumer project)
├── tests/                           # Test suite for all scripts
├── hooks/                           # SessionStart hook config
├── commands/                        # User shortcut commands
├── docs/templates/                  # Customizable SRS & design templates
└── CLAUDE.md                        # Cross-session navigation index
```

---

## Guiding Principles

> **"Measure twice, cut once."**

1. **No code without approved requirements** — the SRS captures hidden assumptions before they become bugs
2. **No implementation without approved design** — 2-3 approaches are evaluated before committing to one
3. **No shortcuts on quality** — TDD, coverage, mutation testing, and inline compliance check are non-negotiable gates
4. **One feature, one cycle** — focused work prevents context exhaustion and ensures clean, atomic commits
5. **Persistent artifacts over ephemeral memory** — JSON state files and git history survive any context loss
6. **Systematic debugging over guess-and-fix** — root cause analysis before any fix attempt
7. **Immutable verification steps** — once set, the bar never lowers


![Principles](images/7.png)

## Roadmap

- **Parallel Agent Dispatch** — identify independent features and dispatch worker subagents in parallel

---

## Acknowledgments

- TDD approach inspired by [superpowers](https://github.com/obra/superpowers)
- Long task execution reference from Bilibili creator [数字游牧人](https://b23.tv/UUVywob?share_medium=android&share_source=weixin&bbid=XUD7142DB761960E57CD68EE4E71913CF4699&ts=1773413437129)

## License

[MIT](LICENSE)

---

<p align="center">
  <i>Built for Claude Code — turning AI-assisted development into AI-engineered development.</i>
</p>
