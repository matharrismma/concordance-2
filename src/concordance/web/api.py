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

from typing import Any, Dict, List, Optional, Tuple

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


def _gate_closed() -> Response:
    """A witness endpoint reached before the person's seeking has opened the gate (Ask/Seek/Knock,
    Mt 7:7). Still 404 — the Word is not surfaced yet — but MARKED, so a client can invite them to
    open it rather than showing a dead end. We present the path; we never cross it."""
    return 404, {"error": "gate_closed", "gate": "closed",
                 "detail": "The Word opens as you seek it — bring up Scripture in the conversation, "
                           "and the way opens."}


def _card_brief(c: dict) -> Dict[str, Any]:
    return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
            "surface": c.get("surface"), "snippet": (c.get("body", "") or "")[:200]}


def _esc(s: Any) -> str:
    return (str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _safe_url(u: Any) -> str:
    """Allowlist URL schemes before a value reaches an href/src — blocks javascript:, data:,
    vbscript: and other script-executing schemes. Returns "" for anything not clearly safe.
    _esc handles the quote/angle-bracket context; this handles the URL-scheme context."""
    s = str("" if u is None else u).strip()
    low = s.lower().replace("\t", "").replace("\n", "").replace("\r", "")
    if low.startswith(("http://", "https://", "mailto:", "/", "#", "?", "./")):
        return s
    return ""


# ── Server-rendered page shell (shared by render_seal/badge/card_html) ────
# ONE definition of the crawlable page chrome — the <head>, the site header+nav, and the
# not-found body — so the three server-rendered pages don't each re-declare it. Data stays in
# the markup (no client-JS), so search engines and LLMs can read + cite the page.
_HEAD = ("<!doctype html><html lang=en><head><meta charset=utf-8>"
         "<meta name=viewport content=\"width=device-width,initial-scale=1\">"
         "<link rel=stylesheet href=/styles.css>")


def _site_header(nav_inner: str) -> str:
    """The brand + nav header bar. `nav_inner` is the page-appropriate set of <a> links."""
    return ("<header class=site><div class=wrap style=\"padding:.9rem 1.2rem;display:flex;"
            "justify-content:space-between;align-items:center\"><a class=brand href=/>Narrow"
            f"<span class=road>Highway</span></a><nav class=site>{nav_inner}</nav></div></header>")


def _notfound_page(title: str, body_html: str) -> str:
    """A 404 page: the shared head + a noindex meta + a minimal body. `title`/`body_html` pre-escaped."""
    return (f"{_HEAD}<title>{title} — Narrow Highway</title><meta name=robots content=noindex>"
            f"</head><body><main class=wrap>{body_html}</main></body></html>")


def render_seal_html(content_hash: str, record: Optional[Dict[str, Any]]) -> Tuple[int, str]:
    """Server-render a sealed receipt as a crawlable, citable HTML page (data in the markup,
    not client-JS) so search engines and LLMs can read + cite a verification. (status, html)."""
    short = _esc((content_hash or "")[:16])
    head = _HEAD
    if record is None:
        html = _notfound_page("Seal not found",
                f"<h1>No such seal</h1>"
                f"<p class=muted>No sealed record matches <span class=mono>{short}…</span>. A seal is "
                f"content-addressed — if it existed, this hash would fetch it.</p>"
                f"<p><a href=/>← Narrow Highway</a></p>")
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
            f"<meta property=\"og:description\" content=\"{desc}\">"
            f"<link rel=canonical href=\"/s/{_esc(content_hash)}\">"
            f"<meta property=\"og:type\" content=article>"
            f"<meta name=\"twitter:card\" content=\"summary\"></head><body>"
            f"{_site_header('<a href=/#verify>Verify</a><a href=/seal.html>Seal</a>')}<main class=wrap>"
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


def render_badge_html(badge_hash: str, verify_result: Optional[Dict[str, Any]]) -> Tuple[int, str]:
    """Server-render a badge as a crawlable, citable HTML page (data in the markup) — MIRRORS
    render_seal_html. A badge points at N seals that STILL STAND; the page states EXACTLY N (the
    result's own copy, VERBATIM — no competency noun) and links each sealed check to its /s/<hash>
    seal page so anyone can re-check the evidence. (status, html)."""
    short = _esc((badge_hash or "")[:16])
    head = _HEAD
    if verify_result is None or not verify_result.get("ok"):
        html = _notfound_page("Badge not found",
                f"<h1>No such badge</h1>"
                f"<p class=muted>No badge matches <span class=mono>{short}…</span>. A badge is "
                f"content-addressed — if it existed, this hash would fetch it, and every seal it "
                f"points at would re-verify.</p>"
                f"<p><a href=/>← Narrow Highway</a></p>")
        return 404, html
    n = verify_result.get("checks", 0)
    copy = _esc(verify_result.get("copy") or "")   # the result's own copy — VERBATIM, no competency noun
    title = _esc(verify_result.get("title") or "")
    rows = []
    for h in verify_result.get("sealed_checks", []):
        hs = _esc(str(h))
        hshort = _esc(str(h)[:16])
        rows.append(f"<div class=result><a class=mono href=\"/s/{hs}\">{hshort}… ↗</a>"
                    f"<div class=trail>a sealed verification that re-verifies in the store</div></div>")
    checks_html = "".join(rows) or "<p class=muted>(no sealed checks stand)</p>"
    desc = (f"A re-checkable badge — {copy}, content-addressed {short}. Every referenced seal "
            f"re-verifies from the floor. Narrow Highway: a receipt you own, not a rank we grant.")
    heading = title if title else "The badge"
    html = (f"{head}<title>Badge {short}… · {copy} · Narrow Highway</title>"
            f"<meta name=description content=\"{desc}\">"
            f"<meta property=\"og:title\" content=\"Badge · {copy}\">"
            f"<meta property=\"og:description\" content=\"{desc}\"></head><body>"
            f"{_site_header('<a href=/#verify>Verify</a><a href=/seal.html>Seal</a>')}<main class=wrap>"
            f"<h1>{_esc(heading)}</h1><div class=\"verdict holds\" style=\"font-size:1.4rem\">{copy}</div>"
            f"<p class=lede>A badge is a receipt you OWN. It claims no mastery, skill, or level — only "
            f"that {_esc(str(n))} sealed verifications still stand when you re-check them. The evidence "
            f"is the seals below; re-fetch any one and its bytes must match, or it does not count.</p>"
            f"<section><h2>Sealed checks ({_esc(str(n))})</h2>{checks_html}</section>"
            f"<section class=card><div class=muted style=\"font-size:.8rem\">badge hash (content address)</div>"
            f"<div class=mono style=\"word-break:break-all\">{_esc(badge_hash)}</div>"
            f"<p style=\"margin-top:.6rem\"><a href=\"/badges?hash={_esc(badge_hash)}\">raw JSON ↗</a> · "
            f"re-check: <span class=mono>GET /badges?hash={short}…</span></p></section>"
            f"<footer class=site><p>A badge reports, re-checkably, how many verifications you sealed — "
            f"nothing about how good you are. Success is needing the tool less (John 3:30). "
            f"<a href=/>Narrow Highway →</a></p></footer></main></body></html>")
    return 200, html


def render_card_html(card_id: str, card: Optional[Dict[str, Any]]) -> Tuple[int, str]:
    """Server-render a keeping card as a crawlable, citable HTML page (data IN the markup, not
    client-JS) — MIRRORS render_seal_html. The first artifact of 2.0 standing alone: only FOUND
    fields render (title, body, the cited source line) — cite-fair, generate nothing. Carries a
    canonical link, description + og tags, a schema.org CreativeWork (with citation) JSON-LD, and a
    cross-link to /search. 404 page carries meta robots noindex. (status, html)."""
    import json as _json
    short = _esc((card_id or "")[:24])
    head = _HEAD
    if card is None:
        html = _notfound_page("Card not found",
                f"<h1>No such record</h1>"
                f"<p class=muted>No card matches <span class=mono>{short}</span> in the keeping.</p>"
                f"<p><a href=/search>← Search the keeping</a></p>")
        return 404, html
    title = _esc(card.get("title") or card_id)
    body_txt = card.get("body") or ""
    body_html = f"<p>{_esc(body_txt)}</p>" if body_txt else ""
    src = card.get("source") or {}
    src_ref = str(src.get("ref") or "").strip()
    src_label = str(src.get("label") or "").strip()
    src_url = _safe_url(src.get("url"))  # scheme-allowlisted — no javascript:/data: into href
    # The cited source line — cite-fair: render only what is found, generate nothing.
    cite_bits = []
    if src_label:
        cite_bits.append(_esc(src_label))
    if src_ref:
        cite_bits.append(_esc(src_ref))
    cite_text = " · ".join(cite_bits)
    if cite_text and src_url:
        source_html = (f"<div class=muted style=\"font-size:.8rem\">source</div>"
                       f"<div><a href=\"{_esc(src_url)}\">{cite_text} ↗</a></div>")
    elif cite_text:
        source_html = (f"<div class=muted style=\"font-size:.8rem\">source</div>"
                       f"<div>{cite_text}</div>")
    else:
        source_html = ""
    # Related seal cross-link, if this card carries one (found only).
    seal_hash = str((card.get("extra") or {}).get("seal_hash") or card.get("source_hash") or "").strip()
    canonical = f"/card/{_esc(card_id)}"
    desc = _esc((body_txt or (card.get("title") or ""))[:200])
    # schema.org CreativeWork — a citation-carrying record, machine-readable.
    ld: Dict[str, Any] = {"@context": "https://schema.org", "@type": "CreativeWork",
                          "identifier": card_id, "name": card.get("title") or card_id}
    if body_txt:
        ld["text"] = body_txt
    if src_label or src_ref or src_url:
        citation = {"@type": "CreativeWork"}
        if src_label:
            citation["name"] = src_label
        if src_url:
            citation["url"] = src_url
        if src_ref:
            citation["citation"] = src_ref
        ld["citation"] = citation
    ld_json = _esc(_json.dumps(ld, ensure_ascii=False))
    related = (f"<p style=\"margin-top:.6rem\"><a href=\"/search?q={_esc((card.get('title') or '')[:60])}\">"
               f"related in the keeping ↗</a>")
    if seal_hash:
        related += f" · <a href=\"/s/{_esc(seal_hash)}\">its seal ↗</a>"
    related += f" · <a href=\"/card?id={_esc(card_id)}\">raw JSON ↗</a></p>"
    html = (f"{head}<title>{title} · Narrow Highway</title>"
            f"<link rel=canonical href=\"{canonical}\">"
            f"<meta name=description content=\"{desc}\">"
            f"<meta property=\"og:title\" content=\"{title}\">"
            f"<meta property=\"og:description\" content=\"{desc}\">"
            f"<meta property=\"og:type\" content=article>"
            f"<meta property=\"og:url\" content=\"{canonical}\">"
            f"<meta name=\"twitter:card\" content=\"summary\">"
            f"<script type=\"application/ld+json\">{ld_json}</script></head><body>"
            f"{_site_header('<a href=/search>Search</a><a href=/#verify>Verify</a>')}<main class=wrap>"
            f"<h1>{title}</h1>{body_html}"
            f"<section class=card>{source_html}"
            f"<div class=muted style=\"font-size:.8rem;margin-top:.5rem\">card id</div>"
            f"<div class=mono style=\"word-break:break-all\">{_esc(card_id)}</div>{related}</section>"
            # Local connection-graph — progressive enhancement (hidden until JS finds a real
            # neighborhood, so the crawlable page stands alone). Each edge links to its seal.
            f"<section class=card id=nhconn data-cid=\"{_esc(card_id)}\" style=\"margin-top:1rem;display:none\">"
            f"<div class=muted style=\"font-size:.8rem\">connections</div>"
            f"<canvas id=nhlg role=img aria-label=\"Connection graph — this card and its linked records\" style=\"width:100%;height:320px;display:block;margin:.4rem 0\"></canvas>"
            f"<p class=muted id=nhlg-cap style=\"font-size:.75rem\"></p></section>"
            f"<footer class=site><p>A record from the keeping — found and cited, never generated. "
            f"<a href=/search>Search the keeping →</a></p></footer></main>"
            f"<script src=/graph.js defer></script>"
            f"<script>addEventListener('load',function(){{var s=document.getElementById('nhconn');"
            f"if(window.NHGraph&&s)NHGraph.local('nhconn','nhlg',s.getAttribute('data-cid'));}});</script>"
            f"</body></html>")
    return 200, html


_SITEMAP_PAGES = ("/", "/ask.html", "/bible.html", "/read.html", "/characters.html",
                  "/prophecy.html", "/journal.html", "/map.html", "/steward.html",
                  "/community.html", "/library.html", "/guarantees.html", "/collapse.html",
                  "/seeds.html", "/seal.html")


def build_sitemap(base_url: str) -> str:
    """A crawlable sitemap of the main pages + EVERY public card permalink (/card/<id>) —
    so the ~5k citable, JSON-LD-bearing card pages are discoverable by search + LLM crawlers
    instead of orphaned behind JS. base_url is per-host (each surface advertises its own)."""
    urls = [f"{base_url}{p}" for p in _SITEMAP_PAGES]
    try:
        for c in corpus.default_corpus().cards.values():
            if c.get("kind") == "note" and corpus.is_public(c):
                urls.append(f"{base_url}/card/{c.get('id')}")
    except Exception:
        pass
    rows = "\n".join(f"  <url><loc>{_esc(u)}</loc></url>" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{rows}\n</urlset>\n")


def dispatch(method: str, path: str, query: Dict[str, str], body: Any,
             config: EngineConfig, session_gate_open: bool = False) -> Response:
    """Pure request dispatch — (method, path, query, body, config, session_gate_open) → (status, payload).

    session_gate_open carries the Gate across a conversation: once the person's own seeking has
    opened the door (Ask/Seek/Knock — see /ask), the witness content is surfaced on the secular
    reach too, not just the witness face."""
    method = (method or "GET").upper()
    path = path.rstrip("/") or "/"
    surface = config.surface
    # The Gate (Mt 7:7): witness content opens on the witness face, OR once the conversation has
    # opened the gate. The FOUNDATION is load-bearing on both faces regardless; this governs only
    # what is surfaced. We present the path; we do not cross it.
    allow_witness = config.witness_surfaced or session_gate_open

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
        prior_open = bool(rec and rec.get("gate_open")) or (surface == "witness") or session_gate_open
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
        # Fellowship: if others are already studying this, point to them — the conversation opens into
        # real community (John 3:30). FOUND, never generated; off to the side; never breaks the answer;
        # never for crisis (help-first stays clean). Only when the door is open (they're seeking).
        if r.get("kind") != "crisis" and (gate_open or r.get("kind") in ("ultimate", "scripture")):
            try:
                from .. import groups as _groups
                fs = _groups.suggest(text).get("groups", [])
                if fs:
                    r["fellowship"] = fs
            except Exception:  # noqa: BLE001 — a pointer to community is a bonus, never load-bearing
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

    # Groups — pseudonymous shared-study groups (community: connect around what you study). NOT gated
    # (an opt-in connection surface, both faces); anonymity is the floor (handles, never PII); the
    # Coach/children are a SEPARATE, never-joined surface. Member content is attributed, not verified.
    if method == "POST" and path == "/groups":
        if not isinstance(body, dict) or not str(body.get("topic") or "").strip():
            return _err(400, "topic required")
        from .. import groups
        return _ok(groups.create_group(str(body["topic"]), title=str(body.get("title") or ""),
                                       description=str(body.get("description") or ""),
                                       creator_id=str(body.get("subject_id") or ""),
                                       handle=str(body.get("handle") or "")))
    if method == "GET" and path == "/groups":
        from .. import groups
        return _ok(groups.list_groups(query.get("q") or ""))
    if method == "GET" and path == "/group":
        from .. import groups
        g = groups.get_group((query.get("id") or "").strip())
        return _ok(g) if g is not None else _err(404, "group not found")
    if method == "POST" and path == "/group/join":
        if not isinstance(body, dict) or not str(body.get("id") or "").strip():
            return _err(400, "id required")
        from .. import groups
        g = groups.join_group(str(body["id"]), member_id=str(body.get("subject_id") or ""),
                              handle=str(body.get("handle") or ""))
        return _ok(g) if g is not None else _err(404, "group not found")
    if method == "POST" and path == "/group/contribute":
        if not isinstance(body, dict) or not str(body.get("id") or "").strip():
            return _err(400, "id required")
        from .. import groups
        r = groups.contribute(str(body["id"]), member_id=str(body.get("subject_id") or ""),
                              handle=str(body.get("handle") or ""), text=str(body.get("text") or ""),
                              kind=str(body.get("kind") or "note"), topics=body.get("topics") or [],
                              refs=body.get("refs") or [], private_key=body.get("private_key"))
        return _ok(r) if r is not None else _err(404, "group not found")

    # Coach — the Shepherd as a K-3 reading tutor. READ-ONLY teaching is the floor (NOT gated); it
    # finds + presents the operator's authored curriculum, never generates a lesson, never grades a child.
    if method == "POST" and path == "/coach/mastery":
        # Seal an HONEST INTEGER count of completed units — the moat's math applied to progress, never
        # to the person. Mirrors /steward/budget EXACTLY: hand the derivation-shaped result to
        # receipts.attach (it reads verdict+trail; re-runs NO verifier), so no derivation import here.
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import coach, receipts
        out = coach.mastery(body.get("completed") or [])
        m = coach.mastery_result(body.get("completed") or [])
        out["seal"] = receipts.attach(m["result"], config=config, domain="mathematics").get("seal")
        telemetry.record("coach", surface=surface, op="mastery", sealed=bool(out.get("seal")))
        return _ok(out)

    # Sovereign, portable identity — the person owns a keypair; we reference only the fingerprint.
    # SOVEREIGNTY CONTRACT: the private_key is returned ONCE to the client and NEVER persisted/logged.
    if method == "POST" and path == "/identity/create":
        from .. import identity
        idn = identity.create_identity()  # full dict incl private_key returned ONCE; NOT stored here
        telemetry.record("identity", surface=surface, op="create",
                         signing=bool(idn.get("signing_available")))
        return _ok(idn)

    if method == "POST" and path == "/identity/verify":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import identity
        ok = identity.verify(str(body.get("public_key") or ""), body.get("message") or "",
                             str(body.get("sig") or ""))
        return _ok({"ok": bool(ok)})

    # Badges — a re-checkable receipt pointing at N seals that still stand. NEVER a competency claim.
    if method == "POST" and path == "/badges":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        seal_hashes = body.get("seal_hashes")
        if not isinstance(seal_hashes, list):
            return _err(400, "seal_hashes (list) required")
        from .. import badges
        # private_key (if passed) is in-memory only — used to attest, NEVER persisted or echoed back.
        out = badges.issue_badge(seal_hashes, subject_id=body.get("subject_id"),
                                 title=str(body.get("title") or ""),
                                 private_key=body.get("private_key"))
        telemetry.record("badge", surface=surface, op="issue", checks=int(out.get("checks", 0)))
        return _ok(out)

    if method == "POST" and path == "/self-attest":
        # A person's OWN words — a DISTINCTLY TYPED record that can NEVER count as a sealed check.
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import badges
        return _ok(badges.self_attest(str(body.get("subject_id") or ""),
                                      str(body.get("statement") or ""),
                                      study=body.get("study")))

    # Shared study — a superposition stack: one card lives once, referenced; portable, optionally signed.
    if method == "POST" and path == "/study":
        if not isinstance(body, dict) or not str(body.get("key") or "").strip():
            return _err(400, "key required")
        from .. import badges
        return _ok(badges.study_create(str(body["key"]), body.get("cards") or []))

    if method == "POST" and path == "/study/export":
        if not isinstance(body, dict) or not str(body.get("key") or "").strip():
            return _err(400, "key required")
        from .. import badges
        # private_key (if passed) is in-memory only — used to sign the bundle, NEVER persisted/echoed.
        return _ok(badges.study_export(str(body["key"]), private_key=body.get("private_key")))

    if method == "POST" and path == "/study/import":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import badges
        return _ok(badges.study_import(body.get("bundle") or body,
                                       study_key=body.get("key"),
                                       verify_signature=bool(body.get("verify_signature"))))

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

    # The map — the connection-graph over the keeping (found edges, each sealed). Public on
    # both surfaces (one shared library). scope=overview (default) | shelf | card.
    if method == "GET" and path == "/graph":
        from .. import graph as _graph
        scope = (query.get("scope") or "overview").strip()
        if scope == "overview":
            return _ok(_graph.overview())
        if scope == "shelf":
            sh = (query.get("shelf") or "").strip()
            if not sh:
                return _err(400, "shelf required")
            return _ok(_graph.shelf_graph(sh))
        if scope == "card":
            cid = (query.get("id") or "").strip()
            if not cid:
                return _err(400, "id required")
            r = _graph.neighborhood(cid)
            return _ok(r) if r is not None else _err(404, "card not found")
        return _err(400, "unknown scope")
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

    # Coach GETs — read-only teaching, NOT gated (teaching is the floor on both surfaces). ?subject=
    # selects the path (read / mcguffey / aesop / founding / pilgrims / es); default is the reading path.
    if method == "GET" and path == "/coach/subjects":
        from .. import coach
        return _ok(coach.subjects())
    if method == "GET" and path == "/coach/overview":
        from .. import coach
        return _ok(coach.overview(query.get("subject") or coach.DEFAULT_SUBJECT))
    if method == "GET" and path == "/coach/unit":
        from .. import coach
        return _ok(coach.unit(query.get("id", ""), query.get("subject") or coach.DEFAULT_SUBJECT))
    if method == "GET" and path == "/coach/next":
        from .. import coach
        return _ok(coach.next_unit(query.get("after"), query.get("subject") or coach.DEFAULT_SUBJECT))
    if method == "GET" and path == "/coach/recommend":
        # Adaptive next: ?done=id1,id2,...&subject= (the caller holds progress — no personal data here).
        from .. import coach
        done = [x for x in (query.get("done") or "").split(",") if x.strip()]
        return _ok(coach.recommend(done, query.get("subject") or coach.DEFAULT_SUBJECT))
    if method == "GET" and path == "/coach/guidance":
        from .. import coach
        return _ok(coach.guidance())

    # Identity GETs — capabilities + fingerprint derivation (public key only; no secret involved).
    if method == "GET" and path == "/identity/fingerprint":
        from .. import identity
        pk = (query.get("public_key") or "").strip()
        if not pk:
            return _err(400, "public_key required")
        return _ok({"id": identity.fingerprint(pk)})
    if method == "GET" and path == "/identity/describe":
        from .. import identity
        return _ok(identity.describe())

    # Badge verify (machine JSON) — re-checks a badge from the store; 404 when it does not stand.
    if method == "GET" and path == "/badges":
        h = (query.get("hash") or "").strip()
        if not h:
            return _err(400, "hash required")
        from .. import badges
        rec = badges.verify_badge(h)
        return _ok(rec) if rec.get("ok") else _err(404, "badge not found")

    # Study resolve (machine JSON) — the cards referenced by a study (they live once).
    if method == "GET" and path == "/study":
        key = (query.get("key") or "").strip()
        if not key:
            return _err(400, "key required")
        from .. import badges
        return _ok(badges.study_get(key))

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
        if not allow_witness:
            return _gate_closed()
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.resolve_ref(ref))

    if method == "GET" and path == "/passage":
        # Read a passage (verse / range / whole chapter) — the Bible reading primitive.
        if not allow_witness:
            return _gate_closed()
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.read_passage(ref))

    if method == "GET" and path == "/word_study":
        if not allow_witness:
            return _gate_closed()
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_study(s))

    if method == "GET" and path == "/cross_refs":
        if not allow_witness:
            return _gate_closed()
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.cross_references(ref))

    if method == "GET" and path == "/word_occurrences":
        if not allow_witness:
            return _gate_closed()
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_occurrences(s))

    if method == "GET" and path == "/original":
        if not allow_witness:
            return _gate_closed()
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.original_words(ref))

    if method == "GET" and path == "/canon":
        # The canon as concentric layers — the 66 core + disputed books, framed, never merged.
        if not allow_witness:
            return _gate_closed()
        from .. import canon
        book = (query.get("book") or "").strip()
        return _ok(canon.canon_status(book) if book else canon.overview())

    if method == "GET" and path == "/commentary":
        # Public-domain, attributed commentary (Matthew Henry) — the father's own words, found.
        if not allow_witness:
            return _gate_closed()
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from .. import commentary
        return _ok(commentary.for_ref(ref, source=(query.get("source") or commentary.DEFAULT_SOURCE)))

    if method == "GET" and path == "/tsk":
        # Editorial cross-references (openbible.info, CC BY — expansion of the public-domain TSK).
        if not allow_witness:
            return _gate_closed()
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
        if not allow_witness:
            return _gate_closed()
        name = (query.get("name") or "").strip()
        if not name:
            return _err(400, "name required")
        from .. import characters
        rec = characters.get(name)
        return _ok(rec) if rec is not None else _err(404, "not found in Easton's")

    if method == "GET" and path == "/characters":
        if not allow_witness:
            return _gate_closed()
        from .. import characters
        try:
            limit = int(query.get("limit", "100"))
        except (TypeError, ValueError):
            limit = 100
        return _ok(characters.browse(letter=(query.get("letter") or None),
                                     search=(query.get("search") or None), limit=limit))

    if method == "GET" and path == "/prophecy":
        # Christ-signpost traces — attributed, verdict CONCORDANT/MIXED, NEVER HOLDS (a signpost, not a proof).
        if not allow_witness:
            return _gate_closed()
        from .. import prophecy
        tid = (query.get("id") or "").strip()
        if tid:
            rec = prophecy.get(tid)
            return _ok(rec) if rec is not None else _err(404, "trace not found")
        q = (query.get("q") or "").strip()
        return _ok(prophecy.search(q) if q else prophecy.list_traces())

    if method == "GET" and path == "/seeds":
        # Seeds of the Word — the Areopagus / logos spermatikos pass. Attributed, CONCORDANT/signpost,
        # NEVER HOLDS; the idol named and refused, the Source named — Jesus Christ (Acts 17; 1 John 4:1-3).
        if not allow_witness:
            return _gate_closed()
        from .. import seeds as seeds_mod
        sid = (query.get("id") or "").strip()
        if sid:
            rec = seeds_mod.get(sid)
            return _ok(rec) if rec is not None else _err(404, "seed not found")
        q = (query.get("q") or "").strip()
        if q:
            return _ok(seeds_mod.search(q))
        trad = (query.get("tradition") or "").strip()
        base = seeds_mod.list_seeds(trad)
        base["areopagus"] = seeds_mod.method()
        return _ok(base)

    return _err(404, "not found")


# ── Route registry — ONE declaration per route ───────────────────────────
# Each entry carries a route's methods + metadata: api = a JSON/API GET that must be served
# even when the static site is mounted (else it would fall through to the site handler);
# rl = rate-limited; serve = handled in the serve() Handler rather than dispatch() (e.g. the
# streamed /speak, the site-or-json /card.html). The two sets the server actually consults
# (_API_GET_PATHS, RATELIMITED) are DERIVED below, so a route's metadata lives in exactly one
# place. tests/test_routes.py locks the derivation to the historical values AND asserts every
# path dispatch() handles is registered here — so the two can never silently drift apart.
ROUTES = [
    {"path": "/", "methods": ("GET",)},
    {"path": "/health", "methods": ("GET",), "api": True},
    {"path": "/identity", "methods": ("GET",), "api": True},
    {"path": "/verify", "methods": ("POST",), "rl": True},
    {"path": "/derivation/verify", "methods": ("POST",), "rl": True},
    {"path": "/ask", "methods": ("POST",), "rl": True},
    {"path": "/journal", "methods": ("GET", "POST"), "api": True},
    {"path": "/steward/budget", "methods": ("POST",)},
    {"path": "/steward/cost-destroyed", "methods": ("POST",)},
    {"path": "/steward/ask", "methods": ("POST",)},
    {"path": "/groups", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/group", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/group/join", "methods": ("POST",), "rl": True},
    {"path": "/group/contribute", "methods": ("POST",), "rl": True},
    {"path": "/coach/mastery", "methods": ("POST",), "rl": True},
    {"path": "/identity/create", "methods": ("POST",), "rl": True},
    {"path": "/identity/verify", "methods": ("POST",), "rl": True},
    {"path": "/badges", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/self-attest", "methods": ("POST",)},
    {"path": "/study", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/study/export", "methods": ("POST",), "rl": True},
    {"path": "/study/import", "methods": ("POST",), "rl": True},
    {"path": "/mcp", "methods": ("POST",), "rl": True},
    {"path": "/search", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/cards/stats", "methods": ("GET",), "api": True},
    {"path": "/cards", "methods": ("GET",), "api": True},
    {"path": "/card", "methods": ("GET",), "api": True},
    {"path": "/daily", "methods": ("GET",), "api": True},
    {"path": "/card/connections", "methods": ("GET",), "api": True},
    {"path": "/graph", "methods": ("GET",), "api": True},
    {"path": "/locate", "methods": ("GET",), "api": True},
    {"path": "/library/health", "methods": ("GET",), "api": True},
    {"path": "/pronounce", "methods": ("GET",), "api": True},
    {"path": "/thread", "methods": ("DELETE", "GET"), "api": True},
    {"path": "/threads", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/threads/search", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/thread/verify", "methods": ("GET",), "api": True},
    {"path": "/journal/dates", "methods": ("GET",), "api": True},
    {"path": "/steward", "methods": ("GET",), "api": True},
    {"path": "/coach/subjects", "methods": ("GET",), "api": True},
    {"path": "/coach/overview", "methods": ("GET",), "api": True},
    {"path": "/coach/unit", "methods": ("GET",), "api": True},
    {"path": "/coach/next", "methods": ("GET",), "api": True},
    {"path": "/coach/recommend", "methods": ("GET",), "api": True},
    {"path": "/coach/guidance", "methods": ("GET",), "api": True},
    {"path": "/identity/fingerprint", "methods": ("GET",), "api": True},
    {"path": "/identity/describe", "methods": ("GET",), "api": True},
    {"path": "/grid", "methods": ("GET",), "api": True},
    {"path": "/grid/dimension", "methods": ("GET",), "api": True},
    {"path": "/seal", "methods": ("GET",), "api": True},
    {"path": "/resolve", "methods": ("GET",), "api": True},
    {"path": "/passage", "methods": ("GET",), "api": True},
    {"path": "/word_study", "methods": ("GET",), "api": True},
    {"path": "/cross_refs", "methods": ("GET",), "api": True},
    {"path": "/word_occurrences", "methods": ("GET",), "api": True},
    {"path": "/original", "methods": ("GET",), "api": True},
    {"path": "/canon", "methods": ("GET",), "api": True},
    {"path": "/commentary", "methods": ("GET",), "api": True},
    {"path": "/tsk", "methods": ("GET",), "api": True},
    {"path": "/character", "methods": ("GET",), "api": True},
    {"path": "/characters", "methods": ("GET",), "api": True},
    {"path": "/prophecy", "methods": ("GET",), "api": True},
    {"path": "/seeds", "methods": ("GET",), "api": True},
    {"path": "/card.html", "methods": ("GET",), "api": True, "serve": True},
    {"path": "/speak", "methods": ("POST",), "rl": True, "serve": True},
]

# The JSON/API GET paths (served even with a static site mounted) — DERIVED from ROUTES.
_API_GET_PATHS = frozenset(r["path"] for r in ROUTES if r.get("api"))
# The rate-limited paths (consulted in serve()) — DERIVED from ROUTES.
RATELIMITED = tuple(r["path"] for r in ROUTES if r.get("rl"))


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
    # RATELIMITED is derived from the ROUTES registry (module-level) — single source of truth.

    class Handler(BaseHTTPRequestHandler):
        # Don't advertise the exact Python/http.server version (aids targeted attacks).
        server_version = "NarrowHighway"
        sys_version = ""

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
            # traversal guard (is_relative_to, NOT startswith — a sibling dir whose name merely
            # begins with the site path must not pass) + existence
            if not fp.is_relative_to(site) or not fp.is_file():
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
            """Rate-limit key: the REAL client. Caddy (the single trusted proxy) APPENDS the peer
            to X-Forwarded-For, so the real client is the LAST hop — a client-supplied XFF prefix
            can't forge a fresh bucket. Falls back to the socket peer if XFF is absent."""
            parts = [p.strip() for p in (self.headers.get("x-forwarded-for") or "").split(",") if p.strip()]
            return (parts[-1] if parts else "") or (self.client_address[0] if self.client_address else "?")

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
            # Catch-all: any unhandled exception becomes a clean JSON 500, never a dropped
            # connection with a stderr traceback (which would leak internals + defeat the
            # Server-header hardening). The server also silences handle_error (see _QuietServer).
            try:
                self._do_inner(method)
            except Exception:
                try:
                    self._json(500, {"error": "internal error"})
                except Exception:
                    pass

        def _do_inner(self, method: str) -> None:
            u = urlparse(self.path)
            # DoS guard: reject oversized bodies before reading a single byte
            if method == "POST":
                try:
                    clen = int(self.headers.get("content-length") or 0)
                except ValueError:
                    clen = 0
                if clen > MAX_BODY:
                    return self._json(413, {"error": f"request body too large (> {MAX_BODY} bytes)"})
            if method == "GET" and u.path in ("/robots.txt", "/sitemap.xml"):
                # Surface-aware: each host advertises ITS OWN sitemap + absolute URLs, so the
                # .com reach is crawled (not pointed at .org), and every card permalink is listed.
                host = (self.headers.get("host") or "narrowhighway.com").split(":")[0] or "narrowhighway.com"
                base = "https://" + host
                if u.path == "/robots.txt":
                    b = ("User-agent: *\nAllow: /\nDisallow: /keep\nDisallow: /keep.html\n"
                         f"Sitemap: {base}/sitemap.xml\n").encode("utf-8")
                    ctype = "text/plain; charset=utf-8"
                else:
                    b = build_sitemap(base).encode("utf-8")
                    ctype = "application/xml; charset=utf-8"
                self.send_response(200)
                self.send_header("content-type", ctype)
                self.send_header("x-content-type-options", "nosniff")
                self.send_header("content-length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)
                return
            if method == "GET" and u.path in ("/keep", "/keep.html", "/keep.json"):
                return self._keep(u)  # operator-gated dashboard
            if method == "GET" and u.path.startswith("/s/"):  # server-rendered citable receipt
                h = u.path[3:].split("/")[0].strip()
                status, html = render_seal_html(h, cas.fetch(h))
                return self._html(status, html)
            if method == "GET" and u.path.startswith("/b/"):  # server-rendered citable badge (mirrors /s/)
                h = u.path[3:].split("/")[0].strip()
                from .. import badges as _badges
                status, html = render_badge_html(h, _badges.verify_badge(h))
                return self._html(status, html)
            # Card pages (server-rendered HTML). CRITICAL: /card/connections stays JSON — match it
            # BEFORE the generic /card/<id> HTML prefix. /card (no slug) also stays JSON (falls through).
            if method == "GET" and u.path == "/card.html":  # ?id=<id>  → HTML
                cid = (parse_qs(u.query).get("id", [""]) or [""])[0].strip()
                status, html = render_card_html(cid, corpus.get_card(cid) if cid else None)
                return self._html(status, html)
            if (method == "GET" and u.path.startswith("/card/")
                    and u.path != "/card/connections"):  # /card/<id>  → HTML (JSON routes excluded)
                cid = u.path[len("/card/"):].split("/")[0].strip()
                status, html = render_card_html(cid, corpus.get_card(cid) if cid else None)
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
            if u.path == "/speak":  # optional voice ceiling — returns audio/mpeg, else 503 -> floor
                text = (parse_qs(u.query).get("text", [""]) or [""])[0]
                if method == "POST":
                    n = int(self.headers.get("content-length") or 0)
                    raw = self.rfile.read(n) if n else b""
                    try:
                        text = (json.loads(raw or b"{}") or {}).get("text", text)
                    except (ValueError, TypeError):
                        pass
                from ..voice import speak as _speak
                res = _speak(text)
                if not res:
                    return self._json(503, {"audio": False,
                                            "reason": "voice ceiling unavailable — use the browser floor"})
                audio, state = res
                self.send_response(200)
                self.send_header("content-type", "audio/mpeg")
                self.send_header("x-content-type-options", "nosniff")
                self.send_header("cache-control", "public, max-age=31536000, immutable")
                self.send_header("x-voice-cache", state)
                self.send_header("content-length", str(len(audio)))
                self.end_headers()
                self.wfile.write(audio)
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
            # The Gate carried across the conversation: a simple session flag set by the server when
            # /ask opens the door (Ask/Seek/Knock). Once open, the witness content is surfaced on
            # this reach too. Not an access secret — the gate opens on seeking; this only remembers it.
            session_gate_open = "nh_gate=open" in (self.headers.get("cookie") or "")
            status, payload = dispatch(method, u.path, q, body, config, session_gate_open=session_gate_open)
            extra = None
            if (u.path == "/ask" and isinstance(payload, dict) and payload.get("gate_open")
                    and not session_gate_open):
                extra = {"Set-Cookie": "nh_gate=open; Path=/; Max-Age=31536000; SameSite=Lax"}
            self._json(status, payload, extra)

        def do_GET(self) -> None:
            self._do("GET")

        def do_POST(self) -> None:
            self._do("POST")

        def do_DELETE(self) -> None:
            self._do("DELETE")

        def log_message(self, *args) -> None:  # quiet
            pass

    class _QuietServer(ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            pass  # no stderr tracebacks (info leak); handlers already return clean JSON 500s

    # Warm the heavy singletons at boot (behind their locks) so the first request skips the
    # ~5s corpus+graph build, and concurrent first-hits can't stampede it.
    try:
        corpus.default_corpus()
        from .. import graph as _graph_warm
        _graph_warm._graph()
    except Exception:
        pass

    where = f" + site {site}" if site else ""
    print(f"Narrow Highway API ({surface}) on http://{host}:{port}{where}")
    _QuietServer((host, port), Handler).serve_forever()
