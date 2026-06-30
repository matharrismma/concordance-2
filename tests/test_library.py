"""Library / keeping tools ported into 2.0 — over the shared corpus, additively.

Proves card_get / cards_browse / cards_stats / daily_card at the corpus, HTTP, and MCP layers.
Uses an injected in-memory corpus so it needs no data files. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import corpus  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
_CARDS = {
    "c1": {"id": "c1", "title": "Grace", "shelf": "theology", "surface": "witness", "body": "unmerited favor"},
    "c2": {"id": "c2", "title": "Justice", "shelf": "ethics", "surface": "secular", "body": "to each their due"},
    "c3": {"id": "c3", "title": "Atom", "shelf": "science", "surface": "secular", "body": "smallest unit"},
}


def _inject():
    corpus._DEFAULT = corpus.Corpus(dict(_CARDS))


def test_get_card():
    _inject()
    assert corpus.get_card("c1")["title"] == "Grace"
    assert corpus.get_card("nope") is None


def test_browse_paginates_and_filters():
    _inject()
    r = corpus.browse(limit=2, offset=0)
    assert r["total"] == 3 and len(r["cards"]) == 2
    only_sci = corpus.browse(shelf="science")
    assert only_sci["total"] == 1 and only_sci["cards"][0]["id"] == "c3"


def test_stats():
    _inject()
    s = corpus.stats()
    assert s["total"] == 3 and s["by_surface"]["secular"] == 2 and s["by_shelf"]["theology"] == 1


def test_daily_is_deterministic_per_seed():
    _inject()
    assert corpus.daily("2026-06-28")["id"] == corpus.daily("2026-06-28")["id"]
    assert corpus.daily("2026-06-29")["id"] in _CARDS


def test_http_endpoints():
    _inject()
    from concordance.web.api import dispatch
    assert dispatch("GET", "/card", {"id": "c2"}, None, SEC)[1]["title"] == "Justice"
    assert dispatch("GET", "/card", {"id": "x"}, None, SEC)[0] == 404
    assert len(dispatch("GET", "/cards", {"limit": "2"}, None, SEC)[1]["cards"]) == 2
    assert dispatch("GET", "/cards/stats", {}, None, SEC)[1]["total"] == 3
    assert dispatch("GET", "/daily", {}, None, SEC)[1]["id"] in _CARDS


def test_mcp_tools():
    _inject()
    from concordance.mcp.server import handle
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "cards_stats", "arguments": {}}}, SEC)
    assert json.loads(r["result"]["content"][0]["text"])["total"] == 3
    names = [t["name"] for t in handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)["result"]["tools"]]
    assert {"card_get", "cards_browse", "cards_stats", "daily_card"} <= set(names)


def test_cleanup():
    corpus._DEFAULT = None  # don't leak the injected corpus to other test modules


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} library tests passed — card_get/browse/stats/daily across corpus+HTTP+MCP.")
