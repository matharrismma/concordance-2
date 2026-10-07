"""Unit-pin the geography verifier (A2, 2026-10-06). Haversine distance for 1 deg of longitude at the
equator ~ 111.19 km; lat/lon validity. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import geography as GG


def test_haversine_distance():
    assert GG.verify_haversine_distance({"lat1": 0, "lon1": 0, "lat2": 0, "lon2": 1, "claimed_distance_km": 111.19}).status == "CONFIRMED"
    assert GG.verify_haversine_distance({"lat1": 0, "lon1": 0, "lat2": 0, "lon2": 1, "claimed_distance_km": 200}).status == "MISMATCH"
    assert GG.verify_haversine_distance({}).status == "NOT_APPLICABLE"


def test_lat_lon_validity():
    assert GG.verify_lat_lon_validity({"lat": 45, "lon": 90, "claimed_coords_valid": True}).status == "CONFIRMED"
    assert GG.verify_lat_lon_validity({"lat": 45, "lon": 90, "claimed_coords_valid": False}).status == "MISMATCH"
