"""Serve — a member's wants become the hive's work, and what is found comes back to them.

The goal Matt named is community, serving, developing disciples. This is the serving bridge: the front
of the shepherd loop. A member states a need in their profile (`wants`); this OPENS a real want in the
communal hive (`wants.open_want`) so the library's own misses drive its growth (the tortoise goes and
fetches the gap, cards it, and the keeping grows). Then, when the keeping holds an answer, it RETURNS to
the member — their want, met.

Two honest halves:
  take(wants)    — the need enters the queue. Deduped by the hive (many wanting one thing = one want),
                   so re-stating a want never spams it.
  returns(wants) — what has come back: for each want, the kept cards whose TITLE genuinely names the
                   subject (the same relevance floor discern uses — a gap stays a gap, never a
                   word-collision dressed up as an answer).

Nothing here is generated — a want is the member's own words; a return is a card that was found and
cited. Injectable search/relevance so the seed stays pure; defaults to the real keeping.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_MIN_WANT = 3

# Words that do not name a subject — question and action words. A genuine answer must share a real NOUN
# with the want, not just an action verb or a short ambiguous stem ("tan" colliding with a place "Tan-Tan").
_GENERIC = {"how", "to", "of", "and", "or", "the", "a", "an", "do", "i", "my", "me", "for", "with", "from",
            "on", "in", "at", "make", "making", "made", "build", "building", "start", "starting", "get",
            "getting", "keep", "keeping", "find", "finding", "use", "using", "need", "want", "some", "any",
            "your", "you", "without", "that", "this", "best", "way", "good"}


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w


def _subjects(text: str, minlen: int) -> set:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(w) >= minlen and w not in _GENERIC}


def _genuine(want: str, card: Dict[str, Any]) -> bool:
    """A card genuinely answers a want only when its TITLE shares the want's HEAD noun (the object the
    want is about — the last substantive noun) OR at least TWO of its subject nouns. One weak overlap is
    not an answer: 'tan a deer hide' (head 'hide') is not met by a place 'Tan-Tan' (shares only 'tan')
    nor by 'The deer family' (shares only 'deer', and not the head). A gap stays a gap."""
    toks = [w for w in re.findall(r"[a-z0-9]+", (want or "").lower()) if w not in _GENERIC]
    subj = [_stem(w) for w in toks if len(w) >= 4] or [_stem(w) for w in toks if len(w) >= 3]
    if not subj:
        return False
    title = {_stem(w) for w in re.findall(r"[a-z0-9]+", (card.get("title") or "").lower())}
    return (subj[-1] in title) or (len(set(subj) & title) >= 2)


def take(wants: List[str], *, plane: str = "human") -> Dict[str, Any]:
    """Open a hive want for each stated need — the member's wants become the library's work. Returns the
    opened want ids (deduped by the hive)."""
    from . import wants as _wants
    opened: List[str] = []
    for w in wants or []:
        q = str(w or "").strip()
        if len(q) < _MIN_WANT:
            continue
        r = _wants.open_want(query=q, kind="missing", plane=plane)
        wid = r.get("want_id") or r.get("id")
        if r.get("ok") and wid:
            opened.append(wid)
    return {"ok": True, "opened": opened, "count": len(opened)}


def returns(wants: List[str], *, search_fn=None, relevant_fn=None, limit_each: int = 2) -> Dict[str, Any]:
    """What has come back for a member: for each want, the kept cards that genuinely answer it (title
    names the subject). `met` counts the wants now answered; the rest are still sought (honest)."""
    if search_fn is None:
        from . import corpus
        search_fn = corpus.search
    if relevant_fn is None:
        relevant_fn = _genuine   # substantive-noun match — a short-stem collision is not an answer
    served: List[Dict[str, Any]] = []
    for w in wants or []:
        q = str(w or "").strip()
        if not q:
            continue
        try:
            hits = search_fn(q, 4) or []
        except Exception:  # noqa: BLE001 — a missing/partial keeping is a gap, never a crash
            hits = []
        cards = []
        for c in hits:
            try:
                if relevant_fn(q, c):
                    cards.append({"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf")})
            except Exception:  # noqa: BLE001
                continue
            if len(cards) >= max(1, int(limit_each)):
                break
        served.append({"want": q, "cards": cards, "met": bool(cards)})
    return {"served": served, "met": sum(1 for s in served if s["met"]), "of": len(served)}


__all__ = ["take", "returns"]
