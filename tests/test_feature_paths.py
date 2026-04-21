#!/usr/bin/env python3
"""Unit tests for skills/using-long-task/scripts/feature_paths.py"""

import json
import os
import subprocess
import sys
import tempfile

# Import module under test
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "using-long-task", "scripts")
sys.path.insert(0, SCRIPTS)
import feature_paths  # noqa: E402

SCRIPT_PATH = os.path.join(SCRIPTS, "feature_paths.py")


# ---- slugify() unit tests ----

def test_slugify_ascii_kebab_case():
    assert feature_paths.slugify("Login API (v2)") == "login-api-v2"
    assert feature_paths.slugify("POST /auth/refresh") == "post-auth-refresh"


def test_slugify_cjk_preserved():
    assert feature_paths.slugify("用户登录接口") == "用户登录接口"
    assert feature_paths.slugify("订单管理") == "订单管理"


def test_slugify_mixed_ascii_cjk():
    assert feature_paths.slugify("Login 登录 API") == "login-登录-api"


def test_slugify_empty_or_all_specials_fallback_untitled():
    assert feature_paths.slugify("") == "untitled"
    assert feature_paths.slugify("   ---  ") == "untitled"
    assert feature_paths.slugify("!!!???") == "untitled"
    assert feature_paths.slugify("🚀 ") == "untitled"


def test_slugify_length_cap_40_utf8_safe():
    long_en = "A" * 50
    assert len(feature_paths.slugify(long_en)) == 40
    # CJK at boundary: 40 codepoints (not bytes)
    long_cjk = "字" * 50
    slug = feature_paths.slugify(long_cjk)
    assert len(slug) == 40
    assert all(0x4E00 <= ord(c) <= 0x9FFF for c in slug)


def test_slugify_trailing_dash_trimmed_after_truncation():
    # 38 chars followed by '-x' — truncate to 40 → 'aaa...-' → rstrip → 'aaa...'
    title = "a" * 38 + " x"
    slug = feature_paths.slugify(title)
    assert not slug.endswith("-")
    assert len(slug) <= 40


def test_slugify_merges_repeated_separators():
    assert feature_paths.slugify("foo   bar___baz...qux") == "foo-bar-baz-qux"


# ---- design_doc_path() unit tests ----

def test_design_doc_path_format():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "A"}]}, f)
        assert feature_paths.design_doc_path(fl, 1) == "docs/features/1-a.md"


def test_design_doc_path_cjk_title():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 7, "title": "用户登录"}]}, f, ensure_ascii=False)
        assert feature_paths.design_doc_path(fl, 7) == "docs/features/7-用户登录.md"


def test_design_doc_path_raises_feature_not_found():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "A"}]}, f)
        try:
            feature_paths.design_doc_path(fl, 999)
        except feature_paths.FeatureNotFound as e:
            assert e.feature_id == 999
        else:
            raise AssertionError("expected FeatureNotFound")


# ---- CLI integration tests ----

def _run_cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, SCRIPT_PATH] + args,
        capture_output=True, text=True, cwd=cwd,
    )


def test_cli_basic_stdout_path():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "Login API (v2)"}]}, f)
        r = _run_cli(["design-doc", "--feature", "1"], cwd=d)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == "docs/features/1-login-api-v2.md"


def test_cli_must_exist_missing_returns_1():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "A"}]}, f)
        r = _run_cli(["design-doc", "--feature", "1", "--must-exist"], cwd=d)
        assert r.returncode == 1
        assert "Design doc not on disk" in r.stderr


def test_cli_must_exist_present_returns_0():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "A"}]}, f)
        # create the target file
        os.makedirs(os.path.join(d, "docs", "features"))
        target = os.path.join(d, "docs", "features", "1-a.md")
        with open(target, "w") as f:
            f.write("# design\n")
        r = _run_cli(["design-doc", "--feature", "1", "--must-exist"], cwd=d)
        assert r.returncode == 0, r.stderr


def test_cli_feature_id_not_found_returns_3():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "A"}]}, f)
        r = _run_cli(["design-doc", "--feature", "999"], cwd=d)
        assert r.returncode == 3
        assert "not found" in r.stderr


def test_cli_feature_list_missing_returns_2():
    with tempfile.TemporaryDirectory() as d:
        r = _run_cli(["design-doc", "--feature", "1"], cwd=d)
        assert r.returncode == 2
        assert "feature-list.json not found" in r.stderr


def test_cli_json_output():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "feature-list.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 1, "title": "Login API"}]}, f)
        r = _run_cli(["design-doc", "--feature", "1", "--json"], cwd=d)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out == {
            "path": "docs/features/1-login-api.md",
            "exists": False,
            "feature_id": 1,
            "slug": "login-api",
        }


def test_cli_explicit_feature_list_path():
    with tempfile.TemporaryDirectory() as d:
        fl = os.path.join(d, "custom-fl.json")
        with open(fl, "w", encoding="utf-8") as f:
            json.dump({"features": [{"id": 2, "title": "B"}]}, f)
        # Run from a different cwd; pass --feature-list
        with tempfile.TemporaryDirectory() as other:
            r = _run_cli(["design-doc", "--feature", "2", "--feature-list", fl], cwd=other)
            assert r.returncode == 0, r.stderr
            assert r.stdout.strip() == "docs/features/2-b.md"


# ---- srs-doc CLI tests ----

def test_cli_srs_doc_single_match():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        target = os.path.join(d, "docs", "plans", "2026-04-21-auth-srs.md")
        with open(target, "w") as f:
            f.write("# SRS\n")
        r = _run_cli(["srs-doc"], cwd=d)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == os.path.join("docs", "plans", "2026-04-21-auth-srs.md")


def test_cli_srs_doc_multiple_picks_latest_by_name():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        for name in ("2026-01-10-alpha-srs.md", "2026-04-21-beta-srs.md", "2026-03-02-gamma-srs.md"):
            with open(os.path.join(d, "docs", "plans", name), "w") as f:
                f.write("# SRS\n")
        r = _run_cli(["srs-doc"], cwd=d)
        assert r.returncode == 0, r.stderr
        # Lexicographic max = 2026-04-21-beta-srs.md (date prefix sorts)
        assert r.stdout.strip() == os.path.join("docs", "plans", "2026-04-21-beta-srs.md")


def test_cli_srs_doc_zero_returns_4():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        r = _run_cli(["srs-doc"], cwd=d)
        assert r.returncode == 4
        assert "SRS doc not found" in r.stderr


def test_cli_srs_doc_json_output():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        target_name = "2026-04-21-auth-srs.md"
        with open(os.path.join(d, "docs", "plans", target_name), "w") as f:
            f.write("# SRS\n")
        r = _run_cli(["srs-doc", "--json"], cwd=d)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out == {"path": os.path.join("docs", "plans", target_name), "exists": True}


# ---- system-design-doc CLI tests ----

def test_cli_system_design_doc_single_match():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        target = os.path.join(d, "docs", "plans", "2026-04-21-auth-design.md")
        with open(target, "w") as f:
            f.write("# Design\n")
        r = _run_cli(["system-design-doc"], cwd=d)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == os.path.join("docs", "plans", "2026-04-21-auth-design.md")


def test_cli_system_design_doc_multiple_picks_latest_by_name():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        for name in ("2026-02-14-v1-design.md", "2026-04-21-v2-design.md", "2026-03-15-v1-5-design.md"):
            with open(os.path.join(d, "docs", "plans", name), "w") as f:
                f.write("# Design\n")
        r = _run_cli(["system-design-doc"], cwd=d)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == os.path.join("docs", "plans", "2026-04-21-v2-design.md")


def test_cli_system_design_doc_zero_returns_5():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        r = _run_cli(["system-design-doc"], cwd=d)
        assert r.returncode == 5
        assert "System design doc not found" in r.stderr


def test_cli_system_design_doc_json_output():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "docs", "plans"))
        target_name = "2026-04-21-auth-design.md"
        with open(os.path.join(d, "docs", "plans", target_name), "w") as f:
            f.write("# Design\n")
        r = _run_cli(["system-design-doc", "--json"], cwd=d)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out == {"path": os.path.join("docs", "plans", target_name), "exists": True}


if __name__ == "__main__":
    import traceback
    tests = [fn for name, fn in globals().items() if name.startswith("test_") and callable(fn)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception:
            print(f"  FAIL: {t.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
