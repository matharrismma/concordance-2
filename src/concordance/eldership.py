"""ELDERSHIP — the orca matriarch's weight on the cloud of witnesses. A killer-whale pod is led by its
oldest female: post-reproductive, she carries decades of ecological memory and leads the hunt in lean years
when the young cannot (Brent et al., Current Biology 2015); the pod's dialect is learned and inherited down
her matriline (Ford; Riesch — measured "vocal clans"). The elder is not louder — she has simply endured, and
the memory she carries has been tested by more seasons than anyone else's.

Our cloud of witnesses has elders too: a source that has ENDURED — carried its testimony across generations
into the public domain, or stands in the canon — is a matriarch of the corpus. This does not change WHICH
answer leads (the ranker's work) or how many witnesses there are (quorum's work). It reports whether the
witnesses include elders: "two witnesses, both enduring sources" is held more firmly than two that surfaced
last week. Honest confidence, weighted by standing — "the fear of the Lord is the beginning of wisdom," and
wisdom keeps company with age (Job 12:12).

GATED OFF by default (CONCORDANCE_ELDERSHIP): `assess` returns None, so the response is unchanged until a
node opts in. Held for review. Consistent with quorum: it groups the same witnesses (distinct sources on the
lead's subject) and asks, of those, how many are elders.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from . import quorum

# A four-digit year old enough that a work is enduring — carried into the public domain (published ~95+
# years ago, the US PD horizon) or older. The matriarch has stood at least this long.
_ENDURED_BEFORE = 1931
_YEAR = re.compile(r"\b(1[5-9]\d\d|20[01]\d)\b")
_PD_MARK = re.compile(r"\b(public domain|public-domain|\bpd\b|cc0)\b", re.I)
# The canon and the standing reference works that carry the memory of the tradition.
_CANON = ("bible", "scripture", "kjv", "asv", "web ", "webster 1913", "strong", "septuagint",
          "vulgate", "koine", "masoretic")


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_ELDERSHIP", "").strip().lower() in ("1", "true", "yes", "on")


def _source_text(card: Dict[str, Any]) -> str:
    src = card.get("source") or {}
    parts = [str(src.get("label") or ""), str(src.get("license") or ""),
             str(src.get("url") or ""), str(src.get("year") or src.get("date") or ""),
             str(card.get("year") or "")]
    return " ".join(parts).lower()


def standing(card: Dict[str, Any]) -> Dict[str, Any]:
    """An elder has ENDURED. Canon or a standing reference is a matriarch of the tradition (highest);
    a source carried into the public domain by age is an elder that has outlived its own century."""
    text = _source_text(card)
    if any(name in text for name in _CANON):
        return {"elder": True, "standing": 1.0, "why": "canon / standing reference — a matriarch of the tradition"}
    years = [int(y) for y in _YEAR.findall(text)]
    if _PD_MARK.search(text) or (years and min(years) < _ENDURED_BEFORE):
        return {"elder": True, "standing": 0.8,
                "why": "an enduring source — carried across generations into the public domain"}
    return {"elder": False, "standing": 0.0, "why": "recent testimony — not yet an elder"}


def assess(hits: List[Dict[str, Any]], lead: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Of the witnesses corroborating the lead's subject, how many are elders. None when gated off.

    Groups witnesses exactly as quorum does (distinct sources on the same subject), so a source counts
    once however many cards it wrote; a source is an elder if ANY of its cards here has elder standing."""
    if not enabled() or not hits:
        return None
    lead = lead or hits[0]
    subj = quorum._subject_toks(lead)
    by_source: Dict[str, bool] = {}
    for h in hits:
        if subj and not (quorum._subject_toks(h) & subj):
            continue                                   # only witnesses to the SAME subject
        key = quorum._source_key(h)
        if by_source.get(key):
            continue                                   # already an elder on this source
        by_source[key] = standing(h)["elder"]
    total = len(by_source)
    elders = sum(1 for v in by_source.values() if v)
    return {
        "elders": elders, "witnesses": total,
        "means": (f"{elders} of {total} witnesses are enduring sources — the elders concur; hold this the "
                  "more firmly (a matriarch's memory, tested by more seasons)"
                  if elders else
                  "no enduring witness yet — this rests on recent testimony; weigh it as such"),
    }
