"""Unit-pin the geometry verifier (A2, 2026-10-06). Pythagorean 3-4-5; circle r=1 (area pi, circ 2pi)."""
from __future__ import annotations
from concordance.verifiers import geometry as G


def test_pythagorean():
    assert G.verify_pythagorean({"pyth_a": 3, "pyth_b": 4, "pyth_c": 5, "claimed_right_triangle": True}).status == "CONFIRMED"
    assert G.verify_pythagorean({"pyth_a": 3, "pyth_b": 4, "pyth_c": 6, "claimed_right_triangle": True}).status == "MISMATCH"
    assert G.verify_pythagorean({}).status == "NOT_APPLICABLE"


def test_circle_properties():
    assert G.verify_circle_properties({"circle_radius": 1, "claimed_circle_area": 3.14159265,
                                       "claimed_circle_circumference": 6.2831853}).status == "CONFIRMED"
    assert G.verify_circle_properties({"circle_radius": 1, "claimed_circle_area": 4.0,
                                       "claimed_circle_circumference": 6.2831853}).status == "MISMATCH"
