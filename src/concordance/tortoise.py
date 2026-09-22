"""THE TORTOISE — the whole source, delivered on demand.

Matt, 2026-09-21: "We will be the card catalogue. We won't hold the texts on board. We will keep
that on the external hard drive. We can send the whole source but it will be the tortoise."

The two tiers, joined here. A card is the HARE — light, everywhere, findable: title, discipline,
language, public-domain provenance, and a pointer. The full book is the TORTOISE — it does not ride
in the card; it is fetched, slowly and on demand, from the public-domain source the card points to,
the moment a reader opens it. This module is that opening: card -> the plain text of the work.

WHAT IT IS, AND IS NOT.
  • It READS THROUGH. `sources.fetch()` anchors a body to a drive and hashes it, so a copied drive is
    verifiable forever. This holds nothing: it streams the text once, to one reader, and keeps no
    copy. The box carries the catalogue, not the library.
  • It stays behind the SAME GATE as the ark's fetch — the public-domain hosts (Internet Archive,
    Project Gutenberg, Library of Congress) and no others. You can only read what is catalogued, and
    a catalogued card can only point into that allowlist. The reader is not an open web proxy.
  • It is HONEST about a miss. A scan that is images, or access-restricted, or a PDF that will not
    render as text — each says so plainly and hands back the direct link to carry the whole source.
    A card that points nowhere fetchable is not dressed up as a book.

Conduit, not source: the text returned is the public-domain author's own words, found and passed
through, never generated and never ours.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import sources

# words too common to locate on — a passage is found by its DISTINCTIVE terms, not "the" and "with"
_LOCATE_STOP = frozenset((
    "the a an of to and but in on for is are was were be his her its their our my your this that these "
    "those with from about into over under out up down how what when where why who which can could "
    "would should will not no as at by or if it he she they we you i do does did section part chapter "
    "passage page read me us about on regarding book manual work volume treatise").split())
_LOC_SENT = re.compile(r"(?<=[.!?])\s")


def _source_url(card: Dict[str, Any]) -> str:
    src = card.get("source") or {}
    return (src.get("url") or (card.get("extra") or {}).get("tortoise") or "").strip()


def readable(card: Optional[Dict[str, Any]]) -> bool:
    """Does this card point into the public-domain allowlist? (What earns a 'Read the full work' door.)"""
    return bool(card) and sources._host_ok(_source_url(card))


def open_work(card: Dict[str, Any], *, meta=None) -> Dict[str, Any]:
    """Open the full text behind a catalogue card. Never raises for an expected miss.

    `meta` injects Archive metadata in tests so no test touches the network.
    """
    src = card.get("source") or {}
    detail_url = _source_url(card)
    extra = card.get("extra") or {}
    head = {
        "card": card.get("id"),
        "title": card.get("title"),
        "author": card.get("author"),
        "language": card.get("language") or extra.get("language"),
        # The shelf/discipline this work sits under — the reader offers it as an off-ramp back onto
        # the finding path ("more like this"), so read leads back into find, not to a dead end.
        "discipline": extra.get("discipline") or card.get("box") or card.get("shelf"),
        "detail_url": detail_url,          # the catalogue page — the whole source, to carry (the tortoise)
        "identifier": src.get("identifier"),
        "pd_basis": src.get("pd_basis"),
        "pd_year": src.get("pd_year"),
        "license": src.get("license") or "public-domain",
        "held": src.get("held"),
    }
    if not sources._host_ok(detail_url):
        return {**head, "status": "not_available",
                "reason": "this card points to no fetchable public-domain source"}

    text_url = sources.resolve_text_url(detail_url, meta)
    if not text_url:
        return {**head, "status": "not_available",
                "reason": "no plain-text edition stands behind this catalogue entry — it may be "
                          "images or maps, or the item is access-restricted. The whole source is "
                          "still yours to carry at the link below."}

    res = sources.read_through(text_url)
    st = res.get("status")
    if st == "read":
        return {**head, "status": "read", "text_url": text_url, "final_url": res.get("final_url"),
                "media_type": res.get("media_type"), "chars": res.get("chars"),
                "truncated": res.get("truncated"), "text": res.get("text")}
    if st == "binary":
        return {**head, "status": "binary", "text_url": text_url,
                "download_url": res.get("download_url"), "media_type": res.get("media_type"),
                "reason": res.get("reason")}
    return {**head, "status": "not_available", "reason": res.get("reason", "the source could not be reached")}


_HEAD_KEYS = ("card", "title", "author", "language", "discipline", "detail_url", "identifier",
              "pd_basis", "pd_year", "license", "held")


def _snap(text: str, start: int, length: int) -> str:
    """A window of the text, snapped OUT to whole-sentence bounds so a passage never begins or ends
    mid-word. Verbatim (only inter-word whitespace is collapsed for reading)."""
    end = min(len(text), start + length)
    lo = max(0, start)
    pre = text[max(0, start - 220):start]
    ms = list(re.finditer(r"[.!?]\s|\n\n", pre))
    if ms:
        lo = max(0, start - 220) + ms[-1].end()
    hi = end
    post = text[end:end + 220]
    mp = re.search(r"[.!?]\s|\n\n", post)
    if mp:
        hi = end + mp.start() + 1
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def locate_in_text(text: str, query: str, *, window_chars: int = 1500,
                   scan_chars: int = 1_800_000) -> Dict[str, Any]:
    """The passage-finder over a plain string — used both for a KEPT work (the tortoise reads it) and
    for a reader's OWN copy they dropped in (store-nothing: their text, passed through, never held).

    Returns {found, passage, offset, terms, distinct_terms, hits, note}. The passage is verbatim,
    snapped to sentence bounds. Honest when the area is not in the text.
    """
    text = (text or "")[:scan_chars]
    terms = [t for t in dict.fromkeys(re.findall(r"[a-zà-ÿ0-9]{3,}", (query or "").lower()))
             if t not in _LOCATE_STOP]
    if not text.strip():
        return {"found": False, "passage": "", "query": query, "terms": terms,
                "note": "There is no readable text to search."}
    if not terms:
        return {"found": False, "query": query, "terms": [], "offset": 0,
                "passage": _snap(text, 0, window_chars),
                "note": "No distinctive term to locate on — the opening is shown."}

    hits: List[tuple] = []
    low = text.lower()
    for t in terms:
        for m in re.finditer(r"\b" + re.escape(t) + r"\b", low):
            hits.append((m.start(), t))
    if not hits:
        return {"found": False, "query": query, "terms": terms, "offset": None, "passage": "",
                "note": "That area is not discussed here — try another wording, or another source."}
    hits.sort()
    pos = [h[0] for h in hits]

    # densest window by (distinct terms, then total hits) — two pointers over sorted positions
    from collections import defaultdict
    cnt: Dict[str, int] = defaultdict(int)
    distinct = 0
    j = 0
    best = (-1, -1)
    best_center = pos[0]
    for i in range(len(hits)):
        if j < i:
            j = i
        while j < len(hits) and pos[j] - pos[i] <= window_chars:
            if cnt[hits[j][1]] == 0:
                distinct += 1
            cnt[hits[j][1]] += 1
            j += 1
        score = (distinct, j - i)
        if score > best:
            best = score
            best_center = pos[i]
        cnt[hits[i][1]] -= 1
        if cnt[hits[i][1]] == 0:
            distinct -= 1

    start = max(0, best_center - window_chars // 3)
    return {"found": True, "query": query, "terms": terms, "offset": start,
            "distinct_terms": best[0], "hits": best[1],
            "passage": _snap(text, start, window_chars),
            "note": "Found — the passage where these terms cluster densest."}


def locate(card: Dict[str, Any], query: str, *, window_chars: int = 1500,
           scan_chars: int = 1_800_000, meta=None) -> Dict[str, Any]:
    """Find WHERE in a KEPT work a topic is discussed and return THAT passage, verbatim. Fetches the
    work (the tortoise), then locates within it. Honest when the work cannot be read or the area is
    absent."""
    op = open_work(card, meta=meta)
    head = {k: op.get(k) for k in _HEAD_KEYS}
    if op.get("status") != "read":
        return {**head, "status": op.get("status", "not_available"), "reason": op.get("reason"),
                "found": False, "passage": "", "query": query}
    return {**head, "status": "read",
            **locate_in_text(op.get("text") or "", query, window_chars=window_chars, scan_chars=scan_chars)}


__all__ = ["open_work", "readable", "locate", "locate_in_text"]
