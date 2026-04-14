---
name: long-task-multi-repo
description: "Use when repos-manifest.json exists - handles multi-repo exploration, global SRS elicitation, per-repo SRS split, and dependency distribution. Fully independent from single-repo pipeline."
---

**LANGUAGE RULE**: You MUST respond to the user in Chinese (Simplified). All generated documents, reports, and user-facing output must be written in Chinese. Skill names, code identifiers, and JSON field names remain in English.

# Multi-Repo Requirements Elicitation, SRS Split & Dependency Distribution

Turn raw ideas into a structured, high-quality Software Requirements Specification (SRS) for a multi-repo project. Explores all repos, elicits global requirements through systematic questioning (ISO/IEC/IEEE 29148 + EARS), splits the approved SRS into per-repo documents, and distributes all dependency files so each repo can work independently.

Adapts depth automatically: **Lite track** for clear-scope projects (3–5 rounds), **Expert track** for complex domains (10–20 rounds). Both produce the same SRS template output.

<HARD-GATE>
Do NOT invoke any design skill, implementation skill, write any code, scaffold any project, or take any design/implementation action until you have completed the full pipeline: global SRS approved → split → dependencies distributed → handoff summary presented.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need an SRS"

Every project goes through this process. "Simple" multi-repo projects are where unexamined cross-repo assumptions cause the most wasted work. The SRS can be short, but you MUST present it and get approval.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Explore project context** — read existing docs, code, constraints at project root; detect SRS template
2. **Multi-repo exploration** — explore each repo via `long-task-explore`, identify inter-repo relationships, confirm topology with user
3. **Targeted codebase exploration** (brownfield only) — focused explore with context-driven parameters; dedup with Step 2
4. **Complexity assessment** — evaluate 5 signals, select Lite or Expert track (internal)
5. **Problem & scope elicitation** — Lite: L1 / Expert: E1+E2; include cross-repo interaction probes
6. **Functional requirements elicitation** — Lite: L2 / Expert: E3+E4; annotate repo ownership per capability
7. **NFR + hidden requirements** — Lite: L3 / Expert: E5+E6
8. **Constraints, assumptions, glossary** — same for both tracks
9. **Classify requirements** — functional / NFR / constraint / assumption / interface / exclusion
10. **Write requirements + repo annotation** — EARS templates, repo ownership annotation, diagrams
11. **Validate SRS** — 8 quality attributes, anti-patterns, testability
12. **Granularity analysis** — bidirectional sizing (G1-G6 split, S1-S4 merge)
12b. **FR granularity confirmation** — present finalized FR list; dedicated user approval of split/merge rationality
12c. **Single-round mode confirmation** — offer single-round mode (all FRs in wave 0); decision applies globally to all per-repo pipelines
13. **Scope fit & deferral** — assess current-round vs next-round, deferred backlog
14. **[Expert only] Alignment validation** — via `references/alignment-validation.md`
15. **SRS Compliance Review** — dispatch srs-reviewer subagent; gate: all checks PASS
16. **Present & approve global SRS** — Lite: single block; Expert: section-by-section
17. **Save global SRS & backlog** — `docs/plans/YYYY-MM-DD-<topic>-srs.md` at project root + deferred backlog
18. **Split global SRS into per-repo SRS** — group FRs by repo, split cross-repo FRs, generate per-repo SRS + IFRs
19. **Distribute dependency files** — copy reference docs, global SRS, deferred backlog, cross-repo deps to each sub-repo
20. **Handoff** — present summary with cross-repo deps + dev order, end session

**Terminal state: session ends after handoff.** No chaining to design — user independently cd's into each repo.

---

## Re-entry Guard

Before starting Step 1, check if the SRS split was already completed in a previous session:

1. Read `repos-manifest.json` → check if `cross_repo_deps` field exists (set by Step 18)
2. Check if any repo in the manifest already has a per-repo SRS at `<repo_path>/docs/plans/*-srs.md`

If **both** conditions are true → SRS split was already done. **Skip directly to Step 20 (Handoff)** — present the summary and remind the user to cd into each repo.

If only the global SRS exists (`docs/plans/*-srs.md` at project root) but no per-repo SRS → **skip to Step 18 (Split)** — split the existing global SRS, then continue to Steps 19-20.

If no global SRS exists → proceed normally from Step 1.

---

## Step 1: Explore Project Context

1. Read the user-provided requirement doc / idea description thoroughly
2. Scan for existing documentation at project root:
   - `docs/plans/` — any prior SRS, design docs
   - `docs/rules/` — codebase conventions (brownfield)
   - Root-level reference files (*.md, *.pdf, *.json, *.yaml) — user-provided specs, API docs, etc.
3. If `docs/rules/` has populated `.md` files beyond a greenfield stub → note as brownfield. Record:
   - `coding-style.md` — language conventions
   - `mandatory-libraries.md` — required internal libraries (2/3方件 constraints)
   - `prohibited-apis.md` — banned APIs
   - `build-and-compilation.md` — build system and CI/CD constraints
   - These constraints may affect requirement feasibility and should be considered during elicitation
4. Check for an SRS template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/srs-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 2: Multi-Repo Exploration

**Trigger**: `repos-manifest.json` exists in project root (this skill is only invoked when it does).

**Execution**:
1. Read `repos-manifest.json` → get repo list (name, path)
2. For each repo, dispatch `long-task-explore` to build context:
   ```
   Agent(
     subagent_type="general-purpose",
     description="Explore repo: {repo_name}",
     prompt="""
     Invoke the long-task:long-task-explore skill with these parameters:
     - Path: {repo_path}
     - Depth: (omit — let explore auto-detect based on LOC)
     - Focus: architecture,api,deps
     Execute the skill and return the exploration results.
     """
   )
   ```
   > Depth is NOT hardcoded — explore's Step 2 Project Detection auto-selects (quick/standard/deep) based on LOC.
   > Dispatch all repos in parallel when possible.
3. Record per-repo profile: language, framework, architecture patterns, API surface, entry points
4. Identify inter-repo relationships:
   - Shared dependencies / packages (e.g., common internal library)
   - API contracts between repos (e.g., backend exposes REST, frontend consumes)
   - Shared database / message queue / event bus
   - Shared configuration or environment (e.g., same Docker network)
5. Present multi-repo topology summary to user for confirmation via `AskUserQuestion`:
   - Repo count and names
   - Detected tech stack per repo
   - Inter-repo relationships
   - Ask: "以上多仓库拓扑是否正确？是否有遗漏的仓库或关系？"

This step is **non-blocking** — if explore fails for a repo, log a warning and proceed with whatever context was gathered.

The multi-repo topology informs all subsequent elicitation rounds: questions should probe which repo a requirement belongs to, and specifically ask about cross-repo interactions.

## Step 3: Targeted Codebase Exploration (brownfield only — no user interaction)

**Trigger conditions** (ANY of these):
1. `docs/rules/` exists AND contains ≥1 `.md` file beyond a greenfield stub (brownfield project), AND the user's description mentions concrete functionality, a domain area, or a specific module
2. The user's description mentions concrete functionality — explore each repo with inferred focus

**Skip if**: user description is too vague to derive a focus direction (e.g., "I want to build a platform" with no specifics).

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

3. **Dedup with Step 2**: If Step 2 already explored a repo, reuse those findings instead of re-dispatching explore for the same repo. Only dispatch explore for repos where the inferred focus dimensions differ significantly from what Step 2 used (`architecture,api,deps`), or where Step 2 failed/returned no findings.

   For repos that need fresh exploration, dispatch in parallel:
   ```
   For each repo in repos-manifest.json (not already covered by Step 2):
     Agent(
       subagent_type="general-purpose",
       description="Targeted exploration: {repo_name}",
       prompt="""
       Invoke the long-task:long-task-explore skill with these parameters:
       - Path: {repo_path}
       - Depth: {determined_depth or omit for auto-detect}
       - Focus: {inferred_dimensions}
       - User question: "{user_description_summary}"
       Execute the skill and return the exploration results.
       """
     )
   ```

4. Integrate findings into your understanding — merge with Step 2 results per repo
5. Reference discovered modules, APIs, data models in your questions (e.g., "I found `src/auth/` with JWT-based authentication in the backend repo — do you want to extend this or replace it?")
6. If explore returns BLOCKED or no actionable findings → skip silently, proceed

**This step is non-blocking** — failure or lack of useful results never prevents proceeding to elicitation.

## Step 4: Complexity Assessment (internal — no user interaction)

Evaluate 5 complexity signals against the user's description and project context:

| # | Signal | Lite indicator | Expert indicator |
|---|---|---|---|
| S1 | **Stated scope** | Single purpose, clear boundary ("a script that does X") | Vague/broad scope ("a platform for managing...", "a system that...") |
| S2 | **Actor count** | 1 actor or no user-facing interaction | 2+ distinct user roles mentioned |
| S3 | **Integration surface** | No external systems, or 1 well-known API | 2+ external systems, custom protocols |
| S4 | **Domain complexity** | Developer tool, utility, well-understood domain | Business domain with jargon, regulatory exposure, multi-stakeholder |
| S5 | **Description style** | Solution-specific ("build X using Y") | Problem-oriented or vague ("we need better X", "users complain about Y") |

**≥3 Expert signals → Expert track. Otherwise → Lite track.**

> **Multi-repo note**: Multi-repo projects naturally escalate complexity signals — multiple repos often imply 2+ actors (S2) and 2+ integration points (S3). Account for this but don't auto-force Expert solely because of multi-repo topology.

**Escalation triggers** (if detected later → switch to Expert immediately):
- Answer to Problem/Scope question reveals domain jargon, regulatory requirements, or multi-stakeholder conflict
- FR count exceeds 10 after elicitation

On escalation: all Lite artifacts gathered so far become Expert input. Do NOT restart or announce a disruptive switch — simply begin asking deeper questions.

---

## Lite Track

For projects with clear scope, single actor, and well-understood domain. Target: 3–5 interaction rounds.

### L1: Focused Problem & Scope (single AskUserQuestion, ≤4 questions)

1. "What problem does this solve, and what does success look like when it's working?"
2. "Who uses it, and in what environment (desktop/mobile/CLI/API)?"
3. "What is explicitly out of scope for this version?"
4. "Any hard constraints — language, platform, hosting, licenses?"

> **Multi-repo addition**: If the user's answers don't clarify cross-repo scope, add a follow-up: "各仓库之间如何协作？哪些功能是跨仓库的？" (How do the repos collaborate? Which features span multiple repos?)

Output: one-sentence problem statement in SRS Section 1, actor list, scope boundary, constraints.

If the answer to Q1 is vague or problem-oriented → escalation trigger fires → switch to Expert.

### L2: Flat Capability Elicitation (1–3 rounds of ≤4 questions each)

For each capability area, ask per round (up to 4 questions):
- What does the user do? (trigger/action)
- What does the system do in response? (observable behavior)
- What inputs would be invalid, and what should happen?
- Confirm a concrete Given/When/Then example

Group related capabilities into the same round when they share a workflow. Split large capability areas across multiple rounds.

> **Multi-repo addition**: For each capability, probe repo ownership: "这个功能主要由哪个仓库负责？是否涉及跨仓库交互？" (Which repo owns this? Does it involve cross-repo interaction?)

### L3: Quick NFR + Hidden Requirements Check (single AskUserQuestion)

1. "Any performance targets — response time, throughput, data volume?"
2. "Does this handle personal data, face regulations, or need accessibility support? (If yes, which?)"
3. "Multiple languages or timezones?"
4. "Any security requirements beyond basic auth?"

Any YES to Q2 → generate EARS-formatted NFR candidates inline. If Q2 reveals significant regulatory exposure → escalation trigger.

### L4–L6: Classify, Write, Validate, Present, Save

After Lite elicitation, proceed to the **shared steps** (Steps 9–17 in the checklist):
- L4 = Steps 9–10 (classify, EARS + repo annotation, diagrams)
- L5 = Steps 11–12b–12c–13 + Step 15 (validate, granularity, granularity confirmation, single-round mode confirmation, deferral, SRS reviewer with Group P = PASS-SKIPPED)
- L6 = Steps 16–17 (present entire SRS in one block as single approval, save)

Then proceed to **Steps 18–20** (split, distribute, handoff).

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

> **Multi-repo addition**: "各仓库目前的职责划分是什么？是否存在职责重叠或不清晰的地方？" (What are the current responsibilities of each repo? Any overlap or ambiguity?)

Plus remaining standard scope questions not yet answered by E1 (out of scope, constraints).

**Rule**: Total questions ≤4. Prioritize probes that surface new information over re-asking what E1 already covered.

### E3: Scenario Walkthrough [Expert only]

Read `references/scenario-walkthrough.md` and follow it exactly.

**Summary**: One walkthrough per major workflow (1–3 workflows). User narrates end-to-end. LLM extracts explicit steps, implicit steps, flow gaps, integration points, error mentions. Follow-up for flow gaps (bounded by extraction count).

> **Multi-repo addition**: During extraction, mark each step with the repo it belongs to. When a step crosses repo boundaries (e.g., "frontend calls backend API"), extract it as a candidate IFR (Interface Requirement).

### E4: Hypothesis-Correction [Expert only]

Read `references/hypothesis-correction.md` and follow it exactly.

**Summary**: Per FR (or 2–3 related FR group), present Behavior Hypothesis Table with applicable dimensions (selected by FR type). User marks check/cross/plus. Converges naturally when no new corrections emerge.

### E5: Hidden Requirements [Expert only]

Single AskUserQuestion, checkbox-style (YES/NO + tell me more), ≤4 probes:

1. **Regulatory/Compliance**: "Does this system handle data or processes subject to regulations? (Personal data → GDPR/CCPA; Health → HIPAA; Payments → PCI-DSS; Financial → SOX; Government → sector-specific)"
   - YES → implied NFRs: data residency, audit logging, breach notification timeline, consent management, data retention limits

2. **Accessibility**: "Do any users have accessibility needs — visual impairment, motor limitations, older adults, screen reader users, or keyboard-only navigation? Will this run on mobile?"
   - YES → implied NFRs: WCAG 2.1 AA compliance, keyboard navigability, minimum touch targets (44x44px), sufficient color contrast (4.5:1)

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

Same as shared Steps 9–13 (including Step 12b granularity confirmation and Step 12c single-round mode confirmation) in the checklist. No differences from standard process.

### E10: Alignment Validation [Expert only]

Read `references/alignment-validation.md` and follow it exactly.

**Summary**: Root cause traceability (Pain Map → FR coverage), JTBD outcome verification (**gate — blocks E11 on failure**), pre-mortem, orphan FR detection. Output → SRS Section 1.3 Alignment Validation field.

### E11: SRS Reviewer, Present, Save

Same as shared Steps 15–17, with two differences:
- SRS reviewer includes **Group P** (active, not PASS-SKIPPED)
- Present section-by-section for non-trivial projects (not single combined approval)

Then proceed to **Steps 18–20** (split, distribute, handoff).

---

## Steps 9–13: Shared Quality Pipeline (both tracks)

### Step 9: Classify Requirements

Organize into categories:

| Category | ID Prefix | Description |
|---|---|---|
| Functional | FR-001 | Observable system behaviors |
| Non-Functional | NFR-001 | Quality attributes with measurable criteria |
| Constraint | CON-001 | Hard limits that restrict the solution space |
| Assumption | ASM-001 | Beliefs assumed true; document invalidation risk |
| Interface | IFR-001 | External system contracts (includes cross-repo interfaces) |
| Exclusion | EXC-001 | Explicitly out of scope |

### Step 10: Write Requirements with EARS Templates + Repo Annotation

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
- **Priority** — Must / Should / Could / Won't (MoSCoW)
- **Source** — which stakeholder need or user story this traces to

#### 10a. Repo Annotation

For each FR/NFR, annotate which repo it belongs to:
- **Repo**: `backend` — single-repo requirement
- **Repo**: `backend, frontend` — cross-repo requirement
- **Cross-repo note**: (for cross-repo only) describe the inter-repo interaction, e.g., "Backend provides REST API `/auth/login`; Frontend consumes it"

This annotation is used in Step 18 to split the global SRS into per-repo SRS documents. If a requirement spans multiple repos, it will be split into separate per-repo FRs linked by dependencies and IFR contracts.

#### 10b. Generate Diagrams

After all requirements are written, generate visual aids:

**Use Case View** (Section 3.1): `graph LR` with all actors as `Actor((Name))`, all FR-xxx as use case nodes inside `subgraph System Boundary`, directed edges per actor-to-use-case participation.

**Process Flows** (Section 4.1): One `flowchart TD` per functional area with 3+ sequential steps or branching. Start/End as `([label])`, decisions as `{condition?}` with `-- YES -->` / `-- NO -->` labels.

**Multi-repo interaction diagram**: One `graph LR` showing repos as subgraphs, with cross-repo IFR edges.

### Step 11: Validate SRS Quality

#### 11a. Per-Requirement Checks (8 quality attributes)

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

#### 11b. Anti-Pattern Detection

| Anti-Pattern | Detection Signal | Fix |
|---|---|---|
| **Ambiguous adjective** | "fast", "large", "scalable" without number | Quantify |
| **Compound requirement** | "and" / "or" joining two capabilities | Split |
| **Design leakage** | "class", "table", "endpoint" | Rewrite as behavior |
| **Passive without agent** | "data shall be validated" — by whom? | Add actor |
| **TBD / TBC** | Unresolved placeholders | Resolve or Open Question |
| **Missing negatives** | Only positive cases specified | Add error/boundary cases |
| **Untestable NFR** | NFR without measurable threshold | Add metric |

#### 11c. Completeness Cross-Check

- Every functional area has at least one error/boundary case
- All external interfaces have data format + protocol
- All NFRs have measurement method, not just target
- Glossary covers all domain-specific terms
- Out-of-Scope section lists deferred features
- **All cross-repo interfaces have both provider and consumer sides documented**

### Step 12: Granularity Analysis — Bidirectional Sizing

Right-size each FR for one Worker session. Apply both over-size (G) and under-size (S) heuristics. The goal: each FR should produce a feature that productively uses ~50% of the model's context window. As a concrete sizing target, each FR should produce approximately 1,000 lines of implementation code (excluding unit test code).

**Multi-repo sizing basis**: The ~1,000 LOC target refers to the **per-repo implementation** of a single FR, not the combined total across all repos. For cross-repo FRs (annotated with multiple repos), estimate the LOC for each repo's portion independently — if any repo's portion falls below ~500 LOC, the FR is an under-size candidate for that repo after Step 18 split. For single-repo FRs, the target applies directly.

**Step 12.0 — Select your sizing profile:** You know your own maximum context window. Apply the matching row to all G/S decisions below.

| Context window | Profile | Target ACs per FR | Single-feature implementation scope |
|---|---|---|---|
| ≤ 200K tokens | **Standard** | 3-12 | ~1,000 lines implementation code per repo (excluding UT) |
| > 200K tokens | **Extended** | 5-20 | ~1,000 lines implementation code per repo (excluding UT) |

An FR below the profile minimum AC count is under-sized (S-heuristic candidate). An FR above the profile maximum is over-sized (G-heuristic candidate). When the AC-based heuristic is ambiguous, estimate the likely implementation LOC **per repo**: an FR producing significantly fewer than ~1,000 lines in its target repo is a merge candidate; significantly more is a split candidate.

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

**Phase 2 — Under-size detection (S1-S4):** Merge FRs that are too trivial for a dedicated session.

| # | Heuristic | Detection Signal | Action |
|---|---|---|---|
| S1 | **Trivial addition** | Single field/constant/config, no behavioral logic, ≤1 AC | Merge into parent entity/endpoint FR |
| S2 | **Single-assertion test** | Only 1 AC with no error/boundary cases | Enrich with error/boundary ACs, or merge into related FR sharing same entity/endpoint |
| S3 | **Pure data echo** | Displays/returns data another FR produces, no transformation | Merge into the producing FR as vertical slice |
| S4 | **Config/setup only** | Env setup, dependency install, scaffolding, no business logic | Merge all S4 FRs into a single Foundation FR |

**Merge rules:**
- **Content preservation (mandatory)**: the absorbed FR's EARS statement, all acceptance criteria, and description text are fully integrated into the primary FR — no requirement content may be lost or summarized away. The primary FR's description and AC list must contain the complete union of both FRs' content.
- The absorbed FR entry is then eliminated from the SRS. After all merges, re-number FR IDs sequentially (FR-001, FR-002, ...) and update all SRS cross-references (Use Case View, Process Flows, Traceability Matrix).
- Combined ACs must stay ≤ 20 (if exceeds, G3 re-triggers — split along better seams)
- Merged FRs must share primary actor and functional area
- If both G and S trigger on the same FR: G wins (split first, then S re-checks children)

**Decision thresholds:**

| Candidate Count (G or S) | Action |
|---|---|
| 0 | Skip |
| 1-3 | Auto-apply; present rationale inline |
| 4+ | Present to user via AskUserQuestion for approval |

Note: All granularity changes (auto-applied or user-approved) are subject to the holistic FR granularity confirmation in Step 12b.

### Step 12b: FR Granularity Confirmation

After all G1-G6 splits, S1-S4 merges, and FR ID re-numbering, present the finalized FR list for dedicated user confirmation.

**Content preservation check (before presenting):** For every merged FR, verify that the primary FR now contains the complete union of EARS statements and acceptance criteria from all absorbed FRs. No original requirement content may be lost.

**Present via AskUserQuestion:**

1. Show the complete FR list in table format:
   | FR ID | Title | AC Count | Est. Impl. LOC | Changed? | Notes |
   |-------|-------|----------|----------------|----------|-------|
   - "Changed?" column: "split from FR-XXX" / "absorbed FR-YYY" / "unchanged"
   - "Est. Impl. LOC" column: rough estimate targeting ~1,000 lines **per repo** (excluding UT). For cross-repo FRs, show per-repo breakdown (e.g., "backend: ~800, frontend: ~400")
   - For merged FRs, list which original FRs were absorbed so user can verify completeness

2. Ask: "Please review the FR list above. Each FR targets ~1,000 lines of implementation code per repo (excluding unit tests). For cross-repo FRs, per-repo LOC breakdowns are shown — portions below ~500 LOC may be merged after Step 18 split. All merged FRs retain the complete requirement content of the absorbed FRs. Confirm the granularity is appropriate, or indicate which FRs should be further split, merged, or adjusted."

3. Process response:
   - **Confirmed** → proceed to Step 12c
   - **Adjustment requested** → apply changes, re-number IDs, re-present (loop until confirmed)

**Mandatory for both Lite and Expert tracks.** Even if Step 12 produced 0 granularity candidates (no splits or merges), present the FR list for confirmation — the user may identify granularity issues the heuristics missed.

### Step 12c: Single-Round Mode Confirmation

After FR granularity confirmation, present via `AskUserQuestion`:

> "The finalized FR list contains {N} functional requirement(s).
>
> **Single-round mode available**: All FRs will be implemented in this development round (wave 0) without deferral. Each FR maps to one feature; the Worker processes one feature per session. All pipeline steps (feature-design, TDD, quality gates, feature-ST) run normally — no steps are skipped.
>
> **Multi-repo scope**: This decision applies at the global SRS level. When the global SRS is split into per-repo SRS documents (Step 18), each per-repo SRS inherits `Single-Round: Yes` — all per-repo pipelines will set `single_round: true` in their `feature-list.json` and skip deferral analysis.
>
> **Context overflow risk**: If any single FR is estimated to exceed ~1,000 lines of implementation code (excluding unit tests), consider splitting it further (return to Step 12).
>
> [Enable single-round mode] / [Skip — proceed to deferral analysis]"

Process response:
- **Enable** → record `Single-Round: Yes` in the global SRS document metadata header. Step 13 (Scope Fit & Deferral) still executes but presents a confirmation summary instead of deferral recommendations — user has declared intent to implement all FRs in this round.
- **Skip** → proceed to Step 13 normally (full deferral analysis).

**Mandatory for both Lite and Expert tracks.**

### Step 13: Scope Fit & Deferral

Assess whether all requirements belong in the current round. Apply scope fit criteria (Priority, Dependency, Completeness, Risk, Scope budget). Present deferral recommendations to user. If deferrals approved, generate `docs/plans/YYYY-MM-DD-<topic>-deferred.md`.

Rules:
- Must-priority FRs are NEVER auto-deferred
- Dependency integrity — if FR-X depends on FR-Y, both stay
- Deferred backlog preserves EARS + acceptance criteria for increment pickup

**Single-round mode behavior**: If `Single-Round: Yes` was recorded in Step 12c, this step still executes but replaces deferral recommendations with a confirmation summary: list all FRs, confirm all are assigned to wave 0, and present for user acknowledgment. No FRs are deferred.

---

## Step 15: SRS Compliance Review

Dispatch a subagent to independently verify the SRS:

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are an SRS compliance reviewer aligned with ISO/IEC/IEEE 29148.
  Read the reviewer prompt at: skills/long-task-multi-repo/prompts/srs-reviewer-prompt.md

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

## Steps 16–17: Present, Save

### Step 16: Present & Approve Global SRS

- **Lite track**: Present entire SRS in one block. Single approval step.
- **Expert track (< 5 FR)**: Combined approval step.
- **Expert track (≥ 5 FR)**: Section by section:
  1. Purpose, Scope, Problem Statement & Exclusions
  2. Glossary & User Personas
  3. Functional Requirements (with repo annotations)
  4. Non-Functional Requirements
  5. Constraints, Assumptions & Interfaces

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

### Step 17: Save Global SRS Document & Deferred Backlog

Save to `docs/plans/YYYY-MM-DD-<topic>-srs.md` at project root.

Read the template found in Step 1:
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved SRS content
3. Add metadata at top if not already present (`Date`, `Status`, `Standard`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

If a deferred backlog was generated in Step 13, save alongside: `docs/plans/YYYY-MM-DD-<topic>-deferred.md`. Commit both.

---

## Step 18: Split Global SRS into Per-Repo SRS

**Execution**:

1. **Group FRs by repo annotation** (from Step 10a):
   - Single-repo FRs → directly assigned to target repo
   - Cross-repo FRs → split into per-repo independent FRs:
     a. Original FR is preserved in the global SRS, marked: "Split: FR-001a (backend), FR-001b (frontend)"
     b. Each child FR inherits the relevant portion of the original FR's acceptance criteria
     c. Child FRs are linked via `dependencies` in their respective per-repo SRS
     d. For each cross-repo boundary, create an IFR (Interface Requirement) documenting the contract:
        - API endpoint / message format / shared data schema
        - Dependency repo name: "Depends on: {repo_name}"
   - NFRs: if repo-specific, assign to that repo; if global (e.g., "system response time < 200ms"), copy to all repos

2. **Generate per-repo SRS documents**:
   For each repo in `repos-manifest.json`:
   a. `mkdir -p <repo_path>/docs/plans/`
   b. Write `<repo_path>/docs/plans/YYYY-MM-DD-<topic>-srs.md`:
      - Copy global SRS header sections (Purpose, Scope, Glossary) — adapted for this repo's context
      - Include only this repo's FRs, NFRs, CONs, ASMs
      - Add `## Interface Requirements` section: list all cross-repo IFRs with dependency repo names
      - Add metadata header: `Global SRS Reference: docs/plans/global-srs.md`
      - If global SRS metadata contains `Single-Round: Yes`, propagate to per-repo SRS metadata header: `Single-Round: Yes`
   c. If deferred backlog exists, copy applicable items to `<repo_path>/docs/plans/YYYY-MM-DD-<topic>-deferred.md`

3. **Per-repo codebase rules**: Do NOT invoke `long-task-codebase-scanner` here.
   When the user later starts a session in a sub-repo, the router's brownfield detection will invoke `long-task-codebase-scanner` for that repo if `<repo_path>/docs/rules/` does not exist yet. This avoids duplicate scanning.

4. **Update `repos-manifest.json`**:
   ```json
   {
     "detected": "2026-04-08T12:00:00Z",
     "project_root_is_git": false,
     "repos": [
       {"name": "backend", "path": "backend"},
       {"name": "frontend", "path": "frontend"}
     ],
     "global_srs": "docs/plans/2026-04-08-myproject-srs.md",
     "cross_repo_deps": [
       {
         "from_fr": "FR-001a",
         "from_repo": "backend",
         "to_fr": "FR-001b",
         "to_repo": "frontend",
         "interface": "REST API /auth/login"
       }
     ]
   }
   ```

5. **Per-repo granularity re-check** — after splitting, each repo's FR set may contain under-sized child FRs that were properly sized at the global level but became too small after split. For each repo:

   a. List the repo's FRs with **per-repo LOC estimates** (not global totals)
   b. Apply S1-S4 under-size heuristics within the repo's FR set:
      - Child FRs estimated below ~500 LOC are merge candidates with other FRs in the **same repo**
      - S-heuristic merge rules apply identically to Step 12 (content preservation mandatory, combined ACs ≤ 20, same actor/functional area)
   c. If merges are applied:
      - Re-number per-repo FR IDs sequentially
      - Update per-repo SRS cross-references and IFR dependency links
      - Update `repos-manifest.json` cross_repo_deps entries accordingly
   d. Skip this step if the repo has only 1 FR (nothing to merge into)

6. **Commit** (if project root has git) or skip if no root-level git

7. **Present split summary** to user for confirmation via `AskUserQuestion`:
   - Per-repo FR list with per-repo LOC estimates (table format per repo)
   - Cross-repo dependencies and interface contracts
   - Any merges applied in step 5 with rationale
   - Ask: "各仓库 SRS 拆分结果是否正确？是否需要调整？"

## Step 19: Distribute Dependency Files

After SRS split is confirmed, distribute all reference and dependency files to each sub-repo so they can work fully independently.

### 19a. Copy user-provided reference documents

Scan project root for user-added reference files:
- `docs/` directory contents **excluding** `docs/plans/` (which are generated artifacts)
- Root-level reference files: `*.md`, `*.pdf`, `*.json`, `*.yaml`, `*.yml` that are NOT generated artifacts (`repos-manifest.json`, `feature-list.json`, `task-progress.md`, `RELEASE_NOTES.md`, `long-task-guide.md`, `env-guide.md`)

For each repo:
1. `mkdir -p <repo_path>/docs/references/`
2. Copy identified reference files to `<repo_path>/docs/references/`
3. If a reference file is clearly repo-specific (by name containing the repo name, or by content), only copy to that repo; otherwise copy to all repos

### 19b. Copy global SRS + deferred backlog

For each repo:
1. Copy the global SRS → `<repo_path>/docs/plans/global-srs.md`
2. If deferred backlog exists → copy to `<repo_path>/docs/plans/global-deferred.md`
3. The per-repo SRS metadata header `Global SRS Reference` already points to `docs/plans/global-srs.md` (local copy)

### 19c. Generate per-repo cross-repo dependency summary

For each repo:
1. Extract entries from `cross_repo_deps` in `repos-manifest.json` where this repo appears as `from_repo` or `to_repo`
2. Write `<repo_path>/docs/plans/cross-repo-deps.md`:
   ```markdown
   # Cross-Repo Dependencies: {repo_name}

   ## This repo provides (as interface provider)

   | IFR | Consumer Repo | Interface | Related FR |
   |-----|--------------|-----------|------------|
   | IFR-001 | frontend | REST API POST /auth/login | FR-001a |

   ## This repo consumes (as interface consumer)

   | IFR | Provider Repo | Interface | Related FR |
   |-----|--------------|-----------|------------|
   | IFR-002 | backend | REST API GET /users | FR-003b |

   ## Development Order Note

   - Complete provider interfaces before consumer implementations
   - If this repo is a consumer: ensure provider repo's interface is stable before integration testing
   ```
3. Add `## Cross-Repo Dependencies` section to the per-repo SRS, referencing `cross-repo-deps.md`:
   > "详见 [cross-repo-deps.md](cross-repo-deps.md) 获取本仓库的跨仓库接口依赖详情。"

### 19d. Add Reference Documents section to per-repo SRS

Append `## Reference Documents` section to each per-repo SRS:
```markdown
## Reference Documents

- [Global SRS](global-srs.md) — 全局需求规格说明书（完整版）
- [Global Deferred Backlog](global-deferred.md) — 全局延迟需求积压（如存在）
- [Cross-Repo Dependencies](cross-repo-deps.md) — 本仓库跨仓库接口依赖
- `docs/references/` — 用户提供的参考文档
```

## Step 20: Handoff

Present a structured handoff summary to the user:

1. **Per-repo summary table**:
   | Repo | FR Count | Key Requirements | Distributed Files |
   |------|----------|-----------------|-------------------|
   | backend | 8 | Auth, Data API, ... | SRS, global-srs, cross-repo-deps, 2 ref docs |
   | frontend | 6 | UI, Dashboard, ... | SRS, global-srs, cross-repo-deps, 2 ref docs |

2. **Cross-repo dependency summary** (from `repos-manifest.json` `cross_repo_deps`):
   - List each interface contract with provider and consumer repos
   - Recommended development order: "建议先完成 {provider_repo}（提供接口方），再进行 {consumer_repo}（消费接口方）。"

3. **Distributed files per repo**:
   ```
   <repo>/docs/plans/
   ├── YYYY-MM-DD-<topic>-srs.md       # 本仓库独立 SRS
   ├── YYYY-MM-DD-<topic>-deferred.md  # 延迟需求（如有）
   ├── global-srs.md                    # 全局 SRS 副本
   ├── global-deferred.md               # 全局延迟需求副本（如有）
   └── cross-repo-deps.md              # 跨仓库接口依赖
   <repo>/docs/references/
   └── *.md / *.pdf / ...              # 用户参考文档
   ```

4. **Instructions**:
   "全局 SRS 已完成并拆分为各仓库独立 SRS。所有参考文档、全局 SRS、跨仓库依赖信息已复制到各子仓库的 docs/ 目录下。"
   "请分别 cd 到各仓库目录，独立启动新 session 执行后续流程（Design → ATS → Init → Worker → ST）。"
   If cross-repo deps exist: "存在跨仓库依赖，建议先完成接口提供方仓库，再处理接口消费方仓库。具体依赖关系见上方摘要。"

5. **End session** — do NOT invoke any other skill.

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
| "Skip the walkthrough, I have enough FRs" | Walkthroughs find cross-capability gaps that per-FR questioning misses |
| "Cross-repo interfaces will be figured out during design" | IFR contracts must be in the SRS — design depends on stable interface specifications |

## Integration

**Called by:** using-long-task (when `repos-manifest.json` exists)
**Chains to:** nothing — session ends with handoff (user independently navigates to each repo)
**References:** `references/problem-framing.md`, `references/scenario-walkthrough.md`, `references/hypothesis-correction.md`, `references/alignment-validation.md`, `prompts/srs-reviewer-prompt.md`
**Produces:** global SRS (`docs/plans/YYYY-MM-DD-<topic>-srs.md`), per-repo SRS, per-repo dependency files, updated `repos-manifest.json`
