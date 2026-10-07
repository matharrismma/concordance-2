"""Unit-pin the architecture verifier (A2, 2026-10-06). Floor area ratio = floor area / lot area
(2000/1000 = 2.0). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import architecture as AC


def test_floor_area_ratio():
    assert AC.verify_floor_area_ratio({"total_floor_area_m2": 2000, "lot_area_m2": 1000, "claimed_far": 2.0}).status == "CONFIRMED"
    assert AC.verify_floor_area_ratio({"total_floor_area_m2": 2000, "lot_area_m2": 1000, "claimed_far": 3.0}).status == "MISMATCH"
    assert AC.verify_floor_area_ratio({}).status == "NOT_APPLICABLE"
