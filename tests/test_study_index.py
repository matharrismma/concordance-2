"""The quick-find index — one door into the whole reference section, and an honest one.

Matt, 2026-07-28: "We need a quick find index. focus added to the reference section, so you can
use the archetypes." Pinned here:

  * one query reaches EVERY shelf of the reference section — archetypes, storyboards, tables,
    atlas, harmony, timeline, encyclopedia — a shelf the index skips is a shelf that effectively
    does not exist for the person searching;
  * per-source caps hold, so the encyclopedia (3,962 entries) cannot drown the six-row table that
    actually answers the question;
  * every archetype hit carries Matt's framing VERBATIM — a quick find must not quietly become a
    quick label;
  * disputed places stay honest even in one-line snippets;
  * the gate holds, and agents get the same index.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import study_index  # noqa: E402


def _kinds(r):
    return {h["kind"] for h in r["hits"]}


def test_one_query_reaches_across_the_whole_reference_section():
    r = study_index.find("shepherd")
    ks = _kinds(r)
    assert "storyboard" in ks, "the shepherd-king storyboard must surface"
    assert any(k.startswith("table:") for k in ks), "the tables must surface (Names of God, the parable)"
    assert "encyclopedia" in ks
    r2 = study_index.find("jerusalem")
    assert "place" in _kinds(r2) and "timeline" in _kinds(r2)


def test_the_archetypes_are_reachable_and_framed():
    r = study_index.find("guilt")
    arch = [h for h in r["hits"] if h["kind"] == "archetype"]
    assert arch, "David after his sin must be findable from the word 'guilt'"
    for h in arch:
        assert "not saying you are that person" in h["framing"], \
            "every archetype hit carries the framing — a quick find must not become a quick label"
        assert h.get("refs"), "an archetype hit points at Scripture, not at itself"


def test_no_single_shelf_drowns_the_rest():
    r = study_index.find("god", limit=40)
    from collections import Counter
    per = Counter(h["kind"] for h in r["hits"])
    assert per.get("encyclopedia", 0) <= 8, \
        "the largest shelf must stay capped or the index becomes an Easton's search"


def test_disputed_places_stay_honest_in_one_line():
    r = study_index.find("sinai")
    pl = [h for h in r["hits"] if h["kind"] == "place"]
    assert pl and "disputed" in pl[0]["snippet"], \
        "even a snippet must not plant a flag the atlas refuses to plant"


def test_too_short_and_empty_queries_answer_gently():
    assert study_index.find("")["count"] == 0
    assert study_index.find("a")["count"] == 0


def test_the_gate_holds_and_agents_get_the_same_index():
    from concordance import mcp
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    st, body = dispatch("GET", "/study_find", {"q": "shepherd"}, None, EngineConfig("secular"))
    # SEEING, not understanding. Matt, 2026-07-31: "seeing them is fine — understanding
    # the deeper meaning comes after the gate" and "we don't need to refuse use, we refuse
    # abuse". The text and its reference apparatus answer on both surfaces now; only
    # exposition waits (api.AFTER_THE_GATE).
    assert st == 200 and body.get("gate") != "closed"   # finding is seeing
    st2, body2 = dispatch("GET", "/study_find", {"q": "shepherd"}, None, EngineConfig("witness"))
    assert st2 == 200 and body2["count"] > 0

    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "study_find", "arguments": {"q": "wilderness"}}},
                   EngineConfig("witness"), {})
    body = json.loads(r["result"]["content"][0]["text"])
    assert body["count"] > 0 and "characteristics have been displayed" in body["framing"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — one door, every shelf, nobody labeled.")
