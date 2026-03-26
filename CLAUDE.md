# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill plugin** called `long-task-agent` that enables multi-session execution of complex software projects exceeding a single context window. It implements a multi-phase architecture (Requirements → UCD → Design → ATS → Initializer → Worker → System Testing → Finalize, with an Increment re-entry point) with persistent state bridging via on-disk artifacts.

The skill system follows the **superpowers architectural pattern**: 13 independent skills loaded on-demand via the `Skill` tool, with a bootstrap router (`using-long-task`) injected at session start via hook.

## Key Commands

### Initialize a new long-task project
```bash
python long-task-agent/skills/long-task-init/scripts/init_project.py <project-name> --path <output-dir>

# With language preset (auto-fills test/coverage/mutation tools):
python long-task-agent/skills/long-task-init/scripts/init_project.py <project-name> --path <output-dir> --lang python

# With custom thresholds:
python long-task-agent/skills/long-task-init/scripts/init_project.py <project-name> --path <output-dir> --lang java \
  --line-cov 85 --branch-cov 75 --mutation-score 70
```

### Validate feature-list.json
```bash
python long-task-agent/scripts/validate_features.py feature-list.json
```

### Validate LLM-generated guide
```bash
python long-task-agent/scripts/validate_guide.py long-task-guide.md
python long-task-agent/scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
```

### Check required configurations
```bash
python long-task-agent/scripts/check_configs.py feature-list.json
python long-task-agent/scripts/check_configs.py feature-list.json --feature 3
```

### Check Chrome DevTools MCP availability (for UI features)
```bash
python long-task-agent/scripts/check_devtools.py feature-list.json
python long-task-agent/scripts/check_devtools.py feature-list.json --feature 3
```

### Check Jinja2 availability (for enterprise MCP template rendering)
```bash
python long-task-agent/scripts/check_jinja2.py
python long-task-agent/scripts/check_jinja2.py --quiet
```

### Check enterprise MCP provider availability
```bash
python long-task-agent/scripts/check_mcp_providers.py tool-bindings.json
python long-task-agent/scripts/check_mcp_providers.py tool-bindings.json --feature 3
```

### Render SKILL.md templates (Jinja2) with enterprise tool bindings
```bash
# Enterprise MCP mode (renders to .long-task-bindings/)
python long-task-agent/scripts/apply_tool_bindings.py tool-bindings.json

# Default Chrome DevTools mode (renders to .long-task-bindings/)
python long-task-agent/scripts/apply_tool_bindings.py --defaults

# Regenerate committed SKILL.md defaults from templates (developer workflow)
python long-task-agent/scripts/apply_tool_bindings.py --regenerate-defaults

# Dry run (shows what would be written)
python long-task-agent/scripts/apply_tool_bindings.py tool-bindings.json --dry-run
```

### Validate ATS document
```bash
python long-task-agent/scripts/validate_ats.py docs/plans/ats.md
python long-task-agent/scripts/validate_ats.py docs/plans/ats.md --srs docs/plans/srs.md
```

### Check ATS coverage against features and ST cases
```bash
python long-task-agent/scripts/check_ats_coverage.py docs/plans/ats.md --feature-list feature-list.json
python long-task-agent/scripts/check_ats_coverage.py docs/plans/ats.md --feature-list feature-list.json --feature 3
python long-task-agent/scripts/check_ats_coverage.py docs/plans/ats.md --feature-list feature-list.json --strict
```

### Check system testing readiness
```bash
python long-task-agent/scripts/check_st_readiness.py feature-list.json
```

### Validate ST test case document
```bash
python long-task-agent/scripts/validate_st_cases.py docs/test-cases/feature-1-user-login.md
python long-task-agent/scripts/validate_st_cases.py docs/test-cases/feature-1-user-login.md --feature-list feature-list.json --feature 1
```

### Validate increment request
```bash
python long-task-agent/scripts/validate_increment_request.py increment-request.json
```

### Validate bugfix request
```bash
python long-task-agent/scripts/validate_bugfix_request.py bugfix-request.json
```

### Get tech-stack CLI commands (eliminates per-language lookup)
```bash
python long-task-agent/scripts/get_tool_commands.py feature-list.json
python long-task-agent/scripts/get_tool_commands.py feature-list.json --json

# Enterprise MCP mode (outputs MCP tool specs instead of CLI commands)
python long-task-agent/scripts/get_tool_commands.py feature-list.json --bindings tool-bindings.json
python long-task-agent/scripts/get_tool_commands.py feature-list.json --bindings tool-bindings.json --json
```

### Check real test compliance
```bash
python long-task-agent/scripts/check_real_tests.py feature-list.json
python long-task-agent/scripts/check_real_tests.py feature-list.json --feature 3
python long-task-agent/scripts/check_real_tests.py feature-list.json --feature 3 --require-for-deps
python long-task-agent/scripts/check_real_tests.py feature-list.json --json
```

### Check retrospective authorization
```bash
python long-task-agent/scripts/check_retro_auth.py feature-list.json
```

### Validate retrospective record
```bash
python long-task-agent/scripts/validate_retrospective_record.py docs/retrospectives/record.md
```

### Check retrospective readiness
```bash
python long-task-agent/scripts/check_retrospective_readiness.py
```

### Post retrospective report
```bash
python long-task-agent/scripts/post_retrospective_report.py --feature-list feature-list.json
```

### Run tests
```bash
# Run all tests (from this repo's root)
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_validate_features.py
python -m pytest tests/test_init_project.py
python -m pytest tests/test_check_configs.py
python -m pytest tests/test_validate_guide.py
python -m pytest tests/test_check_devtools.py
python -m pytest tests/test_check_jinja2.py
python -m pytest tests/test_check_st_readiness.py
python -m pytest tests/test_get_tool_commands.py
python -m pytest tests/test_validate_bugfix_request.py
python -m pytest tests/test_validate_increment_request.py
python -m pytest tests/test_validate_st_cases.py
python -m pytest tests/test_check_real_tests.py
python -m pytest tests/test_validate_ats.py
python -m pytest tests/test_check_ats_coverage.py
python -m pytest tests/test_check_retro_auth.py
python -m pytest tests/test_validate_retrospective_record.py
python -m pytest tests/test_check_retrospective_readiness.py
```

### Auto-loop (multi-feature automation)
```bash
# Claude Code: auto-loop with fresh context per feature, logs saved automatically
python scripts/auto_loop.py feature-list.json
python scripts/auto_loop.py feature-list.json --max-iterations 30 --log-dir logs
python scripts/auto_loop.py feature-list.json --cooldown 10

# OpenCode: auto-loop with fresh context per feature
python scripts/auto_loop_opencode.py feature-list.json
python scripts/auto_loop_opencode.py feature-list.json --model anthropic/claude-sonnet-4-6
```

> **Path note**: the `python long-task-agent/skills/long-task-init/scripts/...` paths above are consumer-facing (run from the target project root after plugin install). When developing in this repo, replace `long-task-agent/` with `./` or omit it entirely.

## Architecture

### 13-Skill System

The skill system uses on-demand loading via the `Skill` tool. Only the bootstrap router is loaded at session start; other skills are loaded as needed.

#### Phase Skills (loaded one at a time based on project state)

| Skill | Phase | Trigger |
|-------|-------|---------|
| `using-long-task` | Bootstrap | Injected via SessionStart hook into every session |
| `long-task-hotfix` | Hotfix | bugfix-request.json exists (HIGHEST priority — above increment) |
| `long-task-increment` | Phase 1.5 | increment-request.json exists |
| `long-task-requirements` | Phase 0a | No SRS, no design doc, no feature-list.json |
| `long-task-ucd` | Phase 0b | SRS exists, no UCD doc, no design doc, no feature-list.json |
| `long-task-design` | Phase 0c | SRS + UCD exist (or no UI features), no design doc, no feature-list.json |
| `long-task-ats` | Phase 0d | Design doc exists, no ATS doc, no feature-list.json |
| `long-task-init` | Phase 1 | ATS doc exists (or auto-skipped for tiny projects), no feature-list.json |
| `long-task-work` | Phase 2 | feature-list.json exists, some active features failing |
| `long-task-st` | Phase 3 | feature-list.json exists, ALL active features passing |

#### Discipline Skills (loaded by long-task-work as sub-skills)

| Skill | Purpose |
|-------|---------|
| `long-task-feature-design` | Feature Detailed Design — interface contracts, algorithm pseudocode, state diagrams, boundary matrices, test inventory (bridges system design → TDD) |
| `long-task-tdd` | TDD Red-Green-Refactor |
| `long-task-quality` | Coverage Gate + Feature-Scoped Mutation Gate |
| `long-task-feature-st` | Black-Box Feature Acceptance Testing — self-managed environment lifecycle, Chrome DevTools MCP + ISO/IEC/IEEE 29119 (per-feature, after Quality Gates) |


#### Meta Skills (invoked conditionally by phase skills)

| Skill | Purpose |
|-------|---------|
| `long-task-finalize` | Post-ST Documentation — scenario-based usage examples generation + RELEASE_NOTES/task-progress finalization (after ST Go verdict) |
| `long-task-retrospective` | Skill Self-Evolution — consolidate retrospective records and upload to REST API (after ST Go verdict, if authorized) |

#### Skill Call Graph

```
using-long-task (router)
   ├─→ long-task-requirements ──→ long-task-ucd ──→ long-task-design ──→ long-task-ats ──→ long-task-init ──→ long-task-work
   │                              (auto-skip if no UI)                   (auto-skip ≤5 FR)                     │
   ├─→ long-task-hotfix (if bugfix-request.json exists — HIGHEST priority, above increment)
   │      └─→ validate → reproduce → root cause → enqueue as category=bugfix feature
   │          └─→ long-task-work (new failing bugfix feature detected)
   │
   ├─→ long-task-increment (if increment-request.json exists)
   │      └─→ updates SRS/Design/UCD in place, appends features to feature-list.json
   │          └─→ long-task-work (new failing features detected)
   │
   ├─→ long-task-work (if active features remain failing)
   │      ├─→ long-task-feature-design (Step 4, feature detailed design)
   │      ├─→ long-task-tdd (Steps 6-8)
   │      ├─→ long-task-quality (Step 9)
   │      └─→ long-task-feature-st (Step 10, black-box acceptance testing)
   │
   └─→ long-task-st (if ALL active features passing)
          ├─→ long-task-work (if defects found → fix → return to ST)
          └─→ long-task-finalize (after Go verdict → examples + doc finalization)
```

### Eight-Phase Workflow

0a. **Requirements** (`long-task-requirements`):
   - Structured elicitation aligned with ISO/IEC/IEEE 29148
   - Challenge each requirement against 8 quality attributes
   - Apply EARS templates, assign unique IDs, write Given/When/Then acceptance criteria
   - Anti-pattern detection (weasel words, compound requirements, design leakage)
   - Save SRS to `docs/plans/YYYY-MM-DD-<topic>-srs.md`
   - **Hard gate**: no UCD/design until SRS approved

0b. **UCD Style Guide** (`long-task-ucd`):
   - Takes approved SRS as input; auto-skips to design if no UI features
   - Define visual style direction (2-3 options), style tokens (colors, typography, spacing)
   - Generate text-to-image prompts per component type and per page
   - Save UCD to `docs/plans/YYYY-MM-DD-<topic>-ucd.md`
   - **Hard gate**: no design until UCD approved (for UI projects)
   - Referenced by design (UI/UX section), worker (frontend features), and review (UCD compliance)

0c. **Design** (`long-task-design`):
   - Takes approved SRS + UCD as input (WHAT + LOOK → HOW)
   - Propose 2-3 approaches with trade-offs, evaluate against SRS constraints/NFRs
   - Per-feature detailed design with Mermaid diagrams (class, sequence, flow)
   - Third-party dependency versions with compatibility verification
   - Development plan with milestones, task decomposition, priority ordering
   - Get section-by-section design approval
   - Save design doc to `docs/plans/YYYY-MM-DD-<topic>-design.md`
   - **Hard gate**: no coding until design approved

0d. **Acceptance Test Strategy** (`long-task-ats`):
   - Takes approved SRS + Design + UCD as input (WHAT + HOW + LOOK → TEST STRATEGY)
   - Maps every FR/NFR/IFR to acceptance scenarios with required test categories
   - Category assignment: FUNC+BNDRY (all FRs), +SEC (input/auth), +UI (ui:true), +PERF (NFR with metrics)
   - NFR test method matrix with tools, thresholds, and load parameters
   - Cross-feature integration scenarios pre-planned for ST phase
   - Risk-driven test priority ordering
   - Independent ATS reviewer subagent (7 dimensions: R1-R7) with custom review template support
   - Auto-skip for tiny projects (≤5 FR): embeds simplified mapping in design doc
   - Save ATS to `docs/plans/YYYY-MM-DD-<topic>-ats.md`
   - **Hard gate**: no Init until ATS approved (or auto-skipped)
   - Downstream: constrains Init `srs_trace` → ATS category lookup and feature-st test case derivation

**Hotfix** (`long-task-hotfix`):
   - Triggered by `bugfix-request.json` signal file (HIGHEST routing priority — above increment)
   - Validates signal file via `validate_bugfix_request.py`
   - Reproduces the bug; confirms root cause via 4-phase systematic debugging
   - Enqueues bug as `category: "bugfix"` feature in `feature-list.json` (status: "failing")
   - Deletes signal file; router auto-detects failing bugfix feature → Worker
   - Worker runs full TDD → Quality → ST → Inline Compliance pipeline for the fix
   - Worker uses `"fix:"` commit prefix and `### Fixed` RELEASE_NOTES entry for bugfix features

1.5. **Increment** (`long-task-increment`):
   - Triggered by `increment-request.json` signal file (high routing priority — below hotfix)
   - Collects new/modified/deprecated requirements with EARS templates
   - Impact analysis against existing features (user-approved)
   - Updates SRS, Design, UCD documents **in place** (git tracks history)
   - Appends new features to `feature-list.json` with `wave` metadata
   - Resets modified features to `"failing"`, marks deprecated features with `"deprecated": true`
   - Deletes signal file on completion; router auto-detects failing features → Worker

1. **Initializer Session** (`long-task-init`):
   - Reads both SRS and design documents
   - Runs `init_project.py` to scaffold deterministic artifacts
   - LLM generates project-tailored `long-task-guide.md`
   - Decomposes SRS requirements into 10-200+ verifiable features in `feature-list.json`
   - Creates project skeleton + initial git commit

2. **Worker Session** (`long-task-work` orchestrator):
   - Orient → Bootstrap → Config Gate → DevTools Gate → Plan
   - **TDD** (`long-task-tdd`): Red → Green → Refactor (driven by Feature Design Test Inventory + SRS)
   - **Quality** (`long-task-quality`): Coverage Gate → Feature-Scoped Mutation Gate
   - **ST Acceptance** (`long-task-feature-st`): Black-box acceptance testing — self-managed start/cleanup, Chrome DevTools MCP UI execution + ISO/IEC/IEEE 29119 per feature
   - **Inline Check**: Mechanical compliance verification (interface contracts, test inventory, dependency versions, UCD tokens)
   - Persist → Continue (chains to ST when all features pass)

3. **System Testing** (`long-task-st`):
   - Cross-feature & system-wide verification (per-feature ST already done in Worker cycles)
   - ST Readiness Gate → ST Plan (RTM) → Regression → Integration → Cross-Feature E2E → System-Wide NFR
   - Compatibility → Exploratory → Defect Triage → ST Report → Verdict (Go/No-Go) → Finalize
   - If Critical/Major defects found → loops back to Worker for fixes
   - Aligned with IEEE 829 and ISTQB best practices

   **Finalize** (`long-task-finalize`):
   - Invoked by ST after Go/Conditional-Go verdict
   - Generates scenario-based usage examples for external developers and AI Code Agents
   - Updates RELEASE_NOTES.md and task-progress.md with ST completion
   - Git commits all documentation artifacts

### Critical Rules

- **Config gate before planning**: Never plan or code when required configs are missing; load the project config first (per `long-task-guide.md` Config Management section), prompt user for missing values via text input, save to the appropriate config file
- **Requirements before UCD/design**: Run requirements elicitation; no UCD/design until SRS approved
- **UCD before design (UI projects)**: Run UCD style guide generation; no design until UCD approved (auto-skips for non-UI projects)
- **Design before ATS**: Run design phase; no ATS until design approved
- **ATS before implementation**: Run ATS phase; no coding until ATS approved (auto-skips for tiny projects ≤5 FR)
- **ATS constrains downstream**: Init `srs_trace` → ATS category lookup drives `ui` flag assignment; feature-st test case derivation must satisfy ATS category requirements
- **ATS reviewer is mandatory**: Independent subagent reviews ATS before approval; max 2 fix rounds then user escalation
- **Strict TDD**: Always Red→Green→Refactor→Coverage→Mutation
- **Coverage gate after TDD Green**: Run coverage tool, verify line >= 90%, branch >= 80%
- **Mutation gate after TDD Refactor**: For projects with > `mutation_full_threshold` active features, run feature-scoped mutation (changed files + feature's tests only); for smaller projects run full mutation. Verify score >= 80%. Full mutation runs during ST phase (Step 3b) for all projects.
- **Verification enforcement**: Never mark "passing" without fresh evidence
- **Inline compliance check after every feature**: mechanical interface contract, test inventory, dependency version, and UCD token verification (no SubAgent)
- **Systematic debugging**: Never guess-and-fix; always trace root cause first
- **One feature per session**: End session after completing one feature; multi-feature automation is handled by the external auto-loop script (`scripts/auto_loop.py`)
- **UI features require Chrome DevTools MCP testing**: Mark with `"ui": true`
- **System testing before release**: When all features pass, run ST phase (regression, integration, E2E, NFR, exploratory); no release without Go verdict
- **Hotfix before increment**: When both `bugfix-request.json` and `increment-request.json` exist, hotfix runs first; `increment-request.json` is preserved for next session
- **Bug fixes via hotfix skill only**: Never manually add bugfix features to feature-list.json; use the `long-task-hotfix` skill so root cause is confirmed and the fix is fully traceable
- **Incremental changes via increment skill only**: Never manually edit feature-list.json to add/modify/deprecate features; use the `long-task-increment` skill for audited, tracked changes
- **srs_trace required per feature**: Every feature must include `srs_trace` (array of SRS requirement IDs); `verification_steps` is optional
- **ST acceptance test cases after Quality Gates**: Generate and execute ISO/IEC/IEEE 29119 acceptance test cases per feature after TDD and Quality Gates; test cases validate implementation against requirements
- **Deprecated features excluded**: Worker skips deprecated features; ST readiness ignores them; routing counts only active features
- **Service lifecycle via env-guide.md**: All service start/stop/restart operations use the commands in `env-guide.md`. No implicit hook-based cleanup exists. Always follow the 4-step Restart Protocol between test cycles. Always capture the first 30 lines of startup output to extract PID/port.
- **Startup output in code**: Any code that starts a server or background service must print bound port, PID, and ready signal at startup — enables reliable extraction via `head -30` of the startup log.
- **Real tests mandatory for features with external dependencies**: Features with `required_configs[]` containing connection-string keys (URL, HOST, PORT, DSN, URI, CONNECTION, ENDPOINT) cannot claim pure-function exemption. `check_real_tests.py --require-for-deps` enforces this mechanically. If configs are missing, use AskUserQuestion — never skip real tests.

### Generated Persistent Artifacts

| File | Phase | Purpose |
|------|-------|---------|
| `docs/plans/*-srs.md` | Requirements | Approved SRS — the WHAT (ISO/IEC/IEEE 29148 aligned) |
| `docs/plans/*-deferred.md` | Requirements | Deferred requirements backlog — structured tracking for next-round pickup via increment skill |
| `docs/plans/*-ucd.md` | UCD | Approved UCD style guide — the LOOK (UI projects only; text-to-image prompts, style tokens) |
| `docs/plans/*-design.md` | Design | Approved design — the HOW |
| `docs/plans/*-ats.md` | ATS | Approved acceptance test strategy — the TEST PLAN (requirement→scenario mapping with category constraints, reviewed by ats-reviewer subagent) |
| `bugfix-request.json` | Hotfix | Signal file triggering hotfix session (deleted after processing) |
| `increment-request.json` | Increment | Signal file triggering incremental requirements (deleted after processing) |
| `docs/retrospectives/*.md` | Worker | Skill improvement records (collected during sessions, uploaded after ST) |
| `docs/retrospectives/reported/*.md` | Retrospective | Uploaded improvement records (audit trail) |
| `feature-list.json` | Init | Structured task inventory with status; includes `constraints[]`, `assumptions[]`, `waves[]` |
| `CLAUDE.md` | Init | Cross-session navigation index (appended by `init_project.py`) |
| `task-progress.md` | Init | `## Current State` header (updated by Worker each session) + session log |
| `RELEASE_NOTES.md` | Init | Living release notes (Keep a Changelog format) |
| `examples/` | Finalize | Scenario-based usage examples for external developers and AI Code Agents |
| `init.sh` / `init.ps1` | Init | Environment bootstrap (LLM-generated) |
| `env-guide.md` | Init | Service lifecycle commands — start/stop/restart/verify with output capture; user-editable |
| `long-task-guide.md` | Init | Worker session guide: includes env activation commands + direct test/coverage/mutation commands (LLM-generated, validated) |
| `.env.example` | Init | Template for required env configs (safe to commit; `.env` has secrets) |
| `docs/plans/*-st-plan.md` | ST | System testing plan with Requirements Traceability Matrix |
| `docs/plans/*-st-report.md` | ST | System testing report with Go/No-Go verdict |
| `docs/features/YYYY-MM-DD-<feature-name>.md` | Worker | Per-feature detailed design (interface contracts, test inventory, TDD tasks) |
| `docs/test-cases/feature-*.md` | Worker | Per-feature ST test case documents (ISO/IEC/IEEE 29119) |
| `docs/templates/srs-template.md` | — | Default SRS template (user-customizable) |
| `docs/templates/design-template.md` | — | Default design document template (user-customizable) |
| `docs/templates/ats-template.md` | — | Default ATS document template (user-customizable) |
| `docs/templates/ats-review-template.md` | — | Default ATS review spec template (7 dimensions, user-customizable) |
| `docs/templates/st-case-template.md` | — | Default ST test case template (ISO/IEC/IEEE 29119-3, user-customizable) |
| `docs/templates/deferred-backlog-template.md` | — | Default deferred requirements backlog template (user-customizable) |
| `logs/session-*.md` | auto_loop | Auto-captured session logs per iteration (one feature per file) |

### Feature List Schema

`feature-list.json` root structure:
```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "tech_stack": {
    "language": "python|java|typescript|c|cpp",
    "test_framework": "pytest|junit|vitest|gtest|...",
    "coverage_tool": "pytest-cov|jacoco|c8|gcov|...",
    "mutation_tool": "mutmut|pitest|stryker|mull|..."
  },
  "quality_gates": {
    "line_coverage_min": 90,
    "branch_coverage_min": 80,
    "mutation_score_min": 80,
    "mutation_full_threshold": 100
  },
  "waves": [
    {
      "id": 0,
      "date": "2025-01-15",
      "description": "Initial release"
    }
  ],
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
  "required_configs": [
    {
      "name": "Config display name",
      "type": "env|file",
      "key": "ENV_VAR_NAME (for env type)",
      "path": "path/to/file (for file type)",
      "description": "What this config is for",
      "required_by": [1, 3],
      "check_hint": "How to set it up",
      "connectivity_check": "curl -f http://localhost:5432/health (optional — LLM uses during Config Gate connectivity verification)"
    }
  ],
  "ats_template_path": "docs/templates/custom-ats-template.md (optional)",
  "ats_review_template_path": "docs/templates/custom-ats-review-template.md (optional)",
  "ats_example_path": "docs/templates/ats-example.md (optional)",
  "st_case_template_path": "docs/templates/custom-st-template.md (optional)",
  "st_case_example_path": "docs/templates/st-case-example.md (optional)",
  "retro_api_endpoint": "https://api.example.com/retro (optional — enables skill feedback collection)",
  "retro_authorized": false,
  "features": [...]
}
```

Each feature in `features` array:
```json
{
  "id": 1,
  "wave": 0,
  "category": "core",
  "title": "Feature title",
  "description": "What it does",
  "priority": "high|medium|low",
  "status": "failing|passing",
  "srs_trace": ["FR-001", "FR-002"],
  "verification_steps": ["step 1", "step 2"],
  "dependencies": [],
  "ui": false,
  "ui_entry": "/optional-path",
  "deprecated": false,
  "deprecated_reason": null,
  "supersedes": null,
  "st_case_path": "docs/test-cases/feature-1-user-login.md (optional)",
  "st_case_count": 8
}
```

Traceability fields:
- `srs_trace` (feature): Array of SRS requirement IDs (e.g. `["FR-001", "FR-002"]`) — required; maps feature to source requirements for ATS category lookup and ST traceability
- `verification_steps` (feature): Array of behavioral scenario strings — optional; if present, provides supplementary test context

ST test case fields (all optional, backward-compatible):
- `st_case_template_path` (root): Custom ST test case template path (defines structure)
- `st_case_example_path` (root): Example file path (defines style, language, detail level)
- `st_case_path` (feature): Path to generated ST test case document
- `st_case_count` (feature): Number of ST test cases generated for this feature

Bugfix-specific fields (all optional, only on `category: "bugfix"` features):
- `bug_severity` (feature): Severity of the bug — `"Critical"`, `"Major"`, `"Minor"`, or `"Cosmetic"`
- `bug_source` (feature): Where the bug was found — `"manual-testing"` (set by hotfix skill)
- `fixed_feature_id` (feature): ID of the feature this bug fix relates to (or `null` if unlinked)
- `root_cause` (feature): Confirmed one-sentence root cause (set by hotfix skill after systematic debugging)

Increment-specific fields:
- `waves[]` (root): Tracks each increment batch — `id` (0=initial), `date`, `description`
- `wave` (feature): Which wave introduced/last modified this feature (default 0)
- `deprecated` (feature): If `true`, excluded from Worker/ST/routing counts
- `deprecated_reason` (feature): Required when `deprecated=true`
- `supersedes` (feature): ID of the deprecated feature this one replaces (optional)

## File Structure

```
long-task-agent/
├── skills/                            # 13 skills (on-demand loaded via Skill tool)
│   ├── using-long-task/               # Bootstrap router (injected via hook)
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── architecture.md        # Detailed architecture patterns
│   │       └── roadmap.md             # Future enhancements
│   ├── long-task-requirements/SKILL.md # Phase 0a: Requirements & SRS (ISO 29148)
│   ├── long-task-ucd/SKILL.md         # Phase 0b: UCD style guide (text-to-image prompts)
│   ├── long-task-hotfix/               # Hotfix: user-reported bug triage, root-cause, enqueue → Worker
│   │   └── SKILL.md
│   ├── long-task-increment/SKILL.md    # Phase 1.5: Incremental requirements development
│   ├── long-task-design/SKILL.md      # Phase 0c: Design (takes SRS + UCD as input)
│   ├── long-task-ats/                 # Phase 0d: Acceptance Test Strategy (takes SRS + Design + UCD as input)
│   │   └── SKILL.md
│   ├── long-task-init/                # Phase 1: Initialization (reads SRS + UCD + design)
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── init_project.py        # Project scaffolding (run as `python scripts/init_project.py`)
│   │   └── references/
│   │       └── init-script-recipes.md # Environment bootstrap templates (conda, venv, nvm, etc.)
│   ├── long-task-feature-design/      # Feature Detailed Design discipline
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── feature-design-template.md # Feature detailed design template
│   ├── long-task-work/               # Phase 2: Worker orchestrator
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── systematic-debugging.md # Four-phase debugging process
│   │       ├── subagent-development.md # Subagent-driven development mode
│   │       └── worktree-isolation.md  # Git worktree isolation & branch finishing
│   ├── long-task-feature-st/          # Per-feature black-box acceptance testing (self-managed lifecycle, Chrome DevTools MCP + ISO/IEC/IEEE 29119)
│   │   ├── SKILL.md
│   │   └── prompts/
│   │       └── e2e-scenario-prompt.md # Chrome DevTools MCP E2E scenario derivation + page lifecycle protocol
│   ├── long-task-st/                  # Phase 3: System Testing (IEEE 829)
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── st-recipes.md          # Per-language ST tool recipes
│   ├── long-task-tdd/                 # TDD discipline
│   │   ├── SKILL.md
│   │   ├── testing-anti-patterns.md   # 14 anti-patterns catalog
│   │   ├── references/
│   │   │   └── ui-error-detection.md  # Three-layer UI error detection
│   │   └── prompts/
│   │       └── implementer-prompt.md
│   ├── long-task-quality/             # Quality gates
│   │   ├── SKILL.md
│   │   └── coverage-recipes.md        # Multi-language tool setup
│   ├── long-task-finalize/             # Post-ST documentation & examples (Meta Skill)
│   │   └── SKILL.md
│   └── long-task-retrospective/       # Skill self-evolution — collect & upload improvement records
│       ├── SKILL.md
│       └── prompts/
│           └── reflection-prompt.md
├── agents/
│   ├── ats-reviewer.md               # ATS reviewer agent definition (7 dimensions: R1-R7)
│   ├── example-generator.md          # Example generator agent definition (scenario-based usage examples)
│   └── reflection-analyst.md         # Reflection analyst agent definition (session retrospective)
├── docs/
│   └── templates/                     # Document templates (user-customizable)
│       ├── srs-template.md            # Default SRS template (ISO 29148)
│       ├── design-template.md         # Default design document template
│       ├── ats-template.md            # Default ATS document template (user-customizable)
│       ├── ats-review-template.md     # Default ATS review spec template (user-customizable, 7 dimensions)
│       ├── st-case-template.md        # Default ST test case template (ISO/IEC/IEEE 29119-3)
│       └── deferred-backlog-template.md # Default deferred requirements backlog template
├── hooks/
│   ├── hooks.json                     # Plugin-level hook config (SessionStart)
│   ├── session-start                  # Inject using-long-task + phase detection (bash)
│   ├── run-hook.cmd                   # Cross-platform polyglot wrapper for bash hooks
│   └── (port_guard.py, session_cleanup.py removed — service lifecycle managed via env-guide.md)
├── scripts/
│   ├── get_tool_commands.py           # Tech stack → CLI commands lookup
│   ├── validate_features.py           # Feature list validation
│   ├── validate_guide.py              # Guide structural validation
│   ├── check_configs.py               # Required config checking
│   ├── check_devtools.py              # Chrome DevTools MCP checking
│   ├── check_jinja2.py               # Jinja2 availability checking (enterprise MCP)
│   ├── check_st_readiness.py          # System testing readiness checking
│   ├── validate_ats.py               # ATS document structure validation
│   ├── check_ats_coverage.py         # ATS↔feature-list↔ST coverage checking
│   ├── check_real_tests.py            # Real test verification (existence + mock grep)
│   ├── validate_bugfix_request.py     # Bugfix request signal validation
│   ├── validate_increment_request.py  # Increment request signal validation
│   ├── validate_st_cases.py          # ST test case document validation
│   ├── check_retro_auth.py            # Retrospective feedback authorization check
│   ├── validate_retrospective_record.py # Retrospective record validation
│   ├── check_retrospective_readiness.py # Retrospective readiness check
│   ├── post_retrospective_report.py   # POST retrospective records to REST API
│   ├── auto_loop.py                  # Auto-loop for Claude Code (fresh context per feature, logs, AskUserQuestion detection)
│   └── auto_loop_opencode.py         # Auto-loop for OpenCode (fresh context per feature, logs, signal file detection)
├── tests/
│   ├── test_validate_features.py
│   ├── test_init_project.py
│   ├── test_get_tool_commands.py
│   ├── test_check_configs.py
│   ├── test_validate_guide.py
│   ├── test_check_devtools.py
│   ├── test_check_jinja2.py
│   ├── test_check_st_readiness.py
│   ├── test_check_real_tests.py
│   ├── test_validate_bugfix_request.py
│   ├── test_validate_increment_request.py
│   ├── test_validate_st_cases.py
│   ├── test_check_retro_auth.py
│   ├── test_validate_retrospective_record.py
│   └── test_check_retrospective_readiness.py
```

## See Also

- [ReadMe.md](ReadMe.md) - Overview and design rationale
- [skills/using-long-task/references/architecture.md](skills/using-long-task/references/architecture.md) - Detailed TDD workflow, Chrome DevTools testing patterns
- [skills/using-long-task/references/roadmap.md](skills/using-long-task/references/roadmap.md) - Future enhancements
- [skills/long-task-ats/SKILL.md](skills/long-task-ats/SKILL.md) - Acceptance Test Strategy skill
- [agents/ats-reviewer.md](agents/ats-reviewer.md) - ATS reviewer subagent (7 review dimensions)
- [agents/example-generator.md](agents/example-generator.md) - Example generator subagent (scenario-based usage examples)
- [skills/long-task-finalize/SKILL.md](skills/long-task-finalize/SKILL.md) - Post-ST documentation & examples skill
- [skills/long-task-feature-design/SKILL.md](skills/long-task-feature-design/SKILL.md) - Feature detailed design skill
- [skills/long-task-work/references/systematic-debugging.md](skills/long-task-work/references/systematic-debugging.md) - Systematic debugging
- [skills/long-task-work/references/subagent-development.md](skills/long-task-work/references/subagent-development.md) - Subagent-driven development
- [skills/long-task-work/references/worktree-isolation.md](skills/long-task-work/references/worktree-isolation.md) - Worktree isolation & branch finishing
- [skills/long-task-tdd/references/ui-error-detection.md](skills/long-task-tdd/references/ui-error-detection.md) - UI error detection specification
- [skills/long-task-st/references/st-recipes.md](skills/long-task-st/references/st-recipes.md) - System testing recipes per language


<!-- long-task-agent -->
## Long-Task Agent

This project uses a multi-session agent workflow with 13 skills loaded on-demand.
The `using-long-task` skill is injected at session start and routes to the correct phase.
Flow: Requirements (SRS) → UCD (UI projects) → Design → ATS (Acceptance Test Strategy) → Init → Worker cycles → System Testing → Finalize.
Incremental development: place `increment-request.json` → Increment skill updates SRS/Design/ATS/UCD in place → new features appended → Worker cycles → ST.

Key files: `docs/plans/*-srs.md` (SRS), `docs/plans/*-deferred.md` (deferred backlog), `docs/plans/*-ucd.md` (UCD style guide), `docs/plans/*-design.md` (design), `docs/plans/*-ats.md` (ATS — acceptance test strategy with requirement→scenario mapping, reviewed by ats-reviewer subagent), `feature-list.json` (task inventory), `task-progress.md` (session log), `RELEASE_NOTES.md` (changelog), `docs/features/*.md` (per-feature detailed design), `docs/test-cases/feature-*.md` (per-feature ST test cases), `docs/plans/*-st-report.md` (ST report), `increment-request.json` (increment signal).
<!-- /long-task-agent -->
