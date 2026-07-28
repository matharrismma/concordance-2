"""Back-matter reference tables — every ref real, every dispute carried, both planes served.

Contract §6 item 9: topical index, weights & measures, parables/miracles lists, book
introductions, names of God. What this file pins:

  * every scripture reference in every table resolves against the corpus (651 of them) — a table
    that points nowhere is worse than no table;
  * EVERY book of the 66 resolves — pinned because building these tables found a real engine bug:
    the core reader's book regex admitted no spaces, so "Song of Solomon" (the one space-bearing
    book with no leading digit) was unreachable through every passage surface, live. The satellites
    (commentary, xrefs, teachings) had the space-tolerant pattern; the CORE was the one left behind;
  * the disputes are PRESENT — a cubit with one length or a Revelation with one date would be the
    flattening this project refuses;
  * names of God carry Strong's numbers that resolve in the actual lexicon (the plumb-line, not our
    paraphrase);
  * the gate holds: witness content, closed on the secular surface until the Gate opens, and the
    agent tool mirrors the human page (parity of substance).

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import backmatter  # noqa: E402


def test_six_tables_none_empty_each_with_a_means():
    idx = backmatter.tables()
    keys = {t["key"] for t in idx["tables"]}
    assert keys == {"weights_measures", "names_of_god", "parables", "miracles",
                    "book_intros", "topical_index"}
    for t in idx["tables"]:
        assert t["count"] > 0, t["key"]
        assert t.get("means"), f"{t['key']} reports a count with no explanation of what it counts"


def test_every_reference_in_every_table_resolves():
    from concordance.verifiers.scripture import read_passage
    bad = [r for r in backmatter.all_refs() if read_passage(r).get("status") != "ok"]
    assert not bad, f"{len(bad)} reference(s) do not resolve: {bad[:8]}"


def test_all_66_books_are_reachable_through_the_core_reader():
    """The regression that found the bug: [A-Za-z.]+ admitted no spaces, so Song of Solomon was
    unreachable through /resolve, /original and every read_passage caller — live."""
    from concordance.verifiers.scripture import default_bible, read_passage
    books = sorted({k[0] for k in default_bible().idx.keys()})
    assert len(books) == 66
    unreachable = [b for b in books if read_passage(f"{b} 1:1").get("status") != "ok"]
    assert not unreachable, f"books the reader cannot reach: {unreachable}"
    # and the fix must not have loosened the old forms
    for ref in ("John 3:16", "John 3", "1 John 1:9", "John 3:16-18"):
        assert read_passage(ref).get("status") == "ok", ref


def test_the_disputes_are_carried_not_flattened():
    cubit = next(e for e in backmatter.WEIGHTS_MEASURES if e["name"] == "Cubit")
    assert "17.5" in cubit["equivalent"] and "20.6" in cubit["equivalent"], \
        "the cubit must carry BOTH systems"
    assert cubit.get("disputed")
    talent = next(e for e in backmatter.WEIGHTS_MEASURES if e["name"] == "Talent")
    assert talent.get("disputed")
    rev = next(e for e in backmatter.BOOK_INTROS if e["book"] == "Revelation")
    assert "95" in rev["date"] and "65" in rev["date"], "Revelation must carry both datings"
    dan = next(e for e in backmatter.BOOK_INTROS if e["book"] == "Daniel")
    assert "both" in dan["author"].lower(), "Daniel's dating debate must be named"
    heb = next(e for e in backmatter.BOOK_INTROS if e["book"] == "Hebrews")
    assert "unknown" in heb["author"].lower(), "Hebrews' authorship must stay honestly unknown"
    bart = next(e for e in backmatter.MIRACLES if "Bartimaeus" in e["name"])
    assert bart.get("note"), "the two-vs-one blind men difference is carried, not harmonised"


def test_names_of_god_resolve_in_the_actual_lexicon():
    from concordance import corpus
    cards = corpus.default_corpus().cards
    missing = [e["name"] for e in backmatter.NAMES_OF_GOD
               if e.get("strongs") and f"card_src_lex_{e['strongs'].lower()}" not in cards]
    assert not missing, f"names whose Strong's number has no lexicon entry: {missing}"


def test_book_intros_cover_all_66_in_canon_order():
    assert len(backmatter.BOOK_INTROS) == 66
    assert backmatter.BOOK_INTROS[0]["book"] == "Genesis"
    assert backmatter.BOOK_INTROS[38]["book"] == "Malachi", "39 OT books end at index 38"
    assert backmatter.BOOK_INTROS[39]["book"] == "Matthew"
    assert backmatter.BOOK_INTROS[65]["book"] == "Revelation"


def test_the_gate_holds_and_opens():
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    # The closed gate answers 404 marked gate:closed — deliberately NOT 401/403, so the room's
    # existence is never revealed to someone who has not sought it (fails closed, invites the ask).
    st, body = dispatch("GET", "/backmatter", {}, None, EngineConfig("secular"))
    assert st == 404 and body.get("gate") == "closed", \
        "the tables must live behind the Gate on the secular surface"
    st2, body2 = dispatch("GET", "/backmatter", {}, None, EngineConfig("witness"))
    assert st2 == 200 and len(body2["tables"]) == 6
    st3, body3 = dispatch("GET", "/backmatter", {"table": "names_of_god"}, None, EngineConfig("witness"))
    assert st3 == 200 and body3["count"] == len(backmatter.NAMES_OF_GOD)
    st4, _ = dispatch("GET", "/backmatter", {"table": "no_such"}, None, EngineConfig("witness"))
    assert st4 == 404


def test_agents_get_the_same_tables_humans_do():
    """Parity of substance: the page a human reads is a tool an agent can call."""
    from concordance import mcp
    from concordance.config import EngineConfig
    wit = EngineConfig("witness")
    names = {t["name"] for t in mcp.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, wit, {})["result"]["tools"]}
    assert "backmatter" in names
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "backmatter", "arguments": {"table": "parables"}}}, wit, {})
    body = json.loads(r["result"]["content"][0]["text"])
    assert body["count"] == len(backmatter.PARABLES)
    # and on the secular surface without the gate open, the tool is not listed
    sec_names = {t["name"] for t in mcp.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, EngineConfig("secular"), {})["result"]["tools"]}
    assert "backmatter" not in sec_names, "witness tool leaked onto the closed secular surface"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the back of the book is served whole.")
