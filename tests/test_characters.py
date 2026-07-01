"""B6b — character charts / Bible dictionary (Easton's 1897, PD; ported from 1.0).

Proves lookup resolves EVERY figure regardless of the parse's imperfect category tag (Moses is
tagged 'concept' but must still resolve), browse, the witness-gated endpoints, and the MCP tools.
Hermetic: a fixture store. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
_TMP = tempfile.mkdtemp(prefix="nh-char-")
os.environ["CONCORDANCE_CHARACTERS_DIR"] = _TMP
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-char-data-")

(Path(_TMP) / "easton.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
    {"id": "easton_moses", "name": "Moses", "category": "concept",  # mis-tagged in the 1.0 parse
     "text": "The great lawgiver. Drawn from the water.", "scripture_refs": ["Exodus 2:10", "Deuteronomy 34:5"]},
    {"id": "easton_david", "name": "David", "category": "person",
     "text": "The shepherd king of Israel.", "scripture_refs": ["1 Samuel 16:13"]},
    {"id": "easton_bethlehem", "name": "Bethlehem", "category": "place",
     "text": "House of bread.", "scripture_refs": ["Micah 5:2"]},
]), encoding="utf-8")

from concordance import characters, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def test_get_resolves_despite_imperfect_category():
    m = characters.get("Moses")
    assert m and m["category"] == "concept" and m["ref_count"] == 2   # resolves though mis-tagged
    assert m["name"] == "Moses" and "lawgiver" in m["text"]
    assert characters.get("David")["category"] == "person"


def test_get_by_slug_and_missing():
    assert characters.get("bethlehem")["name"] == "Bethlehem"
    assert characters.get("Nonesuch") is None


def test_browse_letter_and_search():
    assert any(i["name"] == "David" for i in characters.browse(letter="D")["items"])
    assert any(i["name"] == "Bethlehem" for i in characters.browse(search="bread")["items"])


def test_endpoints_witness_gated():
    assert dispatch("GET", "/character", {"name": "Moses"}, None, SEC)[0] == 404
    assert dispatch("GET", "/character", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/character", {"name": "Moses"}, None, WIT)
    assert st == 200 and p["ref_count"] == 2
    assert dispatch("GET", "/character", {"name": "Nonesuch"}, None, WIT)[0] == 404
    st2, b = dispatch("GET", "/characters", {"letter": "D"}, None, WIT)
    assert st2 == 200 and any(i["name"] == "David" for i in b["items"])


def test_mcp_tools():
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, WIT)
    names = {t["name"] for t in r["result"]["tools"]}
    assert {"character_get", "characters_browse"} <= names
    assert "character_get" not in {t["name"] for t in
                                   mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)["result"]["tools"]}
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "character_get", "arguments": {"name": "Moses"}}}, WIT)
    assert json.loads(c["result"]["content"][0]["text"])["ref_count"] == 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} character B6b tests passed — every figure resolves, imperfect tags and all.")
