"""Unit-pin the labor verifier (A2, 2026-10-06). Gross pay = hourly_rate * hours (20 * 40 = 800).
Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import labor as LB


def test_gross_pay():
    assert LB.verify_gross_pay({"hourly_rate": 20, "hours_worked": 40, "claimed_gross_pay": 800}).status == "CONFIRMED"
    assert LB.verify_gross_pay({"hourly_rate": 20, "hours_worked": 40, "claimed_gross_pay": 1000}).status == "MISMATCH"
    assert LB.verify_gross_pay({}).status == "NOT_APPLICABLE"
