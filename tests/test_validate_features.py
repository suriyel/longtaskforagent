#!/usr/bin/env python3
"""
Unit tests for validate_features.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "skills", "using-long-task", "scripts", "validate_features.py")


def run_validator(feature_data):
    """Run validate_features.py with given data, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(feature_data, f, indent=2)
        f.flush()
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


def test_valid_feature_list():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "Test feature",
                "description": "A test feature",
                "priority": "high",
                "status": "failing",
                "verification_steps": ["Step 1"],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0, got {code}: {stdout}"
    assert "VALID" in stdout


def test_missing_required_field():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "Test feature",
                # Missing: description, priority, status
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit, got {code}: {stdout}"


def test_invalid_status():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1,
                "category": "core",
                "title": "Test feature",
                "description": "A test feature",
                "priority": "high",
                "status": "in-progress",  # Invalid!
                "verification_steps": ["Step 1"],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for invalid status: {stdout}"


def test_duplicate_ids():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            },
            {
                "id": 1, "category": "core", "title": "B",
                "description": "B", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for duplicate IDs: {stdout}"


def test_invalid_dependency_reference():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [99]  # ID 99 doesn't exist
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for invalid dependency: {stdout}"


def test_empty_verification_steps():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": [], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for empty verification_steps: {stdout}"


def test_valid_tech_stack():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {
            "language": "python",
            "test_framework": "pytest",
            "coverage_tool": "pytest-cov",
            "mutation_tool": "mutmut"
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid tech_stack: {stdout}"
    assert "VALID" in stdout


def test_invalid_language():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {
            "language": "ruby",
            "test_framework": "rspec",
            "coverage_tool": "simplecov",
            "mutation_tool": "mutant"
        },
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for unsupported language: {stdout}"


def test_todo_language_is_valid():
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {"language": "TODO"},
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for TODO language: {stdout}"


def test_all_supported_languages():
    for lang in ["python", "java", "javascript", "typescript", "c", "cpp", "c++", "scala"]:
        data = {
            "project": "test-project",
            "created": "2025-01-01",
            "tech_stack": {"language": lang},
            "features": [
                {
                    "id": 1, "category": "core", "title": "A",
                    "description": "A", "priority": "high", "status": "failing",
                    "verification_steps": ["Step 1"], "dependencies": []
                }
            ]
        }
        code, stdout, _ = run_validator(data)
        assert code == 0, f"Expected exit 0 for language '{lang}': {stdout}"


# --- constraints[] validation tests ---

def test_valid_constraints():
    """constraints[] as array of strings should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "constraints": [
            "Must run offline — no external API calls",
            "Python 3.8+ only"
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid constraints: {stdout}"
    assert "VALID" in stdout


def test_constraints_not_array_fails():
    """constraints that is not an array should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "constraints": "not an array",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for non-array constraints: {stdout}"


def test_constraints_non_string_item_fails():
    """constraints[] with a non-string item should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "constraints": ["Valid constraint", 42],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for non-string constraint item: {stdout}"


def test_empty_constraints_is_valid():
    """Empty constraints[] should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "constraints": [],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for empty constraints: {stdout}"


def test_no_constraints_key_is_valid():
    """Omitting constraints entirely should pass (backward compat)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 when constraints is omitted: {stdout}"


# --- assumptions[] validation tests ---

def test_valid_assumptions():
    """assumptions[] as array of strings should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "assumptions": [
            "JWT validation handled by API Gateway; business layer must NOT re-validate",
            "Input data is pre-sanitised before reaching this service"
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid assumptions: {stdout}"
    assert "VALID" in stdout


def test_assumptions_not_array_fails():
    """assumptions that is not an array should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "assumptions": {"key": "not a list"},
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for non-array assumptions: {stdout}"


def test_assumptions_non_string_item_fails():
    """assumptions[] with a non-string item should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "assumptions": ["Valid assumption", True],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero exit for non-string assumption item: {stdout}"


def test_empty_assumptions_is_valid():
    """Empty assumptions[] should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "assumptions": [],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for empty assumptions: {stdout}"


def test_no_assumptions_key_is_valid():
    """Omitting assumptions entirely should pass (backward compat)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 when assumptions is omitted: {stdout}"


def test_constraints_and_assumptions_shown_in_summary():
    """Non-empty constraints and assumptions should appear in summary output."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "constraints": ["No external API calls"],
        "assumptions": ["JWT validated by Gateway"],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0: {stdout}"
    assert "Constraints: 1" in stdout, f"Expected 'Constraints: 1' in summary: {stdout}"
    assert "Assumptions: 1" in stdout, f"Expected 'Assumptions: 1' in summary: {stdout}"


# --- UI field validation tests ---

# --- srs_trace validation tests ---

def test_valid_srs_trace():
    """Feature with valid srs_trace should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "dependencies": [],
                "srs_trace": ["FR-001", "IFR-003"]
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid srs_trace: {stdout}"


def test_srs_trace_invalid_format():
    """srs_trace with invalid requirement ID format should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "dependencies": [],
                "srs_trace": ["FR-001", "INVALID", "FR-01"]
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for invalid srs_trace format: {stdout}"
    assert "srs_trace" in stdout


def test_srs_trace_not_array():
    """srs_trace that is not an array should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "dependencies": [],
                "srs_trace": "FR-001"
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-array srs_trace: {stdout}"


def test_feature_without_srs_trace_ok():
    """Feature without srs_trace should pass (field is optional)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for feature without srs_trace: {stdout}"


def test_feature_without_verification_steps_ok():
    """Feature without verification_steps should pass (field is now optional)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "dependencies": [],
                "srs_trace": ["FR-001"]
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for feature without verification_steps: {stdout}"


# --- wave/deprecated/supersedes validation tests ---

def test_valid_wave_fields():
    """Features with valid wave field should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "waves": [
            {"id": 0, "date": "2025-01-01", "description": "Initial release"},
            {"id": 1, "date": "2025-03-01", "description": "Add export"}
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "passing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "wave": 0
            },
            {
                "id": 2, "category": "core", "title": "B",
                "description": "B", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [1],
                "wave": 1
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid waves: {stdout}"
    assert "Waves: 2" in stdout


def test_wave_not_in_waves_array_fails():
    """Feature with wave not in root waves[] should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "waves": [
            {"id": 0, "date": "2025-01-01", "description": "Initial"}
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "wave": 5
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for wave not in waves[]: {stdout}"


def test_wave_negative_fails():
    """Negative wave number should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "wave": -1
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for negative wave: {stdout}"


def test_waves_duplicate_id_fails():
    """Duplicate wave IDs should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "waves": [
            {"id": 0, "date": "2025-01-01", "description": "A"},
            {"id": 0, "date": "2025-03-01", "description": "B"}
        ],
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "wave": 0
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for duplicate wave IDs: {stdout}"


def test_valid_deprecated_feature():
    """Deprecated feature with reason should pass."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Old feature",
                "description": "A", "priority": "high", "status": "passing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "deprecated": True,
                "deprecated_reason": "Replaced by feature 2"
            },
            {
                "id": 2, "category": "core", "title": "New feature",
                "description": "B", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "supersedes": 1
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for valid deprecated: {stdout}"
    assert "1 deprecated" in stdout


def test_deprecated_without_reason_fails():
    """deprecated=true without deprecated_reason should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "passing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "deprecated": True
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for deprecated without reason: {stdout}"


def test_deprecated_not_boolean_fails():
    """deprecated field that is not boolean should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "deprecated": "yes"
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-boolean deprecated: {stdout}"


def test_supersedes_invalid_reference_fails():
    """supersedes referencing non-existent ID should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "supersedes": 99
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for invalid supersedes ref: {stdout}"


def test_supersedes_not_integer_fails():
    """supersedes field that is not an integer should fail."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "supersedes": "old"
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code != 0, f"Expected non-zero for non-integer supersedes: {stdout}"


def test_no_wave_fields_backward_compat():
    """Features without wave/deprecated/supersedes should pass (backward compat)."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 for backward compat: {stdout}"


def test_deprecated_excluded_from_summary_counts():
    """Deprecated features should be shown separately in summary."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "passing",
                "verification_steps": ["Step 1"], "dependencies": [],
                "deprecated": True,
                "deprecated_reason": "No longer needed"
            },
            {
                "id": 2, "category": "core", "title": "B",
                "description": "B", "priority": "high", "status": "passing",
                "verification_steps": ["Step 1"], "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0: {stdout}"
    assert "1 passing" in stdout
    assert "1 deprecated" in stdout


# --- Simple verification_steps warning tests ---

def test_simple_verification_step_warning():
    """Short verification_step without chaining should produce a warning."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Simple Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "verification_steps": ["API returns 200"],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0 (warning, not error): {stdout}"
    assert "simple assertion" in stdout.lower(), f"Expected simple assertion warning: {stdout}"


def test_rich_verification_step_no_warning():
    """Rich verification_step with chaining should NOT produce the simple assertion warning."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "Rich Feature",
                "description": "A feature", "priority": "high", "status": "failing",
                "verification_steps": [
                    "Given a registered user, when POST /api/login with valid credentials, then response 200 with JWT token; and GET /api/profile with token returns user data"
                ],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0, f"Expected exit 0: {stdout}"
    assert "simple assertion" not in stdout.lower(), f"Unexpected simple assertion warning: {stdout}"


def test_short_step_with_chaining_no_warning():
    """Short step with chaining keywords should not warn."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "features": [
            {
                "id": 1, "category": "core", "title": "A",
                "description": "A", "priority": "high", "status": "failing",
                "verification_steps": ["Given X, when Y, then Z"],
                "dependencies": []
            }
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0
    assert "simple assertion" not in stdout.lower()


def test_single_round_true_valid():
    """single_round: true should pass validation."""
    data = {
        "project": "test",
        "created": "2025-01-01",
        "single_round": True,
        "features": [
            {"id": 1, "category": "core", "title": "A", "description": "A",
             "priority": "high", "status": "failing", "dependencies": []}
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0


def test_single_round_false_valid():
    """single_round: false should pass validation."""
    data = {
        "project": "test",
        "created": "2025-01-01",
        "single_round": False,
        "features": [
            {"id": 1, "category": "core", "title": "A", "description": "A",
             "priority": "high", "status": "failing", "dependencies": []}
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0


def test_single_round_invalid_type():
    """single_round must be a boolean."""
    data = {
        "project": "test",
        "created": "2025-01-01",
        "single_round": "yes",
        "features": [
            {"id": 1, "category": "core", "title": "A", "description": "A",
             "priority": "high", "status": "failing", "dependencies": []}
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 1
    assert "single_round must be a boolean" in stdout


def test_no_single_round_backward_compat():
    """Omitting single_round should be fine (backward compat)."""
    data = {
        "project": "test",
        "created": "2025-01-01",
        "features": [
            {"id": 1, "category": "core", "title": "A", "description": "A",
             "priority": "high", "status": "failing", "dependencies": []}
        ]
    }
    code, stdout, _ = run_validator(data)
    assert code == 0


# ---- current-lock validation ----

def _basic_failing(id_=1):
    return {"id": id_, "category": "core", "title": f"T{id_}",
            "description": "D", "priority": "high", "status": "failing",
            "dependencies": []}


def test_current_null_is_valid():
    data = {"project": "p", "created": "2025-01-01",
            "current": None,
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code == 0
    assert "current=none" in stdout


def test_current_design_phase_valid():
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "design"},
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code == 0
    assert "current=#1(design)" in stdout


def test_current_tdd_phase_valid():
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "tdd"},
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code == 0
    assert "current=#1(tdd)" in stdout


def test_current_phase_st_rejected():
    """Simple branch has no ST phase."""
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "st"},
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code != 0
    assert "phase" in stdout.lower()


def test_current_phase_invalid_rejected():
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "bogus"},
            "features": [_basic_failing()]}
    code, _, _ = run_validator(data)
    assert code != 0


def test_current_not_object_rejected():
    data = {"project": "p", "created": "2025-01-01",
            "current": "invalid",
            "features": [_basic_failing()]}
    code, _, _ = run_validator(data)
    assert code != 0


def test_current_missing_feature_id_rejected():
    data = {"project": "p", "created": "2025-01-01",
            "current": {"phase": "design"},
            "features": [_basic_failing()]}
    code, _, _ = run_validator(data)
    assert code != 0


def test_current_references_nonexistent_feature_rejected():
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 999, "phase": "design"},
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code != 0
    assert "999" in stdout


def test_current_references_passing_feature_rejected():
    f = _basic_failing()
    f["status"] = "passing"
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "tdd"},
            "features": [f]}
    code, stdout, _ = run_validator(data)
    assert code != 0
    assert "passing" in stdout.lower()


def test_current_references_deprecated_feature_rejected():
    f = _basic_failing()
    f["deprecated"] = True
    f["deprecated_reason"] = "obsolete"
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "design"},
            "features": [f]}
    code, stdout, _ = run_validator(data)
    assert code != 0
    assert "deprecated" in stdout.lower()


def test_no_current_key_backward_compat():
    """Omitting current should still pass (backward compat for pre-refactor files)."""
    data = {"project": "p", "created": "2025-01-01",
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code == 0
    assert "current=none" in stdout


def test_current_summary_displayed():
    data = {"project": "p", "created": "2025-01-01",
            "current": {"feature_id": 1, "phase": "tdd"},
            "features": [_basic_failing()]}
    code, stdout, _ = run_validator(data)
    assert code == 0
    assert "current=#1(tdd)" in stdout


if __name__ == "__main__":
    tests = [
        test_valid_feature_list,
        test_missing_required_field,
        test_invalid_status,
        test_duplicate_ids,
        test_invalid_dependency_reference,
        test_empty_verification_steps,
        test_valid_tech_stack,
        test_invalid_language,
        test_todo_language_is_valid,
        test_all_supported_languages,
        test_valid_constraints,
        test_constraints_not_array_fails,
        test_constraints_non_string_item_fails,
        test_empty_constraints_is_valid,
        test_no_constraints_key_is_valid,
        test_valid_assumptions,
        test_assumptions_not_array_fails,
        test_assumptions_non_string_item_fails,
        test_empty_assumptions_is_valid,
        test_no_assumptions_key_is_valid,
        test_constraints_and_assumptions_shown_in_summary,
        test_valid_srs_trace,
        test_srs_trace_invalid_format,
        test_srs_trace_not_array,
        test_feature_without_srs_trace_ok,
        test_feature_without_verification_steps_ok,
        test_valid_wave_fields,
        test_wave_not_in_waves_array_fails,
        test_wave_negative_fails,
        test_waves_duplicate_id_fails,
        test_valid_deprecated_feature,
        test_deprecated_without_reason_fails,
        test_deprecated_not_boolean_fails,
        test_supersedes_invalid_reference_fails,
        test_supersedes_not_integer_fails,
        test_no_wave_fields_backward_compat,
        test_deprecated_excluded_from_summary_counts,
        test_simple_verification_step_warning,
        test_rich_verification_step_no_warning,
        test_short_step_with_chaining_no_warning,
        test_single_round_true_valid,
        test_single_round_false_valid,
        test_single_round_invalid_type,
        test_no_single_round_backward_compat,
        test_current_null_is_valid,
        test_current_design_phase_valid,
        test_current_tdd_phase_valid,
        test_current_phase_st_rejected,
        test_current_phase_invalid_rejected,
        test_current_not_object_rejected,
        test_current_missing_feature_id_rejected,
        test_current_references_nonexistent_feature_rejected,
        test_current_references_passing_feature_rejected,
        test_current_references_deprecated_feature_rejected,
        test_no_current_key_backward_compat,
        test_current_summary_displayed,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
