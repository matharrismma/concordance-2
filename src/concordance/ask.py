"""Ask — the conduit front door: a concordance with a voice.

It FINDS, VERIFIES, and CITES; it never generates the answer. Routing is deterministic (no
model), so the front door stays sovereign and honest — every word returned is either a fixed
frame or found/verified/cited material. On ultimate matters it points to Christ, Scripture,
and real people; in crisis it puts real help first. A window, not a wall; a conduit, not the
source — success is the person freer and nearer Christ, needing the tool less (John 3:30).

No LLM. No runtime generation. The "voice" is the engine's existing verbs — verify, resolve,
word_study, search — plus curated, attributed pointers.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from . import corpus
from .config import EngineConfig

# Real help — never generated, never laundered. Crisis gets people first, not Scripture-as-fix.
_CRISIS_RESOURCES = [
    {"label": "Call or text 988 — US Suicide & Crisis Lifeline, 24/7", "ref": "tel:988"},
    {"label": "findahelpline.com — a free, confidential helpline in your country", "ref": "https://findahelpline.com"},
    {"label": "Reach a real person today — a friend, a pastor, a doctor", "ref": None},
]
_CRISIS_WORDS = ("suicide", "kill myself", "killing myself", "end my life", "end it all",
                 "want to die", "wanna die", "hurt myself", "self harm", "self-harm", "overdose",
                 "no reason to live", "better off dead", "don't want to be here", "cut myself")

_ULTIMATE_WORDS = ("meaning of life", "why am i here", "my purpose", "point of it all", "point of life",
                   "suffering", "why does god", "why would god", "afraid to die", "fear of death",
                   "guilt", "ashamed", "shame", "worthless", "hopeless", "no hope", "despair",
                   "forgiven", "forgiveness", "salvation", "be saved", "who am i", "my identity",
                   "so lonely", "all alone", "meaningless", "empty inside")

# Fixed pointer — points UP and OUT, never poses as the source. Accurate public-domain WEB.
_ULTIMATE_MESSAGE = ("This isn't a question a tool should answer for you, and this one won't "
                     "pretend to. The wisdom you're reaching for is in a Person, not in software. "
                     "Here is His word on it — and here are real people to walk with.")
_ULTIMATE_SCRIPTURE = [
    ("Matthew 11:28", "Come to me, all you who labor and are heavily burdened, and I will give you rest."),
    ("John 14:6", "Jesus said to him, “I am the way, the truth, and the life. No one comes to the Father, except through me.”"),
    ("Psalm 34:18", "Yahweh is near to those who have a broken heart, and saves those who have a crushed spirit."),
]

_MATH_EQ = re.compile(r"^\s*(.+?)\s*=\s*(.+?)\s*$")
_REF = re.compile(r"\b[1-3]?\s?[A-Za-z]{2,}\.?\s+\d{1,3}:\d{1,3}\b")
_STRONGS = re.compile(r"\b([GHgh]\d{1,4})\b")


def _looks_math(t: str) -> bool:
    m = _MATH_EQ.match(t or "")
    if not m:
        return False
    sides = m.group(1) + m.group(2)
    return bool(re.search(r"[0-9x+\-*/^()]", sides)) and not re.search(r"[A-Za-z]{4,}", sides)


def classify(text: str) -> str:
    """Deterministically route the input. Crisis first (safety); then structured (Strong's,
    scripture ref, math); then ultimate matters; else search the keeping."""
    t = (text or "").lower()
    if any(w in t for w in _CRISIS_WORDS):
        return "crisis"
    if _STRONGS.search(text or ""):
        return "word_study"
    if _REF.search(text or ""):
        return "scripture"
    if _looks_math(text or ""):
        return "verify"
    if any(w in t for w in _ULTIMATE_WORDS):
        return "ultimate"
    return "search"


_NOTE = ("This finds and verifies; it does not generate the answer. A window, not a wall — "
         "the wisdom is in Christ, not this tool.")


def respond(text: str, config: EngineConfig) -> Dict[str, Any]:
    """Compose a conduit response: found + verified + cited + curated material only. No LLM."""
    kind = classify(text or "")
    base: Dict[str, Any] = {"kind": kind, "note": _NOTE}

    if kind == "crisis":
        return {**base, "message": "You matter, and you don't have to carry this alone. Please "
                "reach a real person right now — someone who can be with you.",
                "resources": _CRISIS_RESOURCES}

    if kind == "ultimate":
        return {**base, "message": _ULTIMATE_MESSAGE,
                "scripture": [{"ref": r, "text": t} for r, t in _ULTIMATE_SCRIPTURE],
                "real_help": ["A pastor, or a local church", "Someone who loves you", "Prayer — He hears"],
                "also_in_the_keeping": [corpus._brief(c) for c in corpus.search(text, limit=4)]}

    if kind == "verify":
        from .derivation import verify as _verify
        from .receipts import attach
        m = _MATH_EQ.match(text)
        res = _verify({"mode": "equality",
                       "params": {"expr_a": m.group(1).strip(), "expr_b": m.group(2).strip(), "variables": {}}})
        return {**base, "verify": attach(res, config=config, domain="mathematics")}

    if kind == "word_study" and config.witness_surfaced:
        from .verifiers import scripture
        return {**base, "word_study": scripture.word_study(_STRONGS.search(text).group(1).upper())}

    if kind == "scripture" and config.witness_surfaced:
        from .verifiers import scripture
        return {**base, "scripture": scripture.resolve_ref(_REF.search(text).group(0))}

    # default — and the secular fallback for scripture/word_study: search the shared keeping
    return {**base, "kind": "found", "results": [corpus._brief(c) for c in corpus.search(text, limit=6)]}
