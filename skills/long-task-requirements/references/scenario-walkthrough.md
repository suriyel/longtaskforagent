# Scenario Walkthrough Execution Protocol

## When This Runs

Expert track Step E3. Called by SKILL.md after Problem Framing (E1) and Enhanced Scope (E2).

## Purpose

Discover macro-level flow gaps, integration points, and implicit sequencing before drilling into individual FRs. Question-based elicitation per capability misses cross-capability requirements — walkthroughs expose them by forcing the user to narrate the full journey.

## How Many Walkthroughs

One walkthrough per major workflow. Determine major workflows from Pain Map top items and E2 answers.

| Expert Scale | Walkthroughs |
|---|---|
| Small (5–15 FR) | 1–2 |
| Medium (15–50 FR) | 2–3 |
| Large (50–200+ FR) | 3–5 (one per epic/domain) |

## Walkthrough Prompt (one AskUserQuestion per workflow)

> "Walk me through a complete [workflow name] from start to finish. Start from the moment you decide to [trigger]. Tell me each step you'd take, what the system should show or do at each point, and where you'd stop. Include what happens when things go wrong."

Adapt the trigger to the specific workflow. Examples:
- "...from the moment you need to onboard a new employee..."
- "...from the moment a customer places an order..."
- "...from the moment you notice an anomaly in the data..."

## LLM Extraction (internal, no user interaction)

For each narrative answer, extract and categorize:

| Category | What to look for | Example | Action |
|---|---|---|---|
| **Explicit steps** | Direct statements of desired system behavior | "I click 'Submit' and the system saves the record" | → candidate FR |
| **Implicit steps** | Actions the user glosses over or considers "obvious" | "then I'd log in" (implies authentication) | → candidate FR, flagged for confirmation in follow-up |
| **Flow gaps** | Transitions where the user jumped ahead without explaining the mechanism | "then the report appears" (how? triggered manually? auto-generated? scheduled?) | → targeted follow-up question |
| **Integration points** | Mentions of external systems, data sources, hand-offs to other tools | "I export it to Salesforce" | → candidate IFR |
| **Error mentions** | Any reference to failures, exceptions, or recovery | "sometimes the API times out" | → candidate acceptance criterion for the relevant FR |

## Flow Gap Follow-up (single AskUserQuestion per workflow, if gaps exist)

If the extraction produced flow gaps or implicit steps needing confirmation, ask in a single follow-up:

> "In your walkthrough of [workflow], I noticed a few points I want to confirm:
> 1. Between [step A] and [step B], how does [transition] happen — does the user trigger it, or does the system do it automatically?
> 2. You mentioned [vague step] — what exactly should the screen show at that point?
> 3. When [error mention] happens, what's the expected recovery path?"

Adapt the number of questions to the number of gaps. If no gaps were found, skip the follow-up entirely.

## Output

- **Candidate FR list** with provenance (which walkthrough, which step, explicit vs implicit)
- **Candidate IFR list** from integration points
- **Candidate acceptance criteria** from error mentions

All outputs feed Hypothesis-Correction (E4) — each candidate FR gets a Behavior Hypothesis Table in the next step.

## Convergence

This step is bounded by:
- Number of major workflows (finite, determined before walkthroughs begin)
- User narrative length (finite — the user stops when the story ends)
- Flow gap follow-up count (finite, deterministic list from extraction)

No open-ended "what else?" or "anything I missed?" questions. The walkthrough structure itself is exhaustive for its scope.
