# Systematic Debugging

## Iron Law

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Never apply a fix based on a guess. Always trace the bug to its root cause, then fix that cause.

## When This Applies

- Test failure during TDD Green or Refactor
- Regression detected during testing
- Runtime error during functional testing
- Build or environment failure during Bootstrap
- Any unexpected behavior during implementation

## Four-Phase Debugging Process

### Phase 1: Root Cause Investigation

**Goal**: Understand WHAT is happening and WHERE.

1. **Collect error evidence**:
   - Read the full error message (not just the first line)
   - Note the stack trace — which file, which line, which function
   - Record the exact command/action that triggered the error

2. **Reproduce reliably**:
   - Can you trigger the error consistently?
   - What is the minimal reproduction case?
   - Does it happen in isolation or only with other features?

3. **Check recent changes**:
   - `git diff` — what changed since it last worked?
   - `git log --oneline -10` — what commits were made?
   - Did the error exist before your current changes?

4. **Trace data flow**:
   - Follow the failing input from entry point to error location
   - Log intermediate values if needed
   - Identify where actual behavior diverges from expected behavior

### Phase 2: Pattern Analysis

**Goal**: Understand WHY it's happening.

1. **Find working examples**:
   - Is there similar code that works correctly?
   - What's different between the working and broken paths?

2. **Check dependencies**:
   - Are all dependencies available and correct versions?
   - Did an upstream API or schema change?
   - Are environment variables / configs correct?

3. **Compare contexts**:
   - Does it work locally but fail in tests (or vice versa)?
   - Does it work with one input but fail with another?
   - Is it timing-dependent (race condition)?

### Phase 3: Hypothesis & Testing

**Goal**: Form ONE hypothesis and validate it.

1. **Form a single hypothesis**:
   - "The error occurs because X is null when Y expects it to be non-null"
   - Be specific — vague hypotheses lead to vague fixes

2. **Design a minimal test**:
   - What's the smallest change that would confirm or disprove the hypothesis?
   - Can you add a targeted assertion or log?

3. **Test the hypothesis**:
   - Make ONLY the diagnostic change
   - Run the failing test
   - Did the hypothesis hold?

4. **If hypothesis was wrong**:
   - Record what you learned
   - Return to Phase 1 with new information
   - Do NOT try random fixes

### Phase 4: Implementation

**Goal**: Fix the root cause with a verified solution.

1. **Write a failing test for the bug**:
   - The test should fail for the same reason as the original bug
   - This prevents regression

2. **Implement a single, targeted fix**:
   - Fix only the root cause identified in Phase 3
   - Avoid "while I'm here" changes

3. **Verify the fix**:
   - The new test passes
   - All existing tests still pass
   - The original error no longer occurs

4. **If fix doesn't work after 3 attempts**:
   - Stop and reconsider the root cause
   - You may have misidentified it
   - Consider asking the user for help or context

## Supporting Techniques

### Root Cause Tracing

Trace bugs backward through the call stack:

```
Error at line N in file F
  ← Called from line M in file G
    ← Called from line K in file H
      ← Root cause: incorrect value set at line K in file H
```

Work backward from the error to find where the wrong value was introduced.

### Defense in Depth

After fixing a root cause, consider adding validation at multiple layers:

```
Layer 1: Input validation     → Reject bad data early
Layer 2: Function preconditions → Assert expected state
Layer 3: Output verification   → Confirm correct results
```

Only add validation that serves a purpose — don't add defensive code for impossible states.

### Condition-Based Waiting (for timing bugs)

Replace arbitrary timeouts with condition polling:

```
# BAD: sleep(5) and hope the server is ready
# GOOD: Poll until condition is met or timeout expires

wait_for("Expected text", timeout=10000)
```

For non-UI timing bugs:
```python
# Poll with backoff
for attempt in range(max_retries):
    result = check_condition()
    if result:
        break
    time.sleep(backoff * attempt)
else:
    raise TimeoutError("Condition not met")
```

### Test Pollution Detection

When a test passes in isolation but fails when run with the suite, another test is polluting shared state.

Binary search approach:
1. Run failing test with first half of the suite → still fails?
2. If yes → polluter is in the first half; bisect again
3. If no → polluter is in the second half; bisect again
4. Repeat until the single polluting test is found
5. Fix the polluter (cleanup its shared state)

## Red Flags (Stop and Reconsider)

| Red Flag | What It Signals | Correct Response |
|----------|----------------|-----------------|
| "Let me just try this quick fix" | Skipping root cause analysis | Go back to Phase 1 |
| "It's probably X, let me change it" | Guessing without evidence | Form a testable hypothesis |
| "I'll add a try/catch to suppress the error" | Hiding symptoms, not fixing cause | Find and fix the root cause |
| "Let me restart everything and try again" | Hoping the problem goes away | Reproduce reliably first |
| "This worked before, not sure what changed" | Need to check git diff | Compare current state with last known good |
| Third fix attempt still failing | Wrong root cause identified | Stop, reassess from Phase 1 |

## Debugging Decision Tree

```
Error encountered
  │
  ├─ Can reproduce? ─── No ──→ Add logging, try again
  │                              (make it reproducible first)
  ├─ Yes
  │
  ├─ Recent change caused it? ─── Yes ──→ git diff, focus on changes
  │
  ├─ No / Unknown
  │
  ├─ Trace to root cause ──→ Found cause? ─── Yes ──→ Write test → Fix → Verify
  │
  ├─ No
  │
  ├─ Find working example ──→ Compare differences ──→ Form hypothesis
  │
  └─ Hypothesis holds? ─── Yes ──→ Write test → Fix → Verify
                          No ──→ Record learning → Return to trace
```
