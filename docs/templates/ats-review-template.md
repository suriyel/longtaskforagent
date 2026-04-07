# ATS Review Template

> This template defines the review dimensions, severity levels, and pass criteria for the ATS reviewer subagent.
> Users may override this template via `ats_review_template_path` in `feature-list.json` (or specify it during the ATS phase).
> Custom templates can add/remove dimensions, redefine severity criteria, and customize pass conditions.

---

## Review Dimensions

### R1: Requirement Coverage Completeness

**Purpose**: Ensure every SRS requirement has a corresponding ATS mapping row.

**Checks:**
- Every FR-xxx from SRS appears in ATS mapping table
- Every NFR-xxx from SRS appears in ATS mapping table
- Every IFR-xxx from SRS appears in ATS mapping table
- No orphan rows (ATS rows referencing non-existent SRS requirements)

**Defect severity:**
- FR/NFR/IFR missing from ATS → **Major**
- Orphan ATS row (no matching SRS requirement) → **Minor**

---

### R2: Category Diversity

**Purpose**: Ensure each requirement has the appropriate test categories assigned based on its nature.

**Mandatory category rules:**
| Condition | Required Categories |
|-----------|-------------------|
| All FR-xxx | FUNC + BNDRY (minimum) |
| FR handles user input, authentication, or authorization | + SEC |
| NFR-xxx with performance metrics | PERF |

**Checks:**
- All FRs have at least FUNC + BNDRY
- FRs handling user input/auth have SEC
- NFRs with performance metrics have PERF
- No FR has only a single category assigned

**Defect severity:**
- Missing mandatory category → **Major**
- Single-category FR (should have at least 2) → **Minor**

---

### R3: Scenario Adequacy

**Purpose**: Ensure acceptance scenarios are comprehensive enough to validate each requirement.

**Checks:**
- Each FR has both normal-path and abnormal-path scenarios
- Minimum case counts match requirement complexity (see heuristics table)
- Scenarios are concrete and actionable (not vague)
- Each SRS Given/When/Then acceptance criterion is reflected in at least one scenario

**Defect severity:**
- Missing abnormal/error path scenario → **Major**
- Minimum case count too low for complexity → **Major**
- Vague scenario description → **Minor**

---

### R4: Verifiability

**Purpose**: Ensure all scenarios and pass criteria are measurable and executable.

**Checks:**
- Each scenario has specific inputs and expected outputs
- Pass criteria are measurable and assertable (numbers, states, responses)
- No weasel words: "reasonable", "appropriate", "correctly", "properly", "quickly", "合理", "正确", "适当"

**Defect severity:**
- Non-measurable pass criterion for NFR → **Critical**
- Non-measurable pass criterion for FR → **Major**
- Weasel word in scenario description → **Minor**

---

### R5: NFR Testability

**Purpose**: Ensure non-functional requirements have concrete, executable test methods.

**Checks:**
- Each NFR has an explicit test tool specified
- Each NFR has quantified thresholds (not just "fast" or "scalable")
- Load parameters are defined (concurrency, duration, data volume)
- NFR test methods are feasible with the project's stated tech stack

**Defect severity:**
- NFR without test tool or threshold → **Major**
- Missing load parameters → **Minor**
- Infeasible tool choice for tech stack → **Major**

---

### R6: Cross-Feature Integration

**Purpose**: Ensure critical multi-feature data flows are identified and planned for verification.

**Checks:**
- Critical data flow paths that span 3+ features are identified
- High-risk interaction points (auth boundaries, data handoffs) are covered
- Integration scenarios reference specific feature IDs
- Data consistency verification points are included

**Defect severity:**
- Missing critical data flow path → **Major**
- Missing feature ID reference in integration scenario → **Minor**
- No integration scenarios at all (when project has >5 features) → **Major**

---

### R7: Risk Consistency

**Purpose**: Ensure test depth aligns with requirement priority and architectural risk.

**Checks:**
- Risk levels align with SRS requirement priorities (Critical/High should be High risk)
- High-risk areas have deeper test requirements (more categories, more cases)
- Security-critical features are flagged as High risk
- Test depth varies appropriately (not everything is "standard")

**Defect severity:**
- High-priority requirement with Low risk assessment → **Major**
- All requirements at same risk/depth level → **Minor**
- Security-critical feature not flagged as High risk → **Major**

---

## Severity Definitions

| Level | Definition | Blocking? |
|-------|-----------|-----------|
| **Critical** | Requirement completely missing from ATS; NFR with unmeasurable criterion | Yes — blocks approval |
| **Major** | Category gap, missing scenarios, non-verifiable criteria, risk inconsistency | Yes — must fix before approval |
| **Minor** | Style issue, single-category FR, weak wording, missing integration detail | No — fix recommended |

## Pass Criteria

| Condition | Verdict |
|-----------|---------|
| 0 Critical + 0 Major | **PASS** |
| 0 Critical + 0 Major + ≤5 Minor | **PASS** (with notes) |
| Any Critical OR any Major | **FAIL** (must fix and re-review) |

## Custom Dimension Guidelines

When creating a custom review template, you may:

1. **Add dimensions** — e.g., R8 for GDPR data testing coverage, R9 for compliance-specific checks
2. **Remove dimensions** — e.g., remove R6 for single-feature projects
3. **Modify severity rules** — e.g., make single-category FR a Major instead of Minor
4. **Modify pass criteria** — e.g., require 0 Minor for PASS
5. **Add category rules** — e.g., add GDPR as a mandatory category for data-processing FRs

Maintain the same output format (dimension table + defect list + verdict) for compatibility with the ATS skill's review processing logic.
