# <Project Name> — Software Requirements Specification

**Date**: YYYY-MM-DD
**Status**: Approved
**Standard**: Aligned with ISO/IEC/IEEE 29148

## 1. Purpose & Scope
[Core problem being solved. System boundaries.]

### 1.1 In Scope
[What the system WILL do in this version]

### 1.2 Out of Scope
[What is explicitly EXCLUDED — deferred or not planned]
[If requirements were deferred during granularity analysis, reference the deferred backlog:
"Deferred requirements tracked in [deferred backlog](YYYY-MM-DD-<topic>-deferred.md)"]

### 1.3 Problem Statement

**Root Cause (5-Whys)**:
```
Symptom: [user-stated problem in their words]
Why 1: [first cause]
Why 2: [cause of Why 1]
Why 3: [deepest supported cause]
Root Cause: [systemic cause requirements must address]
```

**Jobs-to-be-Done**: When [situation], I want to [motivation], so I can [outcome].

**Pain Map**:
| Pain Point | Current Workaround | Frequency | Severity | Score |
|---|---|---|---|---|

**Alignment Validation**: [PASS / PARTIAL / FAIL — filled by alignment validation step]

[Not applicable — Lite track or fully-specified increment]

## 2. Glossary & Definitions
| Term | Definition | Do NOT confuse with |
|------|-----------|---------------------|
[Every domain-specific or ambiguous term. Omit section if none.]

## 3. Stakeholders & User Personas
| Persona | Technical Level | Key Needs | Access Level |
|---------|----------------|-----------|--------------|
[Omit if no UI / end-user features]

### 3.1 Use Case View

```mermaid
graph LR
    %% Replace this placeholder with actual content during Step 4c
    %% Actors: use Actor((Name)) syntax as external nodes
    %% Use cases: place inside subgraph System Boundary
    %% Edges: Actor --> UseCaseNode for each participation

    Actor1((Persona Name))
    subgraph System Boundary
        UC1[FR-001: Use Case Title]
        UC2[FR-002: Use Case Title]
    end
    Actor1 --> UC1
    Actor1 --> UC2
```

[Omit this section if no user-facing functional requirements exist]

## 4. Functional Requirements

### FR-001: <Title>
**Priority**: Must
**EARS**: When <trigger>, the system shall <action>.
**Visual output** (if ui-facing): [One sentence: what the user sees change. e.g., "The snake's position on the game board updates visually after each tick." Write "N/A — backend-only" if this FR has no user-visible output.]
**Acceptance Criteria**:
- Given <context>, when <action>, then <expected result>
- Given <error context>, when <action>, then <error handling>

[Repeat for each functional requirement]

### 4.1 Process Flows

[One flowchart per functional area with 3+ steps or branching logic — generated during Step 4c]

#### Flow: <Workflow Name>

```mermaid
flowchart TD
    %% Replace this placeholder with actual content during Step 4c
    %% Start/End: ([label]) rounded stadium nodes
    %% Decisions: {condition?} with -- YES --> and -- NO --> labeled branches
    %% Include error/boundary paths from acceptance criteria

    S([Start: trigger])
    D{Decision?}
    B1[Action on YES]
    B2[Action on NO]
    E([End: outcome])

    S --> D
    D -- YES --> B1
    D -- NO --> B2
    B1 --> E
    B2 --> E
```

[Add additional #### Flow sections for each distinct functional area]
[Omit this section if all requirements are single-step with no branching]

## 5. Non-Functional Requirements
| ID | Category (ISO 25010) | Requirement | Measurable Criterion | Measurement Method |
|----|---------------------|-------------|---------------------|-------------------|
| NFR-001 | Performance | Response time | p95 < 200ms | Load test with k6 |
[If none apply, write "None identified" and state why]

## 6. Interface Requirements
| ID | External System | Direction | Protocol | Data Format |
|----|----------------|-----------|----------|-------------|
| IFR-001 | Payment Gateway | Outbound | REST/HTTPS | JSON |
[Omit if no external interfaces]

## 7. Constraints
| ID | Constraint | Rationale |
|----|-----------|-----------|
| CON-001 | Must run on Python 3.8+ | Corporate standard |
[If none, write "None identified"]

## 8. Assumptions & Dependencies
| ID | Assumption | Impact if Invalid |
|----|-----------|------------------|
| ASM-001 | JWT validation handled by API Gateway | Business layer must add validation |
[If none, write "None identified"]

## 9. Acceptance Criteria Summary
[Consolidated table or list linking each FR/NFR to its pass/fail criteria]

## 10. Traceability Matrix
| Requirement ID | Source (stakeholder need) | Pain Point Addressed | Verification Method |
|---------------|-------------------------|---------------------|-------------------|
| FR-001 | User story: "As a user, I want to..." | [Pain Map row label or "None — new capability"] | Automated test |
[Every requirement must appear in this matrix]

## 11. Open Questions
[Any items that need resolution during the design phase. If none, write "None".]
