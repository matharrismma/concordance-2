"""Unit-pin the oceanography verifier (A2, 2026-10-06). Pressure at 10 m depth ~ 1.9924 atm
(1 atm air + ~0.9924 atm water). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import oceanography as OC


def test_pressure_at_depth():
    assert OC.verify_pressure_at_depth({"depth_m": 10, "claimed_pressure_atm": 1.9924}).status == "CONFIRMED"
    assert OC.verify_pressure_at_depth({"depth_m": 10, "claimed_pressure_atm": 1.0}).status == "MISMATCH"
    assert OC.verify_pressure_at_depth({}).status == "NOT_APPLICABLE"
