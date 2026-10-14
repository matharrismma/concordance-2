"""THE PARABLE REGISTER — "the exact right parable for the situation" (the end goal, Matt 2026-10-14).

Christ taught in parables — "without a parable he didn't speak to them" (Matthew 13:34). The parable is
the final register of the wisdom engine (front-load -> recall -> NARROW -> PARABLE): a story the hearer
walks INTO and discovers himself inside, so wisdom is imparted, not lectured. This module answers a
situation with the ONE of Christ's parables whose SHAPE fits it — and, where Christ gave the meaning
Himself, His own explanation as the turn.

THE LINE (composition layer): we never WRITE a parable. We FIND the one whose shape already fits and
present it VERBATIM, cited. The authored artifact here is only the INDEX — which ache each parable
answers (the cues), and where Christ explained it (the turn ref). That index is the operator's
discernment (Matt curates; this is a first pass), found and auditable, exactly like teachings._CUES.
Every word shown is resolved live from the canon (WEB), never generated. A situation with no fitting
parable gets honest silence — never a forced one.

  parable.for_situation(text)  -> the fitting parable {id,title,story,turn,theme,...} or None
  parable.walk(text)           -> the walked arc (meet -> story -> turn -> step), verbatim, or None

The companion beneath the parable — Matt's own narrative, FOUND and fit, spoken in his cloned voice —
is the caller's to attach (voice.illustrate); a story surface is where his narrative voice belongs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .teachings import _BY_ID, _stem, _topic_stems  # one stemmer, one queue — the same Red

# ── THE REGISTER — Christ's twelve parables, each with the narrative, His own turn, and the ache it
# answers. id matches teachings._QUEUE (the same Words in Red). story_ref / turn_ref are resolved live.
#   story_ref — the narrative verses (may trim the "why I speak in parables" aside).
#   turn_ref  — Christ's OWN explanation or application, verbatim; "" where He left it to sit whole.
#   theme     — a short FOUND descriptor (nouns of the parable's shape), for fitting the companion.
#   cues      — the aches it answers, in the words a person brings (phrases are strong; bare words weak).
_PARABLES: List[Dict[str, Any]] = [
    {
        "id": "par_prodigal", "story_ref": "Luke 15:11-32", "turn_ref": "Luke 15:31-32",
        "theme": "son father return home shame welcome forgiveness wasted lost found",
        "cues": ["wasted my life", "wasted everything", "squandered", "ashamed to come", "ashamed to go back",
                 "too ashamed", "ran away", "came back", "come home", "far from home", "estranged",
                 "prodigal", "ruined everything", "am i too far gone", "can i come back", "does god still want me",
                 "unworthy", "my son left", "my daughter left", "shame", "wasted"],
    },
    {
        "id": "par_lost_sheep", "story_ref": "Luke 15:3-7", "turn_ref": "Luke 15:7",
        "theme": "shepherd sheep lost wandered sought found rejoicing one repents",
        "cues": ["far from god", "drifting away", "drifting from", "drifted away", "backslidden", "strayed",
                 "wandered", "wandered off", "lost my faith", "lost my way", "fallen away", "left the church",
                 "am i too far", "does god still look for me", "walked away from god"],
    },
    {
        "id": "par_samaritan", "story_ref": "Luke 10:25-37", "turn_ref": "Luke 10:36-37",
        "theme": "neighbor mercy stranger wounded road priest help compassion enemy crossed",
        "cues": ["who is my neighbor", "who's my neighbor", "do i have to help", "should i help",
                 "not my problem", "not my people", "they're not my", "passed by", "crossed the road",
                 "ignored them", "help a stranger", "mercy", "walked past", "someone in need"],
    },
    {
        "id": "par_talents", "story_ref": "Matthew 25:14-30", "turn_ref": "Matthew 25:29-30",
        "theme": "servant talents entrusted invest buried fear return stewardship use gift",
        "cues": ["afraid to use", "afraid to try", "buried my gift", "bury my gift", "waste my gift",
                 "wasting my gift", "what if i fail", "playing it safe", "too scared to try", "hide my gift",
                 "buried my talent", "use what i have", "squander my talent", "potential", "stewardship",
                 "afraid of failing"],
    },
    {
        "id": "par_unforgiving", "story_ref": "Matthew 18:23-35", "turn_ref": "Matthew 18:35",
        "theme": "servant debt forgiven unforgiving mercy king settle accounts brother",
        "cues": ["cant forgive", "can't forgive", "unable to forgive", "forgive", "bitterness", "bitter",
                 "grudge", "resentment", "resentful", "they hurt me", "wont let it go", "won't let it go",
                 "hold it against", "holding a grudge"],
    },
    {
        "id": "par_rich_fool", "story_ref": "Luke 12:16-21", "turn_ref": "Luke 12:21",
        "theme": "rich man barns harvest security soul tonight treasure not rich toward god",
        "cues": ["enough saved", "saved up", "enough money", "feel secure", "financially secure", "nest egg",
                 "retirement", "store up", "storing up", "bigger barns", "hoarding", "set for life",
                 "money will make me safe", "just want to be safe", "enough to feel safe"],
    },
    {
        "id": "par_sower", "story_ref": "Matthew 13:3-9", "turn_ref": "Matthew 13:18-23",
        "theme": "farmer seed soil path rocky thorns good ground word root fruit choke",
        "cues": ["faith keeps dying", "doesnt take root", "doesn't take root", "no roots", "falls away",
                 "cares of the world", "worries choke", "distracted from god", "excited then nothing",
                 "it doesnt stick", "it doesn't stick", "shallow faith", "hear but forget", "fizzles out"],
    },
    {
        "id": "par_weeds", "story_ref": "Matthew 13:24-30", "turn_ref": "Matthew 13:36-43",
        "theme": "wheat weeds field enemy sowed harvest grow together end age separated",
        "cues": ["why evil", "why does god let evil", "evil grows", "wicked prosper", "why doesnt god stop",
                 "why doesn't god stop", "good and bad together", "church full of hypocrites",
                 "why are there hypocrites", "evil next to", "injustice in the world", "let them grow"],
    },
    {
        "id": "par_dragnet", "story_ref": "Matthew 13:47-48", "turn_ref": "Matthew 13:49-50",
        "theme": "net fish sea gathered good bad sorted end age judgment separated",
        "cues": ["final judgment", "end of the age", "will i be judged", "sorted out", "sheep and goats",
                 "who gets in", "separated out"],
    },
    {
        "id": "par_mustard", "story_ref": "Matthew 13:31-32", "turn_ref": "",
        "theme": "mustard seed smallest grows greatest tree birds kingdom small beginning",
        "cues": ["too small to matter", "small beginning", "feels insignificant", "nothing i do matters",
                 "just a seed", "feels pointless", "it's so small", "its so small", "doesnt feel like enough",
                 "little faith"],
    },
    {
        "id": "par_leaven", "story_ref": "Matthew 13:33", "turn_ref": "",
        "theme": "leaven yeast meal hidden works through whole kingdom unseen slow",
        "cues": ["no visible progress", "working quietly", "behind the scenes", "unseen work",
                 "nothing is changing", "slow growth", "hidden work"],
    },
    {
        "id": "par_treasure", "story_ref": "Matthew 13:44-46", "turn_ref": "",
        "theme": "treasure field pearl merchant sold all joy worth kingdom found hidden",
        "cues": ["is it worth it", "worth giving up", "give up everything", "sacrifice everything",
                 "sell everything", "worth the cost", "count the cost", "all in", "worth losing"],
    },
]
_BY_PAR = {p["id"]: p for p in _PARABLES}

# The fixed connective frames — the CRAFT (the voice that walks), never a claim. The claims are the
# verbatim Red; these only carry the reader between them. Kept minimal and constant.
_MEET = "Jesus told a story for this. Here it is, in his own words —"
_TURN_LEAD = "And he told them what it means —"
_SIT = "He left this one to sit. Read it once more, slowly."
_STEP = "Now read it again, and ask: where am I in the story?"


def _passage(ref: str) -> str:
    """The verbatim WEB text of a reference, or '' — the one shared, cached resolver (never generated)."""
    if not (ref or "").strip():
        return ""
    try:
        from .verifiers.scripture import passage_text
        return (passage_text(ref) or "").strip()
    except Exception:  # noqa: BLE001 — a ref the engine can't resolve is an honest empty, never a crash
        return ""


def for_situation(text: str, *, resolve: bool = True) -> Optional[Dict[str, Any]]:
    """The ONE parable whose shape fits this situation — matched on the curated ache index (the
    operator's discernment, found not generated). A PHRASE cue (multi-word) is strong and fits alone; a
    bare WORD cue is weak and needs a second hit, so a lone common word ("money", "shame") cannot pull a
    parable in by accident. No fit -> None (honest silence; the caller keeps its own flow). When resolve,
    the verbatim story + turn come back with it."""
    low = " " + (text or "").lower().strip() + " "
    q = set(_topic_stems(text))
    if not q:
        return None
    best, best_score, best_strong = None, 0, 0
    for p in _PARABLES:
        phrase_hits = word_hits = 0
        for c in p["cues"]:
            if " " in c:
                if c in low:
                    phrase_hits += 1
            elif _stem(c) in q:
                word_hits += 1
        strong = phrase_hits
        score = phrase_hits * 3 + word_hits
        # PRECISION GUARD — a parable fires only on a phrase cue, or on two distinct word cues. One bare
        # word is never enough (keeps the register 0-false-positive: a factual query finds no parable).
        if phrase_hits < 1 and word_hits < 2:
            continue
        if (strong, score) > (best_strong, best_score):
            best, best_score, best_strong = p, score, strong
    if not best:
        return None
    t = _BY_ID.get(best["id"], {})
    out: Dict[str, Any] = {
        "id": best["id"], "title": t.get("title", best["id"]), "group": "The Parables",
        "story_ref": best["story_ref"], "turn_ref": best["turn_ref"], "theme": best["theme"],
        "score": best_score, "red": True,
    }
    if resolve:
        out["story"] = _passage(best["story_ref"])
        out["turn"] = _passage(best["turn_ref"]) if best["turn_ref"] else ""
    return out


def walk(text: str) -> Optional[Dict[str, Any]]:
    """The walked parable experience: meet -> the story (verbatim) -> the turn (Christ's own, where he
    gave it) -> one step. All claims found and cited; only the thin connective frames are composed. The
    companion (Matt's narrative, fit and voiced) is attached by the caller. None where no parable fits."""
    fit = for_situation(text, resolve=True)
    if not fit or not fit.get("story"):
        return None
    turn = None
    if fit.get("turn"):
        turn = {"lead": _TURN_LEAD, "ref": fit["turn_ref"], "text": fit["turn"]}
    return {
        "id": fit["id"], "title": fit["title"], "red": True, "theme": fit["theme"],
        "meet": _MEET,
        "story": {"ref": fit["story_ref"], "text": fit["story"], "attribution": "Christ Himself"},
        "turn": turn,                       # None -> the parable sits whole
        "sit": None if turn else _SIT,
        "step": _STEP,
    }


def all_parables() -> List[Dict[str, Any]]:
    """The register, for coverage checks and the surface's index — titles + refs, no resolve."""
    return [{"id": p["id"], "title": _BY_ID.get(p["id"], {}).get("title", p["id"]),
             "story_ref": p["story_ref"], "turn_ref": p["turn_ref"], "theme": p["theme"],
             "cue_count": len(p["cues"])} for p in _PARABLES]


__all__ = ["for_situation", "walk", "all_parables"]
