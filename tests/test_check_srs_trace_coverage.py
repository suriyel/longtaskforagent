"""Tests for scripts/check_srs_trace_coverage.py"""

import json
import os
import subprocess
import sys
import textwrap


SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "check_srs_trace_coverage.py"
)


def run_script(feature_list_path, *extra_args):
    cmd = [sys.executable, SCRIPT, feature_list_path] + list(extra_args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def make_feature_list(tmp_path, features, language="python",
                      real_test=None):
    data = {
        "project": "trace-test",
        "created": "2025-01-01",
        "tech_stack": {
            "language": language,
            "test_framework": "pytest",
            "coverage_tool": "pytest-cov",
        },
        "quality_gates": {"line_coverage_min": 90, "branch_coverage_min": 80},
        "features": features,
    }
    if real_test is not None:
        data["real_test"] = real_test
    fl = tmp_path / "feature-list.json"
    fl.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(fl)


def make_test_file(tmp_path, filename, content):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    f = tests_dir / filename
    f.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(f)


class TestBasicCoverage:

    def test_single_fr_id_hit_in_function_name(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            def test_fr_001_login_success():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]}
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        assert "PASS" in out

    def test_single_fr_id_hit_in_comment(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            # Covers FR-001 acceptance criterion
            def test_login():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]}
        ])
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0

    def test_single_fr_id_hit_in_docstring(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", '''
            def test_login():
                """Validates FR-001 login success path."""
                assert True
        ''')
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]}
        ])
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0

    def test_one_uncovered_fr_id_fails(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            # Covers FR-001
            def test_login():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001", "FR-002"]}
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 1
        assert "FR-002" in out
        assert "UNCOVERED" in out

    def test_zero_coverage_fails(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            def test_login():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001", "FR-002"]}
        ])
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 1


class TestWordBoundary:

    def test_fr_1_does_not_match_fr_10(self, tmp_path):
        """Matching FR-1 must not match FR-10."""
        make_test_file(tmp_path, "test_feature_1.py", """
            # Covers FR-10 only
            def test_something():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "F",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-1"]}
        ])
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 1

    def test_nfr_id_matching(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            def test_perf_nfr_005():
                '''Latency NFR-005 budget assertion.'''
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Perf",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["NFR-005"]}
        ])
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0


class TestAliases:

    def test_alias_satisfies_coverage(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            def test_fr_001_login():
                # underscore alias used in test names
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"],
             "srs_trace_aliases": {"FR-001": ["fr_001"]}}
        ])
        # Even without the alias, "fr_001" would normally match the
        # literal pattern through case-insensitive hyphen-vs-underscore
        # failure; verify alias path works for non-trivial rewrites.
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0

    def test_nontrivial_alias_path(self, tmp_path):
        """FR-001 literal absent; alias '@srs-login' rescues coverage."""
        make_test_file(tmp_path, "test_feature_1.py", """
            # @srs-login primary flow
            def test_login():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"],
             "srs_trace_aliases": {"FR-001": ["@srs-login"]}}
        ])
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0


class TestScopeResolution:

    def test_feature_ref_filters_scope(self, tmp_path):
        """Only files referencing feature_id should be in scope."""
        # File refs feature 1, contains FR-001
        make_test_file(tmp_path, "test_feature_1.py", """
            # feature 1 — covers FR-001
            def test_login():
                assert True
        """)
        # File refs feature 2, contains FR-002 — not in scope for feature 1
        make_test_file(tmp_path, "test_feature_2.py", """
            # feature 2
            # The string FR-001 appears in an unrelated comment
            def test_unrelated():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]},
            {"id": 2, "category": "core", "title": "Other",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-002"]},
        ])
        # feature 1 has its own FR-001 anchor within the feature-1 file
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        # feature 2 has no FR-002 anywhere → uncovered
        code, out, _ = run_script(fl, "--feature", "2")
        assert code == 1

    def test_explicit_test_files_override(self, tmp_path):
        make_test_file(tmp_path, "test_other.py", """
            # FR-001 in an unrelated file
            def test_other():
                assert True
        """)
        make_test_file(tmp_path, "test_feature_1.py", """
            def test_login():
                assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]}
        ])
        # Explicit scope = test_feature_1.py only → FR-001 not present
        code, _, _ = run_script(
            fl, "--feature", "1",
            "--test-files", "tests/test_feature_1.py",
        )
        assert code == 1


class TestAllFeatures:

    def test_all_features_union_check(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            # feature 1 — FR-001
            def test_a(): assert True
        """)
        make_test_file(tmp_path, "test_feature_2.py", """
            # feature 2 — FR-002
            def test_b(): assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "F1",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]},
            {"id": 2, "category": "core", "title": "F2",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-002"]},
        ])
        code, out, _ = run_script(fl)
        assert code == 0
        assert "2 feature(s) checked" in out

    def test_deprecated_features_skipped(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            # feature 1 — FR-001
            def test_a(): assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "F1",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]},
            {"id": 2, "category": "core", "title": "F2-dead",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-999"],
             "deprecated": True, "deprecated_reason": "replaced"},
        ])
        code, out, _ = run_script(fl)
        # Deprecated feature not counted → 1 checked, FR-999 NOT required
        assert code == 0
        assert "1 feature(s) checked" in out


class TestEdgeCases:

    def test_feature_without_srs_trace_is_noop(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            def test_login(): assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "F1",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": []}
        ])
        code, out, _ = run_script(fl, "--feature", "1")
        assert code == 0
        assert "no srs_trace declared" in out

    def test_missing_feature_id(self, tmp_path):
        fl = make_feature_list(tmp_path, [])
        (tmp_path / "tests").mkdir()
        code, _, _ = run_script(fl, "--feature", "42")
        assert code == 2

    def test_missing_feature_list_file(self, tmp_path):
        code, _, _ = run_script(str(tmp_path / "nope.json"))
        assert code == 2

    def test_malformed_json(self, tmp_path):
        fl = tmp_path / "feature-list.json"
        fl.write_text("not json", encoding="utf-8")
        code, _, _ = run_script(str(fl))
        assert code == 2

    def test_json_output_shape(self, tmp_path):
        make_test_file(tmp_path, "test_feature_1.py", """
            # FR-001
            def test_a(): assert True
        """)
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "F1",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001", "FR-404"]}
        ])
        code, out, _ = run_script(fl, "--feature", "1", "--json")
        assert code == 1
        data = json.loads(out)
        assert data["verdict"] == "FAIL"
        assert data["uncovered_total"] == 1
        assert data["per_feature"][0]["uncovered_fr_ids"] == ["FR-404"]


class TestLanguageSupport:

    def test_java_test_file_discovery(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "LoginTest.java").write_text(textwrap.dedent("""
            // feature 1 — covers FR-001
            class LoginTest {
                @Test
                void testLogin() {}
            }
        """), encoding="utf-8")
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]}
        ], language="java")
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0

    def test_typescript_test_file_discovery(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "login.test.ts").write_text(textwrap.dedent("""
            // feature 1 — FR-001
            it('logs in', () => {});
        """), encoding="utf-8")
        fl = make_feature_list(tmp_path, [
            {"id": 1, "category": "core", "title": "Login",
             "description": "d", "priority": "high", "status": "failing",
             "srs_trace": ["FR-001"]}
        ], language="typescript")
        code, _, _ = run_script(fl, "--feature", "1")
        assert code == 0
