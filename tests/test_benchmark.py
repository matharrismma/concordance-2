"""The regression gate — the derivation moat must stay 58/58 with 0 false-positives.

A false-positive (sealing a falsehood) is the one unforgivable failure for a verifier,
so this test fails loudly if any falsehood ever returns HOLDS. Runnable with `pytest`
OR `python tests/test_benchmark.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from benchmark import run  # noqa: E402


def test_moat_is_green_zero_false_positives():
    n, corr, fp, fn = run(verbose=False)
    assert n == 58, f"expected 58 claims, got {n}"
    assert fp == 0, f"CRITICAL: {fp} false-positive(s) — a falsehood was sealed"
    assert corr == n, f"benchmark not green: {corr}/{n} correct ({fn} false-negatives)"


if __name__ == "__main__":
    test_moat_is_green_zero_false_positives()
    print("  ok  moat is green — 58/58, 0 false-positives")
