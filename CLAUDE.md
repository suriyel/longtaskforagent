# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Claude Code skill plugin** (`long-task-agent`) enabling multi-session execution of complex software projects. Implements: Requirements → Design → Init → Worker → Finalize, with Hotfix and Increment re-entry points. State bridges via on-disk artifacts. skills loaded on-demand via the `Skill` tool; bootstrap router (`using-long-task`) routes to the correct phase based on project state. Standalone `/deep-explore` skill for on-demand codebase exploration. Standalone `/static-review` skill for pre-push static analysis (iterative scan-fix to zero violations). Standalone `/coverage-retrofit` skill for retrofitting UT coverage and `/mutation-retrofit` skill for retrofitting mutation testing on existing codebases. Independent `long-task-multi-repo` skill for multi-repo projects.

## Key Commands

> **Path note**: paths below are consumer-facing (`long-task-agent/...`). In this repo, replace `long-task-agent/` with `./` or omit.

| Purpose | Command |
|---------|---------|
| Init project | `python scripts/init_project.py <name> --path <dir> [--lang python\|java\|typescript]` |
| Validate feature-list | `python scripts/validate_features.py feature-list.json` |
| Route to next phase | `python scripts/phase_route.py --json` |
| Count phase state | `python scripts/count_pending.py feature-list.json [--json]` |
| Resolve feature design doc path | `python scripts/feature_paths.py design-doc --feature <id> [--must-exist]` |
| Validate guide | `python scripts/validate_guide.py long-task-guide.md` |
| Validate increment | `python scripts/validate_increment_request.py increment-request.json` |
| Validate bugfix | `python scripts/validate_bugfix_request.py bugfix-request.json` |
| Get tool commands | `python scripts/get_tool_commands.py feature-list.json [--json]` |
| Run all tests | `python -m pytest tests/` |
| Run single test | `python -m pytest tests/test_<script_name>.py` |
| Auto-loop (Claude Code) | `python scripts/auto_loop.py feature-list.json [--max-iterations 30] [--log-dir logs] [--cooldown 10]` |
| Auto-loop (OpenCode) | `python scripts/auto_loop_opencode.py feature-list.json [--model anthropic/claude-sonnet-4-6]` |
| Deep-explore codebase | Invoke `long-task:long-task-explore` or `/deep-explore [quick\|standard\|deep] [--focus area] [--path dir]` |
| Static analysis review | Invoke `long-task:long-task-static-review` or `/static-review [--tool checkstyle] [--max-iterations N] [--path dir] [--dry-run]` |
| Coverage retrofit | Invoke `long-task:long-task-coverage-retrofit` or `/coverage-retrofit [--path dir] [--files list] [--branch <branch>] [--max-iterations N] [--line-cov N] [--branch-cov N] [--dry-run]` |
| Mutation retrofit | Invoke `long-task:long-task-mutation-retrofit` or `/mutation-retrofit [--path dir] [--files list] [--branch <branch>] [--max-iterations N] [--mutation N] [--skip-coverage-check] [--dry-run]` |

## Architecture

### Skill System

#### Phase Skills

| Skill | Phase | Trigger |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Routes to correct phase; invoked by LLM at session start based on skill description |
| `long-task-multi-repo` | Multi-repo | `repos-manifest.json` exists — exploration, global SRS, split, dependency distribution |
| `long-task-hotfix` | Hotfix | `bugfix-request.json` exists (HIGHEST priority) |
| `long-task-increment` | Phase 1.5 | `increment-request.json` exists |
| `long-task-codebase-scanner` | Phase 0-pre | No SRS/rules docs, >3 source files — brownfield scan |
| `long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json (single-repo only) |
| `long-task-design` | Phase 0b | SRS exists, no design doc, no feature-list.json |
| `long-task-init` | Phase 1 | Design doc exists, no feature-list.json |
| `long-task-work-design` | Phase 2a | `current.phase=design` (or router newly picks a feature); produces `docs/features/<id>-<slug>.md`, advances `current.phase → tdd`, ends session |
| `long-task-work-tdd` | Phase 2b | `current.phase=tdd`; runs R-G-R SubAgents, clears `current`, marks feature `passing`, ends session |

#### Standalone Skills (no pipeline dependency)

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `long-task-explore` | Deep codebase exploration — architecture, data flow, domain model, API surface, dependencies, code health | On-demand via `/deep-explore` |
| `long-task-static-review` | Pre-push static analysis — auto-detect and fix Checkstyle violations to zero with quality gates per iteration | On-demand via `/static-review [--tool checkstyle] [--max-iterations N] [--path dir]` |
| `long-task-coverage-retrofit` | Retrofit UT coverage for existing/legacy codebases — iterative measure→fix→verify until line + branch coverage thresholds met | On-demand via `/coverage-retrofit [--path dir] [--branch <branch>] [--dry-run]` |
| `long-task-mutation-retrofit` | Retrofit mutation testing for existing/legacy codebases — iterative measure→fix→verify until mutation score threshold met | On-demand via `/mutation-retrofit [--path dir] [--branch <branch>] [--dry-run]` |

#### Discipline Skills (sub-skills dispatched by `long-task-work-design` / `long-task-work-tdd`)

| Skill | Purpose |
|-------|---------|
| `long-task-feature-design` | Feature Detailed Design — interface contracts, pseudocode, test inventory |
| `long-task-tdd-red` | TDD Red — write failing tests for Test Inventory |
| `long-task-tdd-green` | TDD Green — minimal implementation to pass all tests |
| `long-task-tdd-refactor` | TDD Refactor — clean up + static analysis + §11.1 compliance |

#### Skill Call Graph

```
long-task-multi-repo (repos-manifest.json exists — exploration, global SRS, split, dep distribution, handoff)
   └─→ triggered directly when repos-manifest.json exists (router precondition, not a detection step)

using-long-task (router — delegates to scripts/phase_route.py --json; single-repo only)
   ├─→ long-task-codebase-scanner (brownfield, no docs/rules/) → re-evaluate → long-task-requirements OR long-task-design
   ├─→ long-task-requirements ──→ long-task-design ──→ long-task-init
   ├─→ long-task-hotfix (bugfix-request.json — HIGHEST priority)
   │      └─→ validate → reproduce → root cause → enqueue as category=bugfix feature
   ├─→ long-task-increment (increment-request.json)
   │      └─→ update SRS/Design → append features
   └─→ (feature-list.json exists) — phase_route.py routes per root `current`
          ├─→ long-task-work-design (current.phase=design; or new pick → atomic current write)
          │      └─→ long-task-feature-design SubAgent → advance current.phase → tdd → commit → end session
          └─→ long-task-work-tdd (current.phase=tdd)
                 ├─→ long-task-tdd-red SubAgent
                 ├─→ long-task-tdd-green SubAgent
                 ├─→ long-task-tdd-refactor SubAgent
                 └─→ Persist (current=null, feature.status=passing) → commit → end session

long-task-explore (standalone — no pipeline dependency)
   ├─→ codebase-locator SubAgent (breadth-first scan)
   ├─→ codebase-analyzer SubAgent (architecture, data flow, domain, API)
   └─→ codebase-pattern-finder SubAgent (dependencies, coupling, health, debt)

long-task-static-review (standalone — no pipeline dependency)
   └─→ iterative scan-fix cycle (detect tool → scan → fix → compile → UT → mutation → re-scan → repeat until 0)

long-task-coverage-retrofit (standalone — no pipeline dependency)
   └─→ iterative measure→fix→verify cycle (detect env → baseline → coverage-fix SubAgent → re-measure → repeat until line+branch thresholds met)
   └─→ supports --branch <branch> for incremental mode (diff-scoped)

long-task-mutation-retrofit (standalone — no pipeline dependency)
   └─→ iterative measure→fix→verify cycle (detect env → baseline → mutation-fix SubAgent → re-measure → repeat until mutation threshold met)
   └─→ supports --branch <branch> for incremental mode (diff-scoped)
```

### Phase Workflow Summary

| Phase | Skill | Key Output |
|-------|-------|------------|
| 0-pre: Codebase Scan (brownfield) | `long-task-codebase-scanner` | `docs/rules/*.md` — coding style, 二方件 constraints, build patterns |
| 0-multi: Multi-Repo | `long-task-multi-repo` | Global SRS + per-repo SRS split + dependency distribution; session ends with handoff |
| 0a: Requirements | `long-task-requirements` | `docs/plans/*-srs.md` (ISO/IEC/IEEE 29148; Lite 3-5 rounds / Expert 10-20 rounds; Step 10c: single-round mode confirmation) |
| 0b: Design | `long-task-design` | `docs/plans/*-design.md` (merges `docs/rules/` into §11 if brownfield) |
| Hotfix | `long-task-hotfix` | Bugfix enqueued as `category=bugfix` feature; root cause confirmed |
| 1.5: Increment | `long-task-increment` | SRS/Design updated in place; new features appended with `wave` metadata |
| 1: Init | `long-task-init` | `feature-list.json`, `long-task-guide.md`, project skeleton |
| 2a: Worker Design | `long-task-work-design` | Per-feature design doc (`docs/features/<id>-<slug>.md`); advances `current.phase: design → tdd`; ends session |
| 2b: Worker TDD | `long-task-work-tdd` | R-G-R SubAgents; clears `current`; marks feature `passing`; ends session |

### Critical Rules

- **Gate order**: Requirements (SRS) → Design → Init → Feature Design → TDD Red → TDD Green → TDD Refactor → Persist. No skipping.
- **Strict TDD**: Always Red→Green→Refactor (3 separate SubAgents).
- **Verification enforcement**: Never mark "passing" without fresh evidence.
- **§11 compliance in TDD Refactor**: §11.1 grep + code reuse + implementation-summary verification — merged into TDD Refactor SubAgent.
- **Systematic debugging**: Never guess-and-fix; trace root cause first.
- **One feature × one phase per session**: Each Worker-phase skill ends with a session-termination banner; no auto-advance. Multi-feature/multi-phase automation via `scripts/auto_loop.py`.
- **Root `current` lock is the single source of truth**: `feature-list.json.current = {feature_id, phase: "design"|"tdd"} | null`. `phase_route.py` and `validate_features.py` enforce this shape.
- **Hotfix before increment**: When both signal files exist, hotfix runs first; `increment-request.json` preserved.
- **Bug fixes via hotfix skill only**: Never manually add bugfix features; root cause must be confirmed and traceable.
- **Incremental changes via increment skill only**: Never manually edit feature-list.json features; use increment skill.
- **srs_trace required per feature**: Every feature must include `srs_trace` (array of SRS requirement IDs).
- **Deprecated features excluded**: Worker skips; routing counts only active features.
- **二方件 constraints binding**: Design §11.1 mandatory internal libraries are binding for all new code.
- **Codebase scan before requirements or design (brownfield)**: >3 source files + ≥5 commits + no `docs/rules/` → invoke `long-task-codebase-scanner` skill (rule 7b: before requirements; rule 5b: before design in brownfield repos).
- **Targeted explore in requirements/increment (brownfield)**: Requirements Step 1.6 and Increment Step 3.5 auto-trigger `long-task-explore` (quick/standard) when brownfield context + concrete focus direction exist. Non-blocking — failure never prevents proceeding.
- **Static analysis tools: detect, don't parse**: Scanner records tool name + config path + run command. Downstream runs the tool directly.
- **Multi-repo: fully handled by independent `long-task-multi-repo` skill**: Hook detects topology → generates `repos-manifest.json` → `long-task-multi-repo` skill triggered directly (router precondition). User then independently cd's into each repo for single-repo pipeline.

### Multi-Repo Support

Projects with multiple git repositories under a non-git root directory are handled by the independent `long-task-multi-repo` skill:

1. **Hook detection**: `hooks/session-start` detects sub-directory git repos, generates `repos-manifest.json`
2. **Router precondition**: `repos-manifest.json` existence triggers `long-task-multi-repo` directly (router itself is single-repo only)
3. **Multi-repo skill**: Explores all repos, elicits global requirements, writes global SRS, splits into per-repo SRS with IFR contracts, distributes dependency files (reference docs, global SRS, deferred backlog, cross-repo deps) to each sub-repo
4. **Independent execution**: User cd's into each repo directory and runs the full single-repo pipeline (Design → Init → Worker) independently

Key files:
- `repos-manifest.json` — multi-repo topology + cross-repo deps (generated by hook, enriched by multi-repo skill; absent in single-repo projects)
- `docs/plans/*-srs.md` (at project root) — global SRS (multi-repo reference)
- `<repo>/docs/plans/*-srs.md` — per-repo SRS with IFR contracts
- `<repo>/docs/plans/cross-repo-deps.md` — per-repo cross-repo dependency summary
- `<repo>/docs/references/` — user-provided reference docs copied from project root

### Generated Persistent Artifacts

| File | Phase | Purpose |
|------|-------|---------|
| `repos-manifest.json` | Hook + multi-repo | Multi-repo topology + cross-repo deps (generated by hook, enriched by multi-repo skill; absent in single-repo) |
| `docs/rules/*.md` | 0-pre | Codebase conventions (brownfield; merged into Design §11) |
| `docs/plans/*-srs.md` | 0a / multi-repo | Approved SRS (single-repo: per-repo; multi-repo: global at root + per-repo in each sub-repo) |
| `<repo>/docs/plans/global-srs.md` | multi-repo | Copy of global SRS distributed to each sub-repo |
| `<repo>/docs/plans/cross-repo-deps.md` | multi-repo | Per-repo cross-repo interface dependency summary |
| `<repo>/docs/references/*` | multi-repo | User-provided reference docs copied from project root |
| `docs/plans/*-deferred.md` | 0a | Deferred requirements backlog |
| `docs/plans/*-design.md` | 0b | Approved design (includes §11 codebase constraints) |
| `bugfix-request.json` | Hotfix | Signal file (deleted after processing) |
| `increment-request.json` | Increment | Signal file (deleted after processing) |
| `feature-list.json` | 1 | Task inventory with status, constraints, assumptions, waves |
| `long-task-guide.md` | 1 | Tool command reference (test recipes only; NOT workflow guide) |
| `task-progress.md` | 1 | `## Current State` + session log |
| `RELEASE_NOTES.md` | 1 | Keep a Changelog format |
| `docs/features/YYYY-MM-DD-<name>.md` | 2 | Per-feature detailed design |
| `examples/` | 1 (Init) | Optional usage examples directory |
| `logs/session-*.md` | auto_loop | Session logs per iteration |
| `docs/explore/codebase-research.md` | Standalone | Deep codebase exploration report (from `/deep-explore`) |

### Feature List Schema

`feature-list.json` root:
```json
{
  "project": "name",
  "created": "2025-01-15",
  "tech_stack": { "language": "python|java|typescript|c|cpp", "test_framework": "...", "coverage_tool": "...", "mutation_tool": "..." },
  "single_round": false,
  "waves": [{ "id": 0, "date": "2025-01-15", "description": "Initial release" }],
  "constraints": ["Hard limit"],
  "assumptions": ["Implicit belief"],
  "features": [...]
}
```

Each feature:
```json
{
  "id": 1, "wave": 0, "category": "core|bugfix",
  "title": "...", "description": "...", "priority": "high|medium|low", "status": "failing|passing",
  "srs_trace": ["FR-001"], "verification_steps": ["optional scenario"],
  "dependencies": [],
  "deprecated": false, "deprecated_reason": null, "supersedes": null,
  "bug_severity": "Critical|Major|Minor|Cosmetic (bugfix only)",
  "bug_source": "manual-testing (bugfix only)",
  "fixed_feature_id": null, "root_cause": "confirmed root cause (bugfix only)"
}
```

Key field notes:
- `srs_trace`: required; maps feature to SRS requirements for traceability
- `deprecated: true` → `deprecated_reason` required; excluded from Worker/routing
- `waves[]`: increment batch tracking; `wave` on feature = which wave introduced/modified it
- `single_round`: optional boolean; set to `true` by Init when SRS contains `Single-Round: Yes` metadata (user-confirmed at Requirements Step 10c); informational flag — all Worker steps execute their full standard flow regardless

## File Structure

```
long-task-agent/
├── skills/
│   ├── using-long-task/SKILL.md + references/architecture.md
│   ├── long-task-requirements/SKILL.md + references/{problem-framing,scenario-walkthrough,hypothesis-correction,alignment-validation}.md
│   ├── long-task-multi-repo/SKILL.md + references/ (symlinks to requirements refs) + prompts/ (symlinks)
│   ├── long-task-hotfix/SKILL.md
│   ├── long-task-increment/SKILL.md
│   ├── long-task-design/SKILL.md
│   ├── long-task-init/SKILL.md + scripts/init_project.py
│   ├── long-task-feature-design/SKILL.md + references/feature-design-template.md
│   ├── long-task-work-design/SKILL.md       (Worker phase A: per-feature design)
│   ├── long-task-work-tdd/SKILL.md          (Worker phase B: R-G-R)
│   ├── long-task-tdd-shared/references/{iron-law,testing-anti-patterns}.md
│   ├── long-task-tdd-red/SKILL.md + references/tdd-red-execution.md
│   ├── long-task-tdd-green/SKILL.md + references/tdd-green-execution.md
│   ├── long-task-tdd-refactor/SKILL.md + references/tdd-refactor-execution.md
│   ├── long-task-coverage-fix/SKILL.md + references/coverage-fix-execution.md (standalone, used by coverage-retrofit)
│   ├── long-task-mutation-fix/SKILL.md + references/mutation-fix-execution.md (standalone, used by mutation-retrofit)
│   ├── long-task-explore/SKILL.md + references/exploration-dimensions.md (standalone)
│   ├── long-task-static-review/SKILL.md + references/tool-profiles.md (standalone)
│   ├── long-task-coverage-retrofit/SKILL.md + references/{coverage-recipes,iron-law,testing-anti-patterns}.md (standalone, symlinks)
│   ├── long-task-mutation-retrofit/SKILL.md + references/{coverage-recipes,iron-law,testing-anti-patterns}.md (standalone, symlinks)
│   ├── long-task-codebase-scanner/SKILL.md (standalone + pipeline Phase 0-pre)
├── agents/{codebase-locator,codebase-analyzer,codebase-pattern-finder}.md
├── docs/templates/{srs,design,deferred-backlog,rules-index,explore-report}-template.md
├── hooks/{hooks.json,session-start,run-hook.cmd}
│   └── using-long-task/references/{architecture,systematic-debugging,subagent-development,worktree-isolation}.md
├── scripts/{get_tool_commands,validate_features,validate_guide,
│           validate_bugfix_request,validate_increment_request,
│           phase_route,count_pending,feature_paths,
│           auto_loop,auto_loop_opencode}.py
└── tests/test_<script_name>.py  (one file per script)
```

## See Also

- [ReadMe.md](ReadMe.md) — Overview and design rationale
- [skills/using-long-task/references/architecture.md](skills/using-long-task/references/architecture.md) — Persistent artifacts, phase overview
- [skills/long-task-codebase-scanner/SKILL.md](skills/long-task-codebase-scanner/SKILL.md) — Brownfield codebase scanner
- [skills/using-long-task/references/systematic-debugging.md](skills/using-long-task/references/systematic-debugging.md) — Systematic debugging (shared by work-design / work-tdd)
- [skills/using-long-task/references/subagent-development.md](skills/using-long-task/references/subagent-development.md) — Subagent-driven development (shared)
- [skills/using-long-task/references/worktree-isolation.md](skills/using-long-task/references/worktree-isolation.md) — Worktree isolation (multi-version TDD)
- [skills/long-task-work-design/SKILL.md](skills/long-task-work-design/SKILL.md) — Worker phase A (feature design + handoff)
- [skills/long-task-work-tdd/SKILL.md](skills/long-task-work-tdd/SKILL.md) — Worker phase B (TDD R-G-R + persist)
- [scripts/phase_route.py](scripts/phase_route.py) — single-source-of-truth phase router
- [skills/long-task-multi-repo/SKILL.md](skills/long-task-multi-repo/SKILL.md) — Multi-repo requirements, SRS split, dependency distribution
- [skills/long-task-explore/SKILL.md](skills/long-task-explore/SKILL.md) — Standalone deep codebase exploration
- [skills/long-task-static-review/SKILL.md](skills/long-task-static-review/SKILL.md) — Standalone pre-push static analysis (Checkstyle)
- [skills/long-task-coverage-retrofit/SKILL.md](skills/long-task-coverage-retrofit/SKILL.md) — Standalone UT coverage retrofit for legacy codebases
- [skills/long-task-mutation-retrofit/SKILL.md](skills/long-task-mutation-retrofit/SKILL.md) — Standalone mutation testing retrofit for legacy codebases
- [agents/codebase-locator.md](agents/codebase-locator.md) — Codebase structure locator (breadth-first)
- [agents/codebase-analyzer.md](agents/codebase-analyzer.md) — Architecture/data flow/domain analyzer (depth-first)
- [agents/codebase-pattern-finder.md](agents/codebase-pattern-finder.md) — Pattern/health/debt finder (metrics-driven)


<!-- long-task-agent -->
## Long-Task Agent

This project uses a multi-session agent workflow with skills loaded on-demand.
`using-long-task` delegates to `scripts/phase_route.py --json`; follow the emitted `next_skill`. Every Worker-session does **one feature × one phase** and ends with a session-termination banner — no auto-advance.
Flow: Codebase Scan (brownfield) → Requirements (SRS) → Design (merges rules into §11) → Init → Worker-Design → Worker-TDD (× each feature).
Incremental development: place `increment-request.json` → Increment skill updates SRS/Design in place → new features appended → Worker cycles.

Key files: `repos-manifest.json` (multi-repo topology — generated by hook, absent in single-repo), `docs/rules/*.md` (codebase conventions — brownfield only), `docs/plans/*-srs.md` (SRS), `docs/plans/*-deferred.md` (deferred backlog), `docs/plans/*-design.md` (design, includes §11 codebase constraints), `feature-list.json` (task inventory + root `current` lock), `task-progress.md` (session log), `RELEASE_NOTES.md` (changelog), `docs/features/<id>-<slug>.md` (per-feature detailed design; path via `scripts/feature_paths.py`), `increment-request.json` (increment signal), `docs/explore/codebase-research.md` (standalone exploration report).
Multi-repo support: session-start hook detects sub-directory git repos → `repos-manifest.json`. Independent `long-task-multi-repo` skill handles exploration, global SRS, per-repo split, and dependency distribution. User then independently cd's into each repo to run the single-repo pipeline.
<!-- /long-task-agent -->
