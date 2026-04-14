# Feature-Level Detailed Design — SubAgent Execution Reference

You are a Feature Design execution SubAgent. Follow these rules exactly. When finished, return your result using the **Structured Return Contract** at the bottom of this document.

---

# Feature-Level Detailed Design

Produce a detailed design for a single feature, bridging system-level design (§4.N) and TDD implementation.

System design answers "WHAT classes exist and HOW they interact."
This skill answers "WHAT each method does internally, WHAT can go wrong, and HOW to test it."

## Inputs

Read ALL of these BEFORE writing any design content:

1. **Feature object** from feature-list.json — ID, title, description, srs_trace, dependencies, priority (verification_steps if present)
2. **System design section** — full §4.N from the design document (read the entire subsection, NOT grep)
3. **SRS requirement** — full FR-xxx from the SRS document
4. **Constraints & assumptions** from feature-list.json root
5. **Existing code** — if dependency features are passing, read their public interfaces (imports, class/function signatures)
6. **Internal API contracts** (if §6.2 exists) — from Design Section 6.2, read rows where this feature appears as Provider or Consumer. These define cross-feature schemas that this feature's Interface Contract (§3) must align with.
7. **Codebase Conventions & Constraints** — Read Design doc §11 in full. Extract and keep in working memory:
   - §11.1: Mandatory internal libraries table (domain, library, replaces, import pattern)
   - §11.2: Prohibited APIs table (prohibited, reason, use instead)
   - §11.3: Approved 3rd-party libraries (purpose, library, version)
   - §11.5: Naming conventions table (rule, convention)
   - §11.6: Error handling pattern description
   §11 is always present in the design document. Empty tables mean no constraints for that category.

## Template

Use `skills/long-task-feature-design/references/feature-design-template.md` as the structural template. Copy the template, fill each section for the target feature.

## Checklist

You MUST complete each step in order:

### 1. Load Context

Read all input artifacts listed in Inputs above.

### 1a. Project Structure

After loading context, fill the "Project Structure" section of the template:
1. From the design document §4.N and existing code (dependency features), identify all files this feature will create or modify
2. Mark each as [existing], [new], or [modified]
3. Include only files architecturally relevant to this feature — omit test utilities, configs unless directly modified

### 1b. Ambiguity Scan

After reading all inputs and BEFORE writing any design content, scan for specification ambiguities that could affect design correctness. This scan uses the following taxonomy:

| Code | What to check |
|------|---------------|
| `SRS-VAGUE` | Acceptance criterion contains vague language ("fast", "user-friendly", "appropriate", "should handle") without measurable thresholds or concrete behaviors |
| `SRS-DESIGN-CONFLICT` | SRS requirement and Design §4.N contradict on interface type, data format, behavior, or error handling |
| `SRS-MISSING` | Acceptance criterion has no Given/When/Then or the expected result is not specified |
| `ATS-MISMATCH` | ATS requires a test category (e.g., SEC) but the feature's observable behavior has no surface for that category |
| `DEP-AMBIGUOUS` | Cross-feature interface is unclear — missing or incomplete §6.2 entry for a dependency |
| `CONSTRAINT-CONFLICT` | §11 codebase convention conflicts with feature requirement — e.g., §11.1 mandates an internal library that lacks capabilities the feature needs (streaming, specific protocol, batch size), or §11.2 prohibits an API the feature's SRS explicitly requires |

**Scan procedure:**

1. For each SRS acceptance criterion (from srs_trace requirements): check if it contains measurable, specific, testable conditions. Flag vague language without numeric thresholds or concrete behaviors → `SRS-VAGUE`
2. For each SRS requirement mapped to this feature: cross-reference against Design §4.N. Flag contradictions in interface type, data format, behavior, or error handling → `SRS-DESIGN-CONFLICT`
3. For each SRS acceptance criterion: verify Given/When/Then exists with explicit expected results → `SRS-MISSING`
4. For each ATS-required category (if ATS doc provided): check if the feature's observable behavior has a testable surface for that category → `ATS-MISMATCH`
5. For §6.2 contracts where this feature is Provider or Consumer: check if schemas are complete (no missing fields, no ambiguous types) → `DEP-AMBIGUOUS`
6. For each non-empty §11.1 row: check if the feature's requirements demand capabilities beyond the mandatory library's known API. For each non-empty §11.2 row: check if the feature's SRS acceptance criteria explicitly require the prohibited API → `CONSTRAINT-CONFLICT`

**For each detected ambiguity, produce a structured record:**
```
- Category: [code from taxonomy]
- Source: [document path + section/line reference]
- Description: [what is ambiguous]
- Impact: [which design sections cannot be completed without resolution — e.g., "§3 Interface Contract postcondition", "§7 Test Inventory expected result"]
- Suggested interpretation: [SubAgent's best guess based on context, if one exists; "none" if no reasonable interpretation]
- Question for user: [specific, actionable question that would resolve the ambiguity]
```

**For `category: "bugfix"` features**: only scan `SRS-VAGUE` and `SRS-DESIGN-CONFLICT` on the bug's acceptance criteria. Skip `ATS-MISMATCH` (bugfix features focus on root cause, not full specification coverage).

**Decision gate:**
- **Zero ambiguities detected** → proceed to Step 2 normally. No friction added.
- **All ambiguities have a reasonable suggested interpretation AND impact is LIMITED to non-critical sections** (does NOT affect Interface Contract signatures, Test Inventory expected results, or cross-feature §6.2 contracts) → proceed with assumptions. Document each assumption in the design document's `## Clarification Addendum` section with Authority = "assumed". Set Verdict to `PASS`. Include assumption count in `### Next Step Inputs`.
- **Any ambiguity has HIGH impact** (affects Interface Contract signatures, Test Inventory expected results, or cross-feature contracts) **OR has no reasonable suggested interpretation** → set Verdict to `CLARIFY`. Include the full Ambiguities table in the Structured Return Contract. Do NOT proceed to Step 2 — the orchestrator will collect user answers and re-dispatch.

> **On re-dispatch with Clarification Addendum**: If the SubAgent prompt includes a `## Clarification Addendum (user-approved resolutions)` section, treat those resolutions as authoritative constraints. Do NOT re-flag them as ambiguities. Incorporate them into the design as if they were in the original SRS/Design documents.

### 1c. Existing Implementation Discovery

After loading context and BEFORE writing design content, discover reusable code in passing dependency features. This prevents duplicate implementations and ensures consistency with established patterns.

**Discovery procedure:**

1. From `dependencies[]` in the feature object, list all features with `"status": "passing"`
2. For each passing dependency feature, read its implementation files (from its feature design Project Structure, or from source tree) and catalog:

   | Discovery Category | What to Find | Record |
   |-------------------|--------------|--------|
   | Utility functions | Shared validators, formatters, parsers, type converters | Function name, file path, signature, purpose |
   | API client implementations | HTTP clients, SDK wrappers, service connectors | Class/module, file path, target service, available methods |
   | Data access patterns | Repository classes, ORM models, query builders | Class, file path, entity/table, CRUD methods |
   | Error handling helpers | Custom exception classes, error middleware, Result types | Class/type name, file path, usage pattern |
   | §11.1 library usage patterns | How mandatory internal libraries are actually imported and called | Import statement, typical call site with file:line |

3. For each §11.1 mandatory library with non-empty rows: find at least one concrete usage example in passing features. Record the import pattern and typical call site. If no usage exists yet (first feature needing it), note: "First usage — implement per §11.1 import pattern."

4. Record ALL discoveries in the "## Existing Code Reuse" section of the design document. For each item, assign one of:
   - **REUSE**: This feature should import and call existing code directly
   - **EXTEND**: This feature should extend/subclass existing code
   - **PATTERN**: This feature should follow the same structural pattern but create own implementation

**If zero passing dependencies**: Write "No passing dependencies — all §11.1 library usage follows import patterns directly." and proceed.

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
- **§11.5 naming compliance**: All method, parameter, and class names MUST follow §11.5 naming conventions. If §11.5 documents `snake_case` and the design names a method `getUserData`, change to `get_user_data`.
- **§11.1 library compliance**: For any method that performs HTTP calls, DB queries, file I/O, logging, or other operations covered by §11.1 mandatory libraries: annotate in a "Uses" note after the Raises column — e.g., "Uses: @company/http (§11.1)". The method signature MUST NOT assume direct use of replaced APIs (e.g., do not type-hint `axios.Response` when §11.1 replaces axios).
- **§11.2 prohibited API check**: If any method's preconditions, postconditions, or Raises reference APIs from §11.2 prohibited list, this is a design defect. Replace with the §11.2-specified alternative before proceeding.
- **Existing code reuse check**: For each method in the Interface Contract, cross-check the "Existing Code Reuse" section. If a passing dependency already provides equivalent functionality marked REUSE, do NOT create a new method — reference the existing one. If EXTEND, design the method as an override/extension of the existing class.

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

**e) §11 library usage mapping:**

For each non-trivial method, identify which §11.1 mandatory libraries and "Existing Code Reuse" REUSE items it must use:

| Method | Operation | Required Library/Reuse Item | Import Pattern | Replaces |
|--------|-----------|---------------------------|----------------|----------|
| [method] | [e.g., HTTP GET to external API] | [e.g., @company/http (§11.1)] | [e.g., `from company.http import get`] | [e.g., requests.get, urllib] |
| [method] | [e.g., validate email format] | [e.g., REUSE: validate_email() from Feature #2] | [e.g., `from src.utils.validators import validate_email`] | [new implementation] |

Error handling within pseudocode: follow §11.6 error handling pattern. If §11.6 documents "custom Error subclasses + centralized handler", pseudocode RAISE statements must use project custom error classes, not generic exceptions.

> **Skip rule**: If the method has no external I/O and no reusable items apply, write "N/A — pure computation, no library dependencies"

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
| E  | INTG/db    | §3 method + external dependency | [real DB setup] | [data persisted + queryable] | [connection not established / wrong table] |
| F  | INTG/api   | §4.N cross-service call | [real HTTP endpoint] | [correct response schema] | [wrong endpoint / timeout not handled] |

Category format: `MAIN/subtag` where MAIN is one of `FUNC, BNDRY, SEC, UI, PERF, INTG` and subtag is a free-form label.

Rules:
- Minimum 1 row per SRS acceptance criterion (from srs_trace requirements)
- Negative tests (FUNC/error + BNDRY/*) >= 40% of total rows
- "Traces To" references the design section the test derives from
- "Kills Which Bug?" names a specific wrong implementation this test catches

**ATS category alignment** (if ATS doc was provided): Every main category listed in the ATS mapping table for this feature's requirement(s) MUST appear as at least one row's Category prefix in this Test Inventory. For example, if ATS requires SEC for FR-005, at least one Test Inventory row must have Category = `SEC/*`. Missing ATS categories → add rows before proceeding to §8.

**Integration test rows (INTG category):**
- For features with external dependencies (DB, HTTP services, file system, third-party SDK): add ≥1 `INTG/*` row per dependency type
- Derive from: Interface Contract (§3) methods that interact with external systems + design doc external dependency specifications
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
- [ ] Every skipped section has explicit "N/A — [reason]"
- [ ] All functions/methods named in §4.N have at least one Test Inventory row
- [ ] All method/class/parameter names comply with §11.5 naming conventions
- [ ] All operations covered by §11.1 mandatory libraries use those libraries (no replaced alternatives in Interface Contract or Algorithm)
- [ ] Existing Code Reuse section documents all discoverable reusable code from passing dependencies

## Diagram Quality Rules

Concrete, verifiable rules:

- **Component/flow diagrams**: every edge labeled with data type; every node maps to a class/module
- **Sequence diagrams**: include alt/opt/loop blocks for all branches; show return types; participant names match class names from §2
- **Flow diagrams**: every decision node has exactly 2 exits; no transitions without labeled conditions
- **State diagrams**: every state reachable from initial; every terminal reachable; no orphan states; guard conditions on ambiguous transitions
- **Increment change tracking** (when feature.wave > 0 and prior feature design exists): apply visual change markers per design template Diagram Change Tracking Convention. New nodes/states/participants use green styling (`classDef newNode fill:#d1fae5,stroke:#2ea043,stroke-width:2px` or equivalent per diagram type); modified elements use amber styling (`classDef modNode fill:#fef3c7,stroke:#d4a017,stroke-width:2px`). Include legend before each affected diagram. Remove previous-wave markers.

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
### Verdict: PASS | FAIL | BLOCKED | CLARIFY
### Summary
[1-3 sentences — what was designed, key architectural decisions, document completeness]
### Artifacts
- [docs/features/YYYY-MM-DD-<feature-name>.md]: Feature detailed design document
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Sections Complete | N/9 | 9/9 (or N/A justified) | PASS/FAIL |
| Test Inventory Rows | N | ≥ SRS acceptance criteria count (from srs_trace) | PASS/FAIL |
| Negative Test Ratio | N% | ≥ 40% | PASS/FAIL |
| Verification Checklist | N/11 | 11/11 | PASS/FAIL |
| Design Interface Coverage | N/M | M/M | PASS/FAIL |
| §11 Compliance | N checked / M total | All checked | PASS/FAIL |
| Existing Code Reuse Items | N | ≥ 0 (informational) | INFO |
### Issues (only if FAIL or BLOCKED)
| # | Severity | Description |
|---|----------|-------------|
### Ambiguities (only if CLARIFY)
| # | Category | Source | Description | Impact | Suggested Interpretation | Question |
|---|----------|--------|-------------|--------|--------------------------|----------|
| 1 | [code] | [doc § section] | [what is ambiguous] | [affected design sections] | [best guess or "none"] | [specific question for user] |
### Assumptions Made (only if PASS with assumptions)
| # | Category | Source | Assumption | Rationale |
|---|----------|--------|------------|-----------|
| 1 | [code] | [doc § section] | [what was assumed] | [why this is reasonable] |
### Next Step Inputs
- feature_design_doc: [path to the design document]
- test_inventory_count: [number of test inventory rows]
- tdd_task_count: [number of TDD tasks]
- ambiguity_count: [number of unresolved ambiguities, 0 if PASS]
- assumption_count: [number of assumptions made, 0 if none]
- constraint_compliance: [PASS/FAIL]
- reuse_items_count: [number of REUSE/EXTEND/PATTERN items]
```

**IMPORTANT**: Write the design document to disk at the specified output path. The orchestrator expects the file to exist after this SubAgent completes.
