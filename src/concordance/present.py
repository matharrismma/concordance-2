"""THE EXPERIENCE LAYER — the card stays bare; the magic is derived on the way out.

Matt, 2026-07-29: *"We want our card to be bare, but we want the user experience to be a bit
magical, so we can take the cards and add an experience layer on top without slowing the process
down too much."*

Two rules, and they are the whole module:

**1. NOTHING HERE IS EVER STORED.** A card holds facts — `url`, `sha256`, `fetched_at`,
`drop_kind`, `reach`. It never holds "🔗", "youtube.com", or "3 minutes ago". Presentation written
into a record goes stale the instant it is written (a "2 minutes ago" from last March), and it
bloats every copy of the card on every device and every shard. The keeping is a substrate, not a
skin. `derive()` reads a card and returns a *separate* block; the caller may attach it under
`presentation` for this response only.

**2. IT MUST BE FREE.** Pure functions, no I/O, no network, no corpus load — string and integer
work over one card. A read of 40 cards must not become 40 fetches, or the layer would buy polish
with the very speed that makes the cards worth having. There is a small cache keyed by
`(id, updated_at)` so a card presented twice costs nothing the second time; because the key carries
`updated_at`, a changed card can never serve a stale presentation.

What "magical" means here, concretely: a reader should be able to tell at a glance what a thing IS
and whether to trust it — is this a recipe or a question, whose is it, where does the link actually
go, when did we last look, and has anyone vouched for it. All of that is *already* in the bare card.
The layer only says it in human.

Honest by construction: every string below is derived from a field that is present. Where the card
does not say, this returns nothing rather than a confident guess — an "unknown" rendered as a
plausible label is the exact failure this project refuses.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# Kind → how a person says it, plus one glyph. A closed table: an unknown kind falls through to the
# raw string rather than being dressed up as something it is not.
_KINDS = {
    "note":       ("A note", "✎"),
    "writing":    ("Writing", "❞"),
    "recipe":     ("A recipe", "✦"),
    "build":      ("A build", "⚒"),
    "field_note": ("A field note", "⊹"),
    "question":   ("A question", "?"),
    "link":       ("A link worth keeping", "↗"),
    "suggestion": ("A suggestion", "✧"),
}

# Providers worth NAMING, because "youtube.com" tells a reader what to expect and a bare hostname
# does not. Only hosts whose nature is unambiguous — never a guess about what a page contains.
_PROVIDERS = {
    "youtube.com": "YouTube video", "youtu.be": "YouTube video",
    "vimeo.com": "Vimeo video", "rumble.com": "Rumble video",
    "archive.org": "Internet Archive", "gutenberg.org": "Project Gutenberg",
    "wikipedia.org": "Wikipedia", "wikisource.org": "Wikisource",
    "github.com": "GitHub", "arxiv.org": "arXiv preprint",
    "loc.gov": "Library of Congress", "biblehub.com": "BibleHub",
    "sacred-texts.com": "Sacred Texts", "ccel.org": "Christian Classics Ethereal Library",
    "substack.com": "Substack post", "podcasts.apple.com": "Apple Podcasts",
}

_MAX_CACHE = 4096
_cache: Dict[tuple, Dict[str, Any]] = {}


def _host_of(url: str) -> str:
    try:
        return (urlparse(str(url or "")).hostname or "").lower().lstrip("www.")
    except ValueError:
        return ""


def _provider(host: str) -> str:
    """Name the provider only when the host itself settles it. `_PROVIDERS` is matched on the
    registrable tail so `m.youtube.com` and `www.youtube.com` both land."""
    if not host:
        return ""
    for known, label in _PROVIDERS.items():
        if host == known or host.endswith("." + known):
            return label
    return ""


def when(ts: Any, now: Optional[int] = None) -> str:
    """"3 minutes ago" — with the honesty that a missing timestamp yields nothing at all, never
    "just now". Coarse on purpose: a shelf does not need seconds, and a coarse figure cannot imply
    a precision the record does not have."""
    try:
        t = int(float(ts or 0))
    except (TypeError, ValueError):
        return ""
    if t <= 0:
        return ""
    d = max(0, int(now if now is not None else time.time()) - t)
    if d < 90:
        return "just now"
    for secs, unit in ((3600, "minute"), (86400, "hour"), (86400 * 30, "day"),
                       (86400 * 365, "month")):
        if d < secs:
            n = max(1, d // (secs // 60 if unit == "minute" else
                             3600 if unit == "hour" else
                             86400 if unit == "day" else 86400 * 30))
            return f"{n} {unit}{'s' if n != 1 else ''} ago"
    n = max(1, d // (86400 * 365))
    return f"{n} year{'s' if n != 1 else ''} ago"


def _size(n: Any) -> str:
    try:
        b = int(n or 0)
    except (TypeError, ValueError):
        return ""
    if b <= 0:
        return ""
    return f"{b} bytes" if b < 1024 else (f"{b / 1024:.0f} KB" if b < 1024 * 1024
                                          else f"{b / 1048576:.1f} MB")


def _standing(card: Dict[str, Any]) -> str:
    """One phrase for where this card stands, in the reader's terms — the distinction the whole
    Commons rests on: amplified is not verified.

    Returns "" when the card names neither a stage nor a ring. The first draft fell through to
    "on this member's shelf", which is a confident sentence about a card that said nothing — the
    exact failure this layer must not commit."""
    stage = str(card.get("lifecycle_stage") or "")
    ring = str((card.get("extra") or {}).get("ring") or "")
    if stage == "public" and ring == "commons":
        return "carried on the commons — a member's own work, not the library's claim"
    if stage == "public_review":
        return "offered to the commons, waiting for a person to read it"
    if ring == "private":
        return "yours alone"
    if ring == "shelf":
        return "on this member's shelf"
    return ""


def _waybill_line(wb: Dict[str, Any], reach: str, err: str, now: Optional[int]) -> str:
    """The provenance of a link, in one readable line — or an honest sentence about our failure."""
    if reach and reach != "FETCHED":
        return ("We could not reach it when this was carded"
                + (f" ({err})" if err else "")
                + " — that is a fact about us, not about the link.")
    if not wb:
        return ""
    bits = []
    seen = when(wb.get("fetched_at"), now)
    if seen:
        bits.append(f"looked at {seen}")
    sz = _size(wb.get("bytes"))
    if sz:
        bits.append(sz)
    h = str(wb.get("sha256") or "")
    if h:
        bits.append(f"fingerprint {h[:12]}…")
    st = wb.get("status")
    if isinstance(st, int) and st >= 400:
        bits.append(f"answered {st}")
    return " · ".join(bits)


def derive(card: Dict[str, Any], now: Optional[int] = None) -> Dict[str, Any]:
    """The presentation block for one bare card. Pure, cheap, and never written back.

    Only keys the card actually supports appear. A reader (or an agent) can render entirely from
    this without re-deriving anything, and a client that ignores it loses nothing but polish.
    """
    if not isinstance(card, dict) or not card:
        return {}          # nothing in, nothing out — never a block of plausible defaults
    # Cache ONLY a card that carries both an id and a version. Keying on `updated_at` is what makes
    # a stale presentation impossible — but a MISSING `updated_at` makes every card with that id
    # share one key, and two different cards then serve each other's block. Caught by the
    # never-invented test, which got the first card's answer for the second card. No version, no
    # cache: correctness first, and a versionless card is rare enough that it costs nothing.
    cid, ver = str(card.get("id") or ""), card.get("updated_at")
    cacheable = bool(cid) and isinstance(ver, (int, float)) and now is None
    key = (cid, ver)
    if cacheable:
        hit = _cache.get(key)
        if hit is not None:
            return hit

    x = card.get("extra") or {}
    kind = str(x.get("drop_kind") or card.get("box") or "")
    label, glyph = _KINDS.get(kind, (kind.replace("_", " ") or "", "•"))
    out: Dict[str, Any] = {
        "glyph": glyph,
        "kind_label": label,
        # the label as the card gives it. No fallback: a card that names nobody must not be
        # rendered as though it named "a member of the Commons".
        "by": str((card.get("source") or {}).get("label") or ""),
        "authority": str((card.get("source") or {}).get("authority_tier") or ""),
        "posted": when(card.get("created_at"), now),
        "standing": _standing(card),
    }
    url = str(x.get("url") or (card.get("source") or {}).get("url") or "")
    if url:
        host = _host_of(url)
        out["link"] = {
            "url": url,
            "host": host,
            "provider": _provider(host),
            # what to call the thing: the page said its own name, or the member's title
            "titled": str((x.get("waybill") or {}).get("page_title") or "") or str(card.get("title") or ""),
            "waybill_line": _waybill_line(x.get("waybill") or {}, str(x.get("reach") or ""),
                                          str(x.get("reach_error") or ""), now),
            "reach": str(x.get("reach") or ""),
            # stated, not implied: we do not embed, and the reader should know why
            "embed": str(x.get("embed") or ""),
        }
    if x.get("quote"):
        out["quote"] = {"text": str(x["quote"]), "attribution": str(x.get("attribution") or "")}
    if x.get("promoted_by"):
        out["vouched"] = {"by": str(x["promoted_by"]), "reason": str(x.get("promoted_reason") or "")}

    if cacheable:
        if len(_cache) >= _MAX_CACHE:
            _cache.clear()          # a plain flush beats an eviction policy nobody will tune
        _cache[key] = out
    return out


def attach(cards, now: Optional[int] = None):
    """Attach `presentation` to each card IN THE RESPONSE ONLY — a shallow copy per card, so the
    stored record is never touched. This is the one place a read path should call."""
    out = []
    for c in cards or []:
        if isinstance(c, dict):
            out.append(dict(c, presentation=derive(c, now)))
        else:
            out.append(c)
    return out


__all__ = ["derive", "attach", "when"]
