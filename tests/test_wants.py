"""THE WANT LIST — the queen is dumb, and these tests prove she is dumb in the right ways.

Matt, 2026-08-01: the hive of specialists coming back to a queen; each one dumb, crafted for its
task; miners with maps, filtration, canaries, and branches that can be cut; healing always from
source to source. What this file pins is the QUEEN's side of that covenant:

  * a want opens only on an explicit ask, and the same miss asked twice is ONE want asked twice;
  * queries and notes pass the scrub BEFORE storage, and no requester identity is ever written;
  * an option is a found, attributed source in a ledger cell — quarantine by construction — and
    it carries its shaft-tags (miner, run) so a poisoned branch can be cut by query;
  * nothing closes without a NAME and the card it produced;
  * the wire works: POST /want and GET /wants through the real dispatch.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_ledger(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    yield


def test_the_same_miss_is_one_want_asked_twice():
    from concordance import wants
    a = wants.open_want(query="the history of the printing press")
    b = wants.open_want(query="  The HISTORY of the printing-press!! ")
    assert a["ok"] and b["ok"]
    assert a["id"] == b["id"], "normalization failed — two cells for one miss"
    assert b["asks"] == 2
    assert wants.fold()[a["id"]]["asks"] == 2


def test_a_want_needs_words():
    from concordance import wants
    assert not wants.open_want(query="ab")["ok"]
    assert not wants.open_want(query="")["ok"]
    assert not wants.open_want(query="x", kind="nonsense")["ok"]


def test_the_scrub_runs_before_storage_and_no_identity_is_written(monkeypatch):
    from concordance import gateway, wants
    monkeypatch.setattr(gateway, "scrub", lambda t: ("[SCRUBBED]" + t, {}))
    r = wants.open_want(query="find me the coal mining safety manual")
    assert r["ok"]
    raw = (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "wants.jsonl").read_text(encoding="utf-8")
    ev = json.loads(raw.strip().splitlines()[0])
    assert ev["query"].startswith("[SCRUBBED]"), "the query reached disk unscrubbed"
    assert not {"ip", "addr", "user", "session", "agent"} & set(ev), \
        "a want recorded something about the PERSON — it may only record the library's gap"


def test_expand_requires_a_real_card():
    from concordance import corpus, wants
    old = corpus._DEFAULT
    corpus._DEFAULT = corpus.Corpus({"c1": {"id": "c1", "title": "T", "shelf": "s",
                                            "surface": "secular", "body": "b"}})
    try:
        assert not wants.open_want(kind="expand", card_id="")["ok"]
        assert not wants.open_want(kind="expand", card_id="ghost")["ok"]
        r = wants.open_want(kind="expand", card_id="c1")
        assert r["ok"] and wants.fold()[r["id"]]["kind"] == "expand"
    finally:
        corpus._DEFAULT = old


def test_options_are_quarantined_cells_with_shaft_tags():
    from concordance import wants
    w = wants.open_want(query="public domain field surgery manual")
    assert not wants.add_option("want_nope", {"label": "x"})["ok"]
    assert not wants.add_option(w["id"], {"label": ""})["ok"], "an option names its source"
    assert not wants.add_option(w["id"], {"label": "x", "url": "javascript:alert(1)"})["ok"]
    r = wants.add_option(w["id"], {"label": "FM 21-76 Survival", "url": "https://example.org/fm",
                                   "snippet": "the field manual", "domain": "example.org",
                                   "miner": "tortoise", "run": "run_test_1"})
    assert r["ok"]
    cell = wants.fold()[w["id"]]["options"][0]
    assert cell["miner"] == "tortoise" and cell["run"] == "run_test_1", \
        "the shaft-tags are missing — a poisoned branch could not be cut by query"
    assert wants.fold()[w["id"]]["state"] == "options_ready"


def test_the_cell_holds_a_few_not_a_results_page():
    from concordance import wants
    w = wants.open_want(query="the letters of pliny the younger")
    for i in range(wants._MAX_OPTIONS):
        assert wants.add_option(w["id"], {"label": f"src {i}"})["ok"]
    assert not wants.add_option(w["id"], {"label": "one too many"})["ok"]


def test_closing_carries_a_name_and_the_card_it_produced():
    from concordance import wants
    w = wants.open_want(query="a chosen thing")
    assert not wants.close_want(w["id"], "card_x", "")["ok"], "no anonymous minting"
    assert not wants.close_want(w["id"], "", "Matt")["ok"], "a close names its card"
    assert wants.close_want(w["id"], "card_x", "Matt")["ok"]
    assert wants.fold()[w["id"]]["state"] == "closed"
    assert not wants.close_want(w["id"], "card_y", "Matt")["ok"], "closed is closed"


def test_the_listing_is_steered_by_demand():
    from concordance import wants
    a = wants.open_want(query="asked once only")
    b = wants.open_want(query="asked three times")
    wants.open_want(query="asked three times"); wants.open_want(query="asked THREE times")
    ws = wants.listing()["wants"]
    assert ws[0]["id"] == b["id"] and ws[0]["asks"] == 3, "demand steers acquisition"
    assert {w["id"] for w in ws} >= {a["id"], b["id"]}


def test_the_wire_works():
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    sec = EngineConfig("secular")
    st, body = dispatch("POST", "/want", {}, {"kind": "missing", "query": "the wire test want"}, sec)
    assert st == 200 and body["ok"], body
    st2, body2 = dispatch("GET", "/wants", {}, None, sec)
    assert st2 == 200 and body2["total"] >= 1
    assert any(w["query"] == "the wire test want" for w in body2["wants"])
    st3, _ = dispatch("POST", "/want", {}, {"kind": "missing", "query": "x"}, sec)
    assert st3 == 400, "a wordless want must be refused on the wire too"


def test_the_agent_plane_stays_separate_until_the_next_human_seconds():
    """Matt: "that plane stays separate and must be approved by a human. We ask the next human
    that looks at it." An agent's want is held apart on the desk; the NEXT HUMAN asking for the
    same thing seconds it onto the human plane — ambient approval, no queue, no path around."""
    from concordance import wants
    a = wants.open_want(query="the antikythera mechanism papers", plane="agent")
    assert a["ok"] and a["plane"] == "agent"
    desk_human = wants.listing(plane="human")["wants"]
    assert not any(w["id"] == a["id"] for w in desk_human), "an agent want leaked onto the human desk"
    assert any(w["id"] == a["id"] for w in wants.listing(plane="agent")["wants"])
    # the next human looks, and asks for the same thing
    b = wants.open_want(query="The Antikythera Mechanism papers!", plane="human")
    assert b["id"] == a["id"] and b.get("seconded_agent_want") is True
    w = wants.fold()[a["id"]]
    assert w["plane"] == "human" and w["asks"] == 2, "the seconding did not promote the plane"
    # a second agent asking does NOT promote — only a human's look counts
    c = wants.open_want(query="the venerable bede's reckoning of time", plane="agent")
    d = wants.open_want(query="the venerable bede's reckoning of time", plane="agent")
    assert d["id"] == c["id"] and wants.fold()[c["id"]]["plane"] == "agent"
    assert not wants.open_want(query="anything at all", plane="martian")["ok"]


def test_the_agent_tools_work_over_mcp_and_the_gate_holds():
    """The three tools on the wire — and the covenant in their behavior: want_open lands on the
    agent plane, want_offer lands quarantined with the agent's shaft-tag, and nothing here can
    mint a card."""
    import json
    from concordance import mcp, wants
    from concordance.config import EngineConfig
    sec = EngineConfig("secular")

    def call(name, arguments):
        r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": name, "arguments": arguments}}, sec, {})
        return json.loads(r["result"]["content"][0]["text"])

    o = call("want_open", {"query": "the mcp plane test want"})
    assert o["ok"] and o["plane"] == "agent"
    lst = call("wants_list", {"plane": "agent"})
    assert any(w["id"] == o["id"] for w in lst["wants"])
    off = call("want_offer", {"want_id": o["id"], "label": "A PD source", "url": "https://example.org/pd",
                              "snippet": "found, not written", "agent": "claude"})
    assert off["ok"]
    cell = wants.fold()[o["id"]]["options"][0]
    assert cell["miner"] == "agent:claude", "the agent's shaft-tag is missing"
    from concordance import corpus
    assert corpus.get_card("card_acq_" + o["id"].removeprefix("want_") + "_1") is None,         "an MCP offer produced a card without a human choosing — the comb was bypassed"


# ── PRESSURE TEST FINDINGS, 2026-08-01 — each of these was a real defect, found by pressure ──

def test_an_over_long_ask_is_refused_not_silently_truncated():
    """8,000 characters used to be cut to 300 and stored as if the person had written that.
    Storing something they did not say and calling it their want is a small lie; the honest
    answer names the limit."""
    from concordance import wants
    r = wants.open_want(query="A" * 8000)
    assert not r["ok"] and "300" in r["error"]
    assert not wants.open_want(query="a fine ask", note="N" * 900)["ok"]
    assert wants.open_want(query="A" * 300)["ok"], "exactly at the limit must still pass"


def test_concurrent_asks_for_one_miss_are_all_counted():
    """40 concurrent asks were recorded as 32: two threads both saw "no such want", both
    appended an open, and the second open RESET the count. Demand steers acquisition, so a lost
    ask is a lost vote. Fixed twice over — the decision is atomic now, AND the fold treats a
    double-open as an ask so ledgers already written this way heal themselves."""
    import threading
    from concordance import wants
    def ask(_):
        wants.open_want(query="the one contested want")
    ts = [threading.Thread(target=ask, args=(i,)) for i in range(40)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    cells = [w for w in wants.fold().values() if w["query"] == "the one contested want"]
    assert len(cells) == 1, f"{len(cells)} cells for one miss"
    assert cells[0]["asks"] == 40, f"lost {40 - cells[0]['asks']} ask(s) to the race"


def test_the_fold_heals_a_ledger_that_already_has_double_opens():
    """The self-healing half: an old ledger written before the lock still folds correctly,
    because the events are the source and the fold reads them honestly."""
    import json
    import time
    from concordance import wants
    p = wants._path()
    p.parent.mkdir(parents=True, exist_ok=True)
    wid = wants._want_id("missing", "an old racy want")
    with open(p, "a", encoding="utf-8") as fh:
        for _ in range(3):     # three opens for one id — the shape the race produced
            fh.write(json.dumps({"ev": "open", "id": wid, "kind": "missing",
                                 "query": "an old racy want", "card_id": "", "note": "",
                                 "plane": "human", "at": int(time.time())}) + "\n")
    w = wants.fold()[wid]
    assert w["asks"] == 3, "the fold discarded asks from a double-open ledger"


def test_a_500_leaves_a_trace_for_the_operator_and_nothing_for_the_caller():
    """/wants answered 500 on one process while the identical code served 200 on the other, and
    the log said NOTHING — a restart healed it and took the evidence with it. The caller still
    learns only 'internal error'; the operator now gets the path and the traceback."""
    src = (ROOT / "src" / "concordance" / "web" / "api.py").read_text(encoding="utf-8")
    assert '"[500] "' in src, "the catch-all still swallows the failure"
    assert "_tb.format_exc()" in src and "_sys.stderr" in src
    i = src.index('"[500] "')
    tail = src[i:i + 400]
    assert "self._json(500, {\"error\": \"internal error\"})" in tail,         "the caller must still learn nothing beyond 'internal error'"


def test_the_desk_shows_what_is_still_wanted():
    """A refused want sat on the live desiderata desk beside the live ones, minutes after `drop`
    shipped — the drop recorded perfectly and the DESK was the liar. Resolved wants are not
    hidden, only one explicit state= away, with the reason and the name attached."""
    from concordance import wants
    live = wants.open_want(query="a want still wanted")
    gone = wants.open_want(query="a want a steward refused")
    done = wants.open_want(query="a want already filled")
    wants.drop_want(gone["id"], "not something this library should hold", "Matt Harris")
    wants.close_want(done["id"], "card_made", "Matt Harris")

    desk = {w["id"] for w in wants.listing()["wants"]}
    assert live["id"] in desk
    assert gone["id"] not in desk, "a refused want is still on the desk"
    assert done["id"] not in desk, "a filled want is still on the desk"

    # and nothing is hidden — asking names it, with the record intact
    dropped = wants.listing(state="dropped")["wants"]
    assert [w["id"] for w in dropped] == [gone["id"]]
    assert dropped[0]["reason"] == "not something this library should hold"
    assert dropped[0]["closed_by"] == "Matt Harris"
    assert [w["id"] for w in wants.listing(state="closed")["wants"]] == [done["id"]]


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
