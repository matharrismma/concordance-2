"""OT prophecy -> NT fulfillment — the NT-explicit map (Matt, 2026-08-30).

Proves the map loads, is navigable by verse and by theme, and — the part that matters — stays a
CONDUIT: every pairing is one the New Testament itself names, carried with its source and its verses'
own text, verdict CONCORDANT and NEVER "HOLDS". Reads the real repo data. Runs with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
# Point the module at the repo's curated data file, wherever the test runs from.
os.environ["CONCORDANCE_PROPHECY_MESSIANIC"] = str(
    Path(__file__).resolve().parent.parent / "data" / "prophecy" / "messianic.jsonl")

from concordance import prophecy_fulfillments as pf  # noqa: E402


def test_the_map_loads_and_is_grouped_by_theme():
    assert pf.available()
    d = pf.list_all()
    assert d["count"] >= 40 and d["generated"] is False and d["conduit"] is True
    assert {"birth", "ministry", "passion"} <= set(d["themes"])   # the arc is there


def test_a_verse_finds_the_fulfillments_that_touch_it():
    d = pf.for_ref("Isaiah 53")
    assert d["count"] >= 3
    for m in d["matches"]:                                        # each match really touches Isaiah 53
        refs = [m["ot_ref"]] + m["nt_refs"]
        assert any("isaiah 53" in (r or "").lower() for r in refs)
    # a verse in it works the same as the whole chapter
    assert pf.for_ref("Isaiah 53:4")["count"] >= 1
    # a chapter nothing points to is an honest empty, not a guess
    assert pf.for_ref("Obadiah 1")["count"] == 0


def test_each_pairing_carries_its_verses_source_and_a_conduit_verdict():
    d = pf.list_all()
    for theme in d["themes"].values():
        for m in theme:
            assert (m.get("ot") or {}).get("text")               # the OT verse's own words ride along
            assert m["nt_fulfillments"] and m["nt_fulfillments"][0].get("text")
            assert m.get("source")                               # the NT's own citation, attributed
            assert m["verdict"] == "CONCORDANT"                  # a signpost the NT affirms — NEVER HOLDS
    assert "never HOLDS" in pf.NOTE                              # the discipline reaches the reader


def test_get_returns_one_fulfillment_whole():
    m = pf.list_all()["themes"]["passion"][0]
    full = pf.get(m["id"])
    assert full and full["ot"]["ref"] and full["nt_fulfillments"][0]["ref"]
    assert pf.get("mp_not_a_real_id") is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} prophecy-fulfillment tests passed — the NT names each; a signpost, never a proof.")
