"""Arc 2 (the Bible) B3 — cross-references by shared original words + word occurrences.

Proves the Concordance logic (deterministic, ranked by shared Strong's) via an injected in-memory
fixture (no dependency on the 360k-row real DB), the witness-gated endpoints, and the new MCP tools.
Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-xref-")

from concordance.strongs import Concordance  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402
from concordance import mcp  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def _conc_with_fixture() -> Concordance:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE concordance (b INTEGER,c INTEGER,v INTEGER,word_pos INTEGER,word TEXT,strongs TEXT)")
    conn.executemany("INSERT INTO concordance VALUES (?,?,?,?,?,?)", [
        (43, 3, 16, 1, "loved", "G26"), (43, 3, 16, 2, "God", "G2316"), (43, 3, 16, 3, "world", "G2889"),
        (43, 3, 17, 1, "God", "G2316"), (43, 3, 17, 2, "world", "G2889"),
        (62, 4, 8, 1, "love", "G26"), (62, 4, 8, 2, "God", "G2316"),
    ])
    conn.commit()
    web = sqlite3.connect(":memory:")
    web.execute("CREATE TABLE t_web (b INTEGER,c INTEGER,v INTEGER,t TEXT)")
    c = Concordance()
    c._conc = conn  # inject — bypass ROOT/real DB for a hermetic, deterministic test
    c._web = web
    return c


def test_verse_strongs_in_word_order():
    assert _conc_with_fixture().verse_strongs(43, 3, 16) == ["G26", "G2316", "G2889"]


def test_word_occurrences_counts_all_verses():
    r = _conc_with_fixture().word_occurrences("G2316")
    assert r["status"] == "ok" and r["occurrence_count"] == 3


def test_cross_references_ranks_by_shared_words():
    r = _conc_with_fixture().cross_references("John 3:16")
    assert r["status"] == "ok" and r["source_strongs"] == ["G26", "G2316", "G2889"]
    xr = r["cross_references"]
    assert xr[0]["ref"] == "John 3:17" and xr[0]["shared_count"] == 2   # most shared words first
    assert "1 John 4:8" in [x["ref"] for x in xr]
    assert all(x["ref"] != "John 3:16" for x in xr)                     # source verse excluded


def test_cross_references_bad_ref():
    assert _conc_with_fixture().cross_references("nonsense")["status"] == "not_found"


def test_endpoints_witness_gated():
    assert dispatch("GET", "/cross_refs", {"ref": "John 3:16"}, None, SEC)[0] == 404
    assert dispatch("GET", "/cross_refs", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/cross_refs", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and "status" in p
    assert dispatch("GET", "/word_occurrences", {"strongs": "G26"}, None, SEC)[0] == 404
    assert dispatch("GET", "/word_occurrences", {}, None, WIT)[0] == 400


def test_mcp_lists_and_calls_new_tools():
    def names(cfg):
        r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, cfg)
        return {t["name"] for t in r["result"]["tools"]}
    wit = names(WIT)
    assert {"read_passage", "cross_references", "word_occurrences", "pronounce"} <= wit
    sec = names(SEC)
    assert "pronounce" in sec and "cross_references" not in sec   # witness tool hidden on secular
    r = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "pronounce", "arguments": {"text": "agape"}}}, SEC)
    payload = json.loads(r["result"]["content"][0]["text"])
    assert payload["respelling"] == "a-ga-pe" and payload["synthesized"] is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} cross-reference B3 tests passed — the dots connect through the original words.")
