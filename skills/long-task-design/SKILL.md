---
name: long-task-design
description: "Use when SRS doc exists but no design doc and no feature-list.json - take the approved SRS as input and produce an architecture/design document focused on HOW to build it"
---

**LANGUAGE RULE**: You MUST respond to the user in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Skill names, code identifiers, and JSON field names remain in English.

# Design Document Generation

Take the approved SRS as input. Propose implementation approaches, get section-by-section design approval, and produce a design document that answers HOW — while the SRS answers WHAT.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, run init_project.py, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "The SRS Is Detailed Enough To Start Coding"

The SRS describes WHAT the system must do. The design document describes HOW. Even when requirements are crystal clear, the implementation approach (architecture, data model, tech stack choices) needs explicit decisions and user approval. Skipping design causes mid-session corrections and rework.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Read the approved SRS** — from `docs/plans/*-srs.md`
2. **Explore technical context** — existing code, frameworks, runtime environment
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Section-by-section design approval** — architecture, data model, API, UI, testing
5. **Write design document** — save to `docs/plans/YYYY-MM-DD-<topic>-design.md` and commit
6. **Transition to Init** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-init`

**The terminal state is invoking long-task-init.** Do NOT invoke any other implementation skill.

## Step 1: Read SRS & Extract Design Inputs

1. Read the approved SRS document from `docs/plans/*-srs.md`
2. Extract key design drivers:
   - **Functional scope** — FR count, priority distribution, dependency chains
   - **Constraints** — hard limits that restrict technology/approach choices
   - **Interface requirements** — external systems, protocols, data formats to integrate with
   - **User personas** — technical levels that affect API design decisions
3. List any SRS **Open Questions** that must be resolved before design can proceed
   - If unresolved questions affect architecture → ask user via `AskUserQuestion` before Step 2

## Step 2: Explore Technical Context

1. Explore existing code / repos the project will build on
2. Identify technical constraints not in the SRS (e.g., monorepo structure, existing libraries)
3. Check for a design document template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/design-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 3: Propose Approaches

Present **2-3 implementation approaches** with explicit trade-offs:

```markdown
## Approach A: [Name]
**How it works**: [1-2 sentences]
**Pros**: [bullet list]
**Cons**: [bullet list]
**Best when**: [conditions]
**Third-party dependencies**: [key libraries/frameworks this approach requires, with versions]

## Approach B: [Name]
...

## Recommendation: Approach [X]
**Reason**: [why this fits best given the SRS constraints]
```

**Key**: Each approach must be evaluated against the SRS constraints.

## Step 4: Section-by-Section Approval

For non-trivial projects, break the design into sections and get approval per section:

0. **Project structure** — target project directory tree, marking [existing] / [new] / [modified] entries
   - For greenfield: show the planned directory layout
   - For brownfield: explore the existing codebase first (Step 2), then mark which directories/files this design will add or modify
1. **Architecture** — system components, logical view, tech stack decisions
   - Must include a **Logical View** (Mermaid `graph`) showing layers/packages/modules and dependency directions
   - Must include a **Component Diagram** (Mermaid `graph`) showing runtime components and interactions
   - Must justify tech stack choices against SRS constraints
2. **Key feature designs** — one chapter per key feature or feature group
   - Each feature chapter MUST include at least:
     - **Class diagram** (Mermaid `classDiagram`) — classes/modules, attributes, methods, relationships
     - **One behavioral diagram**: sequence diagram (Mermaid `sequenceDiagram`) or flow diagram (Mermaid `flowchart`)
     - **Integration Surface** (§4.N.6) — declaring Provides/Requires tables with §6.2 Contract IDs; write "Self-contained" if no cross-feature dependencies
   - For complex features, include ALL four views: class diagram, sequence diagram, flow diagram, and design notes
   - All diagrams MUST use **Mermaid** format — no ASCII art, no image references
3. **Data model** — schemas, relationships, storage strategy
   - Must use Mermaid ER diagrams (`erDiagram`) where applicable
4. **API / interface design**
   - **External interfaces** (§6.1) — endpoints, contracts, protocols (trace to SRS IFR-xxx)
   - **Internal API contracts** (§6.2) — feature-to-feature boundaries; every §3.3 component diagram edge must have a corresponding §6.2 row with Contract ID, request/response schemas, and error codes
5. **Third-party dependencies** — ALL libraries/frameworks with **exact version numbers**
   - Must verify mutual compatibility between dependencies
   - Must verify compatibility with the project's target runtime version
   - Must note license type for each dependency
   - Must include a dependency graph (Mermaid) for non-trivial dependency chains
6. **Testing strategy** — high-level test approach decisions only
   - Test philosophy: TDD (Red → Green → Refactor)
   - Tool selections: test framework, coverage tool, mutation tool (with versions — these are design decisions)
   - Coverage thresholds: line >= X%, branch >= Y%, mutation >= Z%
   - **Boundary**: "Detailed test scenarios are defined during feature design and TDD phases — not here."
7. **Development plan** — milestones, task decomposition, priority ordering
   - Must define milestones with clear exit criteria
   - Must decompose into context-budget-sized features (P0-P3) — each row in §9.2 becomes one feature in `feature-list.json`; group related right-sized FRs (already validated by SRS G+S heuristics) into vertical slices; include `Mapped FRs` column for traceability
   - Must show dependency chain (Mermaid `graph`) identifying the critical path
   - Must include risk assessment with mitigation strategies

> **Feature sizing is upstream**: FRs are right-sized at the Requirements phase via bidirectional granularity analysis (G1-G6 split + S1-S4 merge). §9.2 groups these right-sized FRs into implementation features. Each row should map 1+ related FRs into a vertical slice that productively fills one Worker session (~50% of context window, targeting ~1,000 lines implementation code excluding UT per FR). Feature counts in the scaling table below refer to the final §9.2 row count.

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 features): Combine all sections into a single approval step, but still include the required diagrams and dependency versions.

## Step 4b: Populate §11 — Codebase Conventions & Constraints

**Always execute this step** — for both brownfield and greenfield projects. §11 must be present in every design document so downstream skills (feature-design, TDD, Worker) can read it unconditionally.

**Brownfield** (if `docs/rules/` exists and is populated with convention scan results from Phase 0-pre):

1. **Read all `docs/rules/*.md` files** — `coding-style.md`, `coding-constraints.md`, `build-and-compilation.md`
2. **Populate §11 of the design document** (Codebase Conventions & Constraints) using the design template's §11 structure:
   - §11.1: Extract "Mandatory Internal Libraries" table from `coding-constraints.md`
   - §11.2: Extract "Prohibited APIs / Libraries" table from `coding-constraints.md`
   - §11.3: Extract "Approved 3rd-Party Libraries" table from `coding-constraints.md`
   - §11.4: Extract "Static Analysis Tools" table from `coding-constraints.md` (tool name + config path + run command only — do not read config contents)
   - §11.5: Extract key naming and formatting rules from `coding-style.md` (summary table)
   - §11.6: Extract error handling pattern from `coding-constraints.md`
3. **Cross-verify** — check for conflicts between scanned conventions and design decisions:
   - §8 (Third-Party Dependencies): new dependencies must not conflict with §11.2 prohibited list
   - §6.2 (Internal API Contracts): libraries used must comply with §11.1 internal library mandates
   - If conflicts exist: mark with "⚠ Design Override: [reason]" and present to user for confirmation
4. **Present §11 to user** for review (same approval flow as other sections)

**Greenfield** (if `docs/rules/` does not exist or is empty):

1. **Populate §11 with empty tables** (column headers + zero rows) for each subsection §11.1–§11.6, using the design template's §11 structure
2. **Present to user**: "§11 created with empty convention tables. Add constraints now if known, or leave empty — downstream skills read §11 unconditionally."
3. If user adds constraints: incorporate and re-present for approval
4. If user leaves empty: proceed — empty tables signal "no constraints" to downstream skills

## Step 5: Write Design Document

Save the approved design to `docs/plans/YYYY-MM-DD-<topic>-design.md`.

### Template usage

Read the template found in Step 2 (user-specified or default `docs/templates/design-template.md`):
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved design content
3. Add metadata at top if not already present (`Date`, `Status`, `SRS Reference`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

## Step 5b: Design Integration Coherence Check

Before transitioning to Init, mechanically verify cross-feature integration coherence:

1. **Contract completeness**: For each edge in §3.3 component diagram, verify a corresponding row exists in §6.2 Internal API Contracts. Flag missing rows.
2. **Schema consistency**: For each §6.2 row, verify that Provider feature's §4.N class diagram includes the Response Schema type, and Consumer feature's §4.N references the Request Schema. Flag mismatches.
3. **Dependency completeness**: For each feature that appears in a §6.2 "Consumer" column, verify it lists the Provider feature ID in §9.3 dependency chain. Flag missing dependency edges.

Present any flagged issues to the user. Resolve before proceeding to Init.

## Step 6: Transition to Init

Once the design document is saved and committed:

1. Summarize key inputs the Init skill will need:
   - **From SRS**: requirements, acceptance criteria → features
   - **From Design**: tech stack, architecture → project skeleton
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-init` to scaffold the project

## Scaling the Design Phase

| Project Size | Features | Design Depth |
|---|---|---|
| Tiny | 1-5 | Single paragraph approach + 1 approval step; logical view + 1 feature diagram + dependency table + simplified dev plan |
| Small | 5-20 | 2-3 approach options + combined section approval; logical view + key feature diagrams + dependency table + milestone plan |
| Medium | 20-50 | Full multi-section approval; all architecture views + per-feature diagrams + full dependency analysis + detailed dev plan |
| Large | 50-200+ | Full multi-section approval; comprehensive diagrams for every feature group + dependency compatibility matrix + phased dev plan with risk register |

## Section 4 Depth Strategy

For projects with many features, §4.N sections are written at different depths to manage context window constraints:

| Project Size | §4.N Content per Feature |
|---|---|
| Small (< 20) | Full: overview + class diagram + behavioral diagram + design notes + integration surface |
| Medium (20-50) | Full for P0/P1 features; Thin for P2/P3 features |
| Large (50+) | Thin for ALL features: overview + key types + integration surface only |

**Thin §4.N format:**

```markdown
### 4.N Feature: <Name> (FR-xxx)
#### 4.N.1 Overview
[1-2 sentences]
#### 4.N.2 Key Types
[List the main classes/types this feature introduces, with one-line purpose each]
#### 4.N.6 Integration Surface
[Provides/Requires tables referencing §6.2]
```

This is safe because the feature-design SubAgent (Worker Step 4) produces the full class/sequence/flow/algorithm design with access to §6.2 contracts. The thin §4.N serves as an **integration specification**, not a complete design.

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "The SRS already implies the architecture" | SRS describes WHAT, not HOW. Present options. |
| "There's only one way to build this" | Present at least 2 approaches. Even obvious choices benefit from stated trade-offs. |
| "I already know the best approach" | Present options, let the user choose |
| "The user seems impatient, I'll skip design" | Explain the value briefly, then run efficiently |
| "I'll design as I go" | Upfront design is cheaper than mid-session corrections |
| "Let me re-clarify requirements here" | Requirements belong in the SRS. If missing, note as Open Question and resolve with user before design. |

## Diagram Requirements

All architectural and design views MUST use **Mermaid** syntax. This ensures:
- Diagrams are version-controlled alongside the document (no external image files)
- Diagrams are renderable in GitHub, GitLab, and most Markdown viewers
- Diagrams stay in sync with design changes

### Required Diagram Types

| Section | Diagram Type | Mermaid Syntax | Required? |
|---|---|---|---|
| Architecture Logical View | Layered package diagram | `graph TB` | Always |
| Architecture Components | Component interaction | `graph LR` | Always |
| Key Feature — Structure | Class diagram | `classDiagram` | Per feature |
| Key Feature — Behavior | Sequence diagram | `sequenceDiagram` | Per feature (at least one behavioral) |
| Key Feature — Logic | Flow/decision diagram | `flowchart TD` | Per feature (at least one behavioral) |
| Data Model | ER diagram | `erDiagram` | If persistent storage |
| Dependency Graph | Dependency tree | `graph LR` | If > 3 third-party deps |
| Development Plan | Critical path | `graph LR` | Always |

### Diagram Quality Checklist
- [ ] Each diagram has a clear title or surrounding heading
- [ ] Class diagrams show visibility modifiers (`+`/`-`/`#`) and key methods
- [ ] Sequence diagrams show the main success path and at least one error path
- [ ] Flow diagrams include decision nodes for all branching logic
- [ ] No placeholder diagrams — every diagram reflects actual approved design content
- [ ] Every edge in §3.3 component diagram includes Contract ID referencing §6.2
- [ ] During increment updates: new/modified diagram elements use visual change-tracking styles (green=NEW, amber=MODIFIED) per design template convention; previous-wave markers removed

## Third-Party Dependency Rules

1. **Exact versions required** — specify `1.2.3` or a constrained range `^1.2.0` / `>=1.2,<2.0`; never use `latest` or omit version
2. **Compatibility matrix** — verify each dependency is compatible with:
   - The target language/runtime version (e.g., Python >= 3.10, Node >= 18)
   - Other dependencies in the stack (check for known conflicts)
3. **License audit** — document the license for each dependency; flag any copyleft licenses (GPL, AGPL) that may conflict with project requirements
4. **Upgrade path** — note any dependencies approaching EOL or with known migration concerns

## Development Plan Rules

The development plan section bridges the design document to the Init phase. It MUST include:

1. **Milestones** — time-boxed phases with clear scope and exit criteria
   - M1 is always "Foundation" (project skeleton, CI, core abstractions)
   - Final milestone is always "Polish & Release" (docs, examples)
2. **Task decomposition** — features mapped to priorities (P0-P3) with rationale
   - P0: Foundation — required by all other features
   - P1: Core value — the minimum viable feature set
   - P2: Extended — important but not launch-blocking
   - P3: Nice-to-have — defer if timeline is tight
3. **Dependency chain** — Mermaid graph showing which features block others
4. **Paired feature ordering** — When the project has both backend and frontend features, organize the task decomposition table so that each backend feature is paired with its corresponding frontend feature. This produces a natural development flow: Backend A → Frontend A → Backend B → Frontend B. The Init phase uses this pairing to order features in `feature-list.json`.
5. **Risk register** — technical and schedule risks with mitigation

The Init phase uses this plan to populate `feature-list.json` with correct priority ordering, paired grouping, and dependency chains.

## Integration

**Called by:** using-long-task (when SRS exists, no design doc, no feature-list.json)
**Requires:** Approved SRS at `docs/plans/*-srs.md`; optionally `docs/rules/*.md` (codebase conventions from Phase 0-pre scan)
**Chains to:** long-task-init (after design approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-design.md` (always includes §11 Codebase Conventions — populated from `docs/rules/` for brownfield, empty tables for greenfield)
