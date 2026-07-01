"""B6c — prophecy / Christ-signpost traces (ported from 1.0 signposts).

Proves: traces load, verdicts are NEVER HOLDS (a signpost, not a proof), refs extract, keyword
extraction tolerates both triggers schemas (dict and list), the witness-gated /prophecy endpoint,
and the MCP tool. Hermetic fixture. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
_TMP = tempfile.mkdtemp(prefix="nh-proph-")
os.environ["CONCORDANCE_PROPHECY_DIR"] = _TMP
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-proph-data-")

(Path(_TMP) / "signposts.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
    {"id": "signpost_isaiah", "title": "Isaiah 53", "verdict": "CONCORDANT",
     "verification": "See Isaiah 53:5 and John 1:29.", "wisdom": "Points to Christ, the Lamb (John 1:29).",
     "triggers": {"keywords": ["Isaiah 53", "Suffering Servant"]}},
    {"id": "signpost_islam", "title": "Islamic Christology", "verdict": "MIXED",
     "verification": "Q 4:171 etc.", "wisdom": "Christ exalted yet denied.",
     "triggers": ["Islam", "Isa"]},   # triggers as a LIST — must not crash
]), encoding="utf-8")

from concordance import prophecy, mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def test_list_and_verdicts_never_holds():
    l = prophecy.list_traces()
    assert l["total"] == 2
    assert all(t["verdict"] != "HOLDS" for t in l["traces"])   # a signpost, never a proof
    assert "signpost" in l["note"].lower()


def test_get_extracts_refs_and_tolerates_list_triggers():
    g = prophecy.get("signpost_isaiah")
    assert g and g["verdict"] == "CONCORDANT"
    assert "Isaiah 53:5" in g["scripture_refs"] and "John 1:29" in g["scripture_refs"]
    assert "Isaiah 53" in g["keywords"]
    g2 = prophecy.get("signpost_islam")   # list-form triggers
    assert g2["keywords"] == ["Islam", "Isa"]


def test_search():
    assert any(t["id"] == "signpost_islam" for t in prophecy.search("islam")["traces"])


def test_endpoints_witness_gated():
    assert dispatch("GET", "/prophecy", {}, None, SEC)[0] == 404
    st, p = dispatch("GET", "/prophecy", {}, None, WIT)
    assert st == 200 and p["total"] == 2
    st2, g = dispatch("GET", "/prophecy", {"id": "signpost_isaiah"}, None, WIT)
    assert st2 == 200 and g["verdict"] == "CONCORDANT"
    assert dispatch("GET", "/prophecy", {"id": "nope"}, None, WIT)[0] == 404


def test_mcp_prophecy_tool():
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, WIT)
    assert "prophecy_traces" in {t["name"] for t in r["result"]["tools"]}
    c = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "prophecy_traces", "arguments": {"id": "signpost_isaiah"}}}, WIT)
    assert json.loads(c["result"]["content"][0]["text"])["verdict"] == "CONCORDANT"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} prophecy B6c tests passed — signposts point to Christ; never a proof, always attributed.")
