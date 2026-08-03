"""Geography verifier (physical-substance / standalone) — including the GIS operations.

Lat/lon validity, distance, bearing, UTM zone, and the four things that make this a GIS rather
than a coordinate calculator: MEASURE on the true figure of the Earth, PROJECT and say what the
projection cost you, CONTAIN (is this point in that boundary), and NAVIGATE (dead reckoning).

WHY THE ELLIPSOID IS HERE. The original four checks all assume a sphere of radius 6371 km. That
is a fine approximation and a bad measurement: the Earth is an oblate spheroid, and a spherical
great circle is wrong by up to ~0.5% — on a 5,000 km line that is 25 km, which is the difference
between a valley and the next valley over. Rather than silently upgrade the sphere's answer to
"the distance", geodesic_distance computes BOTH and reports the error between them, so a reader
can see what the simpler model cost. Never silently upgrade authority — not even our own.

Checks:
  * geography.lat_lon_validity      — lat in [-90,90], lon in [-180,180]
  * geography.haversine_distance    — great-circle distance on R=6371 km (spherical)
  * geography.initial_bearing       — forward azimuth (0–360°)
  * geography.utm_zone              — UTM zone number from longitude
  * geography.geodesic_distance     — Vincenty inverse on the WGS84 ellipsoid, + sphere error
  * geography.destination_point     — Vincenty direct: dead reckoning from bearing + distance
  * geography.projection_distortion — what a flat map costs you, as a number
  * geography.point_in_polygon      — containment by ray casting, with its boundary declared
  * geography.polygon_area          — spherical excess; area of ground inside a boundary

All public domain: WGS84 is a published national datum, Vincenty's 1975 formulae are PD, and
ray casting and spherical excess are classical.

GEO_LOC_VERIFY shape:
    {
      "lat": 35.0, "lon": -85.0,
      "claimed_coords_valid": true,

      "lat1": 35.0, "lon1": -85.0,
      "lat2": 33.74, "lon2": -84.39,
      "claimed_distance_km": 175.0,          # spherical
      "claimed_geodesic_km": 175.0,          # ellipsoidal (WGS84)

      "claimed_bearing_deg": 145.0,

      "longitude_for_utm": -85.0,
      "claimed_utm_zone": 16,

      "bearing_deg": 145.0, "distance_km": 175.0,       # dead reckoning from lat1/lon1
      "claimed_dest_lat": 33.74, "claimed_dest_lon": -84.39,

      "lat_for_projection": 60.0,            # Web Mercator distortion at this parallel
      "claimed_area_inflation": 4.0,

      "polygon": [[35.0,-85.0], [35.0,-84.0], [34.0,-84.0], [34.0,-85.0]],
      "point": [34.5, -84.5], "claimed_inside": true,
      "claimed_area_km2": 10200.0,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch  # declarative run() driver


_EARTH_RADIUS_KM = 6371.0

# WGS84 — the datum GPS reports in, and the one every modern map is tied to.
_WGS84_A = 6378137.0                  # semi-major axis (equatorial), metres
_WGS84_F = 1.0 / 298.257223563        # flattening
_WGS84_B = _WGS84_A * (1.0 - _WGS84_F)  # semi-minor axis (polar), metres


def _coord_valid(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def verify_lat_lon_validity(spec: Dict[str, Any]) -> VerifierResult:
    name = "geography.lat_lon_validity"
    lat = spec.get("lat")
    lon = spec.get("lon")
    claimed = spec.get("claimed_coords_valid")
    if lat is None or lon is None or claimed is None:
        return na(name)
    try:
        latf, lonf = float(lat), float(lon)
    except (TypeError, ValueError):
        return error(name, "lat and lon must be numeric")
    actual = _coord_valid(latf, lonf)
    data = {"lat": latf, "lon": lonf, "actual_valid": actual,
            "claimed_valid": bool(claimed),
            "rule": "lat ∈ [-90, 90], lon ∈ [-180, 180]"}
    if actual == bool(claimed):
        return confirm(name, f"({latf}, {lonf}) valid={actual} (matches claim)", data)
    return mismatch(name, f"({latf}, {lonf}) valid={actual}, claimed {bool(claimed)}", data)


def verify_haversine_distance(spec: Dict[str, Any]) -> VerifierResult:
    name = "geography.haversine_distance"
    lat1 = spec.get("lat1"); lon1 = spec.get("lon1")
    lat2 = spec.get("lat2"); lon2 = spec.get("lon2")
    claimed = spec.get("claimed_distance_km")
    if any(v is None for v in (lat1, lon1, lat2, lon2, claimed)):
        return na(name)
    try:
        a1, o1, a2, o2, c = float(lat1), float(lon1), float(lat2), float(lon2), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all coordinates and claimed_distance_km must be numeric")
    if not (_coord_valid(a1, o1) and _coord_valid(a2, o2)):
        return error(name, f"coordinates out of range")
    # Haversine.
    phi1 = math.radians(a1)
    phi2 = math.radians(a2)
    dphi = math.radians(a2 - a1)
    dlam = math.radians(o2 - o1)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    actual = 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(h))
    rel_tol = clamp_tol(spec, "tolerance_relative", 0.01)  # 1% default
    diff = abs(actual - c)
    threshold = max(0.5, rel_tol * actual)  # absolute floor 0.5 km
    data = {"lat1": a1, "lon1": o1, "lat2": a2, "lon2": o2,
            "actual_distance_km": actual, "claimed_distance_km": c,
            "diff_km": diff, "earth_radius_km": _EARTH_RADIUS_KM,
            "formula": "haversine on spherical Earth"}
    if diff <= threshold:
        return confirm(name,
                       f"haversine({a1},{o1} → {a2},{o2}) = {actual:.2f} km (matches claim {c})",
                       data)
    return mismatch(name,
                    f"haversine = {actual:.2f} km, claimed {c} (diff {diff:.2f})",
                    data)


def verify_initial_bearing(spec: Dict[str, Any]) -> VerifierResult:
    """Forward azimuth from (lat1, lon1) to (lat2, lon2), 0=N, 90=E."""
    name = "geography.initial_bearing"
    lat1 = spec.get("lat1"); lon1 = spec.get("lon1")
    lat2 = spec.get("lat2"); lon2 = spec.get("lon2")
    claimed = spec.get("claimed_bearing_deg")
    if any(v is None for v in (lat1, lon1, lat2, lon2, claimed)):
        return na(name)
    try:
        a1, o1, a2, o2, c = float(lat1), float(lon1), float(lat2), float(lon2), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    phi1 = math.radians(a1)
    phi2 = math.radians(a2)
    dlam = math.radians(o2 - o1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    actual = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    diff = min(abs(actual - c), 360.0 - abs(actual - c))  # circular diff
    tol = clamp_tol(spec, "tolerance_deg", 1.0)
    data = {"lat1": a1, "lon1": o1, "lat2": a2, "lon2": o2,
            "actual_bearing_deg": actual, "claimed_bearing_deg": c,
            "diff_deg": diff, "tolerance_deg": tol,
            "formula": "θ = atan2(sin Δλ · cos φ₂, cos φ₁·sin φ₂ − sin φ₁·cos φ₂·cos Δλ)"}
    if diff <= tol:
        return confirm(name,
                       f"bearing = {actual:.2f}° (matches claim {c}, diff {diff:.2f})",
                       data)
    return mismatch(name,
                    f"bearing = {actual:.2f}°, claimed {c} (diff {diff:.2f})",
                    data)


def verify_utm_zone(spec: Dict[str, Any]) -> VerifierResult:
    """UTM zone = floor((lon + 180) / 6) + 1, in [1, 60]."""
    name = "geography.utm_zone"
    lon = spec.get("longitude_for_utm")
    claimed = spec.get("claimed_utm_zone")
    if lon is None or claimed is None:
        return na(name)
    try:
        lf = float(lon)
        c = int(claimed)
    except (TypeError, ValueError):
        return error(name, "longitude must be numeric, claimed_utm_zone integer")
    if not (-180.0 <= lf <= 180.0):
        return error(name, f"longitude out of range, got {lf}")
    actual = int(((lf + 180.0) // 6) + 1)
    if actual > 60:
        actual = 60  # exactly +180° edge case
    data = {"longitude": lf, "actual_utm_zone": actual, "claimed_utm_zone": c,
            "formula": "zone = floor((lon + 180) / 6) + 1"}
    if actual == c:
        return confirm(name, f"longitude {lf}° → UTM zone {actual} (matches claim)", data)
    return mismatch(name, f"longitude {lf}° → UTM zone {actual}, claimed {c}", data)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# GIS: measure · navigate · project · contain
# ─────────────────────────────────────────────────────────────────────────────────────────────

def _vincenty_inverse(a1: float, o1: float, a2: float, o2: float
                      ) -> Optional[Tuple[float, float, float]]:
    """Geodesic distance (metres) and the two azimuths on WGS84. None if it will not converge.

    Vincenty (1975). Returning None rather than a number is the whole point of this function:
    the iteration genuinely fails to converge for near-antipodal pairs, and an engine that
    quietly returned its last iterate would be reporting OUR failure as a measurement. The
    caller turns None into CANNOT_CHECK, never into a distance.
    """
    phi1, phi2 = math.radians(a1), math.radians(a2)
    L = math.radians(o2 - o1)
    U1 = math.atan((1 - _WGS84_F) * math.tan(phi1))
    U2 = math.atan((1 - _WGS84_F) * math.tan(phi2))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sinU2, cosU2 = math.sin(U2), math.cos(U2)

    lam = L
    for _ in range(200):
        sinLam, cosLam = math.sin(lam), math.cos(lam)
        sinSigma = math.sqrt((cosU2 * sinLam) ** 2 +
                             (cosU1 * sinU2 - sinU1 * cosU2 * cosLam) ** 2)
        if sinSigma == 0:
            return (0.0, 0.0, 0.0)          # coincident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLam
        sigma = math.atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLam / sinSigma
        cos2Alpha = 1 - sinAlpha ** 2
        cos2SigmaM = 0.0 if cos2Alpha == 0 else cosSigma - 2 * sinU1 * sinU2 / cos2Alpha
        C = _WGS84_F / 16 * cos2Alpha * (4 + _WGS84_F * (4 - 3 * cos2Alpha))
        lam_prev = lam
        lam = L + (1 - C) * _WGS84_F * sinAlpha * (
            sigma + C * sinSigma * (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM ** 2)))
        if abs(lam - lam_prev) < 1e-12:
            break
    else:
        return None                          # near-antipodal: say so, do not guess

    u2 = cos2Alpha * (_WGS84_A ** 2 - _WGS84_B ** 2) / (_WGS84_B ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    dSigma = B * sinSigma * (cos2SigmaM + B / 4 * (
        cosSigma * (-1 + 2 * cos2SigmaM ** 2) -
        B / 6 * cos2SigmaM * (-3 + 4 * sinSigma ** 2) * (-1 + 4 * cos2SigmaM ** 2)))
    s = _WGS84_B * A * (sigma - dSigma)
    sinLam, cosLam = math.sin(lam), math.cos(lam)
    fwd = math.atan2(cosU2 * sinLam, cosU1 * sinU2 - sinU1 * cosU2 * cosLam)
    rev = math.atan2(cosU1 * sinLam, -sinU1 * cosU2 + cosU1 * sinU2 * cosLam)
    return (s, math.degrees(fwd) % 360.0, math.degrees(rev) % 360.0)


def _haversine_km(a1: float, o1: float, a2: float, o2: float) -> float:
    phi1, phi2 = math.radians(a1), math.radians(a2)
    dphi, dlam = math.radians(a2 - a1), math.radians(o2 - o1)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def verify_geodesic_distance(spec: Dict[str, Any]) -> VerifierResult:
    """Distance on the WGS84 ellipsoid — and what the spherical answer would have cost."""
    name = "geography.geodesic_distance"
    lat1, lon1 = spec.get("lat1"), spec.get("lon1")
    lat2, lon2 = spec.get("lat2"), spec.get("lon2")
    claimed = spec.get("claimed_geodesic_km")
    if any(v is None for v in (lat1, lon1, lat2, lon2, claimed)):
        return na(name)
    try:
        a1, o1, a2, o2, c = (float(lat1), float(lon1), float(lat2), float(lon2), float(claimed))
    except (TypeError, ValueError):
        return error(name, "all coordinates and claimed_geodesic_km must be numeric")
    if not (_coord_valid(a1, o1) and _coord_valid(a2, o2)):
        return error(name, "coordinates out of range")

    got = _vincenty_inverse(a1, o1, a2, o2)
    if got is None:
        # THREE STATES, NEVER TWO. We could not measure it; that is not a verdict on the claim.
        return error(name,
                     "Vincenty did not converge (near-antipodal pair) — CANNOT_CHECK, "
                     "not a judgement on the claim",
                     {"lat1": a1, "lon1": o1, "lat2": a2, "lon2": o2,
                      "reason": "iteration limit on a near-antipodal geodesic"})
    s_m, fwd, rev = got
    actual = s_m / 1000.0
    sphere = _haversine_km(a1, o1, a2, o2)
    sphere_err = sphere - actual
    rel_tol = clamp_tol(spec, "tolerance_relative", 0.001)      # 0.1% — the ellipsoid earns it
    diff = abs(actual - c)
    threshold = max(0.05, rel_tol * actual)
    data = {"lat1": a1, "lon1": o1, "lat2": a2, "lon2": o2,
            "actual_geodesic_km": actual, "claimed_geodesic_km": c, "diff_km": diff,
            "spherical_haversine_km": sphere,
            "spherical_error_km": sphere_err,
            "spherical_error_percent": (abs(sphere_err) / actual * 100.0) if actual else 0.0,
            "forward_azimuth_deg": fwd, "reverse_azimuth_deg": rev,
            "datum": "WGS84", "semi_major_m": _WGS84_A, "flattening": _WGS84_F,
            "formula": "Vincenty (1975) inverse geodesic on an oblate spheroid"}
    if diff <= threshold:
        return confirm(name,
                       f"geodesic = {actual:.3f} km (matches claim {c}); the spherical model "
                       f"would have said {sphere:.3f} km, off by {sphere_err:+.3f} km",
                       data)
    return mismatch(name, f"geodesic = {actual:.3f} km, claimed {c} (diff {diff:.3f})", data)


def verify_destination_point(spec: Dict[str, Any]) -> VerifierResult:
    """Dead reckoning: from a point, a bearing and a distance, where do you actually land?

    This is the check that matters with no GPS and a compass — and the direct geodesic is the
    honest form of it, because a spherical answer walks you off course by the same 0.5%.
    """
    name = "geography.destination_point"
    lat1, lon1 = spec.get("lat1"), spec.get("lon1")
    brg, dist = spec.get("bearing_deg"), spec.get("distance_km")
    clat, clon = spec.get("claimed_dest_lat"), spec.get("claimed_dest_lon")
    if any(v is None for v in (lat1, lon1, brg, dist, clat, clon)):
        return na(name)
    try:
        a1, o1, b, d = float(lat1), float(lon1), float(brg), float(dist)
        cla, clo = float(clat), float(clon)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if not _coord_valid(a1, o1):
        return error(name, "start coordinates out of range")
    if d < 0:
        return error(name, "distance_km must not be negative")

    s = d * 1000.0
    alpha1 = math.radians(b)
    U1 = math.atan((1 - _WGS84_F) * math.tan(math.radians(a1)))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sigma1 = math.atan2(math.tan(U1), math.cos(alpha1))
    sinAlpha = cosU1 * math.sin(alpha1)
    cos2Alpha = 1 - sinAlpha ** 2
    u2 = cos2Alpha * (_WGS84_A ** 2 - _WGS84_B ** 2) / (_WGS84_B ** 2)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))

    sigma = s / (_WGS84_B * A)
    for _ in range(200):
        cos2SigmaM = math.cos(2 * sigma1 + sigma)
        sinSigma, cosSigma = math.sin(sigma), math.cos(sigma)
        dSigma = B * sinSigma * (cos2SigmaM + B / 4 * (
            cosSigma * (-1 + 2 * cos2SigmaM ** 2) -
            B / 6 * cos2SigmaM * (-3 + 4 * sinSigma ** 2) * (-1 + 4 * cos2SigmaM ** 2)))
        prev = sigma
        sigma = s / (_WGS84_B * A) + dSigma
        if abs(sigma - prev) < 1e-12:
            break
    else:
        return error(name, "direct geodesic did not converge — CANNOT_CHECK")

    sinSigma, cosSigma = math.sin(sigma), math.cos(sigma)
    cos2SigmaM = math.cos(2 * sigma1 + sigma)
    lat2 = math.atan2(sinU1 * cosSigma + cosU1 * sinSigma * math.cos(alpha1),
                      (1 - _WGS84_F) * math.sqrt(sinAlpha ** 2 +
                      (sinU1 * sinSigma - cosU1 * cosSigma * math.cos(alpha1)) ** 2))
    lam = math.atan2(sinSigma * math.sin(alpha1),
                     cosU1 * cosSigma - sinU1 * sinSigma * math.cos(alpha1))
    C = _WGS84_F / 16 * cos2Alpha * (4 + _WGS84_F * (4 - 3 * cos2Alpha))
    L = lam - (1 - C) * _WGS84_F * sinAlpha * (
        sigma + C * sinSigma * (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM ** 2)))
    a2 = math.degrees(lat2)
    o2 = ((math.degrees(L) + o1 + 540.0) % 360.0) - 180.0

    off_km = _vincenty_inverse(a2, o2, cla, clo)
    off = (off_km[0] / 1000.0) if off_km else float("inf")
    tol = clamp_tol(spec, "tolerance_km", 1.0)
    data = {"from": [a1, o1], "bearing_deg": b, "distance_km": d,
            "actual_dest_lat": a2, "actual_dest_lon": o2,
            "claimed_dest_lat": cla, "claimed_dest_lon": clo,
            "miss_km": off, "tolerance_km": tol, "datum": "WGS84",
            "formula": "Vincenty (1975) direct geodesic on an oblate spheroid"}
    if off <= tol:
        return confirm(name, f"{d} km on bearing {b}° lands at ({a2:.5f}, {o2:.5f}) — "
                             f"{off:.3f} km from the claim", data)
    return mismatch(name, f"lands at ({a2:.5f}, {o2:.5f}), claimed ({cla}, {clo}) — "
                          f"off by {off:.3f} km", data)


def verify_projection_distortion(spec: Dict[str, Any]) -> VerifierResult:
    """What a flat map costs you at a given latitude, as a number rather than a complaint.

    'No flat map is honest' is a theorem, not an opinion: Gauss's Theorema Egregium says a sphere
    cannot be flattened without stretching, because Gaussian curvature is intrinsic. Web Mercator
    (EPSG:3857 — the projection under nearly every slippy map on Earth) is conformal, so it keeps
    ANGLES exactly and pays for it entirely in AREA: a feature at latitude φ is drawn sec²φ times
    too large. That is why Greenland looks the size of Africa on a phone.
    """
    name = "geography.projection_distortion"
    lat = spec.get("lat_for_projection")
    c_area = spec.get("claimed_area_inflation")
    c_scale = spec.get("claimed_scale_factor")
    if lat is None or (c_area is None and c_scale is None):
        return na(name)
    try:
        phi = float(lat)
    except (TypeError, ValueError):
        return error(name, "lat_for_projection must be numeric")
    if not (-90.0 <= phi <= 90.0):
        return error(name, f"latitude out of range, got {phi}")
    if abs(phi) >= 89.5:
        return error(name,
                     "Web Mercator is undefined at the poles (sec φ → ∞); it is normally cut at "
                     "±85.05° so the map is square — CANNOT_CHECK, not a mismatch",
                     {"latitude": phi, "standard_cutoff_deg": 85.0511287798066})

    k = 1.0 / math.cos(math.radians(phi))     # linear scale factor
    area = k * k                              # area inflation
    data = {"latitude": phi, "actual_scale_factor": k, "actual_area_inflation": area,
            "projection": "Web Mercator (EPSG:3857), conformal",
            "preserved": "angles and shape locally", "sacrificed": "area",
            "why": "Gauss's Theorema Egregium — a curved surface has no distortion-free flattening",
            "formula": "k = sec φ ; area factor = sec² φ"}
    tol = clamp_tol(spec, "tolerance_relative", 0.01)

    if c_area is not None:
        try:
            ca = float(c_area)
        except (TypeError, ValueError):
            return error(name, "claimed_area_inflation must be numeric")
        data["claimed_area_inflation"] = ca
        if abs(area - ca) <= max(1e-6, tol * area):
            return confirm(name, f"at {phi}° Web Mercator inflates area {area:.4f}× "
                                 f"(matches claim {ca})", data)
        return mismatch(name, f"at {phi}° area inflation is {area:.4f}×, claimed {ca}", data)

    try:
        cs = float(c_scale)
    except (TypeError, ValueError):
        return error(name, "claimed_scale_factor must be numeric")
    data["claimed_scale_factor"] = cs
    if abs(k - cs) <= max(1e-6, tol * k):
        return confirm(name, f"at {phi}° the scale factor is {k:.4f} (matches claim {cs})", data)
    return mismatch(name, f"at {phi}° the scale factor is {k:.4f}, claimed {cs}", data)


def _clean_ring(poly: Any) -> Optional[List[Tuple[float, float]]]:
    if not isinstance(poly, (list, tuple)) or len(poly) < 3:
        return None
    out: List[Tuple[float, float]] = []
    for p in poly:
        if not isinstance(p, (list, tuple)) or len(p) < 2:
            return None
        try:
            la, lo = float(p[0]), float(p[1])
        except (TypeError, ValueError):
            return None
        if not _coord_valid(la, lo):
            return None
        out.append((la, lo))
    if out[0] == out[-1]:            # accept an explicitly closed ring
        out = out[:-1]
    return out if len(out) >= 3 else None


def _crosses_antimeridian(ring: Sequence[Tuple[float, float]]) -> bool:
    """Any edge jumping more than 180° of longitude is really crossing the date line."""
    n = len(ring)
    return any(abs(ring[i][1] - ring[(i + 1) % n][1]) > 180.0 for i in range(n))


def verify_point_in_polygon(spec: Dict[str, Any]) -> VerifierResult:
    """Containment by ray casting — with the boundary of the method declared, not assumed.

    Ray casting treats lat/lon as a plane. That is correct for any boundary that does not cross
    the antimeridian and is not wrapped around a pole — which is nearly every county, parish,
    watershed and property line anyone will ask about. Outside that, the method is WRONG rather
    than approximate, so this refuses instead of answering. A refusal that names what it cannot
    do is worth more than a confident wrong containment.
    """
    name = "geography.point_in_polygon"
    ring = _clean_ring(spec.get("polygon"))
    pt = spec.get("point")
    claimed = spec.get("claimed_inside")
    if ring is None or pt is None or claimed is None:
        return na(name)
    if not isinstance(pt, (list, tuple)) or len(pt) < 2:
        return error(name, "point must be [lat, lon]")
    try:
        plat, plon = float(pt[0]), float(pt[1])
    except (TypeError, ValueError):
        return error(name, "point coordinates must be numeric")
    if not _coord_valid(plat, plon):
        return error(name, "point out of range")
    if _crosses_antimeridian(ring):
        return error(name,
                     "this boundary crosses the antimeridian, where planar ray casting is wrong "
                     "rather than approximate — CANNOT_CHECK; split the polygon at ±180°",
                     {"vertices": len(ring)})

    inside = False
    n = len(ring)
    for i in range(n):
        y1, x1 = ring[i]
        y2, x2 = ring[(i + 1) % n]
        if (y1 > plat) != (y2 > plat):
            xint = (x2 - x1) * (plat - y1) / (y2 - y1) + x1
            if plon < xint:
                inside = not inside
    data = {"point": [plat, plon], "vertices": n, "actual_inside": inside,
            "claimed_inside": bool(claimed),
            "method": "even-odd ray casting in the lat/lon plane",
            "valid_when": "boundary does not cross ±180° longitude or enclose a pole"}
    if inside == bool(claimed):
        return confirm(name, f"({plat}, {plon}) inside={inside} (matches claim)", data)
    return mismatch(name, f"({plat}, {plon}) inside={inside}, claimed {bool(claimed)}", data)


def verify_polygon_area(spec: Dict[str, Any]) -> VerifierResult:
    """Area of ground inside a boundary, by spherical excess — how much land is actually there."""
    name = "geography.polygon_area"
    ring = _clean_ring(spec.get("polygon"))
    claimed = spec.get("claimed_area_km2")
    if ring is None or claimed is None:
        return na(name)
    try:
        c = float(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed_area_km2 must be numeric")
    if _crosses_antimeridian(ring):
        return error(name,
                     "boundary crosses the antimeridian — CANNOT_CHECK; split at ±180°",
                     {"vertices": len(ring)})

    # Girard/L'Huilier via the standard spherical-polygon line integral.
    n = len(ring)
    total = 0.0
    for i in range(n):
        la1, lo1 = math.radians(ring[i][0]), math.radians(ring[i][1])
        la2, lo2 = math.radians(ring[(i + 1) % n][0]), math.radians(ring[(i + 1) % n][1])
        total += (lo2 - lo1) * (2 + math.sin(la1) + math.sin(la2))
    actual = abs(total * _EARTH_RADIUS_KM * _EARTH_RADIUS_KM / 2.0)
    rel_tol = clamp_tol(spec, "tolerance_relative", 0.01)
    diff = abs(actual - c)
    data = {"vertices": n, "actual_area_km2": actual, "claimed_area_km2": c, "diff_km2": diff,
            "earth_radius_km": _EARTH_RADIUS_KM,
            "formula": "spherical excess (line integral over the ring)",
            "note": "spherical, not ellipsoidal — good to ~0.3% at any size that fits on a map"}
    if diff <= max(1e-6, rel_tol * actual):
        return confirm(name, f"{n}-vertex boundary encloses {actual:.3f} km² "
                             f"(matches claim {c})", data)
    return mismatch(name, f"boundary encloses {actual:.3f} km², claimed {c} "
                          f"(diff {diff:.3f})", data)


_RULES = [
    (lambda gv: (all(k in gv for k in ("lat", "lon", "claimed_coords_valid"))), verify_lat_lon_validity),
    (lambda gv: (all(k in gv for k in ("lat1", "lon1", "lat2", "lon2", "claimed_distance_km"))), verify_haversine_distance),
    (lambda gv: (all(k in gv for k in ("lat1", "lon1", "lat2", "lon2", "claimed_bearing_deg"))), verify_initial_bearing),
    (lambda gv: (all(k in gv for k in ("longitude_for_utm", "claimed_utm_zone"))), verify_utm_zone),
    # GIS
    (("lat1", "lon1", "lat2", "lon2", "claimed_geodesic_km"), verify_geodesic_distance),
    (("lat1", "lon1", "bearing_deg", "distance_km",
      "claimed_dest_lat", "claimed_dest_lon"), verify_destination_point),
    (lambda gv: "lat_for_projection" in gv and
                ("claimed_area_inflation" in gv or "claimed_scale_factor" in gv),
     verify_projection_distortion),
    (("polygon", "point", "claimed_inside"), verify_point_in_polygon),
    (("polygon", "claimed_area_km2"), verify_polygon_area),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, 'GEO_LOC_VERIFY', _RULES, domain='geography', none_reason='no GEO_LOC_VERIFY artifacts present')
