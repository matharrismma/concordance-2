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
        "cues": ["final judgment", "end of the age", "will i be judged", "sorted out",
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
    # ── the register, extended toward Christ's full set (2026-10-17, issue #18): every story verbatim (WEB),
    # His own turn where He gave one; cues are the aches it answers, in a person's words.
    {
        "id": "par_lost_coin", "story_ref": "Luke 15:8-10", "turn_ref": "Luke 15:10",
        "theme": "woman coin lost lamp swept house searched found rejoice friends one sinner repents",
        "cues": ["lost something precious", "swept the house", "searching everywhere",
                 "turned the house upside down", "found what i lost", "lost coin", "one small thing lost",
                 "searched all night", "rejoice with me", "does one person matter", "does one soul matter"],
    },
    {
        "id": "par_pharisee_tax_collector", "story_ref": "Luke 18:9-14", "turn_ref": "Luke 18:14",
        "theme": "pharisee tax collector temple prayer proud humble justified mercy sinner exalted",
        "cues": ["better than them", "at least im not", "at least i'm not", "not like those people", "look down on",
                 "self righteous", "holier than thou", "god be merciful to me", "im a sinner", "i'm a sinner",
                 "proud of my goodness", "judging others", "compare myself to others", "beating my chest"],
    },
    {
        "id": "par_persistent_widow", "story_ref": "Luke 18:1-8", "turn_ref": "Luke 18:6-8",
        "theme": "widow judge persistent plead justice delay pray always not lose heart",
        "cues": ["keep praying", "god isn't answering", "god isnt answering", "prayed for years", "give up praying",
                 "unanswered prayer", "keep asking", "no answer to prayer", "stop praying", "lose heart",
                 "losing heart", "how long must i pray", "persistent prayer", "nagging god", "pray and not give up"],
    },
    {
        "id": "par_friend_midnight", "story_ref": "Luke 11:5-8", "turn_ref": "Luke 11:9-10",
        "theme": "friend midnight bread knock persistence ask seek knock opened given",
        "cues": ["ask boldly", "keep knocking", "bother god", "bothering god", "ashamed to ask god",
                 "too small to ask", "knock and it will be opened", "ask and it will be given", "persist in asking",
                 "shameless asking", "can i ask god for"],
    },
    {
        "id": "par_two_builders", "story_ref": "Matthew 7:24-27", "turn_ref": "",
        "theme": "wise foolish builders rock sand house rain floods winds hears does words fall",
        "cues": ["built on sand", "built my life on", "when the storm comes", "house on the rock",
                 "solid foundation", "everything collapsed", "my foundation", "what am i building on", "storm hit",
                 "rock or sand", "hear but don't do", "hear but dont do", "foundation", "my life fell apart when"],
    },
    {
        "id": "par_workers_vineyard", "story_ref": "Matthew 20:1-16", "turn_ref": "Matthew 20:15-16",
        "theme": "landowner laborers vineyard hours denarius last first generous envy fair",
        "cues": ["not fair", "it's not fair", "its not fair", "they got the same", "i worked harder",
                 "unfair that they", "late in life", "deathbed conversion", "worked all day", "last minute faith",
                 "came to faith late", "same reward", "why do they get", "envious", "generous to them"],
    },
    {
        "id": "par_ten_virgins", "story_ref": "Matthew 25:1-13", "turn_ref": "Matthew 25:13",
        "theme": "virgins lamps oil bridegroom delayed slept ready door shut watch",
        "cues": ["be ready", "not ready", "caught unprepared", "ran out of oil", "too late to prepare", "keep watch",
                 "ready for his return", "fell asleep waiting", "wasn't ready", "wasnt ready", "unprepared",
                 "the door was shut"],
    },
    {
        "id": "par_two_sons", "story_ref": "Matthew 21:28-32", "turn_ref": "Matthew 21:31-32",
        "theme": "two sons vineyard said no went said yes did not obeyed will of father",
        "cues": ["said i would", "said yes but", "never followed through", "talk is cheap", "actions not words",
                 "promised god", "said i'd go", "said id go", "all talk", "didn't follow through",
                 "didnt follow through", "say one thing do another", "changed my mind and went"],
    },
    {
        "id": "par_wicked_tenants", "story_ref": "Matthew 21:33-41", "turn_ref": "Matthew 21:42-44",
        "theme": "vineyard tenants servants beaten son killed owner stone builders rejected cornerstone",
        "cues": ["rejected the son", "reject the messenger", "killed the prophets",
                 "the stone the builders rejected", "cornerstone", "stole the inheritance",
                 "rejected by the builders", "they killed the son"],
    },
    {
        "id": "par_wedding_banquet", "story_ref": "Matthew 22:1-14", "turn_ref": "Matthew 22:14",
        "theme": "king wedding feast invited refused garment called chosen",
        "cues": ["too busy for god", "invited but", "declined the invitation", "many are called", "few are chosen",
                 "wedding garment", "not dressed for", "busy with my farm", "busy with business",
                 "turned down the invitation", "refused the invitation"],
    },
    {
        "id": "par_great_banquet", "story_ref": "Luke 14:16-24", "turn_ref": "Luke 14:24",
        "theme": "great supper invited excuses field oxen married poor crippled compel fill house",
        "cues": ["made excuses", "excuses not to come", "bought a field", "just got married", "compel them to come",
                 "the poor and the crippled", "fill my house", "no time for the feast",
                 "something more important than", "i'll come later", "ill come later", "excuse after excuse"],
    },
    {
        "id": "par_faithful_servant", "story_ref": "Matthew 24:45-51", "turn_ref": "",
        "theme": "faithful wise servant master household food delayed returns unexpected reward",
        "cues": ["while the master is away", "when the master returns", "faithful while waiting",
                 "living like he won't come back", "living like he wont come back", "he's delaying", "hes delaying",
                 "taking advantage while", "faithful servant", "put in charge of", "beating the servants",
                 "nobody is watching"],
    },
    {
        "id": "par_unjust_steward", "story_ref": "Luke 16:1-9", "turn_ref": "Luke 16:10-13",
        "theme": "manager accused shrewd debtors reduced faithful little much mammon two masters",
        "cues": ["shrewd", "use money wisely", "worldly wealth", "faithful with little", "faithful in small things",
                 "serve two masters", "god and money", "mammon", "unrighteous mammon", "make friends with money",
                 "dishonest manager", "about to be fired", "fired from my job and"],
    },
    {
        "id": "par_rich_man_lazarus", "story_ref": "Luke 16:19-31", "turn_ref": "",
        "theme": "rich man lazarus beggar gate sores died abraham bosom torment chasm warn brothers moses prophets",
        "cues": ["ignored the poor", "beggar at my gate", "after death", "too late to change", "warn my family",
                 "warn my brothers", "great chasm", "the rich man and lazarus", "lazarus", "fine linen",
                 "feasted every day", "what happens after death", "moses and the prophets",
                 "if someone came back from the dead"],
    },
    {
        "id": "par_two_debtors", "story_ref": "Luke 7:41-43", "turn_ref": "Luke 7:47",
        "theme": "creditor two debtors forgave both loves more much little sins many",
        "cues": ["forgiven much", "forgiven more", "loves much", "love little", "owe more", "the one forgiven more",
                 "who loves more", "forgiven little", "my sins are many", "she loved much", "washed his feet",
                 "forgiven so much"],
    },
    {
        "id": "par_barren_fig", "story_ref": "Luke 13:6-9", "turn_ref": "",
        "theme": "fig tree vineyard fruit three years cut down one more year dig fertilize",
        "cues": ["one more year", "no fruit", "fruitless", "cut it down", "second chance", "another chance",
                 "give it another year", "dig around it", "fertilize", "bearing no fruit", "still no fruit",
                 "wasting the ground", "why hasn't my life produced", "why hasnt my life produced"],
    },
    {
        "id": "par_counting_cost", "story_ref": "Luke 14:28-33", "turn_ref": "Luke 14:33",
        "theme": "tower cost build finish king war ten thousand renounce disciple",
        "cues": ["can i afford to follow", "what will it cost me", "build the tower", "started building",
                 "half built", "half finished", "couldn't finish", "couldnt finish", "ran out of money to finish",
                 "estimate the cost", "king going to war", "afford to finish", "unable to finish",
                 "started something i cant finish", "started something i can't finish"],
    },
    {
        "id": "par_lamp", "story_ref": "Matthew 5:14-16", "turn_ref": "Matthew 5:16",
        "theme": "light world city hill lamp basket stand shine good works glorify father",
        "cues": ["hide my faith", "keep my faith private", "let my light shine", "afraid to be seen",
                 "light under a basket", "lamp under a bushel", "city on a hill", "hide my light", "private faith",
                 "afraid to share my faith", "shine before others", "keep it to myself"],
    },
    {
        "id": "par_new_wine", "story_ref": "Luke 5:36-39", "turn_ref": "",
        "theme": "new garment old patch new wine old wineskins burst new skins old better",
        "cues": ["old ways", "new life old habits", "can't patch the old", "cant patch the old", "new wineskins",
                 "old wineskins", "new patch on old", "mixing old and new", "the old is better",
                 "go back to the old", "new wine", "old habits die"],
    },
    {
        "id": "par_seed_secretly", "story_ref": "Mark 4:26-29", "turn_ref": "",
        "theme": "seed ground sleep rise sprout grows knows not how blade ear full grain harvest sickle",
        "cues": ["can't see growth", "cant see growth", "how does faith grow", "growing without me",
                 "sleep and rise", "he knows not how", "first the blade", "slow growth", "growing underground",
                 "nothing happening yet", "harvest will come", "patient growth", "is anything growing"],
    },
    {
        "id": "par_sheep_goats", "story_ref": "Matthew 25:31-46", "turn_ref": "Matthew 25:40",
        "theme": "son of man glory nations sheep goats right left hungry thirsty stranger naked sick prison least of these",
        "cues": ["least of these", "did it to me", "didn't help the hungry", "didnt help the hungry",
                 "visited the prisoner", "clothed the naked", "i was hungry", "a stranger and you",
                 "the sheep and the goats", "sheep and goats", "separate the sheep", "inherit the kingdom",
                 "depart from me", "when did we see you", "fed the hungry"],
    },
    {
        "id": "par_good_shepherd", "story_ref": "John 10:11-16", "turn_ref": "",
        "theme": "good shepherd lays down life sheep hired hand wolf knows own one flock",
        "cues": ["lays down his life", "hired hand", "knows my name", "knows his sheep", "the good shepherd",
                 "hired hand runs", "wolf comes", "one flock one shepherd", "other sheep", "i know my own",
                 "does he know me", "a shepherd who stays"],
    },
    {
        "id": "par_vine", "story_ref": "John 15:1-8", "turn_ref": "John 15:5",
        "theme": "true vine farmer branches prune fruit abide apart nothing withered glorified",
        "cues": ["apart from him", "abide in him", "remain in him", "bear fruit", "bearing fruit", "abide in me",
                 "pruned", "pruning", "cut off from the vine", "branch that bears no fruit", "fruitful",
                 "remain in me", "without him i can do nothing", "connected to the vine", "why am i being pruned"],
    },
    {
        "id": "par_unworthy_servants", "story_ref": "Luke 17:7-10", "turn_ref": "Luke 17:10",
        "theme": "servant plowing serve table thank duty unworthy servants done what ought",
        "cues": ["done my duty", "deserve credit", "god owes me", "earned it", "deserve thanks", "unworthy servants",
                 "only done what we ought", "expect a reward for serving", "shouldn't god be grateful",
                 "shouldnt god be grateful", "i've served so long", "ive served so long"],
    },
    {
        "id": "par_children_market", "story_ref": "Matthew 11:16-19", "turn_ref": "Matthew 11:19",
        "theme": "generation children marketplaces flute dance mourn john neither wisdom justified",
        "cues": ["cant win with them", "can't win with them", "criticized either way", "damned if i do",
                 "nothing pleases them", "we played the flute", "never satisfied with", "whatever i do is wrong",
                 "no pleasing them"],
    },
    {
        "id": "par_empty_house", "story_ref": "Matthew 12:43-45", "turn_ref": "Matthew 12:45",
        "theme": "unclean spirit returns house empty swept seven spirits worse last state",
        "cues": ["relapsed", "worse than before", "went back to my old", "seven other spirits",
                 "swept and put in order", "fell back into", "the last state worse", "empty and swept",
                 "cleaned up but empty", "back where i started but worse", "worse off than before"],
    },
    {
        "id": "par_speck_beam", "story_ref": "Matthew 7:3-5", "turn_ref": "Matthew 7:5",
        "theme": "speck brother eye beam own eye hypocrite remove first see clearly",
        "cues": ["speck in their eye", "log in my eye", "plank in my own eye", "judging their small",
                 "fix myself first", "pointing out their faults", "beam in my eye", "their faults not mine",
                 "remove the beam", "hypocrite", "see clearly to remove"],
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
