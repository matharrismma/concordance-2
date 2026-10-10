"""A real, deterministic, offline syntax parser - no model, no network (Matt, 2026-10-10: "real
syntax parser"). It answers one honest question: does a sentence have a valid phrase-structure
parse under the engine's English grammar, given deterministic part-of-speech tags? It returns the
tree it found.

WHY THIS IS HONEST AND 0-FALSE-POSITIVE. The parser CONFIRMS only a derivation it actually built -
a structural fact about the grammar, stated as such ("a valid phrase-structure parse exists"),
never a judgment that the sentence is good English or true. Function words (the closed classes) are
tagged from fixed sets, so the skeleton of a sentence is pinned; a word with the wrong function
word in the wrong place has no parse and is reported as such. Content words (open class) are tagged
by a few reliable suffix cues and otherwise allowed to be a noun, verb, or adjective - the grammar,
constrained by the pinned function words, decides. This discriminates real structure from word
salad ("the cat sat" parses; "cat the sat" does not) without a POS lexicon.

THE LIMIT, NAMED. Open-class POS here is a heuristic, not a lexicon; a public-domain POS list
(e.g. Moby Part-of-Speech) would sharpen it and is the intended next step. Coordination (and/or
joining clauses) and long-distance dependencies are outside this grammar and simply do not parse -
an honest "not derivable here", never a wrong parse. The regex/rule verifiers remain the floor;
this is an addition, not a replacement.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

# The closed classes - pinned, finite, deterministic (kept here so the parser has no import cycle
# with the linguistics verifier).
_ARTICLE = {"a", "an", "the"}
_DET = _ARTICLE | {"this", "that", "these", "those", "some", "any", "each", "every", "all", "both",
                   "either", "neither", "no", "my", "your", "his", "her", "its", "our", "their",
                   "many", "much", "more", "most", "few", "several", "enough", "such"}
_PRON = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "mine",
         "yours", "hers", "ours", "theirs", "who", "whom", "which", "what", "myself", "yourself",
         "himself", "herself", "itself", "ourselves", "themselves", "someone", "anyone", "everyone",
         "nobody", "something", "anything", "everything", "nothing"}
_PREP = {"in", "on", "at", "by", "for", "with", "to", "of", "from", "into", "onto", "over", "under",
         "above", "below", "between", "through", "during", "before", "after", "against", "among",
         "around", "behind", "beside", "near", "upon", "within", "without", "toward", "across",
         "along", "about"}
_AUX = {"is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
        "did", "can", "could", "will", "would", "shall", "should", "may", "might", "must"}

# A word can hold several closed classes (that = determiner/pronoun). The parser keeps all; the
# grammar chooses. Open-class suffix cues are added on top.
_SUF_ADV = ("ly",)
_SUF_ADJ = ("ous", "ful", "ive", "able", "ible", "ical", "ic", "ish", "less", "ar", "ant", "ent")
_SUF_N = ("tion", "sion", "ness", "ity", "ment", "ance", "ence", "ship", "hood", "dom", "ism",
          "ist", "er", "or", "age")
_SUF_V = ("ize", "ise", "ify", "ate")

_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def tag(word: str) -> Set[str]:
    """The set of part-of-speech tags a token may take. Closed classes are pinned; open-class words
    get suffix cues plus the content baseline {N, V, ADJ}. Never empty for a real word."""
    w = str(word or "").strip().lower()
    tags: Set[str] = set()
    if w in _ARTICLE:
        tags.add("DET")
    if w in _DET:
        tags.add("DET")
    if w in _PRON:
        tags.add("PRON")
    if w in _PREP:
        tags.add("P")
    if w in _AUX:
        tags.add("AUX")
        tags.add("V")           # auxiliaries can head a VP as a copula/main verb too
    # open-class cues (added, not exclusive)
    if w.endswith(_SUF_ADV):
        tags.add("ADV")
    if w.endswith(_SUF_ADJ):
        tags.add("ADJ")
    if w.endswith(_SUF_N):
        tags.add("N")
    if w.endswith(_SUF_V):
        tags.add("V")
    # content baseline: a word that is not purely a function word can be N / V / ADJ
    if not ({"DET", "PRON", "P", "AUX"} & tags) or {"N", "V", "ADJ", "ADV"} & tags:
        tags |= {"N", "V", "ADJ"}
    return tags


# The grammar. Nonterminals are the keys; terminals are the POS tags. No epsilon productions, so
# the memoized recursive parser terminates (every recursive call is on a strictly smaller span).
GRAMMAR: Dict[str, List[Tuple[str, ...]]] = {
    "S":   [("NP", "VP")],
    "NP":  [("PRON",), ("NOM",), ("DET", "NOM"), ("NP", "PP")],
    "NOM": [("N",), ("ADJ", "NOM"), ("N", "N")],
    "VP":  [("V",), ("V", "NP"), ("V", "PP"), ("V", "NP", "PP"), ("AUX", "VP"),
            ("VP", "PP"), ("VP", "ADV"), ("ADV", "VP")],
    "PP":  [("P", "NP")],
}


def _derive(sym: str, i: int, j: int, pos: List[Set[str]], memo: Dict) -> Optional[tuple]:
    """A parse tree for `sym` spanning tokens[i:j], or None. Tree = (label, child, ...)."""
    key = (sym, i, j)
    if key in memo:
        return memo[key]
    memo[key] = None                                   # guard against re-entry on the same span
    result = None
    if sym not in GRAMMAR:                             # terminal POS tag
        if j == i + 1 and sym in pos[i]:
            result = (sym, i)                          # leaf carries its token index
    else:
        for prod in GRAMMAR[sym]:
            kids = _derive_seq(prod, i, j, pos, memo)
            if kids is not None:
                result = (sym,) + tuple(kids)
                break
    memo[key] = result
    return result


def _derive_seq(prod: Tuple[str, ...], i: int, j: int, pos: List[Set[str]], memo: Dict):
    """Child trees if the symbol sequence `prod` derives tokens[i:j], else None."""
    if not prod:
        return [] if i == j else None
    first, rest = prod[0], prod[1:]
    if not rest:
        t = _derive(first, i, j, pos, memo)
        return [t] if t is not None else None
    for k in range(i + 1, j):                          # first takes [i:k] (>=1 token), rest [k:j]
        tf = _derive(first, i, k, pos, memo)
        if tf is None:
            continue
        tr = _derive_seq(rest, k, j, pos, memo)
        if tr is not None:
            return [tf] + tr
    return None


def _bracket(tree, tokens) -> str:
    """A tree as a bracketed string: (S (NP (DET the) (NOM (N cat))) (VP (V sat)))."""
    label = tree[0]
    if len(tree) == 2 and isinstance(tree[1], int):
        return f"({label} {tokens[tree[1]]})"
    return "(" + label + " " + " ".join(_bracket(c, tokens) for c in tree[1:]) + ")"


def parse(sentence: str) -> Dict:
    """Parse one sentence. Returns {ok, grammatical, tokens, pos, tree, bracket, reason}.
    grammatical is True iff the grammar derives S over the whole token span."""
    tokens = _WORD.findall(str(sentence or ""))
    if not tokens:
        return {"ok": False, "reason": "no word tokens"}
    pos = [tag(t) for t in tokens]
    unknown = [tokens[i] for i, p in enumerate(pos) if not p]
    if unknown:
        return {"ok": False, "reason": f"could not tag: {unknown}", "tokens": tokens}
    tree = _derive("S", 0, len(tokens), pos, {})
    out = {"ok": True, "tokens": tokens, "pos": [sorted(p) for p in pos],
           "grammatical": tree is not None}
    if tree is not None:
        out["tree"] = tree
        out["bracket"] = _bracket(tree, tokens)
    else:
        out["reason"] = "no valid phrase-structure parse under the engine's grammar"
    return out
