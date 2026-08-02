"""COMPARE — two subjects side by side, every cell attributed. Composition is not generation.

Matt, 2026-08-01, after asking the library to compare and contrast Nazarene vs Wesleyan:
*"Nothing worth reading. We don't want to set our rules so tight we can provide no value."*

He was right, and the failure was not the ranking — it was that the question was never READ AS A
COMPARISON. Two subjects went into one bag of words, six Wesleyan cards came out, and the missing
half was never mentioned. `message: None`. The library answered half a question as though it were
the whole one.

THE LINE THIS MODULE HOLDS. The doctrine forbids GENERATING substance and letting authored text
pass as found. It does not forbid ARRANGING what we hold. Two voice cards laid side by side on
shared axes — confession, centre, founded, distinctive — each cell carrying its own card and
citation, is the concordance doing its work. A table whose every entry is attributable is MORE
honest than prose, not less. Confusing "do not author" with "do not assemble" is what left this a
pile of cards instead of an answer.

So: nothing here writes a sentence of substance. It selects, aligns, and names what is absent.

HAVING THE WORD IS NOT HAVING THE THING, and this is the trap the Nazarene question exposed.
Searching "Nazarene" returns five cards — every one about Jesus of Nazareth, the biblical epithet.
A naive `count > 0` would report the subject held and cheerfully compare a denomination against a
figure of speech. The `churches` shelf is the registry of traditions we actually cover (28 voices,
one per tradition, each chosen by that tradition's own reckoning), so THAT is the test for whether
a tradition is held — not whether its name appears somewhere in the corpus.

When a side is missing we say so plainly, show what we DO hold and what it actually is, and offer
to go and get the rest. That is the want loop doing the job it exists for.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# The shelf that holds one orienting voice per tradition — the registry of what we cover.
VOICE_SHELF = "churches"

# "compare and contrast X vs Y" · "X versus Y" · "difference between X and Y" · "contrast X with Y"
# Deterministic: reading the SHAPE of a question is a parse, not a judgement, and needs no model.
_PATTERNS = (
    re.compile(r"\b(?:compare\s+and\s+contrast|compare|contrast)\s+(.+?)\s+(?:vs\.?|versus|and|with|to)\s+(.+)$", re.I),
    re.compile(r"\b(?:difference|differences)\s+between\s+(.+?)\s+and\s+(.+)$", re.I),
    re.compile(r"^(.+?)\s+(?:vs\.?|versus)\s+(.+)$", re.I),
)

_TRAILING = re.compile(r"[\s?.!,;:]+$")
_LEADING = re.compile(r"^\s*(?:the|a|an)\s+", re.I)


def subjects_of(query: str) -> Optional[List[str]]:
    """The two things being compared, or None when this is not a comparison."""
    q = _TRAILING.sub("", str(query or "").strip())
    if not q:
        return None
    for pat in _PATTERNS:
        m = pat.search(q)
        if not m:
            continue
        a = _LEADING.sub("", _TRAILING.sub("", m.group(1).strip()))
        b = _LEADING.sub("", _TRAILING.sub("", m.group(2).strip()))
        if a and b and a.lower() != b.lower():
            return [a, b]
    return None


def _voice_card(subject: str, cards: List[dict]) -> Optional[dict]:
    """The orienting card for a tradition — the one written to say what it IS."""
    want = {w for w in re.findall(r"[a-z]{3,}", subject.lower())}
    for c in cards:
        if c.get("shelf") != VOICE_SHELF:
            continue
        hay = f"{c.get('title', '')} {c.get('body', '')}".lower()
        if any(w in hay for w in want):
            return c
    return None


def _side(subject: str, search) -> Dict[str, Any]:
    """One column: what we hold about this subject, and honestly what KIND of holding it is."""
    cards = search(subject, limit=8) or []
    voice = _voice_card(subject, cards)
    return {
        "subject": subject,
        # THE DISTINCTION THAT MATTERS. `held_as_tradition` is the real question for a
        # denominational comparison; `mentions` is merely whether the word occurs.
        "held_as_tradition": voice is not None,
        "mentions": len(cards),
        "voice": voice,
        "cards": cards[:5],
        "shelves": sorted({str(c.get("shelf")) for c in cards}) if cards else [],
    }


def compare(query: str, search=None) -> Optional[Dict[str, Any]]:
    """A comparison, or None when the question is not one.

    `search` is injected so this stays testable and so the caller decides which corpus/surface
    it reads — this module never reaches for a store of its own.
    """
    subjects = subjects_of(query)
    if not subjects:
        return None
    if search is None:
        from . import corpus
        search = corpus.search

    sides = [_side(s, search) for s in subjects]
    missing = [s["subject"] for s in sides if not s["held_as_tradition"]]

    # SHARED GROUND, only where both sides actually stand on it. Never asserted — read off the
    # cards' own connection edges, so the common root is evidence rather than a claim.
    shared: List[str] = []
    if not missing:
        edges = []
        for s in sides:
            v = s["voice"] or {}
            edges.append({str(e.get("to_card_id")) for e in (v.get("connections") or [])})
        if len(edges) == 2:
            shared = sorted(edges[0] & edges[1])

    if missing:
        have = "; ".join(
            f"{s['subject']}: {s['mentions']} card(s) on the {', '.join(s['shelves'])} shelf"
            for s in sides if s["mentions"] and not s["held_as_tradition"])
        message = (
            f"I cannot compare these honestly: the keeping has no tradition card for "
            f"{' and '.join(missing)}. "
            + (f"What it does hold under that name is something else — {have}. " if have else "")
            + "I will not set two things side by side when one of them is not here.")
    else:
        message = ("Both traditions are held. Each column is the tradition's own voice card, in "
                   "its own reckoning, and every line below is a card you can open.")

    return {
        "kind": "comparison",
        "subjects": subjects,
        "sides": sides,
        "missing": missing,
        "shared_ground": shared,
        "message": message,
        # The offer, not an auto-log: a person asks, a person chooses. Same rule as the want desk.
        "want": ({"offer": f"open a want for {' and '.join(missing)}", "queries": missing}
                 if missing else None),
    }


__all__ = ["compare", "subjects_of", "VOICE_SHELF"]
