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
