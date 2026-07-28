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
import time
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
    # found: "text or ''" only substitutes the fallback for a FALSY text — a truthy non-string
    # (an int/list from an uncoerced caller) survives past that guard and crashes on ".lower()".
    # is_crisis() (the safety-critical function built on this) must never crash instead of
    # answering — every current caller happens to coerce first, but this is the one place that
    # should defend its own contract regardless, matching corpus.search()'s identical fix.
    t = (str(text) if text else "").lower().translate(_SMART_QUOTES).replace("'", "")
    return re.sub(r"\s+", " ", t).strip()


def is_crisis(text: str) -> bool:
    """The one crisis test. Every surface calls this — a copied list is a list that drifts."""
    return any(w in normalize(text) for w in _CRISIS_WORDS)


# The Fellowship Mesh ("The Way") is hidden — never advertised. The agent opens the door ONLY when
# someone types something that shows they are seeking the body: a longing for other believers, or a
# confession of Christ. Ask, seek, knock (Matthew 7:7); treasure hidden in a field (Matthew 13:44).
_WAY_PHRASES = (
    "other believers", "fellow believers", "community of believers", "network of believers",
    "find believers", "meet believers", "connect with believers", "find fellowship", "a fellowship",
    "meet other christians", "connect with christians", "find other christians", "the remnant",
    "gather with believers", "find my people", "body of christ", "the flock",
    "fellowship of believers", "other christians near", "christians near me")


def _seeks_the_way(text: str) -> bool:
    """Does this utterance seek the hidden fellowship — a longing for the body, or a confession? Kept
    specific so the door does not open to the merely curious; the crisis path has already returned."""
    t = normalize(text)
    if any(p in t for p in _WAY_PHRASES):
        return True
    try:
        from . import mesh
        return mesh._confesses(text)
    except Exception:  # noqa: BLE001 — the door simply stays closed if the mesh is unavailable
        return False

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

# ── the one decision no tool can make, or complete, for a person ────────────────────────────
# When someone says, plainly, that they are ready to respond in faith — not asking about
# salvation in the abstract (that's "ultimate"), but ready NOW — the fitting thing is not more
# of this tool's own words. It is Scripture, in the order the Church has long walked people
# through it (the Romans Road), and a real person to go to next. Checked BEFORE _ULTIMATE_WORDS
# in classify() so this more specific, more urgent moment is never swallowed by the general
# "ultimate matters" bucket — and it opens the Gate itself (Ask/Seek/Knock): this IS the knock.
_DECISION_PHRASES = (
    "i want to accept jesus", "i want to accept christ", "accept jesus as my savior",
    "accept jesus as my personal savior", "accept christ as my savior", "accept christ as my lord",
    "i want to be saved", "how can i be saved", "how do i get saved", "how do i become saved",
    "i want to ask jesus into my heart", "ask jesus into my heart", "invite jesus into my heart",
    "i want to give my life to christ", "give my life to jesus", "give my life to god",
    "i want to become a christian", "how do i become a christian",
    "i want to follow jesus", "i want to follow christ",
    "i want to be born again", "how do i get born again",
    "i want to receive christ", "i want to receive jesus",
    "i want to trust jesus", "i want to trust in jesus", "i want to trust christ",
    "i want to confess my faith", "profession of faith", "statement of faith",
    "declare my faith in christ", "declare my faith in jesus",
    "sinners prayer", "pray the sinners prayer",
    "i want to make a decision for christ", "decision for christ",
    "how do i get right with god", "i want to give my heart to jesus",
    "i want to surrender my life to christ", "i want to surrender my life to jesus",
)


def wants_to_decide(text: str) -> bool:
    """Is this person saying, plainly, that they are ready to respond in faith right now? Not
    "ultimate" musing — a decision. The Romans Road answers this, not this tool's own words."""
    t = " " + normalize(text) + " "
    return any((" " + p + " ") in t for p in _DECISION_PHRASES)


# The Romans Road — God's own word, in order; found and cited from the WEB (public domain),
# never generated or paraphrased. This tool presents it and points to a real person; it never
# prays it for you, completes it for you, or claims the authority to declare the outcome.
_DECISION_MESSAGE = ("This is the one decision no tool can make for you, or complete for you. "
                     "Here is God's own word on it, in the order the Church has long walked "
                     "people through — the Romans Road. Read it, then find a real person: a "
                     "pastor, an elder, a Christian near you. Tell them. That is where this goes "
                     "next — not here.")
_ROMANS_ROAD = [
    ("Romans 3:23", "for all have sinned, and fall short of the glory of God;"),
    ("Romans 6:23", "For the wages of sin is death, but the free gift of God is eternal life in Christ Jesus our Lord."),
    ("Romans 5:8", "But God commends his own love toward us, in that while we were yet sinners, Christ died for us."),
    ("Romans 10:9", "that if you will confess with your mouth that Jesus is Lord and believe in your heart that God raised him from the dead, you will be saved."),
    ("Romans 10:10", "For with the heart one believes resulting in righteousness; and with the mouth confession is made resulting in salvation."),
    ("Romans 10:11", "For the Scripture says, “Whoever believes in him will not be disappointed.”"),
    ("Romans 10:13", "For, “Whoever will call on the name of the Lord will be saved.”"),
]

# ── discernment: which Scripture is being asked about, however a person writes it ───────────
# A phone keyboard buries the colon two layers deep, so people type "John 3 16"; dictation
# produces the same. And the church has named its passages for centuries — "the prodigal son"
# IS Luke 15:11-32. All deterministic: a loose numeric form is trusted only when the canon
# actually resolves it, so "Room 12 14" is never mistaken for a book.
_REF_LOOSE = re.compile(
    r"\b([1-3]?\s?[A-Za-z]{2,})\.?\s+(\d{1,3})\s*(?:[:.,]|v(?:erse)?\s*|\s)\s*"
    r"(\d{1,3})(?:\s*[-\u2013]\s*(\d{1,3}))?\b")

# The names the church already uses — gathered, not authored. Longest match first, so
# "parable of the lost sheep" never half-matches a shorter key.
_PASSAGES = {
    "parable of the sower": "Matthew 13:1-23", "the sower": "Matthew 13:1-23",
    "prodigal son": "Luke 15:11-32", "good samaritan": "Luke 10:25-37",
    "parable of the lost sheep": "Luke 15:1-7", "lost sheep": "Luke 15:1-7",
    "mustard seed": "Matthew 13:31-32", "ten virgins": "Matthew 25:1-13",
    "parable of the talents": "Matthew 25:14-30", "rich fool": "Luke 12:13-21",
    "lords prayer": "Matthew 6:9-13", "beatitudes": "Matthew 5:3-12",
    "sermon on the mount": "Matthew 5:1-12", "golden rule": "Matthew 7:12",
    "great commission": "Matthew 28:18-20", "greatest commandment": "Matthew 22:36-40",
    "great commandment": "Matthew 22:36-40", "ten commandments": "Exodus 20:1-17",
    "the fall": "Genesis 3:1-24", "noahs ark": "Genesis 6:9-22",
    "the flood": "Genesis 7:1-24", "tower of babel": "Genesis 11:1-9",
    "david and goliath": "1 Samuel 17:32-51", "shepherds psalm": "Psalm 23:1-6",
    "twenty third psalm": "Psalm 23:1-6", "valley of dry bones": "Ezekiel 37:1-14",
    "lions den": "Daniel 6:16-23", "fiery furnace": "Daniel 3:16-28",
    "jonah and the whale": "Jonah 1:1-17", "jonah and the fish": "Jonah 1:1-17",
    "parting of the red sea": "Exodus 14:21-31", "red sea": "Exodus 14:21-31",
    "burning bush": "Exodus 3:1-14", "pentecost": "Acts 2:1-21",
    "road to damascus": "Acts 9:1-19", "damascus road": "Acts 9:1-19",
    "doubting thomas": "John 20:24-29", "walking on water": "Matthew 14:22-33",
    "walks on water": "Matthew 14:22-33",
    "feeding of the five thousand": "Matthew 14:13-21",
    "feeds the five thousand": "Matthew 14:13-21",
    "water into wine": "John 2:1-11", "wedding at cana": "John 2:1-11",
    "raising of lazarus": "John 11:38-44", "last supper": "Luke 22:14-23",
    "the crucifixion": "John 19:16-30", "the resurrection": "Luke 24:1-12",
    "the ascension": "Acts 1:6-11", "born again": "John 3:1-21",
    "nicodemus": "John 3:1-21", "woman at the well": "John 4:7-26",
    "fruit of the spirit": "Galatians 5:22-23", "armor of god": "Ephesians 6:10-18",
    "love chapter": "1 Corinthians 13:1-13", "love is patient": "1 Corinthians 13:4-8",
    "hall of faith": "Hebrews 11:1-40", "faith chapter": "Hebrews 11:1-40",
    "by grace through faith": "Ephesians 2:8-9", "the word became flesh": "John 1:1-14",
    "creation": "Genesis 1:1-31",
}
_PASSAGE_KEYS = sorted(_PASSAGES, key=len, reverse=True)

_EXPLAIN = re.compile(
    r"\b(explain|mean(?:s|ing)?|understand|study|teach|what does|what is|tell me about"
    r"|help me with)\b", re.I)

# A person bringing their own hurt is not a search query. Below crisis (which outranks everything
# and is handled first), discern first-person distress and meet it with a fitting word of
# Scripture — gently, pointing to Christ. The verse is RESOLVED live from the canon, never
# hardcoded, so it is found and attributed, not generated.
_COMFORT_VERSE = {
    "anxious": "Philippians 4:6-7", "anxiety": "Philippians 4:6-7", "worried": "Matthew 6:34",
    "worry": "Matthew 6:34", "afraid": "Isaiah 41:10", "fear": "Isaiah 41:10",
    "scared": "Isaiah 41:10", "fearful": "Isaiah 41:10", "alone": "Deuteronomy 31:6",
    "lonely": "Hebrews 13:5", "abandoned": "Hebrews 13:5", "weary": "Matthew 11:28",
    "exhausted": "Matthew 11:28", "overwhelmed": "Psalm 61:2", "hopeless": "Romans 15:13",
    "despair": "Romans 15:13", "grief": "Psalm 34:18", "grieving": "Psalm 34:18",
    "mourning": "Matthew 5:4", "sad": "Psalm 34:18", "depressed": "Psalm 42:11",
    "broken": "Psalm 147:3", "heartbroken": "Psalm 147:3", "ashamed": "Romans 8:1",
    "guilty": "Romans 8:1", "lost": "Luke 19:10", "empty": "Psalm 23:1", "hurting": "Psalm 34:18",
    "discouraged": "Joshua 1:9", "helpless": "Psalm 46:1", "restless": "Matthew 11:28",
}
_DISTRESS_WORDS = tuple(_COMFORT_VERSE.keys())
_FIRST_PERSON = re.compile(r"\b(i|im|i'm|i\s*am|my|me|ive|i've|feel|feeling)\b", re.I)


def distress_ref(text: str) -> str:
    """If someone brings their OWN hurt (first-person + a feeling word) and it is NOT a crisis,
    the fitting comfort verse — a canon reference to resolve. Else ''. Never fabricates."""
    if is_crisis(text) or not _FIRST_PERSON.search(text or ""):
        return ""
    low = " " + normalize(text) + " "
    for w in _DISTRESS_WORDS:
        if (" " + w) in low:
            return _COMFORT_VERSE[w]
    return ""


# Honest fallback — a random classic is worse than an honest "I don't know". When the keeping's
# best hit shares no real word with the question, say so plainly instead of dumping it.
_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "is", "are", "was", "were", "do", "does", "did", "how",
    "what", "why", "who", "when", "where", "which", "that", "this", "it", "its", "for", "and",
    "or", "on", "at", "by", "with", "about", "i", "you", "my", "me", "we", "can", "could",
    "should", "would", "will", "tell", "explain", "mean", "means", "meaning", "so", "if", "be",
    "am", "as", "from", "into", "than", "then", "there", "here", "some", "any", "old", "new"))
_WORD3 = re.compile(r"[a-z]{3,}")
_QUESTION = re.compile(
    r"^\s*(is|are|was|were|do|does|did|can|could|how|why|when|where|which|will|should|has|have)\b",
    re.I)


def _content_tokens(s: str) -> set:
    return {w for w in _WORD3.findall((s or "").lower()) if w not in _STOP}


def _is_question(text: str) -> bool:
    t = (text or "").strip()
    return t.endswith("?") or bool(_QUESTION.match(t))


def _shares_a_word(text: str, card: Dict[str, Any]) -> bool:
    """Does the keeping's hit actually share a DISTINCTIVE word with what was asked? A match on a
    common word ('year', 'day') is not enough — 'what year did the Titanic sink' must be carried by
    a hit that names the Titanic, not merely one that says 'year'. So when the question has specific
    words (≥5 letters), require one of THOSE to match; only fall back to any-word when it has none."""
    q = _content_tokens(text)
    if not q:
        return True                                   # nothing specific asked — don't second-guess
    hay = _content_tokens((card.get("title") or "") + " " + (card.get("body") or ""))
    distinctive = {w for w in q if len(w) >= 5}
    return bool(distinctive & hay) if distinctive else bool(q & hay)


def find_ref(text: str):
    """The one place a scripture reference is discerned from prose. Strict form first, then
    the church passage names, then phone-typed loose forms validated against the canon."""
    t = text or ""
    m = _REF.search(t)
    if m:
        return m.group(0)
    low = " " + normalize(t) + " "
    for name in _PASSAGE_KEYS:
        if (" " + name + " ") in low or low.rstrip().endswith(" " + name):
            return _PASSAGES[name]
    m = _REF_LOOSE.search(t)
    if m:
        cand = m.group(1).strip() + " " + m.group(2) + ":" + m.group(3)
        try:
            from .verifiers import scripture as _s
            if _s.resolve_ref(cand).get("status") == "ok":
                return cand + (("-" + m.group(4)) if m.group(4) else "")
        except Exception:  # noqa: BLE001
            return None
    # chapter-only — "Psalm 23", "what does John 3 say", "read Romans 8" — trusted ONLY when the
    # canon actually resolves it, so "have 3 apples" or "Route 66" never becomes Scripture. The
    # whole chapter is read downstream.
    try:
        from .verifiers import scripture as _sc2
        for mc in _CHAPTER.finditer(t):
            cand = re.sub(r"\s+", " ", mc.group(1).strip()) + " " + mc.group(2)
            if _sc2.read_passage(cand).get("verses"):
                return cand
    except Exception:  # noqa: BLE001
        pass
    return None


_MATH_EQ = re.compile(r"^\s*(.+?)\s*=\s*(.+?)\s*$")
_REF = re.compile(r"\b[1-3]?\s?[A-Za-z]{2,}\.?\s+\d{1,3}:\d{1,3}\b")
# a bare "<book> <chapter>" (no verse) — validated against the canon in find_ref before it is trusted
_CHAPTER = re.compile(r"\b([1-3]?\s?[A-Za-z]{2,})\.?\s+(\d{1,3})\b")
_STRONGS = re.compile(r"\b([GHgh]\d{1,4})\b")


def _looks_math(t: str) -> bool:
    m = _MATH_EQ.match(t or "")
    if not m:
        return False
    sides = m.group(1) + m.group(2)
    return bool(re.search(r"[0-9x+\-*/^()]", sides)) and not re.search(r"[A-Za-z]{4,}", sides)


# A checkable primality claim/question — "is 17 prime?", "17 is prime", "is 15 composite", "15 is not
# prime". A verification engine should VERIFY it (17 → HOLDS), not return keyword-matched sequences.
_PRIME_Q = re.compile(r"\bis\s+(\d{1,12})\s+(?:an?\s+)?(prime|composite)(?:\s+number)?\b", re.I)
_PRIME_D = re.compile(r"\b(\d{1,12})\s+is\s+(not\s+)?(?:an?\s+)?(prime|composite)(?:\s+number)?\b", re.I)


def _primality_claim(text: str):
    """(n, claimed_prime) if the text asks/claims a primality, else None."""
    m = _PRIME_Q.search(text or "")
    if m:
        return int(m.group(1)), (m.group(2).lower() == "prime")
    m = _PRIME_D.search(text or "")
    if m:
        claim = (m.group(3).lower() == "prime")
        return int(m.group(1)), (not claim if m.group(2) else claim)
    return None


# A posture of service (Matt: "it is more of a posture of service than anything"). Beyond the
# narrow distress words, when someone speaks a FIRST-PERSON struggle — and is NOT asking a factual
# question — we meet them as a servant would: sit with them, offer the companion who walked it, let
# the Word speak. Conservative on purpose: a factual query ("what was Goliath", "look up grief")
# is served as a fact, never seated; crisis is a higher lane and is decided first.
_FACTUAL_INTENT = re.compile(
    r"\b(learn|teach|tell me|what('?s| is| are| was| were)|who('?s| is| was| were)|where "
    r"(is|was)|when (did|was)|how (do|does|did|to|many|much)|define|definition|explain|look up|"
    r"search|list|meaning of|history of|about the|difference between)\b", re.I)
_FIRST_PERSON_STATE = re.compile(
    r"\b(i feel|i'?m |im |i am |i can'?t|i cant|i failed|i lost|i'?ve |i have been|i keep|i just|"
    r"i don'?t know|i dont know|my heart|i messed|i ruined|i hate myself|i give up|i'?m not|"
    r"i can not|i wander|i doubt|i'?m so|i feel like)\b", re.I)


def _wants_a_companion(text: str) -> bool:
    """A first-person struggle (not a factual question) that a biblical moment can sit with."""
    t = text or ""
    if _FACTUAL_INTENT.search(t) or not _FIRST_PERSON_STATE.search(t):
        return False
    from . import archetypes as _arch
    return _arch.best(t) is not None


# "What does X mean?" / "define X" / "the meaning of X" — a request to DEFINE a term. We look the
# term up on the WORD shelves (lexicon = the tongues, dictionary = English) instead of keyword-matching
# the whole sentence — which once answered "what does agape mean" with "mean deviation from the mean".
_DEFINE_ASK = re.compile(
    r"(?:what\s+do(?:es)?\s+(?:the\s+word\s+|the\s+term\s+|an?\s+)?['\"]?(?P<a>[^?'\".]+?)['\"]?\s+"
    r"(?:mean|means|stand\s+for|signify|denote|refer\s+to)"
    r"|(?:define|definition\s+of|meaning\s+of|what\s+is\s+the\s+(?:meaning|definition)\s+of)\s+"
    r"(?:the\s+word\s+|the\s+term\s+)?['\"]?(?P<b>[^?'\".]+?)['\"]?)\s*[?.!]?\s*$", re.I)
_WORD_SHELVES = {"dictionary", "lexicon", "tongues", "word", "hebrew_ot", "greek_nt", "thesaurus"}


def define_term(text: str) -> Optional[str]:
    """The term someone asked us to define, or None. A TERM (1-3 words), not a clause."""
    m = _DEFINE_ASK.search((text or "").strip())
    if not m:
        return None
    term = (m.group("a") or m.group("b") or "").strip().strip(".?!\"' ")
    if term and 1 <= len(term.split()) <= 3 and re.search(r"[A-Za-zͰ-Ͽ֐-׿]", term):
        return term
    return None


# Understanding what they're ASKING — the subject is what remains when the question-scaffolding is
# taken away. "how far away is the moon" is a question about the MOON; searching the whole sentence
# lets "far/away/is/the" drown it (and even mis-predict the deck). We keep the content words.
_STOP = {"how", "what", "when", "where", "who", "whom", "whose", "why", "which",
         "is", "are", "was", "were", "be", "been", "am", "do", "does", "did", "done",
         "has", "have", "had", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
         "the", "a", "an", "of", "to", "in", "on", "at", "for", "and", "or", "but", "about",
         "as", "by", "with", "from", "into", "please", "tell", "me", "us", "give", "show",
         "there", "that", "this", "these", "those", "it", "its", "i", "you", "we", "they",
         "far", "away", "many", "much", "really", "actually", "exactly", "some", "any"}


def subject(text: str) -> str:
    """What the person is actually asking about — content words, question-scaffolding removed."""
    words = re.findall(r"[A-Za-z0-9']+", (text or "").lower())
    return " ".join(w for w in words if w not in _STOP).strip()


def anticipate(text: str, r: Dict[str, Any]) -> list:
    """Be a step ahead: the likely NEXT thing to ask, as clickable follow-ups. A concierge, never a
    salesman — NOTHING on crisis or grief (you don't upsell someone who is hurting), and never more
    than three. Each is {label, prompt}; the prompt routes through this same conduit."""
    kind = r.get("kind")
    if kind in ("crisis", "comfort", "reminder", "kept_list", "kept_note"):
        return []
    subj = subject(text)
    if kind == "scripture" and r.get("scripture"):
        ref = (r["scripture"][0].get("ref") or "").strip()
        base = ref.split(":")[0] if ref else ""
        out = []
        if base:
            out.append({"label": "Read the whole chapter", "prompt": base})
        if ref:
            out.append({"label": "What does it mean?", "prompt": "explain " + ref})
            out.append({"label": "The original words", "prompt": "the original words of " + ref})
        return out[:3]
    if kind in ("define", "word_study"):
        term = define_term(text) or (r.get("word_study") or {}).get("word") or subj
        if not term:
            return []
        return [{"label": 'Where "%s" is used' % term, "prompt": term + " in the bible"},
                {"label": "In the original tongue", "prompt": "the Greek or Hebrew word for " + term}]
    if kind == "verify" and (r.get("verify") or {}).get("verdict"):
        return [{"label": "Show the worked proof", "prompt": "show me the worked proof"}]
    if kind == "compute":
        return []                                  # a number is a complete answer — no clutter
    if kind == "resourceful":                      # keep first things first when improvising
        return [{"label": "What keeps me alive first?", "prompt": "the rule of threes"}]
    if subj:                                        # a search/fact — where to go deeper
        return [{"label": "What connects to this?", "prompt": "what connects to " + subj},
                {"label": "See it in the keeping", "prompt": subj}]
    return []


# Resourcefulness — "use what is available to accomplish the task" (Matt, 2026-07-26: so that even
# someone with nothing could figure out a solution from what they have on hand). The practical
# shelves of the keeping — the field library, the apothecary, the almanac, the free tools — hold
# what a named resource enables. We SURFACE that knowledge; we never invent a plan.
# The genuinely practical/how-to shelves — the field library, herbs, the almanac, the free tools.
# Deliberately NOT "reference"/"medicine"/"nutrition": those are dictionary/drug/food-row data that
# add noise ("Judas Iscariot", "Bottle Brush") to a 'what can I do with this' answer, not help.
_PRACTICAL_SHELVES = frozenset({"survival", "apothecary", "almanac", "access"})
_RESOURCEFUL = re.compile(
    r"(what (?:can|could|should) i (?:do|make|build|use|create|cook|fix|craft)\b.*\b(?:with|from|out of)\b"
    r"|(?:make|build|create|improvise|fix|cook|craft)\b.+\b(?:with|from|out of)\b"
    r"|all i (?:have|got)\b|i only have\b|i just have\b|i've only got\b|with (?:only|just)\b)", re.I)


def _wants_resourceful(text: str) -> bool:
    """A 'what can I do with what I have' question — material resources named, a solution sought.
    Placed AFTER crisis/comfort/ultimate in classify, so hurt and ultimate questions are met first;
    if it wrongly fires, the practical-shelf search simply finds nothing and degrades gently."""
    t = normalize(text or "")
    if _RESOURCEFUL.search(t):
        return True
    return bool(re.search(r"\bi have\b.+\bwhat (?:can|could|should|do) i\b", t))


def classify(text: str) -> str:
    """Deterministically route the input. Crisis first (safety); then structured (Strong's,
    scripture ref, math); then ultimate matters; else search the keeping."""
    t = normalize(text)
    if is_crisis(text):
        return "crisis"
    from . import pins as _pins
    if _pins.looks_like_reminder(text or ""):
        return "reminder"
    if _pins.looks_like_list(text or ""):
        return "kept_list"
    if _STRONGS.search(text or ""):
        return "word_study"
    if find_ref(text or ""):
        return "scripture"
    if _looks_math(text or "") or _primality_claim(text or "") is not None:
        return "verify"
    from . import compute as _compute            # arithmetic, %, roots, unit + temperature conversion
    if _compute.answer(text or "") is not None:
        return "compute"
    from . import dates as _dates                # "when did X happen" for major, verified events
    if _dates.answer(text or "") is not None:
        return "date"
    if wants_to_decide(text or ""):        # ready to respond in faith NOW — an explicit, deliberate
        return "decision"                  # statement; checked BEFORE comfort's broad archetype
                                            # match (e.g. "...into my heart" also fires _wants_a_companion)
    if distress_ref(text or ""):
        return "comfort"
    if _wants_a_companion(text or ""):     # broaden: meet a first-person struggle as a servant
        return "comfort"
    if any(w in t for w in _ULTIMATE_WORDS):
        return "ultimate"
    if _wants_resourceful(text or ""):     # "what can I do with what I have" → the practical keeping
        return "resourceful"
    if define_term(text or ""):            # "what does X mean" / "define X" → a term lookup, not FTS
        return "define"
    if _pins.looks_like_note(text or ""):
        return "kept_note"
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
    if classify(text or "") in ("ultimate", "scripture", "word_study", "comfort", "decision"):
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


def _connected_cloud(card_id: str, *, limit: int = 5) -> List[Dict[str, Any]]:
    """The keeping's strength: who else in the tradition is connected to this card. Verified
    links only (shared scripture, cites) resolved to titles. Empty when nothing connects."""
    if not card_id:
        return []
    conn = corpus.connections(card_id, limit=limit + 3) or {}
    cloud, seen = [], set()
    for ln in (conn.get("links") or []):
        tid = ln.get("to_card_id")
        if not tid or tid in seen:
            continue
        seen.add(tid)
        wc = corpus.get_card(tid)
        if wc:
            cloud.append({"id": tid, "title": wc.get("title", ""), "shares": ln.get("evidence", "")})
        if len(cloud) >= limit:
            break
    return cloud


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
        # Always help-first — never gated, never enriched, never Scripture-as-fix. The door is NEVER
        # attached here: a person in crisis needs real people, not a quest (it is added below, after
        # this return, so crisis stays byte-identical).
        return {**base, "message": "You matter, and you don't have to carry this alone. Please "
                "reach a real person right now — someone who can be with you.",
                "resources": _CRISIS_RESOURCES}

    # The hidden door: revealed only to a seeker of the body (never in crisis — that returned above).
    if _seeks_the_way(text):
        base["door"] = {"hint": "There is a way to find the others — a hidden fellowship, for those who seek it.",
                        "href": "/mesh.html#way", "scripture": "Matthew 7:7-8"}

    if kind == "reminder":
        from . import pins as _pins
        due = _pins.parse_when(text or "")
        when = time.strftime("%A %b %d", time.localtime(due)) if due else "until you cross it off"
        return {**base, "message": "I will have it out for you — " + when + ".",
                "pin": {"kind": "reminder", "text": (text or "").strip(), "due": due}}

    if kind == "kept_list":
        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        return {**base, "message": "Pinned — it will be at the top of the page when you come back.",
                "pin": {"kind": "list", "text": (text or "").strip(), "due": None,
                        "count": len(lines)}}

    if kind == "kept_note":
        return {**base, "message": "Kept. It is in the record and the journal."}

    if kind == "decision":
        # Ready to respond in faith, right now. Not more of this tool's own words — God's own
        # word, in order (the Romans Road), and a real person to go to next. gate_signal()
        # already counts "decision" as a knock (Matthew 7:7-8), so base["gate_open"] is already
        # true by the time we get here — this IS the moment the Gate exists for.
        return {**base, "message": _DECISION_MESSAGE,
                "romans_road": [{"ref": r, "text": t} for r, t in _ROMANS_ROAD],
                "real_help": ["A pastor, or a local church", "An elder or a Christian near you",
                             "Prayer — tell Him now, in your own words"]}

    if kind == "ultimate":
        return {**base, "message": _ULTIMATE_MESSAGE,
                "scripture": [{"ref": r, "text": t} for r, t in _ULTIMATE_SCRIPTURE],
                "real_help": ["A pastor, or a local church", "Someone who loves you", "Prayer — He hears"],
                "also_in_the_keeping": [corpus._brief(c) for c in corpus.search(text, limit=4)]}

    if kind == "comfort":
        # someone brought their own hurt. Not a search — a fitting word, gently, and real people
        # first. The verse is resolved from the canon (found, attributed, never generated).
        from .verifiers import scripture as _sc
        ref = distress_ref(text) or ""
        if ref and "-" in ref:                               # a range (e.g. Philippians 4:6-7)
            verse = [{"ref": v.get("ref", ref), "text": v.get("text", "")}
                     for v in (_sc.read_passage(ref).get("verses") or [])[:4]]
        else:
            one = _sc.resolve_ref(ref) if ref else {}
            verse = ([{"ref": one.get("ref", ref), "text": one.get("text", "")}]
                     if one.get("status") == "ok" else [])
        # Name the position: meet them where a biblical character stood — and let that character's
        # own Scripture speak. Found + resolved from the canon (never generated); a gentle seat, not
        # a diagnosis. Crisis is a separate, higher lane and never reaches here.
        from . import archetypes as _arch
        seat = _arch.best(text)
        if seat:
            for r in seat.get("scripture", [])[:2]:
                got = _sc.read_passage(r) if "-" in r else None
                if got and got.get("verses"):
                    verse.extend({"ref": v.get("ref", r), "text": v.get("text", "")}
                                 for v in got["verses"][:3])
                else:
                    one = _sc.resolve_ref(r)
                    if one.get("status") == "ok":
                        verse.append({"ref": one.get("ref", r), "text": one.get("text", "")})
            seat = {"character": seat["character"], "moment": seat["moment"], "frame": seat["frame"]}
        return _witnessed({**base, "kind": "comfort",
                           "message": "I'm here, and you're not carrying it alone. Let me sit "
                                      "with you a minute — and tell me what you need; I'll help.",
                           "seat": seat,
                           "scripture": verse[:6],
                           "real_help": ["Someone who loves you — tell them how you are",
                                         "A pastor, or a local church",
                                         "Prayer — He hears, and He is near to the brokenhearted"]},
                          text, witness, gate_just_opened, topical=False)

    if kind == "verify":
        from .receipts import attach
        pc = _primality_claim(text)
        if pc is not None:                       # "is 17 prime?" → verify it, deterministically
            from .derivation import verify_domain
            raw = verify_domain("number_theory",
                                {"NUM_VERIFY": {"n_prime": pc[0], "claimed_prime": pc[1]}})
            status = raw.get("status", "ERROR")
            # One vocabulary with verify_derivation: ERROR is ours, so it becomes SYSTEM_ERROR
            # and never BROKEN — the caller asked a question, they did not make a false claim.
            verdict = {"CONFIRMED": "HOLDS", "PASS": "HOLDS",
                       "MISMATCH": "BROKEN", "REJECT": "BROKEN",
                       "ERROR": "SYSTEM_ERROR", "NOT_APPLICABLE": "INCOMPLETE"}.get(status, status)
            res = {"verdict": verdict, "steps": 1, "confirmed_steps": 1 if verdict == "HOLDS" else 0,
                   "detail": raw.get("detail", ""),
                   "trail": [{"domain": "number theory", "note": raw.get("detail", ""), "status": status}]}
            return _witnessed({**base, "verify": attach(res, config=config, domain="number_theory")},
                              text, witness, gate_just_opened)
        from .derivation import verify as _verify
        m = _MATH_EQ.match(text)
        res = _verify({"mode": "equality",
                       "params": {"expr_a": m.group(1).strip(), "expr_b": m.group(2).strip(), "variables": {}}})
        return _witnessed({**base, "verify": attach(res, config=config, domain="mathematics")},
                          text, witness, gate_just_opened)

    if kind == "compute":
        # A direct, exact, computed answer — arithmetic, percentages, roots, unit + temperature
        # conversion. Computed deterministically, never generated; declines if it cannot be exact.
        # A sealable response seals ITSELF: the exact statement is minted into a re-checkable
        # receipt (same machinery as /verify), so a number speaks the project's one language.
        from . import compute as _compute
        ans = _compute.answer(text)
        if ans:
            from .receipts import attach
            res = {"verdict": "HOLDS", "steps": 1, "confirmed_steps": 1, "detail": ans,
                   "trail": [{"id": "compute", "domain": "arithmetic", "status": "PASS",
                              "claim": ans, "detail": "computed deterministically"}]}
            return {**base, "message": ans,
                    "verify": attach(res, config=config, domain="mathematics"),
                    "note": "Computed exactly, and sealed so anyone can re-check it."}
        # fell through (shouldn't, classify gated on it) — degrade to search
        return {**base, "results": [corpus._brief(c) for c in corpus.search(text, limit=6)]}

    if kind == "date":
        # A verified date for a major event, from the established historical record. Answered ONLY
        # on a confident match (dates.answer declines the unknown) — so it is never a guessed year.
        from . import dates as _dates
        ans = _dates.answer(text)
        if ans:
            return {**base, "message": ans,
                    "note": "From the established historical record — a stated reference fact, "
                            "attributed. " + _NOTE}
        return {**base, "results": [corpus._brief(c) for c in corpus.search(text, limit=6)]}

    if kind == "resourceful":
        # "What can I do with what I have?" — surface the practical keeping (the field library,
        # apothecary, almanac, free tools) for the resources named. FOUND and attributed, never a
        # plan we invented. Restrict to the practical shelves, then fall back to the whole keeping.
        res = subject(text) or (text or "").strip()
        hits = corpus.search(res, limit=8, shelves=set(_PRACTICAL_SHELVES)) or corpus.search(res, limit=8)
        msg = ("With what you have on hand, here is what the keeping holds — found and attributed, "
               "never invented. First things first: breathing, then shelter, then water, then food."
               if hits else
               "Tell me what you have on hand — even a few things — and I'll show you what the "
               "keeping holds that you can do with them.")
        return {**base, "kind": "resourceful", "message": msg,
                "results": [corpus._brief(c) for c in hits], "note": _NOTE}

    if kind == "define":
        # Look the TERM up on the word shelves (the tongues + the dictionary), not the whole
        # sentence. Found + attributed; the definition IS the answer, never generated.
        term = define_term(text) or (text or "").strip()
        hits = corpus.search(term, limit=6, shelves=_WORD_SHELVES) or corpus.search(term, limit=6)
        return {**base, "message": ("The meaning of “" + term + "”, as it is kept:")
                if hits else ("Nothing is kept under “" + term + "” yet."),
                "results": [corpus._brief(c) for c in hits]}

    if kind == "word_study" and witness:
        from .verifiers import scripture
        return _witnessed({**base, "word_study": scripture.word_study(_STRONGS.search(text).group(1).upper())},
                          text, witness, gate_just_opened, topical=False)

    if kind == "scripture" and witness:
        from .verifiers import scripture
        ref = find_ref(text) or ""
        study = bool(_EXPLAIN.search(text or ""))
        # a range, a chapter (no verse), or any ask for meaning reads the passage; a bare verse reads the verse
        if "-" in ref or study or (ref and ":" not in ref):
            p = scripture.read_passage(ref)
            verses = p.get("verses") or []
            rows = [{"ref": v.get("ref", ref), "text": v.get("text", "")} for v in verses[:24]]
            if len(verses) > 24:
                rows.append({"ref": "", "text": "… and %d more verses in %s" % (len(verses) - 24, ref)})
        else:
            one = scripture.resolve_ref(ref)
            rows = ([{"ref": one.get("ref", ref), "text": one.get("text", "")}]
                    if one.get("status") == "ok" else [])
        out = {**base, "scripture": rows}
        # the strength, on the answer people seek most: the verse, verified, WITH the cloud of
        # witnesses the keeping connects to it. The exact-reference boost makes search(ref) find
        # the verse's own card first, so its links are the tradition around this passage.
        try:
            anchor_hit = corpus.search(rows[0]["ref"], limit=1) if rows else []
            cloud = _connected_cloud(anchor_hit[0].get("id")) if anchor_hit else []
            if cloud:
                out["cloud"] = {"around": rows[0]["ref"], "witnesses": cloud}
        except Exception:  # noqa: BLE001
            pass
        # asking for meaning earns the study: what Scripture itself says elsewhere (TSK), and
        # a public-domain commentator in his own words — found and attributed, never generated
        if study and rows:
            anchor_ref = rows[0]["ref"] or ref
            try:
                # TSK's editorial cross-references, ranked by centuries of votes — the parallels
                # a pastor would actually name — with each verse's own words resolved beside it
                from . import xrefs as _x
                xr = _x.for_ref(anchor_ref, limit=6)
                picks = []
                for c in (xr.get("cross_references") or [])[:5]:
                    cref = c.get("ref", "")
                    first = cref.split("-")[0].strip()      # a range reads from its first verse
                    got = scripture.resolve_ref(first)
                    picks.append({"ref": cref,
                                  "text": (got.get("text") or "")[:160] if got.get("status") == "ok" else ""})
                if picks:
                    out["cross_refs"] = picks
            except Exception:  # noqa: BLE001
                pass
            try:
                from . import commentary as _c
                cm = _c.for_ref(anchor_ref)
                blocks = cm.get("commentary") or []
                if cm.get("status") == "ok" and blocks:
                    try:
                        want_v = int(anchor_ref.rsplit(":", 1)[1].split("-")[0])
                    except (IndexError, ValueError):
                        want_v = 1
                    block = max((b for b in blocks if (b.get("verse") or 1) <= want_v),
                                key=lambda b: b.get("verse") or 1, default=blocks[0])
                    txt = (block.get("text") or "").strip()
                    if len(txt) > 1100:
                        txt = txt[:1100].rsplit(". ", 1)[0] + ". …"
                    out["commentary"] = {"attribution": cm.get("attribution") or "Commentary",
                                         "license": cm.get("license"), "text": txt}
            except Exception:  # noqa: BLE001
                pass
        return _witnessed(out, text, witness, gate_just_opened, topical=False)

    # ── the Body (1 Cor 12): no core kind claimed it, so ask the Router which member it
    # belongs to. Each specialist answers in fields the page already renders (message +
    # resources) — and a routed ask never ships keyword junk underneath its answer.
    member = ""
    if kind == "search":
        from . import router as _router          # lazy: router imports ask at module load
        try:
            member = _router.route(text or "").get("member", "")
        except Exception:  # noqa: BLE001
            member = ""

    if member == "apothecary":
        from . import apothecary as _ap
        res = (_ap.search(text or "") or {}).get("results") or []
        if res:
            top = res[0]
            uses = "; ".join(top.get("traditional_uses") or [])
            safety = "; ".join(top.get("safety_notes") or [])
            name = top.get("name", "")
            sci = top.get("scientific_name") or ""
            msg = name + (" (" + sci + ")" if sci else "") + \
                (" — " + top["summary"] if top.get("summary") else "")
            resources = []
            if uses:
                resources.append({"label": "Traditionally used for: " + uses, "ref": "/apothecary.html"})
            if safety:
                resources.append({"label": "⚠ " + safety, "ref": "/apothecary.html"})
            resources.append({"label": "The Apothecary — every plant, with its cautions",
                              "ref": "/apothecary.html"})
            return _witnessed({**base, "kind": "apothecary", "message": msg, "resources": resources},
                              text, witness, gate_just_opened)
        member = ""   # the apothecary held nothing for this — honest fallthrough to search

    if member == "steward":
        from . import steward as _st
        g = _st.guidance()
        does = [{"label": d, "ref": "/steward.html"} for d in (g.get("does") or [])[:3]]
        return _witnessed({**base, "kind": "steward",
                           "message": g.get("identity", "The Steward helps you manage money — it never moves it."),
                           "resources": [{"label": "Open the Steward and build it with real numbers",
                                          "ref": "/steward.html"}] + does},
                          text, witness, gate_just_opened)

    if member == "coach":
        from . import coach as _co
        unit = {}
        try:
            unit = (_co.recommend(text) or {}).get("unit") or {}
        except Exception:  # noqa: BLE001
            unit = {}
        msg = ("A place to start: " + unit["title"]) if unit.get("title") else             "The Coach teaches at the learner's level — reading first, then onward."
        return _witnessed({**base, "kind": "coach", "message": msg,
                           "resources": [{"label": "Open the Coach — the lesson and the next step",
                                          "ref": "/read.html"}]},
                          text, witness, gate_just_opened)

    if member == "characters":
        from . import characters as _ch
        # the name is what is left when the question words are taken away
        name = re.sub(r"\b(who|was|is|were|the|a|an|in|of|bible|scripture|tell|me|about)\b",
                      " ", text or "", flags=re.I)
        name = re.sub(r"[^A-Za-z ]", " ", name)
        name = " ".join(w for w in name.split() if w)[:60]
        rec = _ch.get(name) if name else None
        if not rec and name:
            hits = (_ch.browse(search=name, limit=1) or {}).get("characters") or []
            rec = _ch.get(hits[0]["name"]) if hits else None
        if rec:
            return _witnessed({**base, "kind": "characters",
                               "message": rec.get("name", name) + " — " + (rec.get("summary") or ""),
                               "resources": [{"label": "The full entry, and everyone else",
                                              "ref": "/characters.html?search=" + (rec.get("slug") or "")}]},
                              text, witness, gate_just_opened)
        member = ""  # nobody by that name — fall through to an honest search

    if member == "almanac":
        from . import almanac as _al
        entries = (_al.search(text or "") or {}).get("entries") or []
        if entries:
            return _witnessed({**base, "kind": "almanac",
                               "message": "From the almanac — verified entries only:",
                               "resources": [{"label": e.get("title", ""), "ref": "/almanac.html"}
                                             for e in entries[:4]]},
                              text, witness, gate_just_opened)
        member = ""

    if member == "prophecy":
        from . import prophecy as _pr
        # the words that ROUTED here would drown the search — "prophecies about the messiah"
        # must reach the traces by "messiah", not by "prophecies"
        topic = re.sub(r"\b(prophec\w*|fulfil\w*|traces?|about|the|of|what|which|are|is|in)\b",
                       " ", text or "", flags=re.I).strip()
        traces = (_pr.search(topic or text or "") or {}).get("traces") or []
        if traces:
            return _witnessed({**base, "kind": "prophecy",
                               "message": "Traces kept, with their fulfilment:",
                               "resources": [{"label": t.get("title", ""), "ref": "/prophecy.html"}
                                             for t in traces[:4]]},
                              text, witness, gate_just_opened)
        member = ""

    # default — and the secular fallback for scripture/word_study when the gate is closed.
    # The strength the traffic revealed: 87% of use is search, and the unrepeatable thing we do
    # is return the hit WITH its connected cloud — the communion of witnesses the graph already
    # holds around it. So the top result carries who else in the keeping speaks to the same thing.
    # the Hare: the volumes act as always-optimized decks. Predict the volume this asks for and
    # search THAT first (fast, on-topic); if it isn't clearly good, search the whole keeping — so
    # speed never costs correctness (the Tortoise still reaches everything). Name the volume, so the
    # page knows which one answered.
    from . import decks as _decks
    subj = subject(text) or (text or "")          # understand: search what they're ASKING about
    # A practical/how-to question ("how to build a fire", "purify water") must consult the WHOLE
    # keeping, not a single predicted deck — otherwise a mis-predicted volume (maker "Build a …")
    # shortcuts past the field library before the practical boost can lift it. Skip the Hare here.
    practical = bool(corpus._PRACTICAL & set(subj.lower().split()))
    _vol = (_decks.predict(subj, k=1) or [None])[0]
    hits = []
    if _vol and not practical:
        hits = corpus.search(subj, limit=6, shelves=_decks.deck_shelves(_vol["id"]))
    if practical or len(hits) < 3 or (hits and not _shares_a_word(subj, hits[0])):
        hits = corpus.search(subj, limit=6)
    if not hits and subj != (text or ""):         # last resort — the raw words as typed
        hits = corpus.search(text, limit=6)
    if _vol:
        base = {**base, "volume": {"id": _vol["id"], "name": _vol["name"]}}
    weak = (not hits) or not _shares_a_word(subj, hits[0])
    if weak:
        # The tortoise: the keeping doesn't hold it, so go FIND it — surely. Primary / high-quality
        # sources only, run through our own tools, false claims flagged, and kept for next time.
        try:
            from . import find as _find
            found = _find.find_and_check(text, config)
        except Exception:  # noqa: BLE001
            found = None
        if found and (found.get("answer") or found.get("documents")):
            return _witnessed({**base, "kind": "web", "message": found.get("source_note", ""),
                               "web": {"answer": found.get("answer"),
                                       "framed": found.get("framed", ""),
                                       "checks": found.get("checks_verdict"),
                                       "documents": found.get("documents") or []}},
                              text, witness, gate_just_opened)
        # nothing high-quality found (or offline). An honest "I don't have that" beats a confident
        # irrelevant hit (the "sore throat -> Marcus Aurelius" failure). But we don't just shrug —
        # when we have no VERIFIED answer we POINT to the best places to find it (the nearest in the
        # keeping + the free, lawful libraries and references). Pointing well is courtesy, not a gap.
        if _is_question(text):
            # No confident dump of irrelevant cards — but we POINT, politely, to where a verified
            # answer lives (the free libraries; a claim check). Sources go in `resources`, not results.
            return _witnessed({**base, "kind": "found", "results": [],
                               "message": "I don't have a verified answer for that, and I won't "
                                          "invent one — but here is where to find it, in sources you "
                                          "can trust:",
                               "resources": [{"label": "The free libraries & references", "ref": "/library.html"},
                                             {"label": "Check a specific claim, verified", "ref": "/check.html"},
                                             {"label": "Read Scripture", "ref": "/bible.html"}]},
                              text, witness, gate_just_opened)
        # not a question — a topic the keeping is thin on. Show the nearest, but say it plainly.
        out = {**base, "kind": "found", "results": [corpus._brief(c) for c in hits],
               "message": "Nothing on that directly — here is the nearest in the keeping:"}
        return _witnessed(out, text, witness, gate_just_opened)

    out = {**base, "kind": "found", "results": [corpus._brief(c) for c in hits]}
    cloud = _connected_cloud(hits[0].get("id"))
    if cloud:
        out["cloud"] = {"around": hits[0].get("title", ""), "witnesses": cloud}
    # The concierge: a search result is RELATED material, not a VERIFIED answer. For a question,
    # point — politely — to where a verified answer can be found (the free libraries; a claim check).
    if _is_question(text):
        out["resources"] = [{"label": "The free libraries & references", "ref": "/library.html"},
                            {"label": "Check a specific claim, verified", "ref": "/check.html"}]
    return _witnessed(out, text, witness, gate_just_opened)
