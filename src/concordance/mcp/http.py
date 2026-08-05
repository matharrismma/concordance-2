"""Streamable HTTP transport for MCP — sovereign, stdlib only.

Wraps the pure JSON-RPC `handle()` in the MCP Streamable HTTP semantics so remote MCP
connector clients can mount the engine over HTTP:

  POST   /mcp  — a JSON-RPC request (or batch) → a JSON or SSE response; 202 for a
                 notification-only payload. `initialize` mints an `Mcp-Session-Id`
                 (returned as a header); later requests may carry it (validated
                 leniently — the tools are stateless, so a missing/unknown id still serves).
  GET    /mcp  — 200 text/event-stream: the SSE half of the transport. We initiate no
                 server→client messages, so the stream sends a retry hint and closes
                 cleanly (404 for an unknown Mcp-Session-Id, per spec).
  DELETE /mcp  — terminate the session (200).

Content negotiation: SSE (one `message` event) when the client accepts ONLY
text/event-stream; otherwise a single JSON response. Both are spec-compliant for a
request/response tool server.
"""
from __future__ import annotations

import json
import os
import secrets
from typing import Any, Dict, Tuple

from .server import PROTOCOL_VERSION, handle, negotiate_protocol_version

_DEFAULT_ORIGINS = {"https://narrowhighway.com", "https://narrowhighway.org",
                    "https://narrowhighway.tv"}


def _origin_allowed(origin: str) -> bool:
    """DNS-rebinding defense (MCP Streamable-HTTP). Non-browser clients (agents) send no
    Origin and are allowed; a browser Origin must be on the allowlist. Extend via
    CONCORDANCE_ALLOWED_ORIGINS (comma-separated).

    PARSED, never prefix-matched (red team 2026-08-05, P0): startswith("http://localhost")
    accepted http://localhost.evil.com. Scheme, hostname and port are compared exactly;
    loopback is the literal set {localhost, 127.0.0.1, ::1} over http, any port."""
    if not origin:
        return True
    from urllib.parse import urlsplit
    try:
        u = urlsplit(origin.strip())
        scheme = (u.scheme or "").lower()
        host = (u.hostname or "").rstrip(".").lower()
        port = u.port  # raises for garbage ports
    except ValueError:
        return False
    if not scheme or not host or u.username or u.password:
        return False
    if scheme == "http" and host in ("localhost", "127.0.0.1", "::1"):
        return True
    allowed = {a.strip().lower().rstrip("/") for a in
               os.environ.get("CONCORDANCE_ALLOWED_ORIGINS", "").split(",") if a.strip()}
    allowed |= {a.lower() for a in _DEFAULT_ORIGINS}
    # normalize the candidate to scheme://host[:port] with default ports elided
    default = {"http": 80, "https": 443}.get(scheme)
    norm = f"{scheme}://{host}" if port in (None, default) else f"{scheme}://{host}:{port}"
    return norm in allowed

# In-memory session registry. Lightweight: the tools are stateless, so a session is just
# a validity token + the negotiated protocol version. Cleared on restart.
_SESSIONS: Dict[str, Dict[str, Any]] = {}
# A bound on total tracked sessions — nothing here is security-critical (an unknown id still
# serves, see handle_http's docstring), but with NO cap `initialize` calls accumulate forever
# with no eviction (unlike ratelimit.py's own periodic sweep), a slow, unbounded memory leak
# over a long-running process. Evict oldest first (dicts are insertion-ordered) once past the cap.
_MAX_SESSIONS = 10_000


def _new_session(protocol_version: str) -> str:
    sid = secrets.token_hex(16)
    if len(_SESSIONS) >= _MAX_SESSIONS:
        _SESSIONS.pop(next(iter(_SESSIONS)), None)
    # store the NEGOTIATED revision, not the raw client string — the header path reads this
    # back, and body and header must never disagree about what was agreed
    _SESSIONS[sid] = {"protocol": negotiate_protocol_version(protocol_version)}
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
                config, profile=None) -> Tuple[int, Dict[str, str], bytes]:
    """Handle one Streamable-HTTP MCP request. Returns (status, headers, body_bytes)."""
    method = (method or "GET").upper()

    origin = _hget(headers, "Origin")
    if origin and not _origin_allowed(origin):  # DNS-rebinding defense
        return (403, {"Content-Type": "application/json"},
                b'{"error":"origin not allowed"}')

    if method == "GET":
        # The SSE half of Streamable HTTP. Measured 2026-08-05: 78->141 refusals/day and
        # rising — Bun/node/undici (the TypeScript MCP SDK: Claude-side clients) open this
        # stream, and MCPScoringEngine was flunking us 405 by 405. We initiate no
        # server->client messages, so the honest stream is: 200, a retry hint so clients
        # reconnect gently instead of hammering, then a clean close — never a held thread
        # per stream (the fd-exhaustion lesson: reading must not knock out proving).
        sid = _hget(headers, "Mcp-Session-Id")
        if sid and sid not in _SESSIONS:
            return (404, {"Content-Type": "application/json"},
                    b'{"error":"unknown or expired session; re-initialize"}')
        return (200, {"Content-Type": "text/event-stream", "Cache-Control": "no-store"},
                b"retry: 60000\n\n: narrowhighway keeps no server-initiated stream; POST for tools\n\n")
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
    # THE GATE for an agent lives on the session record: `ask` opens it (the classifier decides,
    # never the caller), and the witness tools become listable and callable for that session only.
    # An unknown or absent session id gets a scratch dict — so it is CLOSED, and stays closed,
    # because nothing persists it. Same rule as the browser cookie on the HTTP side.
    sid = _hget(headers, "Mcp-Session-Id")
    for m in msgs:
        if not isinstance(m, dict):
            continue
        if m.get("method") == "initialize":
            new_sid = _new_session((m.get("params") or {}).get("protocolVersion"))
            sid = new_sid
        session = _SESSIONS.get(sid) if sid else None
        if session is None:
            session = {}
        resp = handle(m, config, session, profile=profile)
        if resp is not None:
            out.append(resp)

    # the session's negotiated revision; a constant here re-created the very mismatch the
    # negotiation fix removed (a 2025-06-18 client reading a 2024-11-05 header mid-session)
    _neg = (_SESSIONS.get(sid) or {}).get("protocol") if sid else None
    resp_headers: Dict[str, str] = {"MCP-Protocol-Version": _neg or negotiate_protocol_version(None)}
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
