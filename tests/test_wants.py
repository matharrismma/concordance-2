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


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
