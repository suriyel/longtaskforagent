# Problem Framing Execution Protocol

## When This Runs

Expert track Step E1. Called by SKILL.md. Do NOT run in Lite track.

## E1a. Derive from Context (internal, no user interaction)

Before asking anything, derive from the user's initial description:
- Draft a one-sentence problem statement
- List the actors whose lives change if the system is built
- Hypothesize 2–3 current-state pain points
- Flag if the user stated a **solution** ("build me X") rather than a **problem** ("I can't do Y") — solution-anchored requests must be challenged in E1b

## E1b. Problem Framing Round (single AskUserQuestion, ≤4 questions)

Adapt phrasing to project context. Skip any question whose answer is already unambiguously clear from Step 1 context.

1. **5-Whys seed**: "What goes wrong today without this system? Walk me through a real recent example — what happened, what did you have to do instead, and what was the cost (time, money, errors, frustration)?"
   - Derive the WHY chain internally from the answer (up to 3 levels). Stop at the deepest cause supported by the user's answer. Do NOT invent causes beyond what was stated or clearly implied.

2. **JTBD probe**: "What outcome are you ultimately trying to achieve — not the tool you want, but what success looks like in your world?"
   - Target answer shape: "I want to [motivation] so I can [outcome]"
   - If the answer is still solution-shaped ("I want a dashboard"), follow up once: "And what does having that let you do that you can't do today?"

3. **Pain ranking**: "Of the problems you described, which one costs you the most — and how often does it happen? (daily / weekly / monthly)"
   - Accept qualitative ranking; do NOT force numbers the user doesn't have.

4. **Solution challenge** *(only ask if the user proposed a specific solution in their original description)*: "Is that the only way to solve this, or would you also be satisfied if [JTBD outcome] was achieved some other way?"
   - Purpose: detect when the user is anchored on a particular implementation when a simpler solution would satisfy the JTBD.
   - If the user has NOT proposed a specific solution, skip this question entirely.

## E1c. Build Artifacts (internal, no further user questions)

From the answers, produce three artifacts to be embedded in SRS Section 1.3:

**5-Whys Chain**:
```
Symptom: [user-stated problem in their words]
Why 1: [first cause]
Why 2: [cause of Why 1]
Why 3: [deepest supported cause — stop here unless answer goes further]
Root Cause: [systemic cause that requirements must address]
```
Stop at the deepest WHY supported by the user's answer. Mark the stopping point.

**JTBD Statement**:
```
When [situation], I want to [motivation], so I can [outcome].
```
Construct from the user's JTBD probe answer. Use their words as much as possible.

**Pain Map**:
| Pain Point | Current Workaround | Frequency | Severity (H/M/L) | Score (F×S) |
|---|---|---|---|---|
| [pain 1] | [what they do today] | Daily/Weekly/Monthly | H/M/L | 3/2/1 × 3/2/1 |

Score: Frequency (Daily=3, Weekly=2, Monthly=1) × Severity (H=3, M=2, L=1). Highest scores = highest-priority pain to address.

## E1d. Internal Checkpoint

Before proceeding to E2, verify: can you state **WHY** the system needs to exist, **WHO** suffers most from the current state, and **WHAT** the minimum outcome is that would constitute success — without guessing?

- **YES** → proceed to E2
- **NO** → open one more targeted AskUserQuestion to resolve the gap

## Output

All three artifacts → written into SRS Section 1.3 (Problem Statement).
These feed:
- E2 (workaround probe uses Pain Map)
- E3 (walkthrough workflows derived from Pain Map)
- E10 (alignment validation checks backward from Pain Map and JTBD)
