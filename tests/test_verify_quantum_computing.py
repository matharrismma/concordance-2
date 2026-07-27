"""Quantum-computing verifier — Grover-iterations overflow safety.

Proves verify_grover_iterations confirms/mismatches correctly, and guards the gap found this
sweep: int(n_items) handles an arbitrarily large caller string with no overflow (Python ints are
unbounded), but math.sqrt(n) must convert n to a float first and raises OverflowError once n
exceeds float's representable range — a crash, not a decline. Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import quantum_computing  # noqa: E402

_HUGE = "1" + "0" * 400   # a Python int parses this fine, but math.sqrt(n) later overflows to float


def test_grover_iterations_confirms_a_true_claim():
    r = quantum_computing.verify_grover_iterations(
        {"n_items": 1_000_000, "claimed_grover_iterations": 785})
    assert r.passed


def test_grover_iterations_catches_a_false_claim():
    r = quantum_computing.verify_grover_iterations(
        {"n_items": 1_000_000, "claimed_grover_iterations": 1})
    assert r.failed


def test_overflowing_n_items_declines_instead_of_crashing():
    r = quantum_computing.verify_grover_iterations(
        {"n_items": _HUGE, "claimed_grover_iterations": 5})
    assert r.status == "ERROR"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} quantum_computing verifier tests passed.")
