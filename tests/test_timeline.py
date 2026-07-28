"""Timeline — Old Testament, New Testament, Church History, one spine. Proves: every entry is a
well-formed row, eras group in narrative order, get() fetches real verbatim WEB text for single-
chapter refs, disputed dates carry both positions and nothing else claims a winner, an unknown id
declines rather than guessing, the witness-gated /timeline endpoint, and the MCP tool. Runnable with
pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_BIBLE_EN", str(Path(__file__).resolve().parent.parent / "data" / "bible_en.jsonl"))

from concordance import mcp, timeline  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def test_every_event_is_well_formed_and_ids_are_unique():
    d = timeline.eras()
    assert d["total"] == len(timeline._TIMELINE) == 100
    seen_ids = set()
    for era in d["eras"]:
        for period in era["periods"]:
            for ev in period["events"]:
                assert ev["id"] not in seen_ids, f"duplicate id {ev['id']}"
                seen_ids.add(ev["id"])
                assert ev["event"], f"{ev['id']} has no event name"
                assert ev["date"], f"{ev['id']} has no date"


def test_eras_group_in_narrative_order():
    d = timeline.eras()
    names = [e["era"] for e in d["eras"]]
    assert names == ["Old Testament", "New Testament", "Church History"]


def test_disputed_events_carry_positions_and_are_flagged():
    g = timeline.get("t011")  # the Exodus — early/late date debate
    assert g and g["event"] == "The Exodus from Egypt"
    assert g["disputed"] is True
    assert len(g["positions"]) == 2
    views = {p["view"].split(" —")[0].split(" (")[0] for p in g["positions"]}
    dates = [p["date"] for p in g["positions"]]
    assert "1446 BC" in dates
    assert any("1250" in d or "1260" in d for d in dates)


def test_undisputed_events_carry_no_positions():
    g = timeline.get("t064")  # Council of Nicaea
    assert g and g["event"] == "The Council of Nicaea"
    assert g["disputed"] is False
    assert g["positions"] == []
    assert g["date"] == "AD 325"


def test_get_fetches_real_verbatim_text_for_a_single_chapter_reference():
    g = timeline.get("t020")  # Solomon's Temple — 1 Kings 6
    assert g and g["event"] == "Solomon's reign begins; Temple construction started"
    assert len(g["refs"]) == 1
    ref = g["refs"][0]
    assert ref["ref"] == "1 Kings 6:1-38"
    assert ref["text"], "expected fetched WEB text for a single-chapter reference"
    assert "temple" in ref["text"].lower() or "house" in ref["text"].lower()


def test_get_handles_a_cross_chapter_reference_without_crashing():
    # t001's ref "Genesis 1:1-2:3" spans two chapters — display-only, declines the inline text
    # gracefully rather than guessing or crashing.
    g = timeline.get("t001")
    assert g is not None
    assert g["refs"][0]["ref"] == "Genesis 1:1-2:3"
    assert g["refs"][0]["text"] == ""


def test_events_with_no_scripture_reference_return_an_empty_refs_list():
    g = timeline.get("t064")  # Council of Nicaea — a church-history event, no scripture ref
    assert g is not None
    assert g["refs"] == []


def test_unknown_id_declines_rather_than_guessing():
    assert timeline.get("bogus") is None
    assert timeline.get("") is None
    assert timeline.get(None) is None


def test_endpoint_is_witness_gated():
    assert dispatch("GET", "/timeline", {}, None, SEC)[0] == 404
    st, p = dispatch("GET", "/timeline", {}, None, WIT)
    assert st == 200 and p["total"] == 100
    st2, g = dispatch("GET", "/timeline", {"id": "t089"}, None, WIT)
    assert st2 == 200 and "Pilgrims" in g["event"]
    assert dispatch("GET", "/timeline", {"id": "nope"}, None, WIT)[0] == 404


def test_mcp_timeline_tool_is_witness_only():
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, WIT)
    assert "timeline" in {t["name"] for t in r["result"]["tools"]}
    r2 = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)
    assert "timeline" not in {t["name"] for t in r2["result"]["tools"]}
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "timeline", "arguments": {"id": "t054"}}}, WIT)
    assert json.loads(c["result"]["content"][0]["text"])["event"] == "John's exile on Patmos; the writing of Revelation"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} timeline tests passed — Old Testament, New Testament, Church History, found and cited.")
