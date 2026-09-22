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

from typing import Any, Dict, Optional

from . import sources


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


__all__ = ["open_work", "readable"]
