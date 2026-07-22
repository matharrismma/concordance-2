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
# Written WITHOUT apostrophes: the text is normalized the same way before matching, so a phone
# that types don’t (U+2019) cannot walk past a phrase this list already contains. That exact
# miss was live — "i don't want to be here" reached crisis, "i don’t want to be here" did not.
_CRISIS_WORDS = ("suicide", "suicidal", "kill myself", "killing myself", "end my life",
                 "end it all", "want to end it", "wanna end it", "going to end it",
                 "gonna end it", "ready to end it", "take my own life", "taking my own life",
                 "want to die", "wanna die", "dont want to live", "dont want to be here",
                 "dont want to wake up", "no reason to live", "nothing to live for",
                 "no point in living", "better off dead", "better off without me",
                 "cant go on", "cant do this anymore", "hurt myself", "harm myself",
                 "self harm", "self-harm", "cut myself", "overdose", "off myself",
                 "unalive myself", "hang myself", "shoot myself", "goodbye cruel world")

# Smart quotes in, straight quote out; then apostrophes dropped entirely so dont == don't.
_SMART_QUOTES = str.maketrans({"’": "'", "‘": "'", "‛": "'", "´": "'", "`": "'"})


def normalize(text: str) -> str:
    """Lowercase, straighten smart quotes, drop apostrophes, collapse whitespace.

    Safety matching runs on this form. A person reaching for help types on a phone, in a
    hurry, without punctuation — the check must not depend on how their keyboard behaved.
    """
    t = (text or "").lower().translate(_SMART_QUOTES).replace("'", "")
    return re.sub(r"\s+", " ", t).strip()


def is_crisis(text: str) -> bool:
    """The one crisis test. Every surface calls this — a copied list is a list that drifts."""
    return any(w in normalize(text) for w in _CRISIS_WORDS)

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
    t = normalize(text)
    if is_crisis(text):
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

# ── The Gate (Ask/Seek/Knock, Matthew 7:7) ────────────────────────────────────────────────
# Facts by default. When the person's OWN conversation seeks — the God-ward / ultimate questions —
# the door opens and the Word comes (scripture resolves + references), and KEEPS coming. We present
# the paths; we do not cross them (never coerce). Gate closed → genuinely useful, never preachy.
# Crisis is ALWAYS help-first and is never gated or enriched (people before Scripture-as-fix).
_GATE_WORDS = (
    "god", "jesus", "christ", "gospel", "scripture", "bible", "biblical", "psalm", "faith",
    "pray", "prayer", "sinner", "soul", "heaven", "hell", "salvation", "saved", "savior",
    "saviour", "believe", "belief", "church", "holy spirit", "the spirit", "worship", "eternal",
    "eternity", "repent", "grace", "mercy", "the cross", "disciple", "kingdom of god", "born again",
    "the word", "word of god", "creator", "the lord", "spiritual", "religion", "the gospel",
)
_THRESHOLD_REF = "Matthew 7:7-8"
_THRESHOLD_TEXT = ("Ask, and it will be given you. Seek, and you will find. Knock, and it will be "
                   "opened for you. For everyone who asks receives. He who seeks finds. To him who "
                   "knocks it will be opened.")
_THRESHOLD_NOTE = "You knocked. The door is open — and His word stays with you now."

_VERSE_RE = re.compile(r"\b[1-3]?\s?[A-Za-z]{2,}\.?\s+\d{1,3}:\d{1,3}")


def gate_signal(text: str) -> bool:
    """Does this message knock (Ask/Seek/Knock)? True when the conversation turns God-ward or to
    ultimate matters — the person's own seeking opens the door. We never force it."""
    if classify(text or "") in ("ultimate", "scripture", "word_study"):
        return True
    t = " " + (text or "").lower() + " "
    return any(w in t for w in _GATE_WORDS)


def _is_scripture_card(c: Dict[str, Any]) -> bool:
    src = c.get("source") or {}
    if str(c.get("shelf", "")).lower() in ("scripture", "bible", "word", "verse", "gospel", "psalms"):
        return True
    if str(c.get("kind", "")).lower() in ("scripture", "verse"):
        return True
    return bool(_VERSE_RE.search(str(src.get("ref", "")) or "") or _VERSE_RE.search(str(c.get("title", "")) or ""))


def _scripture_from_keeping(text: str, limit: int = 2):
    """Best-effort: real scripture cards from the keeping on this topic — found + cited, never
    generated. Returns [] if none match (we don't force an irrelevant verse)."""
    out = []
    for c in corpus.search(text, limit=8):
        if _is_scripture_card(c):
            out.append(corpus._brief(c))
        if len(out) >= limit:
            break
    return out


def _witnessed(r: Dict[str, Any], text: str, witness: bool, just_opened: bool,
               topical: bool = True) -> Dict[str, Any]:
    """Once the door is open, bring the Word — and keep bringing it. Present, don't cross."""
    if not witness:
        return r
    if just_opened:
        r["threshold"] = {"ref": _THRESHOLD_REF, "text": _THRESHOLD_TEXT, "note": _THRESHOLD_NOTE}
    if topical:
        refs = _scripture_from_keeping(text)
        if refs:
            r["scripture_refs"] = refs
    return r


def respond(text: str, config: EngineConfig, *, gate_open: bool = False,
            gate_just_opened: bool = False) -> Dict[str, Any]:
    """Compose a conduit response: found + verified + cited + curated material only. No LLM.

    The Gate: on the witness surface — or once a .com conversation has opened the door — the full
    witness is surfaced (scripture resolves, references come). Routing still keys ONLY on the
    current text, so crisis and ultimate are byte-identical regardless of gate state."""
    kind = classify(text or "")
    witness = bool(config.witness_surfaced or gate_open)  # the gate opens the full .org experience on .com
    # generated:false is machine-checkable proof of the conduit contract — the front door
    # carries the same flag the coach/verify payloads do (this engine finds; it never generates).
    base: Dict[str, Any] = {"kind": kind, "note": _NOTE, "gate_open": witness, "generated": False}

    if kind == "crisis":
        # Always help-first — never gated, never enriched, never Scripture-as-fix.
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
        return _witnessed({**base, "verify": attach(res, config=config, domain="mathematics")},
                          text, witness, gate_just_opened)

    if kind == "word_study" and witness:
        from .verifiers import scripture
        return _witnessed({**base, "word_study": scripture.word_study(_STRONGS.search(text).group(1).upper())},
                          text, witness, gate_just_opened, topical=False)

    if kind == "scripture" and witness:
        from .verifiers import scripture
        return _witnessed({**base, "scripture": scripture.resolve_ref(_REF.search(text).group(0))},
                          text, witness, gate_just_opened, topical=False)

    # default — and the secular fallback for scripture/word_study when the gate is closed
    return _witnessed({**base, "kind": "found",
                       "results": [corpus._brief(c) for c in corpus.search(text, limit=6)]},
                      text, witness, gate_just_opened)
