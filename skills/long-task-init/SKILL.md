---
name: long-task-init
description: "Use when ATS doc exists (or auto-skipped) but feature-list.json not yet created - scaffold project artifacts and populate features from Design §10.2"
---

**LANGUAGE RULE**: You MUST respond to the user in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Skill names, code identifiers, and JSON field names remain in English.

# Initialize Long-Task Project

Run once after both SRS and design are approved. Scaffolds all persistent artifacts, populates features from Design §10.2 (FRs already right-sized at Requirements phase), and prepares the project for iterative Worker cycles.

**Announce at start:** "I'm using the long-task-init skill to scaffold the project."

## Input Documents

This skill reads from **three** approved documents:

| Document | Location | Provides |
|----------|----------|----------|
| **SRS** | `docs/plans/*-srs.md` | Functional requirements (FR-xxx), NFRs (NFR-xxx), constraints (CON-xxx), assumptions (ASM-xxx), interface requirements (IFR-xxx), glossary, user personas, acceptance criteria |
| **Design** | `docs/plans/*-design.md` | Tech stack, architecture, data model, API design, testing strategy |
| **ATS** | `docs/plans/*-ats.md` | Requirement→scenario mapping, required test categories per requirement (constrains downstream feature-st via srs_trace lookup) |

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

1. **Read the approved SRS, design, and ATS documents** from `docs/plans/`
   - SRS: `docs/plans/*-srs.md` — for requirements, constraints, assumptions, NFRs, glossary, personas
   - Design: `docs/plans/*-design.md` — for tech stack, architecture decisions
   - ATS: `docs/plans/*-ats.md` — for requirement→category mapping (constrains `ui` flag and downstream feature-st category requirements via srs_trace)
2. **Run `scripts/init_project.py`** to scaffold deterministic artifacts:
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` — from the SRS title
   - `<language>` — one of `python|java|typescript|c|cpp` from the design doc tech stack
   - Use `--line-cov`, `--branch-cov`, `--mutation-score` to override thresholds (defaults: 90/80/80)
   - Creates: `feature-list.json`, `CLAUDE.md` (appended), `task-progress.md`, `RELEASE_NOTES.md`, `examples/`, `docs/plans/`
   - Auto-copies helper scripts (`validate_features.py`, `validate_guide.py`, `get_tool_commands.py`, `validate_st_cases.py`, `validate_increment_request.py`, `validate_bugfix_request.py`, `check_st_readiness.py`, `check_ats_coverage.py`) into project `scripts/`

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
     - `skills/using-long-task/references/architecture.md` — TDD workflow details
   - Include ONLY the project's language-specific coverage/mutation commands (get from `python scripts/get_tool_commands.py feature-list.json`)
   - **Must include all required sections**: Orient, Bootstrap, Config Gate, TDD Red, TDD Green, Coverage Gate, TDD Refactor, Mutation Gate, Verification Enforcement, Inline Compliance Check, Persist, Critical Rules
   - **Must include `Environment Commands` section** with:
     - Environment activation command (e.g., `source .venv/bin/activate`, `conda activate myenv`, `nvm use 20`)
     - Direct test execution command (e.g., `pytest --cov=src tests/`)
     - Direct mutation testing command (e.g., `mutmut run`)
     - Direct coverage report command
     - These replace the now-removed test.sh/mutate.sh wrappers — Claude runs these directly
   - **Must include `Service Commands` section** (only if project has server processes): reference `env-guide.md` as the authoritative source for start/stop/restart commands; list health check URLs; include reminder about the Restart Protocol
   - **Must include `Config Management` section**: describe how to add/update a config value for this project (e.g., "append `KEY=value` to `.env`" for dotenv projects, "set `key=value` in `application.properties`" for Spring Boot projects, "export KEY=value" for system-env-only projects). This section is referenced by the Worker Config Gate when prompting users for missing values.
   - Validate:
     ```bash
     python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
     ```
5. **Generate `env-guide.md`** — Create an explicit service lifecycle guide at the project root (user-editable):

   - Read the design doc for service port declarations, health check URLs, and service names (API design / architecture sections)
   - Read `.env.example` for `*_PORT=` variables
   - Generate `env-guide.md` with the following sections:

   **Header note** (top of file):
   > User-editable. Claude reads this file before managing services. Update when ports change or new services are added.

   **Services table**:
   | Service Name | Port | Start Command | Stop Command | Verify URL |
   |---|---|---|---|---|
   | (one row per service) | | | | |

   **Start All Services** — for each service:
   ```bash
   # Unix/macOS
   [start command] > /tmp/svc-<slug>-start.log 2>&1 &
   sleep 3
   head -30 /tmp/svc-<slug>-start.log
   # → Extract PID and port from output; record both in task-progress.md

   # Windows alternative
   cmd /c "start /b [command] > %TEMP%\svc-<slug>-start.log 2>&1"
   timeout /t 3 /nobreak >nul
   powershell "Get-Content $env:TEMP\svc-<slug>-start.log -TotalCount 30"
   ```

   **Verify Services Running** — for each service:
   ```bash
   curl -f http://localhost:<port>/health   # or appropriate health endpoint
   ```

   **Stop All Services** — kill by PID (primary) or port (fallback):
   ```bash
   # By PID (preferred — use PID recorded in task-progress.md)
   kill <PID>                              # Unix/macOS
   taskkill /F /PID <PID>                  # Windows

   # By port (fallback)
   lsof -ti :<port> | xargs kill -9        # Unix/macOS
   for /f "tokens=5" %a in ('netstat -ano ^| findstr :<port>') do taskkill /F /PID %a  # Windows
   ```

   **Verify Services Stopped** — ports must show no output:
   ```bash
   lsof -i :<port>                         # Unix/macOS — expect no output
   netstat -ano | findstr :<port>           # Windows — expect no output
   ```

   **Restart Protocol (4 steps)**:
   1. **Kill** — Stop All Services (by PID from task-progress.md, or by port)
   2. **Verify dead** — run Verify Services Stopped; poll port max 5 seconds — must not respond
   3. **Start** — run Start All Services with output capture → `head -30` → extract new PID/port → update task-progress.md
   4. **Verify alive** — run Verify Services Running; poll health endpoint max 10 seconds — must respond

   - **Complex startup sequences**: if a service requires >2 shell commands to start (e.g., DB migration + seed + server), generate `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-start.ps1` containing the full sequence; update env-guide.md "Start All Services" to call `bash scripts/svc-<slug>-start.sh` instead of inline commands; same for stop sequences (`scripts/svc-<slug>-stop.sh`). This keeps env-guide.md readable while versioning the logic in scripts/
   - If the project is CLI-only or library-only (no server processes): generate a minimal `env-guide.md` with a header note "No server processes — environment activation only" and only the activation command from `long-task-guide.md`

6. **Generate `init.sh` / `init.ps1`** — Create real, runnable bootstrap scripts:
   - Read `references/init-script-recipes.md` (in the long-task-init skill directory) for per-tool templates and best practices
   - **Detect environment manager** from design doc tech stack and project constraints:
     - Python: miniconda/conda/mamba, venv, poetry, pipenv, uv, pyenv
     - Node.js: nvm, fnm, volta, corepack
     - Java: sdkman, jenv
     - General: devcontainer, docker, nix
   - **Must handle**: env creation, activation, dependency install, tool version verification
   - **Must be idempotent** — safe to re-run without breaking an existing environment
   - **Must be cross-platform** — `init.sh` for Unix/macOS, `init.ps1` for Windows
   - **Must include**: error handling, version checks, clear success/failure output
   - Actual dependency installation commands (not commented stubs)
   - Must be immediately executable after `git clone`
   - **Note**: psutil is not required — service lifecycle is managed via `env-guide.md` commands, not hooks
7. **Populate SRS fields in `feature-list.json`** — from the **SRS document**:
   - `constraints[]` — copy CON-xxx items from SRS "Constraints" section; each a concise string
   - `assumptions[]` — copy ASM-xxx items from SRS "Assumptions & Dependencies" section; each a concise string
   - NFR-xxx rows → create `category: "non-functional"` features with `srs_trace` (e.g. `["NFR-001"]`) and optionally measurable `verification_steps`; coverage/mutation gates do not apply to NFR features
8. **Populate features from Design §10.2** — FRs are already right-sized at the Requirements phase (G1-G6 over-size + S1-S4 under-size heuristics). The design document's Task Decomposition table (§10.2) maps right-sized FRs to prioritized features with dependency ordering. Populate `feature-list.json` `features[]`:
   - Each §10.2 row → one feature. Do NOT further split or merge — granularity was finalized in the SRS phase.
   - `srs_trace`: copy the "Mapped FRs" column — the array of FR IDs this feature implements (e.g. `["FR-003", "FR-004", "FR-005"]`)
   - `title` + `description`: derive from the §10.2 Feature name + the mapped FRs' descriptions
   - `priority`: P0/P1 → `"high"`, P2 → `"medium"`, P3 → `"low"`
   - `dependencies`: from §10.3 Dependency Chain diagram
   - `status`: always `"failing"`
   - `verification_steps` is OPTIONAL — if provided, consolidate acceptance criteria from all mapped FRs into behavioral scenarios (Given/When/Then):
     - Each step MUST be a behavioral scenario with Given/When/Then structure, not a simple assertion
     - BAD: `"Login page displays correctly"` → no action, no assertion
     - GOOD: `"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - For features with backend dependencies: at least one step MUST verify real data flow across the dependency boundary
     - **Minimum complexity**: each feature SHOULD have ≥ 1 verification_step with 3+ chained actions
   - **Ordering**: follow §10.2 row order (already priority-sorted and paired backend/frontend by Design)
   - Each feature MUST be independently verifiable and completable in one session
   - **Validation gate**: after populating all features, verify:
     - Every FR-xxx from SRS appears in at least one feature's `srs_trace` (no orphaned requirements)
     - Every feature's `srs_trace` contains at least one FR (no empty traces)
9. **Populate `required_configs`** — from the **SRS document** (IFR-xxx interface requirements) and design doc:
   - API keys, service URLs → type `env`
   - Config files, certificates → type `file`
   - Link each to features via `required_by`; provide `check_hint` with setup instructions
9b. **Generate `scripts/check_configs.py`** — project-specific config checker (LLM-generated, not copied from plugin):
    - Analyze the project's config format based on `tech_stack.language` and the design doc:
      - Python + `.env` pattern → use `load_dotenv`-style KEY=VALUE parsing
      - Java/Spring → parse `src/main/resources/application.properties` or `application.yml`
      - Node.js → read `.env` or `config/` directory
      - Go / Rust → read TOML / YAML config files, or rely on system environment
      - Any project that relies solely on system environment variables → no file loading needed
    - Generate a script with this **standardized interface**:
      - Usage: `python scripts/check_configs.py feature-list.json [--feature <id>]`
      - Reads `required_configs[]` from `feature-list.json`
      - Loads config values using the project-native format (hardcoded for this project)
      - Checks each `env`-type config via `os.environ`, each `file`-type config via `os.path.exists`
      - Prints each missing config with its `name` and `check_hint`
      - Exit 0 = all required configs present; Exit 1 = one or more missing
    - **No `--dotenv` or format flag needed** — the loading logic is built in for this project
    - The plugin's `scripts/check_configs.py` is available as a reference template if useful
10. **Generate `.env.example`** — from `required_configs`:
    - For each `env`-type config, write a commented template line:
      ```
      # <name> — <description>
      # Hint: <check_hint>
      # Required by features: <required_by ids>
      <KEY>=
      ```
    - Add secrets config files to `.gitignore` (e.g., `.env`); `.env.example` is safe to commit
    - This template lists the required env vars; users load them via whichever config format the project uses; the Worker Config Gate will prompt for missing values
11. **Validate**:
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
12. **Scaffold project skeleton** (dirs, configs, dependency manifests) — based on **design doc** architecture
13. **Git init + build/commit conventions + initial commit**
    > **Existing repo**: If the current directory already contains a `.git/` directory, **skip `git init`** — only stage and commit the newly scaffolded files. If the directory is not a git repo, run `git init` first.
    
    a. **Populate `feature-list.json` `build_system` field** (from rules → Design):
       - Read `docs/rules/build-and-compilation.md` (if exists) → extract build tool and key commands
       - Read Design doc §13.7 (Build & CI/CD Summary) → extract Build System value
       - Map to `build_system.build_command`
    b. **Populate `feature-list.json` `commit_conventions` field** (from rules → Design):
       - Read `docs/rules/commit-conventions.md` (if exists, brownfield) → extract commit format, subject length, branch pattern
       - Read Design doc §13.8 (Commit Conventions) → extract Format, Subject Length, Branch Naming
       - Map to `commit_conventions` sub-fields: `profile`, `prefix_whitelist`, `subject_max_length`, `subject_min_length`, `branch_naming`
       - Convention mapping: "Conventional Commits" → profile `conventional-commits`; "Angular" → `angular`; ticket prefix (e.g., `JIRA-xxx:`) → `ticket-prefixed` + `custom_pattern`; gitmoji → `gitmoji`; no convention → `freeform`
       - If greenfield with no specific convention, default to `conventional-commits`
       - Default `strip_trailers: true` (禁止 Co-Authored-By, Signed-off-by 等尾缀签名)
    c. **Present extracted values to user for confirmation** (AskUserQuestion):
       - Show the auto-extracted `build_system` and `commit_conventions` values
       - User confirms or modifies before writing to `feature-list.json`
    d. Commit the updated `feature-list.json` in the initial commit
14. **Run init script and verify environment**:
    - Run `init.sh` (or `init.ps1`), verify environment setup completes without errors
    - Verify test execution works: activate env → run test command from `long-task-guide.md` → confirm tests execute (may all fail at this point — that's expected)
    - Verify mutation testing command is available: activate env → run mutation tool version check
    - If any check fails: diagnose root cause, fix the script or configuration, re-run
    - Do NOT start services here — services are started during ST testing using the commands defined in `env-guide.md`
15. **Update `task-progress.md`** — update `## Current State` with initial progress (0/N features passing), then append Session 0 entry (include SRS + design doc references)
16. **Begin first Worker cycle** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-work`

## Service Config Maintenance (Worker cycles)

When a Worker cycle introduces a new backend service, changes a service port, or discovers that the actual start/stop command differs from env-guide.md, update `env-guide.md`:
- Add/update the Services table row (service name, port, start/stop/verify commands)
- Add/update corresponding Start, Verify, Stop, and Restart commands
- If the startup or stop sequence requires >2 shell steps: extract to `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-stop.sh` and update env-guide.md to reference the script
- Include env-guide.md and any `scripts/svc-*` changes in the same git commit as the feature

**env-guide.md must always reflect commands that actually work.** Any time a command is proven correct (during TDD Green or after fixing a failure), env-guide.md must be updated to match.

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
  "required_configs": [
    {
      "name": "Display name",
      "type": "env|file",
      "key": "ENV_VAR (for env type)",
      "path": "path/to/file (for file type)",
      "description": "What this config is for",
      "required_by": [1, 3],
      "check_hint": "How to set it up"
    }
  ],
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
| `init.sh` / `init.ps1` | Environment bootstrap (LLM-generated) |
| `env-guide.md` | Service lifecycle commands — start/stop/restart/verify with output capture; user-editable |
| `long-task-guide.md` | Worker session guide with env activation + direct test commands (LLM-generated, validated) |
| `.env.example` | Template for required env configs (safe to commit) |

## Integration

**Called by:** long-task-ats (Step 12) or using-long-task (when ATS doc exists, no feature-list.json)
**Reads:** `docs/plans/*-srs.md` (requirements) + `docs/plans/*-design.md` (architecture) + `docs/plans/*-ats.md` (test strategy constraints)
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
