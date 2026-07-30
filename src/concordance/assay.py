"""THE CARD ASSAY — a governed process for improving or removing a card.

Matt, 2026-07-30: *"Sometimes a project is best when the excess has been stripped away… We need a
process of improving or removing cards."*

The bias of this module is **improvement**. A card that can be repaired is repaired; removal is the
last answer, not the first, and even then nothing is deleted — `docs/THE_RECORD.md` already settled
that: *"Retraction is a record too. A `retracts` card with its reason. Deleting would destroy the
trail."* That machinery existed and had never once been used (0 retracted cards of 548,585). This
is what uses it.

FOUR VERDICTS, never two:

    STANDS        the card is complete as it is — including short cards
    IMPROVABLE    a specific, named, mechanical repair exists (and this says what it is)
    EMPTY         there is no content here to keep
    CANNOT_CHECK  we cannot tell, and say so rather than guessing

**LENGTH IS NOT THE TEST, and this is the whole reason the module is careful.** Twice in one
session a length rule produced a false finding here. A ≥120-character rule once condemned 330 real
Clarke notes — his entire comment on 1 Chr 1:12 is *"Caphthorim — 'The Cappadocians.' — T."*, 37
characters and complete. And 246 cards were reported as carrying a placeholder because their titles
contained `_xxx`, which is the Roman numeral XXX. Both were confident, both were numeric, both were
wrong. So every rule below asks what the body DOES — does it define, assert, or point — never how
long it is. A test pins that.

The assay reads a card and returns a judgement. It changes nothing: applying an improvement or a
retraction is a separate, explicit act with a reason attached, so a bad rule can never quietly eat
the library.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

STANDS = "STANDS"
IMPROVABLE = "IMPROVABLE"
EMPTY = "EMPTY"
CANNOT_CHECK = "CANNOT_CHECK"

# Boilerplate a carder appended to every card of a kind. Alone it is not content; beside real words
# it is harmless. Matched whole-line so a sentence that merely mentions "article" is untouched.
_BOILERPLATE = (
    "the full 1915 article renders on this card's page.",
    "the full article renders on this card's page.",
    "see the source for the full entry.",
)

# A bare cross-reference: the entry exists in the source and says only "look over there". That is
# FAITHFUL — the source really does say that — so it is never EMPTY. It is IMPROVABLE, because the
# pointer can become an edge in the graph and then it earns its place.
_XREF = re.compile(r"^\s*(?:see\s+also|see|cf\.?|compare)\s+([^.;]{1,80})\.?\s*$", re.I)

# Truncation. THIS RULE WAS WRONG ONCE AND THE NUMBER IS WHY IT IS NARROW NOW.
#
# The first draft was `[a-z,]\s*$` — any body ending in a lowercase letter or a comma — and it
# flagged 157,130 cards, 29% of the library. They were not truncated. They were Scripture verses,
# which are punctuated with a comma precisely because the sentence carries into the next verse
# ("Count it all joy, my brothers, when you fall into various temptations,"), and recipe ingredient
# lines ("6 tablespoons cold butter, cubed"). A complete thing may simply end in a lowercase letter.
#
# So truncation now means only what truncation actually looks like: a word cut in half, an ellipsis
# a slicer left behind, or a sentence abandoned on a dangling function word. When the consequence
# of a rule is queueing work against the library, the rule errs toward leaving things alone.
# NARROWED A THIRD TIME, and the third one is the lesson. After the verse-comma fix, the rule still
# flagged 105 lexicon cards ending in a preposition — but "to violently make gain of" and "the
# occasion of" are COMPLETE BDB glosses. A lexicon ends that way on purpose.
#
# Three misfires of one rule, each from assuming the library writes like prose. It does not: it
# holds verses, glosses, ingredient lists, Hebrew, and commentary, and every one of them ends
# differently. So only signals that are truncation in ANY style survive — a word cut in half, or an
# ellipsis a slicer left behind. Dangling-connective detection is gone; it cost more in false
# accusations than it ever found. Some real truncations will be missed, and that is the right way
# to be wrong when the output is a worklist against a working library.
_TRUNCATED = re.compile(r"(?:\w-|\.\.\.|…)\s*$")

_SLUG_TITLE = re.compile(r"§[a-z]+_[0-9]+(?:_[ivxlcdm]+)?", re.I)


def _clean(body: str) -> str:
    """The body with pure boilerplate lines removed — so a card that is ONLY boilerplate reads as
    empty, while a card that carries boilerplate after real words is judged on the real words."""
    keep = [ln for ln in (body or "").splitlines()
            if ln.strip().lower() not in _BOILERPLATE]
    return "\n".join(keep).strip()


def assay(card: Dict[str, Any]) -> Dict[str, Any]:
    """Judge one card. Returns {verdict, reason, improvement} and touches nothing.

    `improvement` is present only for IMPROVABLE and names the repair in words a person can check,
    because an automated fix nobody can read is how a library gets quietly rewritten.
    """
    if not isinstance(card, dict):
        return {"verdict": CANNOT_CHECK, "reason": "not a card"}
    if card.get("retracted"):
        return {"verdict": STANDS, "reason": "already retracted; the record keeps it"}

    raw = str(card.get("body") or "")
    title = str(card.get("title") or "").strip()
    body = _clean(raw)
    src = card.get("source") or {}

    # ── EMPTY: nothing a reader could take away.
    if not body:
        return {"verdict": EMPTY,
                "reason": ("no body at all" if not raw.strip()
                           else "the body is only carder boilerplate")}
    if title and body.strip().lower() == title.lower():
        return {"verdict": EMPTY, "reason": "the body only repeats the title — it says nothing more"}

    # ── IMPROVABLE: a specific repair, named.
    m = _XREF.match(body)
    if m:
        target = m.group(1).strip()
        # Faithful to the source (the entry really is a cross-reference), so never EMPTY —
        # but a pointer belongs in the graph, where it can actually carry a reader.
        return {"verdict": IMPROVABLE,
                "reason": f"a bare cross-reference to {target!r} — true to the source, but a "
                          f"pointer that only a human can follow",
                "improvement": {"kind": "resolve_xref", "target": target,
                                "how": "add a `see_also` connection to the card that holds it, and "
                                       "let the reader arrive instead of being redirected"}}
    if _TRUNCATED.search(body) and len(body) > 40:
        return {"verdict": IMPROVABLE,
                "reason": "the body stops mid-sentence — it was cut, not written that way",
                "improvement": {"kind": "refill_from_source", "target": str(src.get("label") or ""),
                                "how": "re-mint this card from its source so the sentence finishes"}}
    if _SLUG_TITLE.search(title):
        return {"verdict": IMPROVABLE,
                "reason": "the title carries a raw internal citation slug",
                "improvement": {"kind": "render_title", "target": title,
                                "how": "render the slug the way a person cites it — "
                                       "`Meditations 4.38` rather than `§aur_04_xxxviii`"}}

    # ── CANNOT_CHECK: it has words, but nothing says where they came from. That is a fact about
    # OUR record-keeping, not a charge against the card, so it never routes to removal.
    if not (src.get("label") or src.get("url") or src.get("ref")):
        return {"verdict": CANNOT_CHECK,
                "reason": "real content, but the card names no source — we cannot tell whether it "
                          "is sound, and that is our gap, not its fault"}

    return {"verdict": STANDS, "reason": "complete, sourced, and says something on its own"}


def survey(cards, limit_examples: int = 3) -> Dict[str, Any]:
    """Assay many cards and report the shape of the library. Reporting only — the point of a
    process is that the judgement and the act are separate steps."""
    counts: Dict[str, int] = {STANDS: 0, IMPROVABLE: 0, EMPTY: 0, CANNOT_CHECK: 0}
    by_improvement: Dict[str, int] = {}
    examples: Dict[str, List[Dict[str, str]]] = {}
    by_shelf: Dict[str, Dict[str, int]] = {}
    n = 0
    for c in cards or []:
        n += 1
        a = assay(c)
        v = a["verdict"]
        counts[v] = counts.get(v, 0) + 1
        shelf = str((c or {}).get("shelf") or "?")
        by_shelf.setdefault(shelf, {}).setdefault(v, 0)
        by_shelf[shelf][v] += 1
        if v == IMPROVABLE:
            k = (a.get("improvement") or {}).get("kind", "?")
            by_improvement[k] = by_improvement.get(k, 0) + 1
        if v != STANDS and len(examples.setdefault(v, [])) < limit_examples:
            examples[v].append({"id": str((c or {}).get("id") or ""),
                                "title": str((c or {}).get("title") or "")[:70],
                                "reason": a["reason"]})
    return {"total": n, "counts": counts, "improvements": by_improvement,
            "examples": examples, "by_shelf": by_shelf}


def retraction(card_id: str, reason: str, by: str) -> Dict[str, Any]:
    """The record of a removal — a CARD, not a deletion.

    `THE_RECORD.md`: *"Deleting would destroy the trail."* So a retirement mints a new card that
    says what was withdrawn and why, carries a `retracts` edge to it, and the original stays exactly
    where it was. Views hide a retracted card (`corpus.is_public` already refuses it); the trail
    keeps it forever.

    A reason and a name are both required. An unexplained removal teaches nobody anything, and an
    anonymous one is not accountable to the people this library is for.
    """
    card_id, reason, by = (card_id or "").strip(), (reason or "").strip(), (by or "").strip()
    if not card_id:
        return {"ok": False, "error": "which card?"}
    if not reason:
        return {"ok": False, "error": "a retraction without a reason is just a deletion wearing a "
                                      "record's clothes"}
    if not by:
        return {"ok": False, "error": "no anonymous removals — a retraction carries a name"}
    return {"ok": True, "card": {
        "id": f"card_retract_{card_id}",
        "kind": "note",
        "title": f"Retracted: {card_id}",
        "body": reason,
        "source": {"label": f"{by} — a steward of the keeping", "authority_tier": "operator"},
        "shelf": "record", "box": "retraction",
        "connections": [{"to_card_id": card_id, "relationship": "retracts", "evidence": reason}],
        "author": "steward", "generated": False,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "durable",
        "surface": "secular",
        "extra": {"retracts": card_id, "by": by},
    }}


__all__ = ["assay", "survey", "retraction", "STANDS", "IMPROVABLE", "EMPTY", "CANNOT_CHECK"]
