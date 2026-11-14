"""THE MEANING TEST of data/sticks/sky_data_stream.json (run 2026-11-14-sky-stream, step sky).

A golden pins what an entry mints, by content hash, and not what its seals mean. This file holds the entry's nine
sealed expressions to their sources: each constant is stated once below with the source it was read from (public GETs
of 2026-11-14, named in the step's build note), and each seal's expr must be exactly its template applied to those
constants, its value the expression's own float. The noon seals' latitude is the ephemeris entry's own sun_nyc
latitude, and their T is the Julian Day of the USNO solstice moment by verifiers.ephemeris._julian_day, from J2000 in
Julian centuries. Each seal holds through verify_derivation in the numeric shape while a claim moved by one part in 1e6
does not; the marks are the nine sealed instances, once each, and two notes; and no field is longer than tickstick
keeps, since it cuts a longer one without a word."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ENTRY = ROOT / "data" / "sticks" / "sky_data_stream.json"
EPHEMERIS = ROOT / "data" / "sticks" / "ephemeris.json"

# THE CONSTANTS, each stated once, with the source it was read from.
AU_M = "149597870700"       # a, taken as 1 au: IAU 2012 Resolution B2, 'a conventional unit of length equal to
#                             149 597 870 700 m exactly', a defined unit and not Earth's semi-major axis
C_M_S = "299792458"         # c in m/s, a defining constant of the SI (BIPM, the SI Brochure, 9th edition, 2019)
C_KM_S = "299792.458"       # the same c in km/s
P_DAYS = "365.256363004"    # Earth's sidereal orbital period in days, epoch J2000 (Wikipedia, Earth, its infobox)
DAY_S = "86400"             # the day of 86400 s (Wikipedia, Astronomical constant: the astronomical unit of time)
ECC = "0.0167086"           # Earth's orbital eccentricity, epoch J2000 (Wikipedia, Earth, its infobox)
P03 = "5028.796195"         # the linear term of the IAU 2006 (P03) general precession p_A, arcsec per Julian century:
#                             the rate at J2000.0, which grows by the next term, +1.1054348 t^2 (ERFA src/p06e.c;
#                             Capitaine, Wallace and Chapront 2003)
T0_K = "2.72548"            # the CMB temperature in K (Fixsen 2009, arXiv:0911.1955)
V_KM_S = "369.82"           # the Sun's speed against the CMB in km/s (Planck 2018 results I, Sect. 2.1 and Table 3)
H_HZ = "1420405751.768"     # hydrogen's unperturbed hyperfine frequency in Hz (Hellwig et al. 1970, NIST's copy)
GAIA_N = "1811709771"       # Gaia DR3's total number of sources (ESA, cosmos.esa.int/web/gaia/dr3)
OBL06 = ("84381.406", "46.836769", "0.0001831", "0.00200340")
#                             the IAU 2006 mean obliquity of the ecliptic in arcsec (ERFA src/obl06.c), taken to T^3:
#                             its T^4 and T^5 terms are left out, and its T, in TT, is reckoned here from the UT moment
J2000_JD, CENTURY_D = "2451545", "36525"     # ERFA_DJ00 and ERFA_DJC (ERFA src/erfam.h)
SOLSTICE_UT = (2024, 6, 20, 20, 51)          # the 2024 June solstice in UT (USNO, aa.usno.navy.mil/api/seasons)
SOLSTICE_JD = "2460482.36875"                # its Julian Day by verifiers.ephemeris._julian_day (checked below)
LAT_NYC = "40.7128"                          # the ephemeris entry's sun_nyc latitude (checked below)
SIGHT = "72.72"             # noon_height's sealed value rounded to two decimals: a worked example, not an observation

T = f"(({SOLSTICE_JD} - {J2000_JD})/{CENTURY_D})"
EPS = f"({OBL06[0]} - {OBL06[1]}*{T} - {OBL06[2]}*{T}**2 + {OBL06[3]}*{T}**3)/3600"
TEMPLATES = {
    "aberration": f"2*pi*{AU_M}/({C_M_S}*{P_DAYS}*{DAY_S}*sqrt(1 - {ECC}**2))*180/pi*3600",   # arcsec
    "precession_per_degree": f"3600/({P03}/100)",                                            # years per degree
    "precession_turn": f"1296000/({P03}/100)",                                               # years per turn
    "cmb_dipole": f"{T0_K}*{V_KM_S}/{C_KM_S}*1000",                                          # mK
    "hydrogen_period": f"1e9/{H_HZ}",                                                        # ns
    "hydrogen_wavelength": f"{C_M_S}/{H_HZ}*100",                                            # cm
    "gaia_bits": f"log({GAIA_N})/log(2)",                                                    # bits
    "noon_height": f"90 - {LAT_NYC} + {EPS}",                                                # degrees
    "noon_sight": f"90 - {SIGHT} + {EPS}",                                                   # degrees
}
KEYS = list(TEMPLATES)


def entry() -> dict:
    return json.loads(ENTRY.read_text(encoding="utf-8"))


def seals() -> dict:
    return {s["key"]: s for s in entry()["seals"]}


def sun_nyc() -> dict:
    return next(s for s in json.loads(EPHEMERIS.read_text(encoding="utf-8"))["seals"] if s["key"] == "sun_nyc")


def verdict(seal: dict, claimed: float) -> str:
    """The seal path's own check (sticks.seal_numeric): verify_derivation on the numeric shape."""
    from concordance.derivation import verify_derivation
    return verify_derivation([{"id": seal["nid"], "domain": seal["domain"], "spec": {"mode": "numeric", "params": {
        "numeric_expr": seal["expr"], "claimed_value": claimed, "rel_tol": seal["tol"]}}}])["verdict"]


def test_the_entry_holds_exactly_the_nine_numeric_seals_in_order():
    e = entry()
    assert (e["schema"], e["name"], e["aliases"]) == (1, "sky_data_stream", ["sky_data_stream", "sky_stream"])
    assert list(seals()) == KEYS
    for key, s in seals().items():
        assert set(s) == {"key", "nid", "expr", "value", "tol", "domain"}, key
        assert (s["nid"], s["domain"], s["tol"]) == ("sky_" + key, "mathematics", 1e-9), key


@pytest.mark.parametrize("key", KEYS)
def test_each_seal_expr_is_exactly_its_template_applied_to_the_stated_constants(key):
    assert seals()[key]["expr"] == TEMPLATES[key]


@pytest.mark.parametrize("key", KEYS)
def test_each_seal_value_is_its_expressions_own_float(key):
    from concordance.verifiers import mathematics
    s = seals()[key]
    assert s["value"] == float(mathematics._parse(s["expr"], []).evalf())


def test_the_noon_seals_latitude_is_the_ephemeris_entrys_sun_nyc_lat():
    lat = sun_nyc()["spec"]["lat"]
    assert repr(lat) == LAT_NYC
    assert seals()["noon_height"]["expr"].startswith(f"90 - {lat!r} + (")


def test_the_noon_seals_t_is_the_julian_day_of_the_usno_solstice_from_j2000_in_julian_centuries():
    from concordance.verifiers.ephemeris import _julian_day
    year, month, day, hour, minute = SOLSTICE_UT
    assert _julian_day(year, month, day + (hour * 60 + minute) / 1440) == float(SOLSTICE_JD)
    assert _julian_day(2000, 1, 1.5) == float(J2000_JD)                  # J2000.0, 2000 January 1.5
    for key in ("noon_height", "noon_sight"):
        assert seals()[key]["expr"].count(T) == 3, key                  # T, T**2 and T**3, written out in place


def test_noon_sight_reads_back_noon_heights_sealed_value_rounded_to_two_decimals():
    s = seals()
    assert round(s["noon_height"]["value"], 2) == float(SIGHT)
    # Both add the same EPS, so the sight's distance from the latitude is the rounding and nothing else.
    gap = s["noon_sight"]["value"] - float(LAT_NYC)
    assert abs(gap - (s["noon_height"]["value"] - float(SIGHT))) < 1e-9 and 0.0032 < gap < 0.0034


@pytest.mark.parametrize("key", KEYS)
def test_each_seal_holds_through_verify_derivation_and_a_claim_moved_by_one_part_in_1e6_does_not(key):
    s = seals()[key]
    assert verdict(s, s["value"]) == "HOLDS"
    assert verdict(s, s["value"] * (1 + 1e-6)) == "BROKEN"


def test_the_marks_name_exactly_the_nine_seals_once_each_plus_two_notes():
    st = entry()["sticks"]
    assert len(st) == 1 and st[0]["question"] == "The sky as a data stream" and st[0]["field"] == "ephemeris"
    assert [(m["kind"], m.get("seal")) for m in st[0]["marks"]] == [("instance", k) for k in KEYS] + [("note", None)] * 2
    assert all(set(m) == ({"kind", "claim", "seal"} if "seal" in m else {"kind", "claim"}) for m in st[0]["marks"])


def test_the_stick_is_stick_the_sky_as_a_data_stream_and_no_other_entry_states_it():
    from concordance import tickstick
    assert "stick_" + tickstick._slug(entry()["sticks"][0]["question"]) == "stick_the_sky_as_a_data_stream"
    for path in sorted(ENTRY.parent.glob("*.json")):
        if path != ENTRY:
            other = json.loads(path.read_text(encoding="utf-8"))
            assert all(tickstick._slug(st.get("question", "")) != "the_sky_as_a_data_stream"
                       for st in other.get("sticks", [])), path.name


def test_no_field_is_cut_on_the_way_in():
    """tickstick.create keeps question[:300], statement[:2000], field[:80] and references[:12], each [:300], and tick
    keeps claim[:CLAIM_CAP] and by[:80], all without a word: every field here fits, so nothing is cut."""
    from concordance import tickstick
    st = entry()["sticks"][0]
    assert len(st["question"]) <= 300 and 0 < len(st["statement"]) <= 2000
    assert 0 < len(st["field"]) <= 80 and 0 < len(st["by"]) <= 80
    assert 0 < len(st["references"]) <= 12 and all(0 < len(r) <= 300 for r in st["references"])
    assert all(8 <= len(m["claim"].strip()) == len(m["claim"]) <= tickstick.CLAIM_CAP for m in st["marks"])
