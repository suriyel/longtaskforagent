# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Claude Code skill plugin** (`long-task-agent`) enabling multi-session execution of complex software projects. Implements: Requirements → UCD → Design → ATS → Init → Worker → ST → Finalize, with Hotfix and Increment re-entry points. State bridges via on-disk artifacts. 27 skills loaded on-demand via the `Skill` tool (16 top-level + 5 increment sub-skills + 3 requirements sub-skills + 3 init sub-skills); bootstrap router (`using-long-task`) routes to the correct phase based on project state. Standalone `/deep-explore` skill for on-demand codebase exploration.

## Key Commands

> **Path note**: paths below are consumer-facing (`long-task-agent/...`). In this repo, replace `long-task-agent/` with `./` or omit.

| Purpose | Command |
|---------|---------|
| Init project | `python scripts/init_project.py <name> --path <dir> [--lang python\|java\|typescript] [--line-cov N] [--branch-cov N]` |
| Validate feature-list | `python scripts/validate_features.py feature-list.json` |
| Validate guide | `python scripts/validate_guide.py long-task-guide.md [--feature-list feature-list.json]` |
| Check configs | `python scripts/check_configs.py feature-list.json [--feature N]` |
| Check DevTools MCP | `python scripts/check_devtools.py feature-list.json [--feature N]` |
| Validate ATS | `python scripts/validate_ats.py docs/plans/ats.md [--srs docs/plans/srs.md]` |
| Check ATS coverage | `python scripts/check_ats_coverage.py docs/plans/ats.md --feature-list feature-list.json [--feature N] [--strict]` |
| Check ST readiness | `python scripts/check_st_readiness.py feature-list.json` |
| Validate ST cases | `python scripts/validate_st_cases.py docs/test-cases/feature-N.md [--feature-list feature-list.json --feature N]` |
| Validate increment | `python scripts/validate_increment_request.py increment-request.json` |
| Validate bugfix | `python scripts/validate_bugfix_request.py bugfix-request.json` |
| Get tool commands | `python scripts/get_tool_commands.py feature-list.json [--json]` |
| Check real tests | `python scripts/check_real_tests.py feature-list.json [--feature N] [--require-for-deps] [--json]` |
| Run all tests | `python -m pytest tests/` |
| Run single test | `python -m pytest tests/test_<script_name>.py` |
| Auto-loop (Claude Code) | `python scripts/auto_loop.py feature-list.json [--max-iterations 30] [--log-dir logs] [--cooldown 10]` |
| Auto-loop (OpenCode) | `python scripts/auto_loop_opencode.py feature-list.json [--model anthropic/claude-sonnet-4-6]` |
| Deep-explore codebase | Invoke `long-task:long-task-explore` or `/deep-explore [quick\|standard\|deep] [--focus area] [--path dir]` |

## Architecture

### 27-Skill System (16 top-level + 5 increment sub-skills + 3 requirements sub-skills + 3 init sub-skills)

#### Phase Skills

| Skill | Phase | Trigger |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Routes to correct phase; invoked by LLM at session start based on skill description |
| `long-task-hotfix` | Hotfix | `bugfix-request.json` exists (HIGHEST priority) |
| `long-task-increment` | Phase 1.5 | `increment-request.json` exists |
| `codebase-scanner` (SubAgent) | Phase 0-pre | No SRS/rules docs, >3 source files — brownfield scan |
| `long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json |
| `long-task-ucd` | Phase 0b | SRS exists, no UCD/design doc, no feature-list.json |
| `long-task-design` | Phase 0c | SRS + UCD exist (or no UI), no design doc, no feature-list.json |
| `long-task-ats` | Phase 0d | Design doc exists, no ATS doc, no feature-list.json |
| `long-task-init` | Phase 1 | ATS doc exists (or auto-skipped), no feature-list.json |
| `long-task-work` | Phase 2 | feature-list.json exists, some active features failing |
| `long-task-st` | Phase 3 | feature-list.json exists, ALL active features passing |

#### Standalone Skills (no pipeline dependency)

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `long-task-explore` | Deep codebase exploration — architecture, data flow, domain model, API surface, dependencies, code health | On-demand via `/deep-explore` |

#### Discipline Skills (sub-skills of long-task-work)

| Skill | Purpose |
|-------|---------|
| `long-task-feature-design` | Feature Detailed Design — interface contracts, pseudocode, diagrams, test inventory |
| `long-task-tdd` | TDD Red-Green-Refactor |
| `long-task-quality` | Coverage Gate |
| `long-task-feature-st` | Black-Box Feature Acceptance Testing (self-managed lifecycle, Chrome DevTools MCP + ISO/IEC/IEEE 29119) |

#### Discipline Skills (sub-skills of long-task-increment)

All dispatched by `long-task-increment` orchestrator; each returns a Structured Return Contract (see `skills/long-task-work/references/structured-return-contract.md`); main agent handles approval via `skills/long-task-increment/references/approval-revise-loop.md`.

| Skill | Purpose |
|-------|---------|
| `long-task-increment-impact` | Step 3 — impact matrix + API compatibility table from new/modified/deprecated requirements |
| `long-task-increment-design` | Step 4 — in-place revision of design doc; §6.2 contract propagation; env-guide.md §3/§4 update |
| `long-task-increment-ats` | Step 4b — in-place ATS mapping table revision; auto-skip if no ATS |
| `long-task-increment-ucd` | Step 5 — in-place UCD style guide revision; auto-skip if no UI reqs |
| `long-task-increment-srs` | Step 6 — in-place SRS update + §1.4 ESI backfill + feature-list.json decomposition + validate |

#### Discipline Skills (sub-skills of long-task-requirements)

All dispatched by `long-task-requirements` orchestrator; each returns a Structured Return Contract; main agent handles approval via `skills/long-task-requirements/references/approval-revise-loop.md`.

| Skill | Purpose |
|-------|---------|
| `long-task-requirements-quality` | Step 7–11 — classify, write EARS, generate diagrams, quality-validate, granularity size (G1-G6/S1-S4), propose deferrals |
| `long-task-requirements-alignment` | Expert E10 — root-cause traceability, JTBD verification, pre-mortem, orphan FR detection |
| `long-task-requirements-finalize` | Step 15 — save SRS + optional deferred backlog + git commit |

#### Discipline Skills (sub-skills of long-task-init)

All dispatched by `long-task-init` orchestrator; each returns a Structured Return Contract; main agent handles approval via `skills/long-task-init/references/approval-revise-loop.md`.

| Skill | Purpose |
|-------|---------|
| `long-task-init-env` | Step 3 — generate `env-guide.md` (§1–§6) from template + `docs/rules/*.md` + design; §3/§4 dual approval gate |
| `long-task-init-bootstrap` | Step 4 — generate `init.sh` / `init.ps1` from recipes + tech_stack; zero-approval with internal `bash -n` + PowerShell syntax self-check |
| `long-task-init-features` | Step 5 — generate `long-task-guide.md` + populate `feature-list.json` + `.env.example` + project-specific `scripts/check_configs.py` + validate; returns LOC distribution for sizing gate |

#### Meta Skills

| Skill | Purpose |
|-------|---------|
| `long-task-finalize` | Post-ST: usage examples + RELEASE_NOTES/task-progress finalization |

#### Skill Call Graph

```
using-long-task (router)
   ├─→ codebase-scanner SubAgent (brownfield, no docs/rules/) ──→ long-task-requirements
   ├─→ long-task-requirements ──→ long-task-ucd ──→ long-task-design ──→ long-task-ats ──→ long-task-init ──→ long-task-work
   │      ├─→ long-task-requirements-quality (Step 7–11)
   │      ├─→ long-task-requirements-alignment (Expert E10; auto-skip for Lite)
   │      └─→ long-task-requirements-finalize (Step 15)
   │                              (auto-skip: no UI)               (auto-skip: ≤5 FR)
   │                                                                                   │
   │                                                                    long-task-init orchestrator:
   │                                                                    ├─→ long-task-init-env (Step 3)
   │                                                                    ├─→ long-task-init-bootstrap (Step 4)
   │                                                                    └─→ long-task-init-features (Step 5) → long-task-work
   ├─→ long-task-hotfix (bugfix-request.json — HIGHEST priority)
   │      └─→ validate → reproduce → root cause → enqueue as category=bugfix → long-task-work
   ├─→ long-task-increment (increment-request.json)
   │      ├─→ long-task-increment-impact (Step 3)
   │      ├─→ long-task-increment-design (Step 4)
   │      ├─→ long-task-increment-ats (Step 4b; auto-skip if no ATS)
   │      ├─→ long-task-increment-ucd (Step 5; auto-skip if no UI)
   │      └─→ long-task-increment-srs (Step 6) → long-task-work
   ├─→ long-task-work (active features failing)
   │      ├─→ long-task-feature-design (Step 4)
   │      ├─→ long-task-tdd (Steps 6-8)
   │      ├─→ long-task-quality (Step 9)
   │      └─→ long-task-feature-st (Step 10)
   └─→ long-task-st (ALL active features passing)
          ├─→ long-task-work (defects found → fix)
          └─→ long-task-finalize (Go verdict)

long-task-explore (standalone — no pipeline dependency)
   ├─→ codebase-locator SubAgent (breadth-first scan)
   ├─→ codebase-analyzer SubAgent (architecture, data flow, domain, API)
   └─→ codebase-pattern-finder SubAgent (dependencies, coupling, health, debt)
```

### Phase Workflow Summary

| Phase | Skill | Key Output |
|-------|-------|------------|
| 0-pre: Codebase Scan (brownfield) | `codebase-scanner` SubAgent | `docs/rules/*.md` — coding style, 2/3方件 constraints, build patterns, commit conventions |
| 0a: Requirements | `long-task-requirements` | `docs/plans/*-srs.md` (ISO/IEC/IEEE 29148; Lite 3-5 rounds / Expert 10-20 rounds) |
| 0b: UCD Style Guide | `long-task-ucd` | `docs/plans/*-ucd.md` (auto-skips if no UI features) |
| 0c: Design | `long-task-design` | `docs/plans/*-design.md` (6 sections: architecture / feature integration specs / data model / internal API contracts / external interfaces / task decomposition) |
| 0d: ATS | `long-task-ats` | `docs/plans/*-ats.md` (req→scenario mapping; independent reviewer subagent; auto-skips ≤5 FR) |
| Hotfix | `long-task-hotfix` | Bugfix enqueued as `category=bugfix` feature; root cause confirmed |
| 1.5: Increment | `long-task-increment` | SRS/Design/UCD updated in place; new features appended with `wave` metadata |
| 1: Init | `long-task-init` | `feature-list.json`, `long-task-guide.md`, project skeleton, initial git commit |
| 2: Worker | `long-task-work` | TDD → Quality → Feature-ST → Inline Check per feature |
| 3: System Testing | `long-task-st` | ST plan/report; Go/No-Go verdict; chains to Finalize |

### Critical Rules

- **Gate order**: Config gate → Requirements (SRS) → UCD (UI projects) → Design → ATS → Init → TDD → Coverage → Feature-ST → ST → Finalize. No skipping.
- **ATS reviewer mandatory**: Independent subagent reviews ATS before approval; max 2 fix rounds then user escalation.
- **ATS constrains downstream**: `srs_trace` → ATS category lookup drives `ui` flag; feature-st must satisfy ATS category requirements.
- **Strict TDD**: Always Red→Green→Refactor. Coverage: line ≥90%, branch ≥80%.
- **Verification enforcement**: Never mark "passing" without fresh evidence.
- **Inline compliance after every feature**: interface contract, test inventory, dependency versions, UCD tokens (no SubAgent).
- **Systematic debugging**: Never guess-and-fix; trace root cause first.
- **One feature per session**: Multi-feature automation via `scripts/auto_loop.py`.
- **UI features**: Mark `"ui": true`; require Chrome DevTools MCP testing; Feature Design must include Visual Rendering Contract (selectors, render triggers, positive + interactive assertions); TDD asserts elements present AND interactive; Feature-ST verifies rendering then performs Exploratory Visual Assessment (Rendering Completeness, Interactive Depth, Visual Coherence, Functional Accuracy). Blank canvas = failing. Display-only elements = Major defect.
- **System testing before release**: ST phase required (regression, integration, E2E, NFR, exploratory); no release without Go verdict.
- **Hotfix before increment**: When both signal files exist, hotfix runs first; `increment-request.json` preserved.
- **Bug fixes via hotfix skill only**: Never manually add bugfix features; root cause must be confirmed and traceable.
- **Incremental changes via increment skill only**: Never manually edit feature-list.json features; use increment skill.
- **srs_trace required per feature**: Every feature must include `srs_trace` (array of SRS requirement IDs).
- **ST acceptance test cases after Quality Gates**: ISO/IEC/IEEE 29119 test cases per feature; validate implementation against requirements.
- **Deprecated features excluded**: Worker skips; ST readiness ignores; routing counts only active features.
- **Service lifecycle via env-guide.md**: All start/stop/restart use `env-guide.md` commands. Follow 4-step Restart Protocol between test cycles. Capture first 30 lines of startup output for PID/port.
- **Startup output in code**: Servers must print bound port, PID, and ready signal at startup.
- **Real tests mandatory for external-dependency features**: Features with `required_configs[]` containing URL/HOST/PORT/DSN/URI/CONNECTION/ENDPOINT keys cannot use pure-function exemption. Use `check_real_tests.py --require-for-deps`.
- **2/3方件 constraints binding**: `env-guide.md §4.1` mandatory internal libraries and `§4.2` prohibited APIs (sourced from `docs/rules/coding-constraints.md`) are binding for all new code.
- **Codebase scan before requirements (brownfield)**: >3 source files + ≥5 commits → run codebase-scanner first.
- **Targeted explore in requirements/increment (brownfield)**: Requirements Step 1.6 and Increment Step 3.5 auto-trigger `long-task-explore` (quick/standard) when brownfield context + concrete focus direction exist. Non-blocking — failure never prevents proceeding.
- **Static analysis tools: detect, don't parse**: Scanner records tool name + config path + run command. Downstream runs the tool directly.

### Generated Persistent Artifacts

| File | Phase | Purpose |
|------|-------|---------|
| `docs/rules/*.md` | 0-pre | Codebase conventions (brownfield; projected into `env-guide.md §4` by init) |
| `docs/plans/*-srs.md` | 0a | Approved SRS |
| `docs/plans/*-deferred.md` | 0a | Deferred requirements backlog |
| `docs/plans/*-ucd.md` | 0b | Approved UCD style guide (UI projects only) |
| `docs/plans/*-design.md` | 0c | Approved design (6 sections; no longer includes codebase constraints — those live in `env-guide.md §4`) |
| `docs/plans/*-ats.md` | 0d | Approved ATS (req→scenario mapping; reviewed by ats-reviewer) |
| `bugfix-request.json` | Hotfix | Signal file (deleted after processing) |
| `increment-request.json` | Increment | Signal file (deleted after processing) |
| `feature-list.json` | 1 | Task inventory with status, constraints, assumptions, waves |
| `long-task-guide.md` | 1 | Worker session guide (env activation, test/coverage commands) |
| `env-guide.md` | 1 | Service lifecycle commands (start/stop/restart/verify) |
| `task-progress.md` | 1 | `## Current State` + session log |
| `RELEASE_NOTES.md` | 1 | Keep a Changelog format |
| `init.sh` / `init.ps1` | 1 | Environment bootstrap |
| `.env.example` | 1 | Required env config template |
| `docs/features/YYYY-MM-DD-<name>.md` | 2 | Per-feature detailed design |
| `docs/test-cases/feature-*.md` | 2 | Per-feature ST test cases (ISO/IEC/IEEE 29119) |
| `docs/plans/*-st-plan.md` | 3 | ST plan with RTM |
| `docs/plans/*-st-report.md` | 3 | ST report with Go/No-Go verdict |
| `examples/` | Finalize | Scenario-based usage examples |
| `logs/session-*.md` | auto_loop | Session logs per iteration |
| `docs/explore/codebase-research.md` | Standalone | Deep codebase exploration report (from `/deep-explore`) |

### Feature List Schema

`feature-list.json` root:
```json
{
  "project": "name",
  "created": "2025-01-15",
  "tech_stack": { "language": "python|java|typescript|c|cpp", "test_framework": "...", "coverage_tool": "..." },
  "quality_gates": { "line_coverage_min": 90, "branch_coverage_min": 80 },
  "waves": [{ "id": 0, "date": "2025-01-15", "description": "Initial release" }],
  "constraints": ["Hard limit"],
  "assumptions": ["Implicit belief"],
  "required_configs": [{
    "name": "Display name", "type": "env|file", "key": "ENV_VAR (env type)", "path": "path/to/file (file type)",
    "description": "...", "required_by": [1, 3], "check_hint": "...",
    "connectivity_check": "curl -f http://... (optional)"
  }],
  "ats_template_path": "optional", "ats_review_template_path": "optional", "ats_example_path": "optional",
  "st_case_template_path": "optional", "st_case_example_path": "optional",
  "features": [...]
}
```

Each feature:
```json
{
  "id": 1, "wave": 0, "category": "core|bugfix",
  "title": "...", "description": "...", "priority": "high|medium|low", "status": "failing|passing",
  "srs_trace": ["FR-001"], "verification_steps": ["optional scenario"],
  "dependencies": [], "ui": false, "ui_entry": "/optional-path",
  "deprecated": false, "deprecated_reason": null, "supersedes": null,
  "st_case_path": "optional", "st_case_count": 8,
  "git_sha": "abc1234 (optional — set by Worker Step 11)",
  "bug_severity": "Critical|Major|Minor|Cosmetic (bugfix only)",
  "bug_source": "manual-testing (bugfix only)",
  "fixed_feature_id": null, "root_cause": "confirmed root cause (bugfix only)"
}
```

Key field notes:
- `srs_trace`: required; maps feature to SRS requirements for ATS lookup and ST traceability
- `git_sha`: 7–40 char hex; validated by `validate_features.py`
- `deprecated: true` → `deprecated_reason` required; excluded from Worker/ST/routing
- `waves[]`: increment batch tracking; `wave` on feature = which wave introduced/modified it

## File Structure

```
long-task-agent/
├── skills/
│   ├── using-long-task/SKILL.md + references/{architecture,roadmap}.md
│   ├── long-task-requirements/SKILL.md + references/{problem-framing,scenario-walkthrough,hypothesis-correction,approval-revise-loop}.md
│   ├── long-task-requirements-quality/SKILL.md
│   ├── long-task-requirements-alignment/SKILL.md + references/alignment-validation.md
│   ├── long-task-requirements-finalize/SKILL.md
│   ├── long-task-ucd/SKILL.md
│   ├── long-task-hotfix/SKILL.md
│   ├── long-task-increment/SKILL.md + references/{brownfield-adaptation,approval-revise-loop}.md
│   ├── long-task-increment-impact/SKILL.md
│   ├── long-task-increment-design/SKILL.md
│   ├── long-task-increment-ats/SKILL.md
│   ├── long-task-increment-ucd/SKILL.md
│   ├── long-task-increment-srs/SKILL.md
│   ├── long-task-design/SKILL.md
│   ├── long-task-ats/SKILL.md
│   ├── long-task-init/SKILL.md + scripts/init_project.py + references/approval-revise-loop.md
│   ├── long-task-init-env/SKILL.md
│   ├── long-task-init-bootstrap/SKILL.md + references/init-script-recipes.md
│   ├── long-task-init-features/SKILL.md
│   ├── long-task-feature-design/SKILL.md + references/feature-design-template.md
│   ├── long-task-work/SKILL.md + references/{systematic-debugging,subagent-development,worktree-isolation}.md
│   ├── long-task-feature-st/SKILL.md + prompts/e2e-scenario-prompt.md
│   ├── long-task-st/SKILL.md + references/st-recipes.md
│   ├── long-task-tdd/SKILL.md + testing-anti-patterns.md + references/ui-error-detection.md + prompts/implementer-prompt.md
│   ├── long-task-quality/SKILL.md + coverage-recipes.md
│   ├── long-task-finalize/SKILL.md
│   ├── long-task-explore/SKILL.md + references/exploration-dimensions.md (standalone)
├── agents/{codebase-scanner,ats-reviewer,example-generator,codebase-locator,codebase-analyzer,codebase-pattern-finder}.md
├── docs/templates/{srs,design,ats,ats-review,st-case,deferred-backlog,rules-index,explore-report}-template.md
├── hooks/{hooks.json,session-start,run-hook.cmd}
├── scripts/{get_tool_commands,validate_features,validate_guide,check_configs,check_devtools,
│           check_st_readiness,validate_ats,check_ats_coverage,check_real_tests,
│           validate_bugfix_request,validate_increment_request,validate_st_cases,
│           auto_loop,auto_loop_opencode}.py
└── tests/test_<script_name>.py  (one file per script)
```

## See Also

- [ReadMe.md](ReadMe.md) — Overview and design rationale
- [skills/using-long-task/references/architecture.md](skills/using-long-task/references/architecture.md) — TDD workflow, Chrome DevTools patterns
- [skills/using-long-task/references/roadmap.md](skills/using-long-task/references/roadmap.md) — Future enhancements
- [agents/codebase-scanner.md](agents/codebase-scanner.md) — Brownfield codebase scanner
- [agents/ats-reviewer.md](agents/ats-reviewer.md) — ATS reviewer (7 dimensions)
- [skills/long-task-work/references/systematic-debugging.md](skills/long-task-work/references/systematic-debugging.md) — Systematic debugging
- [skills/long-task-work/references/subagent-development.md](skills/long-task-work/references/subagent-development.md) — Subagent-driven development
- [skills/long-task-work/references/worktree-isolation.md](skills/long-task-work/references/worktree-isolation.md) — Worktree isolation
- [skills/long-task-tdd/references/ui-error-detection.md](skills/long-task-tdd/references/ui-error-detection.md) — UI error detection
- [skills/long-task-st/references/st-recipes.md](skills/long-task-st/references/st-recipes.md) — ST tool recipes per language
- [skills/long-task-explore/SKILL.md](skills/long-task-explore/SKILL.md) — Standalone deep codebase exploration
- [agents/codebase-locator.md](agents/codebase-locator.md) — Codebase structure locator (breadth-first)
- [agents/codebase-analyzer.md](agents/codebase-analyzer.md) — Architecture/data flow/domain analyzer (depth-first)
- [agents/codebase-pattern-finder.md](agents/codebase-pattern-finder.md) — Pattern/health/debt finder (metrics-driven)


<!-- long-task-agent -->
## Long-Task Agent

This project uses a multi-session agent workflow with 27 skills loaded on-demand (16 top-level + 5 increment sub-skills + 3 requirements sub-skills + 3 init sub-skills).
The `using-long-task` skill routes to the correct phase based on project state.
Flow: Codebase Scan (brownfield) → Requirements (SRS) → UCD (UI projects) → Design → ATS (Acceptance Test Strategy) → Init → Worker cycles → System Testing → Finalize.
Incremental development: place `increment-request.json` → Increment skill updates SRS/Design/ATS/UCD in place → new features appended → Worker cycles → ST.

Key files: `docs/rules/*.md` (codebase conventions — brownfield only; projected into env-guide.md §4), `docs/plans/*-srs.md` (SRS), `docs/plans/*-deferred.md` (deferred backlog), `docs/plans/*-ucd.md` (UCD style guide), `docs/plans/*-design.md` (design — 6 sections: architecture / feature integration specs / data model / internal API contracts / external interfaces / task decomposition), `docs/plans/*-ats.md` (ATS — acceptance test strategy with requirement→scenario mapping, reviewed by ats-reviewer subagent), `feature-list.json` (task inventory), `task-progress.md` (session log), `RELEASE_NOTES.md` (changelog), `docs/features/*.md` (per-feature detailed design), `docs/test-cases/feature-*.md` (per-feature ST test cases), `docs/plans/*-st-report.md` (ST report), `env-guide.md` (environment contract — §4 is the Worker/TDD/Feature-Design enforcement source for codebase constraints), `increment-request.json` (increment signal), `docs/explore/codebase-research.md` (standalone exploration report).
<!-- /long-task-agent -->
