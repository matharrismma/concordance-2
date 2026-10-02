"""Principles — the stated rules of those who repeatedly won, gathered from their own public-domain
words, TAGGED to the Strategy Concordance's patterns, and APPLIED to a present situation.

Matt, 2026-10-02: "We have figures like Napoleon, Churchill, and Ford. Many others. They have
principles and patterns that have repeatedly been proven successful. We need a mechanism to
identify and tag those principles. Then apply them to current context."

The mechanism, in the house discipline (gather, don't author; found, not generated; every
relation carries its evidence; a gap stays a gap):

  IDENTIFY  A principle is a sentence the figure WROTE in a public-domain work that carries a
            normative cue — a maxim shape ("never…", "the first rule of…", "the secret of… is to…")
            — or that the author himself labelled a maxim (Napoleon's numbered MAXIMs). Verbatim,
            attributed to work + year + Gutenberg number. Nothing paraphrased, nothing invented;
            the cue that selected each sentence rides on the card so the selection is auditable.
  TAG       Each principle is tagged to the Strategy Concordance's PATTERNS (tools/seed_strategy.py:
            concentrate_force, tempo, intelligence, …) by a fixed stem lexicon — the same lexical
            resolution the front door uses for domains. A principle no pattern claims is kept and
            flagged `pattern: none`: an honest gap, and a candidate for a pattern not yet named.
  PROVE     "Repeatedly proven" is a COUNT, not an adjective: for a pattern, how many DISTINCT
            figures state it in their own words, across how many arenas, with how many dated
            cases (the Concordance's instances, each with evidence). The bar for "proven" is the
            Concordance's own bar for a bridge: ≥2 figures AND ≥2 arenas.
  APPLY     A present situation is resolved to patterns by the same lexicon, and the answer is the
            pattern's gist, its proof counts, the figures' verbatim principles under it, and the
            dated cases — ranked by proof. Deterministic, model-free; found=False when nothing in
            the situation matches a pattern (never a guess).

What this is NOT: a verdict that a principle is true. It is a measured record of who said it, in
which arena, how often it won, and where to read it. Discernment stays with the reader and the gate.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ── the pattern lexicon: Strategy Concordance pattern id -> stems that name the move ─────────────
# Stems are matched as word-prefixes on lowercase text (concentrat → concentrate/concentrated/…).
# Multi-word stems match as phrases. Kept TIGHT: each stem should name the move, not merely co-occur.
# ── the pattern lexicon: Strategy Concordance pattern id -> stems that name the move, in the FIGURES'
# own vocabulary (what their public-domain texts say). Word-prefix / phrase match on lowercase text.
PATTERN_LEXICON: Dict[str, List[str]] = {
    'concentrate_force': ['concentrat', 'decisive point', 'mass of', 'masses', 'superior force', 'superiority', 'unite the', 'unite your', 'unite all', 'unite his', 'united force', 'united effort', 'divide the enemy', 'single point', 'whole force', 'all your forces', 'collect your', 'with all his forces', 'entire force'],
    'tempo': ['rapid', 'rapidity', 'celerity', 'speed', 'swift', 'quick', 'promptitude', 'promptness', 'lose no time', 'not a moment', 'delay', 'hesitat', 'at once', 'without delay', 'time is'],
    'own_the_bottleneck': ['line of communication', 'lines of communication', 'line of operation', 'supply', 'supplies', 'depot', 'magazine', 'bridge', 'defile', 'pass of', 'control of the'],
    'asymmetric_leverage': ['surprise', 'unexpected', 'small force', 'inferior force', 'with few', 'weaker', 'feint', 'deceive', 'deception', 'stratagem'],
    'compounding': ['little by little', 'accumulat', 'compound', 'year after year', 'steady', 'perseverance', 'persever', 'patience', 'patient', 'long run', 'small beginnings'],
    'founder_conviction': ['resolution', 'resolve', 'determination', 'determined', 'firmness', 'courage', 'boldness', 'bold', 'will to', 'faith in', 'conviction', 'never give'],
    'antifragility': ['adversity', 'misfortune', 'defeat', 'failure', 'mistakes', 'learn from', 'setback', 'hardship', 'obstacle'],
    'distribution_over_product': ['customer', 'market', 'price', 'cheap', 'sell', 'selling', 'sales', 'consumer', 'buyer', 'reach the customer', 'reach the market'],
    'win_the_narrative': ['opinion', 'morale', 'moral force', 'confidence of', 'reputation', 'spirit of the', 'enthusiasm', 'persuad', 'proclamation', 'hearts', 'inspire'],
    'outlive_the_founder': ['successor', 'succession', 'institution', 'after my death', 'posterity', 'endure', 'lasting', 'outlast'],
    'first_principles': ['first principle', 'fundamental', 'nature of things', 'think for', 'the truth is', 'underlying', 'root of', 'go to the root', 'cause and effect', 'from the ground up'],
    'coalition': ['alliance', 'allies', 'ally', 'coalition', 'confederat', 'in union with', 'act in union', 'co-operat', 'cooperat', 'together with', 'partner'],
    'requisite_variety': ['adapt', 'circumstances', 'terrain', 'nature of the ground', 'flexib', 'vary', 'varies', 'modif', 'suit the', 'lie of the land'],
    'build_a_moat': ['fortif', 'entrench', 'defensive position', 'defend', 'barrier', 'stronghold', 'impregnable', 'rampart'],
    'intelligence': ['information', 'reconnai', 'reconnoit', 'spies', 'spy', 'scout', 'intelligence', 'know the enemy', 'know your', 'observe', 'observation', 'foresee', 'foresight'],
    'cut_losses': ['retreat', 'withdraw', 'abandon', 'fall back', 'sacrifice a', 'cut your losses', 'know when to', 'give way'],
    'standardize': ['standard', 'uniform', 'interchangeable', 'systematic', 'routine', 'discipline', 'drill', 'one way of', 'same way'],
    'decentralize': ['initiative', 'delegat', 'on the spot', 'his own judgment', 'let each', 'trust the man', 'independent command', 'subordinate commander'],
    'reinvest_the_core': ['reinvest', 'put back', 'back into the business', 'surplus', 'plough', 'plow back', 'profits should', 'profits are', 'improve the'],
}

# ── the situation side: a PRESENT context speaks modern words for the same moves ("move fast", "sunk
# cost", "moat"). Used only when resolving a situation (apply), never when tagging a figure's text —
# so modern idiom cannot mis-tag an 1831 maxim, and an 1831 word cannot be required of a shop owner.
SITUATION_STEMS: Dict[str, List[str]] = {
    'concentrate_force': ['focus on one', 'one product', 'one market', 'one thing', 'niche', 'all in on', 'spread too thin'],
    'tempo': ['move fast', 'fast', 'faster', 'before they', 'react', 'first mover', 'head start', 'slow'],
    'asymmetric_leverage': ['small shop', 'small team', 'underdog', 'incumbent', 'bigger rival', 'larger competitor', 'outnumbered', 'leverage'],
    'build_a_moat': ['moat', 'lock-in', 'switching cost', 'defensib', 'hard to copy'],
    'distribution_over_product': ['channel', 'go to market', 'dealer', 'retail'],
    'cut_losses': ['sunk cost', 'walk away', 'pull out', 'shut it down', 'kill the'],
    'intelligence': ["don't know", 'do not know', 'find out', 'research', 'data on', 'what the customer'],
    'decentralize': ['micromanag', 'bottleneck on me', 'empower', 'autonomy', 'decisions at the edge'],
    'coalition': ['team up', 'join forces', 'joint venture', 'divided', 'hold together', 'quarrel', 'faction', 'united front', 'our side', 'infighting'],
    'compounding': ['long game', 'slow and steady', 'consistent', 'every day', 'daily'],
    'antifragility': ['failed', 'we lost', 'went wrong', 'crisis', 'downturn', 'recession'],
    'standardize': ['checklist', 'process', 'repeatable', 'procedure', 'template'],
    'outlive_the_founder': ['depends on me', "when i'm gone", 'handoff', 'second generation'],
    'founder_conviction': ['everyone says', "told it can't", 'nobody believes', 'doubt', 'keep going'],
    'win_the_narrative': ['story', 'brand', 'messag', 'press', 'perception', 'trust us', 'reach the people', 'the people', 'hearts and minds', 'win over'],
    'requisite_variety': ['changed', 'changing', 'new market', 'pivot', 'different rules', 'local'],
    'own_the_bottleneck': ['chokepoint', 'single supplier', 'depend on one', 'gatekeeper', 'platform'],
    'reinvest_the_core': ['flywheel', 'what to do with the profit', 'cash flow', 'dividend'],
    'first_principles': ['from scratch', 'why does', 'assumption', 'conventional wisdom', 'everyone assumes'],
}

# ── the normative cues that make a sentence a candidate PRINCIPLE (the maxim shape) ────────────────
_CUES: List[Tuple[str, re.Pattern]] = [
    ("never", re.compile(r"\bnever\b", re.I)),
    ("always", re.compile(r"\balways\b", re.I)),
    ("must", re.compile(r"\b(?:must|ought to|should)\b", re.I)),
    ("first rule", re.compile(r"\bthe (?:first|great|golden|whole|only|chief|supreme) (?:rule|principle|law|duty|secret|art|object|maxim|thing)\b", re.I)),
    ("the secret of", re.compile(r"\bthe (?:secret|art|essence|whole) of\b", re.I)),
    ("nothing is more", re.compile(r"\bnothing is (?:more|so)\b", re.I)),
    ("it is essential", re.compile(r"\bit is (?:essential|necessary|better|wiser|important|a mistake|an error|fatal|dangerous)\b", re.I)),
    ("a maxim", re.compile(r"\b(?:maxim|precept|rule|principle)\b", re.I)),
    ("he who", re.compile(r"\b(?:he|a man|a general|a leader|a commander|a business|whoever) (?:who|that|which)\b", re.I)),
    ("cannot", re.compile(r"\bcannot\b", re.I)),                      # "a house divided against itself cannot stand"
    ("let us", re.compile(r"\blet us\b", re.I)),                      # "let us strive on to finish the work we are in"
    ("is to", re.compile(r"\b(?:the|a) (?:way|means|key|only way) (?:to|of)\b", re.I)),
]
_WORD = re.compile(r"[a-z]+")
# A principle is GENERAL. A memoir sentence that happens to carry "always"/"never" ("I could always
# sleep") is narrative, not a rule — first-person sentences are dropped unless the author labelled the
# block a maxim or the cue is itself a rule-frame ("the first rule of…", "the secret of…").
_FIRST_PERSON = re.compile(r"\b(?:I|I'd|I'll|I've|me|my|mine|myself|we|we'd|we're|we've|us|our|ours|ourselves)\b")
_RULE_FRAMES = {"first rule", "the secret of", "nothing is more"}
# A memoir also narrates in the third person ("Scott at once had notices posted"): two or more
# past-tense narrative verbs mark a story being told, not a rule being stated.
_NARRATIVE = re.compile(r"\b(?:was|were|had|did|went|came|said|told|made|took|got|gave|saw|sent|wrote|arrived|replied)\b", re.I)
_NARRATIVE_MAX = 1
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
_MIN_WORDS, _MAX_WORDS = 8, 60


_CAPS_PREFIX = re.compile(r"^(?:[A-Z][A-Z'’\-]+[\s,:;.\-—]+){4,}(?=[A-Z][a-z])")   # a chapter heading glued to the first sentence
_TRAIL_NUM = re.compile(r"\s+(?:CHAP\.|\d{1,3}\.|[IVXLC]+\.)\s*$")                 # "… CHAP." / "… 2." (Legge's numbering)
_SIDENOTE = re.compile(r"\s*\[Sidenote:[^\]]*\]")


def _clean(s: str) -> str:
    """Strip edition furniture that is not the author's sentence: a run-on chapter heading, a trailing
    section number, an editor's [Sidenote]. The words that remain are still the author's, verbatim."""
    s = _SIDENOTE.sub("", s)
    s = _CAPS_PREFIX.sub("", s)
    s = _TRAIL_NUM.sub("", s)
    return s.strip()


def _is_heading(s: str) -> bool:
    """A table-of-contents line or chapter title: mostly capitals among its letters."""
    letters = [ch for ch in s if ch.isalpha()]
    return bool(letters) and sum(1 for ch in letters if ch.isupper()) / len(letters) > 0.4


def sentences(text: str) -> List[str]:
    """Plain sentence segmentation of a prose text (paragraph-joined, whitespace-normalised)."""
    flat = re.sub(r"\s+", " ", text.replace("\r", " "))
    return [s.strip() for s in _SENT_SPLIT.split(flat) if s.strip()]


def cues_of(sentence: str) -> List[str]:
    """The normative cues a sentence carries (empty = not a maxim shape)."""
    return [name for name, rx in _CUES if rx.search(sentence)]


def tag(sentence: str, *, situation: bool = False) -> Dict[str, List[str]]:
    """Strategy patterns the sentence names, with the stems that fired. Lexical, deterministic.
    `situation=True` adds the modern SITUATION_STEMS (for resolving a present context)."""
    low = " " + sentence.lower() + " "
    out: Dict[str, List[str]] = {}
    for pid, stems in PATTERN_LEXICON.items():
        if situation:
            stems = list(stems) + SITUATION_STEMS.get(pid, [])
        hit = [st for st in stems if (" " + st) in low or (" " + st) in low.replace("-", " ")]
        if hit:
            out[pid] = hit
    return out


def identify(text: str, *, labelled_blocks: Optional[Iterable[str]] = None,
             limit: int = 60) -> List[Dict[str, Any]]:
    """Candidate principles from a text: sentences of maxim shape (8-60 words, ≥1 normative cue),
    ranked by cue count then by number of patterns tagged. `labelled_blocks` (e.g. Napoleon's
    numbered MAXIMs) are accepted by construction — the author labelled them — cue or not."""
    found: List[Dict[str, Any]] = []
    seen = set()
    for blk in (labelled_blocks or []):
        first = sentences(blk)
        if not first:
            continue
        s = _clean(first[0])
        if not s or s in seen:
            continue
        seen.add(s)
        found.append({"quote": s, "cues": ["labelled maxim"] + cues_of(s), "patterns": tag(s), "labelled": True})
    for s in sentences(text):
        s = _clean(s)
        n = len(_WORD.findall(s.lower()))
        if n < _MIN_WORDS or n > _MAX_WORDS or s in seen or _is_heading(s):
            continue
        c = cues_of(s)
        if not c:
            continue
        if _FIRST_PERSON.search(s) and not (set(c) & _RULE_FRAMES):
            continue                                   # a memoir line, not a maxim
        if len(_NARRATIVE.findall(s)) > _NARRATIVE_MAX and not (set(c) & _RULE_FRAMES):
            continue                                   # a story being told, not a rule being stated
        seen.add(s)
        found.append({"quote": s, "cues": c, "patterns": tag(s), "labelled": False})
    found.sort(key=lambda d: (-int(d["labelled"]), -len(d["cues"]), len(_WORD.findall(d["quote"].lower())), d["quote"]))
    return found[:limit]


# ── the keeping side: principle cards + the Concordance's patterns and cases ─────────────────────
def _data_dir() -> Path:
    env = os.environ.get("CONCORDANCE_DATA_DIR")
    return Path(env) if env else Path(__file__).resolve().parent.parent.parent / "data"


def _load_jsonl(p: Path) -> List[dict]:
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def load_principles(data_dir: Optional[Path] = None) -> List[dict]:
    return [c for c in _load_jsonl((data_dir or _data_dir()) / "principle_cards.jsonl")
            if c.get("kind") == "principle"]


def load_patterns(data_dir: Optional[Path] = None) -> Tuple[Dict[str, dict], Dict[str, List[dict]]]:
    """pattern id -> pattern card; pattern id -> its case cards (from the Strategy Concordance)."""
    cards = _load_jsonl((data_dir or _data_dir()) / "strategy_cards.jsonl")
    pats = {c["id"].replace("card_pattern_", ""): c for c in cards if c.get("kind") == "strategy_pattern"}
    cases: Dict[str, List[dict]] = defaultdict(list)
    for c in cards:
        if c.get("kind") == "strategy_case":
            pid = (c.get("extra") or {}).get("pattern")
            if pid:
                cases[pid].append(c)
    return pats, cases


def load_counters(data_dir: Optional[Path] = None) -> Dict[str, List[dict]]:
    """pattern id -> the cases where the SAME move FAILED (strategy_counter cards)."""
    out: Dict[str, List[dict]] = defaultdict(list)
    for c in _load_jsonl((data_dir or _data_dir()) / "strategy_cards.jsonl"):
        if c.get("kind") == "strategy_counter":
            pid = (c.get("extra") or {}).get("pattern")
            if pid:
                out[pid].append(c)
    return out


def proof(pid: str, principles: List[dict], cases: Dict[str, List[dict]],
          counters: Optional[Dict[str, List[dict]]] = None) -> Dict[str, Any]:
    """The count that makes 'repeatedly proven' a measurement: distinct figures stating the pattern in
    their own words, distinct arenas (figures' + cases'), dated cases with evidence — AND the dated
    cases where the same move FAILED (the record is won–failed, never wins alone)."""
    mine = [p for p in principles if pid in ((p.get("extra") or {}).get("patterns") or [])]
    figures = sorted({(p.get("extra") or {}).get("figure", "?") for p in mine})
    arenas = {(p.get("extra") or {}).get("arena", "?") for p in mine}
    cs = cases.get(pid, [])
    arenas |= {(c.get("extra") or {}).get("arena", "?") for c in cs}
    arenas.discard("?")
    failed = (counters or {}).get(pid, [])
    return {"figures": len(figures), "who": figures, "arenas": sorted(arenas), "cases": len(cs),
            "counter_cases": len(failed), "record": f"{len(cs)}-{len(failed)}",
            "principles": len(mine), "proven": len(figures) >= 2 and len(arenas) >= 2,
            "bounded": len(failed) >= 1}


def apply(situation: str, *, limit: int = 3, per_pattern: int = 4,
          data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Resolve a present situation to the patterns it names and hand back, for each: the gist, the
    proof counts, the figures' own principles (verbatim, attributed) and the dated cases. Ranked by
    lexical hits then proof. found=False when the situation names no pattern — never a guess."""
    hits = tag(situation or "", situation=True)
    pats, cases = load_patterns(data_dir)
    counters = load_counters(data_dir)
    principles = load_principles(data_dir)
    if not hits:
        return {"found": False, "situation": situation, "patterns": [],
                "detail": "the situation names no pattern of the Strategy Concordance (no stem matched)"}
    ranked = []
    for pid, stems in hits.items():
        pr = proof(pid, principles, cases, counters)
        ranked.append((len(stems), pr["figures"] + pr["cases"], pid, stems, pr))
    ranked.sort(key=lambda t: (-t[0], -t[1], t[2]))
    out = []
    for _n, _p, pid, stems, pr in ranked[:limit]:
        pat = pats.get(pid, {})
        mine = [p for p in principles if pid in ((p.get("extra") or {}).get("patterns") or [])]
        mine.sort(key=lambda p: (-int(bool((p.get("extra") or {}).get("labelled"))),
                                 -len((p.get("extra") or {}).get("cues") or []), p.get("id", "")))
        # one principle per figure first (breadth of witness), then the rest
        by_fig: Dict[str, List[dict]] = defaultdict(list)
        for p in mine:
            by_fig[(p.get("extra") or {}).get("figure", "?")].append(p)
        picks: List[dict] = []
        for fig in sorted(by_fig):
            picks.append(by_fig[fig][0])
        for fig in sorted(by_fig):
            picks.extend(by_fig[fig][1:])
        out.append({
            "pattern": pid, "title": pat.get("title", pid), "gist": (pat.get("extra") or {}).get("gist", ""),
            "matched_on": stems, "proof": pr,
            "principles": [{"quote": p.get("body"), "figure": (p.get("extra") or {}).get("figure"),
                            "work": (p.get("extra") or {}).get("work"), "year": (p.get("extra") or {}).get("year"),
                            "url": (p.get("source") or {}).get("url"), "card": p.get("id")}
                           for p in picks[:per_pattern]],
            "cases": [{"who": (c.get("extra") or {}).get("who"), "when": (c.get("extra") or {}).get("when"),
                       "arena": (c.get("extra") or {}).get("arena"), "move": (c.get("extra") or {}).get("move"),
                       "card": c.get("id")} for c in cases.get(pid, [])[:per_pattern]],
            # the boundary: where the SAME move failed, and why — read these before applying the pattern
            "where_it_failed": [{"who": (c.get("extra") or {}).get("who"), "when": (c.get("extra") or {}).get("when"),
                                 "arena": (c.get("extra") or {}).get("arena"), "move": (c.get("extra") or {}).get("move"),
                                 "why": (c.get("extra") or {}).get("failed"), "card": c.get("id")}
                                for c in counters.get(pid, [])[:per_pattern]],
        })
    return {"found": True, "situation": situation, "patterns": out,
            "detail": f"{len(out)} pattern(s) named by the situation; proof = distinct figures × arenas × dated cases",
            "note": "gathered from public-domain works, verbatim and attributed; a measure of who said it and "
                    "how often it won — not a verdict that it is true for you"}
