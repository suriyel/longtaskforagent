# Feature-Level Detailed Design — SubAgent Execution Reference

You are a Feature Design execution SubAgent. Follow these rules exactly. When finished, return your result using the **Structured Return Contract** at the bottom of this document.

---

# Feature-Level Detailed Design

Produce a detailed design for a single feature, bridging system-level design (§4.N) and TDD implementation.

System design answers "WHAT classes exist and HOW they interact."
This skill answers "WHAT each method does internally, WHAT can go wrong, and HOW to test it."

## Inputs

Read ALL of these BEFORE writing any design content:

1. **Feature object** from feature-list.json — ID, title, description, srs_trace, ui flag, dependencies, priority (verification_steps if present)
2. **System design section** — full §4.N from the design document (read the entire subsection, NOT grep)
3. **SRS requirement** — full FR-xxx from the SRS document
4. **UCD sections** (if `"ui": true`) — component/page prompts from the UCD document
5. **Constraints & assumptions** from feature-list.json root
6. **Related NFRs** — NFR-xxx from SRS traceable to this feature
7. **Existing code** — if dependency features are passing, read their public interfaces (imports, class/function signatures)
8. **Internal API contracts** (if §6.2 exists) — from Design Section 6.2, read rows where this feature appears as Provider or Consumer. These define cross-feature schemas that this feature's Interface Contract (§3) must align with.

## Template

Use `skills/long-task-feature-design/references/feature-design-template.md` as the structural template. Copy the template, fill each section for the target feature.

## Checklist

You MUST complete each step in order:

### 1. Load Context

Read all input artifacts listed in Inputs above.

### 2. Component Data-Flow Diagram

Show THIS feature's internal components and how data flows between them at runtime. This is NOT a copy of the system design class diagram — it is a **runtime data-flow view** showing what data enters, how it transforms, and what exits.

Requirements:
- Mermaid `graph` or `flowchart` format
- Label edges with data types (what flows between components)
- Include external dependencies as dashed-border boxes
- Every component maps to a class or module to be implemented

> **Skip rule**: If the feature is a single class with a single method and no internal component collaboration, write "N/A — single-class feature, see Interface Contract below"

### 3. Interface Contract

For each PUBLIC method this feature exposes or modifies:

| Method | Signature | Preconditions | Postconditions | Raises |
|--------|-----------|---------------|----------------|--------|
| name   | full typed signature | what must be true before call | what is guaranteed after call | exception + condition |

Rules:
- Preconditions use Given/When style from SRS acceptance criteria
- Postconditions are specific and testable (not "returns correct result")
- Every SRS acceptance criterion (from srs_trace requirements) must trace to at least one method's postcondition
- Include internal methods only if they contain non-trivial logic
- **§6.2 alignment rule**: For methods that produce or consume cross-feature data, the method signature (parameters, return type) MUST be compatible with the schema defined in Design Section 6.2. If the feature is a **Provider**, postconditions MUST guarantee the Response Schema. If a **Consumer**, preconditions MUST assume the Request Schema format. Any deviation requires explicit justification in Design Rationale and triggers the Contract Deviation Protocol below.

### Contract Deviation Protocol

If during feature design, a §6.2 contract is found to be incorrect, insufficient, or technically infeasible:

1. **DO NOT silently deviate** — a mismatched contract will cause integration failures
2. **Record the deviation** in the design document's Design Rationale section:
   - Contract ID (e.g., IAPI-001)
   - Original schema vs. proposed change
   - Technical reason for the change
   - Impact on Consumer features (list affected feature IDs)
3. **Set Verdict to BLOCKED** with Issue: "Contract deviation requires design update"
4. The orchestrator (long-task-work) will escalate to user via AskUserQuestion
5. If approved: user updates §6.2 in the design doc; orchestrator re-dispatches SubAgent
6. If rejected: SubAgent must conform to the original contract

### 3b. Visual Rendering Contract (mandatory for `"ui": true`)

For features with `"ui": true`, specify ALL visual elements the user must see. This contract is the source of truth for TDD Rule 7 (positive rendering tests) and Feature-ST (rendering verification).

**Source data**: Read the SRS requirement's `Visual output` field (what the user sees change) + the UCD component/page prompts (how it should look) + the system design §4.N UI/UX approach.

**How to fill each column**:
- **Visual Element**: name each distinct visual thing the user sees (e.g., "snake body segments", "game board grid", "score counter", "food item"). NOT abstract concepts like "the UI" or "the page".
- **DOM/Canvas Selector**: a concrete CSS selector (`canvas#game-board`, `div.snake-segment`, `#score-display`) or canvas element ID. Must be specific enough for `document.querySelector()` to find it.
- **Rendered When**: the trigger that causes this element to appear (page load, game start, state change, user action)
- **Visual State Variants**: different visual appearances based on state (alive=green, dead=red; selected=blue border, unselected=grey)
- **Minimum Dimensions**: expected size (20x20px per cell, full viewport width, etc.)
- **Data Source**: what data drives the rendering (GameState.segments[], API response, form input)

**Positive rendering assertions**: for each element, write a testable statement of what MUST be visually present after the trigger. Not "element is visible" but "canvas has non-transparent pixels in the game board region" or "div.snake-segment count equals GameState.segments.length".

**Interactive depth assertions**: for each interactive element, write what interaction it responds to and what visual change results. A rendered element that doesn't respond to its designed interaction is a "display-only" defect.

> **Skip rule**: Write "N/A — backend-only feature" ONLY if `"ui": false`. If `"ui": true`, this section is mandatory and cannot be skipped — even for features that seem "mostly backend" but have `"ui": true"`.

### 4. Internal Sequence Diagram

Show method-to-method calls WITHIN this feature's implementation. Unlike the system design's sequence diagram (system-wide flow), this shows the feature's own classes/functions collaborating.

Requirements:
- Mermaid `sequenceDiagram` format
- Must cover the main success path
- Must cover at least one error path per Raises entry in Interface Contract
- Participants are the feature's OWN classes/functions

> **Skip rule**: If the feature has only one class with no internal cross-method delegation worth diagramming, write "N/A — single-class implementation, error paths documented in Algorithm §5 error handling table"

### 5. Algorithm / Core Logic

For each non-trivial method (anything beyond simple delegation or CRUD):

**a) Flow diagram** (Mermaid `flowchart TD`):
- Decision nodes for every branching condition
- Process nodes for transformations
- Terminal nodes for return/raise

**b) Pseudocode**:
```
FUNCTION name(param1: Type, param2: Type) -> ReturnType
  // Step 1: [major step]
  // Step 2: [formula or key decision]
  //         e.g., score = Σ 1/(k + rank_i) for each list
  // Step 3: [edge case handling]
  //         IF input_list is empty THEN return []
  RETURN result
END
```

**c) Boundary decisions table**:

| Parameter | Min | Max | Empty/Null | At boundary |
|-----------|-----|-----|------------|-------------|
| [param]   | [val] | [val] | [behavior] | [behavior] |

**d) Error handling table**:

| Condition | Detection | Response | Recovery |
|-----------|-----------|----------|----------|
| [condition] | [how detected] | [exception or default] | [caller action] |

> **Skip rule**: If a method is pure delegation (calls another service, returns result), write "Delegates to [X] — see Feature #N" instead of a full algorithm section. An empty section without explicit skip is a defect.

### 6. State Diagram (if applicable)

For features that manage stateful objects (entities with lifecycle):

- Mermaid `stateDiagram-v2` format
- All valid states and transitions
- Transition triggers (events/method calls)
- Guard conditions on transitions

> **Skip rule**: Write "N/A — stateless feature" if no object lifecycle exists. Most query/transform features are stateless.

### 7. Test Inventory

Build this table as the FINAL design step — it synthesizes all sections above into concrete test scenarios.

| ID | Category | Traces To | Input / Setup | Expected | Kills Which Bug? |
|----|----------|-----------|---------------|----------|-----------------|
| A  | FUNC/happy | FR-xxx AC-1 | [specific values] | [exact result] | [wrong impl] |
| B  | FUNC/error | §3 Raises row | [trigger] | [exception type + msg] | [missing branch] |
| C  | BNDRY/edge | §5c boundary table | [edge value] | [behavior] | [off-by-one] |
| D  | FUNC/state | §6 transition | [pre-state + event] | [post-state] | [missing guard] |
| E  | INTG/db    | §3 method + required_configs | [real DB setup] | [data persisted + queryable] | [connection not established / wrong table] |
| F  | INTG/api   | §4.N cross-service call | [real HTTP endpoint] | [correct response schema] | [wrong endpoint / timeout not handled] |

Category format: `MAIN/subtag` where MAIN is one of `FUNC, BNDRY, SEC, UI, PERF, INTG` and subtag is a free-form label.

Rules:
- Minimum 1 row per SRS acceptance criterion (from srs_trace requirements)
- Negative tests (FUNC/error + BNDRY/*) >= 40% of total rows
- "Traces To" references the design section the test derives from
- "Kills Which Bug?" names a specific wrong implementation this test catches

**ATS category alignment** (if ATS doc was provided): Every main category listed in the ATS mapping table for this feature's requirement(s) MUST appear as at least one row's Category prefix in this Test Inventory. For example, if ATS requires SEC for FR-005, at least one Test Inventory row must have Category = `SEC/*`. Missing ATS categories → add rows before proceeding to §8.

**Visual Rendering Coverage** (mandatory for `"ui": true`): For each positive rendering assertion in §3b (Visual Rendering Contract), add at least one `UI/render` Test Inventory row. "Traces To" = §3b Visual Rendering Contract, specific element row. "Kills Which Bug?" = the rendering failure this test catches (e.g., "render function never called", "canvas blank", "DOM element not appended"). If the Visual Rendering Contract lists N visual elements, there must be at least N `UI/render` rows.

**Integration test rows (INTG category):**
- For features with external dependencies (DB, HTTP services, file system, third-party SDK): add ≥1 `INTG/*` row per dependency type
- Derive from: Interface Contract (§3) methods that interact with external systems + `required_configs[]` entries with connection-string keys
- "Traces To" = §3 method + the specific external dependency
- "Kills Which Bug?" = connection/integration failure the unit mock would miss
- If feature is pure computation with no external deps: write "INTG: N/A — pure function, no external I/O" (mirrors TDD Rule 5 exemption)

**Relationship with TDD**: This table is the PRIMARY INPUT for TDD Red (long-task-tdd Step 1). TDD Red uses this table as its starting point and may add tests per its own Rule 1-5 (category coverage, assertion quality, real test requirements). The Test Inventory provides the design-driven scenarios; TDD adds implementation-driven scenarios discovered during coding.

**Design Interface Coverage Gate (mandatory — execute before proceeding to §8):**

1. Re-read §4.N of the system design document
2. Extract ALL named functions, methods, endpoints, middleware, validators,
   and authorization checks (e.g., `check_repo_access`, `validate_input`)
3. For EACH named item: confirm at least one Test Inventory row exercises it
   (match in "Traces To" or "Input / Setup" columns)
4. If ANY design-specified function has zero Test Inventory coverage:
   - Add row(s) — typically error/security category
   - Set "Traces To" = the specific design section (e.g., "§4.5.3 ACL check")
5. Re-verify negative test ratio ≥ 40% after additions

This is the PRIMARY defense against spec drift. If the design says "check_repo_access
enforces ACL" and no test row covers it, the TDD phase will silently skip it —
causing a late-stage finding that triggers cascading mock-setup costs.

### 8. TDD Task Decomposition

After the design is complete, decompose into TDD tasks.

**Task granularity**: Each task should be 2-5 minutes of work. If a task would take longer, split it.

**Task structure**:

#### Task 1: Write failing tests
**Files**: [exact paths]
**Steps**:
1. Create test file with imports
2. Write test code for each row in Test Inventory (§7):
   - Include mock setup, specific input values, concrete assertions
   - Test A: [matching table row A]
   - Test B: [matching table row B]
3. Run: `[test command]`
4. **Expected**: All tests FAIL for the right reason

#### Task 2: Implement minimal code
**Files**: [exact paths]
**Steps**:
1. [Exact change referencing Algorithm §5 pseudocode]
2. [Exact change referencing Interface Contract §3]
3. Run: `[test command]`
4. **Expected**: All tests PASS

#### Task 3: Coverage Gate
1. Run: `[coverage command]`
2. Check thresholds. If below: return to Task 1.
3. Record coverage output as evidence.

#### Task 4: Refactor
1. [Specific refactoring actions]
2. Run full test suite. All tests PASS.

#### Task 5: Mutation Gate
1. Run: `[mutation command] --paths-to-mutate=<changed-files>`
2. Check threshold. If below: improve assertions.
3. Record mutation output as evidence.

### Verification Checklist
- [ ] All SRS acceptance criteria (from srs_trace) traced to Interface Contract postconditions
- [ ] All SRS acceptance criteria (from srs_trace) traced to Test Inventory rows
- [ ] Algorithm pseudocode covers all non-trivial methods
- [ ] Boundary table covers all algorithm parameters
- [ ] Error handling table covers all Raises entries
- [ ] Test Inventory negative ratio >= 40%
- [ ] Visual Rendering Contract complete for ui:true features (all visual elements listed, positive rendering assertions defined, interactive depth assertions defined)
- [ ] Each Visual Rendering Contract element has ≥1 UI/render Test Inventory row
- [ ] Every skipped section has explicit "N/A — [reason]"
- [ ] All functions/methods named in §4.N have at least one Test Inventory row

## Diagram Quality Rules

Concrete, verifiable rules:

- **Component/flow diagrams**: every edge labeled with data type; every node maps to a class/module
- **Sequence diagrams**: include alt/opt/loop blocks for all branches; show return types; participant names match class names from §2
- **Flow diagrams**: every decision node has exactly 2 exits; no transitions without labeled conditions
- **State diagrams**: every state reachable from initial; every terminal reachable; no orphan states; guard conditions on ambiguous transitions

## Skip-Explicitly Rule

Every section (§2-§6) must either:
- Contain COMPLETE content per the requirements above, OR
- State "N/A — [specific reason why this section does not apply]"

An empty or half-filled section is a design defect that blocks TDD. A section that says "N/A" without a reason is also a defect.

---

## Structured Return Contract

When the design document is complete, return your result in EXACTLY this format:

```markdown
## SubAgent Result: Feature Design
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-3 sentences — what was designed, key architectural decisions, document completeness]
### Artifacts
- [docs/features/YYYY-MM-DD-<feature-name>.md]: Feature detailed design document
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Sections Complete | N/8 | 8/8 (or N/A justified) | PASS/FAIL |
| Test Inventory Rows | N | ≥ SRS acceptance criteria count (from srs_trace) | PASS/FAIL |
| Negative Test Ratio | N% | ≥ 40% | PASS/FAIL |
| Verification Checklist | N/10 | 10/10 | PASS/FAIL |
| Design Interface Coverage | N/M | M/M | PASS/FAIL |
| Visual Rendering Assertions | N | ≥ Visual Rendering Contract element count (ui:true) | PASS/FAIL/N/A |
### Issues (only if FAIL)
| # | Severity | Description |
|---|----------|-------------|
### Next Step Inputs
- feature_design_doc: [path to the design document]
- test_inventory_count: [number of test inventory rows]
- tdd_task_count: [number of TDD tasks]
```

**IMPORTANT**: Write the design document to disk at the specified output path. The orchestrator expects the file to exist after this SubAgent completes.
