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

from .. import __version__, cas, corpus
from ..config import EngineConfig
from ..derivation import verify_derivation
from ..verifiers import scripture

Response = Tuple[int, Dict[str, Any]]


def _ok(payload: Dict[str, Any]) -> Response:
    return 200, payload


def _err(status: int, msg: str) -> Response:
    return status, {"error": msg}


def _card_brief(c: dict) -> Dict[str, Any]:
    return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
            "surface": c.get("surface"), "snippet": (c.get("body", "") or "")[:200]}


def dispatch(method: str, path: str, query: Dict[str, str], body: Any,
             config: EngineConfig) -> Response:
    """Pure request dispatch — (method, path, query, body, config) → (status, payload)."""
    method = (method or "GET").upper()
    path = path.rstrip("/") or "/"
    surface = config.surface

    if method == "GET" and path in ("/", "/health"):
        return _ok({"ok": True, "version": __version__, "surface": surface})
    if method == "GET" and path == "/identity":
        return _ok({"surface": surface, "identity": config.identity})

    if method == "POST" and path == "/verify":
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        if isinstance(body.get("steps"), list):
            return _ok(verify_derivation(body["steps"]))
        if body.get("mode"):
            return _ok(verify_derivation([{"id": "b", "domain": "mathematics", "spec": body}]))
        return _err(400, "body must have 'steps' or {mode, params}")

    if method == "GET" and path == "/search":
        q = (query.get("q") or "").strip()
        if not q:
            return _err(400, "q required")
        try:
            limit = int(query.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20
        res = corpus.search(q, limit=limit)  # shared keeping (both surfaces)
        return _ok({"query": q, "count": len(res), "results": [_card_brief(c) for c in res]})

    if method == "GET" and path == "/seal":
        h = (query.get("hash") or "").strip()
        if not h:
            return _err(400, "hash required")
        rec = cas.fetch(h)
        if rec is None:
            return _err(404, "seal not found")
        return _ok(rec)

    if method == "GET" and path == "/resolve":
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        return _ok(scripture.resolve_ref(ref))

    if method == "GET" and path == "/word_study":
        if not config.witness_surfaced:
            return _err(404, "not found")
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        return _ok(scripture.word_study(s))

    return _err(404, "not found")


_API_GET_PATHS = {"/health", "/identity", "/search", "/seal", "/resolve", "/word_study"}


def serve(host: str = "127.0.0.1", port: int = 8000, surface: str = "secular",
          site_dir: str = None) -> None:
    """Thin http.server shell: the API + (optionally) the static site, same-origin. Stdlib only."""
    import json
    import mimetypes
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from pathlib import Path
    from urllib.parse import parse_qs, urlparse

    config = EngineConfig(surface)
    site = Path(site_dir).resolve() if site_dir else None

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, payload: dict) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
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
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _do(self, method: str) -> None:
            u = urlparse(self.path)
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

        def log_message(self, *args) -> None:  # quiet
            pass

    where = f" + site {site}" if site else ""
    print(f"Narrow Highway API ({surface}) on http://{host}:{port}{where}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
