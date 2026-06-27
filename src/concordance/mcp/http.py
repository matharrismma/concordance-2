"""Streamable HTTP transport for MCP — sovereign, stdlib only.

Wraps the pure JSON-RPC `handle()` in the MCP Streamable HTTP semantics so remote MCP
connector clients can mount the engine over HTTP:

  POST   /mcp  — a JSON-RPC request (or batch) → a JSON or SSE response; 202 for a
                 notification-only payload. `initialize` mints an `Mcp-Session-Id`
                 (returned as a header); later requests may carry it (validated
                 leniently — the tools are stateless, so a missing/unknown id still serves).
  GET    /mcp  — 405: this server initiates no server→client stream (pure tool server).
  DELETE /mcp  — terminate the session (200).

Content negotiation: SSE (one `message` event) when the client accepts ONLY
text/event-stream; otherwise a single JSON response. Both are spec-compliant for a
request/response tool server.
"""
from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Tuple

from .server import PROTOCOL_VERSION, handle

# In-memory session registry. Lightweight: the tools are stateless, so a session is just
# a validity token + the negotiated protocol version. Cleared on restart.
_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _new_session(protocol_version: str) -> str:
    sid = secrets.token_hex(16)
    _SESSIONS[sid] = {"protocol": protocol_version or PROTOCOL_VERSION}
    return sid


def _hget(headers: Any, key: str) -> str:
    """Case-insensitive header get for either an http.server Message or a plain dict."""
    if headers is None:
        return ""
    g = getattr(headers, "get", None)
    if g is None:
        return ""
    return (g(key) or g(key.lower()) or g(key.title()) or "") or ""


def _wants_sse(accept: str) -> bool:
    a = (accept or "").lower()
    # Prefer JSON; choose SSE only when the client accepts event-stream but not JSON.
    return "text/event-stream" in a and "application/json" not in a


def handle_http(method: str, headers: Any, raw_body: bytes,
                config) -> Tuple[int, Dict[str, str], bytes]:
    """Handle one Streamable-HTTP MCP request. Returns (status, headers, body_bytes)."""
    method = (method or "GET").upper()

    if method == "GET":
        return (405, {"Allow": "POST, DELETE", "Content-Type": "application/json"},
                b'{"error":"this MCP endpoint offers no server stream; use POST"}')
    if method == "DELETE":
        _SESSIONS.pop(_hget(headers, "Mcp-Session-Id"), None)
        return 200, {}, b""
    if method != "POST":
        return 405, {"Allow": "POST, GET, DELETE"}, b""

    try:
        payload = json.loads(raw_body or b"{}")
    except (ValueError, TypeError):
        return (400, {"Content-Type": "application/json"},
                b'{"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"parse error"}}')

    batch = isinstance(payload, list)
    msgs = payload if batch else [payload]
    out = []
    new_sid = None
    for m in msgs:
        if not isinstance(m, dict):
            continue
        if m.get("method") == "initialize":
            new_sid = _new_session((m.get("params") or {}).get("protocolVersion"))
        resp = handle(m, config)
        if resp is not None:
            out.append(resp)

    resp_headers: Dict[str, str] = {"MCP-Protocol-Version": PROTOCOL_VERSION}
    if new_sid:
        resp_headers["Mcp-Session-Id"] = new_sid

    if not out:  # notifications / responses only
        return 202, resp_headers, b""

    body_obj = out if batch else out[0]
    body_json = json.dumps(body_obj, ensure_ascii=False)
    if _wants_sse(_hget(headers, "Accept")):
        resp_headers["Content-Type"] = "text/event-stream"
        return 200, resp_headers, ("event: message\ndata: " + body_json + "\n\n").encode("utf-8")
    resp_headers["Content-Type"] = "application/json"
    return 200, resp_headers, body_json.encode("utf-8")
