# <Project Name> — Design Document

**Date**: YYYY-MM-DD
**Status**: Approved
**SRS Reference**: docs/plans/YYYY-MM-DD-<topic>-srs.md

<!-- Diagram Change Tracking Convention -->
> **Diagram Change Tracking** — applied only during increment updates (Wave N > 0). Initial design documents do NOT use change markers.
>
> | Diagram Type | New Element | Modified Element | Edge Marking |
> |---|---|---|---|
> | `graph`/`flowchart` | `Node[Label]:::newNode` | `Node[Label]:::modNode` | `A -->\|"label 🟢"\| B` / `🟡` |
> | `classDiagram` | `<<NEW - Wave N>>` annotation | `<<MODIFIED - Wave N>>` annotation | N/A |
> | `sequenceDiagram` | `rect rgb(209,250,229)` wrapper + Note | `rect rgb(254,243,199)` wrapper + Note | Wrapped in `rect` |
> | `erDiagram` | `ENTITY["NEW EntityName"]` alias | `ENTITY["MOD EntityName"]` alias | N/A |
> | `stateDiagram-v2` | `State:::newNode` | `State:::modNode` | Label with `🟢`/`🟡` |
>
> Standard `classDef` block (for graph/flowchart/stateDiagram-v2):
> ```
> classDef newNode fill:#d1fae5,stroke:#2ea043,stroke-width:2px
> classDef modNode fill:#fef3c7,stroke:#d4a017,stroke-width:2px
> ```
>
> **Legend**: Each diagram containing change markers MUST include a Markdown note before the code fence:
> `> **Change Legend (Wave N):** 🟢 = NEW | 🟡 = MODIFIED`
>
> **Cleanup rule**: Remove change markers from previous waves before applying new ones. Each diagram shows only current-wave markers.

## 0. Project Structure

> Target project directory tree. Mark each entry as **[existing]**, **[new]**, or **[modified]** to show the design's footprint on the codebase.

```
project-root/
├── src/
│   ├── models/              [existing]
│   ├── services/            [new]
│   │   └── auth_service.py  [new]
│   └── api/
│       ├── routes.py        [existing]
│       └── middleware.py     [modified]
├── tests/
│   └── test_auth.py         [new]
└── config.py                [existing]
```

[Replace the example above with the actual project directory tree. Include only directories and files that are architecturally significant — omit generated files, caches, and IDE configs. For brownfield projects, focus on areas touched by this design.]

## 1. Design Drivers
[Key SRS inputs: constraints, interface requirements that shaped this design]

## 2. Approach Selection
[Selected approach with justification. Brief mention of alternatives considered.]

## 3. Architecture

### 3.1 Architecture Overview
[High-level system description: key components, their responsibilities, and interactions]

### 3.2 Logical View
[Describe system decomposition into packages/modules/layers. Show major abstractions and their relationships.]

```mermaid
graph TB
    %% Increment change tracking: add classDef newNode/modNode here during Wave N updates
    subgraph Presentation Layer
        API[API Controllers]
    end
    subgraph Business Layer
        SVC[Service Layer]
        DOM[Domain Model]
    end
    subgraph Data Layer
        REPO[Repositories]
        DB[(Database)]
    end
    API --> SVC
    SVC --> DOM
    SVC --> REPO
    REPO --> DB
```

[Replace the example above with the actual logical architecture of the project. Show layers, packages, modules, and their dependency directions.]

### 3.3 Component Diagram

[Show major runtime components and their interactions.
 Every edge MUST include: (1) protocol, (2) schema name referencing a §6.2 Contract ID.]

```mermaid
graph LR
    %% Increment change tracking: add classDef newNode/modNode here during Wave N updates
    A[Component A] -->|"REST: ResourceDTO (IAPI-001)"| B[Component B]
    B -->|"event: ResourceCreatedEvent (IAPI-002)"| C[Component C]
```

[Replace the example above with actual components and interactions. An edge without a Contract ID label is a design defect — add a §6.2 row or justify as a framework-level dependency with no runtime data exchange.]

### 3.4 Tech Stack Decisions
[Justify against SRS constraints]

## 4. Key Feature Designs

> **Instructions**: Create one subsection per key feature (or feature group). Each subsection MUST include at least: a class diagram and one behavioral diagram (sequence or flow). For complex features, include all four views.

### 4.N Feature: <Feature Name> (FR-xxx)

#### 4.N.1 Overview
[1-2 sentences: what this feature does, which SRS requirements it satisfies]

#### 4.N.2 Class Diagram
[Show the classes/modules involved, their attributes, methods, and relationships]

```mermaid
classDiagram
    %% Increment change tracking: use <<NEW - Wave N>> / <<MODIFIED - Wave N>> annotations during Wave N updates
    class ClassName {
        -privateField: Type
        +publicMethod(param: Type): ReturnType
    }
    class AnotherClass {
        +field: Type
        +method(): void
    }
    ClassName --> AnotherClass : uses
```

#### 4.N.3 Sequence Diagram
[Show the interaction between objects/components for the main success scenario]

```mermaid
sequenceDiagram
    %% Increment change tracking: wrap new flows in rect rgb(209,250,229), modified in rect rgb(254,243,199) during Wave N updates
    participant User
    participant Controller
    participant Service
    participant Repository
    User->>Controller: request
    Controller->>Service: process()
    Service->>Repository: query()
    Repository-->>Service: result
    Service-->>Controller: response
    Controller-->>User: result
```

#### 4.N.4 Flow Diagram
[Show the process/logic flow including decision points and error paths]

```mermaid
flowchart TD
    %% Increment change tracking: add classDef newNode/modNode here during Wave N updates
    A[Start] --> B{Condition?}
    B -->|Yes| C[Action A]
    B -->|No| D[Action B]
    C --> E[End]
    D --> E
```

#### 4.N.5 Design Notes
[Key design decisions, edge cases, error handling strategy for this feature]

#### 4.N.6 Integration Surface

**Provides** (other features depend on this):

| Consumer Feature(s) | Contract ID | Endpoint / Method | Response Schema |
|---------------------|-------------|-------------------|----------------|
| [#M Feature B] | [IAPI-001] | [`GET /api/resource/:id`] | [`ResourceDTO`] |

**Requires** (this feature depends on):

| Provider Feature | Contract ID | Endpoint / Method | Request Schema |
|-----------------|-------------|-------------------|---------------|
| [#K Feature C] | [IAPI-002] | [`POST /api/other`] | [`OtherRequest`] |

[If this feature has no cross-feature dependencies, write:
 "Self-contained — no external integration surface."]

[Repeat section 4.N for each key feature or feature group]

## 5. Data Model
[Schemas, relationships, storage strategy]

```mermaid
erDiagram
    %% Increment change tracking: use ENTITY["NEW Name"] / ENTITY["MOD Name"] aliases during Wave N updates
    ENTITY_A ||--o{ ENTITY_B : "relationship"
    ENTITY_A {
        type field_name PK
        type field_name
    }
    ENTITY_B {
        type field_name PK
        type field_name FK
    }
```

## 6. API / Interface Design

### 6.1 External Interfaces
[Endpoints, contracts, protocols for external third-party systems]
[Trace to SRS IFR-xxx requirements]

### 6.2 Internal API Contracts

[For each component-to-component interaction in §3.3, define the contract.
 These are consumed by per-feature design SubAgents to ensure integration coherence.]

| Contract ID | Provider Feature | Consumer Feature(s) | Endpoint / Method | Request Schema | Response Schema | Error Codes |
|-------------|-----------------|---------------------|-------------------|---------------|----------------|-------------|
| IAPI-001 | #N Feature A | #M Feature B, #K Feature C | `GET /api/resource/:id` | `{ id: UUID }` | `ResourceDTO { ... }` | 401, 404 |

[Replace the example above with actual internal contracts from §3.3 edges.]

**Schema Definitions** (referenced by table above):

[Use the project's primary language syntax. Define each shared schema used in the table.]

```
// Example — replace with actual schemas
interface ResourceDTO {
  id: string;
  name: string;
  created_at: string; // ISO 8601
}
```

**When to define an internal API contract:**
1. Any component pair connected by an edge in §3.3 → must have a corresponding row
2. If feature A's `dependencies[]` in feature-list.json includes feature B, and A calls B's methods/APIs at runtime → must have a corresponding row
3. Two features sharing persistent state (same DB table/file/cache) → must define the shared schema
4. **Not required**: Pure framework-level dependencies (e.g., feature B depends on feature A's project skeleton but has no runtime calls)

**Granularity rule:** Define contracts to the level where a Consumer can code independently — i.e., the Consumer can write correct calling code and error handling by reading only this table.

## 7. Third-Party Dependencies

> **Instructions**: List ALL third-party libraries, frameworks, and tools. Each entry MUST specify an exact version (or version range) and compatibility notes.

| Library / Framework | Version | Purpose | License | Compatibility Notes |
|---|---|---|---|---|
| example-lib | 2.3.1 | [purpose] | MIT | Compatible with Python >= 3.10 |
| another-lib | ^4.0.0 | [purpose] | Apache-2.0 | Requires example-lib >= 2.0 |

### 7.1 Version Constraints
[Document any version pinning rationale, known incompatibilities, or upgrade risks]

### 7.2 Dependency Graph
[Show critical dependency relationships if complex]

```mermaid
graph LR
    %% Increment change tracking: add classDef newNode/modNode here during Wave N updates
    App --> LibA["LibA v1.2"]
    App --> LibB["LibB v3.0"]
    LibB --> LibC["LibC v2.1"]
    LibA -.->|"requires >= 2.0"| LibC
```

## 8. Testing Strategy
[Test types, coverage approach, tooling]
[How SRS acceptance criteria map to test suites]

## 9. Development Plan

### 9.1 Milestones

| Milestone | Target | Scope | Exit Criteria |
|---|---|---|---|
| M1: Foundation | [date/sprint] | Core infrastructure, project skeleton | Build passes, dev environment reproducible |
| M2: Core Features | [date/sprint] | [list high-priority features] | All high-priority features passing |
| M3: Extended Features | [date/sprint] | [list medium-priority features] | All medium-priority features passing |
| M4: Polish & Release | [date/sprint] | Quality verification, documentation, examples | All quality gates met, release-ready |

### 9.2 Task Decomposition & Priority

> **Instructions**: Each row becomes one feature in `feature-list.json`. Group related right-sized FRs (already validated by SRS G1-G6 + S1-S4 bidirectional sizing) into vertical slices. Include Mapped FRs for traceability. Each feature should productively fill one Worker session (~50% of model context window, target ~1,000 lines implementation code excluding UT per FR).

| Priority | Feature | Mapped FRs | Dependencies | Milestone | Rationale |
|---|---|---|---|---|---|
| P0 - Critical | [Feature A] | FR-001, FR-002 | None | M1 | Foundation required by all others |
| P1 - High | [Feature B] | FR-003, FR-004, FR-005 | A | M2 | Core value proposition |
| P2 - Medium | [Feature C] | FR-008, FR-009 | B | M3 | Extended functionality |
| P3 - Low | [Feature D] | FR-012 | None | M4 | Nice-to-have |

### 9.3 Dependency Chain
[Show the critical path and feature dependency ordering]

```mermaid
graph LR
    %% Increment change tracking: add classDef newNode/modNode here during Wave N updates
    A[Feature A<br/>P0] --> C[Feature C<br/>P1]
    B[Feature B<br/>P0] --> D[Feature D<br/>P1]
    C --> E[Feature E<br/>P2]
    C --> F[Feature F<br/>P2]
    D --> F
```

### 9.4 Risk & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| [risk description] | High/Med/Low | High/Med/Low | [mitigation strategy] |

## 10. Open Questions / Risks
[Any remaining items to resolve during implementation]

## 11. Codebase Conventions & Constraints

> *This section is auto-populated from `docs/rules/` during design if the project has an existing codebase (brownfield). For greenfield projects, keep each subsection with empty tables — do NOT mark the entire section "N/A". Downstream skills always read §11; empty tables signal "no constraints" without requiring conditional logic.*
> *These conventions are binding for all new code unless explicitly overridden elsewhere in this design document. Design overrides are marked with "⚠ Design Override" annotations.*

### 11.1 2nd-Party Library Constraints

> Mandatory internal libraries that replace standard library or 3rd-party alternatives. All new code MUST use these — do not use the replaced APIs directly.

| Domain | Internal Library | Replaces | Import Pattern | Notes |
|--------|-----------------|----------|---------------|-------|
| [e.g., HTTP Client] | [e.g., `@company/http`] | [e.g., axios, fetch] | [e.g., `import { get } from '@company/http'`] | [e.g., All external HTTP calls] |

### 11.2 Prohibited APIs

| Prohibited | Reason | Use Instead |
|------------|--------|-------------|
| [e.g., `console.log`] | [e.g., Structured logging required] | [e.g., `internal.logger`] |

### 11.3 Approved 3rd-Party Libraries

| Purpose | Library | Version | Pinning Strategy |
|---------|---------|---------|-----------------|
| [e.g., Testing] | [e.g., pytest] | [e.g., ^7.4] | [e.g., Range-pinned] |

### 11.4 Static Analysis Tools

> Downstream TDD/Quality skills run these tools directly — the tools read their own config files.

| Tool | Config File | Run Command |
|------|------------|-------------|
| [e.g., eslint] | [e.g., `.eslintrc.json`] | [e.g., `npx eslint .`] |

### 11.5 Coding Style Summary

| Rule | Convention | Source |
|------|-----------|--------|
| [e.g., Variable naming] | [e.g., camelCase] | [e.g., Observed 95% consistency] |
| [e.g., Indentation] | [e.g., 2 spaces] | [e.g., .editorconfig] |

### 11.6 Error Handling Pattern

[Dominant error handling approach: try/catch, Result types, custom Error classes, centralized middleware, etc.]


