# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Claude Code skill plugin** (`long-task-agent`) enabling multi-session execution of complex software projects. Implements: Requirements → Design → ATS → Init → Worker → ST → Finalize, with Hotfix and Increment re-entry points. State bridges via on-disk artifacts. 13 skills loaded on-demand via the `Skill` tool; bootstrap router (`using-long-task`) routes to the correct phase based on project state. Standalone `/deep-explore` skill for on-demand codebase exploration. Independent `long-task-multi-repo` skill for multi-repo projects.

## Key Commands

> **Path note**: paths below are consumer-facing (`long-task-agent/...`). In this repo, replace `long-task-agent/` with `./` or omit.

| Purpose | Command |
|---------|---------|
| Init project | `python scripts/init_project.py <name> --path <dir> [--lang python\|java\|typescript] [--line-cov N] [--branch-cov N] [--mutation-score N]` |
| Validate feature-list | `python scripts/validate_features.py feature-list.json` |
| Validate guide | `python scripts/validate_guide.py long-task-guide.md` |
| Check configs | `python scripts/check_configs.py feature-list.json [--feature N]` |
| Validate ATS | `python scripts/validate_ats.py docs/plans/ats.md [--srs docs/plans/srs.md]` |
| Check ATS coverage | `python scripts/check_ats_coverage.py docs/plans/ats.md --feature-list feature-list.json [--feature N] [--strict]` |
| Check ST readiness | `python scripts/check_st_readiness.py feature-list.json` |
| Validate ST cases | `python scripts/validate_st_cases.py docs/test-cases/feature-N.md [--feature-list feature-list.json --feature N]` |
| Validate increment | `python scripts/validate_increment_request.py increment-request.json` |
| Validate bugfix | `python scripts/validate_bugfix_request.py bugfix-request.json` |
| Get tool commands | `python scripts/get_tool_commands.py feature-list.json [--json]` |
| Run all tests | `python -m pytest tests/` |
| Run single test | `python -m pytest tests/test_<script_name>.py` |
| Auto-loop (Claude Code) | `python scripts/auto_loop.py feature-list.json [--max-iterations 30] [--log-dir logs] [--cooldown 10]` |
| Auto-loop (OpenCode) | `python scripts/auto_loop_opencode.py feature-list.json [--model anthropic/claude-sonnet-4-6]` |
| Deep-explore codebase | Invoke `long-task:long-task-explore` or `/deep-explore [quick\|standard\|deep] [--focus area] [--path dir]` |

## Architecture

### 13-Skill System

#### Phase Skills

| Skill | Phase | Trigger |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Routes to correct phase; invoked by LLM at session start based on skill description |
| `long-task-multi-repo` | Multi-repo | `repos-manifest.json` exists — exploration, global SRS, split, dependency distribution |
| `long-task-hotfix` | Hotfix | `bugfix-request.json` exists (HIGHEST priority) |
| `long-task-increment` | Phase 1.5 | `increment-request.json` exists |
| `codebase-scanner` (SubAgent) | Phase 0-pre | No SRS/rules docs, >3 source files — brownfield scan |
| `long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json (single-repo only) |
| `long-task-design` | Phase 0b | SRS exists, no design doc, no feature-list.json |
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
| `long-task-feature-st` | Black-Box Feature Acceptance Testing (self-managed lifecycle, ISO/IEC/IEEE 29119) |

#### Skill Call Graph

```
using-long-task (router)
   ├─→ long-task-multi-repo (repos-manifest.json exists — exploration, global SRS, split, dep distribution, handoff)
   ├─→ codebase-scanner SubAgent (brownfield, no docs/rules/) ──→ long-task-requirements (rule 7b) OR long-task-design (rule 5b)
   ├─→ long-task-requirements ──→ long-task-design ──→ long-task-ats ──→ long-task-init ──→ long-task-work
   │                                                  (auto-skip: ≤5 FR)
   ├─→ long-task-hotfix (bugfix-request.json — HIGHEST priority)
   │      └─→ validate → reproduce → root cause → enqueue as category=bugfix → long-task-work
   ├─→ long-task-increment (increment-request.json)
   │      └─→ update SRS/Design → append features → long-task-work
   ├─→ long-task-work (active features failing)
   │      ├─→ long-task-feature-design (Step 4)
   │      ├─→ long-task-tdd (Steps 6-8)
   │      ├─→ Quality Gates SubAgent (Step 8, inline dispatch)
   │      └─→ long-task-feature-st (Step 9)
   └─→ long-task-st (ALL active features passing)
          ├─→ long-task-work (defects found → fix)
          └─→ Finalize (Go verdict — inline Step 13)

long-task-explore (standalone — no pipeline dependency)
   ├─→ codebase-locator SubAgent (breadth-first scan)
   ├─→ codebase-analyzer SubAgent (architecture, data flow, domain, API)
   └─→ codebase-pattern-finder SubAgent (dependencies, coupling, health, debt)
```

### Phase Workflow Summary

| Phase | Skill | Key Output |
|-------|-------|------------|
| 0-pre: Codebase Scan (brownfield) | `codebase-scanner` SubAgent | `docs/rules/*.md` — coding style, 2/3方件 constraints, build patterns, commit conventions |
| 0-multi: Multi-Repo | `long-task-multi-repo` | Global SRS + per-repo SRS split + dependency distribution; session ends with handoff |
| 0a: Requirements | `long-task-requirements` | `docs/plans/*-srs.md` (ISO/IEC/IEEE 29148; Lite 3-5 rounds / Expert 10-20 rounds) |
| 0b: Design | `long-task-design` | `docs/plans/*-design.md` (merges `docs/rules/` into §13 if brownfield) |
| 0d: ATS | `long-task-ats` | `docs/plans/*-ats.md` (req→scenario mapping; independent reviewer subagent; auto-skips ≤5 FR) |
| Hotfix | `long-task-hotfix` | Bugfix enqueued as `category=bugfix` feature; root cause confirmed |
| 1.5: Increment | `long-task-increment` | SRS/Design updated in place; new features appended with `wave` metadata |
| 1: Init | `long-task-init` | `feature-list.json`, `long-task-guide.md`, project skeleton, initial git commit |
| 2: Worker | `long-task-work` | TDD → Quality → Feature-ST → Inline Check per feature |
| 3: System Testing | `long-task-st` | ST plan/report; Go/No-Go verdict; chains to Finalize |

### Critical Rules

- **Gate order**: Config gate → Requirements (SRS) → Design → ATS → Init → TDD → Coverage → Mutation → Feature-ST → ST → Finalize. No skipping.
- **ATS reviewer mandatory**: Independent subagent reviews ATS before approval; max 2 fix rounds then user escalation.
- **ATS constrains downstream**: `srs_trace` → ATS category lookup; feature-st must satisfy ATS category requirements.
- **Strict TDD**: Always Red→Green→Refactor. Coverage: line ≥90%, branch ≥80%. Mutation: score ≥80% (feature-scoped if >`mutation_full_threshold` active features; full during ST).
- **Verification enforcement**: Never mark "passing" without fresh evidence.
- **Inline compliance after every feature**: interface contract, test inventory, dependency versions (no SubAgent).
- **Systematic debugging**: Never guess-and-fix; trace root cause first.
- **One feature per session**: Multi-feature automation via `scripts/auto_loop.py`.
- **System testing before release**: ST phase required (regression, integration, E2E, NFR, exploratory); no release without Go verdict.
- **Hotfix before increment**: When both signal files exist, hotfix runs first; `increment-request.json` preserved.
- **Bug fixes via hotfix skill only**: Never manually add bugfix features; root cause must be confirmed and traceable.
- **Incremental changes via increment skill only**: Never manually edit feature-list.json features; use increment skill.
- **srs_trace required per feature**: Every feature must include `srs_trace` (array of SRS requirement IDs).
- **ST acceptance test cases after Quality Gates**: ISO/IEC/IEEE 29119 test cases per feature; validate implementation against requirements.
- **Deprecated features excluded**: Worker skips; ST readiness ignores; routing counts only active features.
- **Service lifecycle via env-guide.md**: All start/stop/restart use `env-guide.md` commands. Follow 4-step Restart Protocol between test cycles. Capture first 30 lines of startup output for PID/port.
- **Startup output in code**: Servers must print bound port, PID, and ready signal at startup.
- **2/3方件 constraints binding**: Design §13.1 mandatory internal libraries and §13.2 prohibited APIs are binding for all new code.
- **Codebase scan before requirements or design (brownfield)**: >3 source files + ≥5 commits + no `docs/rules/` → run codebase-scanner first (rule 7b: before requirements; rule 5b: before design in brownfield repos).
- **Targeted explore in requirements/increment (brownfield)**: Requirements Step 1.6 and Increment Step 3.5 auto-trigger `long-task-explore` (quick/standard) when brownfield context + concrete focus direction exist. Non-blocking — failure never prevents proceeding.
- **Static analysis tools: detect, don't parse**: Scanner records tool name + config path + run command. Downstream runs the tool directly.
- **Commit convention compliance via LLM**: Worker Step 11 reads `commit_conventions` from `feature-list.json` (profile, prefix whitelist, subject length, branch naming, strip_trailers). No git hook — LLM is responsible for formatting commits correctly.
- **Multi-repo: fully handled by independent `long-task-multi-repo` skill**: Hook detects topology → router invokes skill → skill does exploration, global SRS, split, dependency distribution, handoff. User then independently cd's into each repo for single-repo pipeline.

### Multi-Repo Support

Projects with multiple git repositories under a non-git root directory are handled by the independent `long-task-multi-repo` skill:

1. **Hook detection**: `hooks/session-start` detects sub-directory git repos, generates `repos-manifest.json`
2. **Router invocation**: `using-long-task` detects manifest → invokes `long-task-multi-repo`
3. **Multi-repo skill**: Explores all repos, elicits global requirements, writes global SRS, splits into per-repo SRS with IFR contracts, distributes dependency files (reference docs, global SRS, deferred backlog, cross-repo deps) to each sub-repo
4. **Independent execution**: User cd's into each repo directory and runs the full single-repo pipeline (Design → ATS → Init → Worker → ST) independently

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
| `docs/rules/*.md` | 0-pre | Codebase conventions (brownfield; merged into Design §13) |
| `docs/plans/*-srs.md` | 0a / multi-repo | Approved SRS (single-repo: per-repo; multi-repo: global at root + per-repo in each sub-repo) |
| `<repo>/docs/plans/global-srs.md` | multi-repo | Copy of global SRS distributed to each sub-repo |
| `<repo>/docs/plans/cross-repo-deps.md` | multi-repo | Per-repo cross-repo interface dependency summary |
| `<repo>/docs/references/*` | multi-repo | User-provided reference docs copied from project root |
| `docs/plans/*-deferred.md` | 0a | Deferred requirements backlog |
| `docs/plans/*-design.md` | 0b | Approved design (includes §13 codebase constraints) |
| `docs/plans/*-ats.md` | 0d | Approved ATS (req→scenario mapping; reviewed by ats-reviewer) |
| `bugfix-request.json` | Hotfix | Signal file (deleted after processing) |
| `increment-request.json` | Increment | Signal file (deleted after processing) |
| ~~`.commit-conventions.json`~~ | ~~1~~ | Deprecated — replaced by `commit_conventions` field in `feature-list.json` |
| `feature-list.json` | 1 | Task inventory with status, constraints, assumptions, waves |
| `long-task-guide.md` | 1 | Worker session guide (env activation, test/coverage/mutation commands) |
| `env-guide.md` | 1 | Service lifecycle commands (start/stop/restart/verify) |
| `task-progress.md` | 1 | `## Current State` + session log |
| `RELEASE_NOTES.md` | 1 | Keep a Changelog format |
| `init.sh` / `init.ps1` | 1 | Environment bootstrap |
| `.env.example` | 1 | Required env config template |
| `docs/features/YYYY-MM-DD-<name>.md` | 2 | Per-feature detailed design |
| `docs/test-cases/feature-*.md` | 2 | Per-feature ST test cases (ISO/IEC/IEEE 29119) |
| `docs/report/feature-*-report.md` | 2 | Per-feature development report |
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
  "tech_stack": { "language": "python|java|typescript|c|cpp", "test_framework": "...", "coverage_tool": "...", "mutation_tool": "..." },
  "quality_gates": { "line_coverage_min": 90, "branch_coverage_min": 80, "mutation_score_min": 80, "mutation_full_threshold": 100 },
  "build_system": { "build_command": "make build (from Design §12.7, user-confirmed)" },
  "commit_conventions": {
    "profile": "conventional-commits|angular|ticket-prefixed|gitmoji|freeform|custom",
    "prefix_whitelist": ["feat", "fix", "chore", "..."],
    "subject_max_length": 72, "subject_min_length": 10, "custom_pattern": null,
    "branch_naming": "feature/<name>, fix/<name>",
    "strip_trailers": true
  },
  "waves": [{ "id": 0, "date": "2025-01-15", "description": "Initial release" }],
  "constraints": ["Hard limit"],
  "assumptions": ["Implicit belief"],
  "required_configs": [{
    "name": "Display name", "type": "env|file", "key": "ENV_VAR (env type)", "path": "path/to/file (file type)",
    "description": "...", "required_by": [1, 3], "check_hint": "..."
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
  "dependencies": [],
  "deprecated": false, "deprecated_reason": null, "supersedes": null,
  "st_case_path": "optional", "st_case_count": 8,
  "git_sha": "abc1234 (optional — set by Worker Step 11)",
  "report_path": "optional — set by Worker Step 11a",
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
- `build_system`: optional; populated from `docs/rules/build-and-compilation.md` → Design §12.7 during Init (user-confirmed)
- `commit_conventions`: optional; populated from `docs/rules/commit-conventions.md` → Design §12.8 during Init (user-confirmed); replaces `.commit-conventions.json`; `strip_trailers: true` prohibits Co-Authored-By/Signed-off-by trailers

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
│   ├── long-task-ats/SKILL.md
│   ├── long-task-init/SKILL.md + scripts/init_project.py + references/init-script-recipes.md
│   ├── long-task-feature-design/SKILL.md + references/feature-design-template.md
│   ├── long-task-work/SKILL.md + references/{systematic-debugging,subagent-development,worktree-isolation}.md
│   ├── long-task-feature-st/SKILL.md + prompts/e2e-scenario-prompt.md
│   ├── long-task-st/SKILL.md + references/st-recipes.md (includes Finalize Step 13)
│   ├── long-task-tdd/SKILL.md + testing-anti-patterns.md + prompts/implementer-prompt.md
│   ├── long-task-quality/{references/quality-execution.md,coverage-recipes.md}
│   ├── long-task-explore/SKILL.md + references/exploration-dimensions.md (standalone)
├── agents/{codebase-scanner,ats-reviewer,example-generator,codebase-locator,codebase-analyzer,codebase-pattern-finder}.md
├── docs/templates/{srs,design,ats,ats-review,st-case,deferred-backlog,feature-report,rules-index,explore-report}-template.md
├── hooks/{hooks.json,session-start,run-hook.cmd}
├── scripts/{get_tool_commands,validate_features,validate_guide,check_configs,
│           check_st_readiness,validate_ats,check_ats_coverage,
│           validate_bugfix_request,validate_increment_request,validate_st_cases,
│           auto_loop,auto_loop_opencode}.py
└── tests/test_<script_name>.py  (one file per script)
```

## See Also

- [ReadMe.md](ReadMe.md) — Overview and design rationale
- [skills/using-long-task/references/architecture.md](skills/using-long-task/references/architecture.md) — TDD workflow, testing patterns
- [agents/codebase-scanner.md](agents/codebase-scanner.md) — Brownfield codebase scanner
- [agents/ats-reviewer.md](agents/ats-reviewer.md) — ATS reviewer (7 dimensions)
- [skills/long-task-work/references/systematic-debugging.md](skills/long-task-work/references/systematic-debugging.md) — Systematic debugging
- [skills/long-task-work/references/subagent-development.md](skills/long-task-work/references/subagent-development.md) — Subagent-driven development
- [skills/long-task-work/references/worktree-isolation.md](skills/long-task-work/references/worktree-isolation.md) — Worktree isolation
- [skills/long-task-st/references/st-recipes.md](skills/long-task-st/references/st-recipes.md) — ST tool recipes per language
- [skills/long-task-multi-repo/SKILL.md](skills/long-task-multi-repo/SKILL.md) — Multi-repo requirements, SRS split, dependency distribution
- [skills/long-task-explore/SKILL.md](skills/long-task-explore/SKILL.md) — Standalone deep codebase exploration
- [agents/codebase-locator.md](agents/codebase-locator.md) — Codebase structure locator (breadth-first)
- [agents/codebase-analyzer.md](agents/codebase-analyzer.md) — Architecture/data flow/domain analyzer (depth-first)
- [agents/codebase-pattern-finder.md](agents/codebase-pattern-finder.md) — Pattern/health/debt finder (metrics-driven)


<!-- long-task-agent -->
## Long-Task Agent

This project uses a multi-session agent workflow with 13 skills loaded on-demand.
The `using-long-task` skill routes to the correct phase based on project state.
Flow: Codebase Scan (brownfield) → Requirements (SRS) → Design (merges rules into §13) → ATS (Acceptance Test Strategy) → Init → Worker cycles → System Testing → Finalize.
Incremental development: place `increment-request.json` → Increment skill updates SRS/Design/ATS in place → new features appended → Worker cycles → ST.

Key files: `repos-manifest.json` (multi-repo topology — generated by hook, absent in single-repo), `docs/rules/*.md` (codebase conventions — brownfield only), `docs/plans/*-srs.md` (SRS), `docs/plans/*-deferred.md` (deferred backlog), `docs/plans/*-design.md` (design, includes §13 codebase constraints), `docs/plans/*-ats.md` (ATS — acceptance test strategy with requirement→scenario mapping, reviewed by ats-reviewer subagent), `feature-list.json` (task inventory with `build_system` and `commit_conventions` from rules→Design→user confirmation), `task-progress.md` (session log), `RELEASE_NOTES.md` (changelog), `docs/features/*.md` (per-feature detailed design), `docs/test-cases/feature-*.md` (per-feature ST test cases), `docs/plans/*-st-report.md` (ST report), `docs/report/feature-*-report.md` (per-feature development reports), `increment-request.json` (increment signal), `docs/explore/codebase-research.md` (standalone exploration report).
Multi-repo support: session-start hook detects sub-directory git repos → `repos-manifest.json`. Independent `long-task-multi-repo` skill handles exploration, global SRS, per-repo split, and dependency distribution. User then independently cd's into each repo to run the single-repo pipeline.
<!-- /long-task-agent -->
