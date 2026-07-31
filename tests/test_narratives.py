"""The storyboards — charted in the Bible, components that recombine, reference points not labels.

Matt, 2026-07-28: "We develop story boards or the common narratives. We begin charting in the
Bible. Once that is complete we can isolate the components and mix and match... You may be many of
these characters at times of your life. They are just a reference point."

Pinned here:
  * every reference in every storyboard resolves against the corpus — charted, not asserted;
  * every movement used by any instance exists in the ONE shared vocabulary — that sharedness is
    what makes mix-and-match possible, so a stray beat name would quietly break the design;
  * by_movement genuinely traces a component across storyboards (testing: Israel, Elijah, Jesus);
  * the FRAMING travels on every response shape — index, single storyboard, movement trace — and
    over the wire and to agents: "a reference point, not an identity" must reach whoever reads;
  * the gate holds on the secular surface.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import narratives  # noqa: E402


def test_every_reference_in_every_storyboard_resolves():
    from concordance.verifiers.scripture import read_passage
    bad = [r for r in narratives.all_refs() if read_passage(r).get("status") != "ok"]
    assert not bad, f"storyboard refs that do not resolve: {bad[:8]}"


def test_every_beat_uses_the_shared_vocabulary():
    """Mix-and-match works ONLY because the vocabulary is shared. A beat named outside it would
    be invisible to by_movement — a component that cannot be isolated."""
    for n in narratives.NARRATIVES:
        for mv in n["movements"]:
            assert mv in narratives.MOVEMENTS, f"{n['id']} lists unknown movement {mv!r}"
        for inst in n["instances"]:
            for beat in (inst.get("beats") or {}):
                assert beat in narratives.MOVEMENTS, \
                    f"{n['id']} / {inst['who']}: beat {beat!r} is outside the shared vocabulary"


def test_a_component_isolates_and_traces_across_storyboards():
    t = narratives.by_movement("testing")
    whos = " ".join(a["who"] for a in t["appearances"])
    assert "Israel" in whos and "Jesus" in whos, \
        "'testing' must walk the wilderness through Israel and Jesus at least"
    assert len({a["narrative_id"] for a in t["appearances"]}) >= 3, \
        "isolating one component must cross MULTIPLE storyboards — that is the mix-and-match"
    # Elijah's wilderness beats are descent/provision/call — provision is where he traces
    p = narratives.by_movement("provision")
    assert "Elijah" in " ".join(a["who"] for a in p["appearances"]), \
        "the ravens and the cake at Horeb are provision, and the trace must find them"
    assert narratives.by_movement("no_such_movement") is None


def test_the_framing_travels_on_every_shape():
    """'A reference point, not an identity' is the pastoral guard — it must be ON the data,
    not in a comment, because whoever renders the data is who the person hears."""
    assert "not an identity" in narratives.FRAMING
    assert narratives.storyboards()["framing"] == narratives.FRAMING
    assert narratives.get("exile_and_return")["framing"] == narratives.FRAMING
    assert narratives.by_movement("return")["framing"] == narratives.FRAMING


def test_christ_storyboard_carries_its_own_witness():
    n = narratives.get("descent_and_raising")
    christ = [i for i in n["instances"] if i["who"].startswith("Christ")]
    assert christ and "Matthew 12:40" in (christ[0].get("note") or ""), \
        "Jesus names Jonah's descent as His own sign — the storyboard must say so"


def test_the_gate_holds_and_agents_get_the_same_boards():
    from concordance import mcp
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    st, body = dispatch("GET", "/narratives", {}, None, EngineConfig("secular"))
    # 2026-07-31: knowledge is open on BOTH doors — "we don't hide knowledge, we aren't a
    # secret society". This asserted the tool was hidden from the secular surface; it now
    # asserts the parity that replaced it.
    assert st == 200 and body.get("gate") != "closed"
    st2, body2 = dispatch("GET", "/narratives", {}, None, EngineConfig("witness"))
    assert st2 == 200 and body2["count"] == len(narratives.NARRATIVES)
    st3, body3 = dispatch("GET", "/narratives", {"movement": "reversal"}, None, EngineConfig("witness"))
    assert st3 == 200 and body3["count"] >= 2

    wit = EngineConfig("witness")
    names = {t["name"] for t in mcp.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, wit, {})["result"]["tools"]}
    assert "narratives" in names and "study_find" in names
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "narratives", "arguments": {"movement": "testing"}}}, wit, {})
    body = json.loads(r["result"]["content"][0]["text"])
    assert body["count"] >= 3 and "not an identity" in body["framing"]


def test_the_matcher_meets_a_person_and_ignores_the_mundane():
    """Matt's step 3: application. A first-person situation finds the movement it stands in;
    mundane text finds NOTHING — the 'is 15 = Isaiah 15' lesson, applied before the bug exists."""
    m = narratives.match("I feel so far from home, like I do not belong anywhere anymore")
    assert m and m["movement"] == "exile"
    assert any("Jacob" in x["who"] or "Israel" in x["who"] for x in m["who_stood_here"])
    assert "not an identity" in m["framing"], "the framing rides the payload, always"
    m2 = narratives.match("I have been waiting for years and the promise still has not come")
    assert m2 and m2["movement"] == "delay"
    assert narratives.match("what is 8 times 7") is None
    assert narratives.match("the weather is nice today") is None
    assert narratives.match("") is None


def test_comfort_carries_the_storyboard_and_crisis_never_does():
    """The storyboard sits BENEATH the seat in the comfort lane. Crisis is a separate, higher lane
    and must never be met with a narrative — a person in danger gets the real help, nothing else."""
    import os
    import tempfile
    from concordance import ask
    from concordance.config import EngineConfig
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    try:
        cfg = EngineConfig("witness")
        d = ask.respond("I feel so far from home and from God, cut off from everyone",
                        cfg, gate_open=True)
        assert d.get("kind") == "comfort"
        assert (d.get("storyboard") or {}).get("movement") == "exile"
        assert "not an identity" in d["storyboard"]["framing"]
        d2 = ask.respond("I want to end my life", cfg, gate_open=True)
        assert d2.get("kind") == "crisis"
        assert "storyboard" not in d2, "crisis must never be met with a narrative"
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_the_seat_and_storyboard_reach_the_reader():
    """Found 2026-07-28: the archetype SEAT had been attached server-side since the archetypes
    shipped and NO page ever rendered it — the guarantee stopped short of the reader, again
    (the sixth instance of the pattern this project has now caught). Pinned so neither the seat
    nor the storyboard can go invisible twice."""
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert "d.seat" in html, "the front door must render the seat"
    assert "d.storyboard" in html, "the front door must render the storyboard"
    assert "never an identity" in html or "not an identity" in html.lower() or \
           "framing" in html, "the framing must be shown, not merely carried"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — charted in the Bible; the components recombine; nobody is labeled.")
