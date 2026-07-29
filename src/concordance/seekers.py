"""The great questions — the ones people actually type at 2 a.m., answered in their language.

Matt, 2026-07-28: "Full recalibration based on mission: Great Commission. We are after sinners not
saints... make sure we are engaging and useful to any that enter the site... use the language of
the people that will use this. We never hide who we are, but we are here to demonstrate not preach."

The usefulness probe found the gap the day this was written: six of nine seeker questions —
"is God even real", "what happens when we die", "why do bad things happen to good people" —
fell through to a keyword-search shrug: "the keeping doesn't hold a verified answer." The person
the whole mission is aimed at asked the biggest question they have, and the site changed the
subject. This module is the correction.

The discipline, unchanged from the rest of the house:
  * These answers are CURATED PASTORAL PROSE, the same class as the comfort message and the
    archetype framings — authored once, in plain words, reviewed like any other content. Nothing
    is generated at answer time.
  * Plain language ONLY. No insider vocabulary; where a churchly word is unavoidable it is
    explained in the same breath.
  * Honest about what a tool can and cannot do: the biggest questions are not settled by
    software, and the answers say so. We show what Scripture says AS what Scripture says, show
    where people have found the case compelling, and hand the person the door — never push them
    through it. Demonstrate, don't preach; never hide who we are.
  * Scripture refs are canonical and resolved by the surface (never generated). The gate logic is
    untouched: a God-ward question opens the gate BY BEING ASKED (Matthew 7:7 — the ask classifier
    already works this way); a mundane question can never match here (keyword threshold).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

_TOK = re.compile(r"[a-z']{3,}")


def _toks(s: str) -> Set[str]:
    return set(_TOK.findall((s or "").lower()))


# Each entry: keywords (≥2 must overlap — mundane text never matches), the plain answer, the
# Scripture that speaks to it, and honesty flags where the traditions genuinely differ.
QUESTIONS: List[Dict[str, Any]] = [
    {"id": "is_god_real",
     "keywords": {"god", "real", "exist", "exists", "there", "evidence", "proof", "believe", "atheist"},
     "answer": ("That's the biggest question there is, and no website settles it — including this "
                "one. Here's what we can honestly do: show you what people through the centuries "
                "have found compelling — a universe that runs on laws a mind can read, a sense of "
                "right and wrong nobody taught you, and the historical case around Jesus of "
                "Nazareth. This whole tool was built by people who looked and concluded yes; every "
                "claim we make comes with a receipt you can check yourself. Look for yourself, at "
                "your own pace. The invitation Scripture itself gives is not 'take our word for "
                "it' — it's 'seek, and you will find.'"),
     "refs": ["Psalm 19:1", "Romans 1:20", "Matthew 7:7", "Jeremiah 29:13"]},
    {"id": "what_happens_when_we_die",
     "keywords": {"die", "death", "dies", "died", "afterlife", "happens", "heaven", "gone", "end"},
     "answer": ("Nobody standing on this side can show you a lab result. Here's what we can show "
                "you: what the Bible actually says — that death is real and grieved, not waved "
                "away; and that it also claims one man came back and was seen, which is either the "
                "most important event in history or it isn't. The traditions differ on details, "
                "and we'll show you those differences honestly rather than pretend they don't "
                "exist. If you're asking because you lost someone: we're sorry, truly — and the "
                "verses below have carried a lot of people through that door."),
     "refs": ["John 11:25-26", "1 Corinthians 15:3-6", "Revelation 21:4", "Psalm 23:4"]},
    {"id": "why_bad_things",
     "keywords": {"bad", "things", "happen", "good", "people", "suffering", "unfair", "innocent",
                  "evil", "hurt", "children", "cancer", "allow", "allows"},
     "answer": ("The Bible never gives the tidy answer, and honest teachers admit it. What it "
                "gives instead is a book-length wrestle (Job), a God who is described as close to "
                "the broken rather than distant from them, and — at the center — a God who is "
                "claimed to have taken the suffering on Himself rather than explaining it away. "
                "That's not a formula; it's a companion. If this question is personal for you "
                "right now, the verses below are where sufferers have stood before you."),
     "refs": ["Job 1:21", "Psalm 34:18", "Romans 8:28", "John 16:33"]},
    {"id": "meaning_point",
     "keywords": {"point", "meaning", "purpose", "empty", "meaningless", "matter", "matters",
                  "here", "life", "living", "pointless", "why", "there", "anything", "bother"},
     "answer": ("A book of the Bible opens exactly where you are: 'Meaningless, meaningless — "
                "everything is meaningless.' It was written by a king who tried wealth, work, "
                "pleasure, and achievement, and found the emptiness on the far side of all of it. "
                "The Bible doesn't scold the feeling; it takes it seriously and then makes a "
                "claim: that you were made on purpose, for a purpose, and the ache is homesickness. "
                "You don't have to buy that today. Read the honest book first — it's called "
                "Ecclesiastes, and it's shorter than a podcast."),
     "refs": ["Ecclesiastes 1:2", "Ecclesiastes 3:11", "Psalm 139:13-14", "Matthew 11:28"]},
    {"id": "how_forgive",
     "keywords": {"forgive", "forgiveness", "hurt", "wronged", "betrayed", "angry", "grudge",
                  "resentment", "someone"},
     "answer": ("Forgiveness isn't saying it didn't matter, and it isn't feeling warm toward the "
                "person — it's putting down the debt so it stops collecting interest from YOU. "
                "The Bible is blunt that it's hard: it tells of a man forgiven a fortune who "
                "couldn't forgive pocket change, and everyone can see which one he was meant to "
                "be. Start small if you have to: wanting to want to forgive counts as a start. "
                "And if the person who hurt you was meant to be safe — a parent, a spouse — "
                "forgiveness does not mean going back into harm's way. It never has."),
     "refs": ["Matthew 18:21-22", "Ephesians 4:31-32", "Colossians 3:13", "Luke 23:34"]},
    {"id": "start_over",
     "keywords": {"start", "over", "restart", "second", "chance", "fresh", "new", "beginning",
                  "again", "ruined", "wasted", "messed"},
     "answer": ("The Bible is practically a catalog of second starts: a murderer led a nation, "
                "a betrayer became the first preacher, a persecutor wrote half the New Testament. "
                "The claim underneath is that starting over isn't self-reinvention — it's being "
                "given back. Whatever you're coming out of, the pattern is the same: turn, take "
                "the next honest step, let the past be forgiven rather than re-litigated daily. "
                "The verses below are the ones people in your exact spot have kept in their "
                "pocket."),
     "refs": ["Lamentations 3:22-23", "2 Corinthians 5:17", "Philippians 3:13-14", "Isaiah 43:18-19"]},
    {"id": "does_god_care",
     "keywords": {"care", "cares", "notice", "notices", "matter", "invisible", "forgotten",
                  "listening", "hears", "about", "god"},
     "answer": ("The Bible's own claim is oddly specific: the hairs of your head are counted, "
                "your tears are kept in a bottle, and not one sparrow falls unnoticed. You can't "
                "verify that in a lab — but you can weigh the kind of God being described: not a "
                "distant force but someone who notices small things. The invitation is to test it "
                "the only way it can be tested: bring Him something real and see. That's not a "
                "trick; it's how every relationship starts."),
     "refs": ["Matthew 10:29-31", "Psalm 56:8", "1 Peter 5:7", "Psalm 139:1-4"]},
    {"id": "who_is_jesus",
     "keywords": {"jesus", "christ", "who", "was", "really", "actually", "prophet", "teacher"},
     "answer": ("Historically: a first-century Jewish teacher executed under Pontius Pilate — "
                "that much is about as solid as ancient history gets. The argument is over what "
                "he claimed and what happened next. He didn't leave the option of 'just a good "
                "teacher' open: He claimed to forgive sins and to be one with God, which makes him "
                "either wrong, lying, or right. This site exists because its builders weighed the "
                "evidence — especially the resurrection reports — and concluded 'right.' You can "
                "read the primary sources yourself; the shortest one takes about an hour."),
     "refs": ["Mark 10:45", "John 14:6", "1 Corinthians 15:3-6", "Mark 1:1"]},
    {"id": "how_to_pray",
     "keywords": {"pray", "prayer", "praying", "talk", "god", "how", "start", "words", "allowed"},
     "answer": ("There's no password and no required vocabulary. When Jesus' friends asked him "
                "this exact question, the model He gave is about forty words long and starts with "
                "'Father' — which tells you the register: a child talking to a parent, not a "
                "petitioner addressing a bureau. Say what's true. 'I'm not sure you're there, but "
                "if you are —' is a prayer; people have started there and not stopped. There's no "
                "performance to grade."),
     "refs": ["Matthew 6:9-13", "Luke 11:1", "Philippians 4:6-7", "Psalm 62:8"]},
    {"id": "good_enough",
     "keywords": {"good", "enough", "accept", "accepts", "worthy", "worthless", "failure",
                  "disappointment", "measure", "qualify", "deserve"},
     "answer": ("Here's the strange center of the whole thing: the Bible's answer is 'no, you're "
                "not good enough — and neither is anyone else, and that was never the entry "
                "requirement.' Every other system says climb; this one says the climbing was done "
                "for you, and what's asked of you is to receive it. That's why the people Jesus "
                "was hardest on were the ones certain of their own goodness, and the ones he ate "
                "dinner with were everybody else. If you feel disqualified, you're precisely who "
                "the invitation is addressed to."),
     "refs": ["Romans 3:23-24", "Ephesians 2:8-9", "Luke 5:31-32", "Matthew 9:13"]},
    {"id": "why_trust_bible",
     "keywords": {"bible", "trust", "reliable", "wrote", "written", "changed", "translated",
                  "myth", "stories", "true", "believe"},
     "answer": ("Fair question — don't trust it blindly; that's not even what it asks. A few "
                "checkable facts: it's not one book but 66, written across ~1,500 years, and its "
                "text is the best-attested of any ancient document by manuscript count. This site "
                "shows you the actual Hebrew and Greek under every verse so you can see what was "
                "written rather than take a translator's word. Whether it's TRUE is a bigger "
                "question than textual reliability — but it starts with reading it, and most "
                "people arguing about it haven't. Start with one of the short eyewitness-era "
                "accounts; Mark takes about an hour."),
     "refs": ["Luke 1:1-4", "2 Timothy 3:16", "Psalm 119:105", "Isaiah 40:8"]},
    {"id": "so_much_evil",
     "keywords": {"evil", "world", "wrong", "broken", "hate", "war", "cruelty", "humanity",
                  "wicked", "getting", "worse"},
     "answer": ("The Bible agrees with your eyes: something is deeply wrong with the world, and "
                "it locates the fracture not just 'out there' but running through every human "
                "heart — including the ones writing and reading this. That diagnosis is either "
                "depressing or clarifying, depending on the next line: that the story is not "
                "finished, that evil gets an end date, and that the repair began in the middle of "
                "history rather than waiting for the end of it. We can't prove the ending to you. "
                "We can show you the diagnosis is at least honest."),
     "refs": ["Romans 3:10-12", "Genesis 6:5-6", "Revelation 21:4-5", "John 1:5"]},
]

NOTE = ("Curated answers to the perennial seeker questions, in plain language — authored once and "
        "reviewed like all content, never generated at answer time. Honest about what a tool "
        "cannot settle; identity never hidden; the mode is demonstration, not preaching. Every "
        "reference resolves to the actual text.")


# ANCHORS: a match must touch at least one DISTINCTIVE word for its question, not merely two
# generic ones. Found the hard way: "who was Zaphenath the imaginary" matched who_is_jesus on
# {who, was} — a question about a made-up person answered with the Jesus answer. Generic tokens
# route nothing on their own.
_ANCHORS: Dict[str, Set[str]] = {
    "is_god_real": {"god"},
    "what_happens_when_we_die": {"die", "death", "dies", "died", "afterlife"},
    "why_bad_things": {"bad", "suffering", "evil", "unfair", "innocent"},
    "meaning_point": {"point", "meaning", "purpose", "empty", "meaningless", "pointless"},
    "how_forgive": {"forgive", "forgiveness"},
    "start_over": {"start", "restart", "second", "fresh", "ruined", "messed"},
    "does_god_care": {"god"},
    "who_is_jesus": {"jesus", "christ"},
    "how_to_pray": {"pray", "prayer", "praying"},
    "good_enough": {"god", "worthy", "worthless"},
    "why_trust_bible": {"bible"},
    "so_much_evil": {"evil", "wicked", "cruelty"},
}


def match(text: str) -> Optional[Dict[str, Any]]:
    """The great question this text is asking, or None. Two rules, both required: ≥2 overlapping
    tokens (mundane text can never match) AND at least one ANCHOR word for that question (generic
    words like 'who'/'was' route nothing on their own)."""
    toks = _toks(text)
    if len(toks) < 2:
        return None
    best, score = None, 0
    for q in QUESTIONS:
        anchors = _ANCHORS.get(q["id"], set())
        if anchors and not (toks & anchors):
            continue
        s = len(toks & q["keywords"])
        if s > score:
            best, score = q, s
    if best is None or score < 2:
        return None
    return {"id": best["id"], "answer": best["answer"], "refs": best["refs"], "note": NOTE}


def all_refs() -> List[str]:
    out: List[str] = []
    for q in QUESTIONS:
        out.extend(q["refs"])
    return out


__all__ = ["match", "all_refs", "QUESTIONS", "NOTE"]
