"""Unit-pin the theology_doctrine verifier (A2, 2026-10-06). The Trinitarian formula is complete only
when all three persons are named (Father, Son, Holy Spirit; cf. Matthew 28:19). An incomplete naming is
caught; a missing field is NOT_APPLICABLE. The verifier checks the stated formula, it does not judge faith.
"""
from __future__ import annotations
from concordance.verifiers import theology_doctrine as TH


def test_trinitarian_formula():
    assert TH.verify_trinitarian_formula({"persons_named": ["Father", "Son", "Holy Spirit"],
                                          "claimed_trinitarian_complete": True}).status == "CONFIRMED"
    assert TH.verify_trinitarian_formula({"persons_named": ["Father", "Son"],
                                          "claimed_trinitarian_complete": True}).status == "MISMATCH"
    assert TH.verify_trinitarian_formula({}).status == "NOT_APPLICABLE"
