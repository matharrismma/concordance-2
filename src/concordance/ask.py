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
from typing import Any, Dict, List

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
                 "unalive myself", "hang myself", "shoot myself", "goodbye cruel world",
                 # Past, perfect, and progressive forms of the ideation already listed above.
                 # Someone who has carried this for years rarely phrases it as a present-tense
                 # imperative — "i have wanted to die for 3 years" normalizes to "...wanted to die
                 # ..." and "want to die" never matches across the "-ed" in "wanted" (verified miss,
                 # 2026-08-05; it routed to an ordinary search). These are CONJUGATIONS of phrases
                 # this list already treats as crisis, not new territory, so they add no idiom the
                 # present tense didn't already accept (the deliberate asymmetry: an unnecessary
                 # helpline is a small cost, a missed person is not). No first-person or duration
                 # gate is added — an exclusion on the safety check is how a bypass gets built.
                 "wanted to die", "wanting to die", "wanted to end it", "ending it all",
                 "ending my life", "ending my own life",
                 "feel like ending it", "felt like ending it",
                 # Red team, 2026-08-06: an adversarial pass of 30 realistic phrasings missed all 30.
                 # These close the confirmed holes. The asymmetry stands (an unnecessary helpline is a
                 # small cost; a missed person is not), so this widens coverage and adds no exclusion.
                 # Attempt IN PROGRESS — the highest-cost miss (a person mid-act must not reach search):
                 "took a whole bottle", "took a bottle of pills", "swallowed a bottle",
                 "swallowed a bunch of pills", "took a bunch of pills", "took too many pills",
                 "took all my pills", "took all the pills", "overdosed", "slit my wrists",
                 "slitting my wrists", "cut my wrists", "cutting my wrists", "going to jump",
                 "about to jump", "ready to jump", "jump off a bridge", "jump off the bridge",
                 "gun to my head", "put a gun to", "end myself",
                 # The commonest idioms of ideation:
                 "wish i was dead", "wish i were dead", "wish i could die", "wish i would die",
                 "want to be dead", "dont want to be alive", "dont want to live anymore",
                 "dont want to exist", "want to disappear", "want to vanish",
                 "cant take it anymore", "cant take this anymore", "im a burden",
                 "burden to everyone", "burden to my family", "done with life",
                 "want it to be over", "want it all to be over", "nobody would miss me",
                 "no one would miss me", "better off without me here", "life isnt worth living",
                 "life is not worth living", "not worth living anymore", "tired of living",
                 "tired of being alive",
                 # Abbreviations and euphemisms (the youth/teen demographic). "kms"/"kys" are NOT
                 # in this substring list: as bare substrings they collide with real, common queries
                 # ("convert 5 kms to miles" — the unit_convert domain — "i ran 10 kms", "whiskys"),
                 # so they are matched only as the whole message instead (see _CRISIS_EXACT below).
                 "unalive", "unaliving", "sewerslide",
                 # Spanish — an explicit audience (the es_en curriculum). A caught crisis still
                 # surfaces findahelpline.com (international); localizing the response is a follow-up.
                 "quiero morir", "me quiero morir", "ya no quiero vivir", "quiero matarme",
                 "me quiero matar", "quiero acabar con mi vida", "acabar con mi vida",
                 "no quiero vivir", "no quiero seguir viviendo", "quitarme la vida",
                 "quiero desaparecer",
                 # Answer-path benchmark, 2026-08-26: a 25-cry graded set routed only 18/25 to help.
                 # These seven softer idioms of ideation missed — give-up-on-life, no-hope-left, the
                 # pain, ending things, want-it-all-to-stop, should-be-over. Same asymmetry as above
                 # (an unnecessary helpline is a small cost, a missed person is not); these are near-
                 # synonyms and conjugations of phrases already treated as crisis, and add no exclusion.
                 "give up on life", "giving up on life", "gave up on life", "given up on life",
                 "want it all to stop", "want everything to stop", "want the pain to stop",
                 "make the pain stop", "make it all stop", "just want it all to stop",
                 "cant take the pain", "cant take the pain anymore", "cant take this pain anymore",
                 "cant handle the pain anymore",
                 "cutting myself", "hurting myself", "harming myself",
                 "no hope left", "theres no hope left", "no hope left for me",
                 "life should be over", "my life should be over", "want my life to be over",
                 "wish my life was over", "wish my life were over",
                 "thinking about ending things", "thinking of ending things", "about ending things",
                 "want to end things", "ready to end things", "planning to end things",
                 # Adversarial load, 2026-08-27: a 90+ phrasing sweep across registers found the
                 # quieter idioms of hopelessness the blunt list missed — cant-do-life, no-way-out,
                 # never-get-better, tired-of-being-here, the-point-anymore, would-anyone-notice. Same
                 # asymmetry; these are near-synonyms of ideation already treated as crisis. These are
                 # QUERIES to the engine, where such phrasings are overwhelmingly a cry, not idiom.
                 "cant do life anymore", "do life anymore", "cant keep going", "cant keep doing this",
                 "need the pain to stop", "make my pain stop", "end my suffering", "end the suffering",
                 "hope i dont wake up", "hope i never wake up", "hope i dont wake up tomorrow",
                 "hope i dont wake up in the morning", "wish i didnt have to wake up",
                 "notice if i was gone", "notice if i were gone", "even notice if i was gone",
                 "world would be better without me", "world would be better off without me",
                 "everyone would be better without me",
                 "tired of being here", "so tired of being here",
                 "point of anything anymore", "whats the point anymore", "whats the point of living",
                 "dont see the point anymore", "dont see a point anymore", "dont see the point in living",
                 "never going to get better", "never gonna get better", "nothing will ever get better",
                 "things will never get better", "it will never get better", "itll never get better",
                 "thinking about ending it", "thinking of ending it", "way to end it",
                 "way to end my life", "see no way out", "no way out of this", "no way out but",
                 "why am i still here", "why am i even still here",
                 # bound to "still here" (still alive) — bare "why am i here" is a faith question the
                 # engine should meet with purpose, not a helpline; "still here" is the ideation tell.
                 "why im still here", "why im even still here", "why am i still alive",
                 "no future for me", "cant see a future for myself",
                 # Independent red-team, 2026-08-27: two blind adversarial passes (adult/veiled +
                 # youth/multilingual) beat the net 94/98 — proof a substring list catches what its
                 # author imagined, not what a real, diverse population types. These close the SAFELY-
                 # boundable holes (clear ideation, current online euphemism, non-English cries). The
                 # veiled/behavioral cluster with no reliable token (goodbye + giving-away, grief-
                 # longing, faith-"called home") is NOT force-fit here — it is the documented target of
                 # the semantic/intent backstop (docs/CRISIS_BACKSTOP.md), because forcing it into
                 # substrings would either miss or sweep ordinary estate-planning and grief.
                 "disappointed that i woke up", "disappointed i woke up", "disappointed i wake up",
                 "if i wasnt around", "if i wasnt here anymore", "everyone would breathe easier if i wasnt",
                 "feel like a burden", "i feel like a burden", "im just dead weight to",
                 "cant do another day", "cant face another day", "another day in this body",
                 "pain is never going to stop", "pain will never stop", "im done fighting",
                 "dont want to continue being alive", "want to stop existing", "i want to stop existing",
                 "dont want to be a person anymore", "being alive is too painful", "dont want to be here anymore",
                 "dont wanna be here", "dont wanna be here anymore", "id rather not wake up",
                 "sleep and never wake up", "nap and never wake up", "go to sleep and never wake up",
                 "would anyone even notice if i was gone", "would anyone notice if i was gone",
                 "would anyone care if i was gone", "if i wasnt here would anyone",
                 "ive lived long enough", "lived long enough", "no reason to keep going",
                 "wont be around much longer", "wont be here much longer", "not be around much longer",
                 "praying not to wake up", "pray i dont wake up", "been praying not to wake up",
                 "whats even the point", "whats the point of it all",
                 # online / gaming euphemism (current, evolving; the unambiguous ones):
                 "log off for good", "delete my existence", "uninstall myself", "uninstall my life",
                 "alt f4 my life", "un-exist", "unexist",
                 # non-English cries (highest-signal per language; English-primary engine, low collision):
                 "acabar con mi vida", "mejor muerto", "estaria mejor muerto", "no le veo sentido a la vida",
                 "no despertar nunca", "todos estarian mejor sin mi", "mejor sin mi", "quitar la vida",
                 "para que seguir viviendo", "cansado de vivir", "terminar con mi vida", "no quiero seguir aqui",
                 "ya no puedo mas", "ya no aguanto", "je veux en finir", "en finir", "ne veux plus me reveiller",
                 "nao quero mais viver", "queria sumir pra sempre", "sumir pra sempre",
                 "ayoko na mabuhay", "gusto ko nang mawala", "khong muon song nua", "muon bien mat",
                 "biddi amout", "bidi amout")

# Short self-harm abbreviations ("kms" = kill myself, "kys"). As substrings they collide with real,
# common queries ("5 kms to the store", the unit_convert domain, "whiskys"), so they count only as
# the entire normalized message — where the lone word "kms"/"kys" is the self-harm sense, not a
# distance. This is a targeted inclusion of an ambiguous token in its unambiguous form, NOT an
# exclusion carved into a crisis phrase: every full phrase in _CRISIS_WORDS still matches anywhere.
_CRISIS_EXACT = frozenset({"kms", "kys"})

# Requests to grade, rank, or label the user's OWN child are a child-protection matter however they
# route (checked in respond() before the general search path). Kept here as the cheap pre-filter so
# coach.py is imported only when a child is actually named. Leading space => word start after norm.
_CHILD_REFERENTS = (" my kid", " my child", " my son", " my daughter")

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


def _semantic_backstop(text: str) -> bool:
    """The deterministic semantic net UNDER the substring list — catches the veiled cries that share no
    keyword ("nothing keeping me here since he passed"). An absent or malformed artifact returns False
    (substring-only), never a crash: the backstop can widen the net but is never a single point of
    failure. It only ever ADDS a catch — is_crisis unions it in, so the net can grow but never shrink."""
    try:
        from . import crisis_semantic
        return crisis_semantic.flags(text)
    except Exception:  # noqa: BLE001 — the safety check must never crash instead of answering
        return False


def is_crisis(text: str) -> bool:
    """The one crisis test. Every surface calls this — a copied list is a list that drifts. Substring
    net first (fast, exact); then the semantic backstop for the veiled cries (only adds, never removes)."""
    t = normalize(text)
    if t in _CRISIS_EXACT or any(w in t for w in _CRISIS_WORDS):
        return True
    return _semantic_backstop(text)


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
# A how-to / instructional question seeks INSTRUCTION, not comfort — even when it carries a word
# that is elsewhere a cry ("how do I set a broken bone", "how do I treat a burn"). The procedural
# "I" in "how do I …" tripped the first-person guard and routed a first-aid emergency to comfort
# (measured 2026-08-12). Crisis still outranks everything and is checked first, always.
_HOWTO = re.compile(r"\bhow\s+(do|to|can|should|would|could|does)\b"
                    r"|\bwhat\s+(do|should|can)\s+i\s+do\b", re.I)


def distress_ref(text: str) -> str:
    """If someone brings their OWN hurt (first-person + a feeling word) and it is NOT a crisis,
    the fitting comfort verse — a canon reference to resolve. Else ''. Never fabricates. A how-to
    question is never a cry: 'how do I set a broken bone' is first aid, not a broken heart."""
    if is_crisis(text) or not _FIRST_PERSON.search(text or "") or _HOWTO.search(text or ""):
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
    r"^\s*(is|are|was|were|do|does|did|can|could|how|why|when|where|which|will|should|has|have"
    r"|what|who|whom|whose)\b",   # "what"/"who" were missing — the two commonest question words, so a
    re.I)                          # true miss on "what is X" / "who was X" got the weaker non-question path


def _content_tokens(s: str) -> set:
    return {w for w in _WORD3.findall((s or "").lower()) if w not in _STOP}


def _is_question(text: str) -> bool:
    t = (text or "").strip()
    return t.endswith("?") or bool(_QUESTION.match(t))


def _shares_a_word(text: str, card: Dict[str, Any]) -> bool:
    """Does the keeping's hit actually share a DISTINCTIVE word with what was asked? A match on a
    common word ('year', 'day') is not enough — 'what year did the Titanic sink' must be carried by
    a hit that names the Titanic, not merely one that says 'year'. So when the question has specific
    words (≥5 letters), require one of THOSE to match; only fall back to any-word when it has none.

    AND THE SUBJECT OUTRANKS EVERY OTHER DISTINCTIVE WORD. "Tell me about the Wesleyan Church" has
    two distinctive words, and the original guard accepted a hit on either — so the deck-scoped
    path returned six confession cards about the church in general and this guard waved them
    through on "church" while "wesleyan" appeared in none of them. The very question that opened
    this whole arc ("just random cards... right now its a dud") was still a dud two fixes later,
    because a scoped search cannot see its own blindness: inside a deck with no "wesleyan"
    anywhere, the local partition falls back to the next word. Only the global corpus knows what
    the asking was ABOUT, so when it can name the subject, the hit must carry the SUBJECT — and a
    miss here sends the router back out to the unscoped search, where the partition holds.
    """
    q = _content_tokens(text)
    if not q:
        return True                                   # nothing specific asked — don't second-guess
    hay = _content_tokens((card.get("title") or "") + " " + (card.get("body") or ""))
    try:
        subject = corpus.subject_of(text)
    except Exception:  # noqa: BLE001 — no corpus loaded is not a reason to reject a hit
        subject = None
    if subject:
        # The FAMILY, both numbers — and matched against the family of what was asked, because
        # the subject seat may hold the present form ("baptist") while the question said the
        # plural. A hit about either number carries the question.
        fam = corpus.Corpus.subject_family(subject)
        if fam & {v for w in q for v in corpus.Corpus.subject_family(w)}:
            return bool(fam & hay)
    distinctive = {w for w in q if len(w) >= 5}
    return bool(distinctive & hay) if distinctive else bool(q & hay)


def _prefer_full_coverage(hits: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """Lead with the hit that carries the WHOLE multi-word subject, not a partial match.

    A person's name is a UNIT, but the ranker reduces the asking to its single rarest token — and for
    a famous name the identifying surname is COMMON in the keeping (many of his own books), so the
    rarest token is some other part of the name. "Charles Haddon Spurgeon" reduced to the middle name
    "haddon" and led with a Charles Haddon CHAMBERS comedy over Spurgeon's own works; "Athanasius of
    Alexandria" dropped to "athanasius" (measured live 2026-08-31 — Matt: "if you ask for a name it
    breaks it down to just the last name or a single word"). When the asking carries 2+ distinctive
    words and some hit covers strictly MORE of them than the current lead, move that fuller hit to the
    front — a stable promotion (nothing else reorders), and it only ever fires to fix a partial lead.
    """
    want = {w for w in _content_tokens(text) if len(w) >= 5}
    if len(want) < 2 or len(hits) < 2:
        return hits

    def _cov(c: Dict[str, Any]) -> int:
        return len(want & _content_tokens((c.get("title") or "") + " " + (c.get("body") or "")))

    best = max(range(len(hits)), key=lambda i: _cov(hits[i]))
    if best and _cov(hits[best]) > _cov(hits[0]):
        hits = [hits[best]] + hits[:best] + hits[best + 1:]
    return hits


def _prefer_connected(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compose the LEXICAL rank with the CONNECTION map — two signals, both true (Matt: "2 things can
    be true at once"). Among the word-matches, lift the neighbourhood HUB — a card linked by a
    SUBSTANTIVE edge (a shared scripture, a citation) to OTHER on-topic hits — over an ISLAND that holds
    the word but connects to nothing about it (a `card_src_pron_messiah`-shaped stub). It NEVER replaces
    the words and never deletes a hit; it only lifts a hub over an island lead.

    Honest by construction where the graph is THIN: a card whose only edge is a generic shelf-membership
    (`member_of` a `card_spine_*`) scores 0, so a practical query — whose cards carry no real edges yet —
    is left exactly as the words ranked it. The signal helps where the map is dense (Scripture's
    cross-references) and is inert, never harmful, where it is sparse. Clearing the practical frontier
    needs the substance/region signals, not this one — both are true, and both are needed.

    Connector cards are the map's EDGES, never its destinations. A `card_c_*` / shelf-"connections" card
    (e.g. "Amazing Grace ↔ Ephesians") exists only to link two content cards, so it is BY NATURE the most
    linked card in any pool — count it and it would always win, burying the very content it points to (the
    parasitic-connector failure). So a connector never counts as a destination and is never promoted; it
    stays where the words put it, to DECORATE, not to lead."""
    if len(hits) < 3:
        return hits

    def _connector(c: Dict[str, Any]) -> bool:
        return str(c.get("id") or "").startswith("card_c_") or c.get("shelf") == "connections"

    # Evidence = substantive links into the pool of CONTENT cards (connectors and shelf spines excluded,
    # so the map's edges neither score nor get scored toward).
    content_ids = {c.get("id") for c in hits if not _connector(c)}

    def _evidence(c: Dict[str, Any]) -> int:
        n = 0
        for e in (c.get("connections") or []):
            tid = e.get("to_card_id")
            if tid and tid != c.get("id") and tid in content_ids and not str(tid).startswith("card_spine_"):
                n += 1
        return n

    cand = [i for i in range(len(hits)) if not _connector(hits[i])]   # a connector may never be promoted
    if not cand:
        return hits
    best = max(cand, key=lambda i: _evidence(hits[i]))
    if best and _evidence(hits[best]) > 0 and _evidence(hits[0]) == 0 and not _connector(hits[0]):
        hits = [hits[best]] + hits[:best] + hits[best + 1:]
    return hits


def _shape_found_hits(hits: List[Dict[str, Any]], text: str, practical: bool) -> List[Dict[str, Any]]:
    """The ONE place a found answer's hits are shaped before the lead is chosen — the discernment the
    found path used to scatter across the served block (this is the P2 consolidation: one function, so
    both the found path AND discern can share it). In order:
      1. PRACTICAL JUNK — for a how-to, drop lookup/fiction word-matches (a pill powder, a novel); an
         empty result here is the honest "I don't have a real how-to yet" signal, returned as [].
      2. PRONUNCIATION KEY — never leads a substantive ask ("who composed the Messiah" → a phonetic
         key for "messiah"); demoted behind any real hit unless the ask is about how a word is SAID.
      3. WHOLE NAME — the hit carrying the most of a multi-word subject leads over a partial fragment.
      4. CONNECTION — among the word-matches, a card the CONNECTION MAP embeds in the subject's
         neighbourhood (a substantive link to another on-topic hit) leads over an island stub that
         merely holds the word. Composes with the lexical rank, never replaces it; inert where the
         graph is thin (so a practical query is left exactly as the words ranked it).
    Behavior-preserving through step 3; step 4 only lifts a connected hub over an island lead."""
    if practical:
        clean = [c for c in hits if not _is_practical_junk(c)]
        if not clean:
            return []                     # a how-to with only word-matches — the caller answers honestly
        hits = clean
    if not re.search(r"pronounc|how (?:do you|to|do i) say\b", text or "", re.I):
        pron = [c for c in hits if str(c.get("id") or "").startswith("card_src_pron_")]
        if pron and len(pron) < len(hits):
            hits = [c for c in hits if not str(c.get("id") or "").startswith("card_src_pron_")] + pron
    hits = _prefer_full_coverage(hits, text)
    return _prefer_connected(hits)


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
         "far", "away", "many", "much", "really", "actually", "exactly", "some", "any",
         # authorship / attribution scaffolding — "who WROTE Pilgrims Progress" is about the BOOK, not
         # the verb. Left in, the verb became the subject and led with a pronunciation stub for "wrote"
         # (measured live 2026-08-31). The subject of "who <verb> X" is X.
         "wrote", "write", "writes", "written", "said", "painted", "invented", "discovered",
         "composed", "founded", "authored", "coined", "directed", "produced", "sculpted", "built"}


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
_PRACTICAL_SHELVES = frozenset({
    "survival", "apothecary", "almanac", "access", "fieldkit", "playbook",
    "medicine", "nutrition", "drugs", "foods", "recipes", "curriculum", "activities",
    "agriculture", "energy", "communications", "first_aid", "navigation", "sanitation",
    "water", "practical", "timekeeping",
})
# The academic Theory-Assay catalog answers "what is the law of X" well, but on a HOW-TO question it
# only shares a word and steals the lead (measured: "start a fire" -> Hess's law thermochemistry).
# For practical intents it is dropped from the general pool so a field card always leads.
_ACADEMIC_DEMOTE = frozenset({"theories"})
# Consumer PRODUCTS the FDA registers as "drugs" (hand sanitizers, cosmetics — ~1,000 of the openFDA
# cards): legitimately public, but noise at the top of a how-to it merely shares a word with
# ("keep warm without power" -> "Warm Vanilla Hand Sanitizer"). Demoted, never withheld — a search
# for the product itself still finds it.
_PRODUCT_NOISE = re.compile(          # PREFIX match at a word start (no trailing \b — 'sanitiz'
    r"\b(sanitiz|wipes?|shampoo|lotion|body\s*wash|sunscreen|foaming|scented|deodorant|toothpaste|"  # must
    r"mouthwash|lip\s*balm|moisturiz|cleanser|conditioner|antiperspirant|cosmetic|fragrance|perfume)",  # catch
    re.I)                             # 'sanitizer', 'moisturizing', …)


def _is_product_noise(card: Dict[str, Any]) -> bool:
    return (card.get("shelf") in ("medicine", "drugs")
            and bool(_PRODUCT_NOISE.search(card.get("title") or "")))


# For a HOW-TO, the answer is INSTRUCTIONAL — the field library, the trades, the recipes. The big
# auto-generated reference databases (the drug directory, the USDA food table) are in the practical
# set so they can be SEARCHED, but a single DB row must not LEAD a how-to it merely shares a word
# with ("set a broken bone" -> a T-Bone Steak row; "keep warm" -> a hand sanitizer). They stay one
# tier below a real instructional match.
_FIELD_INSTRUCTIONAL = frozenset({
    "survival", "first_aid", "water", "sanitation", "energy", "navigation", "communications",
    "agriculture", "practical", "fieldkit", "playbook", "apothecary", "almanac", "access",
    "curriculum", "recipes",
})

# Reference-LOOKUP shelves that are never a how-to answer, plus obvious fiction. A dictionary
# definition ("chicken cacciatore"), a drug-database row ("Chicken Powder — HUMAN OTC DRUG"), a
# pronunciation key, a novel ("Love Among the Chickens") merely share a word with a practical
# question — measured live 2026-08-30: "how do i keep chickens" returned a children's story, a
# Wodehouse comedy, and three pill powders. Dropped from a PRACTICAL answer so a homestead question
# can never be answered with a recipe, a novel, or a pill. (Named explicitly, not _FIELD_INSTRUCTIONAL's
# inverse, so legitimate off-shelf cards are not swept out with the junk.)
_PRACTICAL_JUNK_SHELVES = frozenset({"dictionary", "lexicon", "pronunciation", "drug", "drugs",
                                     "thesaurus", "definition", "definitions", "glossary"})


def _is_practical_junk(card: Dict[str, Any]) -> bool:
    if (card.get("shelf") or "").lower() in _PRACTICAL_JUNK_SHELVES:
        return True
    if _is_product_noise(card):              # cosmetic/sanitizer DB rows on the medicine/drugs shelf
        return True
    # openFDA drug/supplement REGISTRATION rows (card_sources.py mints them `card_src_drug_*`) sit on
    # the medicine shelf but are product listings, not instruction — "Chicken Powder, Tongkat Ali: a
    # HUMAN OTC DRUG" for "how do i keep chickens". The shelf itself is legitimate (real first-aid /
    # apothecary cards live there), so key off the id prefix, not the shelf.
    if str(card.get("id") or "").startswith("card_src_drug_"):
        return True
    meta = (" ".join(card.get("bands") or []) + " " + str(card.get("subject") or "")
            + " " + str(card.get("kind") or "")).lower()
    return "fiction" in meta                 # a novel is not a how-to


_RESOURCEFUL = re.compile(
    r"(what (?:can|could|should) i (?:do|make|build|use|create|cook|fix|craft)\b.*\b(?:with|from|out of)\b"
    r"|all i (?:have|got)\b|i only have\b|i just have\b|i've only got\b|with (?:only|just)\b)", re.I)
# A CONSTRUCTION how-to — "make lye soap from wood ash", "build a water filter with sand" — is not the
# constrained "what can I do with what I HAVE" question above; it is a plain how-to that names its
# materials. It used to be swallowed by _RESOURCEFUL and met with the weaker practical-shelf search
# (no lead, no tortoise — measured 2026-08-14: five such queries returned an empty lead). Route it
# instead through the full FOUND pipeline (rank + tortoise) by raising the `practical` flag on it.
_MAKE_FROM = re.compile(
    r"\b(make|build|create|construct|assemble|improvise|fix|repair|cook|craft|forge|fashion|sew|weld|"
    r"brew|distill|smelt|tan|render)\b.+\b(with|from|out of|using)\b", re.I)


# Generic action verbs / filler carried by a how-to but not its SUBJECT — dropped before the
# title-overlap tiebreak so relevance keys on the real noun ("fire", "bread", "meat"), not the verb.
_GENERIC_Q_WORDS = frozenset({
    "make", "made", "making", "build", "building", "start", "starting", "create", "get", "getting",
    "use", "using", "do", "does", "find", "finding", "keep", "keeping", "put", "set", "fix", "fixing",
    "cook", "cooking", "grow", "growing", "need", "want", "help", "way", "ways", "best", "good",
    "without", "have", "using", "your"})


def _practical_pool(query: str) -> List[Dict[str, Any]]:
    """Search the INSTRUCTIONAL field shelves DIRECTLY first — so a matching field card is always in
    the pool even when the auto-generated DB rows (a T-Bone Steak, a hand sanitizer) outrank it
    globally on a shared word. Then the broader practical set, then the whole keeping. Deduped,
    search-order kept; _practical_rank decides the lead."""
    got = (corpus.search(query, limit=8, shelves=set(_FIELD_INSTRUCTIONAL))
           + corpus.search(query, limit=6, shelves=set(_PRACTICAL_SHELVES))
           + corpus.search(query, limit=10))
    seen, out = set(), []
    for c in got:
        if c.get("id") and c["id"] not in seen:
            seen.add(c["id"]); out.append(c)
    return out


def _practical_rank(query: str, pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank so the LEAD is always the best REAL match. Tiers: (0) an INSTRUCTIONAL field card that
    shares a word — the how-to answer; (1) any card that shares a word (incl. the reference
    databases); (2) a practical card; (3) the rest; (4) the academic catalog and product noise LAST —
    present, never leading. WITHIN a tier, the card whose TITLE names more of the subject leads: a
    card ABOUT the thing beats one that merely mentions it in its body (measured 2026-08-14: "start a
    fire" led with a knots card that says 'fire' once; "preserve meat" with 'Strawberry Preserves').
    Stable sort preserves the corpus's search relevance to break a title-overlap tie. Generic action
    verbs are dropped from the subject words first — else "start a fire" scores a 'Meshtastic
    quick-START' node on the shared, meaningless 'start'."""
    qt = _content_tokens(query) - _GENERIC_Q_WORDS

    def _tier(c: Dict[str, Any]) -> int:
        sh, shares = c.get("shelf"), _shares_a_word(query, c)
        if sh in _ACADEMIC_DEMOTE or _is_product_noise(c):
            return 4
        if shares and sh in _FIELD_INSTRUCTIONAL:
            return 0
        if shares:
            return 1
        return 2 if sh in _PRACTICAL_SHELVES else 3

    def _title_overlap(c: Dict[str, Any]) -> int:
        return len(qt & _content_tokens(c.get("title") or ""))

    return sorted(pool, key=lambda c: (_tier(c), -_title_overlap(c)))[:6]


def _stem(w: str) -> str:
    """A crude, dependency-free stem — strip the common inflections so 'burn'/'burns'/'burning' and
    'preserve'/'preserves'/'preserving' collapse to one form. Not linguistics; just enough to compare
    a query's subject word to a card's title word without an exact-token brittleness that would treat
    'burn' and 'burns' as different (and wrongly fire the tortoise past a perfect 'Burns and scalds')."""
    w = (w or "").lower()
    for suf in ("ing", "edly", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[:-len(suf)]
            break
    if w.endswith("e") and len(w) >= 4:
        w = w[:-1]
    return w


def _title_names_subject(query: str, card: Dict[str, Any]) -> bool:
    """Does the card's TITLE actually name the subject asked about (stem-aware)? A card whose title
    carries NONE of the subject words merely mentions the thing in passing ("start a fire" -> a knots
    card) — that is a masked GAP, not the answer. True when there is no real subject word to test
    (all generic), so we never force the tortoise on a bare/odd query."""
    subj = {_stem(w) for w in (_content_tokens(query) - _GENERIC_Q_WORDS)}
    if not subj:
        return True
    title = {_stem(w) for w in _content_tokens(card.get("title") or "")}
    return bool(subj & title)


def _pulled_lead_names_subject(query: str, card: Dict[str, Any]) -> bool:
    """A span the tortoise pulled (or kept from an earlier pull) may LEAD only if its TITLE names the
    subject the USER asked. craft.rank cuts a span wherever it shares ONE distinctive stem, so a
    tangential source can card (a waste-water treatise on 'milk', a carpentry manual on the wrong sense
    of 'wood'); the TITLE — not the body, which is exactly what carries the shared word — is the honest
    signal the span is ABOUT what was asked. Reused by BOTH the fresh-pull lead and the already-kept
    short-circuit, so a mis-selection can neither lead on the call nor be replayed as "already found it".

    Checked against the USER's query, NEVER the card's own `subject`. That field is what RETRIEVAL
    decided the source was about, and the span's title is minted to name that very subject — so trusting
    it is circular and rubber-stamps the mis-selection we are catching. Live 2026-09-01: 'lye soap from
    wood ash' matched the canon's 'carpentry' entry through the shared word 'wood', so the spans were cut
    FOR 'carpentry' and titled "CARPENTRY AND JOINERY"; a subject-vs-title check passed them, confident
    and wrong. A canon source whose spans name a synonym the crude stemmer can't bridge ('beekeeping' for
    the asked 'honeybees') is turned into an honest GAP instead — the safe direction this whole path is
    built on (Matt: an honest "I don't have that" beats a confident irrelevant hit). A gap stays a gap."""
    return _title_names_subject(query, card)


# THE OFF-DOMAIN SHIFT. A distributional topic model was proven unable to tell a how-to from a book
# merely ABOUT the subject — it conflates topic with intent ("hog cholera" sits in the same hog-cluster
# as "raise hogs") and penalizes synonyms ("chickens" vs "poultry"); so a threshold gate on it both
# false-gaps real matches and misses the mismatch. The intent shift is caught DETERMINISTICALLY here
# instead. A practical ask ("raise hogs", "keep bees") is answered wrongly when the best card names the
# subject yet its TITLE has shifted to a DIFFERENT frame the asker never entered — disease ("hog
# cholera"), the study of the thing ("the anatomy of the honey bee"), a reference work. Each domain
# lists the TITLE markers that signal the shift AND the ASK words that mean the asker is ALREADY in that
# domain, so a health question answered by a disease book is NOT a shift. Unambiguous + conservative by
# design: it only ever turns a served answer into a GAP (a slower, surer pull that grows the keeping),
# never a wrong answer, and — unlike a tighter noun match — it never rejects a related FORM.
_OFF_DOMAINS = {
    "health": (
        frozenset({"cholera", "disease", "diseases", "sickness", "pathology", "veterinary", "epidemic",
                   "infection", "plague", "ailment", "ailments", "parasite", "parasites"}),
        frozenset({"disease", "diseases", "sick", "sickness", "ill", "illness", "treat", "treating",
                   "cure", "curing", "remedy", "remedies", "symptom", "symptoms", "heal", "ailment",
                   "health", "medicine", "medical", "veterinary", "pathology", "parasite"})),
    "science": (
        frozenset({"anatomy", "physiology", "microbiology", "embryology", "taxonomy", "morphology"}),
        frozenset({"anatomy", "physiology", "biology", "science", "scientific", "microbiology",
                   "structure"})),
    "reference": (
        frozenset({"biography", "dictionary", "encyclopedia", "catalogue", "catalog"}),
        frozenset({"history", "biography", "dictionary", "who", "when", "catalogue", "catalog"})),
}


def _off_domain_shift(query: str, card: Dict[str, Any]) -> Optional[str]:
    """The card's TITLE has shifted to a frame the ask never entered — the domain, or None. Deterministic,
    no model; only a genuine cross-domain shift trips it (see `_OFF_DOMAINS`). "natural history" is
    matched as a phrase because neither word alone is a reference marker."""
    q = _content_tokens(query)
    tw = _content_tokens(card.get("title") or "")
    for dom, (markers, ask_words) in _OFF_DOMAINS.items():
        if (markers & tw) and not (ask_words & q):
            return dom
    if "natural history" in (card.get("title") or "").lower() and not ({"history", "natural"} & q):
        return "reference"
    return None


def _is_kept_tortoise_source(query: str, card: Dict[str, Any]) -> bool:
    """A public-domain passage THE TORTOISE ITSELF went out and cut FOR this very subject on an
    earlier ask, and kept. The surest thing we can hand a how-to gap on the SECOND asking: instead
    of fetching the same Foxfire manual all over again (~30–90s), lead with the passages already in
    the keeping — "search once, keep it".

    Recognised by the `tortoise` tag `expand.pull_and_card` stamps (so the millions of BULK source
    excerpts, which share the same shape, never short-circuit a real gap), AND by the subject the
    card was crafted for sharing a stemmed word with what is now being asked."""
    if not (card.get("extra") or {}).get("tortoise"):
        return False
    q = {_stem(w) for w in (_content_tokens(query) - _GENERIC_Q_WORDS)}
    if not q:
        return False
    csubj = {_stem(w) for w in _content_tokens(card.get("subject") or "")}
    return bool(q & csubj)


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
    # THE PATH (2026-08-12, the Lighthouse Model Spec: "the output is a PATH, never an answer").
    # Above the cards, a discerned ONE next step + a fitting anchor — composed from what was found,
    # nothing generated. Attached on BOTH surfaces (discernment is not gated), for the retrieval kinds
    # only; the branches that are already a single answer (a proof, a sum, a comparison, crisis) keep
    # their own shape. A failure here never costs the answer.
    if r.get("kind") not in ("verify", "compute", "comparison", "checked", "crisis"):
        try:
            from . import path as _path
            r["path"] = _path.compose(text, kind=r.get("kind", ""), subject=text,
                                      lead=r.get("lead"), resources=r.get("resources"),
                                      scripture=(r.get("scripture") or r.get("romans_road")),
                                      deck=r.get("volume"))
        except Exception:  # noqa: BLE001
            pass
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


def _coach_refusal(base: Dict[str, Any], guard: Dict[str, Any], text: str,
                   witness: bool, gate_just_opened: bool) -> Dict[str, Any]:
    """Render the child-protection refusal as a coach turn: Coach teaches; it never grades or
    labels a person. Shared by the early (a child is named) and in-context (Router→coach) checks."""
    return _witnessed({**base, "kind": "coach", "message": guard["message"],
                       "resources": [{"label": p, "ref": None} for p in guard.get("point_to", [])]
                       + [{"label": guard.get("do_instead", "Ask for the next lesson"), "ref": "/read.html"}]},
                      text, witness, gate_just_opened)


def _lead_excerpt(body: str, n: int = 620) -> str:
    """A generous, sentence-trimmed excerpt of a card's OWN body — enough to be the answer, not a
    180-char tease. The librarian hands you the page, not the spine label."""
    b = " ".join((body or "").split())
    if len(b) <= n:
        return b
    cut = b[:n]
    dot = cut.rfind(". ")
    return cut[:dot + 1] if dot > n * 0.55 else cut.rstrip() + "…"


def _lead_card(card: Dict[str, Any]) -> Dict[str, Any]:
    """The single best hit, shaped to LEAD: title, a full excerpt of its own words, and its source
    (the provenance IS the proof for a found card). Nothing generated — this is the card's content."""
    src = card.get("source") or {}
    return {"id": card.get("id"), "title": card.get("title"), "shelf": card.get("shelf"),
            "excerpt": _lead_excerpt(card.get("body") or ""),
            "source": {"label": src.get("label", ""), "url": src.get("url", ""),
                       "authority_tier": src.get("authority_tier", "")}}


# The librarian's line for a plain found answer: warm, and honest about what it is (kept + cited,
# never composed). It sets up the ONE full card that follows — not a wall of equal snippets.
_FOUND_LEAD = "Here's the clearest thing the keeping holds on this — in its own words, with its source:"


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

    # SAFETY (red team 2026-08-06): a request to grade, rank, or label the user's OWN child is a
    # child-protection matter however it would otherwise route. "is my kid behind for his age"
    # carries no teaching keyword, so the Router never sends it to Coach and the in-coach guardrail
    # below never runs — it fell through to a generic search. Enforce it here for any text that
    # names a child. Scoped to a named child so generic phrasings ("what grade level is this book",
    # "how do I diagnose a car") are untouched. Crisis already returned above and still outranks this.
    if any(p in " " + normalize(text) for p in _CHILD_REFERENTS):
        from . import coach as _coach_early
        _cg = _coach_early.coach_guardrail(text)
        if _cg is not None:
            return _coach_refusal(base, _cg, text, witness, gate_just_opened)

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
        # The storyboard beneath the seat (Matt, 2026-07-28): the movement this person may be
        # standing in, and who stood there before them — Israel between deliverance and
        # inheritance, Hannah in the delay. FRAMING always attached: a reference point, never an
        # identity. Crisis never reaches this branch; the higher lane routed it already.
        storyboard = None
        try:
            from . import narratives as _narr
            storyboard = _narr.match(text)
        except Exception:  # noqa: BLE001 — comfort must not break if the boards cannot load
            storyboard = None
        if storyboard:
            base = {**base, "storyboard": storyboard}
        # Never kindness with no word: when no seat matched (so no character's verses came), the
        # two anchors that fit every ache still come — found and resolved, like everything else.
        # (The seeker probe caught comfort answers carrying ZERO scripture, 2026-07-28.)
        if not verse:
            for r in ("Psalm 34:18", "Matthew 11:28-29"):
                one = _sc.read_passage(r)
                if one.get("status") == "ok":
                    verse.extend({"ref": v.get("ref", r), "text": v.get("text", "")}
                                 for v in (one.get("verses") or [])[:2])
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
        # plan we invented. Ranked like a how-to (instructional field cards lead; drug/food-DB rows and
        # product noise last), handed over with a LEAD card + a discerned PATH via _witnessed — the old
        # shape returned a bare results list with no lead and no path (measured empty 2026-08-14).
        res = subject(text) or (text or "").strip()
        hits = _practical_rank(res, _practical_pool(res))
        hits = [c for c in hits if not _is_practical_junk(c)]   # no drug/dictionary/fiction for "what can I do with X"
        # LEAD only with an INSTRUCTIONAL field card — never a bare reference-DB row that merely shares
        # a word (measured 2026-08-14: "what can I do with a tarp" led with a sailboat physical-activity
        # MET row). When the nearest is only a DB row, be honest and ask for more rather than mislead.
        led = bool(hits) and _shares_a_word(res, hits[0]) and hits[0].get("shelf") in _FIELD_INSTRUCTIONAL
        msg = ("With what you have on hand, here is what the keeping holds — found and attributed, "
               "never invented. First things first: breathing, then shelter, then water, then food."
               if led else
               "Tell me what you have on hand — even a few things — and I'll show you what the "
               "keeping holds that you can do with them.")
        out = {**base, "kind": "resourceful", "message": msg,
               "results": [corpus._brief(c) for c in hits], "note": _NOTE}
        if led:
            out["lead"] = _lead_card(hits[0])
        return _witnessed(out, text, witness, gate_just_opened)

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

    # ── The Candidate Engine, invisible (task #136, 2026-08-05): before we fall to keyword
    # search, if the words carried checkable claims, NARROW them — commit the set, verify each
    # across the domains, and show what held up, what did not, and what we could not judge
    # (held, never guessed). The honest answer includes its own rejects. Crisis returned at the
    # TOP of respond(); every specific kind returned above; this is the general path only.
    # Additive and safe: no checkable claim -> from_prose returns None -> everything below runs
    # exactly as before. The narrowing must never break the answer, so it is fully guarded.
    try:
        from . import candidates as _cand
        _cset = _cand.from_prose(text, config=config)
    except Exception:  # noqa: BLE001 — narrowing is a bonus; the answer path must not depend on it
        _cset = None
    if _cset is not None:
        try:
            _cand.receipt(_cset, config=config)   # seal the WHOLE narrowing, losers included
        except Exception:  # noqa: BLE001
            pass
        return _witnessed({**base, "kind": "checked",
                           "audit": _cand.as_checked(_cset),
                           "message": _cand.checked_message(_cset),
                           "results": [corpus._brief(c) for c in corpus.search(text, limit=4)]},
                          text, witness, gate_just_opened, topical=False)

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
        # SAFETY (red team 2026-08-06): a request to grade/rank/label a child is refused earlier in
        # respond() (the _CHILD_REFERENTS check), which catches it however it routes — including
        # "is my kid behind for his age", which carries no teaching keyword and never reached here.
        # It is deliberately NOT re-checked here on the generic judge patterns alone ("grade level",
        # "reading level"): with no child named, "what grade level is this book" is a legitimate
        # readability question, and the refusal message speaks of "a child" — firing it on a book
        # would be a discernment failure (refuse abuse, not use).
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
    # A how-to question IS a practical intent even when its words aren't in the practical set
    # ("keep warm without power" has none) — the framing itself signals it. So the how-to lane
    # (which prefers field cards and demotes theories + product noise) covers it too.
    practical = (bool(corpus._PRACTICAL & set(subj.lower().split()))
                 or bool(_HOWTO.search(text or "")) or bool(_MAKE_FROM.search(text or "")))
    # THE GREAT QUESTIONS OUTRANK THE CARD SEARCH (Matt, 2026-07-28: "we are after sinners not
    # saints"). "Is god even real" matches thousands of cards by keyword — and a card list is the
    # WRONG answer to a person asking their biggest question. The probe caught nine of twelve
    # seeker questions routed to keyword results; the person the mission is aimed at asked, and
    # the site handed them a filing cabinet. Curated plain-language answers, honest about what a
    # tool cannot settle; the actual text beside every claim; demonstrate, never preach.
    try:
        from . import seekers as _seek
        great = _seek.match(text)
    except Exception:  # noqa: BLE001
        great = None
    if great:
        from .verifiers import scripture as _scr2
        verses = []
        for r in great["refs"][:3]:
            got = _scr2.read_passage(r)
            if got.get("status") == "ok":
                verses.extend({"ref": v.get("ref", r), "text": v.get("text", "")}
                              for v in (got.get("verses") or [])[:2])
        return _witnessed({**base, "kind": "seeker", "message": great["answer"],
                           "scripture": verses, "generated": False,
                           "note": ("A curated answer to a question people have always asked — "
                                    "written plainly, honest about what a tool cannot settle. "
                                    "The verses are the actual text; the weighing is yours.")},
                          text, witness, gate_just_opened)
    # A COMPARISON IS A DIFFERENT QUESTION, and reading it as one bag of words is why
    # "compare and contrast Nazarene vs Wesleyan" returned six Wesleyan cards and never mentioned
    # that the other half was missing. Two subjects must be retrieved SEPARATELY or the answer is
    # half a question answered as though it were whole.
    #
    # Placed here deliberately: AFTER the crisis path and the seeker answers, which outrank
    # everything and always will. A person in trouble is never handed a comparison table.
    from . import compare as _compare
    # `get` rides along so the voice cards arrive FULL — the first live both-sides run presented
    # two voices with body None, because search hands back briefs and nothing rehydrated them.
    # `acquire` is the hand that goes OUT (Matt, 2026-08-02: "I asked it to find the information,
    # and it couldn't do that"): a side the keeping cannot stand up is pulled and carded ON THE
    # CALL — the slower answer — and kept, so the next asking never goes out.
    from . import expand as _expand
    _cmp = _compare.compare(
        text, search=corpus.search, get=corpus.get_card,
        acquire=lambda subject: _expand.pull_and_card(text, subject, config, plane="human"))
    if _cmp:
        out = {**base, "kind": "comparison", "generated": False,
               "message": _cmp["message"], "subjects": _cmp["subjects"],
               # THE VOICE RIDES FULL; the supporting cards stay briefs. Two live runs delivered
               # empty voices, and the second proved the cause was HERE: compare.py rehydrated the
               # voice and this line briefed it right back — `_brief` keeps a 200-char snippet and
               # drops `body`, so the message promised "the tradition's own voice, in its own
               # reckoning" while this shaping threw the reckoning away. The voice is the one card
               # whose CONTENT is the answer; its confession/emphasis/gift/scripture live in
               # `extra` and travel with it.
               "sides": [{"subject": s["subject"],
                          "held_as_tradition": s["held_as_tradition"],
                          "voice": s.get("voice") or None,
                          # a side standing on its own documents carries them — the passages ride
                          # as briefs a reader can open, never silently dropped like the voice was
                          **({"their_own_documents":
                              [corpus._brief(c) for c in s["their_own_documents"]]}
                             if s.get("their_own_documents") else {}),
                          "cards": [corpus._brief(c) for c in s["cards"]]}
                         for s in _cmp["sides"]],
               "missing": _cmp["missing"], "shared_ground": _cmp["shared_ground"],
               "note": ("Composed, not written: every line is a card you can open, in its own "
                        "tradition's voice. Where a side is missing this says so rather than "
                        "filling the gap.")}
        if _cmp.get("want"):
            out["want"] = _cmp["want"]
        return _witnessed(out, text, witness, gate_just_opened)

    _vol = (_decks.predict(subj, k=1) or [None])[0]
    hits = []
    if practical:
        # A how-to question wants the DIRECTLY-USEFUL card, not an academic near-match. Measured live
        # 2026-08-12: "how do I purify water" led with an antibiotics THEORY card, "treat a burn" with
        # conservation of momentum — the Theory-Assay shelf matched a shared word and outranked the
        # field library. Lead with the practical shelves (field kit, medicine, almanac, the trades),
        # merged AHEAD of the whole keeping so the answer a family needs stands first — and the whole
        # keeping still rides behind, so nothing is lost. Only lead with it when it actually matches.
        q = subj
        pool = _practical_pool(q)
        # Subject extraction can drop the very noun ("start a fire" -> "start"): if nothing in the
        # pool shares a word, retry on the words as typed before giving up.
        if q != (text or "") and not any(_shares_a_word(q, c) for c in pool[:6]):
            q = text or q
            pool = _practical_pool(q)
        hits = _practical_rank(q, pool)                # instructional field cards lead; DB rows + noise last
        subj = q                                       # the effective query, for the weak check below
    else:
        if _vol:
            hits = corpus.search(subj, limit=6, shelves=_decks.deck_shelves(_vol["id"]))
        if len(hits) < 3 or (hits and not _shares_a_word(subj, hits[0])):
            hits = corpus.search(subj, limit=6)
    if not hits and subj != (text or ""):         # last resort — the raw words as typed
        hits = corpus.search(text, limit=6)
    if _vol:
        base = {**base, "volume": {"id": _vol["id"], "name": _vol["name"]}}
    weak = (not hits) or not _shares_a_word(subj, hits[0])
    # For a HOW-TO, "shares a word" is not "answered": a cosmetic 'Tan' foundation shares 'tan' with
    # "tan a deer hide"; a reference-DB row shares a noun. None is the instruction asked for. When the
    # best we hold is NOT a genuine instructional field card (or is product noise), treat it as a GAP
    # and let the tortoise go GET the real thing and card it — Matt: "even if we respond slower. The
    # tortoise idea." The whole point: a miss goes out to primary sources and comes back a card, so the
    # NEXT asking is fast. (Crisis/comfort/verify/seeker all returned far above; this is how-tos only.)
    gap_lead = None                                # a real nearest to restore if the tortoise finds nothing
    if practical and not weak and hits:
        _top = hits[0]
        if _is_product_noise(_top) or _top.get("shelf") not in _FIELD_INSTRUCTIONAL:
            weak = True
        elif not _title_names_subject(subj, _top):
            # The lead IS an instructional field card, but its TITLE names none of the subject — it
            # only mentions the thing in passing ("start a fire" -> "The knots worth knowing"). That is
            # a masked GAP the ranker can't see, not the answer: send the tortoise to FETCH the real
            # source and card it (Matt: "even if we respond slower"). Keep this nearest as a fallback
            # so a pull that comes back empty never costs the closest real card we did hold.
            weak = True
            gap_lead = list(hits)
        elif _off_domain_shift(text, _top):
            # The lead names the subject and sits on a field shelf, but its TITLE has shifted to a
            # DIFFERENT frame the asker never entered — "raise hogs" answered by "hog cholera" (a
            # disease book), "keep bees" by "the anatomy of the honey bee". Deterministic and domain-
            # aware (`_off_domain_shift`): it fires only on a genuine cross-domain shift, so it never
            # rejects a related FORM ("honeybees" ~ "beekeeping") and never shifts a health question met
            # by a health book. A masked gap all the same — go FETCH the how-to and keep it; hold this
            # nearest as the fallback if the pull comes back empty.
            weak = True
            gap_lead = list(hits)
    if weak:
        # SEARCH ONCE, KEEP IT (Matt, 2026-08-02: "so we only search once per question"). Before
        # sending the tortoise back out, look in the keeping for passages it ALREADY went and cut
        # for this very subject on an earlier ask. A second identical how-to must be answered from
        # the keeping, instantly — never re-fetch the same public-domain book (a fetch re-downloads
        # the whole body to re-hash it, ~30–90s). Only the tortoise's own tagged passages qualify
        # (see _is_kept_tortoise_source), so a tangential bulk source never short-circuits a real gap.
        # Look on the INSTRUCTIONAL field shelves, where the tortoise keeps its practical passages —
        # an unscoped search for a how-to subject is drowned by dictionary/lexicon rows that merely
        # share a common word ("start fire" pulled in 'jump-start', 'head start', a dozen network
        # ports) and pushed the kept cards past the window (measured live 2026-08-15: the kept
        # passages ranked 10th, 23rd, 28th). Scoped, they stand where they can be found.
        # AND the kept card's TITLE must name the subject (_pulled_lead_names_subject): a pull that
        # MIS-SELECTED on an earlier ask kept its spans too, and _is_kept_tortoise_source recognises them
        # by the shared crafted-subject word — so without this, a kept waste-water span ("raise goats for
        # milk") or carpentry span ("lye soap from wood ash") would be replayed here, instantly and
        # confidently wrong, never even reaching the fresh-pull guard. Same guard, both doors. Live
        # 2026-09-01: these three were being served from exactly this short-circuit.
        already = [c for c in (corpus.search(subj, limit=15, shelves=set(_FIELD_INSTRUCTIONAL)) or [])
                   if _is_kept_tortoise_source(subj, c) and _pulled_lead_names_subject(subj, c)]
        if already:
            # a cut passage leads over the book-level source card — it carries the actual instruction
            already.sort(key=lambda c: 0 if c.get("box") == "excerpt" else 1)
            seen_ids = {c.get("id") for c in already}
            hits = (already + [c for c in (corpus.search(subj, limit=6) or [])
                               if c.get("id") not in seen_ids])[:6]
            weak = False
            gap_lead = None
            base = {**base, "message": ("Here's what the tortoise went and found for this in the "
                                        "public domain — kept from an earlier asking, so it's here "
                                        "at once, no waiting:")}
    if weak:
        # THE PULL RUNS ON EVERY DOOR, not just the comparison (Matt, 2026-08-02: "Now it says it
        # doesn't have anything for southern baptists. It should find what I need, when I need
        # it."). pull_and_card had been wired into the comparison path only, so a plain question
        # about a subject the keeping lacked still fell through to the citation-only tortoise —
        # "here is a book that exists" instead of the information asked for. Fetch, cut, KEEP,
        # answer — and because the cards are kept, the next asking never reaches this branch.
        try:
            from . import expand as _expand
            pulled = _expand.pull_and_card(text, subj, config, plane="human")
        except Exception:  # noqa: BLE001 — the pull failing must never cost the citation fallback
            pulled = {"status": "error"}
        if pulled.get("status") == "carded":
            # THE PULLED CARDS LEAD — but only when the lead's TITLE names the subject. The re-search
            # fills the seats behind the pulled spans (the spy test guards that "fellowship" hits don't
            # bury them). "The spans carry the subject by construction" was too strong a trust: craft.rank
            # cuts a span wherever it shares ONE distinctive stem, so a tangential source still cards —
            # live 2026-08-31, "raise goats for milk" led with a waste-water treatise ("Unfiltered Waste-
            # water..."), "lye soap from wood ash" with a carpentry manual ("CARPENTRY AND JOINERY", cut
            # on the wrong sense of 'wood'), each confident and wrong. Guard the lead with the same masked-
            # gap test the pre-pull path already trusts (_title_names_subject, at the `not
            # _title_names_subject(subj, _top)` branch above): the lead leads only if its TITLE names the
            # subject. Title, NOT body — the wrong source's body is exactly what shares the one common word
            # ('wood', 'milk'); that overlap IS the mis-selection, so a body test would wave carpentry
            # through. Checked against the user's subject OR the subject the card was crafted for, so a
            # canon source cut on its own clean subject ("beekeeping" for "keep honeybees") still leads
            # while a reach mis-selection — whose crafted subject is the user's own words — cannot. Names
            # neither -> weak stays True: the honest gap / web fallback answers, never a confident wrong
            # source. A gap must stay a gap. (hits is reassigned only when the lead passes, so a rejected
            # pull never leaks the wrong card into the fallback display either.)
            pulled_cards = list(pulled.get("cards") or [])[:6]
            _lead = pulled_cards[0] if pulled_cards else None
            if _lead and _pulled_lead_names_subject(subj, _lead):
                seen_ids = {c.get("id") for c in pulled_cards}
                hits = (pulled_cards +
                        [c for c in (corpus.search(subj, limit=6) or [])
                         if c.get("id") not in seen_ids])[:6]
                weak = False
                base = {**base, "message": pulled.get("message", "")}
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
        if practical and gap_lead:
            gap_lead = [c for c in gap_lead if not _is_practical_junk(c)]   # never a novel/pill as "nearest"
        if gap_lead:
            # A masked gap whose tortoise came back empty: show the nearest REAL field card we held,
            # framed honestly (it is adjacent, not exact) — never worse than before, never a confident
            # mislead. "start a fire" keeps the knots card, but says plainly it's the nearest.
            out = {**base, "kind": "found", "lead": _lead_card(gap_lead[0]),
                   "message": "I don't have a card exactly on that yet — here is the nearest the "
                              "keeping holds while I go find the rest:",
                   "results": [corpus._brief(c) for c in gap_lead]}
            return _witnessed(out, text, witness, gate_just_opened)
        if _is_question(text):
            # No confident dump of irrelevant cards — but we POINT, politely, to where a verified
            # answer lives (the free libraries; a claim check). Sources go in `resources`, not results.
            return _witnessed({**base, "kind": "found", "results": [],
                               "message": "I don't have a verified answer for that, and I won't "
                                          "invent one — but here is where to find it, in sources you "
                                          "can trust:",
                               "resources": [{"label": "The free libraries & references", "ref": "/corpus.html"},
                                             {"label": "Check a specific claim, verified", "ref": "/check.html"},
                                             {"label": "Read Scripture", "ref": "/bible.html"}]},
                              text, witness, gate_just_opened)
        # not a question — a topic the keeping is thin on. Show the nearest, but say it plainly.
        out = {**base, "kind": "found", "results": [corpus._brief(c) for c in hits],
               "message": "Nothing on that directly — here is the nearest in the keeping:"}
        return _witnessed(out, text, witness, gate_just_opened)

    # SHAPE THE FOUND HITS — one consolidated discernment step (practical-junk drop · pronunciation-key
    # demotion · whole-name coverage). A how-to left with only word-matches returns [] — answer honestly
    # rather than hand a family a pill powder for "how do i keep chickens".
    _shaped = _shape_found_hits(hits, text, practical)
    if not _shaped:
        return _witnessed({**base, "kind": "found", "results": [],
                           "message": "I don't have a real how-to on that yet, and I won't hand "
                                      "you a word-match. Here's where to look while I go find and "
                                      "keep the tried-and-true source:",
                           "resources": [{"label": "What do you need right now?", "ref": "/situations.html"},
                                         {"label": "Ask out loud", "ref": "/coach"},
                                         {"label": "Search the whole library", "ref": "/read.html"}]},
                          text, witness, gate_just_opened)
    hits = _shaped

    # THE LIBRARIAN, not the filing cabinet (2026-08-12): lead with the ONE best card in its OWN
    # full words, cited to its source, and a warm line to hand it over — then the rest as "more in
    # the keeping." The old shape returned six equal 180-char snippets and no lead sentence: a person
    # who asked got a drawer to rummage, not an answer. `results` stays whole (the page dedups the
    # lead) so nothing downstream that counts on it changes; `lead` + `message` are additive.
    # When the tortoise pulled these cards on the call — or found them already kept from an earlier
    # pull — `base` already carries the honest "went and found it, kept it" line. Keep it rather than
    # paper over it with the generic lead (this is what the spy test guards: a pull that cards must
    # SAY it went and got it). Otherwise, the librarian's warm handoff.
    out = {**base, "kind": "found", "message": base.get("message") or _FOUND_LEAD,
           "lead": _lead_card(hits[0]), "results": [corpus._brief(c) for c in hits]}
    cloud = _connected_cloud(hits[0].get("id"))
    if cloud:
        out["cloud"] = {"around": hits[0].get("title", ""), "witnesses": cloud}
    # The concierge: a search result is RELATED material, not a VERIFIED answer. For a question,
    # point — politely — to where a verified answer can be found (the free libraries; a claim check).
    if _is_question(text):
        out["resources"] = [{"label": "The free libraries & references", "ref": "/corpus.html"},
                            {"label": "Check a specific claim, verified", "ref": "/check.html"}]
    return _witnessed(out, text, witness, gate_just_opened)
