"""The PATH layer — the answer is a PATH, never a bare card.

Matt, 2026-08-12 (from the Lighthouse Model Spec, reviewing the whole project): "the output is always
a path, never an answer… never more than one next step," and — naming the exact symptom of "responses
aren't great" — "John 3:16 as a default answer to everything is a GATE FAILURE."

So above the retrieved cards, a discerned PATH: (1) the TYPE of question, (2) ONE next step, composed
from what was actually found (a card to open, a passage to read, the four gates to walk, a real person
to reach), and (3) a Scripture ANCHOR that FITS — resolved from the canon, attributed — or the honest
"No anchor found." NOTHING here is generated: the type is classified from the words, the step points at
material we hold, and the anchor is a verse the keeping resolves. Conduit, not oracle.

The nine types (the Spec's "load-bearing component"): crisis · decision · relational · doctrine ·
wisdom · resource · timing · formation · historical.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# ── the classifier ──────────────────────────────────────────────────────────────────────────
# `kind` (from ask.classify) already carries the strong routes; map those first, then read the
# remaining `search` queries by their shape. Order matters — the first match wins.
_KIND_TYPE = {
    "crisis": "crisis", "decision": "decision", "ultimate": "wisdom", "comfort": "relational",
    "date": "historical", "resourceful": "resource", "seeker": "wisdom",
    "scripture": "doctrine", "word_study": "doctrine",
}
_HOWTO = re.compile(r"\bhow\s+(?:do|to|can|would|could|does)\b|\bhow\s+do\s+i\b", re.I)
# The "do i <verb>" branch catches a life-decision ("do I keep the house", "do I take the job"). But
# a HOW-TO reuses those same verbs about a craft, not a choice — "how do i KEEP chickens", "how do i
# TAKE honey", "how do i MOVE a hive" — and was misread as a decision, drawing the four-gates / "wait
# and pray" framing onto a homestead question (measured live 2026-08-31). Guard the branch against a
# leading "how" exactly as the "should i" branch already is, so a how-to falls through to `resource`.
_DECISION = re.compile(r"\b(?:(?<!how )should i|shall i|ought i|is it worth|which (?:should|do) i|"
                       r"(?<!how )do i (?:take|buy|sell|quit|accept|sign|move|marry|leave|keep))\b", re.I)
_DOCTRINE = re.compile(r"\b(what does the bible say|is it a sin|is .* a sin|doctrine|theolog|"
                       r"gospel|salvation|trinity|baptism|covenant|scripture say|god's word)\b", re.I)
_HISTORICAL = re.compile(r"\b(when did|what year|what happened|history of|who (?:was|were)|"
                         r"in what year|date of|century|ancient|battle of)\b", re.I)
_TIMING = re.compile(r"\b(when should|is now the time|how long until|what time|is it time to)\b", re.I)
_FORMATION = re.compile(r"\b(how do i (?:grow|become|learn to|get better at|stop|overcome|practice)|"
                        r"discipl\w*|habit|spiritual|walk with god|obey|pray more|read the bible more)\b", re.I)
_RELATIONAL = re.compile(r"\b(my (?:wife|husband|marriage|son|daughter|child|kid|mother|father|mom|dad|"
                         r"friend|neighbor|boss|family)|forgive|reconcile|conflict with)\b", re.I)
_WISDOM = re.compile(r"\b(should i|how should i (?:live|handle)|is it (?:right|wrong|okay)|what is the "
                     r"(?:meaning|purpose)|why does|why do)\b", re.I)


def question_type(text: str, kind_hint: str = "") -> str:
    t = text or ""
    if kind_hint in _KIND_TYPE:
        return _KIND_TYPE[kind_hint]
    if _DECISION.search(t):               # "should I take the job" — a decision, before wisdom's "should i"
        return "decision"
    if _HISTORICAL.search(t):
        return "historical"
    if _TIMING.search(t):
        return "timing"
    if _DOCTRINE.search(t):
        return "doctrine"
    if _FORMATION.search(t):
        return "formation"
    if _RELATIONAL.search(t):
        return "relational"
    if _HOWTO.search(t):
        return "resource"                 # a practical how-to
    if _WISDOM.search(t):
        return "wisdom"
    return "resource" if kind_hint == "found" else "wisdom"


# ── the anchor ──────────────────────────────────────────────────────────────────────────────
# A curated topical anchor map — subject word -> a verse the keeping RESOLVES (found + attributed,
# never generated). Deliberately sparse: a fitting word or nothing. "No anchor found" is honest and
# correct for most practical questions — better than John 3:16 pasted onto everything (the Spec's
# named gate failure).
_ANCHORS = {
    "work": "Colossians 3:23", "labor": "Colossians 3:23", "build": "Psalm 127:1",
    "money": "Matthew 6:33", "poor": "Proverbs 19:17", "provision": "Philippians 4:19",
    "food": "Matthew 6:26", "hunger": "Matthew 5:6", "harvest": "Galatians 6:9",
    "plant": "Galatians 6:9", "seed": "Galatians 6:9", "water": "John 4:14", "fire": "Isaiah 43:2",
    "heal": "Jeremiah 17:14", "sick": "James 5:14", "wound": "Psalm 147:3", "burn": "Isaiah 43:2",
    "fear": "Isaiah 41:10", "afraid": "Isaiah 41:10", "worry": "Matthew 6:34",
    "wisdom": "James 1:5", "understand": "Proverbs 9:10", "learn": "Proverbs 1:5",
    "teach": "Deuteronomy 6:6-7", "child": "Proverbs 22:6", "children": "Proverbs 22:6",
    "marriage": "Mark 10:9", "family": "Joshua 24:15", "forgive": "Colossians 3:13",
    "shelter": "Psalm 91:1", "home": "Psalm 127:1", "storm": "Matthew 7:24-25",
    "prepare": "Proverbs 21:31", "winter": "Proverbs 6:6-8", "store": "Proverbs 6:6-8",
    "wait": "Isaiah 40:31", "time": "Ecclesiastes 3:1", "decide": "Proverbs 3:5-6",
    "lost": "Luke 15:4", "alone": "Deuteronomy 31:6", "grief": "Psalm 34:18",
}
_STOP = {"the", "a", "an", "of", "to", "in", "how", "do", "i", "my", "for", "and", "or", "with",
         "from", "make", "build", "your", "you", "what", "is", "are", "can", "should", "when", "does"}


def _resolve(ref: str) -> Optional[Dict[str, str]]:
    """The verse's own words, resolved from the canon — found, attributed, never fabricated."""
    try:
        from .verifiers import scripture as _sc
        if "-" in ref:
            vs = (_sc.read_passage(ref).get("verses") or [])
            if vs:
                return {"ref": ref, "text": " ".join((v.get("text") or "") for v in vs[:3])[:400]}
            return None
        one = _sc.resolve_ref(ref)
        return {"ref": one.get("ref", ref), "text": one.get("text", "")} if one.get("status") == "ok" else None
    except Exception:  # noqa: BLE001 — an anchor that cannot resolve is simply omitted
        return None


def anchor(text: str, existing: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, str]]:
    """A Scripture anchor that FITS — the first verse the answer already carries, else a curated
    topical match resolved from the canon, else None ('No anchor found')."""
    if existing:
        for v in existing:
            if v.get("ref") and v.get("text"):
                return {"ref": v["ref"], "text": (v.get("text") or "")[:400]}
    for w in re.findall(r"[a-z]{3,}", (text or "").lower()):
        if w in _STOP:
            continue
        ref = _ANCHORS.get(w)
        if ref:
            got = _resolve(ref)
            if got:
                return got
    return None


# ── the one next step ───────────────────────────────────────────────────────────────────────
_FRAMING = {
    "crisis": "This needs a real person, now — not a search.",
    "decision": "This is a decision to weigh, not just a fact to look up.",
    "relational": "This is about a person you carry.",
    "doctrine": "This is a question about the Word.",
    "wisdom": "This is one of the questions people have always asked.",
    "resource": "This is a practical need — something to do.",
    "timing": "This is a question of timing.",
    "formation": "This is about growing, over time.",
    "historical": "This is a matter of record.",
}


def _step(qtype: str, subject: str, lead: Optional[Dict[str, Any]],
          resources: Optional[List[Dict[str, Any]]], anchor_v: Optional[Dict[str, str]],
          deck: Optional[Dict[str, Any]]) -> str:
    lead_t = (lead or {}).get("title") or ""
    if qtype == "crisis":
        return "Reach a real person right now — someone who can be with you."
    if qtype == "decision":
        return ("Walk it through the four gates: RED — does it align with Jesus' words? FLOOR — does "
                "it break a law or a floor? BROTHERS — who will witness it with you? GOD — wait, and pray.")
    if qtype == "relational":
        return ("Go to the person — plainly and gently" +
                (f", and carry this word: {anchor_v['ref']}." if anchor_v else "."))
    if qtype == "doctrine":
        return (f"Read {anchor_v['ref']} in its own words, then the commentary beside it."
                if anchor_v else (f"Open '{lead_t}' and read it in the Word's own words." if lead_t
                                  else "Search the Word for this, and read the passage itself."))
    if qtype == "formation":
        return "Begin one small practice this week — the Field Kit gives a seven-day step to walk."
    if qtype in ("historical", "timing"):
        return (f"The record: open '{lead_t}'." if lead_t else "The record is thin here — go to the sources.")
    if qtype == "wisdom":
        # A life question is not a card lookup — a random practical card pasted on is the same
        # gate failure as a default verse. Sit with the fitting word, else go to the Word + a brother.
        return (f"Sit with {anchor_v['ref']} — read it slowly, and bring the exact situation you face."
                if anchor_v else "Bring this to the Word and to a wiser brother — start there, not with a search.")
    # resource — the practical default: one card to open, in its own words
    if lead_t:
        return f"Open '{lead_t}' — it has the steps, in its source's own words."
    if deck and deck.get("name"):
        return f"Open the '{deck['name']}' door — the cards for this need are there."
    if resources:
        r0 = resources[0]
        return f"Go to {r0.get('label', 'the pointed source')}."
    return "Bring one more detail and I'll point you to the exact card."


def compose(text: str, *, kind: str = "", subject: str = "",
            lead: Optional[Dict[str, Any]] = None,
            resources: Optional[List[Dict[str, Any]]] = None,
            scripture: Optional[List[Dict[str, Any]]] = None,
            deck: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The PATH for one answer: {type, framing, step, anchor}. Composed from what was found — the
    classified type, ONE next step pointing at real material, and a fitting resolved verse or None."""
    qtype = question_type(text, kind)
    anchor_v = anchor(text, existing=scripture)
    return {
        "type": qtype,
        "framing": _FRAMING.get(qtype, ""),
        "step": _step(qtype, subject or text, lead, resources, anchor_v, deck),
        "anchor": anchor_v,          # {ref, text} or None → the page shows "No anchor found"
    }
