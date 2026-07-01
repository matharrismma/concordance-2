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

    if method == "POST" and path == "/ask":
        # The conduit front door: find + verify + cite, never generate. Deterministic router.
        if not isinstance(body, dict) or not str(body.get("text") or "").strip():
            return _err(400, "text required")
        from .. import ask as _ask, threads as _threads
        text = str(body["text"])
        tid = body.get("thread_id") if isinstance(body.get("thread_id"), str) else None
        # The Gate (Ask/Seek/Knock, Mt 7:7): facts by default; once the person's own seeking opens
        # the door, bring the Word — and keep bringing it. The open state lives on the thread (the
        # Deck remembers), so the door, once opened, stays open. We present; we do not cross.
        rec = _threads.get(tid) if tid else None
        prior_open = bool(rec and rec.get("gate_open")) or (surface == "witness")
        gate_open = prior_open or _ask.gate_signal(text)
        just_opened = gate_open and not prior_open
        r = _ask.respond(text, config, gate_open=gate_open, gate_just_opened=just_opened)
        # The Deck: append this exchange (verbatim user text + the exact response) so the
        # conversation is one continuous, resumable chain, carrying the sticky gate state. Nothing
        # generated. Best-effort, OFF TO THE SIDE — never alters the answer, never breaks it.
        try:
            if not tid:
                tid = _threads.new_thread(surface)["thread_id"]
            try:
                _threads.append(tid, text, r, surface=surface, gate_open=gate_open)
            except ValueError:  # a malformed client-held id — start a fresh deck instead of failing
                tid = _threads.new_thread(surface)["thread_id"]
                _threads.append(tid, text, r, surface=surface, gate_open=gate_open)
            r = {**r, "thread_id": tid}
        except Exception:  # noqa: BLE001 — the conduit answer stands even if the deck write fails
            pass
        telemetry.record("ask", surface=surface, kind=r.get("kind"), thread=tid, gate=gate_open)
        return _ok(r)

    if method == "POST" and path == "/journal":
        # The Journal: keep the day's ideas/writings — the extra that rescues what chats waste.
        if not isinstance(body, dict) or not str(body.get("text") or "").strip():
            return _err(400, "text required")
        from .. import stacks
        topics = body.get("topics") if isinstance(body.get("topics"), list) else None
        r = stacks.journal_add(str(body["text"]), kind=str(body.get("kind") or "idea"), topics=topics)
        telemetry.record("journal", surface=surface, kind=str(body.get("kind") or "idea"))
        return _ok(r)

    if method == "POST" and path == "/steward/budget":
        # Steward: the honest arithmetic of a household, sealed. It shows; it never moves money.
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import steward
        b = steward.budget(body.get("income"), body.get("expenses") or [])
        # Seal the math in exact integer cents — a receipt for your money (the moat applied to finance).
        inc_c, tot_c, net_c = round(b["income"] * 100), round(b["total_expenses"] * 100), round(b["net"] * 100)
        from ..derivation import verify as _verify
        from .. import receipts
        res = _verify({"mode": "equality",
                       "params": {"expr_a": str(net_c), "expr_b": f"({inc_c})-({tot_c})", "variables": {}}})
        b["seal"] = receipts.attach(res, config=config, domain="mathematics").get("seal")
        telemetry.record("steward", surface=surface, op="budget", sealed=bool(b.get("seal")))
        return _ok(b)

    if method == "POST" and path == "/steward/cost-destroyed":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import steward
        return _ok(steward.cost_destroyed(body.get("items") or []))

    if method == "POST" and path == "/steward/ask":
        # Free-text to Steward: the boundary, enforced — money-move/advice is declined + pointed back.
        if not isinstance(body, dict) or not str(body.get("text") or "").strip():
            return _err(400, "text required")
        from .. import steward
        g = steward.money_guardrail(str(body["text"]))
        return _ok(g if g else {"kind": "ok", **steward.guidance()})

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

    if method == "GET" and path == "/card/connections":
        cid = (query.get("id") or "").strip()
        if not cid:
            return _err(400, "id required")
        r = corpus.connections(cid)
        return _ok(r) if r is not None else _err(404, "card not found")
    if method == "GET" and path == "/locate":
        return _ok(corpus.locate(query.get("q") or ""))
    if method == "GET" and path == "/library/health":
        return _ok(corpus.health())

    # Pronunciation guide (synthesized, honest floor) — a neutral phonetic helper, both surfaces.
    if method == "GET" and path == "/pronounce":
        from .. import pronounce
        text = (query.get("text") or query.get("word") or "").strip()
        if not text:
            return _err(400, "text required")
        return _ok(pronounce.guide(text))

    # The Deck — a conversation as a resumable, searchable, tamper-evident chain (threads).
    if method == "GET" and path == "/thread":
        from .. import threads as _threads
        tid = (query.get("id") or "").strip()
        if not tid:
            return _err(400, "id required")
        rec = _threads.get(tid)
        return _ok(rec) if rec is not None else _err(404, "thread not found")
    if method == "GET" and path == "/threads":
        from .. import threads as _threads
        try:
            limit = int(query.get("limit", "50"))
        except (TypeError, ValueError):
            limit = 50
        return _ok({"threads": _threads.list_threads(limit=limit)})
    if method == "GET" and path == "/threads/search":
        from .. import threads as _threads
        q = (query.get("q") or "").strip()
        if not q:
            return _err(400, "q required")
        try:
            limit = int(query.get("limit", "10"))
        except (TypeError, ValueError):
            limit = 10
        res = _threads.search(q, limit=limit)
        return _ok({"query": q, "count": len(res), "results": res})
    if method == "GET" and path == "/thread/verify":
        from .. import threads as _threads
        tid = (query.get("id") or "").strip()
        if not tid:
            return _err(400, "id required")
        ok, detail = _threads.verify_thread(tid)
        return _ok({"thread_id": tid, "ok": ok, "detail": detail})
    if method == "DELETE" and path == "/thread":
        # Right-to-be-forgotten: the client holds the id; anyone with it may forget the deck.
        from .. import threads as _threads
        return _ok({"deleted": _threads.delete((query.get("id") or "").strip())})

    # The Journal — a date-stack of the day's ideas/writings + the Deck's exchanges (superposition).
    if method == "GET" and path == "/journal":
        from .. import stacks
        return _ok(stacks.journal_day(query.get("date") or None))
    if method == "GET" and path == "/journal/dates":
        from .. import stacks
        return _ok({"dates": stacks.journal_dates()})

    if method == "GET" and path == "/steward":
        from .. import steward
        return _ok(steward.guidance())

    # Atlas / grid — the map, read-only.
    if method == "GET" and path == "/grid":
        from .. import grid
        ax = (query.get("axis") or "").strip()
        if ax:
            v = grid.axis_view(ax)
            return _ok(v) if v is not None else _err(404, "unknown axis")
        return _ok(grid.overview())
    if method == "GET" and path == "/grid/dimension":
        from .. import grid
        d = (query.get("d") or query.get("dimension") or "").strip()
        if not d:
            return _err(400, "d (dimension) required")
        return _ok({"dimension": d, "axes": grid.dimension_axes(d)})

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

    if method == "GET" and path == "/passage":
        # Read a passage (verse / range / whole chapter) — the Bible reading primitive.
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.read_passage(ref))

    if method == "GET" and path == "/word_study":
        if not config.witness_surfaced:
            return _err(404, "not found")
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_study(s))

    if method == "GET" and path == "/cross_refs":
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.cross_references(ref))

    if method == "GET" and path == "/word_occurrences":
        if not config.witness_surfaced:
            return _err(404, "not found")
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_occurrences(s))

    if method == "GET" and path == "/original":
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.original_words(ref))

    if method == "GET" and path == "/canon":
        # The canon as concentric layers — the 66 core + disputed books, framed, never merged.
        if not config.witness_surfaced:
            return _err(404, "not found")
        from .. import canon
        book = (query.get("book") or "").strip()
        return _ok(canon.canon_status(book) if book else canon.overview())

    if method == "GET" and path == "/commentary":
        # Public-domain, attributed commentary (Matthew Henry) — the father's own words, found.
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from .. import commentary
        return _ok(commentary.for_ref(ref, source=(query.get("source") or commentary.DEFAULT_SOURCE)))

    if method == "GET" and path == "/tsk":
        # Editorial cross-references (openbible.info, CC BY — expansion of the public-domain TSK).
        if not config.witness_surfaced:
            return _err(404, "not found")
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        try:
            limit = int(query.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20
        from .. import xrefs
        return _ok(xrefs.for_ref(ref, limit=limit))

    if method == "GET" and path == "/character":
        # A Bible figure from Easton's (1897, PD) — summary + every verse that speaks of them.
        if not config.witness_surfaced:
            return _err(404, "not found")
        name = (query.get("name") or "").strip()
        if not name:
            return _err(400, "name required")
        from .. import characters
        rec = characters.get(name)
        return _ok(rec) if rec is not None else _err(404, "not found in Easton's")

    if method == "GET" and path == "/characters":
        if not config.witness_surfaced:
            return _err(404, "not found")
        from .. import characters
        try:
            limit = int(query.get("limit", "100"))
        except (TypeError, ValueError):
            limit = 100
        return _ok(characters.browse(letter=(query.get("letter") or None),
                                     search=(query.get("search") or None), limit=limit))

    return _err(404, "not found")


_API_GET_PATHS = {"/health", "/identity", "/search", "/seal", "/resolve", "/word_study",
                  "/card", "/cards", "/cards/stats", "/daily", "/grid", "/grid/dimension",
                  "/card/connections", "/locate", "/library/health",
                  "/thread", "/threads", "/threads/search", "/thread/verify", "/passage",
                  "/pronounce", "/cross_refs", "/word_occurrences", "/original", "/canon",
                  "/commentary", "/journal", "/journal/dates", "/steward", "/tsk",
                  "/character", "/characters"}


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
    RATELIMITED = ("/verify", "/derivation/verify", "/search", "/mcp", "/ask")

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
