"""The GIS half of the geography verifier — measure, navigate, project, contain.

Every assertion here is against a value that exists OUTSIDE this codebase: a published WGS84
constant, a closed-form identity, or a round trip between two independent implementations. A
geometry library that only agrees with itself is a library that is confidently wrong together.

The refusals are tested as hard as the answers. Vincenty genuinely fails to converge on
near-antipodal pairs, planar ray casting is WRONG rather than approximate across the
antimeridian, and Web Mercator is undefined at the poles. In each case the verifier must say
CANNOT_CHECK -- our inability to measure is never a verdict on the claim.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-gis-"))

from concordance.verifiers import geography as G  # noqa: E402


# ── measure ──────────────────────────────────────────────────────────────────────────────────

def test_one_degree_of_latitude_matches_the_published_wgs84_value():
    """The anchor. One degree of latitude at the equator is 110.574 km on WGS84 -- a published
    constant nothing in this repo produced. The sphere says 111.19, and being wrong by 621 m per
    degree is exactly why the ellipsoid is here."""
    s, _f, _r = G._vincenty_inverse(0.0, 0.0, 1.0, 0.0)
    assert abs(s / 1000.0 - 110.574) < 0.001, s / 1000.0
    sphere = G._haversine_km(0.0, 0.0, 1.0, 0.0)
    assert abs(sphere - 111.195) < 0.01
    assert sphere - s / 1000.0 > 0.6          # the sphere overstates by >600 m


def test_the_direct_and_inverse_geodesics_agree():
    """The strongest self-check available: walk 1000 km on a bearing with the DIRECT formula,
    then measure back with the INVERSE formula. They share no code, so agreement to nanometres
    means both are right, not that one is copying the other."""
    r = G.verify_destination_point({
        "lat1": 35.0, "lon1": -85.0, "bearing_deg": 45.0, "distance_km": 1000.0,
        "claimed_dest_lat": 41.08816, "claimed_dest_lon": -76.58860})
    assert r.status == "CONFIRMED", r.detail
    back = G._vincenty_inverse(35.0, -85.0, r.data["actual_dest_lat"], r.data["actual_dest_lon"])
    assert abs(back[0] / 1000.0 - 1000.0) < 1e-6, back[0] / 1000.0
    assert abs(back[1] - 45.0) < 1e-6, back[1]


def test_the_sphere_error_is_reported_not_hidden():
    """A geodesic that quietly replaced the spherical answer would be an upgrade of authority."""
    r = G.verify_geodesic_distance({"lat1": 40.6413, "lon1": -73.7781,
                                    "lat2": 51.4700, "lon2": -0.4543,
                                    "claimed_geodesic_km": 5554.909})
    assert r.status == "CONFIRMED", r.detail
    assert "spherical_haversine_km" in r.data and "spherical_error_km" in r.data
    assert abs(r.data["spherical_error_km"]) > 10.0        # ~15 km on this line
    assert "spherical model" in r.detail


def test_a_near_antipodal_pair_is_cannot_check_never_a_number():
    """Vincenty does not converge there. Returning the last iterate would report OUR failure as
    a measurement -- three states, never two."""
    assert G._vincenty_inverse(0.0, 0.0, 0.5, 179.7) is None
    r = G.verify_geodesic_distance({"lat1": 0.0, "lon1": 0.0, "lat2": 0.5, "lon2": 179.7,
                                    "claimed_geodesic_km": 19000.0})
    assert r.status == "ERROR"
    assert "CANNOT_CHECK" in r.detail
    assert "actual_geodesic_km" not in (r.data or {})     # no number leaked out


# ── project ──────────────────────────────────────────────────────────────────────────────────

def test_web_mercator_area_inflation_is_sec_squared():
    """Closed form: at 60° the scale factor is exactly 2 and area exactly 4. Nothing to fit."""
    r = G.verify_projection_distortion({"lat_for_projection": 60.0, "claimed_area_inflation": 4.0})
    assert r.status == "CONFIRMED"
    assert abs(r.data["actual_scale_factor"] - 2.0) < 1e-12
    assert abs(r.data["actual_area_inflation"] - 4.0) < 1e-12
    for lat in (0.0, 30.0, 45.0, 72.0):
        got = G.verify_projection_distortion(
            {"lat_for_projection": lat, "claimed_scale_factor": 1.0})
        assert abs(got.data["actual_scale_factor"] - 1 / math.cos(math.radians(lat))) < 1e-12


def test_the_projection_says_what_it_sacrificed():
    """The number is only half the answer; a reader must be told angles were kept and area paid."""
    d = G.verify_projection_distortion(
        {"lat_for_projection": 45.0, "claimed_area_inflation": 2.0}).data
    assert d["preserved"].startswith("angles")
    assert d["sacrificed"] == "area"
    assert "Theorema Egregium" in d["why"]


def test_mercator_refuses_the_pole():
    r = G.verify_projection_distortion({"lat_for_projection": 89.9, "claimed_area_inflation": 1.0})
    assert r.status == "ERROR" and "CANNOT_CHECK" in r.detail


# ── contain ──────────────────────────────────────────────────────────────────────────────────

def test_the_area_integral_closes_on_the_whole_sphere():
    """The definitive check on spherical excess: sweep pole to pole and the ring must enclose
    4(pi)R^2. If the integral is wrong by a term, this misses by a lot."""
    ring = ([[89.999, -180 + i] for i in range(361)] +
            [[-89.999, 180 - i] for i in range(361)])
    got = G.verify_polygon_area({"polygon": ring, "claimed_area_km2": 0.0}).data["actual_area_km2"]
    sphere = 4 * math.pi * 6371.0 ** 2
    assert abs(got / sphere - 1.0) < 1e-5, (got, sphere)


def test_containment_answers_the_four_directions():
    sq = [[34, -85], [35, -85], [35, -84], [34, -84]]
    inside = G.verify_point_in_polygon({"polygon": sq, "point": [34.5, -84.5],
                                        "claimed_inside": True})
    assert inside.status == "CONFIRMED" and inside.data["actual_inside"] is True
    for pt in ([33.0, -84.5], [36.0, -84.5], [34.5, -83.0], [34.5, -86.0]):
        out = G.verify_point_in_polygon({"polygon": sq, "point": pt, "claimed_inside": False})
        assert out.status == "CONFIRMED", (pt, out.detail)
        assert out.data["actual_inside"] is False


def test_containment_refuses_the_antimeridian_rather_than_guessing():
    """Planar ray casting is WRONG there, not approximate. A confident wrong containment is the
    worst answer this check can give -- it puts someone on the other side of a border."""
    r = G.verify_point_in_polygon({"polygon": [[0, 179], [0, -179], [1, -179], [1, 179]],
                                   "point": [0.5, 179.5], "claimed_inside": True})
    assert r.status == "ERROR"
    assert "antimeridian" in r.detail and "CANNOT_CHECK" in r.detail
    assert G.verify_polygon_area({"polygon": [[0, 179], [0, -179], [1, -179], [1, 179]],
                                  "claimed_area_km2": 1.0}).status == "ERROR"


def test_the_method_declares_where_it_is_valid():
    d = G.verify_point_in_polygon({"polygon": [[34, -85], [35, -85], [35, -84]],
                                   "point": [34.5, -84.7], "claimed_inside": True}).data
    assert "ray casting" in d["method"] and "valid_when" in d


# ── the fleet ────────────────────────────────────────────────────────────────────────────────

def test_one_packet_fires_every_applicable_check():
    """GIS went INTO the geography verifier, not beside it: one artifact, nine possible checks."""
    res = G.run({"GEO_LOC_VERIFY": {
        "lat": 35.0, "lon": -85.0, "claimed_coords_valid": True,
        "lat1": 35.0, "lon1": -85.0, "lat2": 33.74, "lon2": -84.39,
        "claimed_distance_km": 152.0, "claimed_geodesic_km": 152.0,
        "longitude_for_utm": -85.0, "claimed_utm_zone": 16,
        "lat_for_projection": 60.0, "claimed_area_inflation": 4.0,
        "polygon": [[34, -85], [35, -85], [35, -84], [34, -84]],
        "point": [34.5, -84.5], "claimed_inside": True, "claimed_area_km2": 10190.0}})
    fired = {r.name for r in res}
    for expect in ("geography.geodesic_distance", "geography.projection_distortion",
                   "geography.point_in_polygon", "geography.polygon_area",
                   "geography.lat_lon_validity", "geography.utm_zone"):
        assert expect in fired, (expect, fired)
    assert not any(r.status == "NOT_APPLICABLE" for r in res)


def test_an_empty_packet_is_not_applicable_not_a_pass():
    res = G.run({})
    assert len(res) == 1 and res[0].status == "NOT_APPLICABLE"
