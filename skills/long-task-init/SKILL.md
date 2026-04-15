---
name: long-task-init
description: "Use when design doc exists but feature-list.json not yet created - scaffold project artifacts and populate features from Design §9.2"
---

**LANGUAGE RULE**: You MUST respond to the user in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Skill names, code identifiers, and JSON field names remain in English.

# Initialize Long-Task Project

Run once after both SRS and design are approved. Scaffolds all persistent artifacts, populates features from Design §9.2 (FRs already right-sized at Requirements phase), and prepares the project for iterative Worker cycles.

**Announce at start:** "I'm using the long-task-init skill to scaffold the project."

## Input Documents

This skill reads from **two** approved documents:

| Document | Location | Provides |
|----------|----------|----------|
| **SRS** | `docs/plans/*-srs.md` | Functional requirements (FR-xxx), constraints (CON-xxx), assumptions (ASM-xxx), interface requirements (IFR-xxx), glossary, user personas, acceptance criteria |
| **Design** | `docs/plans/*-design.md` | Tech stack, architecture, data model, API design, testing strategy |

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

1. **Read the approved SRS and design documents** from `docs/plans/`
   - SRS: `docs/plans/*-srs.md` — for requirements, constraints, assumptions, glossary, personas
   - Design: `docs/plans/*-design.md` — for tech stack, architecture decisions
2. **Run `scripts/init_project.py`** to scaffold deterministic artifacts:
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` — from the SRS title
   - `<language>` — one of `python|java|typescript|c|cpp` from the design doc tech stack
   - Use `--line-cov`, `--branch-cov`, `--mutation-score` to override thresholds (defaults: 90/80/80)
   - Creates: `feature-list.json`, `CLAUDE.md` (appended), `task-progress.md`, `RELEASE_NOTES.md`, `examples/`, `docs/plans/`
   - Auto-copies helper scripts (`validate_features.py`, `validate_guide.py`, `get_tool_commands.py`, `validate_increment_request.py`, `validate_bugfix_request.py`) into project `scripts/`

3. **Verify `tech_stack` and `quality_gates`** in `feature-list.json`:
   - Confirm `language`, `test_framework`, `coverage_tool`, `mutation_tool` match the design doc
   - Adjust `quality_gates` thresholds if needed (defaults: line 90%, branch 80%, mutation 80%)
   - Verify tool commands resolve correctly:
     ```bash
     python scripts/get_tool_commands.py feature-list.json
     ```
4. **Generate `long-task-guide.md`** — Create a project-tailored Worker session guide:
   - Read these files for reference:
     - `skills/long-task-work/SKILL.md` — Worker workflow
     - `skills/long-task-quality/references/quality-execution.md` — verification enforcement
     - `skills/long-task-quality/coverage-recipes.md` — coverage/mutation tool setup
     - `skills/using-long-task/references/architecture.md` — Persistent artifact schemas
   - Include ONLY the project's language-specific coverage/mutation commands (get from `python scripts/get_tool_commands.py feature-list.json`)
   - **Must include all required sections**: Orient, TDD Red, TDD Green, Coverage Gate, TDD Refactor, Mutation Gate, Verification Enforcement, Inline Compliance Check, Persist, Critical Rules, Output Optimization
   - **Must include `Environment Commands` section** with:
     - Environment activation command (e.g., `source .venv/bin/activate`, `conda activate myenv`, `nvm use 20`)
     - Direct test execution command (e.g., `pytest --cov=src tests/`)
     - Direct mutation testing command (e.g., `mutmut run`)
     - Direct coverage report command
     - **Quiet recipes** (`[test-quiet]`, `[coverage-quiet]`, `[mutation-full-quiet]`) from `get_tool_commands.py` output — each has a `cmd` (the tool invocation) and an `instruction` (what to do with output: capture, extract, tail); the executing LLM composes the shell-appropriate command at runtime
     - These replace the now-removed test.sh/mutate.sh wrappers — Claude runs these directly
   - Validate:
     ```bash
     python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
     ```
5. **Populate SRS fields in `feature-list.json`** — from the **SRS document**:
   - `constraints[]` — copy CON-xxx items from SRS "Constraints" section; each a concise string
   - `assumptions[]` — copy ASM-xxx items from SRS "Assumptions & Dependencies" section; each a concise string
6. **Populate features from Design §9.2** — FRs are already right-sized at the Requirements phase (G1-G6 over-size + S1-S4 under-size heuristics). The design document's Task Decomposition table (§9.2) maps right-sized FRs to prioritized features with dependency ordering. Populate `feature-list.json` `features[]`:
   - Each §9.2 row → one feature. Do NOT further split or merge — granularity was finalized in the SRS phase.
   - `srs_trace`: copy the "Mapped FRs" column — the array of FR IDs this feature implements (e.g. `["FR-003", "FR-004", "FR-005"]`)
   - `title` + `description`: derive from the §9.2 Feature name + the mapped FRs' descriptions
   - `priority`: P0/P1 → `"high"`, P2 → `"medium"`, P3 → `"low"`
   - `dependencies`: from §9.3 Dependency Chain diagram
   - `status`: always `"failing"`
   - `verification_steps` is OPTIONAL — if provided, consolidate acceptance criteria from all mapped FRs into behavioral scenarios (Given/When/Then):
     - Each step MUST be a behavioral scenario with Given/When/Then structure, not a simple assertion
     - BAD: `"Login page displays correctly"` → no action, no assertion
     - GOOD: `"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - For features with backend dependencies: at least one step MUST verify real data flow across the dependency boundary
     - **Minimum complexity**: each feature SHOULD have ≥ 1 verification_step with 3+ chained actions
   - **Ordering**: follow §9.2 row order (already priority-sorted and paired backend/frontend by Design)
   - Each feature MUST be independently verifiable and completable in one session
   - **Validation gate**: after populating all features, verify:
     - Every FR-xxx from SRS appears in at least one feature's `srs_trace` (no orphaned requirements)
     - Every feature's `srs_trace` contains at least one FR (no empty traces)
   - **Single-round flag propagation**: If the SRS document metadata contains `Single-Round: Yes`, set `"single_round": true` at the root level of `feature-list.json`. This is an informational flag — all Worker steps (feature-design, TDD, quality gates, feature-ST) execute their full standard flow regardless of this flag.
7. **Validate**:
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
8. **Scaffold project skeleton** (dirs, configs, dependency manifests) — based on **design doc** architecture
9. **Update `task-progress.md`** — update `## Current State` with initial progress (0/N features passing), then append Session 0 entry (include SRS + design doc references)
10. **Begin first Worker cycle** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-work`

## Feature List Schema

Root structure:
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
    "mutation_score_min": 80
  },
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
  "features": [...]
}
```

Each feature:
```json
{
  "id": 1,
  "category": "core",
  "title": "Feature title",
  "description": "What it does",
  "priority": "high|medium|low",
  "status": "failing|passing",
  "srs_trace": ["FR-001", "FR-002"],
  "verification_steps": ["step 1", "step 2"],
  "dependencies": []
}
```

## Generated Persistent Artifacts

| File | Purpose |
|------|---------|
| `feature-list.json` | Structured task inventory with status |
| `CLAUDE.md` | Cross-session navigation index (appended) |
| `task-progress.md` | Session-by-session progress log |
| `RELEASE_NOTES.md` | Living release notes (Keep a Changelog format) |
| `examples/` | Runnable examples directory |
| `long-task-guide.md` | Worker session guide with env activation + direct test commands (LLM-generated, validated) |

## Integration

**Called by:** long-task-design (Step 6) or using-long-task (when design doc exists, no feature-list.json)
**Reads:** `docs/plans/*-srs.md` (requirements) + `docs/plans/*-design.md` (architecture)
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
