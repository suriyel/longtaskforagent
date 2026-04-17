"""Tests for scripts/check_real_tests.py"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "check_real_tests.py"
)


def run_script(feature_list_path, *extra_args):
    """Run check_real_tests.py and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, SCRIPT, feature_list_path] + list(extra_args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def make_feature_list(tmp_path, features=None, real_test=None, language="python",
                      required_configs=None):
    """Create a minimal feature-list.json in tmp_path and return its path."""
    data = {
        "project": "test-project",
        "created": "2025-01-01",
        "tech_stack": {"language": language, "test_framework": "pytest",
                       "coverage_tool": "pytest-cov"},
        "quality_gates": {"line_coverage_min": 90, "branch_coverage_min": 80},
        "features": features or [],
    }
    if real_test is not None:
        data["real_test"] = real_test
    if required_configs is not None:
        data["required_configs"] = required_configs

    fl_path = tmp_path / "feature-list.json"
    fl_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(fl_path)


def make_test_file(tmp_path, filename, content):
    """Create a test file in tmp_path/tests/ directory."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    fpath = tests_dir / filename
    fpath.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(fpath)


# --- Basic scenarios ---

class TestNoRealTestConfig:
    """When feature-list.json has no real_test config, defaults are used."""

    def test_no_config_no_features_passes(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[])
        (tmp_path / "tests").mkdir()
        code, out, _ = run_script(fl)
        assert code == 0
        assert "PASS" in out

    def test_no_config_with_features_no_test_dir_fails(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        # No tests/ directory
        code, out, _ = run_script(fl)
        assert code == 1
        assert "FAIL" in out


class TestRealTestDiscovery:
    """Marker pattern correctly discovers real tests in test files."""

    def test_finds_real_tests_by_marker(self, tmp_path):
        make_test_file(tmp_path, "test_auth.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db_connection():
                assert True

            def test_normal_unit():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out
        assert "test_real_db_connection" in out
        assert "PASS" in out

    def test_finds_real_tests_by_comment_label(self, tmp_path):
        make_test_file(tmp_path, "test_api.py", """
            # [real-test] config — reads actual .env.test
            def test_real_config_loaded():
                assert True

            def test_normal():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "real.test",
            "mock_patterns": [],
            "test_dir": "tests"
        })
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out

    def test_finds_real_tests_by_function_name(self, tmp_path):
        make_test_file(tmp_path, "test_feature.py", """
            def test_real_test_db_persist():
                assert True

            def test_unit_logic():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out
        assert "test_real_test_db_persist" in out

    def test_no_real_tests_with_active_features_fails(self, tmp_path):
        make_test_file(tmp_path, "test_stuff.py", """
            def test_normal():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 1
        assert "FAIL" in out
        assert "No real tests found" in out


class TestMockWarnings:
    """Mock patterns correctly flagged as warnings in real test bodies."""

    def test_mock_in_real_test_warns(self, tmp_path):
        make_test_file(tmp_path, "test_service.py", """
            from unittest.mock import MagicMock
            import pytest

            @pytest.mark.real_test
            def test_real_api_call():
                client = MagicMock()
                client.get.return_value = {"ok": True}
                assert client.get()["ok"] is True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "WARN" in out
        assert "Mock warnings" in out
        assert "MagicMock" in out

    def test_mock_patch_in_real_test_warns(self, tmp_path):
        make_test_file(tmp_path, "test_config.py", """
            from unittest import mock
            import pytest

            @pytest.mark.real_test
            def test_real_config():
                with mock.patch("os.getenv", return_value="test_key"):
                    pass
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2
        assert "mock\\.patch" in out or "mock.patch" in out

    def test_no_mock_in_real_test_passes(self, tmp_path):
        make_test_file(tmp_path, "test_clean.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db():
                # No mock usage here — truly real
                result = 1 + 1
                assert result == 2
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "PASS" in out

    def test_mock_in_regular_test_not_flagged(self, tmp_path):
        """Mock in a non-real test should not generate warnings."""
        make_test_file(tmp_path, "test_mixed.py", """
            from unittest.mock import MagicMock
            import pytest

            @pytest.mark.real_test
            def test_real_clean():
                assert True

            def test_normal_with_mock():
                m = MagicMock()
                assert m is not None
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Mock warnings" not in out


class TestSkipWarnings:
    """Skip patterns correctly flagged as warnings in real test bodies (Anti-Pattern #16)."""

    def test_env_guard_return_warns(self, tmp_path):
        """if not os.environ.get(...): return → skip warning."""
        make_test_file(tmp_path, "test_db.py", """
            import os
            import pytest

            @pytest.mark.real_test
            def test_real_db_write():
                db_url = os.environ.get("DATABASE_URL")
                if not os.environ.get("DATABASE_URL"):
                    return
                assert db_url is not None
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "Skip warnings" in out
        assert "test_real_db_write" in out

    def test_pytest_skipif_warns(self, tmp_path):
        """pytest.mark.skipif in real test body → skip warning."""
        make_test_file(tmp_path, "test_service.py", """
            import os
            import pytest

            @pytest.mark.real_test
            @pytest.mark.skipif(not os.environ.get("API_KEY"), reason="no key")
            def test_real_api():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "Skip warnings" in out
        assert "skipif" in out.lower() or "skip_pattern" in out.lower()

    def test_unittest_skip_warns(self, tmp_path):
        """unittest.skip in real test body → skip warning."""
        make_test_file(tmp_path, "test_compat.py", """
            import unittest
            import pytest

            @pytest.mark.real_test
            @unittest.skip("infra not available")
            def test_real_compat():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "Skip warnings" in out

    def test_no_skip_pattern_passes(self, tmp_path):
        """Real test without skip patterns → no skip warnings."""
        make_test_file(tmp_path, "test_clean.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Skip warnings" not in out

    def test_skip_in_regular_test_not_flagged(self, tmp_path):
        """Skip pattern in a non-real test should not generate warnings."""
        make_test_file(tmp_path, "test_mixed.py", """
            import os
            import pytest

            @pytest.mark.real_test
            def test_real_clean():
                assert True

            def test_normal_with_skip():
                if not os.environ.get("OPTIONAL_VAR"):
                    return
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Skip warnings" not in out

    def test_custom_skip_patterns(self, tmp_path):
        """Custom skip_patterns in config are respected."""
        make_test_file(tmp_path, "test_custom.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_custom():
                # SKIP_IF_NO_INFRA
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "real_test",
            "mock_patterns": [],
            "skip_patterns": ["SKIP_IF_NO_INFRA"],
            "test_dir": "tests"
        })
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "Skip warnings" in out

    def test_skip_warning_json_output(self, tmp_path):
        """JSON output includes skip_warnings field."""
        make_test_file(tmp_path, "test_db.py", """
            import os
            import pytest

            @pytest.mark.real_test
            def test_real_db():
                if not os.environ.get("DB_URL"):
                    return
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--json")
        assert code == 2
        data = json.loads(out)
        assert data["verdict"] == "WARN"
        assert "skip_warnings" in data
        assert len(data["skip_warnings"]) >= 1
        assert data["skip_warnings"][0]["func_name"] == "test_real_db"
        assert "skip_pattern" in data["skip_warnings"][0]

    def test_both_mock_and_skip_warns(self, tmp_path):
        """Real test with both mock and skip patterns → WARN with both warning types."""
        make_test_file(tmp_path, "test_both.py", """
            import os
            from unittest.mock import MagicMock
            import pytest

            @pytest.mark.real_test
            def test_real_both():
                if not os.environ.get("DB_URL"):
                    return
                client = MagicMock()
                assert client is not None
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl)
        assert code == 2  # WARN
        assert "Mock warnings" in out
        assert "Skip warnings" in out


class TestFeatureFiltering:
    """--feature flag filters to specific feature."""

    def test_feature_filter(self, tmp_path):
        make_test_file(tmp_path, "test_auth.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_auth_feature_1():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
            {"id": 2, "category": "core", "title": "F2", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        assert "Active features: 1" in out

    def test_feature_filter_nonexistent(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
        ])
        (tmp_path / "tests").mkdir()
        code, out, _ = run_script(fl, "--feature", "99")
        assert code == 1
        assert "not found" in out


class TestDeprecatedFeatures:
    """Deprecated features are excluded from active count."""

    def test_deprecated_excluded(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "passing",
             "verification_steps": ["step1"],
             "deprecated": True, "deprecated_reason": "superseded"},
        ])
        (tmp_path / "tests").mkdir()
        code, out, _ = run_script(fl)
        assert code == 0  # No active features = PASS
        assert "Active features: 0" in out


class TestJsonOutput:
    """--json flag produces valid JSON output."""

    def test_json_output(self, tmp_path):
        make_test_file(tmp_path, "test_x.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_x():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--json")
        assert code == 0
        data = json.loads(out)
        assert data["verdict"] == "PASS"
        assert isinstance(data["real_tests"], list)
        assert len(data["real_tests"]) == 1
        assert data["real_tests"][0]["func_name"] == "test_real_x"


class TestPerFeatureAssociation:
    """Per-feature real test association checking."""

    def test_feature_ref_in_func_name(self, tmp_path):
        """Function name containing feature_N associates the test."""
        make_test_file(tmp_path, "test_login.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_feature_1_login():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        assert "Feature 1: 1 real tests" in out

    def test_feature_ref_in_comment(self, tmp_path):
        """Comment in function body containing feature reference associates the test."""
        make_test_file(tmp_path, "test_api.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_api_call():
                # feature:2 - verifies API connectivity
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 2, "category": "core", "title": "F2", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--feature", "2")
        assert code == 0
        assert "Feature 2: 1 real tests" in out

    def test_feature_ref_in_filename(self, tmp_path):
        """File name containing feature_N associates all real tests in it."""
        make_test_file(tmp_path, "test_feature_3_db.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db_persist():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 3, "category": "core", "title": "F3", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--feature", "3")
        assert code == 0
        assert "Feature 3: 1 real tests" in out

    def test_no_feature_ref_fails_with_feature_flag(self, tmp_path):
        """--feature N fails when no real test references feature N."""
        make_test_file(tmp_path, "test_generic.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_generic():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 1
        assert "No real tests associated with feature 1" in out

    def test_feature_ref_no_cross_match(self, tmp_path):
        """feature_1 does not match feature_10."""
        make_test_file(tmp_path, "test_login.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_feature_10_something():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 1
        assert "No real tests associated with feature 1" in out

    def test_global_check_reports_missing_features(self, tmp_path):
        """Global check (no --feature) reports features without real tests."""
        make_test_file(tmp_path, "test_auth.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_feature_1_auth():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
            {"id": 2, "category": "core", "title": "F2", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
        ])
        code, out, _ = run_script(fl)
        # Global check still PASS (real tests exist overall)
        assert code == 0
        assert "Feature 1: 1 real tests" in out
        assert "Feature 2: 0 real tests" in out
        assert "MISSING" in out

    def test_per_feature_json_output(self, tmp_path):
        """JSON output includes per_feature and features_without_real_tests."""
        make_test_file(tmp_path, "test_feature_1.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
            {"id": 2, "category": "core", "title": "F2", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]},
        ])
        code, out, _ = run_script(fl, "--json")
        assert code == 0
        data = json.loads(out)
        assert "per_feature" in data
        assert len(data["per_feature"]["1"]) == 1
        assert data["per_feature"]["2"] == []
        assert 2 in data["features_without_real_tests"]
        assert 1 not in data["features_without_real_tests"]

    def test_custom_feature_ref_pattern(self, tmp_path):
        """Custom feature_ref_pattern is respected."""
        make_test_file(tmp_path, "test_auth.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_auth():
                # covers: F-001
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "real_test",
            "mock_patterns": [],
            "test_dir": "tests",
            "feature_ref_pattern": r"F-0*{id}(?!\d)"
        })
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        assert "Feature 1: 1 real tests" in out


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_missing_feature_list(self, tmp_path):
        code, out, _ = run_script(str(tmp_path / "nonexistent.json"))
        assert code == 1

    def test_invalid_json(self, tmp_path):
        bad_file = tmp_path / "feature-list.json"
        bad_file.write_text("not json", encoding="utf-8")
        code, out, _ = run_script(str(bad_file))
        assert code == 1

    def test_empty_test_dir(self, tmp_path):
        fl = make_feature_list(tmp_path, features=[])
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        code, out, _ = run_script(fl)
        assert code == 0

    def test_invalid_marker_pattern(self, tmp_path):
        """Invalid regex in marker_pattern should not crash."""
        make_test_file(tmp_path, "test_x.py", """
            def test_something():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "[invalid regex",
            "mock_patterns": [],
            "test_dir": "tests"
        })
        code, out, _ = run_script(fl)
        assert code == 1  # No real tests found with invalid pattern

    def test_custom_test_dir(self, tmp_path):
        """Custom test_dir is respected."""
        custom_dir = tmp_path / "src" / "test"
        custom_dir.mkdir(parents=True)
        test_file = custom_dir / "test_feature.py"
        test_file.write_text(textwrap.dedent("""
            import pytest

            @pytest.mark.real_test
            def test_real_feature():
                assert True
        """), encoding="utf-8")

        fl = make_feature_list(tmp_path, features=[
            {"id": 1, "category": "core", "title": "F1", "description": "d",
             "priority": "high", "status": "failing",
             "verification_steps": ["step1"]}
        ], real_test={
            "marker_pattern": "real_test",
            "mock_patterns": [],
            "test_dir": "src/test"
        })
        code, out, _ = run_script(fl)
        assert code == 0
        assert "Real tests found: 1" in out


class TestRequireForDeps:
    """Tests for --require-for-deps cross-check."""

    def _feature(self, fid=1):
        return {"id": fid, "category": "core", "title": f"F{fid}",
                "description": "d", "priority": "high", "status": "failing",
                "verification_steps": ["step1"]}

    def _conn_configs(self, feature_id=1):
        """required_configs with connection-string keys for a feature."""
        return [
            {"name": "Database URL", "type": "env", "key": "DATABASE_URL",
             "description": "PostgreSQL", "required_by": [feature_id]},
            {"name": "Redis Host", "type": "env", "key": "REDIS_HOST",
             "description": "Redis cache", "required_by": [feature_id]},
        ]

    def test_deps_no_real_tests_fails(self, tmp_path):
        """Feature with connection-string deps but no real tests -> FAIL."""
        make_test_file(tmp_path, "test_f1.py", """
            def test_unit():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[self._feature()],
                               required_configs=self._conn_configs())
        code, out, _ = run_script(fl, "--feature", "1", "--require-for-deps")
        assert code == 1
        assert "has external dependencies" in out
        assert "DATABASE_URL" in out
        assert "Pure-function exemption is NOT allowed" in out

    def test_deps_with_real_tests_passes(self, tmp_path):
        """Feature with deps AND real tests -> PASS."""
        make_test_file(tmp_path, "test_f1.py", """
            import pytest

            @pytest.mark.real_test
            def test_real_db_feature_1():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[self._feature()],
                               required_configs=self._conn_configs())
        code, out, _ = run_script(fl, "--feature", "1", "--require-for-deps")
        assert code == 0
        assert "PASS" in out

    def test_no_deps_no_real_tests_existing_behavior(self, tmp_path):
        """Feature without deps and no real tests -> existing FAIL (no dep message)."""
        make_test_file(tmp_path, "test_f1.py", """
            def test_unit():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[self._feature()])
        code, out, _ = run_script(fl, "--feature", "1", "--require-for-deps")
        assert code == 1
        assert "has external dependencies" not in out

    def test_flag_off_no_crosscheck(self, tmp_path):
        """Without --require-for-deps, deps don't affect verdict."""
        make_test_file(tmp_path, "test_f1.py", """
            def test_unit():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[self._feature()],
                               required_configs=self._conn_configs())
        # Without --require-for-deps, existing behavior applies
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 1  # FAIL because no real tests for active feature
        assert "has external dependencies" not in out

    def test_non_connection_configs_no_enforcement(self, tmp_path):
        """Configs without connection keywords don't trigger enforcement."""
        make_test_file(tmp_path, "test_f1.py", """
            def test_unit():
                assert True
        """)
        non_conn_configs = [
            {"name": "API Key", "type": "env", "key": "API_KEY",
             "description": "API key", "required_by": [1]},
        ]
        fl = make_feature_list(tmp_path, features=[self._feature()],
                               required_configs=non_conn_configs)
        code, out, _ = run_script(fl, "--feature", "1", "--require-for-deps")
        assert code == 1  # FAIL because no real tests
        assert "has external dependencies" not in out  # no dep enforcement

    def test_deps_for_different_feature_no_enforcement(self, tmp_path):
        """Configs required_by a different feature don't affect current feature."""
        make_test_file(tmp_path, "test_f2.py", """
            def test_unit():
                assert True
        """)
        configs = [
            {"name": "DB", "type": "env", "key": "DATABASE_URL",
             "description": "DB", "required_by": [1]},  # required by feature 1, not 2
        ]
        fl = make_feature_list(tmp_path, features=[self._feature(2)],
                               required_configs=configs)
        code, out, _ = run_script(fl, "--feature", "2", "--require-for-deps")
        assert code == 1  # FAIL because no real tests
        assert "has external dependencies" not in out

    def test_json_output_includes_dep_info(self, tmp_path):
        """JSON output includes has_external_deps and dep_configs."""
        make_test_file(tmp_path, "test_f1.py", """
            def test_unit():
                assert True
        """)
        fl = make_feature_list(tmp_path, features=[self._feature()],
                               required_configs=self._conn_configs())
        code, out, _ = run_script(fl, "--feature", "1", "--require-for-deps", "--json")
        assert code == 1
        result = json.loads(out)
        assert result["has_external_deps"] is True
        assert "DATABASE_URL" in result["dep_configs"]
        assert "REDIS_HOST" in result["dep_configs"]
