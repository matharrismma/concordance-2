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


def test_for_ref_declines_a_non_string_ref_instead_of_crashing():
    # found: "ref or ''" only substitutes the fallback for a FALSY ref — a truthy non-string
    # (an int from an uncoerced MCP tool call arg) survived past that guard and crashed
    # re.match() ("expected string or bytes-like object"). Matches corpus.search()'s fix.
    for bad in (123, 45.6, ["a"], {"x": 1}):
        assert commentary.for_ref(bad)["status"] == "not_found"


def test_for_ref_resolves_singular_plural_alias():
    # "Psalm 23" must resolve even though the source book is "Psalms" (singular/plural nudge).
    assert commentary.for_ref("Psalm 23")["status"] == "ok"
    assert commentary.for_ref("Psalms 23:1")["status"] == "ok"


def test_commentary_endpoint_witness_gated():
    # 2026-07-31: knowledge is open on BOTH doors — "we don't hide knowledge, we aren't a
    # secret society". This asserted the tool was hidden from the secular surface; it now
    # asserts the parity that replaced it.
    assert dispatch("GET", "/commentary", {"ref": "John 3:16"}, None, SEC)[0] == 200
    assert dispatch("GET", "/commentary", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/commentary", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and p["status"] == "ok"


def test_source_is_validated_before_it_ever_reaches_a_filesystem_path():
    # found: for_ref()'s source param reached _dir()/source/... with ZERO validation, straight
    # from api.py's UNAUTHENTICATED GET /commentary?source= query param. Confirmed live: planting
    # a _books.json + chapter file OUTSIDE the commentary dir and pointing source at it via ".."
    # returned that file's content. Every traversal shape must be refused before touching disk.
    for bad in ("../../../etc", "../escaped", "a/b/c", "", "a" * 500, "UPPER", "has space"):
        assert commentary._valid_source(bad) is False, f"{bad!r} should not validate as a source"
    assert commentary._valid_source("matthew-henry") is True


def test_traversal_shaped_source_cannot_read_outside_the_commentary_dir():
    outside = Path(_TMP).parent / "nh-cmt-outside"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "_books.json").write_text(json.dumps(
        [{"code": "GEN", "name": "Genesis", "commonName": "Genesis", "chapters": 50}]), encoding="utf-8")
    (outside / "GEN").mkdir(exist_ok=True)
    (outside / "GEN" / "1.json").write_text(json.dumps(
        {"introduction": "LEAKED CONTENT", "blocks": []}), encoding="utf-8")

    rel = os.path.relpath(str(outside), str(Path(_TMP)))
    r = commentary.for_ref("Genesis 1", source=rel)
    assert r["status"] == "no_source", f"traversal source escaped the commentary dir: {r}"

    # the same traversal shape must be refused at the real, unauthenticated HTTP route too
    st, p = dispatch("GET", "/commentary", {"ref": "Genesis 1", "source": rel}, None, WIT)
    assert st == 200 and p["status"] == "no_source"


def test_mcp_commentary_tool():
    def names(cfg):
        r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, cfg)
        return {t["name"] for t in r["result"]["tools"]}
    # 2026-07-31: knowledge is open on BOTH doors — "we don't hide knowledge, we aren't a
    # secret society". This asserted the tool was hidden from the secular surface; it now
    # asserts the parity that replaced it.
    assert "commentary" in names(WIT) and "commentary" in names(SEC)
    r = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "commentary", "arguments": {"ref": "John 3:16"}}}, WIT)
    assert json.loads(r["result"]["content"][0]["text"])["status"] == "ok"


def test_the_registry_widened_to_clarke_and_gill_d5():
    """D5 (Matt, 2026-07-28): Clarke and Gill join Henry — same road (helloao), same registry,
    same cite-fair discipline. Metadata is registered unconditionally; the stores serve where
    the acquisition ran, and a machine without them skips honestly rather than passing silently."""
    from pathlib import Path
    import pytest as _pytest
    from concordance import commentary
    for s in ("adam-clarke", "john-gill"):
        assert s in commentary.SOURCE_META, f"{s} must be registered"
        meta = commentary.SOURCE_META[s]
        assert "Public Domain" in meta["license"] and meta["author"], f"{s}: attribution travels"
    root = Path(__file__).resolve().parent.parent / "data" / "commentary"
    if not (root / "adam-clarke" / "_books.json").exists():
        _pytest.skip("clarke store not migrated on this machine")
    import os as _os
    prior = _os.environ.get("CONCORDANCE_COMMENTARY_DIR")
    _os.environ["CONCORDANCE_COMMENTARY_DIR"] = str(root)   # the real store, not this file's fixture
    try:
        r = commentary.for_ref("John 3:16", source="adam-clarke")
        assert r.get("status") == "ok" and "Clarke" in (r.get("author") or "")
        ctext = " ".join(str(b.get("text") or "") for b in (r.get("commentary") or [])
                         if isinstance(b, dict))
        assert "loved the world" in ctext, "Clarke's own words on John 3:16 reach the caller"
        g = commentary.for_ref("John 3:16", source="john-gill")
        assert g.get("status") == "ok" and "Gill" in (g.get("author") or ""), \
            "Gill answers too — all 1,189 chapters migrated"
        gtext = " ".join(str(b.get("text") or "") for b in (g.get("commentary") or [])
                         if isinstance(b, dict))
        assert gtext.strip(), "Gill's words arrive, not an empty shell"
    finally:
        if prior is None:
            _os.environ.pop("CONCORDANCE_COMMENTARY_DIR", None)
        else:
            _os.environ["CONCORDANCE_COMMENTARY_DIR"] = prior


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} commentary B5 tests passed — the father's own words, found and attributed.")
