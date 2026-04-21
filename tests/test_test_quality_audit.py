"""Meta-tests for scripts/test_quality_audit.py."""
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# [no integration test] — pure function; CLI tested via subprocess as unit tests
# [unit]

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SCRIPT = REPO_ROOT / "skills" / "using-long-task" / "scripts" / "test_quality_audit.py"
sys.path.insert(0, str(AUDIT_SCRIPT.parent))
import test_quality_audit as tqa  # type: ignore


def _write_tests(tmp_path: Path, content: str) -> Path:
    # WRONG_IMPL: helper returns wrong path; helper writes without trailing newline
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_sample.py"
    f.write_text(textwrap.dedent(content), encoding="utf-8")
    return tests_dir


# [unit]
def test_classify_assert_flags_is_not_none_as_low_value():
    # WRONG_IMPL: classify returns 'ok' for is-not-None; returns uppercase 'LOW_VALUE'
    import ast
    # arrange
    node = ast.parse("assert x is not None").body[0]
    # act
    verdict = tqa._classify_assert(node)
    # assert
    assert verdict == "low_value"


# [unit]
def test_classify_assert_flags_isinstance_as_low_value():
    # WRONG_IMPL: classify returns 'ok' for isinstance; ignores Call nodes
    import ast
    # arrange
    node = ast.parse("assert isinstance(x, int)").body[0]
    # act
    verdict = tqa._classify_assert(node)
    # assert
    assert verdict == "low_value"


# [unit]
def test_classify_assert_flags_len_gt_zero_as_low_value():
    # WRONG_IMPL: classify only checks len()==0 not len()>0; treats Gt as Lt
    import ast
    # arrange
    node = ast.parse("assert len(x) > 0").body[0]
    # act
    verdict = tqa._classify_assert(node)
    # assert
    assert verdict == "low_value"


# [unit]
def test_classify_assert_flags_membership_in_as_low_value():
    # WRONG_IMPL: 'in' compare treated as 'ok'; classify only handles '=='
    import ast
    # arrange
    node = ast.parse("assert 'key' in d").body[0]
    # act
    verdict = tqa._classify_assert(node)
    # assert
    assert verdict == "low_value"


# [unit]
def test_classify_assert_treats_specific_equality_as_ok():
    # WRONG_IMPL: classify treats all equality as low_value; ignores constant rhs
    import ast
    # arrange
    node = ast.parse("assert result == 42").body[0]
    # act
    verdict = tqa._classify_assert(node)
    # assert
    assert verdict == "ok"


# [unit]
def test_is_negative_test_catches_pytest_raises(tmp_path):
    # WRONG_IMPL: function returns True for every test; misses pytest.raises inside with
    # arrange
    src = textwrap.dedent("""
        import pytest
        def test_foo():
            with pytest.raises(ValueError):
                raise ValueError()
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    tree, _ = tqa._parse_file(str(f))
    func = tqa._test_functions(tree)[0]
    # act
    verdict = tqa._is_negative_test(func)
    # assert
    assert verdict is True


# [unit]
def test_is_negative_test_catches_http_status_code(tmp_path):
    # WRONG_IMPL: HTTP code detector returns True for 200; ignores Compare nodes
    # arrange
    src = textwrap.dedent("""
        def test_x():
            response = client.get('/')
            assert response.status_code == 401
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    tree, _ = tqa._parse_file(str(f))
    func = tqa._test_functions(tree)[0]
    # act
    verdict = tqa._is_negative_test(func)
    # assert
    assert verdict is True


# [unit]
def test_is_negative_test_name_pattern_recognized(tmp_path):
    # WRONG_IMPL: regex only matches '_error'; name pattern misses '_rejects_' and '_invalid_'
    # arrange
    src = "def test_login_rejects_empty_password():\n    assert True\n"
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    tree, _ = tqa._parse_file(str(f))
    func = tqa._test_functions(tree)[0]
    # act
    verdict = tqa._is_negative_test(func)
    # assert
    assert verdict is True


# [unit]
def test_is_negative_test_positive_test_not_flagged(tmp_path):
    # WRONG_IMPL: positive test flagged as negative (over-eager); name pattern over-matches
    # arrange
    src = "def test_login_returns_token():\n    assert token == 'abc'\n"
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    tree, _ = tqa._parse_file(str(f))
    func = tqa._test_functions(tree)[0]
    # act
    verdict = tqa._is_negative_test(func)
    # assert
    assert verdict is False


# [unit]
def test_wrong_impl_detection_requires_exact_prefix():
    # WRONG_IMPL: regex matches any 'WRONG' string; matches case-insensitively when shouldn't
    # arrange
    comments_ok = ["# WRONG_IMPL: returns hardcoded zero"]
    comments_missing = ["# just a comment", "# no wrong impl here"]
    # act
    found_ok = tqa._has_wrong_impl(comments_ok)
    found_missing = tqa._has_wrong_impl(comments_missing)
    # assert
    assert found_ok is True
    assert found_missing is False


# [unit]
def test_aaa_missing_returns_all_three_when_all_absent():
    # WRONG_IMPL: returns empty list; returns only 'arrange'
    # arrange
    comments = ["# WRONG_IMPL: x", "# some note"]
    # act
    missing = tqa._aaa_missing(comments)
    # assert
    assert set(missing) == {"arrange", "act", "assert"}


# [unit]
def test_aaa_missing_returns_empty_when_all_present():
    # WRONG_IMPL: returns non-empty even when all three present
    # arrange
    comments = ["# arrange", "# act", "# assert"]
    # act
    missing = tqa._aaa_missing(comments)
    # assert
    assert missing == []


# [unit]
def test_audit_file_counts_negative_tests_correctly(tmp_path):
    # WRONG_IMPL: counts all tests as negative; ignores pytest.raises and HTTP codes
    # arrange
    src = textwrap.dedent("""
        import pytest

        def test_happy():
            # WRONG_IMPL: x
            # arrange
            # act
            # assert
            assert compute(2) == 4

        def test_rejects_empty():
            # WRONG_IMPL: x
            # arrange
            # act
            # assert
            with pytest.raises(ValueError):
                compute("")

        def test_returns_404_when_missing():
            # WRONG_IMPL: x
            # arrange
            # act
            # assert
            assert response.status_code == 404
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    # act
    report = tqa._audit_file(str(f))
    # assert
    assert report["total_tests"] == 3
    assert report["negative_tests"] == 2


# [unit]
def test_audit_file_flags_r4_missing_when_no_wrong_impl(tmp_path):
    # WRONG_IMPL: r4_missing stays 0 even when comment absent; detector looks at wrong line
    # arrange
    src = textwrap.dedent("""
        def test_foo():
            # arrange
            # act
            # assert
            assert 1 == 1
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    # act
    report = tqa._audit_file(str(f))
    # assert
    assert report["r4_missing"] == 1


# [unit]
def test_audit_file_flags_r6_missing_when_aaa_absent(tmp_path):
    # WRONG_IMPL: r6_missing ignores missing AAA; checks only one tag instead of three
    # arrange
    src = textwrap.dedent("""
        def test_foo():
            # WRONG_IMPL: x
            assert 1 == 1
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    # act
    report = tqa._audit_file(str(f))
    # assert
    assert report["r6_missing"] == 1


# [unit]
def test_audit_file_detects_r8_reflection_violation(tmp_path):
    # WRONG_IMPL: r8 detector ignores setattr on private; reports public setattr also
    # arrange
    src = textwrap.dedent("""
        def test_reflection_hack():
            # WRONG_IMPL: x
            # arrange
            obj = Thing()
            # act
            setattr(obj, '_internal', 42)
            # assert
            assert obj.result() == 42
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    # act
    report = tqa._audit_file(str(f))
    # assert
    assert report["r8_violations"] >= 1


# [unit]
def test_audit_file_detects_r9_private_access_violation(tmp_path):
    # WRONG_IMPL: r9 detector ignores underscore attrs; reports self._x as violation too
    # arrange
    src = textwrap.dedent("""
        def test_private_probe():
            # WRONG_IMPL: x
            # arrange
            obj = Thing()
            # act
            value = obj._secret_cache
            # assert
            assert value == "hello"
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    # act
    report = tqa._audit_file(str(f))
    # assert
    assert report["r9_violations"] >= 1


# [unit]
def test_audit_file_r9_allows_self_attributes(tmp_path):
    # WRONG_IMPL: self._foo flagged as private access (false positive on test class helpers)
    # arrange
    src = textwrap.dedent("""
        class TestX:
            def test_uses_self_attr(self):
                # WRONG_IMPL: x
                # arrange
                self._cache = {}
                # act
                self._cache['a'] = 1
                # assert
                assert self._cache == {'a': 1}
    """).strip()
    f = tmp_path / "test_x.py"
    f.write_text(src, encoding="utf-8")
    # act
    report = tqa._audit_file(str(f))
    # assert
    assert report["r9_violations"] == 0


# [unit]
def test_verdict_fails_on_low_negative_ratio():
    # WRONG_IMPL: returns 'pass' even when negative_ratio below 0.40; inverts comparison
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.20,
        "low_value_ratio": 0.0,
        "r4_missing": 0, "r6_missing": 0, "r8_violations": 0, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "fail"


# [unit]
def test_verdict_fails_on_high_low_value_ratio():
    # WRONG_IMPL: treats 0.20 as boundary inclusive; verdict returns 'pass' at 0.30
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.50,
        "low_value_ratio": 0.30,
        "r4_missing": 0, "r6_missing": 0, "r8_violations": 0, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "fail"


# [unit]
def test_verdict_fails_when_r4_missing_positive():
    # WRONG_IMPL: r4_missing > 0 still returns 'pass'; gate checks only R2/R3
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.50,
        "low_value_ratio": 0.10,
        "r4_missing": 3, "r6_missing": 0, "r8_violations": 0, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "fail"


# [unit]
def test_verdict_fails_when_r6_missing_positive():
    # WRONG_IMPL: r6_missing > 0 still returns 'pass'; AAA gate never trips
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.50,
        "low_value_ratio": 0.10,
        "r4_missing": 0, "r6_missing": 2, "r8_violations": 0, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "fail"


# [unit]
def test_verdict_fails_when_r8_violations_positive():
    # WRONG_IMPL: reflection gate skipped; r8 > 0 still returns 'pass'
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.50,
        "low_value_ratio": 0.10,
        "r4_missing": 0, "r6_missing": 0, "r8_violations": 1, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "fail"


# [unit]
def test_verdict_fails_when_r9_violations_positive():
    # WRONG_IMPL: private-access gate skipped; r9 > 0 still returns 'pass'
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.50,
        "low_value_ratio": 0.10,
        "r4_missing": 0, "r6_missing": 0, "r8_violations": 0, "r9_violations": 1,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "fail"


# [unit]
def test_verdict_passes_when_all_thresholds_met():
    # WRONG_IMPL: verdict returns 'fail' even when all thresholds met; verdict returns empty string
    # arrange
    agg = {
        "total_tests": 10,
        "negative_ratio": 0.50,
        "low_value_ratio": 0.10,
        "r4_missing": 0, "r6_missing": 0, "r8_violations": 0, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "pass"


# [unit]
def test_verdict_passes_when_zero_tests():
    # WRONG_IMPL: returns 'fail' for empty projects; divides by zero
    # arrange
    agg = {
        "total_tests": 0,
        "negative_ratio": 0.0,
        "low_value_ratio": 0.0,
        "r4_missing": 0, "r6_missing": 0, "r8_violations": 0, "r9_violations": 0,
    }
    # act
    verdict = tqa._verdict(agg)
    # assert
    assert verdict == "pass"


# [unit]
def test_cli_fails_with_exit_1_on_bad_tests(tmp_path):
    # WRONG_IMPL: exit code 0 for failing audit; script crashes on missing --target
    # arrange
    tests_dir = _write_tests(tmp_path, """
        def test_low_value_only():
            assert True
    """)
    # act
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--target", str(tests_dir),
         "--baseline-file", str(tmp_path / "baseline.json")],
        capture_output=True, text=True,
    )
    # assert
    assert result.returncode == 1


# [unit]
def test_cli_exit_2_when_no_test_files(tmp_path):
    # WRONG_IMPL: returns 0 for empty target; returns 1
    # arrange
    (tmp_path / "empty").mkdir()
    # act
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--target", str(tmp_path / "empty")],
        capture_output=True, text=True,
    )
    # assert
    assert result.returncode == 2


# [unit]
def test_cli_baseline_exempts_failing_files(tmp_path):
    # WRONG_IMPL: baseline ignores failing files but doesn't write them; baseline writes all files
    # arrange
    tests_dir = _write_tests(tmp_path, """
        def test_bad():
            assert True
    """)
    baseline = tmp_path / "baseline.json"
    # act
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--target", str(tests_dir),
         "--baseline", "--baseline-file", str(baseline)],
        capture_output=True, text=True,
    )
    # assert
    assert result.returncode == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert len(data["exempt_files"]) == 1


# [unit]
def test_cli_report_file_written_when_feature_id_given(tmp_path):
    # WRONG_IMPL: feature arg ignored; report written to wrong path
    # arrange
    tests_dir = _write_tests(tmp_path, """
        def test_good():
            # WRONG_IMPL: x
            # arrange
            # act
            # assert
            assert 1 + 1 == 2

        def test_rejects_invalid():
            # WRONG_IMPL: x
            # arrange
            # act
            # assert
            import pytest
            with pytest.raises(ValueError):
                raise ValueError()
    """)
    report_dir = tmp_path / "reports"
    # act
    subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--target", str(tests_dir),
         "--feature", "42", "--report-dir", str(report_dir),
         "--baseline-file", str(tmp_path / "baseline.json")],
        capture_output=True, text=True,
    )
    # assert
    out = report_dir / "test_quality_42.json"
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "verdict" in data
    assert "negative_ratio" in data
