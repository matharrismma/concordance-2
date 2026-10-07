"""Unit-pin the economics verifier (A2, 2026-10-06). Rule of 72 (72/8 = 9 yrs); simple interest
I=Prt (1000*0.05*2 = 100). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import economics as EC


def test_rule_of_72():
    assert EC.verify_rule_of_72({"rate_percent": 8, "claimed_doubling_years": 9}).status == "CONFIRMED"
    assert EC.verify_rule_of_72({"rate_percent": 8, "claimed_doubling_years": 5}).status == "MISMATCH"
    assert EC.verify_rule_of_72({}).status == "NOT_APPLICABLE"


def test_simple_interest():
    assert EC.verify_simple_interest({"principal": 1000, "rate": 0.05, "time_years": 2, "claimed_simple_interest": 100}).status == "CONFIRMED"
    assert EC.verify_simple_interest({"principal": 1000, "rate": 0.05, "time_years": 2, "claimed_simple_interest": 200}).status == "MISMATCH"
