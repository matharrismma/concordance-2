"""Unit-pin the archaeology verifier (A2, 2026-10-06). Radiocarbon: one half-life (fraction 0.5) of C-14
(t1/2 = 5730 yr) is ~5730 years. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import archaeology as AR


def test_radiocarbon():
    assert AR.verify_radiocarbon({"fraction_remaining": 0.5, "half_life_years": 5730, "claimed_age_years": 5730}).status == "CONFIRMED"
    assert AR.verify_radiocarbon({"fraction_remaining": 0.5, "half_life_years": 5730, "claimed_age_years": 1000}).status == "MISMATCH"
    assert AR.verify_radiocarbon({}).status == "NOT_APPLICABLE"
