"""Streamable-HTTP MCP transport test — the remote agent mount.

Proves the MCP HTTP semantics: initialize mints an Mcp-Session-Id; tools/call returns
JSON; SSE is chosen when the client accepts only event-stream; notifications get 202; GET
serves the SSE stream side; DELETE is 200; batches return an array; witness tools surface on the witness
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


def test_session_registry_is_bounded():
    # A session per initialize() call must not accumulate forever — found: no eviction at all
    # (unlike ratelimit.py's own periodic sweep), an unbounded memory leak over a long-running
    # process. Push well past the cap and confirm the registry never grows beyond it.
    from concordance.mcp import http as mcp_http
    before = mcp_http._MAX_SESSIONS
    try:
        mcp_http._MAX_SESSIONS = 50   # shrink the cap so the test is fast or fast tests
        mcp_http._SESSIONS.clear()
        for i in range(200):
            _post({"jsonrpc": "2.0", "id": i, "method": "initialize"})
        assert len(mcp_http._SESSIONS) <= mcp_http._MAX_SESSIONS
    finally:
        mcp_http._MAX_SESSIONS = before
        mcp_http._SESSIONS.clear()


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


def test_get_serves_the_sse_stream_side():
    """The lost-Claude-traffic fix (2026-08-05): the TS MCP SDK (Bun/node/undici — Claude-side
    clients) opens the GET stream, and a registry scorer was flunking our 405s at 78->141/day.
    The stream: 200 text/event-stream with a retry hint, closing cleanly — no held thread."""
    st, h, b = handle_http("GET", {"Accept": "text/event-stream"}, b"", SEC)
    assert st == 200 and h["Content-Type"] == "text/event-stream"
    assert b.startswith(b"retry:"), "clients must be told to reconnect gently, not hammer"


def test_get_with_unknown_session_is_404_per_spec():
    st, h, b = handle_http("GET", {"Mcp-Session-Id": "no-such-session"}, b"", SEC)
    assert st == 404                                # the client re-initializes


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


def test_response_header_carries_the_negotiated_version_not_a_constant():
    """The body says one version and the header must not say another: a 2025-06-18 client
    reading a constant 2024-11-05 header mid-session is the same mismatch the negotiation fix
    exists to remove."""
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"}}
    st, h, b = _post(init)
    assert st == 200
    assert h.get("MCP-Protocol-Version") == "2025-06-18", h
    import json as _json
    assert _json.loads(b)["result"]["protocolVersion"] == "2025-06-18"


def test_origin_is_parsed_never_prefix_matched():
    """Red team 2026-08-05 (P0, confirmed live): startswith("http://localhost") accepted
    lookalike hosts. Every row here is one of the report's adversarial shapes."""
    from concordance.mcp.http import _origin_allowed
    assert _origin_allowed("")                                  # agents send no Origin
    assert _origin_allowed("http://localhost")
    assert _origin_allowed("http://localhost:3000")
    assert _origin_allowed("http://127.0.0.1:8080")
    assert _origin_allowed("HTTPS://NarrowHighway.COM")         # mixed case
    assert _origin_allowed("https://narrowhighway.com:443")     # default port elided
    assert _origin_allowed("https://narrowhighway.org.")        # trailing dot
    assert not _origin_allowed("http://localhost.evil.com")     # THE lookalike
    assert not _origin_allowed("http://127.0.0.1.evil.com")
    assert not _origin_allowed("https://narrowhighway.com.evil.com")
    assert not _origin_allowed("https://evil.com")
    assert not _origin_allowed("https://user:pw@narrowhighway.com")  # credentials
    assert not _origin_allowed("http://localhost:99999")        # garbage port
    assert not _origin_allowed("null")                          # opaque origin
    assert not _origin_allowed("file://localhost")
