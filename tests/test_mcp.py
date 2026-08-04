"""MCP server test — the agent surface (pure JSON-RPC handler, no stdio needed).

Proves: initialize handshake; tools/list is the SAME on both surfaces (2026-07-31);
tools/call runs verify (HOLDS/BROKEN) over MCP; the surfaces differ in voice, not in the
surface; notifications get no response; unknown methods error. Runnable with `pytest` OR
`python tests/test_mcp.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp import handle  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def _call(method, params=None, rid=1, config=SEC):
    return handle({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}, config)


def test_initialize():
    r = _call("initialize")
    assert r["result"]["serverInfo"]["name"] == "narrow-highway"
    assert r["result"]["protocolVersion"]


def test_tools_list_is_surface_gated():
    sec = [t["name"] for t in _call("tools/list", config=SEC)["result"]["tools"]]
    wit = [t["name"] for t in _call("tools/list", config=WIT)["result"]["tools"]]
    assert {"verify", "search", "seal_fetch"} <= set(sec)
    # 2026-07-31: the list is no longer SURFACE-GATED — it is the same list. The surfaces differ
    # in voice (how a reader is met), never in what they will show. Twenty tools sat invisible to
    # every agent on .com until this changed.
    assert "word_study" in sec and "resolve" in sec
    assert set(sec) == set(wit), "the two doors drifted apart"


def test_tools_call_verify():
    ok = _call("tools/call", {"name": "verify",
                              "arguments": {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}})
    assert not ok["result"]["isError"]
    assert json.loads(ok["result"]["content"][0]["text"])["verdict"] == "HOLDS"
    bad = _call("tools/call", {"name": "verify",
                               "arguments": {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "5", "variables": {}}}})
    assert json.loads(bad["result"]["content"][0]["text"])["verdict"] == "BROKEN"


def test_witness_tool_gated_off_secular():
    r = _call("tools/call", {"name": "word_study", "arguments": {"strongs": "G26"}}, config=SEC)
    # 2026-07-31: knowledge is open on BOTH doors — "we don't hide knowledge, we aren't a
    # secret society". This asserted the tool was hidden from the secular surface; it now
    # asserts the parity that replaced it.
    assert "error" not in r, "an agent on the secular surface was refused knowledge"
    # on witness it is reachable (a result, not the gating error) — regardless of data state
    rw = _call("tools/call", {"name": "word_study", "arguments": {"strongs": "G26"}}, config=WIT)
    assert "result" in rw and isinstance(json.loads(rw["result"]["content"][0]["text"]), dict)


def test_notification_gets_no_response():
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, SEC) is None


def test_unknown_method_errors():
    assert _call("nope")["error"]["code"] == -32601


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} MCP tests passed — the agent surface speaks JSON-RPC, surface-gated, sovereign.")


def test_protocol_version_is_negotiated_not_dictated():
    """REGRESSION, from a production outage (2026-08-04). The server answered every client with
    a hardcoded 2024-11-05, so modern connectors fell back to old-transport expectations (a GET
    server stream this endpoint 405s by design) and flapped. The wire was fine; the negotiation
    was the outage. The independent MCP assessment named it (F-03) the same day it bit."""
    from concordance.mcp.server import SUPPORTED_PROTOCOL_VERSIONS, negotiate_protocol_version

    def init_with(ver):
        r = handle({"jsonrpc": "2.0", "id": 9, "method": "initialize",
                    "params": {"protocolVersion": ver}}, SEC)
        return r["result"]["protocolVersion"]

    # a supported revision is ECHOED — the client's transport decisions stay coherent
    for ver in SUPPORTED_PROTOCOL_VERSIONS:
        assert init_with(ver) == ver
    # unknown or absent -> our NEWEST, per spec, and the client decides
    newest = SUPPORTED_PROTOCOL_VERSIONS[0]
    assert init_with("1999-01-01") == newest
    assert init_with(None) == newest
    assert negotiate_protocol_version("") == newest
    # the modern revisions must be first-class, or the fallback recreates the outage
    assert "2025-06-18" in SUPPORTED_PROTOCOL_VERSIONS
