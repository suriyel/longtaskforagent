---
name: long-task-increment
description: "Use when increment-request.json exists - collect incremental requirements, perform impact analysis, update design, and decompose new features"
---

# Incremental Requirements Development

Add new requirements, modify existing ones, or deprecate features in a live project. All changes are written back into the existing SRS/Design/UCD documents (tracked via git history), and new features are appended to `feature-list.json` with wave metadata.

**Announce at start:** "I'm using the long-task-increment skill. Let me orient on the current project state before collecting new requirements."

## Prerequisites

- `feature-list.json` exists (project has been initialized)
- `increment-request.json` exists in project root (signal file created by user)

## Checklist

You MUST create a TodoWrite task for each step and complete them in order:

### 1. Orient

- Read `increment-request.json` — understand the reason and scope of this increment
- Read `feature-list.json` — note all features, their statuses, wave history, constraints, assumptions
- Read approved SRS (`docs/plans/*-srs.md`) — current requirements baseline
- Read approved design (`docs/plans/*-design.md`) — current architecture
- If exists: read ATS document (`docs/plans/*-ats.md`) — current test strategy baseline
- If UI project: read UCD style guide (`docs/plans/*-ucd.md`)
- If exists: read deferred backlog (`docs/plans/*-deferred.md`) — pre-elicited requirements available for pickup (skip re-elicitation for items with complete EARS + acceptance criteria)
- Read `task-progress.md` — session history
- Run `git log --oneline -10` — recent context
- Determine current wave number: `max(wave for all features) + 1` (default to 1 if no wave fields exist)

### 2. Incremental Requirements Elicitation

Collect new/changed requirements using structured elicitation (same rigor as Phase 0a):

1. Use `AskUserQuestion` to collect requirements in rounds (2-4 related questions per round)
2. For each requirement, apply the EARS template:
   - **Ubiquitous**: The system shall...
   - **Event-driven**: When \<trigger\>, the system shall...
   - **State-driven**: While \<state\>, the system shall...
   - **Unwanted behavior**: If \<condition\>, then the system shall...
   - **Optional**: Where \<feature\>, the system shall...
3. Assign unique IDs continuing from the existing SRS (e.g., if last FR is FR-020, new ones start at FR-021)
4. Write Given/When/Then acceptance criteria for each
5. Validate against 8 quality attributes: Correct, Unambiguous, Complete, Consistent, Ranked, Verifiable, Modifiable, Traceable
6. Classify changes into three buckets:
   - **New**: entirely new FR/NFR requirements
   - **Modified**: changes to existing FR/NFR (note the original ID being modified)
   - **Deprecated**: existing requirements no longer needed (note the ID being removed)

**Output**: A structured list of new/modified/deprecated requirements with IDs, EARS statements, and acceptance criteria.

### 3. Impact Analysis

Compare new requirements against the existing feature set:

1. For each **new** requirement → identify which existing features (if any) it depends on
2. For each **modified** requirement → identify which existing features have `srs_trace` referencing the original requirement ID; these features will need re-verification
3. For each **deprecated** requirement → identify which features implement it; these will be marked deprecated
4. Check for dependency chain impacts — if a modified feature is depended upon by others, those may need re-verification too

**Output**: Impact matrix presented to user for approval:

```
| Change | Type | Affected Features | Action |
|--------|------|-------------------|--------|
| FR-021 | New | (none) | Add feature(s) |
| FR-005 (modified) | Modified | Feature 5, Feature 8 | Reset to failing, update srs_trace |
| FR-012 (deprecated) | Deprecated | Feature 12 | Mark deprecated |
```

**Hard gate**: User must approve the impact matrix before proceeding.

### 4. Design Revision

Update the existing design document **in place** for affected sections:

1. Read `docs/plans/*-design.md`
2. For **new** requirements:
   - Add Key Feature Design subsection (section 4.N+1) with class diagram, sequence diagram, flow diagram
   - Update Dependency Chain (section 11.3) if new features have dependencies
   - Update Task Decomposition (section 11.2) with new priorities
   - Add any new third-party dependencies to the dependency table
3. For **modified** requirements:
   - Update the corresponding Key Feature Design section (4.N) in place
   - Update sequence/flow diagrams as needed
4. For **deprecated** requirements:
   - Add `[DEPRECATED - Wave N]` marker to the corresponding design section
   - Do NOT delete the section (preserve history context)
5. Get user approval section-by-section
6. Git commit the design update with descriptive message:
   ```
   docs: update design for wave N — <brief scope>

   New: FR-021 (feature title), FR-022 (feature title)
   Modified: FR-005 (what changed)
   Deprecated: FR-012 (reason)
   ```

### 4b. ATS Revision

**Skip this step** if no ATS document exists (`docs/plans/*-ats.md`).

Update the existing ATS document **in place** for affected requirements:

1. Read `docs/plans/*-ats.md`
2. For **new** requirements:
   - Add mapping table rows with requirement ID, scenarios, required categories
   - Apply category assignment rules (FUNC+BNDRY for all FRs; +SEC for input/auth; +UI for ui:true; +PERF for NFRs with metrics)
   - Update the coverage statistics table (Section 2.4)
   - If new NFRs: add rows to the NFR Test Method Matrix (Section 4)
   - If new cross-feature interactions: add rows to Integration Scenarios (Section 5)
3. For **modified** requirements:
   - Update the corresponding mapping table row in place (scenarios, categories)
   - Adjust NFR test methods if thresholds changed
   - Update integration scenarios if data flows changed
4. For **deprecated** requirements:
   - Add `[DEPRECATED - Wave N]` marker to the corresponding mapping table row
   - Do NOT delete the row (preserve traceability)
   - Update coverage statistics (exclude deprecated rows from totals)
5. Update the Risk-Driven Test Priority section if risk profile changed
6. Get user approval for ATS changes
7. Git commit:
   ```
   docs: update ATS for wave N — <brief scope>

   New: <req_ids added>
   Modified: <req_ids changed>
   Deprecated: <req_ids deprecated>
   ```
8. **ATS re-review check**: if ATS changes affect >3 mapping table rows OR introduce a new test category not previously present, ask the user whether a re-review is needed before proceeding. If yes, describe the changes and rationale for the user to approve.

### 5. UCD Revision (UI projects only)

**Skip this step** if the project has no UI features AND none of the new requirements involve UI.

1. Read `docs/plans/*-ucd.md`
2. For new UI requirements:
   - Add component prompts for new UI components
   - Add page prompts for new pages
   - Update style tokens if the design language needs extension
3. For modified UI requirements:
   - Update corresponding component/page prompts in place
4. For deprecated UI requirements:
   - Add `[DEPRECATED - Wave N]` marker to the corresponding prompts
5. Get user approval
6. Git commit:
   ```
   docs: update UCD style guide for wave N — <brief scope>
   ```

### 6. SRS Update & Feature Decomposition

Update the SRS and decompose into features:

**6a. Update SRS in place:**

1. Read `docs/plans/*-srs.md`
2. For **new** requirements:
   - Append to the appropriate section (Functional Requirements, NFRs, etc.)
   - Maintain ID continuity
3. For **modified** requirements:
   - Update the requirement text in place
   - Add a change note: `<!-- Wave N: Modified YYYY-MM-DD — <reason> -->`
4. For **deprecated** requirements:
   - Mark with `[DEPRECATED - Wave N: <reason>]` prefix
   - Do NOT delete (preserve traceability)
5. Update Traceability Matrix if present
6. Git commit:
   ```
   docs: update SRS for wave N — <brief scope>

   Added: FR-021, FR-022
   Modified: FR-005
   Deprecated: FR-012
   ```

**6b. Decompose into features:**

1. **New features**: Append to `feature-list.json` `features[]`:
   - `id`: max existing ID + 1 (continue incrementing)
   - `wave`: current wave number N
   - `status`: `"failing"`
   - `srs_trace`: array of new SRS requirement IDs (e.g. `["FR-021"]`)
   - `verification_steps`: optional — from new acceptance criteria (Given/When/Then)
   - `dependencies`: reference existing feature IDs as needed
   - `ui`, `ui_entry`: set appropriately

2. **Modified features**: For each affected existing feature:
   - Set `status` back to `"failing"` (will require re-implementation/re-verification)
   - Update `srs_trace` to reflect the revised requirement IDs
   - Optionally update `verification_steps` if present
   - Optionally set `wave` to N (to indicate when the modification occurred)

3. **Deprecated features**: For each deprecated feature:
   - Set `deprecated: true`
   - Set `deprecated_reason: "<reason>"`
   - Status remains as-is (it's excluded from all counts)

4. **Replacement features** (when deprecated + new replacement):
   - New feature gets `supersedes: <deprecated_feature_id>`

5. Update root `waves[]` array:
   ```json
   {
     "id": N,
     "date": "YYYY-MM-DD",
     "description": "Brief description from increment-request.json"
   }
   ```

6. Update `constraints[]` and `assumptions[]` if new CON/ASM items

7. Update `required_configs[]` if new configs needed

8. Validate:
   ```bash
   python scripts/validate_features.py feature-list.json
   ```

### 7. Update Auxiliary Files

Update supporting files as needed:

- **`long-task-guide.md`**: If new tools, frameworks, or patterns were introduced → regenerate or update relevant sections; re-validate with `python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json`
- **`init.sh` / `init.ps1`**: If new dependencies were added → update bootstrap scripts (keep idempotent)
- **`.env.example`**: If new `required_configs` of type `env` → append template lines (this is the canonical env-var reference template regardless of the project's actual config format)
- **`scripts/check_configs.py`**: If new `required_configs` are added → regenerate or update the project-specific checker to include the new configs

### 8. Finalize

1. Delete `increment-request.json` (signal file consumed)
2. Final validation:
   ```bash
   python scripts/validate_features.py feature-list.json
   ```
3. Git commit all changes:
   ```
   feat: increment wave N — <scope from increment-request.json>

   New features: <ids>
   Modified features: <ids>
   Deprecated features: <ids>
   Total features: X (Y active, Z deprecated)
   ```
4. Update `task-progress.md`:
   - Update `## Current State` header: progress count (X/Y active features passing), last event (Increment Wave M, date), next up (first failing feature)
   - Append session entry:
     ```
     ## Session N — Increment Wave M
     - **Date**: YYYY-MM-DD
     - **Phase**: Increment
     - **Scope**: <from increment-request.json>
     - **Changes**: Added N features, modified M features, deprecated K features
     - **Documents updated**: SRS, Design, [UCD]
     ```
5. Update `RELEASE_NOTES.md` under `[Unreleased]` section
6. Git commit progress files:
   ```
   chore: update progress for increment wave N
   ```

The router will now detect failing features in `feature-list.json` and route to Worker phase automatically.

## Critical Rules

- **Impact analysis before any changes** — never modify features without understanding blast radius
- **User approval at every stage** — impact matrix, design revisions, SRS updates all require explicit approval
- **In-place document updates** — do NOT create separate increment files; update existing SRS/Design/UCD directly; git history provides the audit trail
- **ID continuity** — new feature IDs always increment from max existing; never reuse deprecated IDs
- **Wave tracking** — every new/modified feature gets the current wave number
- **Deprecated features are immutable** — once deprecated, never un-deprecate; create a new feature instead
- **One increment per signal** — process one increment-request.json fully before accepting another

## Red Flags

| Rationalization | Correct Action |
|---|---|
| "I'll just add features to the JSON directly" | Use this skill for tracked, audited changes. |
| "The existing tests still pass, no need to re-verify" | Modified features must be reset to failing. |
| "I'll update the design later" | Design revision comes BEFORE feature decomposition. |
| "This change is small, skip impact analysis" | Impact analysis catches hidden dependencies. |
| "I'll create a separate SRS document" | Update the main SRS in place; git tracks history. |

## Integration

**Called by:** using-long-task (when increment-request.json exists)
**Reads:** SRS, Design, ATS, UCD, feature-list.json, increment-request.json
**Writes:** SRS (in place), Design (in place), ATS (in place), UCD (in place), feature-list.json (append/modify)
**Chains to:** long-task-work (after increment complete, via router detecting failing features)
