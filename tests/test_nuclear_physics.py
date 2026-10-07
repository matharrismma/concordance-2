"""Unit-pin the nuclear_physics verifier (A2: verifier test-depth, 2026-10-06).
Radioactive decay N = N0 * (1/2)^(t/T): 1000 atoms, one half-life elapsed -> 500 remaining. Wrong claim
caught; missing field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import nuclear_physics as N


def test_radioactive_decay():
    r = N.verify_radioactive_decay({"initial_count": 1000, "half_life_seconds": 10,
                                    "elapsed_seconds": 10, "claimed_remaining_count": 500})
    assert r.status == "CONFIRMED"
    assert N.verify_radioactive_decay({"initial_count": 1000, "half_life_seconds": 10,
                                       "elapsed_seconds": 10, "claimed_remaining_count": 600}).status == "MISMATCH"
    assert N.verify_radioactive_decay({}).status == "NOT_APPLICABLE"
