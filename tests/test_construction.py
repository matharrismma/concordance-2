"""Unit-pin the construction verifier (A2, 2026-10-06). Rectangular area 5*4=20 m^2; concrete volume
5*4*0.1=2 m^3. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import construction as CN


def test_rectangular_area():
    assert CN.verify_rectangular_area({"length_m": 5, "width_m": 4, "claimed_rect_area_m2": 20}).status == "CONFIRMED"
    assert CN.verify_rectangular_area({"length_m": 5, "width_m": 4, "claimed_rect_area_m2": 25}).status == "MISMATCH"
    assert CN.verify_rectangular_area({}).status == "NOT_APPLICABLE"


def test_concrete_volume():
    assert CN.verify_concrete_volume({"length_m": 5, "width_m": 4, "depth_m": 0.1, "claimed_concrete_m3": 2.0}).status == "CONFIRMED"
    assert CN.verify_concrete_volume({"length_m": 5, "width_m": 4, "depth_m": 0.1, "claimed_concrete_m3": 3.0}).status == "MISMATCH"
