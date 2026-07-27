"""History-chronology verifier — century-assignment overflow safety.

Proves verify_century_assignment confirms/mismatches correctly, and guards the gap found this
sweep: int(year_CE) handles an arbitrarily large caller string with no overflow (Python ints are
unbounded), but the true division y/100 (needed for math.ceil) then raises OverflowError once y
exceeds float's representable range — a crash, not a decline. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import history_chronology  # noqa: E402

_HUGE = "1" + "0" * 400   # a Python int parses this fine, but y/100 later overflows to float


def test_century_assignment_confirms_a_true_claim():
    r = history_chronology.verify_century_assignment({"year_CE": 1776, "claimed_century": 18})
    assert r.passed


def test_century_assignment_catches_a_false_claim():
    r = history_chronology.verify_century_assignment({"year_CE": 1776, "claimed_century": 17})
    assert r.failed


def test_overflowing_year_declines_instead_of_crashing():
    r = history_chronology.verify_century_assignment({"year_CE": _HUGE, "claimed_century": 5})
    assert r.status == "ERROR"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} history_chronology verifier tests passed.")
