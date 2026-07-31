"""The places of the Bible — coordinates verified, uncertainty honest, both planes served.

What this file pins:

  * the STATUS DISCIPLINE — a "located" place must carry coordinates; an "unlocated" place must
    NOT (an honest blank beats a confident guess); a "disputed" place must name its candidates,
    never plant a single flag silently;
  * every scripture reference resolves against the corpus;
  * every coordinate falls inside the biblical world's bounding box — a typo'd longitude would
    put Ephesus in the Atlantic and no reader would know;
  * the curated coordinates agree with an INDEPENDENT gazetteer (geonames) for cities that
    continue their ancient selves — the map is cross-checked, not asserted. Skipped gracefully
    where the gazetteer is not provisioned (it lives on the build machine, not the box);
  * the gate holds and the agent tool mirrors the human page.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import bible_places  # noqa: E402

GEONAMES_DB = Path("D:/nh-backup/mirror/repo/lw/00_source/geonames/geonames.db")


def test_the_status_discipline_holds():
    for p in bible_places.PLACES:
        st = p["status"]
        assert st in ("located", "disputed", "unlocated"), p["name"]
        if st == "located":
            assert "lat" in p and "lon" in p, f"{p['name']}: located but no coordinates"
        if st == "unlocated":
            assert "lat" not in p and "lon" not in p, \
                f"{p['name']}: unlocated must be an honest blank, not a guess with a caveat"
        if st == "disputed":
            assert p.get("candidates"), f"{p['name']}: disputed must NAME the candidates"


def test_every_reference_resolves():
    from concordance.verifiers.scripture import read_passage
    bad = [(p["name"], r) for p in bible_places.PLACES for r in p.get("refs", [])
           if read_passage(r).get("status") != "ok"]
    assert not bad, f"references that do not resolve: {bad[:6]}"


def test_every_coordinate_is_inside_the_biblical_world():
    """Malta (lon 14.4) to Susa (lon 48.2); Memphis (lat 29.8) to Philippi (lat 41.0)."""
    for p in bible_places.PLACES:
        if "lat" in p:
            assert 27.0 <= p["lat"] <= 42.5, f"{p['name']}: latitude {p['lat']} is outside the region"
            assert 12.0 <= p["lon"] <= 49.0, f"{p['name']}: longitude {p['lon']} is outside the region"


def test_the_map_agrees_with_an_independent_gazetteer():
    """Continuity cities — the modern city stands on (or beside) the ancient one, so geonames'
    coordinates must land within ~0.35 deg of ours. Catches transposed digits and swapped lat/lon."""
    import pytest
    if not GEONAMES_DB.exists():
        pytest.skip("geonames gazetteer not provisioned on this machine")
    import sqlite3
    con = sqlite3.connect(f"file:{GEONAMES_DB}?mode=ro", uri=True)
    # Country-constrained on purpose: unconstrained, the gazetteer's biggest "Bethlehem" is in
    # SOUTH AFRICA, its "Sur" in Oman, its "Saida" in Algeria — the exact false-flag class this
    # atlas exists to avoid. (Found live when this check first ran without the constraint.)
    checks = {"Jerusalem": ("jerusalem", "IL"), "Damascus": ("damascus", "SY"),
              "Athens": ("athens", "GR"), "Rome": ("rome", "IT"),
              "Tarsus": ("tarsus", "TR"), "Thessalonica": ("thessaloniki", "GR"),
              "Bethlehem": ("bethlehem", "PS"), "Tyre": ("tyre", "LB"),
              "Sidon": ("sidon", "LB"), "Nazareth": ("nazareth", "IL"),
              "Haran": ("harran", "TR"), "Gaza": ("gaza", "PS")}
    for ours_name, (gaz_name, cc) in checks.items():
        ours = bible_places.get(ours_name)
        assert ours is not None, ours_name
        row = con.execute(
            "SELECT lat, lon FROM places WHERE ascii_lc = ? AND cc = ? "
            "ORDER BY population DESC LIMIT 1", (gaz_name, cc)).fetchone()
        assert row, f"gazetteer has no {gaz_name} in {cc}"
        dlat, dlon = abs(row[0] - ours["lat"]), abs(row[1] - ours["lon"])
        assert dlat < 0.35 and dlon < 0.35, \
            f"{ours_name}: ours ({ours['lat']},{ours['lon']}) vs gazetteer ({row[0]},{row[1]})"
    con.close()


def test_the_famous_disputes_are_present():
    sinai = bible_places.get("Mount Sinai (Horeb)")
    assert sinai["status"] == "disputed" and len(sinai["candidates"]) >= 2
    emmaus = bible_places.get("Emmaus")
    assert emmaus["status"] == "unlocated" and len(emmaus["candidates"]) >= 3, \
        "Emmaus has four serious candidates and no flag may be planted"
    golgotha = bible_places.get("Golgotha (Calvary)")
    assert golgotha["status"] == "disputed", "both the Sepulchre and the Garden Tomb are carried"
    eden = bible_places.get("Eden")
    assert eden["status"] == "unlocated" and "lat" not in eden


def test_the_gate_holds_and_the_route_serves():
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    st, body = dispatch("GET", "/places", {}, None, EngineConfig("secular"))
    # SEEING, not understanding. Matt, 2026-07-31: "seeing them is fine — understanding
    # the deeper meaning comes after the gate" and "we don't need to refuse use, we refuse
    # abuse". The text and its reference apparatus answer on both surfaces now; only
    # exposition waits (api.AFTER_THE_GATE).
    assert st == 200 and body.get("gate") != "closed"   # the Atlas is seeing
    st2, body2 = dispatch("GET", "/places", {}, None, EngineConfig("witness"))
    assert st2 == 200 and body2["count"] == len(bible_places.PLACES)
    st3, body3 = dispatch("GET", "/places", {"name": "Jerusalem"}, None, EngineConfig("witness"))
    assert st3 == 200 and body3["name"] == "Jerusalem"
    st4, _ = dispatch("GET", "/places", {"name": "Atlantis"}, None, EngineConfig("witness"))
    assert st4 == 404


def test_agents_get_the_same_map_humans_do():
    from concordance import mcp
    from concordance.config import EngineConfig
    wit = EngineConfig("witness")
    names = {t["name"] for t in mcp.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, wit, {})["result"]["tools"]}
    assert "bible_places" in names
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "bible_places", "arguments": {}}}, wit, {})
    body = json.loads(r["result"]["content"][0]["text"])
    assert body["count"] == len(bible_places.PLACES)
    assert body["by_status"]["unlocated"] >= 4, "the honest blanks must reach agents too"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the map is verified, and its blanks are honest.")
