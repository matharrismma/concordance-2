"""B6a — editorial cross-references (openbible.info, CC-BY expansion of the public-domain TSK).

Proves xrefs.for_ref (ranked by votes, attributed, book aliasing), the witness-gated /tsk endpoint,
and the MCP tool. Hermetic: a fixture SQLite store, no network. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
_TMP = tempfile.mkdtemp(prefix="nh-xref-")
os.environ["CONCORDANCE_XREFS_DIR"] = _TMP
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-xref-data-")

from concordance import xrefs, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")

# fixture: John 3:16 (43,3,16) -> Romans 5:8 (votes 50), 1 John 4:9 (votes 40), Romans 8:32 (votes 30)
_db = Path(_TMP) / "xrefs.db"
_con = sqlite3.connect(str(_db))
_con.execute("CREATE TABLE cross_refs (from_book INT, from_chapter INT, from_verse INT, "
             "to_book INT, to_chapter INT, to_verse_start INT, to_verse_end INT, votes INT)")
_con.execute("CREATE TABLE meta (k TEXT, v TEXT)")
_con.executemany("INSERT INTO cross_refs VALUES (?,?,?,?,?,?,?,?)", [
    (43, 3, 16, 45, 5, 8, 8, 50), (43, 3, 16, 62, 4, 9, 9, 40), (43, 3, 16, 45, 8, 32, 32, 30)])
_con.execute("CREATE INDEX idx_from ON cross_refs(from_book,from_chapter,from_verse)")
_con.commit()
_con.close()


def test_for_ref_ranked_by_votes_and_attributed():
    r = xrefs.for_ref("John 3:16")
    assert r["status"] == "ok" and r["count"] == 3
    assert r["cross_references"][0]["ref"] == "Romans 5:8" and r["cross_references"][0]["votes"] == 50
    assert "CC BY" in r["license"] and "openbible" in r["attribution"].lower()


def test_book_aliases_resolve():
    assert xrefs._resolve_book("John") == 43
    assert xrefs._resolve_book("Jn") == 43
    assert xrefs._resolve_book("Psalm") == 19 and xrefs._resolve_book("Psalms") == 19


def test_bad_ref_and_unknown_book():
    assert xrefs.for_ref("garbage")["status"] == "not_found"
    assert xrefs.for_ref("Zzz 1:1")["status"] == "not_found"


def test_endpoint_witness_gated():
    assert dispatch("GET", "/tsk", {"ref": "John 3:16"}, None, SEC)[0] == 404
    assert dispatch("GET", "/tsk", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/tsk", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and p["status"] == "ok" and p["count"] == 3


def test_mcp_tsk_tool():
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, WIT)
    assert "tsk_cross_references" in {t["name"] for t in r["result"]["tools"]}
    assert "tsk_cross_references" not in {t["name"] for t in
                                         mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)["result"]["tools"]}
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "tsk_cross_references", "arguments": {"ref": "John 3:16"}}}, WIT)
    assert json.loads(c["result"]["content"][0]["text"])["count"] == 3


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} xrefs B6a tests passed — Scripture cross-referenced with Scripture, attributed.")
