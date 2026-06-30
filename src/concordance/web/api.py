"""Sovereign HTTP API — the floor, exposed. Stdlib only (http.server), zero required deps.

One pure dispatcher serves BOTH surfaces via EngineConfig(surface): the .com runs
surface="secular" (the reach), the .org runs surface="witness". The witness endpoints
(/resolve, /word_study) are surfaced only on the witness surface; /verify, /search,
/seal, /identity are on both (the keeping is shared). `dispatch()` is framework-agnostic
and fully testable; `serve()` is a thin http.server shell.

Endpoints:
  GET  /            · /health      → {ok, version, surface}
  GET  /identity                   → {surface, identity}
  POST /verify   {steps:[...]} OR {mode, params}   → derivation verdict + trail (the moat)
  GET  /search?q=&limit=           → ranked corpus results (shared keeping)
  GET  /seal?hash=                 → the sealed record (the receipt), or 404
  GET  /resolve?ref=     (witness) → scripture reference → WEB text
  GET  /word_study?strongs=  (witness) → Strong's definition + occurrences
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

from .. import __version__, cas, corpus, telemetry
from ..config import EngineConfig
from ..derivation import verify_derivation
# NOTE: scripture (a witness verifier) is imported LAZILY inside the witness-gated branches
# below — never at module top. The secular surface (.com) must not load witness code.

Response = Tuple[int, Dict[str, Any]]


def _ok(payload: Dict[str, Any]) -> Response:
    return 200, payload


def _err(status: int, msg: str) -> Response:
    return status, {"error": msg}


def _card_brief(c: dict) -> Dict[str, Any]:
    return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
            "surface": c.get("surface"), "snippet": (c.get("body", "") or "")[:200]}


def _esc(s: Any) -> str:
    return (str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_seal_html(content_hash: str, record: Optional[Dict[str, Any]]) -> Tuple[int, str]:
    """Server-render a sealed receipt as a crawlable, citable HTML page (data in the markup,
    not client-JS) so search engines and LLMs can read + cite a verification. (status, html)."""
    short = _esc((content_hash or "")[:16])
    head = ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content=\"width=device-width,initial-scale=1\">"
            "<link rel=stylesheet href=/styles.css>")
    if record is None:
        html = (f"{head}<title>Seal not found — Narrow Highway</title><meta name=robots content=noindex>"
                f"</head><body><main class=wrap><h1>No such seal</h1>"
                f"<p class=muted>No sealed record matches <span class=mono>{short}…</span>. A seal is "
                f"content-addressed — if it existed, this hash would fetch it.</p>"
                f"<p><a href=/>← Narrow Highway</a></p></main></body></html>")
        return 404, html
    overall = record.get("overall", "?")
    vcls = "holds" if overall == "PASS" else "broken"
    label = {"PASS": "✓ HOLDS", "REJECT": "✗ BROKEN", "QUARANTINE": "◷ INCOMPLETE"}.get(overall, _esc(overall))
    rows = []
    for v in record.get("verifier_results", []):
        claim = _esc((v.get("data") or {}).get("claim") or v.get("name") or "")
        rows.append(f"<div class=result><span class=s>{_esc(v.get('status', ''))}</span> "
                    f"<span class=t>{claim}</span><div class=trail>{_esc(v.get('detail', ''))}</div></div>")
    trail_html = "".join(rows) or "<p class=muted>(no verifier trail)</p>"
    gates = ", ".join(f"{_esc(g.get('gate'))}:{_esc(g.get('status'))}" for g in record.get("gate_results", []))
    desc = (f"A re-checkable verification receipt — verdict {_esc(overall)}, sealed {short}. "
            f"Narrow Highway: every answer is a receipt, not 'trust me'.")
    html = (f"{head}<title>Receipt {short}… · {label} · Narrow Highway</title>"
            f"<meta name=description content=\"{desc}\">"
            f"<meta property=\"og:title\" content=\"Verification receipt · {label}\">"
            f"<meta property=\"og:description\" content=\"{desc}\"></head><body>"
            f"<header class=site><div class=wrap style=\"padding:.9rem 1.2rem;display:flex;"
            f"justify-content:space-between;align-items:center\"><a class=brand href=/>Narrow"
            f"<span class=road>Highway</span></a><nav class=site><a href=/#verify>Verify</a>"
            f"<a href=/seal.html>Seal</a></nav></div></header><main class=wrap>"
            f"<h1>The receipt</h1><div class=\"verdict {vcls}\" style=\"font-size:1.4rem\">{label}</div>"
            f"<p class=lede>A permanent, tamper-evident record of a verification. The content hash IS "
            f"the proof — re-fetch it and the bytes must match, or it is not this record.</p>"
            f"<section><h2>Worked trail</h2>{trail_html}</section>"
            f"<section class=card><div class=muted style=\"font-size:.8rem\">gates</div>"
            f"<div class=mono>{gates}</div><div class=muted style=\"font-size:.8rem;margin-top:.5rem\">"
            f"content hash (the seal)</div><div class=mono style=\"word-break:break-all\">{_esc(content_hash)}</div>"
            f"<p style=\"margin-top:.6rem\"><a href=\"/seal?hash={_esc(content_hash)}\">raw JSON ↗</a> · "
            f"re-check: <span class=mono>GET /seal?hash={short}…</span></p></section>"
            f"<footer class=site><p>Every answer is a receipt, not \"trust me.\" The engine verifies; "
            f"it does not generate the answer. <a href=/>Narrow Highway →</a></p></footer></main></body></html>")
    return 200, html


def dispatch(method: str, path: str, query: Dict[str, str], body: Any,
             config: EngineConfig) -> Response:
    """Pure request dispatch — (method, path, query, body, config) → (status, payload)."""
    method = (method or "GET").upper()
    path = path.rstrip("/") or "/"
    surface = config.surface

    if method == "GET" and path in ("/", "/health"):
        from ..validate import _HAS_JSONSCHEMA, schema_active
        return _ok({"ok": True, "version": __version__, "surface": surface,
                    "schema_active": schema_active(config.schema_path, config.skip_schema_validation),
                    "jsonschema": _HAS_JSONSCHEMA})
    if method == "GET" and path == "/identity":
        return _ok({"surface": surface, "identity": config.identity})

    if method == "POST" and path in ("/verify", "/derivation/verify"):
        # /derivation/verify is the 1.0-compatible alias (preserves the public moat contract).
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        dom = "mathematics"
        if isinstance(body.get("steps"), list):
            res = verify_derivation(body["steps"])
            if body["steps"]:
                dom = str(body["steps"][0].get("domain") or "mathematics")
        elif body.get("mode"):
            res = verify_derivation([{"id": "b", "domain": "mathematics", "spec": body}])
        else:
            return _err(400, "body must have 'steps' or {mode, params}")
        # Mint the receipt: a verdict alone is "trust me"; the seal is re-checkable. ?seal=0 opts out.
        seal_on = str(query.get("seal", "1")).lower() not in ("0", "false", "no", "off")
        from .. import receipts
        res = receipts.attach(res, config=config, domain=dom, enabled=seal_on)
        telemetry.record("verify", surface=surface, verdict=res.get("verdict"),
                         mode=str(body.get("mode") or "steps"), sealed=bool(res.get("seal")))
        return _ok(res)

    if method == "POST" and path == "/mcp":
        # Remote MCP over HTTP — reuse the pure JSON-RPC handler, surface-gated. Stateless
        # request/response (initialize · tools/list · tools/call). Notifications get 202.
        from ..mcp import handle as _mcp_handle
        req = body if isinstance(body, dict) else {}
        telemetry.record("mcp", surface=surface, method=str(req.get("method") or ""))
        resp = _mcp_handle(req, config)
        return (200, resp) if resp is not None else (202, {})

    if method == "GET" and path == "/search":
        q = (query.get("q") or "").strip()
        if not q:
            return _err(400, "q required")
        try:
            limit = int(query.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20
        res = corpus.search(q, limit=limit)  # shared keeping (both surfaces)
        telemetry.record("search", surface=surface, query=q, count=len(res))
        return _ok({"query": q, "count": len(res), "results": [_card_brief(c) for c in res]})

    # Library / keeping tools (ported from 1.0, additive — over the same shared corpus).
    if method == "GET" and path == "/cards/stats":
        return _ok(corpus.stats())
    if method == "GET" and path == "/cards":
        try:
            limit = int(query.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20
        try:
            offset = int(query.get("offset", "0"))
        except (TypeError, ValueError):
            offset = 0
        return _ok(corpus.browse(shelf=(query.get("shelf") or None), limit=limit, offset=offset))
    if method == "GET" and path == "/card":
        cid = (query.get("id") or "").strip()
        if not cid:
            return _err(400, "id required")
        c = corpus.get_card(cid)
        return _ok(c) if c is not None else _err(404, "card not found")
    if method == "GET" and path == "/daily":
        c = corpus.daily(query.get("seed") or None)
        return _ok(c) if c is not None else _err(404, "the keeping is empty")

    if method == "GET" and path == "/seal":
        h = (query.get("hash") or "").strip()
        if not h:
            return _err(400, "hash required")
        rec = cas.fetch(h)
        telemetry.record("seal_fetch", surface=surface, found=rec is not None)
        if rec is None:
            return _err(404, "seal not found")
        return _ok(rec)

    if method == "GET" and path == "/resolve":
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.resolve_ref(ref))

    if method == "GET" and path == "/word_study":
        if not config.witness_surfaced:
            return _err(404, "not found")
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_study(s))

    return _err(404, "not found")


_API_GET_PATHS = {"/health", "/identity", "/search", "/seal", "/resolve", "/word_study",
                  "/card", "/cards", "/cards/stats", "/daily"}


def serve(host: str = "127.0.0.1", port: int = 8000, surface: str = "secular",
          site_dir: str = None) -> None:
    """Thin http.server shell: the API + (optionally) the static site, same-origin. Stdlib only."""
    import json
    import mimetypes
    import os
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from pathlib import Path
    from urllib.parse import parse_qs, urlparse

    # Correct MIME for the self-hosted ML assets: ESM modules are MIME-strict (a browser
    # refuses an .mjs served as octet-stream), and .wasm should be application/wasm.
    mimetypes.add_type("text/javascript", ".mjs")
    mimetypes.add_type("text/javascript", ".js")
    mimetypes.add_type("application/wasm", ".wasm")
    mimetypes.add_type("application/json", ".json")

    from .. import ratelimit

    config = EngineConfig(surface)
    site = Path(site_dir).resolve() if site_dir else None
    limiter = ratelimit.from_env()
    MAX_BODY = int(os.environ.get("CONCORDANCE_MAX_BODY", str(256 * 1024)) or 256 * 1024)
    RATELIMITED = ("/verify", "/derivation/verify", "/search", "/mcp")

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, payload: dict, extra: dict = None) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("x-content-type-options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _static(self, path: str) -> None:
            rel = path.lstrip("/") or "index.html"
            fp = (site / rel).resolve()
            if not str(fp).startswith(str(site)) or not fp.is_file():  # traversal guard + existence
                return self._json(404, {"error": "not found"})
            body = fp.read_bytes()
            ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("content-type", ctype)
            self.send_header("x-content-type-options", "nosniff")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, status: int, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("x-content-type-options", "nosniff")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _rl_key(self) -> str:
            """Rate-limit key: the real client (Caddy sets X-Forwarded-For to it), else peer."""
            xff = (self.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            return xff or (self.client_address[0] if self.client_address else "?")

        def _keep(self, u) -> None:
            """The operator's window — gated. 404 to non-operators (hide-existence).
            SECURITY: the operator decision uses the REAL socket peer + token only; the
            spoofable X-Forwarded-For is never consulted for access (see keep.is_operator)."""
            from .keep import dashboard as _keep_dash
            from .keep import request_is_operator
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            peer_ip = self.client_address[0] if self.client_address else ""
            if not request_is_operator(peer_ip, self.headers, q):
                return self._json(404, {"error": "not found"})
            if u.path == "/keep.json":
                return self._json(200, _keep_dash(config), {"cache-control": "no-store"})
            if site is not None:
                return self._static("keep.html")
            return self._json(404, {"error": "not found"})

        def _do(self, method: str) -> None:
            u = urlparse(self.path)
            # DoS guard: reject oversized bodies before reading a single byte
            if method == "POST":
                try:
                    clen = int(self.headers.get("content-length") or 0)
                except ValueError:
                    clen = 0
                if clen > MAX_BODY:
                    return self._json(413, {"error": f"request body too large (> {MAX_BODY} bytes)"})
            if method == "GET" and u.path in ("/keep", "/keep.html", "/keep.json"):
                return self._keep(u)  # operator-gated dashboard
            if method == "GET" and u.path.startswith("/s/"):  # server-rendered citable receipt
                h = u.path[3:].split("/")[0].strip()
                status, html = render_seal_html(h, cas.fetch(h))
                return self._html(status, html)
            # rate limit the compute / IO paths, keyed by the real client
            if u.path in RATELIMITED:
                key = self._rl_key()
                if not limiter.allow(key):
                    return self._json(429, {"error": "rate limit exceeded"},
                                      {"retry-after": str(limiter.retry_after(key))})
            if u.path == "/mcp":  # full Streamable-HTTP MCP transport (POST/GET/DELETE)
                raw = b""
                if method == "POST":
                    n = int(self.headers.get("content-length") or 0)
                    raw = self.rfile.read(n) if n else b""
                from ..mcp.http import handle_http
                status, hdrs, body = handle_http(method, self.headers, raw, config)
                self.send_response(status)
                for k, v in hdrs.items():
                    self.send_header(k, v)
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                if body:
                    self.wfile.write(body)
                return
            # static site (GET only) for non-API paths, when a site dir is configured
            if method == "GET" and site is not None and u.path not in _API_GET_PATHS:
                return self._static(u.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            body = None
            if method == "POST":
                n = int(self.headers.get("content-length") or 0)
                raw = self.rfile.read(n) if n else b""
                try:
                    body = json.loads(raw or b"{}")
                except (ValueError, TypeError):
                    body = {}
            status, payload = dispatch(method, u.path, q, body, config)
            self._json(status, payload)

        def do_GET(self) -> None:
            self._do("GET")

        def do_POST(self) -> None:
            self._do("POST")

        def do_DELETE(self) -> None:
            self._do("DELETE")

        def log_message(self, *args) -> None:  # quiet
            pass

    where = f" + site {site}" if site else ""
    print(f"Narrow Highway API ({surface}) on http://{host}:{port}{where}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
