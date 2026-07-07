"""The regression gate — the derivation moat must stay 60/60 with 0 false-positives.

A false-positive (sealing a falsehood) is the one unforgivable failure for a verifier,
so this test fails loudly if any falsehood ever returns HOLDS. Runnable with `pytest`
OR `python tests/test_benchmark.py`. (58 → 60: added two finite-sampling traps that the
old inequality path sealed as HOLDS — see test_inequality.py.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from benchmark import run  # noqa: E402


def test_moat_is_green_zero_false_positives():
    n, corr, fp, fn = run(verbose=False)
    assert n >= 60, f"expected >=60 claims, got {n}"
    assert fp == 0, f"CRITICAL: {fp} false-positive(s) — a falsehood was sealed"
    assert corr == n, f"benchmark not green: {corr}/{n} correct ({fn} false-negatives)"


if __name__ == "__main__":
    test_moat_is_green_zero_false_positives()
    print("  ok  moat is green — 60/60, 0 false-positives")
