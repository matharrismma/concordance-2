"""Architecture verifier — occupant load overflow safety.

Proves verify_occupant_load confirms/mismatches correctly, and guards the one gap found this
sweep: a caller-supplied number large enough to overflow float() to inf (e.g. a 300+ digit
string) parsed without raising, then crashed downstream at math.ceil()/int(round()) — the same
shape as the compute.py and steward.py overflow bugs fixed earlier this sweep. Runnable with
pytest OR directly (python tests/test_verify_architecture.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import architecture  # noqa: E402

_HUGE = "1" + "0" * 400   # parses via float() to inf without raising


def test_occupant_load_confirms_a_true_claim():
    r = architecture.verify_occupant_load(
        {"floor_area_m2": 500, "occupant_load_factor_m2_per_person": 4.6, "claimed_occupant_count": 109})
    assert r.passed and r.applicable


def test_occupant_load_catches_a_false_claim():
    r = architecture.verify_occupant_load(
        {"floor_area_m2": 500, "occupant_load_factor_m2_per_person": 4.6, "claimed_occupant_count": 50})
    assert r.failed


def test_overflowing_claimed_count_declines_instead_of_crashing():
    r = architecture.verify_occupant_load(
        {"floor_area_m2": 500, "occupant_load_factor_m2_per_person": 4.6, "claimed_occupant_count": _HUGE})
    assert r.status == "ERROR"


def test_overflowing_floor_area_declines_instead_of_crashing():
    r = architecture.verify_occupant_load(
        {"floor_area_m2": _HUGE, "occupant_load_factor_m2_per_person": 4.6, "claimed_occupant_count": 100})
    assert r.status == "ERROR"


def test_overflowing_load_factor_declines_instead_of_crashing():
    r = architecture.verify_occupant_load(
        {"floor_area_m2": 500, "occupant_load_factor_m2_per_person": _HUGE, "claimed_occupant_count": 100})
    assert r.status == "ERROR"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} architecture verifier tests passed.")
