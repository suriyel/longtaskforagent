"""Guard against drift between scripts/ and skills/using-long-task/scripts/.

Fails if the mirrored triplet isn't byte-identical — catches the degraded case
where a Windows clone lands real files instead of symlinks and someone edits
only one side.
"""
import hashlib
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANON = ROOT / "scripts"
MIRROR = ROOT / "skills" / "using-long-task" / "scripts"
NAMES = ("phase_route.py", "count_pending.py", "validate_features.py")


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("name", NAMES)
def test_mirror_byte_identical(name):
    a, b = CANON / name, MIRROR / name
    assert a.is_file(), f"canonical missing: {a}"
    assert b.exists(), f"mirror missing: {b}"
    assert _sha(a) == _sha(b), (
        f"{name} drifted between {CANON} and {MIRROR}. "
        f"If you edited one, run: cp {a} {b} (or restore the symlink)."
    )
