"""Arc 2 (the Bible) B5 — public-domain, attributed commentary (Matthew Henry).

Proves parse_chapter (the migrator's pure parser), for_ref (verse-covering block / whole chapter /
graceful when unmigrated), the witness-gated /commentary endpoint, and the MCP tool. Hermetic: a
fixture store on disk, no network. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
_TMP = tempfile.mkdtemp(prefix="nh-cmt-")
os.environ["CONCORDANCE_COMMENTARY_DIR"] = _TMP
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-cmt-data-")

from concordance import commentary  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402
from concordance import mcp  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")

# ── fixture store ────────────────────────────────────────────────────
_src = Path(_TMP) / "matthew-henry"
(_src / "JHN").mkdir(parents=True, exist_ok=True)
(_src / "PSA").mkdir(parents=True, exist_ok=True)
(_src / "_books.json").write_text(json.dumps([
    {"code": "JHN", "name": "John", "commonName": "John", "chapters": 21},
    {"code": "PSA", "name": "Psalms", "commonName": "Psalms", "chapters": 150},
]), encoding="utf-8")
(_src / "PSA" / "23.json").write_text(json.dumps({
    "source": "matthew-henry", "book_code": "PSA", "book": "Psalms", "chapter": 23,
    "introduction": "The Lord is my shepherd.",
    "blocks": [{"verse": 1, "text": "David's confidence in God's grace."}],
}), encoding="utf-8")
(_src / "JHN" / "3.json").write_text(json.dumps({
    "source": "matthew-henry", "book_code": "JHN", "book": "John", "chapter": 3,
    "introduction": "Exposition of John 3.",
    "blocks": [{"verse": 1, "text": "On Nicodemus coming by night."},
               {"verse": 16, "text": "For God so loved the world — the love of God is the fountain."}],
}), encoding="utf-8")


def test_parse_chapter_extracts_intro_and_verse_blocks():
    obj = {"introduction": "Intro.", "content": [
        {"type": "verse", "number": 1, "content": ["a", "b"]},
        {"type": "heading", "number": 0, "content": ["skip me"]},
        {"type": "verse", "number": 16, "content": ["For God so loved"]},
    ]}
    p = commentary.parse_chapter(obj)
    assert p["introduction"] == "Intro."
    assert [b["verse"] for b in p["blocks"]] == [1, 16]   # non-verse items dropped
    assert p["blocks"][0]["text"] == "a\n\nb"


def test_for_ref_verse_returns_covering_block_attributed():
    r = commentary.for_ref("John 3:16")
    assert r["status"] == "ok" and r["verse"] == 16
    assert len(r["commentary"]) == 1 and "fountain" in r["commentary"][0]["text"]
    assert "Matthew Henry" in r["attribution"] and "Public Domain" in r["license"]


def test_for_ref_verse_between_blocks_uses_earlier_block():
    r = commentary.for_ref("John 3:10")   # falls under the block that starts at v1
    assert r["status"] == "ok" and r["commentary"][0]["verse"] == 1


def test_for_ref_whole_chapter():
    r = commentary.for_ref("John 3")
    assert r["status"] == "ok" and r["introduction"] == "Exposition of John 3."
    assert len(r["commentary"]) == 2


def test_for_ref_unmigrated_and_bad():
    assert commentary.for_ref("John 99")["status"] == "no_source"   # chapter not migrated
    assert commentary.for_ref("Zzz 1")["status"] == "no_source"     # unknown book
    assert commentary.for_ref("garbage")["status"] == "not_found"   # unparseable


def test_for_ref_resolves_singular_plural_alias():
    # "Psalm 23" must resolve even though the source book is "Psalms" (singular/plural nudge).
    assert commentary.for_ref("Psalm 23")["status"] == "ok"
    assert commentary.for_ref("Psalms 23:1")["status"] == "ok"


def test_commentary_endpoint_witness_gated():
    assert dispatch("GET", "/commentary", {"ref": "John 3:16"}, None, SEC)[0] == 404
    assert dispatch("GET", "/commentary", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/commentary", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and p["status"] == "ok"


def test_mcp_commentary_tool():
    def names(cfg):
        r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, cfg)
        return {t["name"] for t in r["result"]["tools"]}
    assert "commentary" in names(WIT) and "commentary" not in names(SEC)
    r = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "commentary", "arguments": {"ref": "John 3:16"}}}, WIT)
    assert json.loads(r["result"]["content"][0]["text"])["status"] == "ok"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} commentary B5 tests passed — the father's own words, found and attributed.")
