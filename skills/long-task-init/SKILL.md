---
name: long-task-init
description: "Use when ATS doc exists (or auto-skipped) but feature-list.json not yet created - scaffold project artifacts and decompose requirements into features"
---

# Initialize Long-Task Project

Run once after both SRS and design are approved. Scaffolds all persistent artifacts, decomposes requirements into verifiable features, and prepares the project for iterative Worker cycles.

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
   - Auto-copies helper scripts (`validate_features.py`, `check_configs.py`, `check_devtools.py`, `check_jinja2.py`, `check_real_tests.py`, `validate_guide.py`, `get_tool_commands.py`, `validate_st_cases.py`, `validate_increment_request.py`, `validate_bugfix_request.py`, `check_st_readiness.py`, `check_ats_coverage.py`, `check_mcp_providers.py`) into project `scripts/`
3b. **MCP Provider Setup** (SKIP if no enterprise MCP required):
   - Ask user: "Does this project use enterprise MCP servers for test/coverage/mutation/UI automation?"
   - If **YES**:
     1. Collect per capability: MCP server name, install command, tool names, result field paths
     2. Create `tool-bindings.json` at project root using `docs/templates/tool-bindings-template.json` as a guide
     3. Check Jinja2 availability (required for template rendering):
        ```bash
        python scripts/check_jinja2.py
        ```
        → Exit 1: present installation guide to user (`pip install jinja2`); wait for user to install; re-run check to confirm exit 0
        → Exit 0: continue
     4. Render skill templates:
        ```bash
        python scripts/apply_tool_bindings.py tool-bindings.json --output-dir .long-task-bindings
        ```
        → Verify: "N templates rendered to .long-task-bindings/"
     5. Check MCP server availability:
        ```bash
        python scripts/check_mcp_providers.py tool-bindings.json
        ```
        → Exit 1: present installation instructions to user (the script outputs exact `claude mcp add` commands); wait for user to install and restart session; re-run check to confirm exit 0
        → Exit 0: continue
   - If **NO**: skip (skills use plugin defaults — Chrome DevTools MCP for UI, CLI tools for testing)

3. **Verify `tech_stack` and `quality_gates`** in `feature-list.json`:
   - Confirm `language`, `test_framework`, `coverage_tool`, `mutation_tool` match the design doc
   - Adjust `quality_gates` thresholds if needed (defaults: line 90%, branch 80%, mutation 80%)
   - Verify tool commands resolve correctly:
     ```bash
     python scripts/get_tool_commands.py feature-list.json
     ```
   - Verify `real_test` config in feature-list.json:
     - `marker_pattern` matches the project's chosen real test identification method
     - `mock_patterns` covers the project's mock framework keywords
     - `test_dir` points to the correct test directory
4. **Generate `long-task-guide.md`** — Create a project-tailored Worker session guide:
   - Read these files for reference:
     - `skills/long-task-work/SKILL.md` — Worker workflow
     - `skills/long-task-quality/SKILL.md` — verification enforcement
     - `skills/long-task-quality/coverage-recipes.md` — coverage/mutation tool setup
     - `skills/using-long-task/references/architecture.md` — TDD workflow details
   - Include ONLY the project's language-specific coverage/mutation commands (get from `python scripts/get_tool_commands.py feature-list.json`)
   - Include UI testing section ONLY if the project has UI features (`"ui": true`):
     - If `tool-bindings.json` exists and `capability_bindings.ui_tools.tool_mapping` is present: use the enterprise tool names from `tool-bindings.json` throughout the guide (not Chrome DevTools MCP names)
     - Otherwise: use Chrome DevTools MCP tool names (`navigate_page`, `click`, etc.)
   - **Must include all required sections**: Orient, Bootstrap, Config Gate, TDD Red, TDD Green, Coverage Gate, TDD Refactor, Mutation Gate, Verification Enforcement, Inline Compliance Check, Persist, Critical Rules
   - **Must include `Environment Commands` section** with:
     - Environment activation command (e.g., `source .venv/bin/activate`, `conda activate myenv`, `nvm use 20`)
     - Direct test execution command (e.g., `pytest --cov=src tests/`)
     - Direct mutation testing command (e.g., `mutmut run`)
     - Direct coverage report command
     - These replace the now-removed test.sh/mutate.sh wrappers — Claude runs these directly
   - **Must include `Service Commands` section** (only if project has server processes): reference `env-guide.md` as the authoritative source for start/stop/restart commands; list health check URLs; include reminder about the Restart Protocol
   - **Must include `Config Management` section**: describe how to add/update a config value for this project (e.g., "append `KEY=value` to `.env`" for dotenv projects, "set `key=value` in `application.properties`" for Spring Boot projects, "export KEY=value" for system-env-only projects). This section is referenced by the Worker Config Gate when prompting users for missing values.
   - **Must include `Real Test Convention` section**: identification method (marker/folder/naming, adapted to project language), run command to execute only real tests, example real test for this project's tech stack
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
8. **Decompose requirements into features** — from the **SRS document** and **design document's Development Plan** (section 11), populate `feature-list.json` `features[]`:
   - Each FR-xxx → one or more features with `id`, `category`, `title`, `description`, `priority`, `status` (always `"failing"`), `srs_trace`, `dependencies`
   - Each feature MUST include `srs_trace`: an array of SRS requirement IDs (e.g. `["FR-001", "FR-002"]`) that this feature implements
   - `verification_steps` is OPTIONAL — if provided, should trace to SRS acceptance criteria (Given/When/Then)
   - For UI features: set `"ui": true`, optionally `"ui_entry": "/path"`; include `[devtools]`-prefixed verification steps if verification_steps are provided
   - **If verification_steps are provided** — quality rules (drives downstream ST case and TDD quality):
     - Each step MUST be a behavioral scenario with Given/When/Then structure, not a simple assertion
     - BAD: `"Login page displays correctly"` → no action, no assertion
     - GOOD: `"[devtools] Navigate /login → EXPECT: email input, password input, 'Sign In' button; fill valid creds → click Sign In → EXPECT: redirect to /dashboard, user name in header; REJECT: console errors, broken images"`
     - BAD: `"API returns 200 on valid input"` → this is an assertion, not a scenario
     - GOOD: `"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - For `"ui": true` features: every `[devtools]` step MUST describe a multi-step interaction chain (navigate → interact → verify → interact → verify)
     - For features with backend dependencies: at least one step MUST verify real data flow across the dependency boundary
     - **Minimum complexity**: each feature SHOULD have ≥ 1 verification_step with 3+ chained actions
   - **ATS category constraint** (if ATS document exists): for each feature, use srs_trace to look up ATS-required categories. If ANY srs_trace requirement has UI in its ATS categories, set `ui: true`.
   - **Backend-frontend pairing rule**: Frontend features (`"ui": true`) MUST list their backend API dependency features in `dependencies[]`. Additionally, features MUST be ordered in the `features[]` array using **paired grouping**: after each backend feature, place its corresponding frontend feature(s) immediately next in the array. This ensures the Worker develops Backend A → Frontend A → Backend B → Frontend B, rather than all backends then all frontends.
   - Aim for 10-200+ features; each independently verifiable and completable in one session
   - **Priority ordering**: follow the design document's Task Decomposition table (section 11.2) — P0/P1/P2/P3 maps to high/high/medium/low
   - **Dependency chain**: follow the design document's Dependency Chain diagram (section 11.3) to populate each feature's `dependencies[]`
   - **Milestone mapping**: group features by the design document's milestones for logical ordering
   - **Paired ordering within priorities**: Within each priority level, order features so that each backend feature is immediately followed by its frontend counterpart(s). Framework/infrastructure features (P0) come first without pairing. Example ordering:
     - P0: framework/infrastructure features (no pairing needed)
     - P1: [Backend Auth API, Frontend Auth Pages, Backend Orders API, Frontend Orders Pages, ...]
     - P2: [Backend Reports API, Frontend Reports Dashboard, ...]
     - The dependency mechanism ensures Frontend A cannot start until Backend A passes. The array ordering ensures Frontend A is the next candidate after Backend A.
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
13. **Git init + initial commit**
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
  "dependencies": [],
  "ui": false,
  "ui_entry": "/optional-path"
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

## Retrospective Authorization (Final Step)

After all artifacts are scaffolded and feature-list.json is created:

```bash
python scripts/check_retro_auth.py feature-list.json
```

- **Exit 0** (endpoint configured and reachable): Use `AskUserQuestion` to ask user:
  > "检测到 Skill 反馈 API 已配置（{endpoint}）。是否授权在本项目中搜集 Skill 改进建议并在项目结束后上报？搜集内容包括：用户反馈修正、技能缺陷分析。不包含项目代码或业务数据。"
  > Options: "授权 (Recommended)" / "不授权"
  - User authorizes → set `"retro_authorized": true` in `feature-list.json` root
  - User declines → set `"retro_authorized": false` in `feature-list.json` root
- **Exit 1 or 2** (unavailable or disabled): skip silently — do not ask user

## Integration

**Called by:** long-task-ats (Step 12) or using-long-task (when ATS doc exists, no feature-list.json)
**Reads:** `docs/plans/*-srs.md` (requirements) + `docs/plans/*-design.md` (architecture) + `docs/plans/*-ats.md` (test strategy constraints)
**Chains to:** long-task-work (after initialization complete)
**Produces:** feature-list.json + all scaffolded artifacts listed above
