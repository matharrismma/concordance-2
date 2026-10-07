"""Unit-pin the exercise_science verifier (A2, 2026-10-06). Max heart rate ~ 208 - 0.7*age
(Tanaka); age 30 -> 187. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import exercise_science as EX


def test_max_heart_rate():
    assert EX.verify_max_heart_rate({"age_years": 30, "claimed_max_hr": 187}).status == "CONFIRMED"
    assert EX.verify_max_heart_rate({"age_years": 30, "claimed_max_hr": 200}).status == "MISMATCH"
    assert EX.verify_max_heart_rate({}).status == "NOT_APPLICABLE"
