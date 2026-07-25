"""The airlock — the input side. A user drags in a file; we mint cards + a map from it, in the
chamber, and kick the FILE back out. It never enters our core.

Matt, 2026-07-25: "Same on the other end. User drags a file. We create cards and deposit the cards.
We will work using that file while in airlock, but it never enters our core. It is kicked back out,
but we do create valuable maps and cards while it is in airlock."

So ingest() takes the file's TEXT (transient — held only for this call), chunks it into lightweight
cards that MAP BACK to the user's own file (their path/link is the waybill; they keep the file), and
builds a small MAP (the outline, the salient terms, and — if the corpus is at hand — the cards in the
keeping it connects to). It returns {cards, map}. It stores NOTHING: the file is not persisted, and
the minted cards belong to the USER (a personal deck), never merged into the shared core. Privacy and
sovereignty on the input side — carry-your-own-data + the parasitic connector (leverage, never absorb).

Sovereign: stdlib only; the optional connection-map uses the corpus if it is already loaded, else is
skipped. Conduit: cards are the user's own words, chunked and attributed to their file; generated=False.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

_HEADING = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Z0-9 \-]{6,}|\d+[.)]\s+.+)$")
_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]{2,}")
_STOP = {"the", "and", "for", "that", "this", "with", "from", "have", "not", "are", "was", "but",
         "his", "her", "him", "they", "you", "your", "our", "their", "which", "would", "there",
         "been", "were", "will", "what", "when", "who", "into", "than", "then", "them", "also"}
_MAX_CARDS = 500
_MAX_BODY = 1600


def _chunks(text: str) -> List[str]:
    """Split into sections at blank lines / headings, bounded and reasonably sized."""
    blocks, cur = [], []
    for line in (text or "").splitlines():
        if not line.strip():
            if cur:
                blocks.append("\n".join(cur)); cur = []
        elif _HEADING.match(line.strip()) and cur:
            blocks.append("\n".join(cur)); cur = [line]
        else:
            cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    # merge tiny blocks into ~paragraph-sized chunks
    out, buf = [], ""
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if len(buf) + len(b) < 700:
            buf = (buf + "\n\n" + b).strip()
        else:
            if buf:
                out.append(buf)
            buf = b
    if buf:
        out.append(buf)
    return out[:_MAX_CARDS]


def _title(block: str, source: str, i: int) -> str:
    first = block.strip().splitlines()[0].lstrip("#").strip()
    first = re.sub(r"\s+", " ", first)[:80]
    return first or f"{source or 'file'} — section {i + 1}"


def _terms(text: str, k: int = 12) -> List[str]:
    from collections import Counter
    words = [w.lower() for w in _WORD.findall(text or "") if w.lower() not in _STOP]
    return [w for w, _ in Counter(words).most_common(k)]


def ingest(text: str, source: str = "", title: str = "", link: str = "") -> Dict[str, Any]:
    """Mint cards + a map from a dragged file's text, in the airlock. Stores nothing. The cards map
    back to the user's own file (link); the file is kicked back out."""
    text = str(text or "")
    if not text.strip():
        return {"ok": False, "error": "the file is empty"}
    src = (title or source or "your file").strip()
    fp = hashlib.sha256((src + "|" + str(len(text))).encode("utf-8")).hexdigest()[:12]
    blocks = _chunks(text)
    cards: List[dict] = []
    for i, b in enumerate(blocks):
        cards.append({
            "id": f"card_user_{fp}_{i:04d}", "kind": "note", "title": _title(b, src, i)[:180],
            "body": b[:_MAX_BODY],
            "source": {"label": src, "url": link, "domain": "user", "authority_tier": "user"},
            "shelf": "dropbox", "box": "user",
            "bands": _terms(b, 8), "subject": src,
            # the card maps BACK to the user's file — the waybill; the file stays theirs
            "connections": [], "author": "user", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "private", "lifecycle_stage": "private", "volatility": "user",
            "surface": "secular", "generated": False,
            "extra": {"source": src, "link": link, "section": i, "of": len(blocks), "carried_by_user": True},
        })
    outline = [c["title"] for c in cards][:60]
    the_map: Dict[str, Any] = {
        "source": src, "link": link, "sections": len(cards),
        "outline": outline, "top_terms": _terms(text, 16), "connects_to": _connect(text),
    }
    return {"ok": True, "cards": cards, "map": the_map,
            "note": ("The file was worked in the airlock and kicked back out — we kept nothing of it. "
                     "These cards and this map are yours; they point back to your file, which stays with you.")}


def _connect(text: str, limit: int = 6) -> List[Dict[str, str]]:
    """If the corpus is already at hand, name a few cards in the keeping this file connects to.
    Never loads the corpus just for this — leaves the map's 'connects_to' empty rather than pay that cost."""
    try:
        import sys
        corpus = sys.modules.get("concordance.corpus")
        if corpus is None or not getattr(corpus, "_DEFAULT", None):
            return []
        q = " ".join(_terms(text, 10))
        hits = corpus.search(q, limit=limit) if q else []
        return [{"id": c.get("id"), "title": (c.get("title") or "")[:80], "shelf": c.get("shelf")}
                for c in hits]
    except Exception:  # noqa: BLE001 — the connection-map is a bonus, never a requirement
        return []


__all__ = ["ingest"]
