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
figure of speech. The `churches` shelf is the registry of what we actually cover, so THAT is the
test for whether a tradition is held — not whether its name appears somewhere in the corpus.

MEASURED 2026-08-01, because the first version of this docstring asserted "28 voices, one per
tradition" and that was never true: the shelf holds 28 cards, which are **13 traditions**, one
ecumenical-creeds card naming the shared ground, and **14 individual voices** (Wesley, Calvin,
Luther, Aquinas, Spurgeon, Chrysostom…). A tradition card and a person card are different objects
and `_voice_card` will match either, which is correct for orienting a reader and would be wrong
for counting coverage. Anyone reporting "we cover N traditions" must count `box == "tradition"`
and subtract the creeds card — not measure the shelf.

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
    """The orienting card for a tradition — the one written to say what it IS.

    PLURALS COUNT (2026-08-02): "methodists" failed to match the "Methodist / Wesleyan" voice —
    live, on a shelf that plainly holds the tradition — because matching demanded the exact
    surface form. Each wanted word also tries its bare singular/plural, nothing more: this is
    tolerance for how people actually ask, not a stemmer.
    """
    want = set()
    for w in re.findall(r"[a-z]{3,}", subject.lower()):
        want.add(w)
        if w.endswith("es") and len(w) > 4:
            want.add(w[:-2])
        if w.endswith("s") and len(w) > 3:
            want.add(w[:-1])
        want.add(w + "s")
    # A TRADITION OUTRANKS A PERSON for the orienting seat. The registry holds both kinds — the
    # "Baptist" tradition card and "Charles Spurgeon — Baptist" — and taking the first match
    # presented Spurgeon as "southern baptists in its own reckoning" (live, 2026-08-02). A
    # person is a voice OF a tradition, not the tradition's own reckoning; the person still
    # orients when no tradition card matches at all.
    person = None
    for c in cards:
        if c.get("shelf") != VOICE_SHELF:
            continue
        hay = f"{c.get('title', '')} {c.get('body', '')}".lower()
        if any(w in hay for w in want):
            if c.get("box") == "tradition":
                return c
            person = person or c
    return person


def _side(subject: str, search, get=None) -> Dict[str, Any]:
    """One column: what we hold about this subject, and honestly what KIND of holding it is."""
    cards = search(subject, limit=8) or []
    voice = _voice_card(subject, cards)
    # ASK THE SHELF DIRECTLY. Fishing the voice out of the general top-8 made the voice a
    # popularity contest: "methodists" ranked five Tyerman volumes and two dictionary entries
    # above the Methodist / Wesleyan voice card, so the tradition read as undocumented while its
    # own registry card sat on the shelf (live, 2026-08-02). The registry is 29 cards; scoping
    # the lookup to it is cheap and makes "is this tradition held?" a question about the
    # REGISTRY, which is what it always was.
    if voice is None:
        try:
            shelf_only = search(subject, limit=4, shelves={VOICE_SHELF}) or []
        except TypeError:  # a test-injected search without a shelves parameter
            shelf_only = []
        voice = _voice_card(subject, shelf_only)
    # REHYDRATE THE VOICE. Search hands back BRIEFS — title, shelf, a snippet — and the first
    # live run of the both-sides path (Baptist vs Presbyterian, 2026-08-01) presented two voice
    # cards whose body was None: the message promised "the tradition's own voice, in its own
    # reckoning" and delivered an empty card. The voice is the one card in the column whose whole
    # point is its CONTENT — confession, emphasis, the gift it has kept — so it is fetched in
    # full, while the supporting cards stay briefs a reader can open.
    if voice is not None and get is not None:
        full = None
        try:
            full = get(str(voice.get("id") or ""))
        except Exception:  # noqa: BLE001 — a failed lookup falls back to the brief, never breaks
            full = None
        if isinstance(full, dict) and full.get("body"):
            voice = full
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


def compare(query: str, search=None, get=None, acquire=None) -> Optional[Dict[str, Any]]:
    """A comparison, or None when the question is not one.

    `search`, `get` and `acquire` are injected so this stays testable and so the caller decides
    which corpus/surface it reads — this module never reaches for a store of its own until asked.
    `acquire(subject)` is the hand that goes OUT — expand.pull_and_card behind the ask conduit —
    and is only ever tried for a side the keeping cannot stand up by itself.
    """
    subjects = subjects_of(query)
    if not subjects:
        return None
    if search is None:
        from . import corpus
        search = corpus.search
        # `get` defaults ONLY alongside `search`: a caller who injected a search surface has
        # chosen not to touch the resident corpus, and this module must not reach for it anyway.
        if get is None:
            get = corpus.get_card

    sides = [_side(s, search, get=get) for s in subjects]
    missing = [s["subject"] for s in sides if not s["held_as_tradition"]]

    # A MISSING SIDE STANDS ON ITS OWN DOCUMENTS (Matt, 2026-08-02: "It needs to be able to pull
    # the requested information and then make the card for the future, so we only search once per
    # question"). Order is the point:
    #   1. what the keeping ALREADY holds — primary_pd cards cut from the tradition's own texts.
    #      The Nazarene Manual's passages were sitting on the sources shelf while the comparison
    #      said "not here"; having the thing and not presenting it is a miss wearing a refusal.
    #   2. only when nothing is held AND the caller provided an `acquire` hand: go and pull it
    #      NOW — the slower answer — and the pull KEEPS what it cut, so the next asking lands on
    #      branch 1 and never goes out. Search once per question.
    # `held_as_tradition` stays false either way: a curated voice card and a pile of primary
    # passages are different kinds of holding, and the reader is told which they have.
    for s in sides:
        if s["held_as_tradition"]:
            continue
        # The gutenberg shelf COUNTS (2026-08-02): "southern baptists" had 8 held documents —
        # public-domain Baptist histories and the dictionary entry — and this filter admitted
        # only the `sources` shelf, so a side with a shelf-full of primary material reported
        # docs=0 and refused. Every gutenberg card is public domain by construction; a book the
        # library holds whole is exactly the kind of document a missing side may stand on.
        primary = [c for c in (search(s["subject"], limit=8) or [])
                   if c.get("shelf") in ("sources", "gutenberg")
                   or (c.get("source") or {}).get("authority_tier") == "primary_pd"]
        if not primary and acquire is not None:
            try:
                pulled = acquire(s["subject"])
            except Exception:  # noqa: BLE001 — a failed pull leaves an honest refusal, not a 500
                pulled = None
            primary = list((pulled or {}).get("cards") or [])[:5] if isinstance(pulled, dict) \
                else list(pulled or [])[:5]
        if primary:
            s["their_own_documents"] = primary[:5]
    missing_and_empty = [s["subject"] for s in sides
                         if not s["held_as_tradition"] and not s.get("their_own_documents")]

    # SHARED GROUND, only where both sides actually stand on it. Never asserted — read off the
    # cards' own connection edges, so the common root is evidence rather than a claim.
    #
    # MEMBERSHIP IS NOT DOCTRINE. The first live run reported the shelf spine as the two
    # traditions' shared ground — true in the way that two books share a bookcase, and useless in
    # exactly that way, since every tradition on the shelf carries the same `member_of` edge. A
    # vacuous truth presented as a finding teaches a reader to stop reading the findings. Spine
    # edges are excluded; what remains is ground the two actually, specifically share — and when
    # nothing remains, the list is honestly empty rather than padded with the bookcase.
    shared: List[str] = []
    if not missing:
        edges = []
        for s in sides:
            v = s["voice"] or {}
            edges.append({str(e.get("to_card_id")) for e in (v.get("connections") or [])
                          if e.get("relationship") != "member_of"
                          and not str(e.get("to_card_id", "")).startswith("card_spine_")})
        if len(edges) == 2:
            shared = sorted(edges[0] & edges[1])

    documented = [s["subject"] for s in sides
                  if not s["held_as_tradition"] and s.get("their_own_documents")]
    if missing_and_empty:
        have = "; ".join(
            f"{s['subject']}: {s['mentions']} card(s) on the {', '.join(s['shelves'])} shelf"
            for s in sides if s["mentions"] and s["subject"] in missing_and_empty)
        message = (
            f"I cannot compare these honestly: the keeping has no tradition card for "
            f"{' and '.join(missing_and_empty)}. "
            + (f"What it does hold under that name is something else — {have}. " if have else "")
            + "I will not set two things side by side when one of them is not here.")
    elif documented:
        _plural = len(documented) > 1
        message = (
            f"{' and '.join(documented)} "
            + ("are" if _plural else "is")
            + " not among the curated tradition voices, so "
            + ("those sides stand" if _plural else "that side stands")
            + " on passages cut from "
            + ("their" if _plural else "its")
            + " own documents — fetched and kept, so the next asking finds them at once. "
              "Every line is a card you can open.")
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
        # The offer survives ONLY where even the pull came back empty-handed. Offering a person a
        # chore we could have done — or just did — is the want desk's own rule inverted.
        "want": ({"offer": f"open a want for {' and '.join(missing_and_empty)}",
                  "queries": missing_and_empty}
                 if missing_and_empty else None),
    }


__all__ = ["compare", "subjects_of", "VOICE_SHELF"]
