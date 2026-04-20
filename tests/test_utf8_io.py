#!/usr/bin/env python3
"""Verify scripts emit valid UTF-8 stdout/stderr regardless of locale.

Root cause this guards against: on Windows with cp936 (GBK) locale, Python's
sys.stdout defaults to cp936. Claude Code reads subprocess stdout as UTF-8.
Chinese feature titles / path slugs written as GBK bytes get decoded as UTF-8
→ mojibake → LLM generates pinyin filenames that diverge from feature-list.json.

Each test forces a non-UTF-8 stdout encoding on the child via PYTHONIOENCODING
and asserts the output bytes decode cleanly as UTF-8 with CJK characters
preserved verbatim (no `\\uXXXX` escapes, no `?` replacements).
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "skills", "using-long-task", "scripts")

CJK_TITLE = "模式匹配"
CJK_REASON = "支持中文正则匹配模式"
CJK_SCOPE = "新增 pattern_match 模块"


def _run(script: str, *args, cwd=None, stdin_encoding="gbk"):
    """Run a script as subprocess with forced non-UTF-8 stdout encoding.

    Returns CompletedProcess with stdout/stderr captured as raw bytes.
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = stdin_encoding
    # Some CI environments propagate UTF-8 mode — disable it so the test
    # actually exercises the reconfigure() path.
    env["PYTHONUTF8"] = "0"
    env.pop("LC_ALL", None)
    env.pop("LANG", None)
    cmd = [sys.executable, os.path.join(SCRIPTS, script), *args]
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True)


def _make_feature_list(tmpdir, title=CJK_TITLE):
    fl = os.path.join(tmpdir, "feature-list.json")
    data = {
        "project": "utf8-io-test",
        "created": "2026-04-20",
        "tech_stack": {
            "language": "python",
            "test_framework": "pytest",
            "coverage_tool": "pytest-cov",
            "mutation_tool": "mutmut",
        },
        "constraints": [],
        "assumptions": [],
        "features": [{
            "id": 1,
            "category": "core",
            "title": title,
            "description": "…",
            "priority": "high",
            "status": "failing",
            "srs_trace": ["FR-001"],
            "dependencies": [],
        }],
        "current": None,
    }
    with open(fl, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return fl


# ---- feature_paths.py: prints path with CJK slug directly ----

def test_feature_paths_plain_output_is_utf8_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        fl = _make_feature_list(tmp)
        r = _run("feature_paths.py", "design-doc", "--feature", "1",
                 "--feature-list", fl)
        assert r.returncode == 0, r.stderr.decode("utf-8", errors="replace")
        # Must decode cleanly as UTF-8 (no cp936 bytes leaked)
        text = r.stdout.decode("utf-8")
        assert CJK_TITLE in text, f"CJK title missing, got: {text!r}"
        assert f"docs/features/1-{CJK_TITLE}.md" in text


def test_feature_paths_json_output_keeps_cjk_literal_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        fl = _make_feature_list(tmp)
        r = _run("feature_paths.py", "design-doc", "--feature", "1",
                 "--json", "--feature-list", fl)
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        payload = json.loads(text)
        # Literal CJK, not \uXXXX escapes visible in raw bytes
        assert payload["slug"] == CJK_TITLE
        assert CJK_TITLE.encode("utf-8") in r.stdout


def test_feature_paths_under_ascii_encoding_does_not_crash():
    """errors='replace' must prevent UnicodeEncodeError even with ASCII forced."""
    with tempfile.TemporaryDirectory() as tmp:
        fl = _make_feature_list(tmp)
        r = _run("feature_paths.py", "design-doc", "--feature", "1",
                 "--feature-list", fl, stdin_encoding="ascii")
        assert r.returncode == 0, r.stderr.decode("utf-8", errors="replace")
        # reconfigure() overrides PYTHONIOENCODING=ascii → still emits UTF-8
        text = r.stdout.decode("utf-8")
        assert CJK_TITLE in text


# ---- phase_route.py: JSON output with ensure_ascii=False ----

def test_phase_route_json_is_utf8_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        _make_feature_list(tmp)
        r = _run("phase_route.py", "--root", tmp, "--json", cwd=tmp)
        assert r.returncode == 0, r.stderr.decode("utf-8", errors="replace")
        text = r.stdout.decode("utf-8")
        payload = json.loads(text)
        assert payload["ok"] is True
        assert payload["next_skill"] == "long-task-work-design"
        assert payload["feature_id"] == 1


# ---- count_pending.py: JSON output, ensure_ascii=False ----

def test_count_pending_json_is_utf8_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        fl = _make_feature_list(tmp)
        r = _run("count_pending.py", fl, "--json")
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        payload = json.loads(text)
        assert payload["total"] == 1
        assert payload["failing"] == 1


# ---- get_tool_commands.py: caveat_prompts contain CJK ----

def test_get_tool_commands_json_keeps_cjk_literal_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        fl = _make_feature_list(tmp)
        r = _run("get_tool_commands.py", fl, "--json")
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        payload = json.loads(text)
        prompts = payload.get("caveat_prompts", [])
        assert any("检查" in p for p in prompts), \
            f"expected 检查 in caveat_prompts, got: {prompts}"
        # Bytes must contain literal UTF-8 of 检查, not \u68c0\u67e5 escapes
        assert "检查".encode("utf-8") in r.stdout
        assert rb"\u68c0\u67e5" not in r.stdout


def test_get_tool_commands_text_cjk_survives_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        fl = _make_feature_list(tmp)
        r = _run("get_tool_commands.py", fl)
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        assert "检查 conftest.py" in text or "检查 [tool.coverage]" in text


# ---- validate_bugfix_request.py: prints title (CJK) ----

def test_validate_bugfix_title_cjk_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        req = os.path.join(tmp, "bugfix-request.json")
        with open(req, "w", encoding="utf-8") as f:
            json.dump({
                "title": f"修复 {CJK_TITLE} 崩溃",
                "description": "崩溃描述",
                "expected_behavior": "正常返回",
                "actual_behavior": "抛出异常",
                "severity": "Major",
                "feature_id": None,
                "reproduction_steps": ["步骤一", "步骤二"],
            }, f, ensure_ascii=False)
        r = _run("validate_bugfix_request.py", req)
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        assert CJK_TITLE in text


# ---- validate_increment_request.py: prints reason & scope (CJK) ----

def test_validate_increment_reason_scope_cjk_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        req = os.path.join(tmp, "increment-request.json")
        with open(req, "w", encoding="utf-8") as f:
            json.dump({"reason": CJK_REASON, "scope": CJK_SCOPE},
                      f, ensure_ascii=False)
        r = _run("validate_increment_request.py", req)
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        assert CJK_REASON in text
        assert CJK_SCOPE in text


# ---- validate_features.py: warnings can contain CJK verification_steps ----

def test_validate_features_warning_cjk_under_gbk():
    with tempfile.TemporaryDirectory() as tmp:
        fl = os.path.join(tmp, "feature-list.json")
        data = {
            "project": "demo", "created": "2026-04-20",
            "tech_stack": {"language": "python", "test_framework": "pytest",
                           "coverage_tool": "pytest-cov", "mutation_tool": "mutmut"},
            "features": [{
                "id": 1, "category": "core", "title": CJK_TITLE,
                "description": "…", "priority": "high", "status": "failing",
                "srs_trace": ["FR-001"], "dependencies": [],
                # short, no chaining words → triggers a warning that echoes the step
                "verification_steps": ["简单断言"],
            }],
        }
        with open(fl, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        r = _run("validate_features.py", fl)
        assert r.returncode == 0
        text = r.stdout.decode("utf-8")
        assert "简单断言" in text
