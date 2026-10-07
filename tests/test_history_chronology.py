"""Unit-pin the history_chronology verifier (A2, 2026-10-06). The year 1999 CE falls in the 20th
century. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import history_chronology as HC


def test_century_assignment():
    assert HC.verify_century_assignment({"year_CE": 1999, "claimed_century": 20}).status == "CONFIRMED"
    assert HC.verify_century_assignment({"year_CE": 1999, "claimed_century": 19}).status == "MISMATCH"
    assert HC.verify_century_assignment({}).status == "NOT_APPLICABLE"
