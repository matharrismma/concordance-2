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
from urllib.parse import parse_qsl, urlencode

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


# WHAT THE GATE IS FOR — AND WHAT IT NEVER WAS.
#
# Matt, 2026-07-31, in three passes:
#   "I think seeing them is fine. Understanding the deeper meaning comes after the gate."
#   "We don't need to refuse use. We refuse abuse."
#   "We don't hide knowledge. We aren't a secret society. Everyone is a part of the group.
#    They experience what they want of it."
#
# The Gate held twenty paths. The first pass freed fifteen — the text and its reference apparatus,
# which are seeing. The third pass freed the last five, and it is the one that settles the matter:
# a person is not made ready by being refused. Everyone is already part of the group; the depth
# they go to is theirs to choose, not ours to ration.
#
# So NOTHING here is behind the Gate. This set is empty and stays empty, and the test walks the
# code to prove it. The Gate itself remains — as the INVITATION it always should have been. The
# conversation that opens into Scripture still opens; ask.py still meets a reader in kind; the
# .org surface still leads with the witness and .com still leads with the proof. What is gone is
# the refusal.
#
# Abuse is still refused, by the instruments built for it: the read and write ceilings, the named
# crawler refusals in robots.txt, the operator token, the steward warrants with their terms, the
# moderation floor. And what is NOT knowledge is still governed — the operator console is
# authority, a member's private shelf is theirs, and the mesh asks for a confession because
# joining a fellowship is a covenant, not a lookup.
AFTER_THE_GATE = frozenset()


def _gate_closed() -> Response:
    """A path of UNDERSTANDING reached before the person's seeking has opened the gate
    (Ask/Seek/Knock, Mt 7:7). Still 404 — the meaning is not surfaced yet — but MARKED, so a client
    can invite them to open it rather than showing a dead end. We present the path; we never cross
    it. The text itself is never behind this: see AFTER_THE_GATE."""
    return 404, {"error": "gate_closed", "gate": "closed",
                 "detail": "The deeper reading opens as you seek it — bring up Scripture in the "
                           "conversation, and the way opens. The text itself is already yours."}


def _card_brief(c: dict) -> Dict[str, Any]:
    """A search hit, with enough to know what may be CLAIMED from it.

    Traffic, measured 2026-07-30: `/search` carries ~34k requests across the three hosts (re-measured 2026-08-01 with FULL logs (the earlier figure was read from tv.access.log alone — the only log file readable without sudo — and covered 9% of traffic)) and agents are a top client of
    all traffic is ClaudeBot. The brief carried title, shelf, and a snippet — nothing about
    AUTHORITY. So an agent had to fetch the full card just to learn whether the thing it had found
    was a sealed record, a public-domain source, or a member's own opinion. That is a wasted
    round-trip on the hottest path, and worse, it is the moment where an agent in a hurry cites
    something at the wrong weight.

    `authority_tier` and `generated` are the two facts that govern what a reader may say next, so
    they travel with the hit. Both are read straight off the card — nothing new is computed, and
    nothing is asserted that the card does not already carry.
    """
    src = c.get("source") or {}
    return {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
            "surface": c.get("surface"), "snippet": (c.get("body", "") or "")[:200],
            "authority_tier": src.get("authority_tier") or "",
            "source": src.get("label") or "",
            "generated": bool(c.get("generated", False))}


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


# THE TWO KEEPERS. Matt, 2026-08-01: ".tv isn't the priority. We focus on .com and then .org." —
# and, the same night: "We could also make the .org keep the receipts."
#
# The pages used PATH-relative canonicals, so the same page served on .com, .tv and api. declared
# three different "true addresses" and split its standing three ways. Now each addressable thing
# names its ONE keeper, whichever door served it — concentration, not redirection:
#   the LIBRARY lives on .com  — cards, the corpus, the engine;
#   the RECORD lives on .org   — seals and badges. The witness keeps the testimony; that is the
#   job description matching the domain name, and receipts.py already minted witness-surface
#   cite_urls onto .org before this constant existed.
# Old sealed records carry .com cite_urls INSIDE their hashed content — unrewritable by
# construction, and still resolving (every door serves /s/). New records name their keeper.
# THE SEARCH CEILING — announced, never silent.
#
# Measured on the live secular host, 2026-08-01: `limit=1,000,000,000` returned 5,007 results in
# 1.67 MB and 5.1 seconds of server CPU, for a 200-byte request. The read rate limit is deliberately
# generous (R4 — we asked agents to use this surface), so nothing else stood between a cheap request
# and an expensive answer. Four other routes in this file already clamp (500, 50, 50, 25); the two
# BUSIEST doors — GET /search and the MCP `search` tool — were the two with no ceiling at all. That
# was an oversight, not a decision.
#
# 200 is eight times the default and more than any reader needs: we refuse abuse, not use. And when
# the ceiling is applied the answer SAYS SO (`limit_capped`), because a cap that does not report
# itself reads as "that was all of them" — the same lie as a silently truncated measurement.
SEARCH_MAX = 200


def bounded_limit(raw, default: int):
    """(limit, capped-notice-or-None) — clamp a caller's `limit` and hand back what to disclose."""
    try:
        asked = int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError):
        asked = default
    if asked < 1:
        asked = default
    served = min(asked, SEARCH_MAX)
    if served < asked:
        return served, {"asked": asked, "served": served,
                        "why": f"this door serves at most {SEARCH_MAX} results per request; "
                               f"page with a narrower query rather than a larger limit"}
    return served, None


CANONICAL_LIBRARY = "https://narrowhighway.com"
CANONICAL_WITNESS = "https://narrowhighway.org"
CANONICAL_HOST = CANONICAL_LIBRARY   # cards and pages of the library


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

    # WHO HAS BORNE WITNESS. The attestation store existed but no reader of a receipt could see it —
    # and this page is precisely where someone lands to CHECK a claim (it is what cite_url points at).
    # A witness nobody can see is not a witness. Each signature is re-verified as this renders; an
    # entry that no longer checks is shown as broken rather than quietly dropped.
    witness_html = ""
    try:
        from .. import attest as _attest
        w = _attest.witnesses(content_hash)
        n = int(w.get("witnesses") or 0)
        bad = int(w.get("invalid") or 0)
        if n or bad:
            items = "".join(
                f"<div class=result><span class=s>{'✓' if a.get('valid') else '✗'}</span> "
                f"<span class=t>{_esc(a.get('fingerprint') or (a.get('pubkey') or '')[:16])}</span>"
                f"<div class=trail>{_esc(a.get('detail') or '')}</div></div>"
                for a in (w.get("attestations") or []))
            established = ("<b>two or three witnesses</b> — this begins to be established "
                           "(Deuteronomy 19:15)" if n >= 2 else
                           "<b>one witness</b> — a claim, not yet established (Deuteronomy 19:15 "
                           "asks two or three)")
            warn = (f" <span class=muted>{bad} attestation(s) no longer verify.</span>" if bad else "")
            witness_html = (f"<section><h2>Who has borne witness</h2>"
                            f"<p class=lede>{established}.{warn} We count the witnesses and show "
                            f"their keys; we do not tell you the matter is settled — weigh them "
                            f"yourself. Every signature here was re-checked as this page rendered.</p>"
                            f"{items}</section>")
    except Exception:  # noqa: BLE001 — a receipt renders with or without an attestation store
        witness_html = ""
    desc = (f"A re-checkable verification receipt — verdict {_esc(overall)}, sealed {short}. "
            f"Narrow Highway: every answer is a receipt, not 'trust me'.")
    html = (f"{head}<title>Receipt {short}… · {label} · Narrow Highway</title>"
            f"<meta name=description content=\"{desc}\">"
            f"<meta property=\"og:title\" content=\"Verification receipt · {label}\">"
            f"<meta property=\"og:description\" content=\"{desc}\">"
            f"<link rel=canonical href=\"{CANONICAL_WITNESS}/s/{_esc(content_hash)}\">"
            f"<meta property=\"og:type\" content=article>"
            f"<meta name=\"twitter:card\" content=\"summary\"></head><body>"
            f"{_site_header('<a href=/#verify>Verify</a><a href=/seal.html>Seal</a>')}<main class=wrap>"
            f"<h1>The receipt</h1><div class=\"verdict {vcls}\" style=\"font-size:1.4rem\">{label}</div>"
            f"<p class=lede>A permanent, tamper-evident record of a verification. The content hash IS "
            f"the proof — re-fetch it and the bytes must match, or it is not this record.</p>"
            f"<section><h2>Worked trail</h2>{trail_html}</section>"
            f"{witness_html}"
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


def _unchecked_live(card_id: str, ask: Dict[str, Any]) -> Dict[str, Any]:
    """Put the LIVE answer count onto a pure ask block. ONE copy, used by both surfaces.

    `present.derive` is pure and cached by (id, updated_at), so the block it returns can only ever
    say "nobody has checked this" — it cannot see the log, and the cache would freeze that sentence
    in place even if it could. Reading the fold belongs to a route, which is already doing I/O.
    Written once and shared, because the first version of this lived only in the HTML renderer and
    the JSON surface quietly kept telling agents nothing had been checked.
    """
    from .. import unchecked as _u
    st = _u.state_of(card_id)
    if st["disputed"]:
        head = "A reader has disputed this card."
    elif st["answered"]:
        head = f"Checked by {st['checked_by']} reader(s) — you may add your own."
    else:
        head = ask.get("headline", "")
    return dict(ask, headline=head, open=not st["answered"],
                checked_by=st["checked_by"], disputed_by=st["disputed_by"],
                disputed=st["disputed"])


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
    # An ISBE stub opens into the FULL 1915 article at render time (found, attributed — the
    # guarantee reaches the reader; the resident card stays ~600 bytes). If the acquisition
    # db cannot answer, the stub renders — a shorter answer, never a broken page.
    _isbe_head = str((card.get("extra") or {}).get("isbe_headword") or "").strip()
    if _isbe_head:
        from .. import isbe as _isbe_mod
        _full = _isbe_mod.get(_isbe_head)
        if _full and _full.get("text"):
            body_txt = _full["text"]
    if _isbe_head and "\n" in body_txt:
        body_html = "".join(f"<p>{_esc(p)}</p>" for p in body_txt.split("\n\n") if p.strip())
    else:
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
    # A SEAL, AND ONLY A SEAL. This used to fall back to `source_hash`, and the fallback was a
    # false claim: a `source_hash` fingerprints the SOURCE TEXT, while a seal is a sealed
    # verification record in the CAS. They are different objects. Measured 2026-07-31: 66 cards
    # carry a real `seal_hash`; **11,084 carried only a source_hash and were shown a
    # "its seal ↗" link anyway** — and every one of those resolved to 404, because the receipt was
    # never minted. Offering a receipt that does not exist is worse than offering none: it is a
    # claim of verification we never performed, on the surface built to prove we do not do that,
    # read mostly by agents. A fingerprint is not a verdict — never silently upgrade authority.
    seal_hash = str((card.get("extra") or {}).get("seal_hash") or "").strip()
    canonical = f"{CANONICAL_HOST}/card/{_esc(card_id)}"
    # ── THE OVERLAY + THE ADJOINING CARDS ────────────────────────────────────────────────────
    # Matt, 2026-07-30: "Add an overlay for each card when it is pulled by a human. Links to
    # adjoining cards as well for agents and users."
    #
    # The edges were already on the card, but they reached a reader ONLY through the JS canvas
    # below — which stays hidden until scripts run. So on ~39k card views (full-log figure,
    # 2026-08-01), every crawler, every reader without JavaScript, and ClaudeBot arrived at a dead
    # end. These are now real <a href> in the markup, so the graph is walkable by anything that can
    # read HTML. The canvas stays as enhancement for those who get it.
    from .. import present as _present
    _over = _present.derive(card)
    _nb = _present.neighbors(card, resolve=corpus.get_card, limit=8)
    overlay = ""
    bits = [b for b in (_over.get("kind_label"), _over.get("posted"), _over.get("standing")) if b]
    if bits:
        overlay = (f"<p class=muted style=\"font-size:.78rem;margin:.1rem 0 .6rem\">"
                   f"{_esc(' · '.join(bits))}</p>")
    # THE OPEN QUESTION, PUT TO THE READER WHO ACTUALLY OPENED THIS CARD (Matt, 2026-08-01: "you
    # ask the first person that recalls the cards to verify them"). Real <a href>, no JavaScript —
    # the adjoining-card graph was invisible to every no-JS reader and every crawler across ~39k
    # views for exactly that reason, and an ask nobody can see is worse than no ask, because the
    # card then wears the same face as a checked one.
    unchecked_block = ""
    _ask = _over.get("unchecked")
    if _ask:
        # THE COUNT COMES FROM THE LOG, NOT FROM THE CARD. `present.derive` is pure and cached by
        # (id, updated_at), so the block it hands back can only ever say "nobody has checked this"
        # — it has no way to know an answer arrived, and the cache would freeze that sentence in
        # place besides. Reading the fold HERE, where I/O already happens, is what keeps the page
        # honest after the first reader answers. Without this the ask would be a lie within a
        # minute of working correctly.
        _ask = _unchecked_live(card_id, _ask)
        _links = " · ".join(
            f"<a href=\"{_esc(_ask['answers'][v])}\">{_esc(label)}</a>"
            for v, label in (("holds", "Yes, it holds"), ("wrong", "No, this is wrong"),
                             ("unsure", "I'm not sure")))
        _src = _ask.get("source") or {}
        _cite = _esc(str(_src.get("label") or ""))
        if _src.get("url"):
            _cite = f"<a href=\"{_esc(str(_src['url']))}\" rel=nofollow>{_cite}</a>"
        unchecked_block = (
            "<div style=\"border:1px solid #d8cfa8;background:#fbf8ee;padding:.7rem .85rem;"
            "margin:.8rem 0;border-radius:3px\">"
            f"<p style=\"margin:0 0 .35rem;font-weight:600\">{_esc(_ask['headline'])}</p>"
            f"<p class=muted style=\"margin:0 0 .45rem;font-size:.82rem\">{_esc(_ask['question'])}</p>"
            + (f"<p class=muted style=\"margin:0 0 .45rem;font-size:.78rem\">Source: {_cite}</p>"
               if _cite else "")
            + f"<p style=\"margin:0 0 .3rem;font-size:.85rem\">{_links}</p>"
            f"<p class=muted style=\"margin:0;font-size:.72rem\">{_esc(_ask['note'])}</p>"
            "</div>")

    adjoining = ""
    if _nb:
        rows = "".join(
            f"<li style=\"margin:.28rem 0\">"
            f"<span class=muted style=\"font-size:.72rem\">{_esc(n['relationship'])} →</span> "
            f"<a href=\"{_esc(n['href'])}\">{_esc(n['title'] or n['id'])}</a>"
            + (f" <span class=muted style=\"font-size:.72rem\">— {_esc(n['why'][:90])}</span>"
               if n.get("why") else "")
            + "</li>"
            for n in _nb)
        adjoining = (f"<section class=card style=\"margin-top:1rem\">"
                     f"<div class=muted style=\"font-size:.8rem\">adjoining cards</div>"
                     f"<ul style=\"list-style:none;padding-left:0;margin:.4rem 0 0\">{rows}</ul>"
                     f"</section>")
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
    # The adjoining cards, for an agent parsing structured data rather than markup. Same edges,
    # same order, so the two surfaces cannot drift apart.
    if _nb:
        ld["relatedLink"] = [f"{canonical.rsplit('/card/', 1)[0]}/card/{n['id']}" for n in _nb]
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
            # THE INVITATION (Matt, 2026-08-01: "Imagine this is the only site someone has.").
            # 95% of measured traffic is agents, and the card page is where their citations land a
            # person — /card/* is the most-hit path on the site. That person arrives mid-library,
            # cold, with no idea the rest exists. One quiet line says what this place is and that
            # it costs nothing. Server-rendered like everything else here: no script, no account.
            "<p class=muted style=\"font-size:.74rem;margin:0 0 .55rem\">"
            "A card from <a href=\"/\">a free library</a> — ask anything, no account, works "
            "offline. Every card carries its source.</p>"
            f"<h1>{title}</h1>{overlay}{unchecked_block}{body_html}"
            f"<section class=card>{source_html}"
            f"<div class=muted style=\"font-size:.8rem;margin-top:.5rem\">card id</div>"
            f"<div class=mono style=\"word-break:break-all\">{_esc(card_id)}</div>{related}</section>"
            f"{adjoining}"
            # Local connection-graph — progressive enhancement (hidden until JS finds a real
            # neighborhood, so the crawlable page stands alone). Each edge links to its seal.
            f"<section class=card id=nhconn data-cid=\"{_esc(card_id)}\" style=\"margin-top:1rem;display:none\">"
            f"<div class=muted style=\"font-size:.8rem\">connections</div>"
            f"<canvas id=nhlg role=img aria-label=\"Connection graph — this card and its linked records\" style=\"width:100%;height:320px;display:block;margin:.4rem 0\"></canvas>"
            f"<p class=muted id=nhlg-cap style=\"font-size:.75rem\"></p></section>"
            # A FRONT DOOR, alongside `/`. First measured on a partial instrument; the full logs
            # (2026-08-01) show ~39k card views across the hosts against ~6k on the homepage —
            # the homepage from 2,318 distinct IPs, the widest genuine reach we have. The card page was offering
            # only its own seal and raw JSON — so the most-read surface we have said nothing about
            # the engine that makes it worth trusting, or the room where people put their own work.
            # Three doors, named plainly, in the page's own voice. No pitch.
            # THE FLAG — "the user can also flag our card as incomplete and that will trigger
            # Steward to call out for more information and expand" (Matt, 2026-08-01). One dumb
            # control opening a want of kind `expand`; the Steward's rounds do the rest.
            f"<p class=muted style=\"font-size:.78rem\"><a href=\"#\" id=nh-flag>"
            f"Is this card incomplete? Tell the library — it will call out for more ↗</a></p>"
            f"<script>document.getElementById('nh-flag').addEventListener('click',function(e){{"
            f"e.preventDefault();var el=this;"
            f"fetch('/want',{{method:'POST',headers:{{'content-type':'application/json'}},"
            f"body:JSON.stringify({{kind:'expand',card_id:document.getElementById('nhconn').dataset.cid}})}})"
            f".then(function(r){{return r.json()}}).then(function(d){{"
            f"el.textContent=d.ok?'Noted — the library will seek more on this.':(d.error||'Could not record that.')}})"
            f".catch(function(){{el.textContent='Could not reach the want list right now.'}})}});</script>"
            f"<footer class=site><p>A record from the keeping — found and cited, never generated. "
            f"<a href=/search>Search the keeping →</a></p>"
            f"<p class=muted style=\"font-size:.82rem\">"
            f"Every claim here can be checked: <a href=\"/#verify\">verify one yourself ↗</a>"
            f" · members keep their own shelves in <a href=\"/shelf.html\">the Commons ↗</a>"
            f" · <a href=\"/llms.txt\">if you are an agent, start here ↗</a></p></footer></main>"
            f"<script src=/graph.js defer></script>"
            f"<script>addEventListener('load',function(){{var s=document.getElementById('nhconn');"
            f"if(window.NHGraph&&s)NHGraph.local('nhconn','nhlg',s.getAttribute('data-cid'));}});</script>"
            f"</body></html>")
    return 200, html


_SITEMAP_PAGES = ("/", "/situations.html", "/ask.html", "/bible.html", "/read.html", "/characters.html",
                  "/prophecy.html", "/journal.html", "/map.html", "/steward.html",
                  "/community.html", "/corpus.html", "/guarantees.html", "/collapse.html",
                  "/seeds.html", "/seal.html", "/connect.html", "/profile.html", "/corrected.html", "/audit.html",
                  "/proof.html", "/reason.html", "/boundary.html", "/almanac.html", 
                  "/teachings.html", "/brain.html", "/floor.html", 
                  "/harmony.html", "/timeline.html", "/backmatter.html", "/places.html",
                  "/narratives.html",  "/voices.html", "/contact.html",
                  "/playbook.html", "/plow.html")


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



def _thread_is_private(thread_id: str) -> bool:
    """True if this thread is bound to someone's key — then only that key may read it."""
    try:
        from .. import binding as _b
        return bool(_b.owner_of(thread_id))
    except Exception:
        return False

# ── A per-corpus-version cache for the whole-corpus scan routes (red-team DoS #1) ────────────────────
# These GET routes recompute an aggregate over the ENTIRE resident corpus per request (seconds each on a
# large corpus). The corpus is an immutable singleton BETWEEN writes, so a result stays valid until the
# corpus changes — keyed on a cheap fingerprint (the singleton's identity + its card count), which shifts
# on a reload (a new process) or a runtime add_card. A short TTL is a backstop for any in-place edit. This
# turns a repeatable multi-second CPU cost into a one-time-per-corpus-version cost; the read rate-limit
# still bounds the very first (cold) hits.
_SCAN_CACHE = {}
_SCAN_TTL_S = 120
_SCAN_CACHE_MAX = 512


def _corpus_token():
    try:
        from .. import corpus as _c
        cc = _c.default_corpus()
        return (id(cc), len(cc.cards))
    except Exception:  # noqa: BLE001
        return (0, 0)


def _cached_scan(key, compute):
    """Return compute()'s result, cached until the corpus changes (or the TTL lapses). Callers must treat
    the returned value as read-only (it is shared); copy before mutating."""
    import time as _t
    tok, now = _corpus_token(), _t.time()
    hit = _SCAN_CACHE.get(key)
    if hit is not None and hit[0] == tok and hit[1] > now:
        return hit[2]
    val = compute()
    if len(_SCAN_CACHE) >= _SCAN_CACHE_MAX:
        _SCAN_CACHE.clear()
    _SCAN_CACHE[key] = (tok, now + _SCAN_TTL_S, val)
    return val


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
        # `shards` reports open file handles because on 2026-08-01 they climbed to 1023 of 1024
        # unseen, and the first symptom was every /verify answering 500. A leak that nobody can
        # watch is a leak that comes back; now health says the number out loud.
        from .. import corpus_db as _cdb
        return _ok({"ok": True, "version": __version__, "surface": surface,
                    "schema_active": schema_active(config.schema_path, config.skip_schema_validation),
                    "jsonschema": _HAS_JSONSCHEMA,
                    "shards": _cdb.open_connections()})
    if method == "GET" and path == "/health/memory":
        # WHERE THE RESIDENT CORPUS ACTUALLY SPENDS ITS MEMORY, from the live process. The freeze
        # design rests on a belief about this and nobody had measured it: 25,087 cards costing
        # 1.7 GB is ~68 KB each, which no card body explains. If the weight is the token index
        # rather than the cards, freezing moved the wrong thing. Sampled, and it says so.
        c = corpus.default_corpus()
        return _ok({"resident": c.footprint(),
                    "note": "an estimate from samples, labelled as one — see `measured_over`"})
    if method == "GET" and path == "/speak/health":
        # Is the operator's voice wired, or are we on the sovereign floor? Self-check without guessing:
        # actually synthesize one fixed line — content-addressed, so it hits the API once and the cache
        # forever after (near-free to poll). configured() only proves the env is set; this proves the
        # KEY WORKS. Matt, 2026-08-28: a glance-check after any rotation, no engineer needed.
        from .. import voice as _voice
        if not _voice.configured():
            return _ok({"voice": "floor", "wired": False,
                        "reason": "ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID not set — sovereign floor"})
        s = _voice.speak("Narrow Highway voice check.")
        if s:
            return _ok({"voice": "ceiling", "wired": True, "cache": s[1], "bytes": len(s[0])})
        return _ok({"voice": "floor", "wired": False,
                    "reason": "key present but the upstream voice call failed (bad/rotated key?) — floor"})
    if method == "GET" and path == "/tv/lineup":
        # narrowhighway.tv — the museum as an old-school cable network (the SHELL). Channels over the
        # halls we already hold; 'now playing' rotates by the clock, 'from the start' winds to the top,
        # and a 'For You' lane leads when the viewer says what they seek. Conduit — every item is a card
        # that already passed the gate, shown in a broadcast frame; nothing here is generated.
        import time as _time
        from .. import tv as _tv
        return _ok(_tv.lineup(seeking=(query.get("seeking") or "").strip(), now_epoch=_time.time()))
    if method == "GET" and path == "/identity":
        # identity = what the engine IS (the dry, efficient truth); persona = WHO it is to talk to
        # (the separate voice / movie-style experience). The card system stays pure efficiency.
        # The FROZEN mission + kernel + agent covenant (Matt, 2026-07-25) are served here so any
        # agent that reads /identity reads the law it is bound by.
        from .. import branding as _branding
        return _ok({"surface": surface, "identity": config.identity, "persona": config.persona,
                    "motto": _branding.MOTTO,
                    "mission": ("Narrow Highway gives humans and agents a governed way to find, check, "
                                "use, and preserve information without losing its source, authority, "
                                "or history."),
                    "serves_first": ("Families, children, and communities that need us — the people "
                                     "who cannot afford to be without it. Free, no account."),
                    "kernel": ["find what is relevant", "distinguish what kind of thing it is",
                               "verify what can actually be verified", "preserve the trail",
                               "prevent authority from being silently upgraded"],
                    "agent_covenant": [
                        "retrieve from corpora first",
                        "distinguish citation from proof",
                        "quarantine generated material",
                        "request human authorization before writes",
                        "produce a receipt for consequential actions",
                        "carry provenance through every transformation",
                        "respect local data and identity boundaries",
                        "stop when evidence is incomplete"]})

    if method == "GET" and path == "/route":
        # The Router — names the member who should answer, and hands off. It NEVER answers.
        # Rule-based and deterministic (no model), so the body keeps its zero-dependency
        # property; every decision carries the evidence that produced it. No `q` -> the
        # directory of the body. See docs/THE_COMPANION.md §3.
        from .. import router as router_mod
        q = (query.get("q") or "").strip()
        if not q:
            return _ok({"surface": surface, "members": router_mod.members(),
                        "note": "pass ?q= to route an input; the Router names a member, it never answers"})
        return _ok({"surface": surface, "query": q, **router_mod.route(q)})

    if method == "GET" and path == "/bind/challenge":
        # A single-use nonce. Sign it with the private key on your drive to prove possession.
        from .. import binding as binding_mod
        return _ok(binding_mod.challenge((query.get("public_key") or "").strip()))

    if method == "POST" and path == "/bind":
        # The key on your drive IS the identity (docs/THE_COMPANION.md §4.2). No account, no
        # password, no row about you: we store a public key and the ids of threads we already
        # hold. Possession of the drive is the whole proof — and there is no recovery backdoor,
        # because a backdoor we could open for you can be opened without you.
        from .. import binding as binding_mod
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        r = binding_mod.claim((body.get("public_key") or "").strip(), body.get("nonce"),
                              body.get("signature"),
                              (body.get("thread_id") or "").strip() or None)
        return _ok(r) if r.get("ok") else _err(403, r.get("error", "not proven"))

    if method == "POST" and path == "/book":
        # The Book of Days — answers only to the key on your drive. Written by you, indexed by
        # us: notes are stored verbatim, derived pointers are labelled with what produced them,
        # amend keeps the prior text, forget is a real delete, export hands you everything.
        # Every op spends a single-use challenge, so send each proof exactly once.
        from .. import binding as binding_mod, bookofdays as book_mod
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        owner = binding_mod.prove((body.get("public_key") or "").strip(),
                                  body.get("nonce"), body.get("signature"))
        if not owner:
            return _err(403, "not proven — sign a fresh challenge with the key on your drive")
        op = str(body.get("op") or "read").strip()
        try:
            limit = max(1, min(int(body.get("limit") or 100), 500))
        except (TypeError, ValueError):
            limit = 100
        if op == "read":
            return _ok(book_mod.entries(owner, limit=limit))
        if op == "export":
            return _ok(book_mod.export(owner))
        if op == "write":
            r = book_mod.write(owner, body.get("text") or "")
        elif op == "amend":
            r = book_mod.amend(owner, str(body.get("entry_id") or "").strip(),
                               body.get("text") or "")
        elif op == "forget":
            r = book_mod.forget(owner, str(body.get("entry_id") or "").strip())
        elif op == "derive":
            r = book_mod.derive(owner, str(body.get("thread_id") or "").strip())
        else:
            return _err(400, "unknown op — read|write|amend|forget|derive|export")
        return _ok(r) if r.get("ok") else _err(400, r.get("error", "refused"))

    if method == "POST" and path == "/inlet":
        # Bring anything. The Router names the member, the Scribe records it verbatim, and the
        # receipt says exactly where it went — nothing is filed invisibly. Answers to your key.
        from .. import binding as binding_mod, inlet as inlet_mod
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        who = binding_mod.prove((body.get("public_key") or "").strip(),
                                body.get("nonce"), body.get("signature"))
        if not who:
            return _err(403, "not proven — sign a fresh challenge with the key on your drive")
        r = inlet_mod.receive(who, body.get("text") or "",
                              thread_id=str(body.get("thread_id") or "").strip(),
                              surface=surface)
        return _ok(r) if r.get("ok") else _err(400, r.get("error", "nothing brought"))

    if method == "POST" and path == "/returns":
        # What should come back right now, and why — time (a deferral came due), state (sealed
        # work gone quiet), or concordance (the keeping speaks to what you keep carrying).
        # Every item answers "why now?"; nothing is inferred and nothing is generated.
        from .. import binding as binding_mod, inlet as inlet_mod
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        who = binding_mod.prove((body.get("public_key") or "").strip(),
                                body.get("nonce"), body.get("signature"))
        if not who:
            return _err(403, "not proven — sign a fresh challenge with the key on your drive")
        try:
            limit = max(1, min(int(body.get("limit") or 10), 50))
        except (TypeError, ValueError):
            limit = 10
        return _ok(inlet_mod.returns(who, limit=limit))

    if method == "POST" and path == "/fork":
        # Branch a thread at a turn. The shared past keeps its hashes, so ancestry is PROVABLE
        # rather than asserted. A thread bound to a key may only be forked by that key.
        from .. import binding as binding_mod, branch as branch_mod
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        tid = str(body.get("thread_id") or "").strip()
        bound_to = binding_mod.owner_of(tid)
        if bound_to:
            who = binding_mod.prove((body.get("public_key") or "").strip(),
                                    body.get("nonce"), body.get("signature"))
            if who != bound_to:
                return _err(403, "this thread is bound to a key — prove it to fork it")
        seq = body.get("seq")
        try:
            seq = None if seq is None else int(seq)
        except (TypeError, ValueError):
            return _err(400, "seq must be an integer")
        r = branch_mod.fork(tid, seq)
        return _ok(r) if r.get("ok") else _err(400, r.get("error", "refused"))

    if method == "GET" and path == "/thread/lineage":
        _tid = (query.get("id") or query.get("thread_id") or "").strip()
        if _tid and _thread_is_private(_tid):
            return _err(403, "this conversation is bound to a key — it is not readable without it")
        # Where a thread came from, and how much of the past it genuinely shares (by hash).
        from .. import branch as branch_mod
        r = branch_mod.lineage((query.get("id") or query.get("thread_id") or "").strip())
        return _ok(r) if r.get("ok") else _err(404, r.get("error", "no such thread"))

    if method == "POST" and path == "/defer":
        # Hand a thread or a note forward to a member and a time — "the Steward has this in
        # April". `due` is what lets the companion bring something back when it matters.
        from .. import binding as binding_mod, branch as branch_mod
        if not isinstance(body, dict):
            return _err(400, "JSON object body required")
        who = binding_mod.prove((body.get("public_key") or "").strip(),
                                body.get("nonce"), body.get("signature"))
        if not who:
            return _err(403, "not proven — sign a fresh challenge with the key on your drive")
        op = str(body.get("op") or "due").strip()
        if op == "due":
            return _ok(branch_mod.due(who))
        if op == "pending":
            return _ok(branch_mod.pending(who))
        if op == "defer":
            r = branch_mod.defer(who, member=str(body.get("member") or ""),
                                 when=body.get("when"), note=str(body.get("note") or ""),
                                 thread_id=str(body.get("thread_id") or "").strip())
        elif op == "release":
            r = branch_mod.release(who, str(body.get("item_id") or "").strip())
        else:
            return _err(400, "unknown op — defer|due|pending|release")
        return _ok(r) if r.get("ok") else _err(400, r.get("error", "refused"))

    if method == "GET" and path == "/land":
        # Do we already hold a card for this? Then land on it rather than searching again.
        from .. import recall as _recall
        return _ok(_recall.land((query.get("q") or "").strip()))

    if method == "GET" and path == "/cards/for-the-group":
        # Communal cards proven useful across several DIFFERENT conversations — the honest
        # candidates for the shared keeping. Candidates only: nothing is published
        # automatically, and a personal card can never appear here.
        from .. import recall as _recall
        try:
            n = max(2, min(int(query.get("min") or 3), 50))
        except (TypeError, ValueError):
            n = 3
        return _ok(_recall.for_the_group(min_conversations=n))

    if method == "GET" and path == "/thread/recalled":
        # What this conversation left behind that was worth recalling — seals, verses, words.
        _tid = (query.get("id") or query.get("thread_id") or "").strip()
        if _tid and _thread_is_private(_tid):
            return _err(403, "this conversation is bound to a key — it is not readable without it")
        from .. import recall as _recall
        return _ok(_recall.recalled(_tid))

    if method == "GET" and path == "/thread/digest":
        _tid = (query.get("id") or query.get("thread_id") or "").strip()
        if _tid and _thread_is_private(_tid):
            return _err(403, "this conversation is bound to a key — it is not readable without it")
        # An INDEX of a thread, never a summary: what was verified and sealed, what Scripture
        # it cited, which words recur, whether the chain is intact. Counted, not judged —
        # nothing is compressed away, because summarising would mean generating.
        from .. import distill as distill_mod
        tid = (query.get("id") or query.get("thread_id") or "").strip()
        r = distill_mod.digest(tid)
        return _ok(r) if r.get("ok") else _err(404, r.get("error", "no such thread"))

    if method == "GET" and path == "/thread/recall":
        _tid = (query.get("id") or query.get("thread_id") or "").strip()
        if _tid and _thread_is_private(_tid):
            return _err(403, "this conversation is bound to a key — it is not readable without it")
        # Retrieval INTO the chain — the exchanges themselves, verbatim, with why each matched.
        # This is what replaces "summarise the old turns": the past is retrieved, not rewritten.
        from .. import distill as distill_mod
        tid = (query.get("id") or query.get("thread_id") or "").strip()
        try:
            limit = max(1, min(int(query.get("limit", "5")), 25))
        except (TypeError, ValueError):
            limit = 5
        r = distill_mod.recall(tid, query.get("q") or "", limit=limit)
        return _ok(r) if r.get("ok") else _err(404, r.get("error", "no such thread"))

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

    if method == "POST" and path == "/chess":
        # Chess as a deterministic verifier (game theory, applied): is this move legal, is the side
        # to move in check / checkmate / stalemate, what is the material — decided by the rules of
        # chess (move generator proven by perft), and sealed like any other verdict. It does not
        # play; it states what is true. Body: {fen, claim, move?}; claim ∈
        # {legal_move, check, checkmate, stalemate, material}.
        if not isinstance(body, dict) or not str(body.get("fen") or "").strip():
            return _err(400, "fen required")
        from .. import chess as _chess
        res = _chess.verify(str(body["fen"]), str(body.get("claim") or "check"),
                            move=(str(body["move"]) if body.get("move") else None))
        seal_on = str(query.get("seal", "1")).lower() not in ("0", "false", "no", "off")
        from .. import receipts
        res = receipts.attach(res, config=config, domain="chess", enabled=seal_on)
        telemetry.record("chess", surface=surface, verdict=res.get("verdict"),
                         sealed=bool(res.get("seal")))
        return _ok(res)

    if method == "GET" and path == "/path":
        # Wayfinding — a floorplan of the keeping. Given what you're asking (q) and optionally the
        # thread you're in, return where you stand, the connected rooms (on-topic by construction),
        # where you've been, and the next step. Deterministic; reads only.
        from .. import wayfind as _wf
        return _ok(_wf.path(q=(query.get("q") or "").strip() or None,
                            thread_id=(query.get("thread") or "").strip() or None))

    if method == "POST" and path == "/audit":
        # The Auditor: deterministic extractors find every checkable claim in a pasted text,
        # the moat verifies the lot, one sealed coverage report comes back. Extraction is
        # conservative — it would rather miss a claim than check the wrong one.
        if not isinstance(body, dict) or not str(body.get("text") or "").strip():
            return _err(400, "text required")
        from .. import audit as _audit
        seal_on = str(query.get("seal", "1")).lower() not in ("0", "false", "no", "off")
        res = _audit.audit(str(body["text"]), config, seal=seal_on)
        telemetry.record("audit", surface=surface, verdict=res.get("verdict"),
                         claims=res.get("claims_found", 0), sealed=bool(res.get("seal")))
        return _ok(res)

    if method == "POST" and path == "/context/run":
        # THE CONTEXT LOOP — node-local ONLY. Runs the whole circuit behind the node's own walls: hold
        # the private/framing context, verify ONLY the necessity-only, de-identified skeleton in-process,
        # then reattach the verdict with the boundary declared. It is OFF unless the operator opts in
        # (CONCORDANCE_SOVEREIGN_NODE), because on the SHARED hosted server this request body would carry
        # the caller's full private text to us — the exact thing the loop exists to prevent (context
        # stays local). On the shared server: strip locally and send only the skeleton to /verify.
        import os as _os
        # EXPLICIT truthy allowlist — a bare "non-empty" check would let CONCORDANCE_SOVEREIGN_NODE=0/false
        # (an operator's attempt to DISABLE) turn the private-context loop ON on the shared server.
        if _os.environ.get("CONCORDANCE_SOVEREIGN_NODE", "").strip().lower() not in ("1", "true", "yes", "on"):
            return _err(403, "the context loop runs only on a sovereign node — set "
                             "CONCORDANCE_SOVEREIGN_NODE to enable it on your own machine; on the shared "
                             "server, strip locally and send only the skeleton to /verify")
        if not isinstance(body, dict) or not str(body.get("text") or "").strip():
            return _err(400, "text required")
        from .. import context as _context
        seal_on = str(query.get("seal", "1")).lower() not in ("0", "false", "no", "off")
        res = _context.run_verified(str(body["text"]), config=config, seal=seal_on)
        telemetry.record("context_run", surface=surface, verdict=res.get("status"))
        return _ok(res)

    if method == "POST" and path == "/days":
        # Your days: time + concentration, counted from the conversations THIS BROWSER holds.
        # POST, not GET, because a roster of thread ids is personal and belongs in a body rather
        # than a query string that lands in access logs and history. Nothing is enumerated here:
        # ids the caller does not hold simply return nothing, and crisis is never charted.
        if not isinstance(body, dict) or not isinstance(body.get("thread_ids"), list):
            return _err(400, "thread_ids (a list) required")
        try:
            tz = int(body.get("tz_offset_minutes") or 0)
        except (TypeError, ValueError):
            tz = 0
        tz = max(-840, min(840, tz))
        from .. import days as _days
        res = _days.chart(body["thread_ids"], tz_offset_minutes=tz)
        telemetry.record("days", surface=surface, threads=res.get("threads_found", 0))
        return _ok(res)

    if method == "GET" and path == "/apothecary":
        # The Apothecary: read + search the living-with-the-land shelf. ?q= searches,
        # ?id= opens one monograph, bare browses. Safety and verdicts travel with every entry.
        from .. import apothecary as _apo
        if query.get("id"):
            res = _apo.get(str(query["id"]))
            return _ok(res) if res.get("ok") else _err(404, res.get("error", "not found"))
        if query.get("q"):
            return _ok(_apo.search(str(query["q"])))
        return _ok(_apo.browse())

    if method == "POST" and path == "/apothecary/propose":
        # the write side: received and queued for the keeper — never self-publishing
        if not isinstance(body, dict) or not str(body.get("text") or "").strip():
            return _err(400, "text required")
        from .. import apothecary as _apo
        res = _apo.propose(str(body["text"]), name=str(body.get("name") or ""),
                           kind=str(body.get("kind") or ""))
        return _ok(res) if res.get("ok") else _err(400, res.get("error", "refused"))

    if method == "POST" and path == "/pins":
        # what the pages this browser holds are still carrying. POST: ids are personal.
        if not isinstance(body, dict) or not isinstance(body.get("thread_ids"), list):
            return _err(400, "thread_ids (a list) required")
        from .. import pins as _pins
        return _ok(_pins.collect(body["thread_ids"]))

    if method == "POST" and path == "/pins/done":
        if not isinstance(body, dict) or not body.get("thread_id") or not body.get("id"):
            return _err(400, "thread_id and id required")
        from .. import pins as _pins
        res = _pins.done(str(body["thread_id"]), str(body["id"]))
        return _ok(res) if res.get("ok") else _err(404, res.get("error", "not found"))

    if method == "POST" and path == "/console":
        # THE CONSOLE — audio-native coach & scribe. Crisis-first, then route (ask · dictate · schedule
        # · copies), or form a LOCATED artifact from anything dropped in (the location, never the blob).
        # Returns the small, speakable, LoRa-ready payload. See docs/CONSOLE.md.
        if not isinstance(body, dict):
            return _err(400, "text or intake required")
        from .. import console as _console
        intake = body.get("intake")
        if isinstance(intake, dict):
            # A PDF may be sent as base64 for TEXT extraction only — we extract, then discard the bytes
            # (we keep the location + the usable text, never the blob). Capped so intake stays light.
            pdf_bytes = None
            b64 = intake.get("pdf_b64")
            if isinstance(b64, str) and b64:
                import base64 as _b64
                try:
                    pdf_bytes = _b64.b64decode(b64)
                except Exception:  # noqa: BLE001
                    pdf_bytes = None
                if pdf_bytes and len(pdf_bytes) > 12_000_000:
                    return _err(413, "file too large to extract here — keep it on a drive and give the location")
            r = _console.intake_artifact(
                source_location=str(intake.get("source_location") or ""),
                kind=str(intake.get("kind") or "file"), title=str(intake.get("title") or ""),
                extracted_text=str(intake.get("extracted_text") or ""),
                sha256=str(intake.get("sha256") or ""), pdf_bytes=pdf_bytes)
            return _ok(r) if r.get("ok") else _err(400, r.get("error") or "a source location is required")
        text = str(body.get("text") or "").strip()
        if not text:
            return _err(400, "text or intake required")
        from .. import ask as _ask
        gate_open = (surface == "witness") or session_gate_open or _ask.gate_signal(text)
        # v1: dictation is kept edge-side (store-nothing, no account); the signed-write owner arrives
        # with the covenant flow. A proven owner may be threaded here later.
        return _ok(_console.dispatch(text, config, owner=None, gate_open=gate_open))

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
        # Checking should not need a button. If the person wrote prose carrying numbers and the
        # router did not already send it to a verifier, the Auditor extracts the checkable claims
        # and checks them. This runs BEFORE the deck write so the stored exchange is the response
        # the person actually saw — attaching it afterwards left the record missing the check.
        # Never on crisis: numbers in "i have 3 kids and 40 dollars" must not summon arithmetic.
        if r.get("kind") not in ("verify", "crisis") and any(c.isdigit() for c in text):
            try:
                from .. import audit as _audit
                _a = _audit.audit(text, config, seal=False)
                if _a.get("claims_found"):
                    r["audit"] = _a
            except Exception:  # noqa: BLE001
                pass
        # Anticipate — a step ahead: the likely next question, as clickable follow-ups. Best-effort,
        # off to the side; never on crisis/grief (anticipate() returns nothing there).
        try:
            _nxt = _ask.anticipate(text, r)
            if _nxt:
                r["next"] = _nxt
        except Exception:  # noqa: BLE001
            pass
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
            # the organizing book: a list or reminder the responder discerned is pinned to
            # THIS page, so it greets the person at the next open. Off to the side — a pin
            # failure never breaks the answer.
            if r.get("pin"):
                try:
                    from .. import pins as _pins
                    _pins.add(tid, r["pin"]["kind"], r["pin"]["text"], due=r["pin"].get("due"))
                except Exception:  # noqa: BLE001
                    pass
            # Recall: promote what this exchange left behind — a sealed receipt, a verse
            # reached for, a word studied — into cards. We cannot recall everything; we
            # recall what is worth recalling. The chain keeps every word regardless.
            # Off to the side, like the deck write: never alters or breaks the answer.
            try:
                from .. import recall as _recall
                # We search once. If a card is already held for what this names, land on it —
                # it comes back first, and the use is counted toward what the card has earned.
                landed = _recall.land(text, thread_id=tid)
                if landed.get("landed"):
                    r["landed"] = landed["cards"]
                kept = _recall.remember(tid)
                if kept.get("ok") and kept.get("count"):
                    r["recalled"] = kept["kept"]
            except Exception:  # noqa: BLE001
                pass
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
                              refs=body.get("refs") or [],
                              attestation=body.get("attestation"))
        return _ok(r) if r is not None else _err(404, "group not found")

    # The Fellowship Mesh — a network of believers who serve each other (offer / need / collaborate /
    # create). NOT a church, NOT a tithe (a framing so no one is scared off; we support the churches —
    # a church that serves here is just another node). Sovereign: the key on your drive is your node,
    # no account, no PII, no directory of persons. Posts are content-addressed (unaltered) + optionally
    # signed (authentic), hop-limited like a LoRa mesh. Personal data lives in data/mesh/ — never committed.
    if method == "GET" and path == "/mesh":
        from .. import mesh
        return _ok(mesh.guidance())
    if method == "POST" and path == "/mesh/node":
        if not isinstance(body, dict) or not str(body.get("public_key") or "").strip():
            return _err(400, "public_key required (the key on your drive is your identity)")
        from .. import mesh
        return _ok(mesh.register_node(str(body["public_key"]), callsign=str(body.get("callsign") or ""),
                                      node_type=str(body.get("type") or "believer"),
                                      confession=str(body.get("confession") or ""),
                                      confession_sig=body.get("confession_sig")))
    if method == "POST" and path == "/mesh/link":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip() \
           or not str(body.get("neighbor") or "").strip():
            return _err(400, "fp and neighbor (fingerprints) required")
        from .. import mesh
        return _ok(mesh.link(str(body["fp"]), str(body["neighbor"]), op=str(body.get("op") or "link"),
                             signature=body.get("signature"), nonce=body.get("nonce")))
    if method == "GET" and path == "/mesh/map":
        from .. import mesh
        try:
            hops = int(query.get("hops") or 2)
        except (TypeError, ValueError):
            hops = 2
        return _ok(mesh.map_around((query.get("fp") or "").strip(), hops=hops))
    if method == "POST" and path == "/mesh/post":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip() \
           or not str(body.get("text") or "").strip():
            return _err(400, "fp and text required")
        from .. import mesh
        try:
            ttl = int(body.get("ttl") or 2)
        except (TypeError, ValueError):
            ttl = 2
        # ONE way in over the wire: you signed the canonical body on your OWN machine (see
        # GET /mesh/signable) and send only the signature. The legacy `private_key` parameter is gone
        # — no client ever sent it, and a secret in a request body is a secret on the wire (§3).
        return _ok(mesh.post_message(str(body["fp"]), str(body["text"]), kind=str(body.get("kind") or "word"),
                                     refs=body.get("refs") or [], ttl=ttl,
                                     signature=body.get("signature"),
                                     nonce=body.get("nonce"),
                                     created_at=body.get("created_at")))
    if method == "GET" and path == "/mesh/signable":
        # The exact bytes to sign, so anyone — human or agent — can speak without sending a secret.
        from .. import mesh
        fp = (query.get("fp") or "").strip()
        text = query.get("text") or ""
        if not fp or not str(text).strip():
            return _err(400, "fp and text required")
        try:
            ttl = int(query.get("ttl") or 2)
        except (TypeError, ValueError):
            ttl = 2
        target = (query.get("target") or "").strip()
        if target:   # a door note to a specific believer, rather than a post to those around you
            return _ok(mesh.signable_door_note(fp, target, str(text),
                                               kind=str(query.get("kind") or "blessing")))
        return _ok(mesh.signable_message(fp, str(text), kind=str(query.get("kind") or "word"),
                                         ttl=ttl))
    if method == "GET" and path == "/mesh/inbox":
        from .. import mesh
        try:
            limit = int(query.get("limit") or 100)
        except (TypeError, ValueError):
            limit = 100
        return _ok(mesh.inbox((query.get("fp") or "").strip(), limit=limit))
    if method == "POST" and path == "/mesh/tend":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip() \
           or not str(body.get("target") or "").strip():
            return _err(400, "fp (a Guide) and target (the node) required")
        from .. import mesh
        return _ok(mesh.tend(str(body["fp"]), str(body["target"]), str(body.get("role") or "member"),
                             signature=body.get("signature"), nonce=body.get("nonce")))
    if method == "POST" and path == "/mesh/invite":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip():
            return _err(400, "fp required")
        from .. import mesh
        try:
            _mu, _ttl = int(body.get("max_uses") or 0), int(body.get("ttl_days") or 30)
        except (TypeError, ValueError):
            return _err(400, "max_uses and ttl_days must be integers")   # not a 500 (red-team #6)
        return _ok(mesh.make_invite(str(body["fp"]), max_uses=_mu, ttl_days=_ttl))
    if method == "POST" and path == "/mesh/redeem":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip() \
           or not str(body.get("token") or "").strip():
            return _err(400, "fp and token required")
        from .. import mesh
        return _ok(mesh.redeem_invite(str(body["token"]), str(body["fp"])))
    if method == "POST" and path == "/mesh/door":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip() \
           or not str(body.get("target") or "").strip() or not str(body.get("text") or "").strip():
            return _err(400, "fp, target and text required")
        from .. import mesh
        return _ok(mesh.leave_on_door(str(body["fp"]), str(body["target"]), str(body["text"]),
                                      kind=str(body.get("kind") or "blessing"),
                                      signature=body.get("signature"),
                                      nonce=body.get("nonce"),
                                      created_at=body.get("created_at")))
    if method == "GET" and path == "/mesh/door":
        from .. import mesh
        try:
            limit = int(query.get("limit") or 100)
        except (TypeError, ValueError):
            limit = 100
        return _ok(mesh.read_door((query.get("fp") or "").strip(), limit=limit))

    # Formation — "make a wish for life"; the tool FINDS the fitting practice, then points off the
    # screen. Stateless (stores nothing about a person's life); found/attributed, never generated.
    if method == "GET" and path == "/formation":
        from .. import formation
        return _ok(formation.guidance())
    if method == "GET" and path == "/formation/kinds":
        from .. import formation
        return _ok(formation.kinds())
    if method == "GET" and path == "/formation/help":
        from .. import formation
        return _ok(formation.help((query.get("wish") or "").strip(), kind=(query.get("kind") or "become").strip()))

    # Web Push — a word on your door becomes a notification. Sovereign (RFC 8291/8292, our own crypto);
    # the network hop is OFF by default and isolated in push.send. No PII (a subscription, not a number).
    if method == "GET" and path == "/push/key":
        from .. import push
        return _ok({"key": push.public_key_b64(), "enabled": push.enabled()})
    if method == "POST" and path == "/push/subscribe":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip() \
           or not isinstance(body.get("subscription"), dict):
            return _err(400, "fp and subscription required")
        from .. import push
        return _ok(push.subscribe(str(body["fp"]), body["subscription"]))
    if method == "POST" and path == "/push/unsubscribe":
        if not isinstance(body, dict) or not str(body.get("fp") or "").strip():
            return _err(400, "fp required")
        from .. import push
        return _ok(push.unsubscribe(str(body["fp"]), endpoint=str(body.get("endpoint") or "")))

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

    # Sovereign, portable identity — the person owns a keypair; we reference only the public key.
    # SECURITY (red-team P0, 2026-07-25): keys are BORN ON THE DEVICE. The server never mints and
    # returns a private key over the wire (it would transit the server + land in an agent's context).
    # Create yours client-side (the covenant client from four verses, or a local keygen); the server
    # only ever verifies PUBLIC keys.
    if method == "POST" and path == "/identity/create":
        telemetry.record("identity", surface=surface, op="create_refused_remote")
        return _err(400, "identity keys are created on your device — never by the server. Derive one "
                         "from your four covenant verses (the covenant client) or generate one "
                         "locally; the server only verifies public keys (/identity/verify).")

    if method == "POST" and path == "/identity/verify":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import identity
        ok = identity.verify(str(body.get("public_key") or ""), body.get("message") or "",
                             str(body.get("sig") or ""))
        return _ok({"ok": bool(ok)})

    # PROFILE — your keeping, keyed by your fingerprint. Optional, sovereign, no account, no password.
    # The server creates NO keys (see /identity/create) and stores no secret: a human derives their key
    # from their verses on their own device, an agent holds one; both sign their own writes. The default
    # is anonymous — no key, no profile.
    if method == "GET" and path == "/profile":
        fp = (query.get("fp") or "").strip()
        if not fp:
            return _err(400, "fp required (your fingerprint, from your public key)")
        from .. import profile as _profile
        return _ok({"id": fp, "profile": _profile.get(fp)})

    if method == "GET" and path == "/profile/served":
        # SERVING — what has come back for you: your wants, met by the keeping, or still sought (honest).
        fp = (query.get("fp") or "").strip()
        if not fp:
            return _err(400, "fp required")
        from .. import profile as _profile
        from .. import serve as _serve
        wants = _profile.get(fp).get("wants") or []
        return _ok({"id": fp, **_serve.returns(wants)})

    if method == "GET" and path == "/profile/community":
        # COMMUNITY — the fellowship is GATED behind the narrow path (Matt: they must be a confessing
        # Christian to see other members). An OPEN read never reveals a member, so this returns only the
        # narrow-path invitation. To actually see a member's fellowship — your own, or another's once you
        # have confessed — POST a SIGNED request to /profile/community/view (the signature proves your key,
        # so the gate cannot be walked past by quoting a fingerprint).
        from .. import community as _community
        return _ok({"id": (query.get("fp") or "").strip(),
                    **_community.for_member((query.get("fp") or "").strip(), viewer_fp=None),
                    "view": "POST /profile/community/view (signed) to see a member's fellowship"})

    if method == "GET" and path == "/profile/path":
        # DISCIPLESHIP — a member's walked path with the coach, computed from their own progress (`done`).
        fp = (query.get("fp") or "").strip()
        if not fp:
            return _err(400, "fp required")
        from .. import disciple as _disciple
        return _ok({"id": fp, **_disciple.walk(fp)})

    if method == "POST" and path == "/profile/community/signable":
        # The exact bytes a viewer signs to see a member's fellowship (the narrow-path gate is applied after
        # the signature verifies). Computed here for correctness; a sovereign client may compute them itself.
        if not isinstance(body, dict) or not str(body.get("public_key") or "").strip():
            return _err(400, "public_key required")
        from .. import community as _community
        canon = _community.signable_view(str(body["public_key"]), str(body.get("member") or ""),
                                          str(body.get("nonce") or ""))
        return _ok({"signable": canon.decode("utf-8"),
                    "note": "sign these exact bytes with your private key, then POST /profile/community/view"})

    if method == "POST" and path == "/profile/community/view":
        # SIGNED fellowship view. The viewer proves their key; their fingerprint is derived from it, then the
        # narrow-path gate decides: your own in full, a confessor sees the member, anyone else is shown the
        # invitation (200 with the gate). A bad signature is refused — the gate cannot be walked past.
        if not isinstance(body, dict):
            return _err(400, "body required")
        from .. import community as _community
        r = _community.view(str(body.get("public_key") or ""), str(body.get("member") or ""),
                            str(body.get("nonce") or ""), str(body.get("signature") or ""))
        if r.get("ok") or r.get("gated"):
            return _ok(r)                            # served, or the narrow-path invitation — both 200
        return _err(403, r.get("error") or "cannot view the fellowship")

    if method == "POST" and path == "/profile/signable":
        # The exact bytes to sign with your private key — computed here for correctness; a sovereign
        # client may compute them itself. Nothing is stored, no key is seen.
        if not isinstance(body, dict) or not str(body.get("public_key") or "").strip():
            return _err(400, "public_key required")
        from .. import profile as _profile
        try:
            _ts = int(body.get("ts") or 0)
        except (TypeError, ValueError):
            _ts = 0
        canon = _profile.signable(str(body["public_key"]), body.get("patch") or {},
                                  str(body.get("nonce") or ""), op=str(body.get("op") or "put"), ts=_ts)
        return _ok({"signable": canon.decode("utf-8"),
                    "note": "sign these exact bytes with your private key, then POST /profile/save"})

    if method == "POST" and path == "/profile/save":
        # SIGNED write. The server verifies your signature against your public key, then saves — only
        # the key's owner can write, no password, replay refused.
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import profile as _profile
        try:
            _ts = int(body.get("ts") or 0)
        except (TypeError, ValueError):
            _ts = 0
        res = _profile.put(str(body.get("public_key") or ""), body.get("patch") or {},
                           str(body.get("nonce") or ""), str(body.get("signature") or ""), ts=_ts)
        if res.get("ok") and isinstance(body.get("patch"), dict) and body["patch"].get("wants"):
            # SERVING — a member's stated wants become the hive's work (deduped; the queue fills them).
            from .. import serve as _serve
            _serve.take([str(w) for w in body["patch"]["wants"] if isinstance(w, str)])
        telemetry.record("profile", surface=surface, op="save", saved=bool(res.get("ok")))
        return _ok(res) if res.get("ok") else _err(403, res.get("error") or "refused")

    if method == "POST" and path == "/profile/erase":
        # SIGNED erase — it is yours to take back.
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import profile as _profile
        try:
            _ts = int(body.get("ts") or 0)
        except (TypeError, ValueError):
            _ts = 0
        res = _profile.delete(str(body.get("public_key") or ""), str(body.get("nonce") or ""),
                              str(body.get("signature") or ""), ts=_ts)
        telemetry.record("profile", surface=surface, op="erase", saved=bool(res.get("ok")))
        return _ok(res) if res.get("ok") else _err(403, res.get("error") or "refused")

    # Badges — a re-checkable receipt pointing at N seals that still stand. NEVER a competency claim.
    if method == "POST" and path == "/badges":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        seal_hashes = body.get("seal_hashes")
        if not isinstance(seal_hashes, list):
            return _err(400, "seal_hashes (list) required")
        from .. import badges
        # Issues UNSIGNED — "the evidence, not the signature, is the badge". Bind your identity
        # afterward by signing the returned content_hash locally and POSTing it to /attest.
        out = badges.issue_badge(seal_hashes, subject_id=body.get("subject_id"),
                                 title=str(body.get("title") or ""),
                                 )
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
        # Returns the bundle and its content_hash; sign that hash locally and POST /attest to bind
        # your identity to it. No private key crosses the wire.
        return _ok(badges.study_export(str(body["key"])))

    if method == "POST" and path == "/study/import":
        if not isinstance(body, dict):
            return _err(400, "JSON object required")
        from .. import badges
        return _ok(badges.study_import(body.get("bundle") or body,
                                       study_key=body.get("key"),
                                       verify_signature=bool(body.get("verify_signature"))))

    # The six mounts are ENUMERATED, not pattern-matched, so the route-coverage auditor
    # (tests/test_routes.py reads these comparisons by AST) can prove each one is dispatched;
    # test_mcp_profiles pins this tuple to PROFILES so the two cannot drift apart.
    if method == "POST" and (path == "/mcp" or path in (
            "/mcp/core", "/mcp/library", "/mcp/sovereign",
            "/mcp/coach", "/mcp/witness", "/mcp/community")):
        # Remote MCP over HTTP — reuse the pure JSON-RPC handler, surface-gated. Stateless
        # request/response (initialize · tools/list · tools/call). Notifications get 202.
        # /mcp/<profile> mounts one plane of the catalog (task #123); the same resolution runs
        # in the streaming Handler, via the one shared helper below.
        from ..mcp import handle as _mcp_handle
        profile, refusal = resolve_mcp_profile(path)
        if refusal is not None:
            return refusal
        req = body if isinstance(body, dict) else {}
        telemetry.record("mcp", surface=surface, method=str(req.get("method") or ""),
                         profile=profile or "full")
        resp = _mcp_handle(req, config, profile=profile)
        return (200, resp) if resp is not None else (202, {})

    if method == "GET" and path == "/search":
        q = (query.get("q") or "").strip()
        if not q:
            return _err(400, "q required")
        limit, capped = bounded_limit(query.get("limit"), 20)
        res = corpus.search(q, limit=limit)  # shared keeping (both surfaces)
        expansion = None
        if not res:
            # THE SAME SLOW LANE /ask HAS ALWAYS HAD. Proven live 2026-08-01: /search?q=Rigveda
            # returned 0 while two /ask calls found and carded three public-domain Rigveda sources.
            # Same question, same engine, two doors, two answers — and this was the deaf one.
            # A miss is a slower answer, not a dead end.
            from .. import expand as _expand
            expansion = _expand.expand(q, config, plane="human")
            if expansion.get("status") == "acquired":
                res = corpus.search(q, limit=limit)      # it is in the keeping now
        telemetry.record("search", surface=surface, query=q, count=len(res))
        out = {"query": q, "count": len(res), "results": [_card_brief(c) for c in res]}
        if capped:
            out["limit_capped"] = capped
        if expansion and expansion.get("status") != "acquired":
            # Never a bare zero: say WHY there is nothing, and whether it is coming.
            out["expanded"] = {k: v for k, v in expansion.items() if k != "documents"}
        elif expansion:
            out["expanded"] = {"status": "acquired", "message": expansion.get("message"),
                               "found": len(expansion.get("documents") or [])}
        return _ok(out)

    # Library / keeping tools (ported from 1.0, additive — over the same shared corpus).
    if method == "GET" and path == "/cards/stats":
        return _ok(_cached_scan("stats", corpus.stats))
    if method == "GET" and path == "/cards":
        try:
            limit = int(query.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20
        try:
            offset = int(query.get("offset", "0"))
        except (TypeError, ValueError):
            offset = 0
        _sh = query.get("shelf") or None
        return _ok(_cached_scan("browse:%s:%d:%d" % (_sh or "", limit, offset),
                                lambda: corpus.browse(shelf=_sh, limit=limit, offset=offset)))
    if method == "GET" and path == "/card":
        cid = (query.get("id") or "").strip()
        if not cid:
            return _err(400, "id required")
        c = corpus.get_card(cid)
        if c is None:
            return _err(404, "card not found")
        # The same overlay and the same adjoining cards the HTML page shows — so an agent reading
        # JSON and a person reading the page are looking at one thing, and the graph is walkable
        # from either. Both are DERIVED on the way out; the stored card is untouched.
        from .. import present as _present
        _p = _present.derive(c)
        if _p.get("unchecked"):
            # THE SAME LIVE COUNT THE PAGE SHOWS. Fixed here on 2026-08-01 after the HTML surface
            # was corrected and this one was not — the page would report "checked by 2 readers"
            # while an agent fetching the identical card was told nobody had ever looked at it.
            # Correct in one place and absent where the other reader stands is this project's
            # oldest failure, and agents are about 35% of the traffic.
            _p = dict(_p, unchecked=_unchecked_live(str(c.get("id") or ""), _p["unchecked"]))
        return _ok(dict(c, presentation=_p,
                        neighbors=_present.neighbors(c, resolve=corpus.get_card, limit=8)))
    if method == "GET" and path == "/witness":
        # THE CLOUD OF WITNESSES' VOICE — public-domain witnesses' VERBATIM words that frame a question,
        # attributed (witness + work + ref + source). Proposes a way of seeing; the gate and the Word
        # dispose — never a verdict. Public (the commons — PD text), honest-empty where the cloud does not
        # reach. Optional `witness=` scopes to one voice. Nothing generated.
        q = (query.get("q") or "").strip()
        if not q:
            return _err(400, "q required")
        from .. import witness as _witness
        who = (query.get("witness") or "").strip() or None
        return _ok({"q": q, **_witness.see(q, witness=who, k=3)})

    if method == "GET" and path == "/daily":
        _seed = query.get("seed") or None
        c = _cached_scan("daily:%s" % (_seed or ""), lambda: corpus.daily(_seed))
        return _ok(c) if c is not None else _err(404, "the keeping is empty")

    if method == "GET" and path == "/card/connections":
        cid = (query.get("id") or "").strip()
        if not cid:
            return _err(400, "id required")
        r = _cached_scan("conn:%s" % cid, lambda: corpus.connections(cid))
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
    if method == "GET" and path == "/floor":
        # the floor, made visible — the rooted design (both halves) + the two-tree grafts, so a
        # visitor SEES the coherence and is turned upward (Proverbs 9:10).
        from .. import floor as _floor
        # cached per corpus version like its sibling scan routes — payload() is a full-corpus scan
        # (public-card list + grafts), ~2s uncached and repeatable, so it rode the DoS-#1 caution.
        return _ok(_cached_scan("floor", _floor.payload))
    if method == "GET" and path == "/locate":
        _q = query.get("q") or ""
        return _ok(_cached_scan("locate:%s" % _q, lambda: corpus.locate(_q)))
    if method == "GET" and path == "/growth":
        # the standing steering report: corpus health + how much safe growth remains. Aggregate
        # only, read-only — the keeper reads it; the harvester (tools/grow.py) is operator-run.
        from .. import growth as _growth
        m = dict(_cached_scan("growth", lambda: _growth.measure(  # the heavy scan, cached per corpus version
            list(corpus.default_corpus().cards.values()))))
        m["recent"] = _growth.ledger_read(limit=8)                 # the light ledger tail stays fresh
        return _ok(m)

    if method == "GET" and path == "/library/health":
        # `gauges=1` adds the gauge panel: every invented ranking constant located on the
        # measured distribution, with vacuous/binding verdicts. Opt-in because the panel walks
        # the whole token index (~300k entries) — an operator's read, not a heartbeat's.
        h = dict(_cached_scan("health", corpus.health))
        if str(query.get("gauges") or "") in ("1", "true", "yes"):
            h["gauges"] = _cached_scan("gauges", corpus.gauges)
        return _ok(h)

    # Pronunciation guide (synthesized, honest floor) — a neutral phonetic helper, both surfaces.
    if method == "GET" and path == "/pronounce":
        from .. import pronounce
        text = (query.get("text") or query.get("word") or "").strip()
        if not text:
            return _err(400, "text required")
        return _ok(pronounce.guide(text))

    # The Deck — a conversation as a resumable, searchable, tamper-evident chain (threads).
    if method == "GET" and path == "/thread":
        _tid = (query.get("id") or query.get("thread_id") or "").strip()
        if _tid and _thread_is_private(_tid):
            return _err(403, "this conversation is bound to a key — it is not readable without it")
        from .. import threads as _threads
        tid = (query.get("id") or "").strip()
        if not tid:
            return _err(400, "id required")
        rec = _threads.get(tid)
        return _ok(rec) if rec is not None else _err(404, "thread not found")
    if method == "GET" and path in ("/threads", "/threads/search"):
        # PRIVACY: these used to list/search EVERY conversation on the box, with the person's
        # first message as the title — a stranger could enumerate ids and then read the whole
        # thread. Enumeration is now refused outright. Your own threads come back from
        # POST /bind, which requires the key on your drive.
        return _err(403, "listing conversations is not public — prove your key at POST /bind "
                         "to get your own threads")

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
    if method == "GET" and path == "/coach/journey":
        # the one lifelong arc, for any age; ?done=id1,id2,... names where the learner is + next step.
        # Caller holds progress (no personal data). Starts youngest, stays with you, opens the keeping.
        from .. import coach
        done = [x for x in (query.get("done") or "").split(",") if x.strip()]
        return _ok(coach.journey(done))
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
        rec = cas.fetch_anywhere(h)   # the CAS object, or the card that carries it
        telemetry.record("seal_fetch", surface=surface, found=rec is not None)
        if rec is None:
            return _err(404, "seal not found")
        return _ok(rec)

    if method == "GET" and path == "/resolve":
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.resolve_ref(ref))

    if method == "GET" and path == "/passage":
        # Read a passage (verse / range / whole chapter) — the Bible reading primitive.
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.read_passage(ref))

    if method == "GET" and path == "/word_study":
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_study(s))

    if method == "GET" and path == "/cross_refs":
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.cross_references(ref))

    if method == "GET" and path == "/word_occurrences":
        s = (query.get("strongs") or "").strip()
        if not s:
            return _err(400, "strongs required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.word_occurrences(s))

    if method == "GET" and path == "/original":
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from ..verifiers import scripture  # lazy: witness-only
        return _ok(scripture.original_words(ref))

    if method == "GET" and path == "/now":
        # The actual date and time, current at this call. An agent's own clock is months stale
        # (its training cutoff); a layer that stamps receipts with time must be able to TELL time.
        # Served no-store by the JSON layer; freshness is the entire point of this route.
        from .. import ops
        return _ok(ops.now((query.get("tz") or "").strip() or None))

    if method == "GET" and path == "/canon":
        # The canon as concentric layers — the 66 core + disputed books, framed, never merged.
        from .. import canon
        book = (query.get("book") or "").strip()
        return _ok(canon.canon_status(book) if book else canon.overview())

    if method == "GET" and path == "/commentary":
        # Public-domain, attributed commentary (Matthew Henry) — the father's own words, found.
        ref = (query.get("ref") or "").strip()
        if not ref:
            return _err(400, "ref required")
        from .. import commentary
        return _ok(commentary.for_ref(ref, source=(query.get("source") or commentary.DEFAULT_SOURCE)))

    if method == "GET" and path == "/tsk":
        # Editorial cross-references (openbible.info, CC BY — expansion of the public-domain TSK).
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
        name = (query.get("name") or "").strip()
        if not name:
            return _err(400, "name required")
        from .. import characters
        rec = characters.get(name)
        return _ok(rec) if rec is not None else _err(404, "not found in Easton's")

    if method == "GET" and path == "/characters":
        from .. import characters
        try:
            limit = int(query.get("limit", "100"))
        except (TypeError, ValueError):
            limit = 100
        return _ok(characters.browse(letter=(query.get("letter") or None),
                                     search=(query.get("search") or None), limit=limit,
                                     category=(query.get("category") or None)))

    if method == "GET" and path == "/prophecy":
        # Two maps under one door, both attributed and NEVER "HOLDS" (a signpost to Christ, not a proof):
        # the cross-cultural SIGNPOSTS (prophecy.py) and the OT->NT FULFILLMENTS the New Testament itself
        # names (prophecy_fulfillments.py — verdict CONCORDANT, Scripture's own witness carried, not ours).
        from .. import prophecy
        from .. import prophecy_fulfillments as pf
        ref = (query.get("ref") or "").strip()
        if ref:                                      # stand on a verse/chapter, see what the NT takes up
            return _ok(pf.for_ref(ref))
        tid = (query.get("id") or "").strip()
        if tid.startswith("mp_"):                    # one OT->NT fulfillment, whole (both verses' text)
            rec = pf.get(tid)
            return _ok(rec) if rec is not None else _err(404, "fulfillment not found")
        if tid:                                      # one cross-cultural signpost trace
            rec = prophecy.get(tid)
            return _ok(rec) if rec is not None else _err(404, "trace not found")
        if (query.get("fulfillments") or "").strip():   # the whole OT->NT map, grouped by theme
            return _ok(pf.list_all())
        q = (query.get("q") or "").strip()
        return _ok(prophecy.search(q) if q else prophecy.list_traces())

    if method == "GET" and path == "/seeds":
        # Seeds of the Word — the Areopagus / logos spermatikos pass. Attributed, CONCORDANT/signpost,
        # NEVER HOLDS; the idol named and refused, the Source named — Jesus Christ (Acts 17; 1 John 4:1-3).
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

    if method == "GET" and path == "/almanac":
        # The Almanac — 1.0 claims RE-SEALED on the live 2.0 engine (verified-only). Secular,
        # freely surfaced: every entry carries a fresh live receipt, nothing archived-pending.
        from .. import almanac as almanac_mod
        aid = (query.get("id") or "").strip()
        if aid:
            rec = almanac_mod.get(aid)
            return _ok(rec) if rec is not None else _err(404, "almanac entry not found")
        q = (query.get("q") or "").strip()
        if q:
            return _ok(almanac_mod.search(q))
        cat = (query.get("category") or "").strip()
        return _ok(almanac_mod.list_entries(cat))

    if method == "GET" and path == "/codex":
        # The Codex — the project as a compiled, signed, cross-referenced manuscript.
        # Compiled not authored; witnessed cross-refs + the sealed spine; tier-graded.
        from .. import codex as codex_mod
        return _ok(codex_mod.overview())
    if method == "GET" and path == "/codex/scripture":
        from .. import codex as codex_mod
        b = (query.get("book") or "").strip()
        if b:
            rec = codex_mod.scripture_book(b)
            return _ok(rec) if rec is not None else _err(404, "book not in index")
        return _ok(codex_mod.scripture_summary())
    if method == "GET" and path == "/codex/themes":
        from .. import codex as codex_mod
        t = (query.get("theme") or "").strip()
        if t:
            rec = codex_mod.theme(t)
            return _ok(rec) if rec is not None else _err(404, "theme not found")
        return _ok(codex_mod.load_themes())
    if method == "GET" and path == "/codex/connections":
        from .. import codex as codex_mod
        return _ok(codex_mod.load_connections())
    if method == "GET" and path == "/codex/artifact":
        from .. import codex as codex_mod
        return _ok(codex_mod.load_artifact())
    if method == "GET" and path == "/codex/verify":
        from .. import codex as codex_mod
        return _ok(codex_mod.verify_artifact())

    if method == "GET" and path == "/works":
        # The Works — a technical volume of the one book: real worked demonstrations of the
        # depth of mathematics, science and engineering the tools reach, each run through the
        # engine and sealed. Proof, not assertion. Grows as demonstrations are added.
        from .. import compendium as works_mod
        return _ok({"overview": works_mod.overview(), "demonstrations": works_mod.demonstrations()})
    if method == "GET" and path == "/works/item":
        from .. import compendium as works_mod
        rec = works_mod.demonstration((query.get("id") or "").strip())
        return _ok(rec) if rec is not None else _err(404, "demonstration not found")
    if method == "GET" and path == "/works/artifact":
        from .. import compendium as works_mod
        return _ok(works_mod.artifact())
    if method == "GET" and path == "/works/verify":
        from .. import compendium as works_mod
        return _ok(works_mod.verify_artifact())

    if method == "GET" and path == "/decks":
        # The Hare: the curated card sets (decks) with live counts — the atlas renders these.
        from .. import decks as _decks
        return _ok({"decks": _decks.all_decks()})
    if method == "GET" and path == "/decks/predict":
        # "Name the position": which deck(s) does this query call for?
        from .. import decks as _decks
        return _ok({"query": query.get("q", ""), "predicted": _decks.predict(query.get("q", ""), k=3)})
    if method == "GET" and path == "/deck":
        # Search a deck first (fast), fall back to the whole keeping if it comes up short.
        from .. import decks as _decks
        try:
            lim = min(50, max(1, int(query.get("limit") or 12)))
        except (TypeError, ValueError):
            lim = 12
        return _ok(_decks.search(query.get("q", ""), (query.get("id") or "").strip() or None, lim))
    if method == "GET" and path == "/deck/open":
        # Deal the frontloaded hand: open a deck (esp. a need-deck) to the cards it holds, in order,
        # with NO query needed — the anticipated hand for a situation. 404 for an unknown deck id.
        from .. import decks as _decks
        try:
            lim = min(60, max(1, int(query.get("limit") or 15)))
        except (TypeError, ValueError):
            lim = 15
        opened = _decks.open_deck((query.get("id") or "").strip(), lim)
        return _ok(opened) if opened is not None else _err(404, "unknown deck")

    if method == "GET" and path == "/archetypes":
        # The characters of the Bible + their micropositions (the pastoral decks).
        from .. import archetypes as _arch
        return _ok({"archetypes": _arch.archetypes()})
    if method == "GET" and path == "/archetypes/match":
        # Name the position: which biblical moment does this person's need match? The fitting
        # Scripture references come back; the verse — not us — is the answer.
        from .. import archetypes as _arch
        return _ok({"need": query.get("need", ""), "matches": _arch.match(query.get("need", ""), k=3)})
    if method == "GET" and path == "/archetype":
        from .. import archetypes as _arch
        rec = _arch.get((query.get("id") or "").strip())
        return _ok(rec) if rec is not None else _err(404, "microposition not found")

    if method == "POST" and path == "/attest":
        # Phase 2 of binding an identity to a record: you signed its content_hash on your own
        # machine; we verify and record the witness. No private key is accepted here or anywhere.
        if not isinstance(body, dict) or not str(body.get("content_hash") or "").strip():
            return _err(400, "content_hash and attestation required")
        from .. import attest as _attest
        return _ok(_attest.bear_witness(str(body["content_hash"]), body.get("attestation") or {}))
    if method == "GET" and path == "/attest":
        from .. import attest as _attest
        h = (query.get("hash") or query.get("content_hash") or "").strip()
        if not h:
            return _err(400, "hash required")
        return _ok(_attest.witnesses(h))

    if method == "GET" and path == "/consent/signable":
        # Step 1 of a consent grant: the human asks for the exact canonical bytes, signs them ON
        # THEIR DEVICE, and submits only the signature. The key never travels — the mesh's own
        # detached-signature pattern, applied before the bug can exist.
        from .. import consent as _consent
        scope = [s for s in (query.get("scope") or "").split(",") if s.strip()]
        try:
            ttl = int(query.get("ttl_s") or 86400)
        except (TypeError, ValueError):
            ttl = 86400
        r = _consent.signable_grant(query.get("grantor") or "", query.get("agent") or "",
                                    scope, ttl_s=ttl)
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "bad request")
    if method == "POST" and path == "/consent":
        # Step 2: verify the grantor's detached signature over those bytes; keep the grant.
        from .. import consent as _consent
        if not isinstance(body, dict):
            return _err(400, "fields and signature required")
        r = _consent.grant(body.get("fields") or {}, str(body.get("signature") or ""))
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")
    if method == "GET" and path == "/consent":
        from .. import consent as _consent
        return _ok(_consent.check(query.get("agent") or "", query.get("verb") or "",
                                  query.get("grantor") or ""))
    if method == "POST" and path == "/consent/revoke":
        from .. import consent as _consent
        if not isinstance(body, dict):
            return _err(400, "agent, grant_id, grantor, signature required")
        r = _consent.revoke(str(body.get("agent") or ""), str(body.get("grant_id") or ""),
                            str(body.get("grantor") or ""), str(body.get("signature") or ""))
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")

    if method == "POST" and path == "/connect/event":
        # The calendar pilot — the ONE on-behalf write, behind the consent lock. The event lands
        # in the calendar the USER named (their .ics or their CalDAV); nothing is stored here.
        from .. import connect_write as _cw
        if not isinstance(body, dict):
            return _err(400, "grantor, agent, summary, start_iso required")
        r = _cw.create_event(str(body.get("grantor") or ""), str(body.get("agent") or ""),
                             str(body.get("summary") or ""), str(body.get("start_iso") or ""),
                             end_iso=(body.get("end_iso") or None),
                             description=str(body.get("description") or ""))
        if r.get("ok"):
            return _ok(r)
        # A consent refusal is 403 with the teaching attached — not a silent 400.
        return (403, r) if r.get("refused") else _err(400, r.get("error") or "refused")

    # ── THE COMMONS · C1b — the member shelf over HTTP ──────────────────────────────────────
    # A shelf is a covenant key with signed cards on it. The gate is on AMPLIFICATION only:
    # a `shelf` drop is live the moment it is signed; a `commons` drop waits for a human.
    if method == "GET" and path == "/drop/signable":
        from .. import shelves as _sh
        r = _sh.signable_drop(query.get("member") or "", query.get("kind") or "note",
                              query.get("subject") or "", query.get("body") or "",
                              query.get("ring") or "shelf",
                              url=query.get("url") or "", quote=query.get("quote") or "",
                              attribution=query.get("attribution") or "")
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "bad request")
    if method == "POST" and path == "/drop":
        from .. import shelves as _sh
        if not isinstance(body, dict):
            return _err(400, "signed fields and signature required")
        r = _sh.drop(body.get("fields") if isinstance(body.get("fields"), dict) else None,
                     str(body.get("signature") or ""),
                     display_name=str(body.get("display_name") or ""))
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")
    if method == "GET" and path == "/shelf":
        # `viewer` is supplied by the reader and used ONLY to decide what is served. Nothing
        # records that they looked — known when you speak, unseen when you read.
        from .. import shelves as _sh
        r = _sh.shelf_of(query.get("member") or "", viewer=(query.get("viewer") or None))
        return _ok(r) if r.get("ok") else _err(404, r.get("error") or "no such shelf")
    if method == "GET" and path == "/commons":
        from .. import shelves as _sh
        try:
            lim = int(query.get("limit") or 40)
        except (TypeError, ValueError):
            lim = 40
        return _ok(_sh.commons(limit=lim))
    if method == "GET" and path == "/curate/queue":
        # Open on purpose: what waits on a steward is public, so the queue can be watched. Only
        # ACTING on it is gated.
        from .. import shelves as _sh
        return _ok(_sh.review_queue())
    if method == "GET" and path == "/curate/signable":
        # A member taking their OWN card down needs nobody's permission — only their own key.
        from .. import shelves as _sh
        r = _sh.signable_curate(query.get("card_id") or "", query.get("member") or "",
                                query.get("action") or "withdrawn")
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "bad request")
    if method == "POST" and path == "/curate":
        # Authorization lives in shelves.curate, not here, so the MCP door cannot bypass it: a
        # steward token to promote or refuse, or the member's own signature to withdraw. A typed
        # name is not authority. 403 for "not you", 400 for a malformed act.
        from .. import shelves as _sh
        if not isinstance(body, dict):
            return _err(400, "card_id, action, steward, reason required")
        r = _sh.curate(str(body.get("card_id") or ""), str(body.get("action") or ""),
                       str(body.get("steward") or ""), str(body.get("reason") or ""),
                       token=str(body.get("token") or ""),
                       fields=body.get("fields") if isinstance(body.get("fields"), dict) else None,
                       signature=str(body.get("signature") or ""))
        if r.get("ok"):
            return _ok(r)
        return _err(403 if "not authorized" in (r.get("error") or "") else 400,
                    r.get("error") or "refused")

    if method == "GET" and path == "/moderation/signable":
        # Step 1 of a report or a block: the exact canonical bytes to sign ON THE DEVICE. Three
        # witnesses means three KEYS (Deut 19:15) — never three invented names.
        from .. import moderation as _mod
        return _ok(_mod.signable((query.get("action") or "").strip(),
                                 query.get("target_id") or "", query.get("actor") or "",
                                 extra=query.get("extra") or ""))
    if method == "POST" and path == "/want":
        # THE WANT LIST — the library grows by its misses. Explicit human asks only; the queue is
        # the hive's return-point, and wants.py enforces the covenant by shape, not judgement.
        from .. import wants as _wants
        if not isinstance(body, dict):
            return _err(400, "query (kind=missing) or card_id (kind=expand) required")
        # The HTTP door is the HUMAN plane (the button, the flag). Agents come through MCP,
        # which opens on the agent plane — held separate until the next human seconds it.
        r = _wants.open_want(query=str(body.get("query") or ""),
                             kind=str(body.get("kind") or "missing"),
                             card_id=str(body.get("card_id") or ""),
                             note=str(body.get("note") or ""), plane="human")
        return (_ok(r) if r.get("ok") else _err(400, r.get("error", "could not record the want")))

    if method == "GET" and path == "/wants":
        # The desiderata list, posted at the desk — a library is honest about its gaps.
        from .. import wants as _wants
        return _ok(_wants.listing(state=(query.get("state") or None),
                                  plane=(query.get("plane") or None)))

    if path == "/unchecked/answer" and method in ("GET", "POST"):
        # THE DOOR THE ASK POINTS AT. `present.derive` puts these links on every engine-written
        # card, so if this route did not exist the guarantee would be a 404 — worse than saying
        # nothing, because it looks like an invitation and is a dead end.
        #
        # GET is accepted deliberately: the link in the card must work for a reader with no
        # scripts, no account and no key, which is most of the people this is for. Nothing here is
        # destructive — an answer is an append to a log, and a single verdict cannot erase a card.
        from .. import unchecked as _unchecked
        src = body if (method == "POST" and isinstance(body, dict)) else query
        r = _unchecked.answer(str(src.get("card") or src.get("card_id") or ""),
                              str(src.get("verdict") or ""),
                              by=str(src.get("by") or ""), note=str(src.get("note") or ""),
                              attestation=(src.get("attestation")
                                           if isinstance(src.get("attestation"), dict) else None))
        return _ok(r) if r.get("ok") else _err(400, r.get("reason", "could not record the answer"))

    if method == "GET" and path == "/unchecked":
        # What the engine has written that no one has looked at yet. A library that publishes its
        # own unchecked list is harder to fool than one that waits to be audited.
        from .. import unchecked as _unchecked
        try:
            _lim = int(query.get("limit") or 100)
        except (TypeError, ValueError):
            _lim = 100                               # bad limit -> the default, never a 500 (red-team #6)
        return _ok(_unchecked.standing(limit=_lim))

    if method == "POST" and path == "/report":
        # The moderation floor: anyone may report; nobody's report is a verdict. One report is a
        # claim; three distinct SIGNING reporters hold the item for a HUMAN steward (Deut 19:15).
        from .. import moderation as _mod
        if not isinstance(body, dict):
            return _err(400, "kind, target_id, reason, signed fields + signature required")
        r = _mod.report(str(body.get("kind") or ""), str(body.get("target_id") or ""),
                        str(body.get("reason") or ""),
                        note=str(body.get("note") or ""),
                        fields=body.get("fields") if isinstance(body.get("fields"), dict) else None,
                        signature=str(body.get("signature") or ""))
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")
    if method == "POST" and path == "/contact":
        # A public "reach the keeper" form. Messages go straight to the KEEP (the operator window) —
        # persisted to a durable inbox and shown newest-first at the top of the dashboard. No email,
        # no address on the page. Honeypot + the rate limiter above guard it.
        from . import contact as _contact
        r = _contact.submit(body)
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "could not send")
    if method == "POST" and path == "/block":
        # Viewer-side and sovereign: filters what YOU see. A boundary, not a verdict — and only
        # the viewer's own signature may raise or lift it (nobody edits another person's eyes).
        from .. import moderation as _mod
        if not isinstance(body, dict):
            return _err(400, "handle, signed fields + signature required")
        fn = _mod.unblock if body.get("off") else _mod.block
        r = fn(blocked_handle=str(body.get("handle") or ""),
               fields=body.get("fields") if isinstance(body.get("fields"), dict) else None,
               signature=str(body.get("signature") or ""))
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")

    if method == "GET" and path == "/activity.json":
        # UNDER THE HOOD (Matt, 2026-08-05): .com is the working surface; .org is the WITNESS,
        # so .org is where "what we are doing" belongs — a live feed of the work. Every seal is
        # ALREADY public at /s/<hash>, so a stream of recent seals leaks nothing new. Whitelist
        # the fields explicitly — hash/short/domain/verdict/kind/when — and NEVER dump a record
        # (no bodies, no claim text, no operator data; keep.json stays gated). Both surfaces:
        # the record of the work is not witness-only content.
        from .. import cas as _cas, capabilities as _caps
        import os as _os, time as _time
        base = _cas._cas_dir()
        rows = []
        try:
            files = []
            if base.exists():
                for pd in base.iterdir():
                    if pd.is_dir() and len(pd.name) == 2:
                        for f in pd.glob("*.json"):
                            try:
                                files.append((f.stat().st_mtime, pd.name + f.stem, f))
                            except OSError:
                                pass
            files.sort(key=lambda x: x[0], reverse=True)
            for mtime, h, f in files[:30]:
                rec = _cas.fetch(h) or {}
                gr = (rec.get("gate_results") or [{}])
                g0 = gr[0] if gr else {}
                verdict = (rec.get("verdict") or rec.get("overall")
                           or g0.get("verdict") or g0.get("status") or "sealed")
                domain = (rec.get("domain") or g0.get("domain") or rec.get("kind") or "")
                rows.append({"hash": h, "short": h[:16],
                             "verdict": str(verdict)[:24], "domain": str(domain)[:40],
                             "kind": str(rec.get("kind") or "seal")[:40],
                             "when": int(mtime)})
        except Exception:  # noqa: BLE001 — the feed must never 500 the surface
            rows = []
        totals = {}
        try:
            sub = _caps._substrate()
            totals = {"cards": (sub.get("cards") or {}).get("count"),
                      "seals": (sub.get("seals") or {}).get("count") or _cas.stats().get("count"),
                      "domains": (sub.get("domains") or {}).get("count")}
        except Exception:  # noqa: BLE001
            try:
                totals = {"seals": _cas.stats().get("count")}
            except Exception:  # noqa: BLE001
                totals = {}
        # freshness lives in the client's cache-busting URL (a browser won't honour no-store on
        # its own — the stale-read lesson); dispatch()'s Response is (status, payload) only.
        return _ok({"surface": surface, "recent": rows, "totals": totals,
                    "note": "Every seal here is already public at /s/<hash>; this is the work, "
                            "in the open. Counts and verdicts only — nothing personal is shown."})

    if method == "GET" and path == "/build.json":
        # DEPLOYMENT PROVENANCE (red team 2026-08-06, R-14/R-06): tie the SERVED contract to a hash
        # a reviewer can compare against the repository, so "is this finding fixed in production or
        # only in source?" is answerable without trusting us. Everything here is derived live from
        # the running code; it leaks nothing — profile NAMES + tool counts, protocol revisions, and
        # a catalog hash. No bodies, no keys, no personal data, no per-tool internals.
        import hashlib as _hl
        try:
            from ..mcp import server as _srv
            catalog = sorted(f"{t}:{eff}" for p in _srv.PROFILES.values()
                             for t, eff in p["tools"].items())
            cat_hash = _hl.sha256("\n".join(catalog).encode("utf-8")).hexdigest()
            profiles = {n: {"version": p.get("version"), "tools": len(p["tools"])}
                        for n, p in _srv.PROFILES.items()}
            protocol = {"supported": list(_srv.SUPPORTED_PROTOCOL_VERSIONS),
                        "default": _srv.negotiate_protocol_version(None)}
        except Exception as e:  # noqa: BLE001 — provenance must never 500 the surface
            return _ok({"surface": surface, "unavailable": str(e)[:120]})
        try:
            from importlib.metadata import version as _ver
            pkg = _ver("concordance")
        except Exception:  # noqa: BLE001
            pkg = None
        return _ok({
            "surface": surface,
            "package_version": pkg,
            "protocol": protocol,
            "profiles": profiles,
            "tool_catalog_hash": cat_hash,
            "note": ("Derived live from the running code. Compare tool_catalog_hash against the "
                     "repository to confirm which catalog is deployed. Profile names and counts "
                     "only — no bodies, keys, or personal data."),
        })

    if method == "GET" and path == "/capabilities":
        # The live capability statement — every public number computed now, with its definition
        # attached. UNGATED on both surfaces by design: what this engine can and cannot do is not
        # witness content, and a reader who cannot check our claims cannot trust them.
        from .. import capabilities as _caps
        return _ok(_caps.statement(surface))

    if method == "GET" and path == "/systems":
        # THE SYSTEMS HANDICAP — operational health of every subsystem as one number each (a golf
        # handicap: low is strong) and one for the course. Computed live from real signals (tests on
        # disk, SOP presence, module resolution, the issue register) so it recomputes itself as the
        # foundation is laid. UNGATED: knowing what is out is not witness content. Feeds site/systems.html.
        from .. import systems as _systems
        return _ok(_systems.report())

    if method == "GET" and path == "/kernel":
        # THE GATE KERNEL — the law, published where agents READ it. The five moves, the eight-rule
        # agent covenant, the six KINDS, the authority lattice, and the nine-field record. UNGATED:
        # the rules an agent must keep are not witness content, and a reader who cannot see the law
        # cannot be held to it. Agents: check a proposed state-change at POST /kernel/gate first.
        from .. import kernel as _kernel
        return _ok(_kernel.doctrine())

    if method == "POST" and path == "/kernel/gate":
        # Route ONE proposed state-change through the kernel and return the verdict + the nine-field
        # record — so an agent can discern before it writes (the covenant: stop when the evidence is
        # incomplete). Pure: this DECIDES and records; it never persists, and it never replaces the
        # caller's own signature / consent checks on the actual write.
        from .. import kernel as _kernel
        if not isinstance(body, dict):
            return _err(400, "a JSON object is required: {artifact, authority_in, evidence, witness, author, ...}")
        art = body.get("artifact")
        if not isinstance(art, dict):
            return _err(400, "artifact must be an object (the thing entering or changing state)")
        asum = body.get("assumptions")
        rec = _kernel.gate(
            art,
            entered_as=str(body.get("entered_as") or ""),
            authority_in=str(body.get("authority_in") or "quarantined"),
            kind_hint=str(body.get("kind_hint") or ""),
            evidence=body.get("evidence"),
            witness=body.get("witness"),
            author=body.get("author"),
            contradicts=bool(body.get("contradicts")),
            error=body.get("error"),
            assumptions=tuple(str(x) for x in asum) if isinstance(asum, list) else (),
            wait_satisfied=bool(body.get("wait_satisfied", True)),
            in_kind_checked=bool(body.get("in_kind_checked", False)),
            content=str(body.get("content") or ""),
        )
        return _ok({"record": rec.to_dict(), "generated": False})

    if method == "GET" and path == "/playbook":
        # THE PLAYBOOK — "Canon commands, Playbook remembers." The Body's testimony of faithful
        # obedience: read-only here (list, or one entry by ?id=). Confirmed testimony is affirmed BY
        # THE BODY — it is NOT Scripture and binds no conscience; the payload says so on every view.
        from .. import playbook as _pb
        eid = (query.get("id") or "").strip()
        if eid:
            got = _pb.get(eid)
            return _ok(got["entry"]) if got.get("ok") else _err(404, "no such entry")
        return _ok(_pb.list_entries(status=query.get("status") or "",
                                    author=query.get("author") or "",
                                    limit=int(query["limit"]) if str(query.get("limit") or "").isdigit() else 50))

    if method == "POST" and path == "/playbook/signable":
        # Step 1: the exact bytes to sign ON THE DEVICE for a create/witness/outcome/prune. The key
        # never travels; the server mints the nonce + clock so stored and signed bytes cannot drift.
        from .. import playbook as _pb
        b = body if isinstance(body, dict) else {}
        op = str(b.get("op") or "entry").strip()
        if op == "entry":
            r = _pb.signable_entry(str(b.get("author") or ""), str(b.get("confession") or ""),
                                   b.get("anchors") if isinstance(b.get("anchors"), list) else [],
                                   str(b.get("action") or ""), str(b.get("situation") or ""),
                                   str(b.get("body") or ""),
                                   int(b["wait_seconds"]) if str(b.get("wait_seconds") or "").isdigit() else _pb.DEFAULT_WAIT_S)
        elif op == "witness":
            r = _pb.signable_witness(str(b.get("witness") or ""), str(b.get("entry_id") or ""),
                                     bool(b.get("affirms", True)), str(b.get("note") or ""))
        elif op == "outcome":
            r = _pb.signable_outcome(str(b.get("by") or ""), str(b.get("entry_id") or ""),
                                     str(b.get("outcome") or ""), str(b.get("note") or ""))
        elif op == "prune":
            r = _pb.signable_prune(str(b.get("by") or ""), str(b.get("entry_id") or ""),
                                   str(b.get("reason") or ""))
        else:
            return _err(400, "op must be entry | witness | outcome | prune")
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")

    if method == "POST" and path == "/playbook/submit":
        # Step 2: verify the detached signature over those exact bytes and enter the testimony / event.
        from .. import playbook as _pb
        b = body if isinstance(body, dict) else {}
        op = str(b.get("op") or "entry").strip()
        fields = b.get("fields") if isinstance(b.get("fields"), dict) else None
        sig = str(b.get("signature") or "")
        if op == "entry":
            r = _pb.record(fields, sig, str(b.get("display_name") or ""))
        elif op == "witness":
            r = _pb.add_witness(fields, sig)
        elif op == "outcome":
            r = _pb.add_outcome(fields, sig)
        elif op == "prune":
            r = _pb.prune(fields, sig)
        else:
            return _err(400, "op must be entry | witness | outcome | prune")
        return _ok(r) if r.get("ok") else _err(400, r.get("error") or "refused")

    if method == "GET" and path == "/plow":
        # THE PLOW — a personal formation companion. STATELESS: the walk lives on the person's own
        # device; this returns a fresh field + the pattern. It works the field, never judges the
        # farmer, and keeps nothing. Ungated: the pattern is not witness content.
        from .. import plow as _plow
        return _ok({"blank": _plow.blank(), "phases": list(_plow.PHASES), "tiers": list(_plow.TIERS),
                    "signals": {"burden": list(_plow.SIGNALS_BURDEN), "fruit": list(_plow.SIGNALS_FRUIT),
                                "triad": list(_plow.TRIAD)}, "scale": _plow._SCALE, "generated": False,
                    "note": "The Plow works the field; it does not judge the farmer. Your walk lives "
                            "on your device — nothing here is stored on the server."})

    if method == "POST" and path == "/plow":
        # The one transition: the client sends its OWN state + today's signals; the engine returns the
        # next state + ONE next step. Pure and stateless — it stores nothing, records no one.
        from .. import plow as _plow
        b = body if isinstance(body, dict) else {}
        sig = b.get("signals") if isinstance(b.get("signals"), dict) else {}
        st = b.get("state") if isinstance(b.get("state"), dict) else None
        return _ok(_plow.step(st, sig))

    if method == "GET" and path == "/harmony":
        # Harmony of the Gospels — one event, every gospel that witnesses it, side by side.
        # Witness content: the same gate as /teachings, /prophecy, /commentary.
        from .. import harmony as harmony_mod
        eid = (query.get("id") or "").strip()
        if eid:
            rec = harmony_mod.get(eid)
            return _ok(rec) if rec is not None else _err(404, "event not found")
        return _ok(harmony_mod.periods())

    if method == "GET" and path == "/timeline":
        # Timeline — Old Testament, New Testament (Acts onward), and Church History, one spine.
        # Witness content: the same gate as /harmony, /teachings, /prophecy, /commentary.
        from .. import timeline as timeline_mod
        eid = (query.get("id") or "").strip()
        if eid:
            rec = timeline_mod.get(eid)
            return _ok(rec) if rec is not None else _err(404, "event not found")
        return _ok(timeline_mod.eras())

    if method == "GET" and path == "/backmatter":
        # Back-matter reference tables — weights & measures, names of God, parables, miracles,
        # book introductions, topical index. Disputes carried, refs verified, Strong's linked.
        # Witness content: the same gate as /harmony and /timeline.
        from .. import backmatter as backmatter_mod
        key = (query.get("table") or "").strip()
        if key:
            rec = backmatter_mod.get_table(key)
            return _ok(rec) if rec is not None else _err(404, "table not found")
        return _ok(backmatter_mod.tables())

    if method == "GET" and path == "/places":
        # The Atlas — real biblical place coordinates, honest uncertainty. Located places carry
        # coordinates; disputed sites name their candidates; unlocatable places stay blanks.
        # Witness content: the same gate as /harmony, /timeline, /backmatter.
        from .. import bible_places as places_mod
        nm = (query.get("name") or "").strip()
        if nm:
            rec = places_mod.get(nm)
            return _ok(rec) if rec is not None else _err(404, "place not found")
        return _ok(places_mod.places())

    if method == "GET" and path == "/narratives":
        # The storyboards — the common narratives charted in the Bible; components (movements)
        # isolate and recombine. Reference points, never identities. Witness content.
        from .. import narratives as narr_mod
        nid = (query.get("id") or "").strip()
        mv = (query.get("movement") or "").strip()
        if nid:
            rec = narr_mod.get(nid)
            return _ok(rec) if rec is not None else _err(404, "storyboard not found")
        if mv:
            rec = narr_mod.by_movement(mv)
            return _ok(rec) if rec is not None else _err(404, "movement not found")
        return _ok(narr_mod.storyboards())

    if method == "GET" and path == "/study_find":
        # The quick-find index — one lookup across the whole reference section (archetypes,
        # storyboards, tables, atlas, harmony, timeline, encyclopedia). Witness content.
        from .. import study_index as si_mod
        return _ok(si_mod.find(query.get("q") or "", limit=40))

    if method == "GET" and path == "/teachings":
        # Phase 3 — the teaching-review workspace (Words in Red). Witness content: the engine
        # assembles the frozen Greek anchor + existing sites; the operator records the reading.
        from .. import teachings as teachings_mod
        tid = (query.get("id") or "").strip()
        if tid:
            rec = teachings_mod.get(tid)
            return _ok(rec) if rec is not None else _err(404, "teaching not found")
        return _ok(teachings_mod.queue())

    return _err(404, "not found")


# ── Route registry — ONE declaration per route ───────────────────────────
# Each entry carries a route's methods + metadata: api = a JSON/API GET that must be served
# even when the static site is mounted (else it would fall through to the site handler);
# rl = rate-limited; serve = handled in the serve() Handler rather than dispatch() (e.g. the
# streamed /speak, the site-or-json /card.html). The two sets the server actually consults
# (_API_GET_PATHS, RATELIMITED) are DERIVED below, so a route's metadata lives in exactly one
# place. tests/test_routes.py locks the derivation to the historical values AND asserts every
# path dispatch() handles is registered here — so the two can never silently drift apart.
def resolve_mcp_profile(path: str):
    """(profile_or_None, refusal_or_None) for an /mcp* path — ONE resolution for both doors.

    The streaming Handler and dispatch() must agree about which planes exist and whether the
    community plane is enabled, or a client would get different boundaries depending on which
    code path served it. Community is a deployment decision (assessment F-13): publish-class
    tools need governance with a named owner before a host serves them, so the door is closed
    unless CONCORDANCE_COMMUNITY_MCP=1 — and the refusal says so, a sign rather than a void.
    """
    import os
    if not path.startswith("/mcp/"):
        return None, None
    from ..mcp.server import PROFILES
    profile = path[len("/mcp/"):]
    if profile not in PROFILES:
        return None, (404, {"error": f"unknown MCP profile '{profile}'",
                            "profiles": sorted(PROFILES)})
    if profile == "community" and os.environ.get("CONCORDANCE_COMMUNITY_MCP", "").strip() != "1":
        return None, (403, {
            "error": "the community profile is not enabled on this host",
            "why": ("publish-class tools (groups, mesh, commons, moderation) require a "
                    "deployment decision with governance attached; set "
                    "CONCORDANCE_COMMUNITY_MCP=1 to serve this plane"),
            "available": sorted(p for p in PROFILES if p != "community")})
    return profile, None


ROUTES = [
    {"path": "/", "methods": ("GET",)},
    {"path": "/health", "methods": ("GET",), "api": True},
    {"path": "/speak/health", "methods": ("GET",), "api": True},
    {"path": "/tv/lineup", "methods": ("GET",), "api": True},
    {"path": "/health/memory", "methods": ("GET",), "api": True},
    {"path": "/now", "methods": ("GET",), "api": True},
    {"path": "/identity", "methods": ("GET",), "api": True},
    {"path": "/route", "methods": ("GET",), "api": True},
    {"path": "/bind/challenge", "methods": ("GET",), "api": True},
    {"path": "/bind", "methods": ("POST",), "rl": True},
    {"path": "/book", "methods": ("POST",), "rl": True},
    {"path": "/inlet", "methods": ("POST",), "rl": True},
    {"path": "/returns", "methods": ("POST",), "rl": True},
    {"path": "/fork", "methods": ("POST",), "rl": True},
    {"path": "/defer", "methods": ("POST",), "rl": True},
    {"path": "/thread/lineage", "methods": ("GET",), "api": True},
    {"path": "/land", "methods": ("GET",), "api": True},
    {"path": "/cards/for-the-group", "methods": ("GET",), "api": True},
    {"path": "/thread/recalled", "methods": ("GET",), "api": True},
    {"path": "/thread/digest", "methods": ("GET",), "api": True},
    {"path": "/thread/recall", "methods": ("GET",), "api": True},
    {"path": "/verify", "methods": ("POST",), "rl": True},
    {"path": "/derivation/verify", "methods": ("POST",), "rl": True},
    {"path": "/audit", "methods": ("POST",), "rl": True},
    {"path": "/context/run", "methods": ("POST",), "rl": True},  # the context loop — node-local (gated by CONCORDANCE_SOVEREIGN_NODE)
    {"path": "/chess", "methods": ("POST",), "rl": True},
    {"path": "/path", "methods": ("GET",), "api": True},
    {"path": "/days", "methods": ("POST",), "rl": True},
    {"path": "/ask", "methods": ("POST",), "rl": True},
    {"path": "/console", "methods": ("POST",), "rl": True},
    {"path": "/journal", "methods": ("GET", "POST"), "api": True},
    {"path": "/steward/budget", "methods": ("POST",)},
    {"path": "/steward/cost-destroyed", "methods": ("POST",)},
    {"path": "/steward/ask", "methods": ("POST",)},
    {"path": "/groups", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/group", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/group/join", "methods": ("POST",), "rl": True},
    {"path": "/group/contribute", "methods": ("POST",), "rl": True},
    {"path": "/mesh", "methods": ("GET",), "api": True},
    {"path": "/mesh/node", "methods": ("POST",), "rl": True},
    {"path": "/mesh/link", "methods": ("POST",), "rl": True},
    {"path": "/mesh/map", "methods": ("GET",), "api": True},
    {"path": "/mesh/post", "methods": ("POST",), "rl": True},
    {"path": "/mesh/inbox", "methods": ("GET",), "api": True},
    {"path": "/mesh/tend", "methods": ("POST",), "rl": True},
    {"path": "/mesh/invite", "methods": ("POST",), "rl": True},
    {"path": "/mesh/redeem", "methods": ("POST",), "rl": True},
    {"path": "/mesh/door", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/formation", "methods": ("GET",), "api": True},
    {"path": "/formation/kinds", "methods": ("GET",), "api": True},
    {"path": "/formation/help", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/push/key", "methods": ("GET",), "api": True},
    {"path": "/push/subscribe", "methods": ("POST",), "rl": True},
    {"path": "/push/unsubscribe", "methods": ("POST",), "rl": True},
    {"path": "/coach/mastery", "methods": ("POST",), "rl": True},
    {"path": "/identity/create", "methods": ("POST",), "rl": True},
    {"path": "/identity/verify", "methods": ("POST",), "rl": True},
    {"path": "/profile", "methods": ("GET",), "api": True},   # your keeping, keyed by fingerprint (opt-in)
    {"path": "/profile/served", "methods": ("GET",), "api": True},   # serving — your wants, met or still sought
    {"path": "/profile/community", "methods": ("GET",), "api": True},   # community — the narrow-path invitation (no member data on an open read)
    {"path": "/profile/community/signable", "methods": ("POST",), "rl": True},   # bytes to sign for a fellowship view
    {"path": "/profile/community/view", "methods": ("POST",), "rl": True},   # SIGNED fellowship view — gated by confession
    {"path": "/profile/path", "methods": ("GET",), "api": True},   # discipleship — your walked path with the coach
    {"path": "/profile/signable", "methods": ("POST",), "rl": True},
    {"path": "/profile/save", "methods": ("POST",), "rl": True},   # signed write — no account, no password
    {"path": "/profile/erase", "methods": ("POST",), "rl": True},  # signed delete — yours to take back
    {"path": "/badges", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/self-attest", "methods": ("POST",)},
    {"path": "/study", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/study/export", "methods": ("POST",), "rl": True},
    {"path": "/study/import", "methods": ("POST",), "rl": True},
    {"path": "/mcp", "methods": ("POST",), "rl": True},
    {"path": "/mcp/core", "methods": ("POST",), "rl": True},
    {"path": "/mcp/library", "methods": ("POST",), "rl": True},
    {"path": "/mcp/sovereign", "methods": ("POST",), "rl": True},
    {"path": "/mcp/coach", "methods": ("POST",), "rl": True},
    {"path": "/mcp/witness", "methods": ("POST",), "rl": True},
    {"path": "/mcp/community", "methods": ("POST",), "rl": True},
    {"path": "/search", "methods": ("GET",), "api": True, "rl": "read"},
    # These GET routes scan/sort the whole resident corpus per request — put them on the READ bucket so an
    # unauthenticated flood cannot pin every core and starve /verify (red-team #1). /card is a bounded
    # single-id lookup and stays unlimited.
    {"path": "/cards/stats", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/cards", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/card", "methods": ("GET",), "api": True},
    {"path": "/witness", "methods": ("GET",), "api": True, "rl": "read"},   # Cloud of Witnesses' voice — PD, attributed; scans the corpus so read-bucket limited like /search
    {"path": "/daily", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/card/connections", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/graph", "methods": ("GET",), "api": True},
    {"path": "/floor", "methods": ("GET",), "api": True},
    {"path": "/locate", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/library/health", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/growth", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/pronounce", "methods": ("GET",), "api": True},
    {"path": "/thread", "methods": ("DELETE", "GET"), "api": True},
    {"path": "/threads", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/threads/search", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/thread/verify", "methods": ("GET",), "api": True},
    {"path": "/journal/dates", "methods": ("GET",), "api": True},
    {"path": "/steward", "methods": ("GET",), "api": True},
    {"path": "/coach/subjects", "methods": ("GET",), "api": True},
    {"path": "/coach/overview", "methods": ("GET",), "api": True},
    {"path": "/coach/journey", "methods": ("GET",), "api": True},
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
    {"path": "/harmony", "methods": ("GET",), "api": True},
    {"path": "/timeline", "methods": ("GET",), "api": True},
    {"path": "/backmatter", "methods": ("GET",), "api": True},
    {"path": "/places", "methods": ("GET",), "api": True},
    {"path": "/narratives", "methods": ("GET",), "api": True},
    {"path": "/study_find", "methods": ("GET",), "api": True},
    {"path": "/capabilities", "methods": ("GET",), "api": True},
    {"path": "/systems", "methods": ("GET",), "api": True, "rl": "read"},
    {"path": "/kernel", "methods": ("GET",), "api": True},
    {"path": "/kernel/gate", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/playbook", "methods": ("GET",), "api": True},
    {"path": "/playbook/signable", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/playbook/submit", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/plow", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/activity.json", "methods": ("GET",), "api": True},
    {"path": "/build.json", "methods": ("GET",), "api": True},
    {"path": "/mesh/signable", "methods": ("GET",), "api": True},
    {"path": "/attest", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/consent/signable", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/consent", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/consent/revoke", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/connect/event", "methods": ("POST",), "api": True, "rl": True},
    # THE COMMONS (C1b): the shelf, the drops, the curation desk.
    {"path": "/drop/signable", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/drop", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/shelf", "methods": ("GET",), "api": True},
    {"path": "/commons", "methods": ("GET",), "api": True},
    {"path": "/curate/queue", "methods": ("GET",), "api": True},
    {"path": "/curate/signable", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/curate", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/moderation/signable", "methods": ("GET",), "api": True, "rl": True},
    {"path": "/want", "methods": ("POST",), "rl": True},
    {"path": "/wants", "methods": ("GET",), "api": True},
    {"path": "/unchecked", "methods": ("GET",), "api": True},
    {"path": "/unchecked/answer", "methods": ("GET", "POST"), "api": True, "rl": True},
    {"path": "/report", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/block", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/contact", "methods": ("POST",), "api": True, "rl": True},
    {"path": "/seeds", "methods": ("GET",), "api": True},
    {"path": "/almanac", "methods": ("GET",), "api": True},
    {"path": "/apothecary", "methods": ("GET",), "api": True},
    {"path": "/apothecary/propose", "methods": ("POST",), "rl": True},
    {"path": "/pins", "methods": ("POST",), "rl": True},
    {"path": "/pins/done", "methods": ("POST",), "rl": True},
    {"path": "/codex", "methods": ("GET",), "api": True},
    {"path": "/codex/scripture", "methods": ("GET",), "api": True},
    {"path": "/codex/themes", "methods": ("GET",), "api": True},
    {"path": "/codex/connections", "methods": ("GET",), "api": True},
    {"path": "/codex/artifact", "methods": ("GET",), "api": True},
    {"path": "/codex/verify", "methods": ("GET",), "api": True},
    {"path": "/works", "methods": ("GET",), "api": True},
    {"path": "/works/item", "methods": ("GET",), "api": True},
    {"path": "/works/artifact", "methods": ("GET",), "api": True},
    {"path": "/works/verify", "methods": ("GET",), "api": True},
    {"path": "/decks", "methods": ("GET",), "api": True},
    {"path": "/decks/predict", "methods": ("GET",), "api": True},
    {"path": "/deck", "methods": ("GET",), "api": True},
    {"path": "/deck/open", "methods": ("GET",), "api": True},
    {"path": "/archetypes", "methods": ("GET",), "api": True},
    {"path": "/archetypes/match", "methods": ("GET",), "api": True},
    {"path": "/archetype", "methods": ("GET",), "api": True},
    {"path": "/teachings", "methods": ("GET",), "api": True},
    {"path": "/card.html", "methods": ("GET",), "api": True, "serve": True},
    {"path": "/speak", "methods": ("POST",), "rl": True, "serve": True},
    # Retired pages — see _RETIRED and the /daily.html handler in serve(). `retired` marks a path
    # that is deliberately linked from NOWHERE: it exists to catch inbound links we do not control
    # (bookmarks, old indexes, crawlers) and send them where the content actually went. A live page
    # linking to one would be the drift — pointing readers at a tombstone instead of the destination.
    {"path": "/daily.html", "methods": ("GET",), "serve": True, "retired": True},
    {"path": "/hymns.html", "methods": ("GET",), "serve": True, "retired": True},
    # THE CORPUS: four pages were doing one job under four invented names. They are now four
    # sections of /corpus.html, and every old address still resolves.
    {"path": "/library.html", "methods": ("GET",), "serve": True, "retired": True},
    {"path": "/catalog.html", "methods": ("GET",), "serve": True, "retired": True},
    {"path": "/codex.html", "methods": ("GET",), "serve": True, "retired": True},
    {"path": "/works.html", "methods": ("GET",), "serve": True, "retired": True},
    # The 1.0 canon reader. Caddy has been 301ing this to /bible.html since the cutover and
    # DROPPING the ?ref= on the way — 3,020 hard 404s on the witness host, and on the secular host
    # a reader landing on a generic Bible page with the reference silently gone. Handled here now
    # so the reference travels; the Caddy line is removed.
    {"path": "/canon.html", "methods": ("GET",), "serve": True, "retired": True},
]

# A page that existed and is gone is NOT a 404. Each entry names where its content actually
# lives now — and only pages with a real successor belong here. When nothing holds the content
# any more, the honest answer is to leave it 404 rather than send a reader somewhere plausible.
_RETIRED = {
    # THE CUT of 2026-08-05 (lever 5, Matt-approved): measured over 7 days of access logs,
    # 31 pages earned fewer than 12 visits — below the scanner-noise line — while /search,
    # /card, /encyclopedia, /graph, /characters, /bible and the desk carried the site.
    # 43 files -> 8 (+ routes). Every entry names the FINAL home of its content, no chains.
    "/hymns.html": "/?q=hymns",                           # the desk searches the keeping
    "/library.html": "/",
    "/catalog.html": "/",
    "/codex.html": "/",
    "/works.html": "/proof.html",                         # worked, sealed demonstrations ARE the proof
    "/canon.html": "/bible.html",                         # the Word — and ?ref= still arrives with it
    "/corpus.html": "/",                                  # the desk is the one door to the shelves
    "/almanac.html": "/",
    "/apothecary.html": "/",
    "/ask.html": "/",                                     # the desk asks
    "/audit.html": "/proof.html",
    "/backmatter.html": "/bible.html",
    "/boundary.html": "/proof.html",
    "/brain.html": "/graph",
    "/check.html": "/connect.html",
    "/collapse.html": "/proof.html",
    "/community.html": "/",
    "/companion.html": "/",
    "/corrected.html": "/proof.html",
    "/days.html": "/",
    "/floor.html": "/graph",
    "/game.html": "/",
    "/guarantees.html": "/proof.html",
    "/harmony.html": "/bible.html",
    "/journal.html": "/",
    "/map.html": "/graph",
    "/mesh.html": "/",
    "/narratives.html": "/bible.html",
    "/places.html": "/encyclopedia.html",
    "/reason.html": "/proof.html",
    "/seal.html": "/proof.html",
    "/seeds.html": "/proof.html",
    "/shelf.html": "/",
    "/steward.html": "/",
    "/teachings.html": "/bible.html",
    "/theories.html": "/graph",                           # the theory map lives in the constellation
    "/timeline.html": "/bible.html",
    "/tv.html": "https://narrowhighway.tv/",
    "/voices.html": "/bible.html",
    "/walk.html": "/read.html",
}


def _retire_to(path: str, query: str) -> str:
    """Where a retired path goes, CARRYING WHAT IT WAS ASKED FOR.

    A redirect that drops the query is the /canon.html failure: `?ref=X` 301s to a generic page,
    the reader lands somewhere plausible with the reference gone, and nothing reports it. So the
    incoming query is merged onto the destination's own, and the incoming side wins — a link that
    says `?ref=Aaron` means Aaron, whatever section the destination would have opened by default.

    Each destination is the FINAL one, not a hop into another retired page: /hymns.html goes
    straight to the Corpus with its shelf, not through library.html on the way.
    """
    dest = _RETIRED[path]
    if not query:
        return dest
    base, _, own = dest.partition("?")
    merged = dict(parse_qsl(own, keep_blank_values=True))
    merged.update(dict(parse_qsl(query, keep_blank_values=True)))
    return base + ("?" + urlencode(merged) if merged else "")

# The JSON/API GET paths (served even with a static site mounted) — DERIVED from ROUTES.
_API_GET_PATHS = frozenset(r["path"] for r in ROUTES if r.get("api"))
# The rate-limited paths (consulted in serve()) — DERIVED from ROUTES.
#
# TWO buckets, because a read and a write are not the same risk. Both were sharing one 120/min
# cap per client. Re-based on the FULL logs (2026-08-01): 441 refusals ever served — 313 to
# ClaudeBot, mostly /search, across all three hosts. Refusing a reader on the search path is
# refusing the use we asked for, at any percentage.
#
# The ceiling is not removed, it is separated and raised. /search runs FTS across the shards; an
# unbounded one on a 7 GB box is a real exposure, so one source still cannot exhaust it. Writes
# keep the tighter cap they always had.
RATELIMITED = tuple(r["path"] for r in ROUTES if r.get("rl") is True)
READ_LIMITED = tuple(r["path"] for r in ROUTES if r.get("rl") == "read")


def build_server(host: str = "127.0.0.1", port: int = 8000, surface: str = "secular",
                 site_dir: str = None, warm: bool = True):
    """The configured server, built but NOT started — so a test can bind port 0 and drive the real
    wire. `serve()` below is this plus `serve_forever()`.

    Split out 2026-07-29: some guarantees live in the request handler, not in `dispatch()` — the
    `cache-control` header is one. A dispatch-level test would have passed the whole time the wire
    stayed silent about caching, which is how a stale shelf reached a real browser. Pass
    `warm=False` to skip the ~5s corpus/verifier warm when a test does not need it."""
    import json
    import mimetypes
    import os
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from pathlib import Path
    from urllib.parse import parse_qs, quote, urlparse

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
    read_limiter = ratelimit.from_env(read=True)   # the generous bucket — see READ_LIMITED
    MAX_BODY = int(os.environ.get("CONCORDANCE_MAX_BODY", str(256 * 1024)) or 256 * 1024)
    # RATELIMITED is derived from the ROUTES registry (module-level) — single source of truth.

    class Handler(BaseHTTPRequestHandler):
        # Don't advertise the exact Python/http.server version (aids targeted attacks).
        server_version = "NarrowHighway"
        sys_version = ""

        def handle(self) -> None:
            """A thread returns what it borrowed.

            This server is thread-per-connection and corpus_db is connection-per-thread-per-shard,
            so without this `finally` the two multiply without bound. On 2026-08-01 a 250-request
            read burst drove the secular engine to 1023 of 1024 file descriptors and every POST
            /verify then answered 500 — Python could not open receipts.py to import it. Reading
            knocked out proving. The close belongs here, at the one place every request path ends,
            rather than in each route that happens to touch a shard.

            Once per CONNECTION, not per request: keep-alive still reuses an open shard.
            """
            try:
                super().handle()
            finally:
                try:
                    from .. import corpus_db as _cdb
                    _cdb.close_this_thread()
                except Exception:  # noqa: BLE001 — cleanup must never raise into the socket loop
                    pass

        def _json(self, status: int, payload: dict, extra: dict = None) -> None:
            """Every JSON answer here is computed fresh, so every one says so.

            Until 2026-07-29 no API response carried a `cache-control` header at all. A response
            with no directive is HEURISTICALLY cacheable: a browser, a proxy, or a CDN may serve a
            stale copy and be within spec. That surfaced on the Commons as a shelf that was exactly
            one write behind — a member withdrew a card, the store recorded it, and the page still
            showed the card. The reader was told the opposite of the record.

            It was never a shelf bug. It was every read endpoint on this server, so the fix belongs
            here in the one place they all pass through rather than as a cache-buster on one page.
            `extra` still wins, so a route that genuinely wants to be cached can say so out loud.
            """
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("x-content-type-options", "nosniff")
            if "cache-control" not in {k.lower() for k in (extra or {})}:
                self.send_header("cache-control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _static(self, path: str) -> None:
            # The Domain Sort flip: on .com the homepage IS the tool (see home_for). Witness untouched.
            path = home_for(surface, site, path)
            # Resolution (clean-URL + traversal guard) lives in resolve_site_file() so it is unit-
            # tested without warming the server; None means no such file (or an escape attempt).
            fp = resolve_site_file(site, path)
            if fp is None:
                return self._json(404, {"error": "not found"})
            body = fp.read_bytes()
            ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("content-type", ctype)
            self.send_header("x-content-type-options", "nosniff")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _redirect(self, status: int, location: str) -> None:
            self.send_response(status)
            self.send_header("location", location)
            self.send_header("content-length", "0")
            # a 302 must not be cached — its destination is computed per request
            if status != 301:
                self.send_header("cache-control", "no-store")
            self.end_headers()

        def _html(self, status: int, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("x-content-type-options", "nosniff")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _rl_key(self) -> str:
            """Rate-limit key: the REAL client. Caddy (the single trusted proxy, same host) APPENDS the
            peer to X-Forwarded-For, so behind Caddy the real client is the LAST hop. But X-Forwarded-For
            is trusted ONLY when the request actually arrived from the trusted proxy (the socket peer is
            loopback / a configured proxy). A request that reaches the origin port DIRECTLY (bypassing
            Caddy) has an untrusted peer, so its client-supplied XFF is IGNORED and we key on the real
            socket IP — a rotating X-Forwarded-For can no longer mint a fresh bucket per request
            (red-team #3). Configure non-loopback proxies via CONCORDANCE_TRUSTED_PROXY (comma-separated)."""
            import os as _os
            peer = self.client_address[0] if self.client_address else "?"
            trusted = {"127.0.0.1", "::1", "localhost"}
            trusted |= {p.strip() for p in (_os.environ.get("CONCORDANCE_TRUSTED_PROXY", "") or "").split(",")
                        if p.strip()}
            if peer in trusted:
                parts = [p.strip() for p in (self.headers.get("x-forwarded-for") or "").split(",") if p.strip()]
                if parts:
                    return parts[-1]
            return peer or "?"

        def _keep(self, u) -> None:
            """The operator's window. The DATA (/keep.json) is operator-gated; the sign-in SHELL
            (/keep.html) is served publicly so the operator can sign in from any device — no operator
            data is exposed until /keep.json authenticates. (Trades the old hide-existence for a real
            sign-in, per operator decision 2026-07-25.) SECURITY: the operator decision uses the REAL
            socket peer + token (?token= or the X-Keep-Token header) only; the spoofable
            X-Forwarded-For is never consulted for access (see keep.is_operator)."""
            from .keep import dashboard as _keep_dash
            from .keep import request_is_operator
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            peer_ip = self.client_address[0] if self.client_address else ""
            if u.path == "/keep.json":
                if not request_is_operator(peer_ip, self.headers, q):
                    return self._json(404, {"error": "not found"})   # the DATA stays gated
                return self._json(200, _keep_dash(config), {"cache-control": "no-store"})
            # the SHELL — only a sign-in prompt; reveals no operator data
            if site is not None:
                return self._static("keep.html")
            return self._json(404, {"error": "not found"})

        def _do(self, method: str) -> None:
            """Catch-all: any unhandled exception becomes a clean JSON 500 for the CALLER — never a
            dropped connection or a leaked traceback (that would defeat the Server-header
            hardening). But it is logged for US.

            Found by pressure test 2026-08-01: /wants began answering 500 on the secular process
            while the identical code served 200 on the witness, and the log said NOTHING. A
            restart healed it and took the evidence with it. A failure that leaves no trace is
            the same blindness as a log glob that silently reads one file — we could not tell
            our own fault from the caller's. The caller still learns nothing; the operator now
            learns everything.
            """
            try:
                self._do_inner(method)
            except Exception:
                try:
                    import sys as _sys
                    import traceback as _tb
                    print("[500] " + method + " " + str(self.path) + "\n" + _tb.format_exc(),
                          file=_sys.stderr, flush=True)
                except Exception:  # noqa: BLE001 — logging must never mask the 500 itself
                    pass
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
                    # SERVED FROM HERE, not from site/robots.txt — editing the file does nothing,
                    # which is how the first attempt at this change silently failed. Kept generated
                    # because the Sitemap line must name the requesting host.
                    #
                    # Readers and AI agents: welcome, explicitly. ClaudeBot is the single largest
                    # agent we serve (~67k requests across the hosts, full-log 2026-08-01) and the
                    # card permalink is among the most-used things we have — the intended use.
                    #
                    # SEO backlink crawlers: refused by name. SemrushBot alone was 26,883 requests
                    # on the .tv host (34.5% of .tv; ~3% site-wide — re-measured 2026-08-01 with FULL logs (the earlier figure was read from tv.access.log alone — the only log file readable without sudo — and covered 9% of traffic)),
                    # indexing us for a marketing product nobody here uses.
                    # This is a free library on one small box; that capacity belongs to readers and
                    # to agents that actually cite us. Named individually, never a blanket rule, so
                    # a genuine reader is never caught by it.
                    seo = ("SemrushBot", "AhrefsBot", "MJ12bot", "DotBot", "BLEXBot")
                    b = ("# Narrow Highway — a public verification engine.\n"
                         "# Agents: read /llms.txt, then use /search and /card. No login, and\n"
                         "# nothing here records who read what.\n"
                         "User-agent: *\nAllow: /\nDisallow: /keep\nDisallow: /keep.html\n\n"
                         "# SEO backlink crawlers — this capacity belongs to readers.\n"
                         + "".join(f"User-agent: {n}\nDisallow: /\n" for n in seo)
                         + f"\nSitemap: {base}/sitemap.xml\n").encode("utf-8")
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
                status, html = render_seal_html(h, cas.fetch_anywhere(h))
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
            if u.path in RATELIMITED or u.path in READ_LIMITED:
                read = u.path in READ_LIMITED
                lim = read_limiter if read else limiter
                key = self._rl_key()
                if not lim.allow(key):
                    return self._json(429, {"error": "rate limit exceeded"},
                                      {"retry-after": str(lim.retry_after(key))})
            if u.path == "/mcp" or u.path.startswith("/mcp/"):
                # Full catalog on /mcp (existing clients keep working); PROFILE MOUNTS on
                # /mcp/<name> — the assessment's §3.3 made deployment-real. A client that mounts
                # /mcp/library sees and may call ONLY the library plane; a call across planes is
                # refused by name. See docs/MCP_ASSESSMENT_2026-08-04.md and task #123.
                from ..mcp.http import handle_http
                profile, refusal = resolve_mcp_profile(u.path)
                if refusal is not None:
                    return self._json(refusal[0], refusal[1])
                raw = b""
                if method == "POST":
                    n = int(self.headers.get("content-length") or 0)
                    raw = self.rfile.read(n) if n else b""
                status, hdrs, body = handle_http(method, self.headers, raw, config,
                                                 profile=profile)
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
            # RETIRED PAGES — answered with where the content WENT.
            #
            # Both are 1.0 pages on narrowhighway.tv, and both were 404ing: 70 requests for
            # /daily.html and 63 for /hymns.html, every one of them with no referrer — bookmarks,
            # crawlers, and old indexes still asking. A 404 says "no such thing ever existed",
            # which is false. So each is sent to what actually holds its content now.
            #
            # The discipline is the one /canon.html breaks: a redirect must land on the thing that
            # was asked for. /canon.html?ref=X 301s to bible.html having dropped the ref, so the
            # reader arrives somewhere plausible and wrong. These two have real successors — 97
            # hymn cards on a shelf, and the daily card itself — so the redirect is honest.
            if method == "GET" and u.path == "/daily.html":
                # 302, never 301: today's card is a different card tomorrow, and a permanent
                # redirect would be cached in browsers pointing at one frozen day forever.
                c = corpus.daily(None)
                if c and c.get("id"):
                    return self._redirect(302, "/card/" + quote(str(c["id"]), safe=""))
                return self._json(404, {"error": "the keeping is empty"})
            if method == "GET" and u.path in _RETIRED:
                return self._redirect(301, _retire_to(u.path, u.query))
            # static site (GET only) for non-API paths, when a site dir is configured
            if method == "GET" and site is not None and u.path not in _API_GET_PATHS:
                # Domain Sort Part 2: family/teaching pages have moved to .org — 301 there (secular
                # only; the API routes above already ran, so agent endpoints never redirect).
                org = redirect_for(surface, u.path)
                if org is not None:
                    return self._redirect(301, org + (("?" + u.query) if u.query else ""))
                return self._static(u.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            body = None
            if method == "POST":
                n = int(self.headers.get("content-length") or 0)
                raw = self.rfile.read(n) if n else b""
                try:
                    body = json.loads(raw or b"{}")
                except (ValueError, TypeError, RecursionError):
                    # RecursionError: a deeply-nested JSON payload ([[[[…]]]]) — treat as an empty/invalid
                    # body so the handler returns a clean 400, never a 500 + traceback (red-team #5).
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

        def do_HEAD(self) -> None:
            # Health checkers HEAD the MCP mounts (measured 2026-08-05: 501s from the server
            # class, which knows no do_HEAD). A reachable mount answers 204; everything else
            # keeps the old behaviour rather than growing an untested HEAD surface.
            from urllib.parse import urlparse as _up
            p = _up(self.path).path
            if p == "/mcp" or p.startswith("/mcp/"):
                self.send_response(204)
                self.send_header("Allow", "POST, GET, DELETE")
                self.end_headers()
                return
            self.send_response(501)
            self.end_headers()

        def log_message(self, *args) -> None:  # quiet
            pass

    class _QuietServer(ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            pass  # no stderr tracebacks (info leak); handlers already return clean JSON 500s

    # Warm the heavy singletons at boot (behind their locks) so the first request skips the
    # ~5s corpus+graph build, and concurrent first-hits can't stampede it. Also pre-import the
    # heavy verify deps (sympy/scipy/numpy) so the FIRST heavy-domain verification never pays a
    # cold C-extension import inside the per-verification timeout (which could shed a TRUE claim
    # to a transient ERROR — errs safe, but a false negative). See derivation.warm().
    if warm:
        try:
            corpus.default_corpus()
            from .. import graph as _graph_warm
            _graph_warm._graph()
            from ..derivation import warm as _warm_verify
            _warm_verify()
        except Exception:
            pass

    return _QuietServer((host, port), Handler)


def resolve_site_file(site, path: str):
    """Map a request path to a file under `site`, or None if there is none.

    Clean URLs (Matt, 2026-08-22 — "2 paths on everything"): `/golf` resolves to `golf.html`
    when the bare path names no file and carries no extension, so every page answers to BOTH its
    clean address and its old `/page.html` one — no forced redirect, whichever they type is served.
    Traversal-guarded: a resolved path that escapes `site` (`../`) returns None. Extensioned paths
    that miss (a stray `.css`) are NOT retried as `.html`. Pure and importable so the behaviour is
    unit-tested without warming the whole server (tests/test_clean_urls.py).
    """
    rel = path.lstrip("/") or "index.html"
    fp = (site / rel).resolve()
    if (not fp.is_file()) and "." not in rel.rsplit("/", 1)[-1]:
        alt = (site / (rel + ".html")).resolve()
        if alt.is_relative_to(site) and alt.is_file():
            fp = alt
    if not fp.is_relative_to(site) or not fp.is_file():
        return None
    return fp


def home_for(surface: str, site, path: str) -> str:
    """The bare homepage. The Domain Sort flip (Matt, 2026-08-24) had put the working auditor
    (/checkit) at "/" on the .com surface. REVERTED 2026-08-30 (Matt: "the homepage still doesn't
    really show what it does. What are we? Provide a clear value add.") — the auditor is a narrow
    commercial wedge that never says what Narrow Highway IS or that a family is served. "/" now serves
    the DESK (index.html), whose hero states the value plainly and whose doors show the whole offering;
    the auditor stays reachable at /checkit and on the 'Check a claim' door. Reversible: restore the
    branch `if surface == "secular" and path == "/" and resolve_site_file(site, "/checkit"): return
    "/checkit"` to put the wedge back at "/"."""
    return path


# Domain Sort Part 2 (Matt, 2026-08-24): the family / teaching / scripture HUMAN PAGES whose home is
# the .org witness. On the .com (secular) surface they 301 to their .org twin; .org serves them.
#
# ONLY HUMAN PAGES MOVE — agent endpoints never do, which the live surface bore out and pruned this
# set: characters, prophecy, harmony, timeline, backmatter, places, narratives, teachings, seeds,
# journal, steward all answer their clean URL with application/json — they are AGENT ENDPOINTS, not
# pages, so redirecting them would move the machine plane (forbidden). They correctly stay on .com;
# their family CONTENT is already surface-gated in the engine and rendered through the desk. What
# remains as a genuine static human page moving to .org is this short, verified list (each 200 on
# .org, each a real HTML page that 301s cleanly). Expand it only for pages that are actually served
# HTML, never a JSON route. (situations = crisis-first, stays everywhere; almanac/profile: later.)
MOVED_TO_ORG = frozenset({"bible", "read", "encyclopedia"})


def redirect_for(surface: str, path: str):
    """The .org home for a moved family/teaching page, or None. Pure and testable; the set is the
    sort. Reversible — remove a name and .com serves the page again."""
    if surface != "secular":
        return None
    base = path.strip("/").rsplit("/", 1)[-1]
    if base.endswith(".html"):
        base = base[:-5]
    if base in MOVED_TO_ORG:
        return "https://narrowhighway.org" + path
    return None


def serve(host: str = "127.0.0.1", port: int = 8000, surface: str = "secular",
          site_dir: str = None) -> None:
    """Thin http.server shell: the API + (optionally) the static site, same-origin. Stdlib only."""
    httpd = build_server(host, port, surface, site_dir)
    where = f" + site {site_dir}" if site_dir else ""
    print(f"Narrow Highway API ({surface}) on http://{host}:{port}{where}")
    httpd.serve_forever()
