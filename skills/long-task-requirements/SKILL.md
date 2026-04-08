---
name: long-task-requirements
description: "Use when no SRS doc and no design doc and no feature-list.json exist - elicit requirements through structured questioning and produce a high-quality SRS document aligned with ISO/IEC/IEEE 29148"
---

**LANGUAGE RULE**: You MUST respond to the user in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Skill names, code identifiers, and JSON field names remain in English.

# Requirements Elicitation & SRS Generation

Turn raw ideas into a structured, high-quality Software Requirements Specification (SRS) through systematic elicitation, challenge, and validation — aligned with ISO/IEC/IEEE 29148 and EARS requirement syntax.

Adapts depth automatically: **Lite track** for clear-scope projects (3–5 rounds), **Expert track** for complex domains (10–20 rounds). Both produce the same SRS template output.

<HARD-GATE>
Do NOT invoke any design skill, implementation skill, write any code, scaffold any project, or take any design/implementation action until you have presented the SRS and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need an SRS"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The SRS can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Explore project context** — read existing docs, code, constraints; detect SRS template
2. **Complexity assessment** — evaluate 5 signals, select Lite or Expert track (internal)
3. **Problem & scope elicitation**
   - Lite: L1 (focused problem & scope, 1 round)
   - Expert: E1 (problem framing via `references/problem-framing.md`) + E2 (enhanced scope)
4. **Functional requirements elicitation**
   - Lite: L2 (flat capability rounds)
   - Expert: E3 (scenario walkthrough via `references/scenario-walkthrough.md`) + E4 (hypothesis-correction via `references/hypothesis-correction.md`)
5. **NFR + hidden requirements**
   - Lite: L3 (merged, 1 round)
   - Expert: E5 (hidden requirements) + E6 (NFR quantification)
6. **Constraints, assumptions, glossary** — same for both tracks
7. **Classify requirements** — functional / NFR / constraint / assumption / interface / exclusion
8. **Write requirements** — apply EARS templates, assign IDs, write acceptance criteria, generate diagrams
9. **Validate SRS** — check 8 quality attributes, detect anti-patterns, verify testability
10. **Granularity analysis** — bidirectional sizing: detect oversized FRs (G1-G6 split) AND undersized FRs (S1-S4 group) to fit context budget; user approval for non-trivial changes
11. **Scope fit & deferral** — assess current-round vs next-round, generate deferred backlog if applicable
12. **[Expert only] Alignment validation** — via `references/alignment-validation.md`
13. **SRS Compliance Review** — dispatch srs-reviewer subagent; gate: all checks PASS before proceeding
14. **Present & approve SRS** — Lite: single combined step; Expert: section-by-section
15. **Save SRS & backlog** — `docs/plans/YYYY-MM-DD-<topic>-srs.md` + deferred backlog (if any) and commit
16. **Transition to UCD** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ucd`

**The terminal state is invoking long-task-ucd.** Do NOT invoke any other skill.

## Step 1: Explore Context

1. Read the user-provided requirement doc / idea description thoroughly
2. Explore existing code / repos the project will build on or integrate with
3. Identify initial constraints: tech stack, platform, integrations, regulations
4. Read `docs/rules/` (if exists and populated) — codebase conventions extracted by Phase 0-pre scanner:
   - `coding-constraints.md` — 2/3方件 library constraints, prohibited APIs, internal library mandates
   - `build-and-compilation.md` — build system and CI/CD constraints
   - These constraints may affect requirement feasibility and should be considered during elicitation (e.g., "this feature requires HTTP calls — project mandates using internal HTTP library, not standard fetch"; "project CI requires all code to pass checkstyle — affects acceptance criteria")
5. Check for an SRS template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/srs-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 1.5: Complexity Assessment (internal — no user interaction)

After Step 1, evaluate 5 complexity signals against the user's description and project context:

| # | Signal | Lite indicator | Expert indicator |
|---|---|---|---|
| S1 | **Stated scope** | Single purpose, clear boundary ("a script that does X") | Vague/broad scope ("a platform for managing...", "a system that...") |
| S2 | **Actor count** | 1 actor or no user-facing interaction | 2+ distinct user roles mentioned |
| S3 | **Integration surface** | No external systems, or 1 well-known API | 2+ external systems, custom protocols |
| S4 | **Domain complexity** | Developer tool, utility, well-understood domain | Business domain with jargon, regulatory exposure, multi-stakeholder |
| S5 | **Description style** | Solution-specific ("build X using Y") | Problem-oriented or vague ("we need better X", "users complain about Y") |

**≥3 Expert signals → Expert track. Otherwise → Lite track.**

Record the tier decision internally. Do NOT ask the user which tier to use.

### Escalation Trigger (Lite → Expert)

During Lite elicitation, if ANY of these emerge, switch seamlessly to Expert track:
- 2+ distinct user roles with conflicting needs
- 3+ external system integrations surface
- Regulatory/compliance requirements are mentioned
- User contradicts their own earlier answers (signals unclear mental model)
- FR count exceeds 10 after elicitation

On escalation: all Lite artifacts gathered so far become Expert input. Do NOT restart or announce a disruptive switch — simply begin asking deeper questions (E1 problem framing, E3 walkthrough, etc.).

## Step 1.6: Targeted Codebase Exploration (brownfield only — no user interaction)

**Trigger conditions** (ALL must be true):
1. `docs/rules/` exists AND contains ≥1 `.md` file beyond a greenfield stub (brownfield project)
2. The user's description mentions concrete functionality, a domain area, or a specific module (not too abstract to target)

**Skip if**: greenfield project, OR user description is too vague to derive a focus direction (e.g., "I want to build a platform" with no specifics).

**Execution**:
1. Extract a focus direction from the user's description:
   - Identify domain keywords (e.g., "authentication", "payment", "API gateway", "data pipeline")
   - Infer relevant `--focus` dimensions (e.g., auth → `api,architecture`; data pipeline → `dataflow,deps`)
   - Infer `--path` if the user mentions a specific module or directory
2. Determine exploration depth from context (do NOT hardcode):

   | Signal | Depth adjustment |
   |--------|-----------------|
   | Complexity tier = Lite | Prefer quick (locator only, fast) |
   | Complexity tier = Expert | Prefer standard (full analysis) |
   | User description mentions a single module/area | Keep current or lower (narrow scope = less depth needed) |
   | User description spans multiple subsystems | Bump up one level (broad scope = more context needed) |
   | If `--path` narrows to a small subtree | Keep current or lower |

   When in doubt, omit `--depth` and let explore's LOC-based auto-detection decide (<1K→quick, 1K-10K→standard, >10K→deep).

3. Dispatch `long-task-explore` with context-driven parameters:
   ```
   Agent(
     subagent_type="general-purpose",
     description="Targeted codebase exploration for requirements context",
     prompt="""
     Invoke the long-task:long-task-explore skill with these parameters:
     - Depth: {determined_depth or omit for auto-detect}
     - Focus: {inferred_dimensions}
     - Path: {inferred_path or "."}
     - User question: "{user_description_summary}"
     Execute the skill and return the exploration results.
     """
   )
   ```
4. If explore returns useful findings → incorporate into your mental model for L1/E1 questioning:
   - Reference discovered modules, APIs, data models in your questions (e.g., "I found `src/auth/` with JWT-based authentication — do you want to extend this or replace it?")
   - Use discovered architecture patterns to ask more informed questions about integration points
5. If explore returns BLOCKED or no actionable findings → skip silently, proceed to L1/E1

**This step is non-blocking** — failure or lack of useful results never prevents proceeding to elicitation.

---

## Lite Track

For projects with clear scope, single actor, and well-understood domain. Target: 3–5 interaction rounds.

### L1: Focused Problem & Scope (single AskUserQuestion, ≤4 questions)

1. "What problem does this solve, and what does success look like when it's working?"
2. "Who uses it, and in what environment (desktop/mobile/CLI/API)?"
3. "What is explicitly out of scope for this version?"
4. "Any hard constraints — language, platform, hosting, licenses?"

Output: one-sentence problem statement in SRS Section 1, actor list, scope boundary, constraints.

If the answer to Q1 is vague or problem-oriented → escalation trigger fires → switch to Expert.

### L2: Flat Capability Elicitation (1–3 rounds of ≤4 questions each)

For each capability area, ask per round (up to 4 questions):
- What does the user do? (trigger/action)
- What does the system do in response? (observable behavior)
- What inputs would be invalid, and what should happen?
- Confirm a concrete Given/When/Then example

Group related capabilities into the same round when they share a workflow. Split large capability areas across multiple rounds.

### L3: Quick NFR + Hidden Requirements Check (single AskUserQuestion)

1. "Any performance targets — response time, throughput, data volume?"
2. "Does this handle personal data, face regulations, or need accessibility support? (If yes, which?)"
3. "Multiple languages or timezones?"
4. "Any security requirements beyond basic auth?"

Any YES to Q2 → generate EARS-formatted NFR candidates inline. If Q2 reveals significant regulatory exposure → escalation trigger.

### L4–L6: Classify, Write, Validate, Present, Save

After Lite elicitation, proceed to the **shared steps** (Steps 7–16 in the checklist):
- L4 = Steps 7–8 (classify, EARS, diagrams)
- L5 = Steps 9–11 + Step 13 (validate, granularity, deferral, SRS reviewer with Group P = PASS-SKIPPED)
- L6 = Steps 14–16 (present entire SRS in one block as single approval, save, transition to UCD)

---

## Expert Track

For projects with complex domains, multiple actors, or unclear scope. Target: 10–20 interaction rounds.

### E1: Problem Framing [Expert only]

Read `references/problem-framing.md` and follow it exactly.

**Summary**: Single AskUserQuestion (≤4 questions) — 5-Whys seed, JTBD probe, pain ranking, solution challenge. Produces: 5-Whys chain, JTBD statement, Pain Map → embedded in SRS Section 1.3.

### E2: Enhanced Scope Round [Expert only]

Use slots freed by E1 answers. Single AskUserQuestion (≤4 questions). Replace standard Round 1 questions already answered in E1 with targeted probes:

- **Workaround probe**: "Walk me through the most annoying step in [workaround from Pain Map]. What makes it frustrating — is it manual, error-prone, slow, or opaque?"
  → Every step the user hates in their current workaround is a candidate FR.

- **Environment probe**: "Where and when is this typically done — at a desk with a large screen, on mobile in the field, under time pressure, or shared among a team?"
  → Reveals UX, offline, mobile-first, multi-user, and accessibility constraints.

Plus remaining standard scope questions not yet answered by E1 (out of scope, constraints).

**Rule**: Total questions ≤4. Prioritize probes that surface new information over re-asking what E1 already covered.

### E3: Scenario Walkthrough [Expert only]

Read `references/scenario-walkthrough.md` and follow it exactly.

**Summary**: One walkthrough per major workflow (1–3 workflows). User narrates end-to-end. LLM extracts explicit steps, implicit steps, flow gaps, integration points, error mentions. Follow-up for flow gaps (bounded by extraction count).

### E4: Hypothesis-Correction [Expert only]

Read `references/hypothesis-correction.md` and follow it exactly.

**Summary**: Per FR (or 2–3 related FR group), present Behavior Hypothesis Table with applicable dimensions (selected by FR type). User marks ✓/✗/+. Converges naturally when no new corrections emerge.

### E5: Hidden Requirements [Expert only]

Single AskUserQuestion, checkbox-style (YES/NO + tell me more), ≤4 probes:

1. **Regulatory/Compliance**: "Does this system handle data or processes subject to regulations? (Personal data → GDPR/CCPA; Health → HIPAA; Payments → PCI-DSS; Financial → SOX; Government → sector-specific)"
   - YES → implied NFRs: data residency, audit logging, breach notification timeline, consent management, data retention limits

2. **Accessibility**: "Do any users have accessibility needs — visual impairment, motor limitations, older adults, screen reader users, or keyboard-only navigation? Will this run on mobile?"
   - YES → implied NFRs: WCAG 2.1 AA compliance, keyboard navigability, minimum touch targets (44×44px), sufficient color contrast (4.5:1)

3. **Privacy by design**: "Will the system collect, store, or process personally identifiable information (names, emails, locations, behavioral data, device IDs)?"
   - YES → implied NFRs: data minimization, user-controlled data export/deletion, consent recording, breach response time

4. **Internationalization**: "Will any users interact in a language other than [detected primary], or from a different timezone or locale?"
   - YES → implied NFRs: locale-aware date/time/currency formatting, string externalization (no hardcoded UI text), RTL layout if applicable, timezone-aware storage

**Rule**: Any YES → create an NFR candidate in EARS format before proceeding. Mark with Source = "Hidden (E5)". E6 quantifies thresholds.

**Smart Skip**: If Step 1 context clearly shows a purely internal, no-PII, single-language, non-regulated developer tool → collapse all four probes into one confirmation:
> "This appears to be an internal tool with no personal data, no regulated industry exposure, no accessibility requirements, and no i18n needs — correct?"

### E6–E8: NFR, Constraints, Glossary

Same structure as standard elicitation:

**E6 (NFR Quantification)**: Use the same probes as current Round N+1. Absorb E5 candidates as pre-populated rows — quantify their thresholds.

| Category (ISO 25010) | Probe |
|---|---|
| **Performance** | Response time target? Throughput? Concurrent users? |
| **Reliability** | Uptime target? Recovery time? Data loss tolerance? |
| **Usability** | Accessibility requirements? Learnability criteria? |
| **Security** | Authentication method? Authorization model? Data encryption? |
| **Maintainability** | Modularity constraints? Test coverage targets? |
| **Portability** | Platform restrictions? Browser support? |
| **Scalability** | Current load? Target load? Growth timeline? |

Skip categories clearly irrelevant. **Rule**: Every NFR must have a **measurable criterion**.

**E7 (Constraints & Interfaces)**: Hard limits, assumptions, external system contracts.

**E8 (Glossary)**: Domain terms with potential ambiguity.

### E9: Classify, Write, Validate, Granularity, Deferral

Same as shared Steps 7–11 in the checklist. No differences from standard process.

### E10: Alignment Validation [Expert only]

Read `references/alignment-validation.md` and follow it exactly.

**Summary**: Root cause traceability (Pain Map → FR coverage), JTBD outcome verification (**gate — blocks E11 on failure**), pre-mortem, orphan FR detection. Output → SRS Section 1.3 Alignment Validation field.

### E11: SRS Reviewer, Present, Save

Same as shared Steps 13–16, with two differences:
- SRS reviewer includes **Group P** (active, not PASS-SKIPPED)
- Present section-by-section for non-trivial projects (not single combined approval)

---

## Steps 7–11: Shared Quality Pipeline (both tracks)

### Step 7: Classify Requirements

Organize into categories:

| Category | ID Prefix | Description |
|---|---|---|
| Functional | FR-001 | Observable system behaviors |
| Non-Functional | NFR-001 | Quality attributes with measurable criteria |
| Constraint | CON-001 | Hard limits that restrict the solution space |
| Assumption | ASM-001 | Beliefs assumed true; document invalidation risk |
| Interface | IFR-001 | External system contracts |
| Exclusion | EXC-001 | Explicitly out of scope |

### Step 8: Write Requirements with EARS Templates

Apply the EARS template to each functional requirement:

| Pattern | Template | When to use |
|---|---|---|
| **Ubiquitous** | The system shall `<action>`. | Always-on behavior |
| **Event-driven** | When `<trigger>`, the system shall `<action>`. | Response to event |
| **State-driven** | While `<state>`, the system shall `<action>`. | Behavior depends on mode/state |
| **Unwanted behavior** | If `<condition>`, then the system shall `<action>`. | Error handling, fault tolerance |
| **Optional** | Where `<feature/config>`, the system shall `<action>`. | Configurable capability |

For each requirement, also write:
- **Acceptance criteria** — at least one concrete Given/When/Then scenario
- **Visual output** (if ui-facing) — one sentence describing what the user sees change (rendering intent, not rendering specification). E.g., "The snake's position on the game board updates visually after each tick." Write "N/A — backend-only" for FRs with no user-visible output. This field gives downstream phases (Feature Design, TDD) explicit visual language to derive rendering contracts from.
- **Priority** — Must / Should / Could / Won't (MoSCoW)
- **Source** — which stakeholder need or user story this traces to

#### 8c. Generate Diagrams

After all requirements are written, generate visual aids:

**Use Case View** (Section 3.1): `graph LR` with all actors as `Actor((Name))`, all FR-xxx as use case nodes inside `subgraph System Boundary`, directed edges per actor-to-use-case participation.

**Process Flows** (Section 4.1): One `flowchart TD` per functional area with 3+ sequential steps or branching. Start/End as `([label])`, decisions as `{condition?}` with `-- YES -->` / `-- NO -->` labels.

### Step 9: Validate SRS Quality

#### 9a. Per-Requirement Checks (8 quality attributes)

| # | Attribute | Check | Red flag |
|---|---|---|---|
| 1 | **Correct** | Traces to a confirmed stakeholder need? | Orphan requirement (gold-plating) |
| 2 | **Unambiguous** | Two readers would write the same test case? | Weasel words: "fast", "robust", "user-friendly" |
| 3 | **Complete** | All inputs, outputs, error cases, boundaries defined? | "including but not limited to..." |
| 4 | **Consistent** | No contradiction with other requirements? | Timing conflicts, format conflicts |
| 5 | **Ranked** | Has a MoSCoW priority? | Everything is "high priority" |
| 6 | **Verifiable** | Can write a pass/fail test? | "The system shall be easy to use" |
| 7 | **Modifiable** | Stated in exactly one place? | Duplicated across sections |
| 8 | **Traceable** | Has unique ID + source link? | Missing ID or orphan |

#### 9b. Anti-Pattern Detection

| Anti-Pattern | Detection Signal | Fix |
|---|---|---|
| **Ambiguous adjective** | "fast", "large", "scalable" without number | Quantify |
| **Compound requirement** | "and" / "or" joining two capabilities | Split |
| **Design leakage** | "class", "table", "endpoint" | Rewrite as behavior |
| **Passive without agent** | "data shall be validated" — by whom? | Add actor |
| **TBD / TBC** | Unresolved placeholders | Resolve or Open Question |
| **Missing negatives** | Only positive cases specified | Add error/boundary cases |
| **Untestable NFR** | NFR without measurable threshold | Add metric |

#### 9c. Completeness Cross-Check

- Every functional area has at least one error/boundary case
- All external interfaces have data format + protocol
- All NFRs have measurement method, not just target
- Glossary covers all domain-specific terms
- Out-of-Scope section lists deferred features

### Step 10: Granularity Analysis — Bidirectional Sizing

Right-size each FR for one Worker session. Apply both over-size (G) and under-size (S) heuristics. The goal: each FR should produce a feature that productively uses ~50% of the model's context window.

**Step 10.0 — Select your sizing profile:** You know your own maximum context window. Apply the matching row to all G/S decisions below.

| Context window | Profile | Target ACs per FR | Single-feature implementation scope |
|---|---|---|---|
| ≤ 200K tokens | **Standard** | 3-12 | ~200-600 lines code + tests |
| > 200K tokens | **Extended** | 5-20 | ~500-3000 lines code + tests |

An FR below the profile minimum AC count is under-sized (S-heuristic candidate). An FR above the profile maximum is over-sized (G-heuristic candidate).

**Phase 1 — Over-size detection (G1-G6):** Split FRs that are too coarse for a single session.

| # | Heuristic | Detection Signal |
|---|---|---|
| G1 | **Multiple actors** | 2+ distinct roles performing different actions |
| G2 | **CRUD bundle** | Create + Read + Update + Delete as single requirement |
| G3 | **Scenario explosion** | 4+ acceptance criteria covering distinct behavioral paths |
| G4 | **Cross-layer concern** | Backend logic AND user-facing UI in one FR |
| G5 | **Multi-state behavior** | 3+ distinct system states or modes |
| G6 | **Temporal coupling** | Trigger event + deferred/scheduled consequence |

For decomposition candidates: identify atomic behaviors, apply Single Responsibility Test, preserve traceability (FR-003 → FR-003a, FR-003b), re-validate children.

**Phase 2 — Under-size detection (S1-S4):** Group FRs that are too trivial for a dedicated session.

| # | Heuristic | Detection Signal | Action |
|---|---|---|---|
| S1 | **Trivial addition** | Single field/constant/config, no behavioral logic, ≤1 AC | Group with parent entity/endpoint FR |
| S2 | **Single-assertion test** | Only 1 AC with no error/boundary cases | Enrich with error/boundary ACs, or group with related FR sharing same entity/endpoint |
| S3 | **Pure data echo** | Displays/returns data another FR produces, no transformation | Group with the producing FR as vertical slice |
| S4 | **Config/setup only** | Env setup, dependency install, scaffolding, no business logic | Group all S4 FRs into single Foundation FR |

**Grouping rules:**
- Grouped FRs keep the primary FR's ID; description notes "Incorporates: [list]"
- Combined ACs must stay ≤ 20 (if exceeds, G3 re-triggers — split along better seams)
- Grouped FRs must share primary actor and functional area
- If both G and S trigger on the same FR: G wins (split first, then S re-checks children)

**Decision thresholds:**

| Candidate Count (G or S) | Action |
|---|---|
| 0 | Skip |
| 1-3 | Auto-apply; present rationale inline |
| 4+ | Present to user via AskUserQuestion for approval |

### Step 11: Scope Fit & Deferral

Assess whether all requirements belong in the current round. Apply scope fit criteria (Priority, Dependency, Completeness, Risk, Scope budget). Present deferral recommendations to user. If deferrals approved, generate `docs/plans/YYYY-MM-DD-<topic>-deferred.md`.

Rules:
- Must-priority FRs are NEVER auto-deferred
- Dependency integrity — if FR-X depends on FR-Y, both stay
- Deferred backlog preserves EARS + acceptance criteria for increment pickup

---

## Step 13: SRS Compliance Review

Dispatch a subagent to independently verify the SRS:

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are an SRS compliance reviewer aligned with ISO/IEC/IEEE 29148.
  Read the reviewer prompt at: skills/long-task-requirements/prompts/srs-reviewer-prompt.md

  Project context:
  {project_context}

  Full SRS draft (all sections):
  {srs_draft}

  Requirement ID list:
  {requirement_id_list}

  Perform the review following the prompt exactly.
  """
)
```

**ALL checks must PASS to proceed:**
- Group R (R1-R8): quality attributes
- Group A (A1-A6): anti-patterns
- Group C (C1-C5): completeness
- Group S (S1-S4): structural compliance
- Group D (D1-D4): diagrams
- Group G (G1-G3): granularity (over-size detection)
- Group Z (Z1-Z3): sizing (under-size detection)
- Group P (P1-P4): problem alignment (Expert track; PASS-SKIPPED for Lite track)

**On FAIL — two-track resolution:**

**Track 1: USER-INPUT items → ask immediately**

Use `AskUserQuestion` with a targeted questionnaire — do NOT dump the full review report.

**Track 2: LLM-FIXABLE items → auto-fix**

Fix all LLM-FIXABLE items in parallel. Re-dispatch reviewer (Cycle 2).

**Maximum: 2 re-dispatch cycles.** After Cycle 2 failure → escalate to user.

## Steps 14–16: Present, Save, Transition

### Step 14: Present & Approve SRS

- **Lite track**: Present entire SRS in one block. Single approval step.
- **Expert track (< 5 FR)**: Combined approval step.
- **Expert track (≥ 5 FR)**: Section by section:
  1. Purpose, Scope, Problem Statement & Exclusions
  2. Glossary & User Personas
  3. Functional Requirements
  4. Non-Functional Requirements
  5. Constraints, Assumptions & Interfaces

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

### Step 15: Save SRS Document & Deferred Backlog

Save to `docs/plans/YYYY-MM-DD-<topic>-srs.md`.

Read the template found in Step 1:
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved SRS content
3. Add metadata at top if not already present (`Date`, `Status`, `Standard`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

If a deferred backlog was generated in Step 11, save alongside: `docs/plans/YYYY-MM-DD-<topic>-deferred.md`. Commit both.

### Step 16: Transition to UCD

1. Summarize key inputs for the next phase
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ucd`

---

## Scaling Table

| Tier | Signals | Typical FR Count | Elicitation Depth | Approval |
|---|---|---|---|---|
| **Lite** | <3 Expert signals | 1–10 | L1-L3 (flat rounds, merged NFR) | Combined single step |
| **Expert (Small)** | ≥3 Expert signals | 5–15 | E1-E5 (1–2 walkthroughs, grouped hypothesis) | 2–3 sections |
| **Expert (Medium)** | ≥3 Expert signals | 15–50 | E1-E5 (2–3 walkthroughs, per-FR hypothesis) | Per-section |
| **Expert (Large)** | ≥3 Expert signals | 50–200+ | E1-E5 (3–5 walkthroughs, batched hypothesis) | Per-section |

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "This is too simple for an SRS" | Lite track IS the simple path. It produces a short SRS in 3–5 rounds. |
| "The user already described what they want" | User descriptions are raw input; SRS adds structure, completeness, testability |
| "I can figure out the requirements during design" | Requirements define WHAT; discovering them during HOW causes rework |
| "NFRs don't apply to this project" | Every project has at least implicit performance/reliability needs — make them explicit |
| "The glossary is obvious" | Obvious to whom? Define every term the user and developer might interpret differently |
| "I'll just start with the happy path" | Error cases, boundaries, and negatives must be captured NOW |
| "This FR is fine as one big requirement" | Apply the 6 over-size heuristics (G1-G6) — hidden complexity creates oversized features |
| "This FR is small but clear — leave it" | Apply the 4 under-size heuristics (S1-S4) — trivially small FRs waste full pipeline sessions on fixed overhead |
| "All requirements belong in this round" | Scope fit assessment ensures focus — defer lower-priority items |
| "Deferred items can just go in Out-of-Scope" | Out-of-Scope is prose; deferred backlog preserves EARS + acceptance criteria |
| "This is complex but I'll use Lite to save time" | Complexity assessment exists for a reason. If ≥3 Expert signals fired, use Expert. |
| "Skip the walkthrough, I have enough FRs" | Walkthroughs find cross-capability gaps that per-FR questioning misses |
| "The hypothesis table has too many dimensions" | Select dimensions by FR type (5 rows for read-only, 7 for data entry). Not all 8. |
| "Accessibility doesn't apply to this project" | Any user interface has accessibility implications. WCAG 2.1 AA is the baseline. |
| "We'll handle GDPR/privacy in design" | Privacy requirements must be in the SRS. Data model and consent flows depend on them. |
| "Expert path is too many rounds, skip some steps" | Every Expert step prevents downstream rework. If the project is truly simpler, it should be Lite. |

## Integration

**Called by:** using-long-task (when no SRS doc, no design doc, and no feature-list.json)
**Chains to:** long-task-ucd (after SRS approval; auto-skips to design if no UI features)
**References:** `references/problem-framing.md`, `references/scenario-walkthrough.md`, `references/hypothesis-correction.md`, `references/alignment-validation.md`
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-srs.md`, optionally `docs/plans/YYYY-MM-DD-<topic>-deferred.md`
