---
name: long-task-design
description: "Use when SRS doc exists but no design doc and no feature-list.json - take the approved SRS as input and produce an architecture/design document focused on HOW to build it"
---

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
2. **Explore technical context** — existing code, frameworks, deployment environment
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Section-by-section design approval** — architecture, data model, API, UI, testing, deployment
5. **Write design document** — save to `docs/plans/YYYY-MM-DD-<topic>-design.md` and commit
6. **Transition to ATS** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ats`

**The terminal state is invoking long-task-ats.** Do NOT invoke any other implementation skill.

## Step 1: Read SRS & UCD & Extract Design Inputs

1. Read the approved SRS document from `docs/plans/*-srs.md`
2. Read the approved UCD style guide from `docs/plans/*-ucd.md` (if it exists — only present for UI projects)
3. Extract key design drivers:
   - **Functional scope** — FR count, priority distribution, dependency chains
   - **NFR thresholds** — performance targets, reliability, scalability that affect architecture
   - **Constraints** — hard limits that restrict technology/approach choices
   - **Interface requirements** — external systems, protocols, data formats to integrate with
   - **User personas** — technical levels that affect API/UI design decisions
   - **UCD style tokens** (if UCD exists) — color palette, typography, spacing, component catalog → informs frontend architecture and UI/UX section
4. List any SRS **Open Questions** that must be resolved before design can proceed
   - If unresolved questions affect architecture → ask user via `AskUserQuestion` before Step 2

## Step 2: Explore Technical Context

1. Explore existing code / repos the project will build on
2. Identify technical constraints not in the SRS (e.g., monorepo structure, CI/CD pipeline, existing libraries)
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
**NFR impact**: [how this approach affects the SRS NFR thresholds]
**Third-party dependencies**: [key libraries/frameworks this approach requires, with versions]

## Approach B: [Name]
...

## Recommendation: Approach [X]
**Reason**: [why this fits best given the SRS constraints and NFRs]
```

**Key**: Each approach must be evaluated against the SRS constraints and NFR thresholds. An approach that cannot meet a "Must" NFR is disqualified.

## Step 4: Section-by-Section Approval

For non-trivial projects, break the design into sections and get approval per section:

1. **Architecture** — system components, logical view, tech stack decisions
   - Must include a **Logical View** (Mermaid `graph`) showing layers/packages/modules and dependency directions
   - Must include a **Component Diagram** (Mermaid `graph`) showing runtime components and interactions
   - Must justify tech stack choices against SRS constraints
   - Must show how NFR thresholds will be met
2. **Key feature designs** — one chapter per key feature or feature group
   - Each feature chapter MUST include at least:
     - **Class diagram** (Mermaid `classDiagram`) — classes/modules, attributes, methods, relationships
     - **One behavioral diagram**: sequence diagram (Mermaid `sequenceDiagram`) or flow diagram (Mermaid `flowchart`)
   - For complex features, include ALL four views: class diagram, sequence diagram, flow diagram, and design notes
   - All diagrams MUST use **Mermaid** format — no ASCII art, no image references
3. **Data model** — schemas, relationships, storage strategy
   - Must use Mermaid ER diagrams (`erDiagram`) where applicable
4. **API / interface design** — endpoints, contracts, protocols
   - Must align with SRS Interface Requirements (IFR-xxx)
5. **UI/UX approach** (if applicable) — layout strategy, interaction patterns
   - Must address SRS User Personas
   - If UCD document exists: must reference UCD style tokens (colors, typography, spacing) and component catalog
   - Frontend architecture decisions (component library, state management, routing) must be compatible with UCD style tokens
   - Include a mapping: UCD component prompts → concrete implementation components
6. **Third-party dependencies** — ALL libraries/frameworks with **exact version numbers**
   - Must verify mutual compatibility between dependencies
   - Must verify compatibility with the project's target runtime version
   - Must note license type for each dependency
   - Must include a dependency graph (Mermaid) for non-trivial dependency chains
7. **Testing strategy** — high-level test approach decisions only
   - Test philosophy: TDD with quality gates (Red → Green → Refactor → Coverage → Mutation)
   - Tool selections: test framework, coverage tool, mutation tool (with versions — these are design decisions)
   - Coverage thresholds: line >= X%, branch >= Y%, mutation >= Z%
   - **Boundary**: "Detailed requirement-to-test-category mapping, NFR test methods, and cross-feature integration scenarios are defined in the ATS phase — not here."
8. **Deployment / infrastructure** (if applicable) — hosting, CI/CD, environments
9. **Development plan** — milestones, task decomposition, priority ordering
   - Must define milestones with clear exit criteria
   - Must decompose features into prioritized tasks (P0-P3)
   - Must show dependency chain (Mermaid `graph`) identifying the critical path
   - Must include risk assessment with mitigation strategies

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 features): Combine all sections into a single approval step, but still include the required diagrams and dependency versions.

## Step 5: Write Design Document

Save the approved design to `docs/plans/YYYY-MM-DD-<topic>-design.md`.

### Template usage

Read the template found in Step 2 (user-specified or default `docs/templates/design-template.md`):
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved design content
3. Add metadata at top if not already present (`Date`, `Status`, `SRS Reference`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

## Step 6: Transition to ATS

Once the design document is saved and committed:

1. Summarize key inputs the ATS skill will need:
   - **From SRS**: all FR/NFR/IFR requirements with acceptance criteria
   - **From Design**: testing strategy, tech stack, architecture risk areas
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ats` to generate the Acceptance Test Strategy

## Scaling the Design Phase

| Project Size | Features | Design Depth |
|---|---|---|
| Tiny | 1-5 | Single paragraph approach + 1 approval step; logical view + 1 feature diagram + dependency table + simplified dev plan |
| Small | 5-20 | 2-3 approach options + combined section approval; logical view + key feature diagrams + dependency table + milestone plan |
| Medium | 20-50 | Full multi-section approval; all architecture views + per-feature diagrams + full dependency analysis + detailed dev plan |
| Large | 50-200+ | Full multi-section approval; comprehensive diagrams for every feature group + dependency compatibility matrix + phased dev plan with risk register |

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
   - Final milestone is always "Polish & Release" (NFR verification, docs, examples)
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

**Called by:** using-long-task (when SRS + UCD exist, no design doc, no feature-list.json) or long-task-ucd (Step 8)
**Requires:** Approved SRS at `docs/plans/*-srs.md`; optionally approved UCD at `docs/plans/*-ucd.md` (for UI projects)
**Chains to:** long-task-ats (after design approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-design.md`
