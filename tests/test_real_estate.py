"""Unit-pin the real_estate verifier (A2, 2026-10-06). Cap rate = NOI / value (10000/100000 = 0.10).
Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import real_estate as RE


def test_cap_rate():
    assert RE.verify_cap_rate({"net_operating_income": 10000, "property_value": 100000, "claimed_cap_rate": 0.1}).status == "CONFIRMED"
    assert RE.verify_cap_rate({"net_operating_income": 10000, "property_value": 100000, "claimed_cap_rate": 0.2}).status == "MISMATCH"
    assert RE.verify_cap_rate({}).status == "NOT_APPLICABLE"
