"""Unit-pin the units verifier (A2, 2026-10-06). 1 km = 1000 m."""
from __future__ import annotations
from concordance.verifiers import units as U


def test_conversion():
    assert U.verify_conversion({"from_value": 1, "from_unit": "km", "to_unit": "m", "to_value": 1000}).status == "CONFIRMED"
    assert U.verify_conversion({"from_value": 1, "from_unit": "km", "to_unit": "m", "to_value": 500}).status == "MISMATCH"
    assert U.verify_conversion({}).status == "NOT_APPLICABLE"
