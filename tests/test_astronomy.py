"""Unit-pin the astronomy verifier (A2: verifier test-depth, 2026-10-06).
Kepler's third law a^3 = P^2 (a=1 AU, P=1 yr -> consistent); parallax distance d = 1/p (p=0.1" ->
10 pc). Wrong claim caught; missing field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import astronomy as AS


def test_kepler_third_law():
    assert AS.verify_kepler_third_law({"semi_major_axis_au": 1.0, "orbital_period_years": 1.0,
                                       "claimed_kepler_consistent": True}).status == "CONFIRMED"
    assert AS.verify_kepler_third_law({"semi_major_axis_au": 1.0, "orbital_period_years": 2.0,
                                       "claimed_kepler_consistent": True}).status == "MISMATCH"
    assert AS.verify_kepler_third_law({}).status == "NOT_APPLICABLE"


def test_parallax_distance():
    assert AS.verify_parallax_distance({"parallax_arcsec": 0.1, "claimed_distance_parsec": 10}).status == "CONFIRMED"
    assert AS.verify_parallax_distance({"parallax_arcsec": 0.1, "claimed_distance_parsec": 5}).status == "MISMATCH"
    assert AS.verify_parallax_distance({}).status == "NOT_APPLICABLE"
