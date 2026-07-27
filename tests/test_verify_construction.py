"""Construction verifier — paint-coverage and floor-tile overflow safety.

Proves verify_paint_coverage and verify_floor_tiles confirm correctly, and guards the gap found
this sweep: a caller-supplied number large enough to overflow float() to inf (e.g. a 300+ digit
string) parsed without raising, then crashed downstream at math.ceil()/int() — the same shape as
the architecture.py verifier fixed earlier this sweep. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import construction  # noqa: E402

_HUGE = "1" + "0" * 400   # parses via float() to inf without raising


def test_paint_coverage_confirms_a_true_claim():
    r = construction.verify_paint_coverage(
        {"paint_area_m2": 100, "coverage_m2_per_can": 10, "claimed_paint_cans": 10})
    assert r.passed


def test_paint_coverage_overflowing_inputs_decline_instead_of_crashing():
    for spec in (
        {"paint_area_m2": _HUGE, "coverage_m2_per_can": 10, "claimed_paint_cans": 5},
        {"paint_area_m2": 100, "coverage_m2_per_can": 10, "claimed_paint_cans": _HUGE},
    ):
        assert construction.verify_paint_coverage(spec).status == "ERROR"


def test_floor_tiles_confirms_a_true_claim():
    r = construction.verify_floor_tiles(
        {"tile_area_m2": 20, "tile_size_m2": 0.5, "claimed_tile_count": 44})
    assert r.passed


def test_floor_tiles_overflowing_inputs_decline_instead_of_crashing():
    for spec in (
        {"tile_area_m2": _HUGE, "tile_size_m2": 0.5, "claimed_tile_count": 5},
        {"tile_area_m2": 20, "tile_size_m2": 0.5, "claimed_tile_count": _HUGE},
        {"tile_area_m2": 20, "tile_size_m2": 0.5, "waste_factor": _HUGE, "claimed_tile_count": 5},
    ):
        assert construction.verify_floor_tiles(spec).status == "ERROR"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} construction verifier tests passed.")
