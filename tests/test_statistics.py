"""Unit-pin the statistics verifier's significance check (A2, 2026-10-06). p < alpha means significant
(p=0.01 at alpha=0.05). A wrong significance claim is caught; a missing field is NOT_APPLICABLE.
(The GUE/trajectory routes are exercised by tools/tick.py and test_trajectory.)"""
from __future__ import annotations
from concordance.verifiers import statistics as ST


def test_significance_consistency():
    assert ST.verify_significance_consistency({"p_value": 0.01, "alpha": 0.05,
                                               "claimed_significance": "significant"}).status == "CONFIRMED"
    assert ST.verify_significance_consistency({"p_value": 0.10, "alpha": 0.05,
                                               "claimed_significance": "significant"}).status == "MISMATCH"
    assert ST.verify_significance_consistency({}).status == "NOT_APPLICABLE"
