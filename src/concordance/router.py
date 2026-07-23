"""Router — the one who knows whom to call.

The body has many members (1 Cor 12:14). This is the member whose only work is discernment:
read what was brought, name the member that should handle it, and hand off. **It never
answers.** A router that starts answering has become the generalist the body exists to avoid.

Deterministic and rule-based — *no model* — so the body keeps its zero-dependency property
(docs/THE_COMPANION.md §3.2a). This generalises `ask.classify()`, which already routes the
front door with no model, across every member of the body.

Two rules that are not negotiable:
  1. **Crisis outranks everything.** It is checked first, from `ask`'s own word list (imported,
     never copied — a duplicated safety list drifts), and nothing can override it.
  2. **Ambiguity asks, it does not guess.** When two different members tie, the honest answer
     is a question for the person, not a coin flip. Guessing is what a model would do.

Every decision carries `why` — the literal evidence that matched — because a rule-based router
can always explain itself. That is a feature a model cannot offer.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .ask import _ULTIMATE_WORDS, _looks_math, _REF, _STRONGS, is_crisis, normalize

# member -> what it is for. Kept honest: every member here exists as a module today.
MEMBERS: Dict[str, str] = {
    "crisis": "real people, immediately — never a tool's answer",
    "verify": "a checkable claim -> the deterministic verifiers, sealed",
    "word_study": "an original-language word -> lexicon + Strong's",
    "scripture": "a verse reference -> the canon",
    "cross_refs": "what else speaks to this passage",
    "commentary": "public-domain commentary on a passage",
    "almanac": "dates, seasons, observances — verified entries only",
    "characters": "a person of Scripture",
    "prophecy": "a prophetic thread and its fulfilment",
    "steward": "money, bills, resources — never moves money",
    "apothecary": "an ailment or a plant -> traditional remedies, with their cautions",
    "coach": "teaching — a lesson, a next step, at the learner's level",
    "teachings": "the Word, when the weight is ultimate",
    "search": "the keeping — find, attribute, cite",
    "ask_user": "genuinely ambiguous — ask, do not guess",
}

# (priority, member, pattern, why). Lower priority wins. Same priority + different member = tie.
_KEYWORD_RULES: List[Tuple[int, str, str, str]] = [
    (20, "steward", r"\b(bill|bills|budget|rent|invoice|owe|debt|tithe|offering|paycheck|expense|ledger|afford|groceries|savings|spend|spending)\b", "money/resources"),
    (19, "apothecary", r"\b(remed(y|ies)|herbal|herbs?|tincture|poultice|salve|tonic|"
                       r"sore throat|cough|congest\w*|runny nose|head\s?ache|migraine|"
                       r"nause\w*|indigestion|heartburn|upset stomach|bloat\w*|insomnia|sleepless|"
                       r"sunburn|burns?|rash|bruise|sprain|cramps?|sore muscles?|"
                       r"(what|which)\s+(herb|plant|tea|remedy|helps?|is good|can i take|to take)\b[^?]*"
                       r"(throat|cough|cold|head|sleep|nause|stomach|pain|nerves?|skin))\b", "an ailment or a plant"),
    (20, "coach", r"\b(teach|lesson|phonics|spelling|spell|curriculum|grade|homework|learn to read|next step)\b", "teaching"),
    (21, "cross_refs", r"\b(cross[- ]?refs?|cross[- ]?references?|related verses?|parallel passages?)\b", "cross-reference"),
    (21, "commentary", r"\b(commentary|commentaries|exposition|what did the fathers say)\b", "commentary"),
    (22, "almanac", r"\b(almanac|feast|festival|equinox|solstice|liturgical|church calendar|what day is)\b", "calendar/observance"),
    (22, "characters", r"\b(who was|who were|character of)\b", "a person of Scripture"),
    (22, "prophecy", r"\b(prophec(y|ies)|prophetic|fulfilled in|foretold)\b", "prophecy"),
    (23, "teachings", r"\b(sermon on the mount|parable|beatitude|words in red|what did jesus say)\b", "the Word"),
]
_COMPILED = [(p, m, re.compile(rx, re.I), why) for p, m, rx, why in _KEYWORD_RULES]

_CONVERT = re.compile(r"\b(convert|how many)\b.*\b(to|in)\b", re.I)


def _hits(text: str) -> List[Tuple[int, str, str]]:
    """All rules that matched, as (priority, member, why). Crisis short-circuits upstream."""
    t = text or ""
    low = normalize(t)
    out: List[Tuple[int, str, str]] = []

    # 10s — structured signals. Unambiguous shapes, so they outrank keywords.
    m = _STRONGS.search(t)
    if m:
        out.append((10, "word_study", f"Strong's number {m.group(1)}"))
    m = _REF.search(t)
    if m:
        out.append((11, "scripture", f"scripture reference {m.group(0).strip()!r}"))
    if _looks_math(t):
        out.append((12, "verify", "an equation to check"))
    elif _CONVERT.search(low):
        out.append((13, "verify", "a unit conversion to check"))

    # 20s — domain keywords.
    for pri, member, rx, why in _COMPILED:
        mm = rx.search(t)
        if mm:
            out.append((pri, member, f"{why} ({mm.group(0).strip()!r})"))

    # 30 — ultimate matters, below anything structured.
    hit = next((w for w in _ULTIMATE_WORDS if w in low), None)
    if hit:
        out.append((30, "teachings", f"an ultimate question ({hit!r})"))

    return out


def route(text: str) -> Dict[str, Any]:
    """Name the member who should answer. Never answers. Always explains itself.

    -> {member, why, alternatives, considered, answered_here=False}
    """
    t = (text or "").strip()
    low = t.lower()

    # 1. Crisis outranks everything. Never routed anywhere but real help.
    if is_crisis(t):
        return {"member": "crisis", "why": "someone may be in danger — real people first",
                "alternatives": [], "considered": ["crisis"], "answered_here": False}

    if not t:
        return {"member": "ask_user", "why": "nothing was brought",
                "alternatives": [], "considered": [], "answered_here": False}

    hits = _hits(t)
    if not hits:
        return {"member": "search", "why": "no specialist signal — search the keeping",
                "alternatives": [], "considered": [], "answered_here": False}

    hits.sort(key=lambda h: h[0])
    best = hits[0][0]
    top = [h for h in hits if h[0] == best]
    distinct = sorted({h[1] for h in top})
    considered = sorted({h[1] for h in hits})

    # 2. A genuine tie asks; it does not guess.
    if len(distinct) > 1:
        return {"member": "ask_user",
                "why": "more than one member fits — " + ", ".join(f"{h[1]} ({h[2]})" for h in top),
                "alternatives": distinct, "considered": considered, "answered_here": False}

    return {"member": top[0][1], "why": top[0][2],
            "alternatives": [m for m in considered if m != top[0][1]],
            "considered": considered, "answered_here": False}


def members() -> Dict[str, str]:
    """The body, and what each member is for."""
    return dict(MEMBERS)
