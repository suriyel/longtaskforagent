#!/usr/bin/env python3
"""
Validate feature-list.json structure and integrity.

Checks:
- Valid JSON structure
- Required fields present on each feature
- No duplicate IDs
- Status values are valid
- Dependencies reference existing feature IDs
- Verification steps are non-empty (if present — field is optional)
- srs_trace is a valid array of requirement IDs (if present)
- tech_stack.language is a supported value (if present)
- quality_gates values are numbers between 0 and 100 (if present)
Usage:
    python validate_features.py <path/to/feature-list.json>
"""

import json
import os
import re
import sys


REQUIRED_FIELDS = {"id", "category", "title", "description", "priority", "status"}
SRS_TRACE_PATTERN = re.compile(r"^(?:FR|IFR)-\d{3}$")
VALID_STATUSES = {"failing", "passing"}
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_LANGUAGES = {"python", "java", "javascript", "typescript", "c", "cpp", "c++"}
QUALITY_GATE_KEYS = {"line_coverage_min", "branch_coverage_min", "mutation_score_min"}

def validate(path: str) -> tuple[list[str], list[str]]:
    """Validate feature-list.json. Returns (errors, warnings)."""
    errors = []
    warnings = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return [f"Cannot read feature-list.json: {e}"], []

    if "features" not in data:
        return ['"features" key missing from root object'], []

    # Validate tech_stack if present
    tech_stack = data.get("tech_stack")
    if tech_stack:
        if not isinstance(tech_stack, dict):
            errors.append("tech_stack must be an object")
        else:
            lang = tech_stack.get("language", "").lower()
            if lang and lang != "todo" and lang not in VALID_LANGUAGES:
                errors.append(
                    f"tech_stack.language '{lang}' not in supported: {sorted(VALID_LANGUAGES)}"
                )

    # Validate quality_gates if present
    quality_gates = data.get("quality_gates")
    if quality_gates:
        if not isinstance(quality_gates, dict):
            errors.append("quality_gates must be an object")
        else:
            for key in QUALITY_GATE_KEYS:
                val = quality_gates.get(key)
                if val is not None:
                    if not isinstance(val, (int, float)) or val < 0 or val > 100:
                        errors.append(
                            f"quality_gates.{key} must be a number between 0 and 100, got {val!r}"
                        )
            # Validate mutation_full_threshold (positive integer, not a percentage)
            mft = quality_gates.get("mutation_full_threshold")
            if mft is not None:
                if not isinstance(mft, int) or mft < 1:
                    errors.append(
                        f"quality_gates.mutation_full_threshold must be a positive integer, got {mft!r}"
                    )

    # Validate single_round if present
    single_round = data.get("single_round")
    if single_round is not None and not isinstance(single_round, bool):
        errors.append(
            f"single_round must be a boolean, got {type(single_round).__name__}"
        )

    # Validate waves if present
    waves = data.get("waves")
    wave_ids = set()
    if waves is not None:
        if not isinstance(waves, list):
            errors.append('"waves" must be an array')
        else:
            for wi, wave in enumerate(waves):
                wprefix = f"waves[{wi}]"
                if not isinstance(wave, dict):
                    errors.append(f"{wprefix}: must be an object")
                    continue
                wid = wave.get("id")
                if wid is None:
                    errors.append(f"{wprefix}: missing 'id' field")
                elif not isinstance(wid, int) or wid < 0:
                    errors.append(f"{wprefix}: 'id' must be a non-negative integer")
                else:
                    if wid in wave_ids:
                        errors.append(f"{wprefix}: duplicate wave id={wid}")
                    wave_ids.add(wid)
                if not wave.get("date"):
                    errors.append(f"{wprefix}: missing or empty 'date' field")
                if not wave.get("description"):
                    errors.append(f"{wprefix}: missing or empty 'description' field")

    # Validate constraints if present
    constraints = data.get("constraints")
    if constraints is not None:
        if not isinstance(constraints, list):
            errors.append('"constraints" must be an array')
        else:
            for ci, item in enumerate(constraints):
                if not isinstance(item, str):
                    errors.append(f"constraints[{ci}]: must be a string, got {type(item).__name__}")

    # Validate assumptions if present
    assumptions = data.get("assumptions")
    if assumptions is not None:
        if not isinstance(assumptions, list):
            errors.append('"assumptions" must be an array')
        else:
            for ai, item in enumerate(assumptions):
                if not isinstance(item, str):
                    errors.append(f"assumptions[{ai}]: must be a string, got {type(item).__name__}")

    features = data["features"]
    if not isinstance(features, list):
        return ['"features" must be an array'], []

    ids_seen = set()

    for i, feat in enumerate(features):
        prefix = f"Feature [{i}]"

        if not isinstance(feat, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        # Check required fields
        missing = REQUIRED_FIELDS - set(feat.keys())
        if missing:
            errors.append(f"{prefix}: missing fields: {missing}")

        # Check ID uniqueness
        fid = feat.get("id")
        if fid is not None:
            if fid in ids_seen:
                errors.append(f"{prefix}: duplicate id={fid}")
            ids_seen.add(fid)

        # Check status
        status = feat.get("status")
        if status and status not in VALID_STATUSES:
            errors.append(f"{prefix} (id={fid}): invalid status '{status}', must be one of {VALID_STATUSES}")

        # Check priority
        priority = feat.get("priority")
        if priority and priority not in VALID_PRIORITIES:
            errors.append(f"{prefix} (id={fid}): invalid priority '{priority}', must be one of {VALID_PRIORITIES}")

        # Check verification_steps
        steps = feat.get("verification_steps")
        if steps is not None:
            if not isinstance(steps, list) or len(steps) == 0:
                errors.append(f"{prefix} (id={fid}): verification_steps must be a non-empty array")

        # Check wave field type
        wave = feat.get("wave")
        if wave is not None:
            if not isinstance(wave, int) or wave < 0:
                errors.append(f"{prefix} (id={fid}): 'wave' must be a non-negative integer, got {wave!r}")
            elif wave_ids and wave not in wave_ids:
                errors.append(f"{prefix} (id={fid}): wave={wave} not found in root 'waves' array")

        # Check deprecated field
        deprecated = feat.get("deprecated")
        if deprecated is not None and not isinstance(deprecated, bool):
            errors.append(f"{prefix} (id={fid}): 'deprecated' must be a boolean, got {type(deprecated).__name__}")

        # Check deprecated_reason required when deprecated=true
        if deprecated is True:
            reason = feat.get("deprecated_reason")
            if not reason or not isinstance(reason, str) or len(reason.strip()) == 0:
                errors.append(f"{prefix} (id={fid}): 'deprecated_reason' is required when deprecated=true")

        # Check deprecated_reason type when present
        dep_reason = feat.get("deprecated_reason")
        if dep_reason is not None and not isinstance(dep_reason, str):
            errors.append(f"{prefix} (id={fid}): 'deprecated_reason' must be a string, got {type(dep_reason).__name__}")

        # Check supersedes field
        supersedes = feat.get("supersedes")
        if supersedes is not None and not isinstance(supersedes, int):
            errors.append(f"{prefix} (id={fid}): 'supersedes' must be an integer, got {type(supersedes).__name__}")

        # Check srs_trace field (optional, array of requirement IDs)
        srs_trace = feat.get("srs_trace")
        if srs_trace is not None:
            if not isinstance(srs_trace, list):
                errors.append(f"{prefix} (id={fid}): 'srs_trace' must be an array")
            else:
                for ti, trace_id in enumerate(srs_trace):
                    if not isinstance(trace_id, str) or not SRS_TRACE_PATTERN.match(trace_id):
                        errors.append(
                            f"{prefix} (id={fid}): srs_trace[{ti}] must match "
                            f"FR-xxx/IFR-xxx format, got {trace_id!r}"
                        )

        # Check dependencies
        deps = feat.get("dependencies", [])
        if isinstance(deps, list):
            for dep in deps:
                if dep not in ids_seen and dep != fid:
                    # Defer check — dependency may appear later
                    pass

    # Second pass: validate all dependencies and supersedes reference existing IDs
    all_ids = {f.get("id") for f in features if isinstance(f, dict)}
    id_to_feature = {f.get("id"): f for f in features if isinstance(f, dict)}
    for feat in features:
        if not isinstance(feat, dict):
            continue
        fid = feat.get("id")
        for dep in feat.get("dependencies", []):
            if dep not in all_ids:
                errors.append(f"Feature id={fid}: dependency id={dep} does not exist")
        sup = feat.get("supersedes")
        if isinstance(sup, int) and sup not in all_ids:
            errors.append(f"Feature id={fid}: supersedes id={sup} does not exist")

        # Warn if verification_steps look like simple assertions
        vsteps = feat.get("verification_steps", [])
        if isinstance(vsteps, list) and not feat.get("deprecated", False):
            chaining_words = ["→", "then", "and ", "verify", "given", "when", "expect:", "reject:"]
            for vi, vstep in enumerate(vsteps):
                if isinstance(vstep, str) and len(vstep) < 40:
                    has_chaining = any(w in vstep.lower() for w in chaining_words)
                    if not has_chaining:
                        warnings.append(
                            f"Feature id={fid}: verification_steps[{vi}] appears to be a simple "
                            f"assertion rather than a behavioral scenario: '{vstep}'"
                        )

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_features.py <path/to/feature-list.json>")
        sys.exit(1)

    result = validate(sys.argv[1])
    # Support both old (list) and new (tuple) return formats
    if isinstance(result, tuple):
        errors, warnings = result
    else:
        errors, warnings = result, []

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        # Print summary
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        features = data["features"]
        deprecated_count = sum(1 for f in features if isinstance(f, dict) and f.get("deprecated", False))
        active_features = [f for f in features if isinstance(f, dict) and not f.get("deprecated", False)]
        passing = sum(1 for f in active_features if f.get("status") == "passing")
        failing = sum(1 for f in active_features if f.get("status") == "failing")
        summary = f"VALID — {len(features)} features ({passing} passing, {failing} failing"
        if deprecated_count > 0:
            summary += f", {deprecated_count} deprecated"
        summary += ")"

        # Show quality gates if configured
        qg = data.get("quality_gates")
        if qg:
            line_min = qg.get("line_coverage_min", "N/A")
            branch_min = qg.get("branch_coverage_min", "N/A")
            mutation_min = qg.get("mutation_score_min", "N/A")
            summary += f" | Quality gates: line>={line_min}%, branch>={branch_min}%, mutation>={mutation_min}%"

        # Show constraints/assumptions counts
        ct = data.get("constraints", [])
        if ct:
            summary += f" | Constraints: {len(ct)}"
        at = data.get("assumptions", [])
        if at:
            summary += f" | Assumptions: {len(at)}"

        # Show wave distribution if waves exist
        waves_data = data.get("waves", [])
        if waves_data:
            summary += f" | Waves: {len(waves_data)}"

        # Show tech stack if configured
        ts = data.get("tech_stack")
        if ts:
            lang = ts.get("language", "N/A")
            if lang != "TODO":
                summary += f" | Language: {lang}"

        if warnings:
            summary += f" | {len(warnings)} warning(s)"

        print(summary)

        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w}")

        sys.exit(0)


if __name__ == "__main__":
    main()
