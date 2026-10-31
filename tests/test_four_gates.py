"""The Four Gates (four_gates.py — the DECISION protocol; gates.py beside it is the engine's verdict helpers) — a
decision walked RED → FLOOR → BROTHERS → GOD with no model.

Pins: a RED hit halts with its citation and the rest skipped; a FLOOR error halts; a FLOOR warning rides as a
concern; a BROKEN fact halts at FLOOR; no witness → AWAITING with the doors; witness == author → AWAITING
(self-confirmation refused); an independent witness passes BROTHERS; GOD is always RETURNED, never PASS/HALT; a
cry goes to the crisis response; the route exists, is rate-limited, and refuses an empty action. Runnable with
pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import four_gates as gates  # noqa: E402

CLEAN = {"red": [], "floor_error": [], "floor_warn": [], "warnings": [], "worst": None, "rejects": False}
NO_CRISIS = lambda t: False  # noqa: E731


def _hit(i, name, cite, matched="x"):
    return {"id": i, "name": name, "cite": cite, "matched": matched, "severity": "red"}


def _panel(verdict=None, cards=()):
    served = {"name": "the Bookkeeper", "verify": ({"verdict": verdict, "detail": "d"} if verdict else None),
              "gathered": [{"id": c, "title": c} for c in cards],
              "voice": {"boundary": "I count the cost; I never move your money.", "refer": None}}
    return {"ok": True, "panel": [{"id": "face_steward", "expert": "the Bookkeeper", "score": 3, "served": served}]}


def _shepherd(text, **kw):
    return {"gathered": [{"id": "card_src_scripture_prov_3_5", "title": "Proverbs 3:5", "shelf": "scripture"}],
            "offering": {"parable": "x"}, "voice": {"beyond": "I point to the Good Shepherd, not to myself.", "close": "Go in peace."}}


def test_a_red_hit_halts_with_its_citation_and_skips_the_rest():
    scan = dict(CLEAN, red=[_hit("R1", "false witness", "Proverbs 12:22", "fake reviews")])
    out = gates.run("post fake reviews for my shop", crisis_fn=NO_CRISIS, scan_fn=lambda t: scan)
    assert out["verdict"] == "HALTED" and out["halted_at"] == "RED"
    red = out["gates"][0]
    assert red["gate"] == "RED" and red["status"] == "HALT" and red["cites"] == ["Proverbs 12:22"]
    assert "fake reviews" in red["reasons"][0]
    assert [g["status"] for g in out["gates"][1:]] == ["SKIPPED", "SKIPPED", "SKIPPED"]
    assert out["record"]["gates"][0] == {"gate": "RED", "status": "HALT"} and len(out["action_sha256"]) == 64


def test_a_floor_error_halts_and_a_warning_rides_as_a_concern():
    scan = dict(CLEAN, floor_error=[_hit("F1", "no reserve", "Luke 14:28", "spend it all")])
    out = gates.run("spend it all this month", crisis_fn=NO_CRISIS, scan_fn=lambda t: scan)
    assert out["verdict"] == "HALTED" and out["halted_at"] == "FLOOR" and out["gates"][1]["cites"] == ["Luke 14:28"]
    warn = dict(CLEAN, floor_warn=[_hit("F2", "retention", "keep only what stewardship requires")])
    out = gates.run("keep every record forever", crisis_fn=NO_CRISIS, scan_fn=lambda t: warn, convene_fn=lambda *a, **k: _panel())
    floor = out["gates"][1]
    assert floor["status"] == "PASS" and floor["concerns"] and "F2" in floor["concerns"][0]
    assert out["verdict"] == "AWAITING WITNESS"                                           # a warning never halts


def test_a_broken_fact_halts_at_floor_and_a_held_one_is_cited():
    out = gates.run("take the loan at this rate", crisis_fn=NO_CRISIS, scan_fn=lambda t: CLEAN,
                    convene_fn=lambda *a, **k: _panel("BROKEN", ["card_rate"]))
    assert out["verdict"] == "HALTED" and out["halted_at"] == "FLOOR"
    assert "does not hold" in out["gates"][1]["reasons"][0] and out["gates"][1]["cites"] == ["card_rate"]
    out = gates.run("take the loan at this rate", crisis_fn=NO_CRISIS, scan_fn=lambda t: CLEAN,
                    convene_fn=lambda *a, **k: _panel("HOLDS", ["card_rate", "card_apr"]))
    floor = out["gates"][1]
    assert floor["status"] == "PASS" and [r["id"] for r in floor["rests_on"]] == ["card_rate", "card_apr"]
    assert floor["faces"][0]["boundary"].startswith("I count the cost")                 # the face speaks its boundary


def test_the_keeping_unreachable_is_a_gap_not_a_verdict():
    def boom(*a, **k):
        raise RuntimeError("corpus down")
    out = gates.run("plant the north field", crisis_fn=NO_CRISIS, scan_fn=lambda t: CLEAN, convene_fn=boom)
    assert out["gates"][1]["status"] == "PASS" and "unverified" in out["gates"][1]["reasons"][0]


def test_brothers_awaits_without_a_witness_and_refuses_self_confirmation():
    out = gates.run("sell the truck", crisis_fn=NO_CRISIS, scan_fn=lambda t: CLEAN, convene_fn=lambda *a, **k: _panel())
    b = out["gates"][2]
    assert b["gate"] == "BROTHERS" and b["status"] == "AWAITING" and b["doors"] == [gates.MESH_DOOR, gates.GROUP_DOOR]
    assert out["gates"][3]["status"] == "SKIPPED" and out["verdict"] == "AWAITING WITNESS"
    out = gates.run("sell the truck", crisis_fn=NO_CRISIS, scan_fn=lambda t: CLEAN, convene_fn=lambda *a, **k: _panel(),
                    witness={"id": "nh_abc"}, author={"id": "NH_ABC"})         # same identity, different case
    b = out["gates"][2]
    assert b["status"] == "AWAITING" and "self-confirmation" in b["reasons"][0]


def test_an_independent_witness_passes_and_god_is_always_returned():
    out = gates.run("sell the truck to pay the debt", crisis_fn=NO_CRISIS, scan_fn=lambda t: CLEAN,
                    convene_fn=lambda *a, **k: _panel(), witness={"id": "nh_brother"}, author={"id": "nh_me"},
                    shepherd_fn=_shepherd)
    assert [g["status"] for g in out["gates"]] == ["PASS", "PASS", "PASS", "RETURNED"]
    god = out["gates"][3]
    assert god["status"] == "RETURNED" and "Proverbs 9:10" in god["cites"] and god["passages"][0]["title"] == "Proverbs 3:5"
    assert god["voice"]["beyond"].startswith("I point to the Good Shepherd")
    assert out["verdict"] == "RETURNED" and out["halted_at"] is None
    assert "never generated" in out["means"]
    for g in out["gates"]:
        assert g["status"] != "PASS" or g["gate"] != "GOD"                                  # the machine never passes GOD


def test_a_cry_outranks_the_gates():
    out = gates.run("I want to end it all", crisis_fn=lambda t: True, scan_fn=lambda t: CLEAN)
    assert out["kind"] == "crisis" and out["verdict"] == "CRISIS" and out["gates"] == []
    assert gates.run("   ").get("error") == "action required"


def test_the_route_exists_is_rate_limited_and_refuses_an_empty_action():
    from concordance.web.api import ROUTES, dispatch
    from concordance.config import EngineConfig
    route = next(r for r in ROUTES if r["path"] == "/gates")
    assert route["methods"] == ("POST",) and route.get("rl") is True
    st, payload = dispatch("POST", "/gates", {}, {"action": ""}, EngineConfig("secular"))
    assert st == 400 and "action required" in payload.get("error", "")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("ALL PASS")
