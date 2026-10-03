"""ALIGNMENT — gate the keeping by agreement. Matt, 2026-09-28: "section off occult for only call on
explicit. We can gate the keeping by not integrating our areas we don't hold in agreement. Much of the
philosophy and other religions should be able to be referenced, but it should not be fully integrated as
the more aligned material."

Three tiers, read from the discernment atlas (the `under_the_test` / foreshadow charts carry `discerns_terms`
and an `alignment` label), so the classification lives with the discernment, not in a second list:

  ALIGNED   — Scripture, the fathers, science, math, the reference section, and everything else: fully
              integrated, surfaced normally. The discernment CHARTS themselves are aligned — they are the
              discernment and are NEVER gated.
  REFERENCE — other religions and philosophy (the worldviews we do not hold in agreement, credited where
              they foreshadow): referenceable, but not integrated AS the aligned material — a bounded
              down-weight when the subject is not what was sought, and normal weight when it IS sought.
  SECTIONED — the occult (astral projection, séance, the Gateway process, Theosophy/spiritualism): its
              primary sources are EXPLICIT-ONLY — withheld from a result set unless the query itself names
              the subject. Never deleted; still reachable, but only on a deliberate call, always beside the
              chart that tests it (1 John 4:1-3). The front door must discern.

A card's tier is read from its own subject/title/bands matching an atlas chart's terms — the same
distinctive phrases the discernment pairing uses (never generic words). Gated OFF by default
(CONCORDANCE_ALIGNMENT): `verdict` returns (keep=True, damp=1.0) for everything, so ranking and visibility
are byte-for-byte unchanged until a node opts in. Held for review.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_REF_DAMP = 0.6                 # a reference-tier card ranks lower when its subject is not what was sought
_DISCERNMENT_SHELVES = frozenset({"foreshadows", "signposts"})   # the charts and the signposts: never gated
_CACHE: Dict[str, Any] = {"key": None, "terms": [], "chart_tier": {}}


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_ALIGNMENT", "").strip().lower() in ("1", "true", "yes", "on")


def _atlas_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "religions_cards.jsonl"


def _index() -> Tuple[List[Tuple[str, str, str]], Dict[str, str]]:
    """(terms, chart_tier) from the atlas, cached by file signature. `terms` is [(phrase, tier, chart_id)];
    `chart_tier` maps each chart's own id to its tier (so a chart is recognised and never gated)."""
    p = _atlas_path()
    try:
        st = p.stat()
        key = (str(p), st.st_mtime, st.st_size)
    except OSError:
        key = (str(p), None, None)
    if _CACHE["key"] == key:
        return _CACHE["terms"], _CACHE["chart_tier"]
    terms: List[Tuple[str, str, str]] = []
    chart_tier: Dict[str, str] = {}
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            ex = c.get("extra") or {}
            tier = ex.get("alignment")
            dterms = ex.get("discerns_terms") or []
            if tier in ("sectioned", "reference") and dterms:
                cid = str(c.get("id") or "")
                chart_tier[cid] = tier
                for t in dterms:
                    t = str(t).lower().strip()
                    if t:
                        terms.append((t, tier, cid))
    except OSError:
        pass                                       # no atlas on disk → empty index → everything aligned
    _CACHE.update({"key": key, "terms": terms, "chart_tier": chart_tier})
    return terms, chart_tier


def context(query_text: str) -> Set[str]:
    """The chart ids the QUERY explicitly names — a deliberate call for that subject. Empty when the
    gate is off, so the caller does no work."""
    if not enabled():
        return set()
    terms, _ = _index()
    q = " " + str(query_text or "").lower() + " "
    return {cid for phrase, _tier, cid in terms if phrase in q}


def _tier_of(card: Dict[str, Any], terms: List[Tuple[str, str, str]],
             chart_tier: Dict[str, str]) -> Tuple[str, Optional[str]]:
    if str(card.get("id") or "") in chart_tier:
        return "aligned", None                     # a discernment chart is the discernment — never gated
    if card.get("shelf") in _DISCERNMENT_SHELVES:
        # The whole foreshadows shelf and the signposts ARE the discernment — each names the hole and
        # the One who filled it — yet a signpost whose title says "Tao" was tiered `reference` (×0.6)
        # by the very chart that discerns Taoism, and fell out of the first screen for "the way logos
        # derek" (measured live 2026-10-02). The discernment is never gated, by shelf, not only by id.
        return "aligned", None
    hay = (str(card.get("title") or "") + " " + " ".join(str(b) for b in (card.get("bands") or []))
           + " " + str(card.get("subject") or "")).lower()
    found_ref: Optional[Tuple[str, Optional[str]]] = None
    for phrase, tier, cid in terms:
        if phrase in hay:
            if tier == "sectioned":
                return "sectioned", cid            # the stricter wall wins immediately
            if found_ref is None:
                found_ref = (tier, cid)
    if found_ref is not None:
        return found_ref
    return "aligned", None


def verdict(card: Dict[str, Any], ctx: Set[str]) -> Tuple[bool, float]:
    """(keep, damp) for a card given the query's explicit-subject set. keep=False withholds it entirely;
    damp multiplies its score. (True, 1.0) for everything when the gate is off — byte-for-byte unchanged."""
    if not enabled():
        return True, 1.0
    terms, chart_tier = _index()
    tier, cid = _tier_of(card, terms, chart_tier)
    if tier == "sectioned":
        return (cid in ctx), 1.0                   # occult: explicit-only — kept only if the query named it
    if tier == "reference":
        return True, (1.0 if cid in ctx else _REF_DAMP)   # referenceable, down-weighted when not sought
    return True, 1.0
