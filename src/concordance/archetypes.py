"""Archetype decks — the characters of the Bible, and the moments within their lives.

Matt: "The archetypes … those would be all of the characters of the Bible. Name micropositions,
and have decks for different parts of each. The more specifically we identify the need, the more
we use past success to improve — answers get better and better."

Each biblical character is an archetype of a human condition; each MICROPOSITION is a named moment
in that life (David facing the giant; David after his sin; Job when God feels silent; Peter in his
denial; the prodigal on the road home). When a person's need matches a microposition, we meet them
where that character stood — and the FITTING WORD does the speaking, not us.

Discipline: gather, don't author. We supply the character, the moment, the plain situation it
meets, and the CANONICAL Scripture references for that spot — nothing invented, no verse fabricated
(the surface resolves the refs to the actual text). This is the seed the front door already carries
(distress → the fitting comfort verse), named down to the position. Crisis still outranks
everything; this is the non-crisis pastoral layer. Christ is where every road here leads.

This is a first, flagship set — grounded and charitable. It grows; Matt sets the plumb-line and the
tone (where it meets, and where a soul or a tradition falls short) — this only lays the positions.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

_TOK = re.compile(r"[a-z']{3,}")
_STOP = {"the", "and", "for", "was", "with", "have", "this", "that", "from", "your", "you're",
         "not", "but", "are", "who", "how", "why", "what", "when", "will", "cant", "can't",
         "feel", "feeling", "like", "just", "been", "them", "they", "his", "her"}


def _toks(s: str) -> Set[str]:
    return {t for t in _TOK.findall(str(s or "").lower()) if t not in _STOP}


# Each archetype: a character, the condition they embody, and their micropositions.
# A microposition: id, moment (the biblical spot), meets (the human situation, plain), keywords
# (what routes a person's words TO it), scripture (CANONICAL refs — the fitting Word for that spot).
ARCHETYPES: List[Dict[str, Any]] = [
    {"character": "David", "condition": "the whole range of the human heart before God",
     "micropositions": [
        {"id": "david_guilt", "moment": "after his sin with Bathsheba, broken before God",
         "meets": "shame, guilt, having done something terrible, needing to be clean again",
         "keywords": {"guilt", "guilty", "ashamed", "shame", "sinned", "sin", "did", "wrong",
                      "terrible", "unclean", "dirty", "forgive", "forgiven", "repent"},
         "scripture": ["Psalm 51:1-2", "Psalm 51:10", "Psalm 51:17", "1 John 1:9"]},
        {"id": "david_fear", "moment": "hunted by Saul, hiding in caves",
         "meets": "fear, being pursued or threatened, feeling unsafe",
         "keywords": {"afraid", "fear", "scared", "danger", "threatened", "hunted", "unsafe",
                      "anxious", "anxiety", "hiding", "enemies", "trapped"},
         "scripture": ["Psalm 56:3-4", "Psalm 34:4", "Psalm 27:1"]},
        {"id": "david_grief", "moment": "weeping at the gate for his son Absalom",
         "meets": "grief, the loss of a child or someone loved, being crushed",
         "keywords": {"grief", "grieving", "lost", "loss", "died", "death", "mourning", "crushed",
                      "heartbroken", "brokenhearted", "child", "son", "daughter"},
         "scripture": ["2 Samuel 18:33", "Psalm 34:18", "Psalm 147:3"]},
        {"id": "david_giant", "moment": "a boy before Goliath with a sling",
         "meets": "facing something far bigger than you, overwhelmed by an opponent",
         "keywords": {"giant", "goliath", "overwhelmed", "impossible", "bigger", "outmatched",
                      "opponent", "battle", "facing", "against", "odds"},
         "scripture": ["1 Samuel 17:45", "1 Samuel 17:47"]}]},
    {"character": "Job", "condition": "undeserved suffering, and God's seeming silence",
     "micropositions": [
        {"id": "job_loss", "moment": "on the ash-heap, everything taken in a day",
         "meets": "sudden catastrophic loss, suffering you did nothing to deserve",
         "keywords": {"lost", "everything", "suffering", "undeserved", "unfair", "why", "ruin",
                      "ruined", "catastrophe", "wiped", "gone"},
         "scripture": ["Job 1:21", "Job 13:15"]},
        {"id": "job_silence", "moment": "seeking a God who seems to have withdrawn",
         "meets": "God feels absent or silent in the middle of pain",
         "keywords": {"silent", "silence", "absent", "abandoned", "forsaken", "distant", "hidden",
                      "far", "gone", "alone", "unanswered"},
         "scripture": ["Job 23:10", "Job 19:25", "Psalm 22:1-2"]}]},
    {"character": "Hannah", "condition": "unanswered longing, prayer out of bitterness of soul",
     "micropositions": [
        {"id": "hannah_longing", "moment": "weeping in the temple, pouring out her soul",
         "meets": "a deep unmet longing — a child, a hope deferred — bitterness of soul",
         "keywords": {"longing", "barren", "childless", "infertile", "waiting", "deferred", "hope",
                      "bitter", "empty", "unanswered", "desperate", "want"},
         "scripture": ["1 Samuel 1:10", "1 Samuel 1:15", "Psalm 62:8"]}]},
    {"character": "Peter", "condition": "the one who fails and is restored",
     "micropositions": [
        {"id": "peter_denial", "moment": "having denied Christ three times, weeping bitterly",
         "meets": "failing badly, betraying what you believe, self-contempt after",
         "keywords": {"failed", "failure", "denied", "betrayed", "coward", "let", "down",
                      "disappointed", "myself", "weak", "again"},
         "scripture": ["Luke 22:61-62", "Romans 8:1"]},
        {"id": "peter_restored", "moment": "at the charcoal fire, 'do you love me?' — restored",
         "meets": "wondering if you can be forgiven or useful again after failing",
         "keywords": {"forgiven", "restored", "again", "second", "chance", "useful", "worthy",
                      "redeem", "start", "over", "hopeless"},
         "scripture": ["John 21:15-17", "1 Peter 5:7"]}]},
    {"character": "The Prodigal Son", "condition": "the one who wanders far and comes home",
     "micropositions": [
        {"id": "prodigal_home", "moment": "on the road home, the father running to meet him",
         "meets": "having wandered far, wasted much, afraid it's too late to return to God",
         "keywords": {"wandered", "far", "wasted", "away", "return", "returning", "home", "back",
                      "prodigal", "lost", "ran", "rebelled", "late"},
         "scripture": ["Luke 15:20", "Luke 15:22-24"]}]},
    {"character": "Ruth", "condition": "loyalty in loss; the outsider who is taken in",
     "micropositions": [
        {"id": "ruth_startover", "moment": "a widow choosing loyalty, starting over in a strange land",
         "meets": "widowhood, starting over, being a foreigner, not knowing where you belong",
         "keywords": {"widow", "widowed", "startover", "start", "over", "foreigner", "stranger",
                      "belong", "alone", "loyalty", "left", "immigrant", "outsider"},
         "scripture": ["Ruth 1:16", "Ruth 2:12"]}]},
    {"character": "Joseph", "condition": "betrayal turned to providence",
     "micropositions": [
        {"id": "joseph_betrayed", "moment": "sold by his brothers, imprisoned unjustly, later 'you meant it for evil'",
         "meets": "betrayal, injustice, being wronged or forgotten by those who should have loved you",
         "keywords": {"betrayed", "betrayal", "injustice", "unjust", "wronged", "forgotten",
                      "family", "brothers", "prison", "falsely", "accused"},
         "scripture": ["Genesis 50:20", "Romans 8:28"]}]},
    {"character": "Elijah", "condition": "burnout and despair after the victory",
     "micropositions": [
        {"id": "elijah_burnout", "moment": "under the broom tree, asking to die; then the still small voice",
         "meets": "burnout, wanting to give up, feeling utterly alone even after doing right",
         "keywords": {"burnout", "burned", "exhausted", "give", "done", "tired", "quit", "alone",
                      "die", "enough", "depleted", "empty", "cant", "anymore"},
         "scripture": ["1 Kings 19:5-8", "1 Kings 19:11-12"]}]},
    # These three especially meet the seeker, the doubter, the one who opposed — the academic road.
    {"character": "Nicodemus", "condition": "the thinker who comes with questions",
     "micropositions": [
        {"id": "nicodemus_seeker", "moment": "coming by night to ask 'how can these things be?'",
         "meets": "having honest questions, being a thinker, needing to understand before believing",
         "keywords": {"question", "questions", "understand", "think", "thinker", "reason", "logic",
                      "how", "sense", "intellectual", "skeptic", "explain", "prove"},
         "scripture": ["John 3:3", "John 3:16"]}]},
    {"character": "Thomas", "condition": "the honest doubter",
     "micropositions": [
        {"id": "thomas_doubt", "moment": "'unless I see, I will not believe' — then, 'my Lord and my God'",
         "meets": "doubt, needing evidence, unable to believe on someone else's word",
         "keywords": {"doubt", "doubting", "evidence", "proof", "believe", "unless", "see",
                      "convince", "certain", "unsure", "faith"},
         "scripture": ["John 20:27", "John 20:29"]}]},
    {"character": "Paul", "condition": "the enemy of the faith, remade",
     "micropositions": [
        {"id": "paul_change", "moment": "struck down on the Damascus road; 'the chief of sinners' shown mercy",
         "meets": "having opposed God or done real harm, doubting someone like you could change",
         "keywords": {"opposed", "enemy", "against", "persecuted", "change", "changed", "past",
                      "worst", "sinner", "too", "bad", "beyond", "hypocrite"},
         "scripture": ["Acts 9:3-6", "1 Timothy 1:15-16"]}]},
]

# flatten to micropositions for matching
_MICRO: List[Dict[str, Any]] = []
for _a in ARCHETYPES:
    for _m in _a["micropositions"]:
        # route ONLY on the curated keywords — the prose "meets" text carries incidental words
        # (e.g. "betraying what you believe") that would mis-seat a need.
        _MICRO.append({**_m, "character": _a["character"], "condition": _a["condition"],
                       "_route": set(_m["keywords"])})
_BY_ID = {m["id"]: m for m in _MICRO}


def archetypes() -> List[Dict[str, Any]]:
    """The characters and their micropositions (for the atlas / a browse surface)."""
    return [{"character": a["character"], "condition": a["condition"],
             "micropositions": [{"id": m["id"], "moment": m["moment"], "meets": m["meets"]}
                                for m in a["micropositions"]]}
            for a in ARCHETYPES]


def match(need: str, k: int = 3) -> List[Dict[str, Any]]:
    """Name the position: which biblical moment does this person's need match? Returns the top-k
    micropositions by overlap with the person's words (possibly none — then say nothing rather
    than force a fit). The verse is the answer; this only finds the seat."""
    qt = _toks(need)
    if not qt:
        return []
    scored = []
    for m in _MICRO:
        overlap = qt & m["_route"]
        if overlap:
            scored.append((len(overlap), m, sorted(overlap)))
    scored.sort(key=lambda x: -x[0])
    return [_serve(m, matched=mt) for s, m, mt in scored[:max(1, int(k))]]


def _serve(m: Dict[str, Any], matched: Optional[List[str]] = None) -> Dict[str, Any]:
    return {"id": m["id"], "character": m["character"], "condition": m["condition"],
            "moment": m["moment"], "meets": m["meets"], "scripture": list(m["scripture"]),
            "matched": matched or [],
            # a posture of SERVICE, not a diagnosis: we OFFER a companion who walked something like
            # this, gently — the verse does the speaking, and we never stamp a label on a person.
            "frame": f"Someone in the Book walked something like this — {m['character']}, "
                     f"{m['moment']}. Here is the word that met that hour."}


def get(micro_id: str) -> Optional[Dict[str, Any]]:
    m = _BY_ID.get(micro_id)
    return _serve(m) if m else None


def best(need: str) -> Optional[Dict[str, Any]]:
    """The single closest microposition, or None."""
    hits = match(need, k=1)
    return hits[0] if hits else None
