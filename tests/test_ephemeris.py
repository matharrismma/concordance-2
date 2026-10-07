"""Unit-pin the ephemeris verifier (A2, 2026-10-06). The Julian Day for 2000-01-01 (12:00 UT) is
2451545.0. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import ephemeris as EP


def test_julian_day():
    assert EP.verify_julian_day({"iso_date": "2000-01-01", "claimed_julian_day": 2451545.0}).status == "CONFIRMED"
    assert EP.verify_julian_day({"iso_date": "2000-01-01", "claimed_julian_day": 2451000.0}).status == "MISMATCH"
    assert EP.verify_julian_day({}).status == "NOT_APPLICABLE"
