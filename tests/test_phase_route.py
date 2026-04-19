#!/usr/bin/env python3
"""Unit tests for phase_route.py (current-lock routing)."""

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


def _feat(id_, status="failing", deps=None, priority="high", deprecated=False):
    d = {"id": id_, "category": "core", "title": f"T{id_}",
         "description": "D", "priority": priority, "status": status}
    if deps is not None:
        d["dependencies"] = deps
    if deprecated:
        d["deprecated"] = True
        d["deprecated_reason"] = "obsolete"
    return d


def _fl(root, features, current=None, **extra):
    data = {"project": "p", "features": features, "current": current, **extra}
    with open(os.path.join(root, "feature-list.json"), "w") as f:
        json.dump(data, f)


# --- Pre-init ladder (unchanged) ---

def test_greenfield_empty_routes_to_requirements():
    with tempfile.TemporaryDirectory() as d:
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-requirements"
        assert out["ok"] is True
        assert out["counts"] is None


def test_brownfield_heuristic_routes_to_scan():
    with tempfile.TemporaryDirectory() as d:
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


# --- Signal file priority ---

def test_bugfix_signal_has_highest_priority():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "docs/plans/x-ats.md", "# ATS")
        _write(d, "increment-request.json", "{}")
        _write(d, "bugfix-request.json", "{}")
        _fl(d, [_feat(1, "passing")])
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-hotfix"


def test_increment_signal_over_feature_list():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "increment-request.json", "{}")
        _fl(d, [_feat(1)], current={"feature_id": 1, "phase": "tdd"})
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-increment"


# --- Post-init current-lock routing ---

def test_current_design_routes_to_work_design():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1), _feat(2)],
            current={"feature_id": 1, "phase": "design"})
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-work-design"
        assert out["feature_id"] == 1
        assert out["starting_new"] is False


def test_current_tdd_routes_to_work_tdd():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1), _feat(2)],
            current={"feature_id": 2, "phase": "tdd"})
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-work-tdd"
        assert out["feature_id"] == 2


def test_current_st_routes_to_work_st():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1)],
            current={"feature_id": 1, "phase": "st"})
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-work-st"
        assert out["feature_id"] == 1


# --- Null current: pick next ---

def test_current_null_picks_dep_ready_feature():
    with tempfile.TemporaryDirectory() as d:
        # F1 depends on F2; F2 has no deps → F2 picked first
        _fl(d, [_feat(1, deps=[2]), _feat(2)], current=None)
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-work-design"
        assert out["feature_id"] == 2
        assert out["starting_new"] is True


def test_current_null_all_passing_routes_to_system_st():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "passing"), _feat(2, "passing")], current=None)
        code, out, _ = run(d)
        assert out["next_skill"] == "long-task-st"
        assert out["feature_id"] is None


def test_current_null_all_dep_blocked_fails_loud():
    with tempfile.TemporaryDirectory() as d:
        # Dependency cycle: F1→F2, F2→F1
        _fl(d, [_feat(1, deps=[2]), _feat(2, deps=[1])], current=None)
        code, out, _ = run(d)
        assert code == 2
        assert out["ok"] is False
        assert out["next_skill"] is None
        assert any("dependency-ready" in e.lower() or "cycle" in e.lower()
                   for e in out["errors"])


def test_priority_beats_id_on_pick():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, deps=[], priority="medium"),
                _feat(2, deps=[], priority="high")],
            current=None)
        code, out, _ = run(d)
        assert out["feature_id"] == 2  # high beats medium


def test_priority_tie_lowest_id_wins():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(8, deps=[], priority="high"),
                _feat(9, deps=[], priority="high")],
            current=None)
        code, out, _ = run(d)
        assert out["feature_id"] == 8


def test_empty_active_features_returns_null_next_skill():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "passing", deprecated=True)], current=None)
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] is None
        assert out["counts"]["total"] == 0


# --- Dependency readiness semantics ---

def test_deprecated_dep_treated_as_unmet():
    """F1 depends on F2; F2 is deprecated + failing → F1 blocked."""
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, deps=[2]),
                _feat(2, "failing", deprecated=True)],
            current=None)
        code, out, _ = run(d)
        assert code == 2, out
        assert out["ok"] is False


def test_passing_dep_unblocks_pick():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "failing", deps=[2]),
                _feat(2, "passing")],
            current=None)
        code, out, _ = run(d)
        assert out["feature_id"] == 1


# --- Migration signal ---

def test_needs_migration_flagged():
    """Feature still carrying legacy sub_status field triggers migration."""
    with tempfile.TemporaryDirectory() as d:
        f = _feat(1)
        f["sub_status"] = "design_pending"  # legacy field
        _fl(d, [f], current=None)
        code, out, _ = run(d)
        assert code == 0
        assert out["needs_migration"] is True
        assert out["next_skill"] is None


# --- Invalid current structure ---

def test_invalid_current_phase_fails():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1)], current={"feature_id": 1, "phase": "bogus"})
        code, out, _ = run(d)
        assert code == 2
        assert out["ok"] is False


def test_current_references_nonexistent_feature_fails():
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1)], current={"feature_id": 999, "phase": "design"})
        code, out, _ = run(d)
        assert code == 2
        assert out["ok"] is False


def test_current_references_passing_feature_fails():
    """A feature in `current` must have status=failing (locked work in progress)."""
    with tempfile.TemporaryDirectory() as d:
        _fl(d, [_feat(1, "passing")], current={"feature_id": 1, "phase": "tdd"})
        code, out, _ = run(d)
        assert code == 2
        assert out["ok"] is False


# --- Reference scenario (from reference/feature-list.json) ---

def test_reference_scenario_post_migration():
    """F1..F7 + F9..F12 design-stage failing with dep chains; F8 tdd-stage,
    deps=[]. After migration, current should be F8 in tdd (smallest non-done
    pending id), and router should emit work-tdd for F8."""
    with tempfile.TemporaryDirectory() as d:
        features = [
            _feat(1, deps=[7, 8]),
            _feat(2, deps=[1, 7]),
            _feat(3, deps=[1, 7]),
            _feat(4, deps=[7]),
            _feat(5, deps=[7]),
            _feat(6, deps=[7]),
            _feat(7, deps=[8]),
            _feat(8, deps=[]),
            _feat(9, deps=[8]),
            _feat(10, deps=[1, 2, 9]),
            _feat(11, deps=[3, 9]),
            _feat(12, deps=[4, 5, 6, 9]),
        ]
        # Simulate migration output: F8 is current.tdd; others are plain failing
        _fl(d, features, current={"feature_id": 8, "phase": "tdd"})
        code, out, _ = run(d)
        assert code == 0
        assert out["next_skill"] == "long-task-work-tdd"
        assert out["feature_id"] == 8
        assert out["starting_new"] is False


# --- Text output ---

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
    import inspect
    tests = [t for name, t in sorted(globals().items())
             if name.startswith("test_") and inspect.isfunction(t)]
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
