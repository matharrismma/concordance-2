"""Unit-pin the biology verifier (A2, 2026-10-06). Mendelian ratio: observed [75,25] is consistent with
a 3:1 ratio (chi-square ~ 0); [50,50] is not. Missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import biology as BI


def test_mendelian():
    assert BI.verify_mendelian({"expected_ratio": [3, 1], "observed": [75, 25], "alpha": 0.05}).status == "CONFIRMED"
    assert BI.verify_mendelian({"expected_ratio": [3, 1], "observed": [50, 50], "alpha": 0.05}).status == "MISMATCH"
    assert BI.verify_mendelian({}).status == "NOT_APPLICABLE"
