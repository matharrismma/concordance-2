"""Streamable-HTTP MCP transport test — the remote agent mount.

Proves the MCP HTTP semantics: initialize mints an Mcp-Session-Id; tools/call returns
JSON; SSE is chosen when the client accepts only event-stream; notifications get 202; GET
is 405; DELETE is 200; batches return an array; witness tools surface on the witness
config. Runnable with `pytest` OR `python tests/test_mcp_http.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp.http import handle_http  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def _post(obj, accept="application/json", config=SEC):
    return handle_http("POST", {"Accept": accept}, json.dumps(obj).encode("utf-8"), config)


def test_initialize_mints_session():
    st, h, b = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert st == 200 and "Mcp-Session-Id" in h
    assert json.loads(b)["result"]["serverInfo"]["name"] == "narrow-highway"


def test_tools_call_json():
    st, h, b = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "verify", "arguments": {"mode": "equality",
                                        "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}}})
    assert st == 200 and h["Content-Type"] == "application/json"
    assert json.loads(json.loads(b)["result"]["content"][0]["text"])["verdict"] == "HOLDS"


def test_sse_when_only_event_stream_accepted():
    st, h, b = _post({"jsonrpc": "2.0", "id": 3, "method": "tools/list"}, accept="text/event-stream")
    assert st == 200 and h["Content-Type"] == "text/event-stream"
    assert b.startswith(b"event: message")


def test_notification_is_202():
    st, h, b = _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert st == 202 and b == b""


def test_get_is_405():
    st, h, b = handle_http("GET", {"Accept": "text/event-stream"}, b"", SEC)
    assert st == 405


def test_delete_is_200():
    st, h, b = handle_http("DELETE", {"Mcp-Session-Id": "abc"}, b"", SEC)
    assert st == 200


def test_batch_returns_array():
    st, h, b = _post([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                      {"jsonrpc": "2.0", "id": 2, "method": "initialize"}])
    arr = json.loads(b)
    assert isinstance(arr, list) and len(arr) == 2


def test_witness_tools_surface_on_witness():
    st, h, b = handle_http("POST", {"Accept": "application/json"},
                           json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(), WIT)
    names = [t["name"] for t in json.loads(b)["result"]["tools"]]
    assert "word_study" in names and "resolve" in names


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} MCP-HTTP tests passed — Streamable HTTP transport, sessions + SSE, sovereign.")
