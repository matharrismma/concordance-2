"""Unit-pin the law verifier (A2, 2026-10-06). The U.S. Constitution sets the presidential age floor at
35 (Art. II). At 35 the requirement is met; at 30 it is not. Missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import law as LW


def test_constitutional_age_requirement():
    assert LW.verify_constitutional_age_requirement({"age": 35, "office": "president",
                                                     "claimed_meets_age_requirement": True}).status == "CONFIRMED"
    assert LW.verify_constitutional_age_requirement({"age": 30, "office": "president",
                                                     "claimed_meets_age_requirement": True}).status == "MISMATCH"
    assert LW.verify_constitutional_age_requirement({}).status == "NOT_APPLICABLE"
