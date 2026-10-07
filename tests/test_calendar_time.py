"""Unit-pin the calendar_time verifier (A2, 2026-10-06). 2000 is a leap year (divisible by 400).
Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import calendar_time as CT


def test_leap_year():
    assert CT.verify_leap_year({"year": 2000, "claimed_leap": True}).status == "CONFIRMED"
    assert CT.verify_leap_year({"year": 2000, "claimed_leap": False}).status == "MISMATCH"
    assert CT.verify_leap_year({}).status == "NOT_APPLICABLE"
