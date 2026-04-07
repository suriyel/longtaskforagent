---
name: long-task-explore
description: "Use for on-demand deep exploration of an existing codebase - analyzes architecture, data flow, domain model, API surface, dependencies, and code health"
---

# Deep Codebase Exploration

Explore an existing codebase to produce a structured understanding document. Dispatches specialized SubAgents to locate key structures, analyze architecture and data flow, and measure code health.

**Announce at start:** "I'm using the long-task-explore skill to deeply explore this codebase."

## Invocation Modes

This skill can be invoked **standalone** OR **from within pipeline phases** (requirements, increment).

- **Standalone**: operates independently — no pipeline state required, no skill chaining
- **Pipeline**: the calling skill provides focus direction and depth; exploration results feed back to the caller

In both modes:
- Do NOT modify any source code, tests, or configuration files
- If `docs/rules/` exists (from codebase-scanner), reference it but do not depend on it

## CRITICAL: DOCUMENT WHAT IS, NOT WHAT SHOULD BE

- DO NOT suggest improvements or changes
- DO NOT critique the implementation or identify "problems"
- DO NOT recommend refactoring, optimization, or architectural changes
- ONLY describe what exists, where it exists, how it works, and how components interact
- You are creating a technical map of the existing system
- All claims must cite `file:line` evidence
- Read-only — never modify source code

## Step 1: Parse Arguments & Announce

Parse user input for optional parameters:

| Parameter | Values | Default |
|-----------|--------|---------|
| Depth | `quick` / `standard` / `deep` | Auto-detect by LOC |
| `--focus` | `architecture` / `dataflow` / `domain` / `api` / `deps` / `health` (comma-separated) | All 6 dimensions |
| `--path` | Relative directory path | `.` (project root) |
| Natural language | Any text describing area of interest | None (full exploration) |

If the user provides a natural-language question (e.g., "帮我理解认证模块", "how does the payment flow work"), treat it as a focus directive — the SubAgents should prioritize that area while still covering the requested dimensions.

## Step 2: Project Detection

Detect the project's characteristics:

1. **Languages**: count files by extension (`*.py`, `*.js`, `*.ts`, `*.tsx`, `*.java`, `*.go`, `*.rs`, `*.c`, `*.cpp`, `*.rb`, `*.kt`, `*.swift`), excluding `.git/`, `node_modules/`, `venv/`, `.venv/`, `dist/`, `build/`, `__pycache__/`
2. **Frameworks**: check dependency manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, `Gemfile`, `*.csproj`)
3. **LOC estimate**: `find <path> -type f -name "*.{ext}" | head -500 | xargs wc -l` (cap sampling at 500 files for speed)
4. **Depth auto-detection** (if user did not specify `--depth`):

   | LOC Range | Default Depth |
   |-----------|---------------|
   | < 1,000 | `quick` |
   | 1,000 – 10,000 | `standard` |
   | > 10,000 | `deep` |

5. **Existing rules**: if `docs/rules/README.md` exists, read it for context (languages, internal libraries, build system). Pass as supplementary context to SubAgents.

Build a **Project Profile** object:
```
- root: {project_root or --path value}
- languages: [list with file counts]
- frameworks: [detected from manifests]
- loc_estimate: N
- depth: quick|standard|deep
- focus: [dimensions] or "all"
- user_question: "..." or null
- existing_rules_summary: "..." or null
```

## Step 3: Dispatch Locator SubAgent (Phase 1 — Breadth-First Scan)

Dispatch the **codebase-locator** SubAgent to quickly identify key structural positions across the codebase.

```
Agent(
  subagent_type="general-purpose",
  description="Locate codebase structure for [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-locator.md

  ## Project Profile
  {project_profile}

  Execute the full locator process per the agent definition.
  Return the structured location inventory as specified in the Structured Return Contract.
  """
)
```

**Wait for locator to return** before proceeding. The location inventory is the input for Phase 2.

If the locator returns `BLOCKED`, fall back to a minimal inventory by scanning the top-level directory structure and entry points only.

## Step 4: Dispatch Analyzer + Pattern-Finder (Phase 2 — Parallel Deep Dive)

Based on the locator's inventory, dispatch **two SubAgents in parallel**:

### Quick Mode Exception

If depth is `quick`, skip Phase 2. Instead, synthesize the locator's inventory directly into a brief overview document (Step 6, quick format). This avoids unnecessary SubAgent overhead for small projects.

### Standard / Deep Mode

Determine which SubAgents to dispatch based on `--focus`:

| Focus includes | Dispatch |
|----------------|----------|
| `architecture`, `dataflow`, `domain`, `api` (any) | Analyzer |
| `deps`, `health` (any) | Pattern-Finder |
| `all` (default) | Both |

```
# Parallel Agent 1: Architecture Analyzer
Agent(
  subagent_type="general-purpose",
  description="Analyze architecture of [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-analyzer.md
  Read the dimension guide at: {plugin_root}/skills/long-task-explore/references/exploration-dimensions.md

  ## Project Profile
  {project_profile}

  ## Location Inventory (from Locator)
  {locator_results}

  ## Dimensions to Analyze
  {filtered_dimensions: architecture, api, dataflow, domain — based on --focus}

  Execute the full analysis process per the agent definition.
  Return the structured analysis as specified in the Structured Return Contract.
  """
)

# Parallel Agent 2: Pattern & Health Finder
Agent(
  subagent_type="general-purpose",
  description="Find patterns and health metrics for [project]",
  prompt="""
  Read the agent definition at: {plugin_root}/agents/codebase-pattern-finder.md
  Read the dimension guide at: {plugin_root}/skills/long-task-explore/references/exploration-dimensions.md

  ## Project Profile
  {project_profile}

  ## Location Inventory (from Locator)
  {locator_results}

  ## Dimensions to Analyze
  {filtered_dimensions: deps, health — based on --focus}

  Execute the full analysis process per the agent definition.
  Return the structured analysis as specified in the Structured Return Contract.
  """
)
```

Wait for both SubAgents to complete.

## Step 5: Synthesize Findings

Merge the returns from all SubAgents (1–3 depending on depth and focus):

1. **Collect structured returns** — each SubAgent provides verdict, metrics, and content sections
2. **Deduplicate** — if multiple SubAgents mention the same files/modules, consolidate
3. **Cross-reference** — link architecture findings to health hotspots (e.g., "Module X is the most complex AND the most coupled")
4. **Build Key Findings Summary** — aggregate metrics:
   - Languages (from Project Profile)
   - Architecture Pattern (from Analyzer)
   - Entry Points count (from Locator)
   - API Endpoints count (from Locator)
   - Domain Entities count (from Analyzer)
   - External Integrations count (from Locator + Pattern-Finder)
   - Complexity Hotspots top 3 (from Pattern-Finder)
   - Test-to-Source Ratio (from Pattern-Finder)
   - Technical Debt Markers count (from Pattern-Finder)

## Step 6: Write Output

Create the exploration report:

```bash
mkdir -p docs/explore/
```

Write `docs/explore/codebase-research.md` using the template at `docs/templates/explore-report-template.md`.

### Output Size by Depth

| Depth | Content | Budget |
|-------|---------|--------|
| Quick | Key Findings Summary + each section as 3–5 bullet points | <= 150 lines |
| Standard | Full 6 sections with Mermaid diagrams and evidence tables | <= 400 lines |
| Deep | Full 6 sections + detailed Code References index + complete hotspot lists | <= 600 lines |

### Focus Filtering

If `--focus` was specified, only include the requested dimension sections. Always include Key Findings Summary and Code References.

### Re-run Behavior

If `docs/explore/codebase-research.md` already exists, overwrite it cleanly. The report is always a fresh snapshot.

## Step 7: Present Summary

Present the Key Findings Summary to the user in a concise format:

```
## Exploration Complete

**[project-name]** — [languages] / [frameworks]
Depth: [depth] | Files sampled: [N] / [M total]

### Key Findings
- Architecture: [pattern]
- Entry Points: [N] | API Endpoints: [N] | Domain Entities: [N]
- External Integrations: [N]
- Top Complexity Hotspot: [file:line]
- Test/Source Ratio: [N/M]
- Tech Debt Markers: [N] TODOs, [M] FIXMEs

Full report: docs/explore/codebase-research.md
```

If the user provided a natural-language question, answer it directly using the synthesized findings before showing the summary.

Inform the user they can ask follow-up questions about specific modules or components.

## Depth-Specific Behavior Summary

| Aspect | Quick | Standard | Deep |
|--------|-------|----------|------|
| SubAgents dispatched | 1 (locator only) | 2–3 (locator → analyzer + pattern-finder) | 3 (all) |
| File sampling per agent | Top 30 | Top 60 | Top 120 + all configs |
| Mermaid diagrams | 0 | 2–3 | All applicable |
| Evidence citations | Top-3 per category | Top-5 per category | Exhaustive |
| Output budget | 150 lines | 400 lines | 600 lines |

## Focus Dimension Reference

| Keyword | Dimension | Handled By |
|---------|-----------|------------|
| `architecture` | Architecture Overview — module decomposition, patterns, dependency graph | Analyzer |
| `api` | Entry Points & API Surface — endpoints, CLI commands, config surface | Analyzer |
| `dataflow` | Data Flow & State Management — models, pipelines, caching | Analyzer |
| `domain` | Domain Model & Business Logic — entities, rules, algorithms | Analyzer |
| `deps` | Dependencies & Integrations — dependency inventory, coupling, external services | Pattern-Finder |
| `health` | Code Health & Complexity — hotspots, test landscape, tech debt | Pattern-Finder |

## Rules

- **Read-only** — do NOT modify any source files, configs, or git state
- **Evidence-based** — every structural claim needs `file:line` examples
- **No judgment** — document patterns as-is, even if inconsistent or outdated
- **Output budget** — respect line limits per depth level
- **Pipeline isolation** — never read or write pipeline artifacts (feature-list.json, SRS, design docs)
- **Idempotent** — re-running always produces a clean, fresh report
- **SubAgent efficiency** — use Glob for file discovery, Grep for pattern matching, Read for file inspection, Bash only for git/wc/find commands
