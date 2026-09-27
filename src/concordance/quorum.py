"""QUORUM — "a matter is established by two or three witnesses" (Deuteronomy 19:15), which is also the
honeybee's rule: the swarm commits only when enough INDEPENDENT scouts converge on one site (Seeley).

This counts the DISTINCT INDEPENDENT witnesses (sources) that corroborate an answer's subject and reports
whether the answer is ESTABLISHED (>= a quorum) or rests on a single testimony (tentative). It is a
CONFIDENCE signal for honesty — it never changes WHICH answer leads (that is the ranker's work), only how
firmly the answer is held. Two cards from one source are one witness, however many they wrote.

GATED OFF by default (CONCORDANCE_QUORUM): `assess` returns None, so the response is unchanged until a
node opts in. Held for review. The lever, once on, keeps the engine honest: it will SAY "one witness"
rather than dress a single source as settled.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Set

_THRESHOLD = 2                      # two or three witnesses
_WORD = re.compile(r"[a-z0-9]+")


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_QUORUM", "").strip().lower() in ("1", "true", "yes", "on")


def _source_key(card: Dict[str, Any]) -> str:
    """A source's IDENTITY, so two cards from the same source count as ONE witness. The source label
    normalized; falls back to the URL host / author / id when a card names no source."""
    src = card.get("source") or {}
    label = " ".join(str(src.get("label") or "").lower().split())
    if label:
        return label
    url = str(src.get("url") or "").lower()
    if url:
        return url.split("/")[2] if "://" in url else url        # the host, not the exact page
    return str(card.get("author") or "") or str(card.get("id") or "")


def _subject_toks(card: Dict[str, Any]) -> Set[str]:
    text = str(card.get("subject") or card.get("title") or "")
    return {w for w in _WORD.findall(text.lower()) if len(w) > 2}


def witnesses(hits: List[Dict[str, Any]], lead: Optional[Dict[str, Any]] = None) -> Set[str]:
    """The DISTINCT independent sources among the hits that corroborate the LEAD's subject."""
    if not hits:
        return set()
    lead = lead or hits[0]
    subj = _subject_toks(lead)
    out: Set[str] = set()
    for h in hits:
        if not subj or (_subject_toks(h) & subj):        # only witnesses to the SAME subject
            out.add(_source_key(h))
    return out


def assess(hits: List[Dict[str, Any]], threshold: int = _THRESHOLD) -> Optional[Dict[str, Any]]:
    """The witness count + verdict for the lead. None when gated off or given nothing."""
    if not enabled() or not hits:
        return None
    w = witnesses(hits)
    n = len(w)
    return {
        "witnesses": n, "quorum": threshold, "established": n >= threshold,
        "means": (f"established by {n} independent witnesses (Deuteronomy 19:15 — two or three)"
                  if n >= threshold else
                  "a single witness — hold this as one testimony, not settled; seek corroboration"),
    }
