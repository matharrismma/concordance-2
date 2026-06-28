"""Grid scaffold invariant — every axis sits only on declared members.

This is the floor invariant the review asked for: it would have caught biology sitting on
an undeclared 'discreteness'. 'discreteness' is now a declared member (the "missing-1" fix),
so the scaffold is consistent. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import grid  # noqa: E402


def test_every_axis_member_is_declared():
    violations = grid.check_dimension_members()
    assert violations == [], f"axes on undeclared members: {violations}"


def test_discreteness_is_declared_and_carried_by_biology():
    assert "discreteness" in grid.DIMENSIONS
    assert "discreteness" in grid.AXIS_DIMENSIONS["biology"]


def test_floor_consumes_axis_coords_for_biology():
    from concordance.record import axis_coords_for
    ac = axis_coords_for("biology")
    assert ac is not None and "discreteness" in ac.dimensions


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} grid tests passed — scaffold consistent, member invariant holds.")
