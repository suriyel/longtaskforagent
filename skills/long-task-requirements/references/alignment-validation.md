# Alignment Validation Execution Protocol

## When This Runs

Expert track Step E10. Called by SKILL.md after Classify/Write/Validate/Granularity/Deferral (E9), before SRS Reviewer (E11).

## Purpose

Backward validation: given the SRS as written, does it actually solve the root problem identified in E1? This step catches the most dangerous form of requirements failure — a formally correct SRS that addresses the wrong problem.

This is an internal check. No user interaction unless specific failures require it.

## E10a. Root Cause Traceability Check

For EACH row in the Pain Map (from E1, stored in Section 1.3):

1. Find at least one FR in Section 4 whose EARS statement or acceptance criteria addresses this pain point
2. If a pain point has no addressing FR → check if it appears in Section 1.2 Out-of-Scope with an explicit exclusion reason
3. If a pain point is neither addressed nor excluded → this is a **traceability gap**

For the 5-Whys Root Cause (from E1):

1. Verify that at least one FR directly addresses the root cause (not just a symptom)
2. If the root cause is unaddressed → flag as a traceability gap

**On traceability gaps**:
- 1–2 gaps: auto-resolve by either creating a new minimal FR or adding an explicit Out-of-Scope entry (choose whichever requires less new elicitation)
- 3+ gaps: use `AskUserQuestion` presenting the gap table and asking which gaps should become new FRs vs. explicit exclusions

## E10b. JTBD Outcome Verification

Locate the JTBD statement from E1 (stored in Section 1.3).

Check: "If a user completes every Must-priority FR in Section 4, does that achieve the JTBD 'so I can [outcome]'?"

- **YES** → proceed
- **NO** → identify which part of the JTBD outcome is uncovered. Present the gap to the user via AskUserQuestion:
  > "Your stated goal is '[JTBD outcome]'. The current requirements don't fully cover [missing aspect]. Should I add a requirement for this, or is the current scope sufficient?"
  - User wants to add → create a new FR, return to E9 for classification
  - User confirms the current scope is sufficient → record as **PARTIAL**, proceed

**Gate**: JTBD verification blocks E11 until resolved. Acceptable outcomes:
- **PASS** — JTBD fully achievable
- **PARTIAL** — user explicitly confirmed current scope is sufficient despite incomplete JTBD coverage

FAIL (unresolved JTBD gap without user confirmation) cannot proceed to E11.

## E10c. Pre-Mortem

LLM self-assessment (no user interaction unless findings are non-trivial):

> "If we build everything in the SRS as written, what could still leave the user unsatisfied?"

Check against:
- Workaround probe answers from E2 — was every frustrating step in the current workaround addressed by at least one FR?
- Scenario walkthrough narratives from E3 — were all extracted flow gaps resolved in the final FR list?
- Hidden requirements from E5 — did every YES answer become an explicit NFR?
- Pain Map items — are any only partially addressed (workaround eliminated but root cause remains)?

For each pre-mortem finding:
- Should be an FR → add it (return to E9 for classification)
- Should be an NFR → add it
- Known risk but not actionable now → add to Section 11 Open Questions

## E10d. Orphan FR Detection (Gold-Plating Check)

For each FR in Section 4, check if it has a traceable origin:
- Linked to a Pain Map row (addresses a stated pain point)
- Linked to the JTBD outcome (needed to achieve the stated goal)
- Sourced from a walkthrough step (E3 extraction)
- Sourced from Hidden Requirements (E5)

If an FR has **no traceable origin** from any of the above sources:
- Check if any other FR depends on it (infrastructure/utility FRs are often necessary without direct pain point linkage)
- If no dependency exists → flag in Section 11 Open Questions:
  > "FR-xxx has no traceable pain point or JTBD link — confirm in scope or defer to a future increment."

Do **NOT** auto-remove orphan FRs. Surfacing them for user awareness is the action.

## Output

Write the alignment validation result into SRS Section 1.3:

```
**Alignment Validation**: PASS / PARTIAL / FAIL
- Root cause coverage: N of M pain points addressed
- JTBD outcome: achieved / partially achieved (user-confirmed) / not achieved
- Pre-mortem findings: N items added / 0 items found
- Orphan FRs flagged: N items in Open Questions / 0
```

**PARTIAL** (with user-confirmed JTBD) is acceptable and does not block E11.
**FAIL** on JTBD (E10b) without user confirmation blocks E11 until resolved.
