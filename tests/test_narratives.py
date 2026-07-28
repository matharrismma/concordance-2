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
    assert st == 404 and body.get("gate") == "closed"
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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — charted in the Bible; the components recombine; nobody is labeled.")
