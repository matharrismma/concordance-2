"""Unit-pin the finance verifier (A2: closing the verifier test-depth gap, 2026-10-06).

Known public-domain finance identities, hand-checked:
  accounting identity 1000 = 600 + 400; compound A=1000(1+.05/12)^120 = 1647.01;
  NPV([-1000,300,400,500,200]@10%) = 115.566; PV(1100@10%,1yr) = 1000.
Confirms the arithmetic, a mismatch is caught, and a missing field is NOT_APPLICABLE (never a false pass).
"""
from __future__ import annotations

from concordance.verifiers import finance as F


def test_accounting_identity():
    assert F.verify_accounting_identity({"assets": 1000, "liabilities": 600, "equity": 400}).status == "CONFIRMED"
    assert F.verify_accounting_identity({"assets": 1000, "liabilities": 600, "equity": 300}).status == "MISMATCH"
    assert F.verify_accounting_identity({"assets": 1000, "liabilities": 600}).status == "NOT_APPLICABLE"


def test_compound_interest():
    r = F.verify_compound_interest({"principal": 1000, "rate": 0.05, "compounding_per_year": 12,
                                    "years": 10, "claimed_future_value": 1647.01})
    assert r.status == "CONFIRMED"
    assert abs(r.data["actual_future_value"] - 1647.0095) < 0.01
    assert F.verify_compound_interest({"principal": 1000, "rate": 0.05, "compounding_per_year": 12,
                                       "years": 10, "claimed_future_value": 1700.0}).status == "MISMATCH"


def test_npv():
    r = F.verify_npv({"cashflows": [-1000, 300, 400, 500, 200], "discount_rate": 0.10, "claimed_npv": 115.57})
    assert r.status == "CONFIRMED"
    assert abs(r.data["actual_npv"] - 115.5659) < 1e-3
    assert F.verify_npv({"cashflows": [-1000, 300, 400, 500, 200], "discount_rate": 0.10,
                         "claimed_npv": 0.0}).status == "MISMATCH"


def test_present_value():
    assert F.verify_present_value({"future_value": 1100, "pv_discount_rate": 0.10, "pv_periods": 1,
                                   "claimed_present_value": 1000}).status == "CONFIRMED"
    assert F.verify_present_value({"future_value": 1100, "pv_discount_rate": 0.10, "pv_periods": 1,
                                   "claimed_present_value": 900}).status == "MISMATCH"


def test_missing_fields_never_false_pass():
    assert F.verify_npv({}).status == "NOT_APPLICABLE"
    assert F.verify_compound_interest({}).status == "NOT_APPLICABLE"
    assert F.verify_present_value({}).status == "NOT_APPLICABLE"
