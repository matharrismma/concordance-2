"""Unit-pin the hydrology verifier (A2, 2026-10-06). Rational method Q = C*i*A (0.5 * 2 * 10 = 10)."""
from __future__ import annotations
from concordance.verifiers import hydrology as HY


def test_rational_runoff():
    assert HY.verify_rational_runoff({"runoff_coefficient": 0.5, "rainfall_intensity": 2.0,
                                      "drainage_area": 10.0, "claimed_runoff": 10.0}).status == "CONFIRMED"
    assert HY.verify_rational_runoff({"runoff_coefficient": 0.5, "rainfall_intensity": 2.0,
                                      "drainage_area": 10.0, "claimed_runoff": 5.0}).status == "MISMATCH"
    assert HY.verify_rational_runoff({}).status == "NOT_APPLICABLE"
