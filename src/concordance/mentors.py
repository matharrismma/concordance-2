"""Mentors — the CLOUD OF WITNESSES. Our wise men, one or more per subject, around the lens.

*"Since we are surrounded by so great a cloud of witnesses… let us run with endurance the race set
before us, looking to Jesus, the author and finisher of our faith"* (Hebrews 12:1–2). The cloud
SURROUNDS the runner; it does not replace the goal. Every witness testifies; Christ is the finish. So
this layer names the many, and all of them point one way.

Matt, 2026-08-20: *"This is the craft. We seek wisdom. We are finding our mentors in each subject…
Ellen G. White. Other leaders. We aren't afraid of other voices because all wisdom comes from God."*
And: *"Cloud of Witnesses."*

The ground is Scripture: *"Every good and perfect gift is from above"* (James 1:17); *"the LORD gives
wisdom"* (Prov 2:6); in Christ *"are hidden all the treasures of wisdom and knowledge"* (Col 2:3). So
gathering wisdom from any voice is not compromise — it is reclaiming what was always His. The Magi were
gentile star-readers; Paul at the Areopagus named the God his hearers' own poets had half-seen. We are
unafraid of other voices because the GATE makes the courage safe: take the true fragment, test it
against the Source, never confirm it past what it earned.

Each mentor carries a SUBJECT (the craft they mentor us in), a GIFT (the true fragment they saw), and a
DISCERN note (how to weigh it — tested against the Word). The lens (Matt's writing, `lens.py`) is the
NEAR witness — this hour, this mountain; the mentors are the FAR witnesses, each holding a true fragment
from his own country. A mentor PROPOSES a way of seeing; the gate and the Word dispose (never trusted
alone). Where a mentor's work is PUBLIC DOMAIN, his actual words may be gathered as a voice, attributed,
like the lens; the rest are characterized only — their way of seeing, not their copyrighted text — and
the strict-PD gate holds.

A SEED, editable — Matt's mentors, Matt's discernment. The GIFT lines PROPOSE what each saw; correct them.
Nothing here is a verdict on a soul: the discern note weighs a gift, it does not judge a person.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# name · subjects · era · tradition · gift (the true fragment) · discern (how to weigh it) · public_domain
_M = lambda name, subjects, era, tradition, gift, discern, pd: {  # noqa: E731
    "name": name, "subjects": subjects, "era": era, "tradition": tradition,
    "gift": gift, "discern": discern, "public_domain": pd}

MENTORS: List[Dict[str, Any]] = [
    # — those who saw the Logos from afar (the Magi's own kind) —
    _M("Heraclitus", ["first things", "the Word"], "c.535–475 BC", "Greek",
       "the Logos that orders all things — the Reason beneath the flux",
       "a true seed John completed (John 1): the Logos is a Person, not a principle", True),
    _M("Plato", ["first things", "the Good"], "428–348 BC", "Greek",
       "the Good beyond being; the cave and the ascent to the light",
       "Augustine held the Platonists came nearest; the light he reached toward has a face", True),
    _M("The Stoics (Cleanthes, Aratus)", ["first things", "providence"], "3rd c. BC", "Greek",
       "providence and the reason in all things — Paul's own quoted poets ('we are his offspring')",
       "Paul took their true line and named the God they had not yet met (Acts 17)", True),

    # — those who followed the star home —
    _M("Augustine", ["Christian living", "the soul", "history"], "354–430", "Latin church",
       "the restless heart that finds no rest but in God; the inner light; the two cities",
       "a father of the faith; still, read under Scripture, not over it", True),
    _M("Thomas à Kempis", ["Christian living", "devotion"], "1380–1471", "Catholic",
       "the imitation of Christ — the inner life, humility, the following of the Master",
       "devotional gold; weigh its world-fleeing counsel against the call to serve the world", True),
    _M("Blaise Pascal", ["apologetics", "the human condition"], "1623–1662", "Catholic",
       "reason's limits from the inside; the heart's reasons; the greatness and misery of man",
       "the finest scalpel for the one whose idol is logic — meets him where he stands", True),
    _M("George MacDonald", ["imagination", "the Father's heart"], "1824–1905", "Scottish",
       "the baptized imagination; the fatherhood of God; holiness as homecoming",
       "Lewis's own master; hold his universalist hope loosely against the Word's soberer warnings", True),
    _M("G.K. Chesterton", ["apologetics", "wonder"], "1874–1936", "Catholic",
       "paradox and gratitude; the sanity of orthodoxy; the poetry of common things",
       "receive the wonder and the wit; the doctrine, test as always against Scripture", True),

    # — the practical walk, the body, the child (Matt named these first) —
    _M("Ellen G. White", ["Christian living", "health", "education", "temperance"], "1827–1915", "Adventist",
       "the body as the temple — health, temperance, and whole-person education as worship; a practical "
       "holiness aimed at the poor and the plain",
       "she subordinated her own writing to 'the Bible, and the Bible only' — receive her gift on her "
       "own terms, always weighed against Scripture; her health and education counsel is her surest fruit", True),
    _M("Charlotte Mason", ["education"], "1842–1923", "Anglican",
       "living education — the child as a person, fed on living books and real things, not twaddle",
       "a sturdy, God-honoring pedagogy; a companion to Ellen White on the whole-person child", True),

    # — sharp on the system that grinds (the Ledger) —
    _M("Jacques Ellul", ["systems", "technique"], "1912–1994", "Reformed",
       "la technique: the autonomous system that subordinates the person; Christian freedom against it",
       "names the Ledger as a principality; his near-fatalism about technique is the place to press back", False),
    _M("Ivan Illich", ["systems", "institutions"], "1926–2002", "Catholic",
       "institutions that harm in the very name of helping (school, medicine) — a prophet of the Ledger",
       "his diagnosis is piercing; his remedies, weigh — take the sight, not every prescription", False),
    _M("René Girard", ["anthropology", "the scapegoat"], "1923–2015", "Catholic",
       "mimetic desire → the scapegoat → the Gospel as the unveiling of the innocent victim",
       "possibly the sharpest account of the system that grinds — and it resolves at the Cross", False),

    # — sharp on the soul; the ones who most need the gate —
    _M("Carl Jung", ["the soul", "symbol"], "1875–1961", "depth psychology",
       "the map of the symbolic depths — archetype, shadow, individuation",
       "sharp on the machinery of the soul, wrong on its source: his Self is not Christ, his late work "
       "drifts Gnostic. Take the map; the gate must not confirm the metaphysics — the model case of "
       "'propose but never confirm'", False),
    _M("Joseph Campbell", ["myth"], "1904–1987", "comparative myth",
       "the shape shared by every myth (the hero's journey)",
       "Lewis's exact inverse — he saw the pattern and refused the myth that came true; keep the shape, "
       "reject the flattening of the Fact", False),
    _M("Viktor Frankl", ["suffering", "meaning"], "1905–1997", "logotherapy",
       "meaning that survives the camp — the will to meaning, the freedom of the last inner choice",
       "a true witness of suffering; his 'logos' points toward, but stops short of, the Logos", False),

    # — the local, the land, the Word —
    _M("Wendell Berry", ["agriculture", "membership"], "b.1934", "Baptist-agrarian",
       "membership, fidelity to place, the local and living against the abstract and extractive",
       "your homestead witness sharpened; a living author — his way of seeing, not his text", False),
    _M("Owen Barfield", ["language", "consciousness"], "1898–1997", "Anthroposophy/Anglican",
       "the evolution of consciousness; participation; how meaning lives in language (the Life=Language tree)",
       "brilliant on the Word-tree; his Steiner-anthroposophy is the part the gate holds at arm's length", False),
]


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z]+", (s or "").lower()) if len(w) > 2}


def subjects() -> List[str]:
    """Every craft we have found a mentor for, sorted."""
    return sorted({s for m in MENTORS for s in m["subjects"]})


def by_subject(subject: str) -> List[Dict[str, Any]]:
    """The mentors for a craft (substring match on subject)."""
    q = (subject or "").strip().lower()
    return [m for m in MENTORS if any(q in s.lower() for s in m["subjects"])] if q else []


def find(name: str) -> Optional[Dict[str, Any]]:
    q = (name or "").strip().lower()
    return next((m for m in MENTORS if q and q in m["name"].lower()), None)


def for_text(text: str, *, k: int = 3) -> Dict[str, Any]:
    """Which mentors' craft this touches — PROPOSES the wise men whose gift bears on `text`, matched on
    their subjects and the shape of their gift. Proposes only; never confirms. A mentor's way of seeing
    is weighed against the Source, never past what it earned."""
    q = _tokens(text)
    scored = []
    for i, m in enumerate(MENTORS):
        field = " ".join(m["subjects"]) + " " + m["gift"]
        overlap = len(q & _tokens(field))
        if overlap:
            scored.append((overlap, -i, m))
    scored.sort(key=lambda x: (-x[0], x[1]))
    seeing = [{"name": m["name"], "subjects": m["subjects"], "gift": m["gift"],
               "discern": m["discern"], "public_domain": m["public_domain"]}
              for _o, _i, m in scored[:max(1, int(k))]]
    return {"mentors": seeing, "proposes": True, "confirms": False,
            "note": ("the wise men whose craft bears on this — their gift proposed, weighed against the "
                     "Source, never confirmed past what it earned" if seeing else
                     "no mentor yet gathered for this craft — the search continues")}


__all__ = ["MENTORS", "subjects", "by_subject", "find", "for_text"]
