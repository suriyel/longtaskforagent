# Hypothesis-Correction Execution Protocol

## When This Runs

Expert track Step E4. Called by SKILL.md after Scenario Walkthrough (E3).

## Purpose

Fill in every FR's boundaries, error handling, permissions, and data lifecycle — without asking open-ended questions. The LLM proactively derives concrete behavioral assumptions and presents them for user confirmation/correction, rather than asking the user to imagine edge cases from scratch.

## Core Mechanism

For each FR (or group of 2–3 related FRs), the LLM **derives concrete behavioral assumptions** from all available context (walkthrough narrative, domain knowledge, Pain Map, Step 1 context). These are presented as a structured **Behavior Hypothesis Table** for the user to confirm (✓), correct (✗), or supplement (+).

## Behavior Hypothesis Table Format

Present via AskUserQuestion:

> "Based on your walkthrough, here's what I assume about **[FR title]**. Please mark each row: ✓ correct, ✗ wrong (tell me what's right), or + add something I missed."

| # | Dimension | My Assumption | ✓/✗/+ |
|---|---|---|---|
| 1 | **Happy path** | When [trigger], the system [action], resulting in [outcome] | |
| 2 | **Invalid input** | If [specific invalid input], the system [assumed error behavior, e.g., shows inline error, rejects silently, auto-corrects] | |
| 3 | **Boundary** | Maximum [N items / file size / characters] is [assumed limit]; beyond that [assumed behavior] | |
| 4 | **Failure path** | If [external dependency] is unavailable, the system [assumed fallback: retry / queue / show error / degrade gracefully] | |
| 5 | **Permission** | Only [assumed roles] can perform this; unauthorized users see [assumed behavior: 403 / hidden button / redirect] | |
| 6 | **Concurrency** | If two users simultaneously [action], [assumed conflict resolution: last-write-wins / lock / merge / queue] | |
| 7 | **Data lifecycle** | Data created by this action is [retained forever / expires after X / user-deletable / admin-archivable] | |
| 8 | **Negative scope** | This FR does NOT [assumed exclusion — something the user might expect but is out of scope] | |

**Each assumption must be concrete and specific**, not generic. Bad: "If invalid input, the system shows an error." Good: "If the email field contains no @ sign, the system shows an inline error below the field and prevents submission."

## FR Type Definitions & Dimension Selection

Not all 8 dimensions apply to every FR. Select based on FR type:

| FR Type | Definition | Include Dimensions | Skip Dimensions |
|---|---|---|---|
| **Read-only display** | Shows data to the user without modifying state | 1, 3, 4, 5 | 2 (no input), 6 (no write), 7 (no data creation) |
| **Data entry / form** | User submits new data or edits existing data | 1, 2, 3, 4, 5, 7 | 6 (unless multi-user editing is likely) |
| **State-changing action** | Triggers a state transition (approve, cancel, publish, delete) | 1, 2, 4, 5, 6, 7 | 3 (unless batch processing) |
| **Background process** | Runs without direct user interaction (cron job, queue consumer, sync) | 1, 4, 7 | 2, 3, 5, 6 (no direct user interaction) |
| **Integration / API** | Sends or receives data from an external system | 1, 3, 4, 8 | 5 (unless user-facing), 6, 7 |

**Always include dimension 8 (negative scope)** for complex FRs where the boundary between "in scope" and "out of scope" is ambiguous.

## Batching Rules

- Group 2–3 closely related FRs per AskUserQuestion when they share a workflow or data model
- If a single FR needs all 8 dimensions, present it alone
- Prefer fewer FRs with more dimensions over many FRs with fewer — depth over breadth per round

## Convergence Mechanism

The hypothesis-correction protocol is **self-terminating** without any hard cap:

- ✓ (confirmed) → assumption is correct, no further action
- ✗ (corrected) → LLM updates the FR with the user's correction
- \+ (added) → user adds a dimension the LLM missed → new acceptance criterion (or a new FR if the addition describes a distinct capability)

**When no new ✗ or + corrections emerge across all FRs, hypothesis-correction is complete.** There are no open-ended follow-up questions, no "anything else?" probes — the table structure exhausts the behavioral dimensions by design.

If a ✗ correction reveals significant new complexity (e.g., "actually, there are three different approval workflows depending on the amount"), treat the correction as a trigger for a new sub-FR and run another hypothesis table for the newly discovered sub-FR.

## Output Per Row

| User Mark | Becomes |
|---|---|
| ✓ confirmed happy path | EARS statement for the FR |
| ✓ or ✗ boundary/error/permission/concurrency/lifecycle | Given/When/Then acceptance criterion |
| + added dimension | New acceptance criterion for the FR, or a new candidate FR if it describes a distinct capability |
| ✓ confirmed dimension 8 (negative scope) | EXC-xxx exclusion entry |

## Quality Check

After all hypothesis tables are complete, verify:
- Every FR has at least one error/boundary acceptance criterion (satisfies existing A6 anti-pattern check)
- Every FR with external dependencies has a failure-path specified
- Every FR with user input has an invalid-input handling specified
