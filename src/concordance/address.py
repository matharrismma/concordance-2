"""THE ADDRESS — a derived, faceted coordinate for every card. Spec: docs/ADDRESS.md.

Matt, 2026-07-29: *"We need better tagging for recall. The Dewey decimal system for the next
age of computing."*

Dewey's genius was that a notation IS a location. His flaw was one hierarchy: a book on the
theology of music must choose a shelf and lose half of itself. So this is faceted
(Ranganathan's line, not Dewey's), and it adds what neither faced:

    P.D.K / SUBJECT / A.V @ SOURCE

    plane . domain . kind / subject / authority . verification @ source

Three disciplines make it trustworthy rather than merely tidy:

  * **DERIVED, never assigned.** Every facet is a pure function of fields the card already
    carries, so the whole set regenerates and drift becomes a failing test rather than an
    argument between cataloguers.
  * **UNPLACED is honest.** A card whose facets cannot be determined is addressed `UNPLACED`
    and REPORTED. It is never guessed into a bucket to make a number look better.
  * **Provenance and verification are part of the location.** A CONFIRMED physics result and
    an unverified web claim about physics do not belong at the same address.

The address is a coordinate, not a container: `member_of` remains the load-bearing tree (zero
orphans), and this never moves a card out of it.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

# ── the closed vocabularies ──────────────────────────────────────────────────────────────────
PLANES = ("WIT", "SCI", "PRA", "HUM", "OPS")
KINDS = ("FCT", "CHK", "EXP", "IDX", "MON", "TXT", "MBR", "OBJ", "REL")
AUTHORITIES = ("SCR", "REF", "MBR", "WEB")
VERIFICATIONS = ("CONFIRMED", "WITNESSED", "UNCHECKED", "COULD-NOT-CHECK", "BROKEN", "MIXED")
UNPLACED = "UNPLACED"

# Which plane a shelf belongs to. Anything unlisted resolves by heuristic below, and if that
# fails the card is UNPLACED and reported — never defaulted into a plane.
_WITNESS_SHELVES = {
    "scripture", "hebrew_ot", "greek_nt", "lexicon", "commentary", "sermons", "encyclopedia",
    "topical", "codex", "spine", "canon", "churches", "religions", "creeds", "theology",
    "prophecy", "characters", "study", "harmony", "timeline", "backmatter", "voices",
}
_PRACTICAL_SHELVES = {
    "survival", "apothecary", "almanac", "access", "recipes", "cookery", "activities", "foods",
    "drugs", "medicine", "nutrition", "curriculum", "fieldkit", "playbook", "steward",
    "agriculture", "soil_science", "construction", "manufacturing", "real_estate", "labor",
    "energy", "exercise_science", "sports_analytics", "document_validation", "timekeeping",
}
_HUMANITIES_SHELVES = {
    "gutenberg", "classics", "history", "history_chronology", "philosophy", "rhetoric",
    "linguistics", "languages", "law", "economics", "music_theory", "photography",
    "architecture", "contributors", "narratives", "archetypes", "pronunciation",
}
_OPS_SHELVES = {"works", "seals", "systems", "connections", "growth", "sources", "web_cache"}

_SLUG = re.compile(r"[^a-z0-9]+")


def _slug(s: Any, limit: int = 48) -> str:
    return _SLUG.sub("-", str(s or "").lower()).strip("-")[:limit]


# v1 measured 44.9% UNPLACED, 204,136 of them on the plane alone, because these tables were
# hand-written and missed the LARGEST shelves in the keeping (dictionary 149,490 · geography
# 69,135 · taxonomy 37,933). Hand-maintained vocabularies rot; derived ones cannot. So the
# tables below are now OVERRIDES ONLY, and the general case comes from machinery that already
# classifies every shelf: corpus_db.SHARD_ASSIGN (the shard tiers) crossed with the verifier
# registry. A shelf neither names nor implies remains UNPLACED and is reported.
_SHARD_PLANE = {"word": "WIT", "science": "SCI", "world": "SCI",
                "dictionary": "HUM", "books": "HUM", "core": None}


def plane_of(card: Dict[str, Any]) -> Optional[str]:
    """WIT / SCI / PRA / HUM / OPS — or None (never a default)."""
    shelf = (card.get("shelf") or "").strip().lower()
    if not shelf:
        return None
    # 1. explicit overrides, where our own doctrine differs from the shard tiering
    if shelf in _WITNESS_SHELVES:
        if shelf == "spine" and (card.get("surface") or "") != "witness":
            return "OPS"
        return "WIT"
    if shelf in _PRACTICAL_SHELVES:
        return "PRA"
    if shelf in _HUMANITIES_SHELVES:
        return "HUM"
    if shelf in _OPS_SHELVES:
        return "OPS"
    # 2. a shelf that names a verifier domain is science by construction
    try:
        from . import verifiers
        if shelf in verifiers.VERIFIERS:
            return "SCI"
    except Exception:  # noqa: BLE001 — verifiers unavailable is not a reason to guess
        pass
    # 3. DERIVED: the shard the builder assigns this shelf to already encodes its character
    try:
        from . import corpus_db
        tier = corpus_db.SHARD_ASSIGN.get(shelf)
        if tier and _SHARD_PLANE.get(tier):
            return _SHARD_PLANE[tier]
    except Exception:  # noqa: BLE001
        pass
    # 4. last resort: the surface a card is served on
    if (card.get("surface") or "") == "witness":
        return "WIT"
    if (card.get("surface") or "") == "secular":
        return "SCI"
    return None


def kind_of(card: Dict[str, Any]) -> Optional[str]:
    """The card's kind, read from what it IS — box and id prefix are the honest signals."""
    cid = str(card.get("id") or "")
    box = (card.get("box") or "").strip().lower()
    # A minted edge is a RELATION, not a subject — 17,182 of them were UNPLACED in v2 because
    # the vocabulary had no word for what they are. Adding the word is honest; forcing them into
    # FCT would not be.
    if (card.get("shelf") or "").lower() == "connections" or cid.startswith("card_edge_"):
        return "REL"
    if cid.startswith("card_domchk_"):
        return "CHK"
    if cid.startswith(("card_comm_",)):
        return "EXP"
    if cid.startswith(("card_topic_",)) or box == "index":
        return "IDX"
    if cid.startswith(("card_name_",)):
        return "FCT"
    if cid.startswith(("card_herb_",)) or box == "monograph":
        return "MON"
    if cid.startswith(("card_alm_", "card_lesson_", "card_enc_", "card_isbe_", "card_dict_")):
        return "FCT"
    # `card_src_` covers a third of the keeping, and calling all of it TXT made one facet value
    # 84% of the library — a facet that does not discriminate is not a facet. So it splits by
    # what the entry IS: a dictionary headword or a species record is a FACT; a book or a verse
    # is primary TEXT.
    if cid.startswith("card_src_"):
        shelf = (card.get("shelf") or "").lower()
        if shelf in {"gutenberg", "classics", "scripture", "hebrew_ot", "greek_nt", "history"}:
            return "TXT"
        return "FCT"
    if (card.get("kind") or "") == "verse":
        return "TXT"
    if (card.get("author") or "") == "member" or (card.get("authority_tier") or "") == "member":
        return "MBR"
    if box == "spine" or (card.get("shelf") or "") == "spine":
        return "OBJ"
    k = (card.get("kind") or "").strip().lower()
    return {"reference": "FCT", "note": "EXP", "verse": "TXT"}.get(k)


def authority_of(card: Dict[str, Any]) -> Optional[str]:
    """SCR / REF / MBR / WEB. A card with no declared tier but a NAMED SOURCE is reference
    authority — that is what a waybill means. Only a card with neither is UNPLACED."""
    tier = ((card.get("source") or {}).get("authority_tier")
            or card.get("authority_tier") or "").strip().lower()
    mapped = {"scripture": "SCR", "creed": "SCR", "reference": "REF", "matt": "REF",
              "member": "MBR", "web": "WEB", "web_unverified": "WEB"}.get(tier)
    if mapped:
        return mapped
    if (card.get("author") or "") == "member":
        return "MBR"
    src = card.get("source") or {}
    if str(src.get("label") or "").strip():
        return "REF"
    if str(src.get("url") or "").strip():
        return "WEB"        # a URL with no label is exactly what web_unverified means
    return None


def verification_of(card: Dict[str, Any]) -> str:
    """The three-state honesty, made addressable. Never invents a stronger word than the card
    has earned: a card carrying no verdict is UNCHECKED, not WITNESSED."""
    extra = card.get("extra") or {}
    body = card.get("body") or ""
    if extra.get("seal_hash") or extra.get("cite_url") or "RE-CHECKABLE SEAL" in body:
        return "CONFIRMED"
    if "CONFIRMED" in body and "MISMATCH" in body:
        return "MIXED"          # a worked check that shows both the truth and the refusal
    if "CONFIRMED" in body:
        return "CONFIRMED"
    if "MISMATCH" in body or "BROKEN" in body:
        return "BROKEN"
    if "could not check" in body.lower():
        return "COULD-NOT-CHECK"
    tier = authority_of(card)
    if tier in ("SCR", "REF"):
        return "WITNESSED"      # attributed to a named source, not machine-checked
    return "UNCHECKED"


def source_of(card: Dict[str, Any]) -> str:
    extra = card.get("extra") or {}
    for key in ("commentary_source", "sword_module", "easton_id", "isbe_headword"):
        if extra.get(key):
            return _slug(extra[key] if key in ("commentary_source", "sword_module") else key, 24)
    label = ((card.get("source") or {}).get("label") or "").strip()
    if label:
        # the first meaningful clause of the waybill, e.g. "Nave's Topical Bible (…" -> nave-s
        return _slug(label.split("(")[0].split("—")[0], 24) or "unnamed"
    return "unnamed"


def derive(card: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """(address, reason_unplaced). A pure function — same card, same address, always."""
    if not isinstance(card, dict) or not card.get("id"):
        return UNPLACED, "not a card"
    p, k, a = plane_of(card), kind_of(card), authority_of(card)
    missing = [n for n, v in (("plane", p), ("kind", k), ("authority", a)) if not v]
    if missing:
        return UNPLACED, "cannot determine " + ", ".join(missing)
    domain = _slug(card.get("shelf"), 24) or "unfiled"
    # v1 reported 20,200 cards with "no subject". They were not nameless — their titles are in
    # HEBREW AND GREEK, and an ASCII slug of Hebrew is the empty string. The fix is not to skip
    # them (that would drop the plumb-line's own verse cards); it is to fall back to the source
    # ref, then the id, so a non-Latin card is addressable by the coordinate it already carries.
    subject = (_slug(card.get("subject")) or _slug(card.get("title"))
               or _slug((card.get("source") or {}).get("ref"))
               or _slug(str(card.get("id")).replace("card_", "", 1)))
    if not subject:
        return UNPLACED, "no subject, ref, or usable id"
    v = verification_of(card)
    return f"{p}.{domain}.{k}/{subject}/{a}.{v}@{source_of(card)}", None


_ADDR = re.compile(
    r"\A(?P<plane>[A-Z]{3})\.(?P<domain>[a-z0-9_-]+)\.(?P<kind>[A-Z]{3})"
    r"/(?P<subject>[a-z0-9-]+)/(?P<authority>[A-Z]{3})\.(?P<verification>[A-Z-]+)"
    r"@(?P<source>[a-z0-9-]+)\Z")


def parse(address: str) -> Optional[Dict[str, str]]:
    """The facets back out of an address, or None. A parser is what makes a notation a system
    rather than a string: every prefix of a parseable address is a valid query."""
    m = _ADDR.match((address or "").strip())
    return m.groupdict() if m else None


def matches(address: str, pattern: str) -> bool:
    """Prefix/wildcard query: `SCI.optics.CHK/` or `WIT.*.IDX/` or `*.*.*/mercy/`.
    `*` matches one facet segment; a trailing `/` or `.` means "everything below here"."""
    a, p = (address or "").strip(), (pattern or "").strip()
    if not a or not p:
        return False
    if "*" not in p:
        return a.startswith(p)
    rx = re.escape(p).replace(r"\*", "[^./@]*").replace(r"\/", "/")
    return re.match(rx, a) is not None


__all__ = ["derive", "parse", "matches", "plane_of", "kind_of", "authority_of",
           "verification_of", "source_of", "PLANES", "KINDS", "AUTHORITIES",
           "VERIFICATIONS", "UNPLACED"]
