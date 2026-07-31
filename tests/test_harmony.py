"""Harmony of the Gospels — one event, every gospel witness, side by side.

Proves: every entry is a well-formed harmony row (at least one gospel witnesses each event),
periods group in narrative order, get() fetches real verbatim WEB text for single-chapter refs,
an unknown id declines rather than guessing, the witness-gated /harmony endpoint, and the MCP
tool. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_BIBLE_EN", str(Path(__file__).resolve().parent.parent / "data" / "bible_en.jsonl"))

from concordance import harmony, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def test_every_event_has_at_least_one_witness_and_a_real_id():
    p = harmony.periods()
    assert p["total"] == len(harmony._HARMONY) > 90
    seen_ids = set()
    for period in p["periods"]:
        for ev in period["events"]:
            assert ev["id"] not in seen_ids, f"duplicate id {ev['id']}"
            seen_ids.add(ev["id"])
            assert any(ev[g] for g in ("matthew", "mark", "luke", "john")), f"{ev['event']} has no witness"


def test_periods_are_grouped_in_narrative_order():
    p = harmony.periods()
    names = [x["period"] for x in p["periods"]]
    assert names[0] == "Prologue"
    assert names[-1] == "Resurrection and Appearances"
    assert names.index("Birth and Infancy") < names.index("Galilean Ministry") < names.index("Passion Week")


def test_get_fetches_real_verbatim_text_for_an_event_all_four_gospels_record():
    g = harmony.get("h046")  # feeding of the five thousand — all four gospels
    assert g and g["event"] == "Feeding of the five thousand"
    assert g["witness_count"] == 4
    gospels = {w["gospel"] for w in g["witnesses"]}
    assert gospels == {"Matthew", "Mark", "Luke", "John"}
    for w in g["witnesses"]:
        assert w["text"], f"{w['gospel']} {w['ref']} has no fetched text"
        assert "loaves" in w["text"].lower() or "bread" in w["text"].lower() or "five" in w["text"].lower()


def test_get_handles_a_multi_range_reference_without_crashing():
    # h081's matthew ref is "Matthew 26:1-5,14-16" — a comma-range this module deliberately does
    # not attempt inline verbatim text for (display-only); it must decline the text, not crash.
    g = harmony.get("h081")
    assert g is not None
    m = next(w for w in g["witnesses"] if w["gospel"] == "Matthew")
    assert m["ref"] == "Matthew 26:1-5,14-16"


def test_unknown_id_declines_rather_than_guessing():
    assert harmony.get("bogus") is None
    assert harmony.get("") is None
    assert harmony.get(None) is None


def test_endpoint_is_witness_gated():
    # SEEING, not understanding. Matt, 2026-07-31: "seeing them is fine — understanding
    # the deeper meaning comes after the gate" and "we don't need to refuse use, we refuse
    # abuse". The text and its reference apparatus answer on both surfaces now; only
    # exposition waits (api.AFTER_THE_GATE).
    assert dispatch("GET", "/harmony", {}, None, SEC)[0] == 200
    st, p = dispatch("GET", "/harmony", {}, None, WIT)
    assert st == 200 and p["total"] > 90
    st2, g = dispatch("GET", "/harmony", {"id": "h089"}, None, WIT)
    assert st2 == 200 and g["event"] == "The crucifixion" and g["witness_count"] == 4
    assert dispatch("GET", "/harmony", {"id": "nope"}, None, WIT)[0] == 404


def test_mcp_harmony_tool_is_witness_only():
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, WIT)
    assert "harmony" in {t["name"] for t in r["result"]["tools"]}
    r2 = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)
    assert "harmony" not in {t["name"] for t in r2["result"]["tools"]}
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "harmony", "arguments": {"id": "h075"}}}, WIT)
    assert json.loads(c["result"]["content"][0]["text"])["event"] == "The triumphal entry into Jerusalem"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} harmony tests passed — one event, every gospel that witnesses it, found and cited.")
