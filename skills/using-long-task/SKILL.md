---
name: using-long-task
description: "Use when starting any session in a long-task project - routes to the correct phase skill based on project state"
---

<EXTREMELY-IMPORTANT>
You are in a long-task multi-session project. You MUST invoke the correct phase skill BEFORE any response or action — including clarifying questions.

IF A PHASE SKILL APPLIES, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.

**LANGUAGE RULE**: You MUST respond to the user in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Skill names, code identifiers, and JSON field names remain in English.
</EXTREMELY-IMPORTANT>

## How to Access Skills

Use the `Skill` tool to invoke skills by name (e.g., `long-task:long-task-work`). When invoked, the skill content is loaded and presented to you — follow it directly. Never use the Read tool on skill files.

## Phase Detection

Check project state and invoke the corresponding skill:

```dot
digraph phase_detection {
    "Session Start" [shape=doublecircle];
    "bugfix-request.json exists?" [shape=diamond];
    "increment-request.json exists?" [shape=diamond];
    "feature-list.json exists?" [shape=diamond];
    "All active features passing?" [shape=diamond];
    "Design doc (*-design.md) in docs/plans/?" [shape=diamond];
    "ATS doc (*-ats.md) in docs/plans/?" [shape=diamond];
    "SRS doc (*-srs.md) in docs/plans/?" [shape=diamond];
    "docs/rules/ populated?" [shape=diamond];
    "Source files > 3 AND commits >= 5?" [shape=diamond];
    "Invoke long-task:long-task-hotfix" [shape=box style=filled fillcolor=orange];
    "Invoke long-task:long-task-increment" [shape=box style=filled fillcolor=plum];
    "Invoke long-task:long-task-requirements" [shape=box style=filled fillcolor=lightyellow];
    "Run codebase-scanner then long-task:long-task-requirements" [shape=box style=filled fillcolor=wheat];
    "Invoke long-task:long-task-design" [shape=box style=filled fillcolor=lightblue];
    "Invoke long-task:long-task-ats" [shape=box style=filled fillcolor=lightskyblue];
    "Invoke long-task:long-task-init" [shape=box style=filled fillcolor=lightyellow];
    "Invoke long-task:long-task-work" [shape=box style=filled fillcolor=lightgreen];
    "Invoke long-task:long-task-st" [shape=box style=filled fillcolor=lightcoral];

    "Session Start" -> "bugfix-request.json exists?";
    "bugfix-request.json exists?" -> "Invoke long-task:long-task-hotfix" [label="yes"];
    "bugfix-request.json exists?" -> "increment-request.json exists?" [label="no"];
    "increment-request.json exists?" -> "Invoke long-task:long-task-increment" [label="yes"];
    "increment-request.json exists?" -> "feature-list.json exists?" [label="no"];
    "feature-list.json exists?" -> "All active features passing?" [label="yes"];
    "All active features passing?" -> "Invoke long-task:long-task-st" [label="yes"];
    "All active features passing?" -> "Invoke long-task:long-task-work" [label="no"];
    "feature-list.json exists?" -> "ATS doc (*-ats.md) in docs/plans/?" [label="no"];
    "ATS doc (*-ats.md) in docs/plans/?" -> "Invoke long-task:long-task-init" [label="yes"];
    "ATS doc (*-ats.md) in docs/plans/?" -> "Design doc (*-design.md) in docs/plans/?" [label="no"];
    "Design doc (*-design.md) in docs/plans/?" -> "Invoke long-task:long-task-ats" [label="yes"];
    "Design doc (*-design.md) in docs/plans/?" -> "SRS doc (*-srs.md) in docs/plans/?" [label="no"];
    "SRS doc (*-srs.md) in docs/plans/?" -> "Invoke long-task:long-task-design" [label="yes"];
    "SRS doc (*-srs.md) in docs/plans/?" -> "docs/rules/ populated?" [label="no"];
    "docs/rules/ populated?" -> "Invoke long-task:long-task-requirements" [label="yes"];
    "docs/rules/ populated?" -> "Source files > 3 AND commits >= 5?" [label="no"];
    "Source files > 3 AND commits >= 5?" -> "Run codebase-scanner then long-task:long-task-requirements" [label="yes (brownfield)"];
    "Source files > 3 AND commits >= 5?" -> "Invoke long-task:long-task-requirements" [label="no (greenfield)"];
}
```

**Detection rules:**
0. Check `bugfix-request.json` in project root → if exists → `long-task-hotfix` **(HIGHEST priority)**
   Note: If both `bugfix-request.json` AND `increment-request.json` exist, hotfix runs first; `increment-request.json` is preserved and processed next session.
1. Check `increment-request.json` in project root → if exists → `long-task-increment`
2. Check `feature-list.json` in project root → if exists:
   - Run `python scripts/check_st_readiness.py feature-list.json` — if exit 0 (all active features passing, excludes deprecated) → `long-task-st`
   - Otherwise (some active features failing) → `long-task-work`
3. Check `docs/plans/*-ats.md` → if any match → `long-task-init` (ATS done, proceed to init)
4. Check `docs/plans/*-design.md` → if any match → `long-task-ats` (Design done, proceed to ATS)
5. Check `docs/plans/*-srs.md` → if any match → `long-task-design` (SRS done, proceed to design)
7. Otherwise → check codebase conventions:
   a. Check `docs/rules/` — if exists AND contains ≥1 `.md` file (beyond a greenfield stub) → `long-task-requirements` (rules already scanned)
   b. Check for existing source files (brownfield heuristic): count source files (`*.py`, `*.js`, `*.ts`, `*.java`, `*.c`, `*.cpp`, `*.go`, `*.rs`, etc.) excluding `.git/`, `node_modules/`, `venv/`, `dist/`, `build/`; and check `git rev-list --count HEAD`
      - If source files > 3 AND git commits ≥ 5 → **run codebase-scanner** (see Phase 0-pre below) → then `long-task-requirements`
      - Else (greenfield) → create `docs/rules/README.md` stub ("Greenfield — no conventions to extract") → `long-task-requirements`

## Skill Catalog

### Phase Skills (invoke ONE based on detection above)
| Skill | Phase | When |
|-------|-------|------|
| `long-task:long-task-hotfix` | Hotfix | bugfix-request.json exists (HIGHEST priority) |
| `long-task:long-task-increment` | Phase 1.5 | increment-request.json exists |
| `codebase-scanner` (SubAgent) | Phase 0-pre | No SRS, no rules docs, existing source files > 3 — scan codebase before requirements |
| `long-task:long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json |
| `long-task:long-task-design` | Phase 0b | SRS exists, no design doc, no feature-list.json |
| `long-task:long-task-ats` | Phase 0d | Design doc exists, no ATS doc, no feature-list.json |
| `long-task:long-task-init` | Phase 1 | ATS doc exists (or auto-skipped for tiny projects), no feature-list.json |
| `long-task:long-task-work` | Phase 2 | feature-list.json exists, some active features failing |
| `long-task:long-task-st` | Phase 3 | feature-list.json exists, ALL active features passing |

### Standalone Skills (invoke independently — no pipeline dependency)
| Skill | Purpose | Trigger |
|-------|---------|---------|
| `long-task:long-task-explore` | Deep codebase exploration — architecture, data flow, domain model, API surface, dependencies, code health | On-demand via `/deep-explore [quick\|standard\|deep] [--focus area] [--path dir]` |

### Discipline Skills (invoked by long-task-work as sub-skills — do NOT invoke directly)
| Skill | Purpose |
|-------|---------|
| `long-task:long-task-feature-design` | Feature Detailed Design — interface contracts, algorithm pseudocode, state diagrams, boundary matrices, test inventory (bridges system design → TDD) |
| `long-task:long-task-feature-st` | Black-Box Feature Acceptance Testing — self-managed start/cleanup lifecycle, ISO/IEC/IEEE 29119 test case documentation (per-feature, after Quality Gates) |
| `long-task:long-task-tdd` | TDD Red-Green-Refactor | |

## Key Files (shared contract)

| File | Role |
|------|------|
| `docs/plans/*-srs.md` | Approved SRS — the WHAT |
| `docs/plans/*-deferred.md` | Deferred requirements backlog — next-round pickup via increment |
| `docs/plans/*-design.md` | Approved design — the HOW |
| `docs/plans/*-ats.md` | Approved ATS — the TEST STRATEGY (requirement→scenario mapping) |
| `feature-list.json` | Task inventory — the central shared state |
| `task-progress.md` | `## Current State` header (progress) + session-by-session log |
| `long-task-guide.md` | Project-specific Worker guide |
| `RELEASE_NOTES.md` | Living changelog |
| `docs/test-cases/feature-*.md` | Per-feature ST test case documents (ISO/IEC/IEEE 29119) |
| `docs/plans/*-st-report.md` | System testing report — Go/No-Go verdict |
| `bugfix-request.json` | Signal file — triggers hotfix session (deleted after processing) |
| `increment-request.json` | Signal file — triggers incremental requirements (deleted after processing) |
| `docs/rules/*.md` | Codebase conventions — coding style, 2/3方件 constraints, build patterns, commit conventions (brownfield only) |

## Red Flags

These thoughts mean STOP — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "Let me just look at the code first" | Invoke phase skill first. It tells you HOW to orient. |
| "I know which feature to work on" | Worker skill has Orient step. Follow it. |
| "This feature is simple, skip TDD" | long-task-tdd is non-negotiable. |
| "Tests pass, I can mark it done" | Quality gates (Worker Step 8) MUST pass first. |
| "I remember the workflow" | Skills evolve. Load current version via Skill tool. |
| "I need more context first" | Skill check comes BEFORE exploration. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "Requirements are obvious, skip to design" | long-task-requirements captures what you'd miss. |
| "Test categories can be decided during feature-st" | Ad-hoc assignment leads to SEC/PERF gaps. Run ATS first. |
| "ATS is overkill for this project" | Check Scaling Guide — tiny projects auto-skip ATS. |
| "The SRS already implies the design" | SRS = WHAT, design = HOW. Both are needed. |
| "All features pass, we can ship" | Feature tests ≠ system tests. Run ST phase first. |
| "System testing is overkill" | Integration bugs, NFR failures, and workflow gaps hide until ST. |
| "I'll just add features to the JSON directly" | Invoke the `long-task-increment` skill for tracked, audited changes. |
| "The requirement change is small, no need for impact analysis" | Increment skill catches hidden dependencies. |
| "I'll just fix this quick bug directly" | Invoke `long-task-hotfix` — bug gets tracked in feature-list.json as category=bugfix and fixed via the full Worker pipeline. |
| "I'll generate examples during Worker" | Examples are post-ST (ST Step 13). |
| "I already know the project's conventions" | Run codebase-scanner. Implicit knowledge doesn't persist across sessions. 2/3方件 constraints are easy to miss. |
| "This brownfield project is small, no need to scan" | Auto-skip handles greenfield (≤3 files). Let the scanner decide. |

## Skill Priority

1. **Phase skill first** — determines the entire session workflow
2. **Discipline skills second** — invoked by Worker in strict order (tdd → quality → st-case → review)
3. **On error** — follow systematic-debugging approach in `skills/long-task-work/references/systematic-debugging.md` before any fix

## Phase 0-pre: Codebase Convention Scan (Brownfield Only)

When detection rule 7b triggers (brownfield project, no existing `docs/rules/`), execute these steps **before** invoking `long-task-requirements`:

1. **Create output directory**: `mkdir -p docs/rules/`

2. **Detect language & framework**: analyze file extensions and dependency manifests (`package.json`, `requirements.txt`, `pom.xml`, `Cargo.toml`, `go.mod`, `*.csproj`). Determine scan depth:
   | LOC Range | Depth |
   |-----------|-------|
   | < 1,000 | Lightweight (top 20 files) |
   | 1,000–10,000 | Standard (top 50 files) |
   | > 10,000 | Deep (top 100 + all configs) |

3. **Dispatch `codebase-scanner` SubAgent**:

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

4. **Validate results**: verify ≥1 output file exists in `docs/rules/`. If SubAgent returns BLOCKED, write minimal stubs (non-blocking — scan is best-effort).

5. **User review** via `AskUserQuestion`:
   - Present concise summary of key findings (especially 2/3方件 constraints and prohibited APIs)
   - Ask user to confirm or edit `docs/rules/` files before continuing

6. **Git commit**: `docs: add codebase convention rules`

7. **Invoke `long-task:long-task-requirements`**
