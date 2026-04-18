#!/usr/bin/env python3
"""Unit tests for phase_route.py"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "phase_route.py")


def run(root, *extra):
    r = subprocess.run(
        [sys.executable, SCRIPT_PATH, "--root", root, "--json", *extra],
        capture_output=True, text=True
    )
    data = json.loads(r.stdout) if r.stdout.strip() else None
    return r.returncode, data, r.stderr


def _write(root, rel, content=""):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _feat(id_, sub_status=None, status="failing", deprecated=False):
    d = {"id": id_, "category": "core", "title": f"T{id_}",
         "description": "D", "priority": "high", "status": status}
    if sub_status is not None:
        d["sub_status"] = sub_status
    if deprecated:
        d["deprecated"] = True
        d["deprecated_reason"] = "obsolete"
    return d


def _fl(root, features, **extra):
    data = {"project": "p", "features": features, **extra}
    with open(os.path.join(root, "feature-list.json"), "w") as f:
        json.dump(data, f)


def test_greenfield_empty_routes_to_requirements():
    with tempfile.TemporaryDirectory() as d:
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-requirements"
        assert out["ok"] is True
        assert out["counts"] is None


def test_brownfield_heuristic_routes_to_scan():
    with tempfile.TemporaryDirectory() as d:
        # Simulate brownfield: >3 source files + >=5 git commits
        for i in range(5):
            _write(d, f"src/a{i}.py", "# start\n")
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
        for i in range(5):
            _write(d, f"src/a{i}.py", f"x = {i}\n")
            subprocess.run(["git", "add", "."], cwd=d, check=True)
            subprocess.run(["git", "commit", "-qm", f"c{i}"], cwd=d, check=True)
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-brownfield-scan", out


def test_srs_only_routes_to_ucd():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-srs.md", "# SRS")
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-ucd"


def test_ucd_routes_to_design():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-srs.md", "# SRS")
        _write(d, "docs/plans/x-ucd.md", "# UCD")
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-design"


def test_design_routes_to_ats():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-design.md", "# Design")
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-ats"


def test_ats_routes_to_init():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-ats.md", "# ATS")
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-init"


def test_rules_only_routes_to_requirements():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/rules/README.md", "# rules")
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-requirements"


def test_bugfix_signal_has_highest_priority():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-ats.md", "# ATS")
        _write(d, "increment-request.json", "{}")
        _write(d, "bugfix-request.json", "{}")
        _fl(d, [_feat(1, "done", "passing")])
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-hotfix"


def test_increment_signal_over_feature_list():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "increment-request.json", "{}")
        _fl(d, [_feat(1, "tdd_pending")])
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-increment"


def test_post_init_design_bucket():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "design_pending"), _feat(2, "tdd_pending")])
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-work-design"
        assert out["counts"]["design"] == 1
        assert out["counts"]["tdd"] == 1


def test_post_init_tdd_bucket():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "tdd_pending"), _feat(2, "st_pending")])
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-work-tdd"


def test_post_init_st_bucket():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "st_pending"), _feat(2, "done", "passing")])
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-work-st"


def test_post_init_all_done_routes_to_system_st():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "done", "passing"), _feat(2, "done", "passing")])
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-st"


def test_needs_migration_flagged():
    with tempfile.TemporaryDirectory() as d:
        # feature without sub_status — counts as no_sub_status
        _fl(d, [_feat(1)])
        code, out, _ = run(d)
        assert code == 0
        assert out["needs_migration"] is True
        assert out["next_skill"] is None


def test_validation_failure_blocks_routing():
    with tempfile.TemporaryDirectory() as d:
        # sub_status=done requires status=passing — mismatch triggers validation error
        _fl(d, [_feat(1, "done", status="failing")])
        code, out, _ = run(d)
        assert code == 2
        assert out["ok"] is False
        assert len(out["errors"]) > 0
        assert out["next_skill"] is None


def test_empty_active_features_returns_null_next_skill():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "done", "passing", deprecated=True)])
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] is None
        assert out["counts"]["total"] == 0


def test_text_output_when_no_json_flag():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-srs.md", "# SRS")
        r = subprocess.run(
            [sys.executable, SCRIPT_PATH, "--root", d],
            capture_output=True, text=True
        )
        assert r.returncode == 0
        assert "next=long-task-ucd" in r.stdout


if __name__ == "__main__":
    tests = [
        test_greenfield_empty_routes_to_requirements,
        test_brownfield_heuristic_routes_to_scan,
        test_srs_only_routes_to_ucd,
        test_ucd_routes_to_design,
        test_design_routes_to_ats,
        test_ats_routes_to_init,
        test_rules_only_routes_to_requirements,
        test_bugfix_signal_has_highest_priority,
        test_increment_signal_over_feature_list,
        test_post_init_design_bucket,
        test_post_init_tdd_bucket,
        test_post_init_st_bucket,
        test_post_init_all_done_routes_to_system_st,
        test_needs_migration_flagged,
        test_validation_failure_blocks_routing,
        test_empty_active_features_returns_null_next_skill,
        test_text_output_when_no_json_flag,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
