"""Wordcraft — the computable claims about words, letters and alphabets (linguistics as a strength; Matt, 2026-10-08).

What a word's letters say is arithmetic, and arithmetic is what this engine seals: how many letters, vowels and
consonants a word has; whether two words are anagrams; whether a word is a palindrome; how many edits apart two
words are (Levenshtein); how many syllables and phonemes a word has, read off the keeping's own pronunciation shelf
(the CMU Pronouncing Dictionary, ARPABET: one stress digit per vowel, one syllable per vowel); how many letters an
alphabet has (a sourced table); what the plural of a noun is (an irregular table plus the regular rule — a noun not
in the table whose claimed plural is not the regular one is DECLINED, never called wrong); and where a letter ranks in
English letter frequency (a sourced order). Nothing here reads meaning; meaning is the lexicon's door (define,
word_study). Every check names its convention in the detail, so a reader never has to guess what was counted.

WORD_VERIFY packet shape (any subset of fields):
    {"word": "level", "claimed_letters": 5, "claimed_vowels": 2, "claimed_consonants": 3,
     "claimed_syllables": 2, "claimed_phonemes": 5, "pronunciation": "L EH1 V AH0 L", "claimed_palindrome": true,
     "word_a": "listen", "word_b": "silent", "claimed_anagram": true, "claimed_edit_distance": 4,
     "alphabet": "hebrew", "claimed_alphabet_letters": 22,
     "singular": "child", "claimed_plural": "children",
     "letter": "e", "claimed_rank": 1}
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .base import VerifierResult, na, confirm, mismatch, error, dispatch

# the explicit golden the domain gate derives its true/false pair from (numbers and booleans only: a string claim
# such as a plural cannot be falsified by scaling); every check here confirms, and its perturbed twin must not
GOLDEN_PACKET_KEY = "WORD_VERIFY"
GOLDEN_EXAMPLE = {"word": "level", "claimed_letters": 5, "claimed_vowels": 2, "claimed_consonants": 3,
                  "claimed_syllables": 2, "claimed_phonemes": 5, "pronunciation": "L EH1 V AH0 L", "claimed_palindrome": True,
                  "word_a": "listen", "word_b": "silent", "claimed_anagram": True, "claimed_edit_distance": 4,
                  "alphabet": "hebrew", "claimed_alphabet_letters": 22, "letter": "t", "claimed_rank": 2}

VOWEL_LETTERS = frozenset("aeiou")       # the five vowel letters; y is counted as a consonant letter, and the detail says so
_LETTERS = re.compile(r"[A-Za-z]")

# letters in the modern standard alphabet, as the writing-system references give them
ALPHABETS: Dict[str, Tuple[int, str]] = {
    "english": (26, "the Latin alphabet as used for English"),
    "latin": (26, "the basic modern Latin alphabet (the classical alphabet had 23: no J, U, W)"),
    "classical latin": (23, "the classical Latin alphabet: no J, U or W"),
    "hebrew": (22, "the Hebrew abjad: 22 letters, five with final forms"),
    "greek": (24, "the Greek alphabet, alpha to omega"),
    "arabic": (28, "the Arabic abjad"),
    "russian": (33, "the Russian Cyrillic alphabet since the 1918 reform"),
    "cyrillic": (33, "the Russian Cyrillic alphabet since the 1918 reform"),
    "spanish": (27, "the Real Academia alphabet since 2010: 26 Latin letters and ñ"),
    "italian": (21, "the Italian alphabet; j, k, w, x, y occur only in borrowed words"),
    "german": (26, "26 Latin letters; ä, ö, ü and ß are additional signs, not counted"),
    "french": (26, "26 Latin letters; accented forms are not separate letters"),
    "portuguese": (26, "26 letters since the 1990 orthographic agreement"),
    "dutch": (26, "26 Latin letters"),
    "turkish": (29, "the Turkish alphabet of 1928"),
    "polish": (32, "the Polish alphabet"),
    "czech": (42, "the Czech alphabet, the digraph ch counted as a letter"),
    "swedish": (29, "26 Latin letters and å, ä, ö"),
    "norwegian": (29, "26 Latin letters and æ, ø, å"),
    "danish": (29, "26 Latin letters and æ, ø, å"),
    "finnish": (29, "26 Latin letters and å, ä, ö"),
    "icelandic": (32, "the Icelandic alphabet"),
    "korean": (24, "Hangul: 14 basic consonants and 10 basic vowels"),
    "hangul": (24, "Hangul: 14 basic consonants and 10 basic vowels"),
    "georgian": (33, "Mkhedruli, the modern Georgian alphabet"),
    "armenian": (39, "the modern Armenian alphabet; the classical had 36"),
    "phoenician": (22, "the Phoenician abjad"),
}
ALPHABETS_SOURCE = "P. T. Daniels, W. Bright, The World's Writing Systems (Oxford, 1996); the orthographies' own academies"

# English letter frequency, most to least common: Lewand, Cryptological Mathematics (2000), Table 1.1
LETTER_RANK_EN = "etaoinshrdlcumwfgypbvkjxqz"
LETTER_RANK_SOURCE = "R. Lewand, Cryptological Mathematics (MAA, 2000), Table 1.1; Cornell Math Explorers' Club, relative letter frequencies"

# irregular plurals with ONE accepted form — a noun with two accepted plurals (index, formula, cactus, fish...) is
# deliberately absent so a claim about it is declined rather than refused
IRREGULAR_PLURALS: Dict[str, str] = {
    "child": "children", "man": "men", "woman": "women", "mouse": "mice", "goose": "geese", "foot": "feet",
    "tooth": "teeth", "person": "people", "ox": "oxen", "louse": "lice", "datum": "data", "criterion": "criteria",
    "phenomenon": "phenomena", "analysis": "analyses", "basis": "bases", "crisis": "crises", "thesis": "theses",
    "alumnus": "alumni", "larva": "larvae", "nucleus": "nuclei", "sheep": "sheep", "deer": "deer", "moose": "moose",
    "series": "series", "species": "species", "aircraft": "aircraft", "leaf": "leaves", "knife": "knives",
    "wife": "wives", "life": "lives", "half": "halves", "wolf": "wolves", "loaf": "loaves", "shelf": "shelves",
    "calf": "calves", "thief": "thieves", "potato": "potatoes", "tomato": "tomatoes", "hero": "heroes",
    "echo": "echoes", "quiz": "quizzes",
}


def _letters(word: str) -> str:
    return "".join(_LETTERS.findall(str(word or ""))).lower()


def regular_plural(noun: str) -> str:
    """The regular English rule: -s/-x/-z/-ch/-sh take -es; a consonant + y takes -ies; otherwise -s."""
    w = str(noun or "").strip().lower()
    if re.search(r"(s|x|z|ch|sh)$", w):
        return w + "es"
    if re.search(r"[^aeiou]y$", w):
        return w[:-1] + "ies"
    return w + "s"


def levenshtein(a: str, b: str) -> int:
    a, b = str(a or ""), str(b or "")
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def arpabet_counts(pron: str) -> Tuple[int, int]:
    """(syllables, phonemes) of an ARPABET string: one syllable per vowel phoneme (the ones carrying a stress digit)."""
    toks = [t for t in str(pron or "").replace(".", " ").split() if t]
    syll = sum(1 for t in toks if re.search(r"\d", t))
    return syll, len(toks)


def arpabet_from_body(body: str) -> Optional[str]:
    """The FIRST pronunciation in a pronunciation card's body: "word: pronounced (ARPABET) S T R EH1 NG K TH; also
    S T R EH1 NG TH. From the CMU ..." -> "S T R EH1 NG K TH". Stops at ';' (a variant follows) or '.'."""
    m = re.search(r"\(ARPABET\)\s+([A-Z0-9 ]+?)\s*(?:;|\.|$)", str(body or ""))
    return m.group(1).strip() if m else None


def _pronunciation_of(word: str) -> Optional[Tuple[str, str]]:
    """(ARPABET, source label) from the keeping's pronunciation shelf, or None when the word is not held (or no
    corpus is loaded — a cold tool, a test). Never raises."""
    try:
        from .. import corpus as _corpus
        c = _corpus.default_corpus()
        w = str(word or "").strip().lower()
        # The pronunciation shelf names its cards deterministically (card_src_pron_<word>), so the card is read by
        # its id first - ranking is not a lookup (live 2026-10-08: "encyclopedia" surfaced only "encyclopedias" in
        # the top twelve). Search stays as the fallback for a word whose id is spelt differently.
        direct = c.full("card_src_pron_" + w) if c.has("card_src_pron_" + w) else None
        hits = ([direct] if direct else []) + list(c.search(w, limit=12, include_witness=False) or [])
        for h in hits:
            cid = h.get("id") if isinstance(h, dict) else None
            if not cid:
                continue
            card = h if (direct is not None and h is direct) else (c.full(cid) or {})
            if (card.get("shelf") or "") != "pronunciation":
                continue
            if str(card.get("title") or card.get("subject") or "").strip().lower() != w:
                continue
            pron = arpabet_from_body(str(card.get("body") or ""))
            if pron:
                return pron, str((card.get("source") or {}).get("label") or "CMU Pronouncing Dictionary")
    except Exception:  # noqa: BLE001 — a lookup that fails is a miss, never a verdict
        return None
    return None


def verify_letters(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.letters"
    word = spec.get("word")
    if word is None:
        return na(name)
    ls = _letters(word)
    vowels = sum(1 for ch in ls if ch in VOWEL_LETTERS)
    actual = {"letters": len(ls), "vowels": vowels, "consonants": len(ls) - vowels}
    data = {"word": word, **actual, "convention": "letters a-z only; vowels are the five vowel letters a e i o u (y counts as a consonant letter)"}
    checks = []
    for key in ("letters", "vowels", "consonants"):
        c = spec.get("claimed_" + key)
        if c is None:
            continue
        try:
            cf = int(float(c))
        except (TypeError, ValueError):
            return error(name, f"claimed_{key} must be a whole number")
        checks.append((key, cf, actual[key]))
    if not checks:
        return na(name)
    bad = [(k, c, a) for k, c, a in checks if c != a]
    if not bad:
        return confirm(name, f"{word!r}: " + ", ".join(f"{a} {k}" for k, _c, a in checks) + " (matches claim; " + data["convention"] + ")", data)
    return mismatch(name, f"{word!r}: " + ", ".join(f"{a} {k}, claimed {c}" for k, c, a in bad) + " (" + data["convention"] + ")", data)


def verify_anagram(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.anagram"
    a, b, claimed = spec.get("word_a"), spec.get("word_b"), spec.get("claimed_anagram")
    if a is None or b is None or claimed is None:
        return na(name)
    actual = sorted(_letters(a)) == sorted(_letters(b)) and _letters(a) != ""
    data = {"word_a": a, "word_b": b, "actual_anagram": actual, "claimed_anagram": bool(claimed),
            "convention": "letters only, case ignored, spaces and hyphens ignored"}
    if actual == bool(claimed):
        return confirm(name, f"{a!r} and {b!r} {'are' if actual else 'are not'} anagrams (matches claim)", data)
    return mismatch(name, f"{a!r} and {b!r} {'are' if actual else 'are not'} anagrams, claimed {'are' if claimed else 'are not'}", data)


def verify_palindrome(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.palindrome"
    w, claimed = spec.get("word"), spec.get("claimed_palindrome")
    if w is None or claimed is None:
        return na(name)
    ls = _letters(w)
    actual = bool(ls) and ls == ls[::-1]
    data = {"word": w, "actual_palindrome": actual, "claimed_palindrome": bool(claimed), "convention": "letters only, case ignored"}
    if actual == bool(claimed):
        return confirm(name, f"{w!r} {'is' if actual else 'is not'} a palindrome (matches claim)", data)
    return mismatch(name, f"{w!r} {'is' if actual else 'is not'} a palindrome, claimed {'is' if claimed else 'is not'}", data)


def verify_edit_distance(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.edit_distance"
    a, b, claimed = spec.get("word_a"), spec.get("word_b"), spec.get("claimed_edit_distance")
    if a is None or b is None or claimed is None:
        return na(name)
    try:
        c = int(float(claimed))
    except (TypeError, ValueError):
        return error(name, "claimed_edit_distance must be a whole number")
    actual = levenshtein(str(a).lower(), str(b).lower())
    data = {"word_a": a, "word_b": b, "actual_edit_distance": actual, "claimed_edit_distance": c,
            "convention": "Levenshtein distance: insertions, deletions and substitutions, case ignored"}
    if actual == c:
        return confirm(name, f"edit distance {a!r} -> {b!r} = {actual} (matches claim)", data)
    return mismatch(name, f"edit distance {a!r} -> {b!r} = {actual}, claimed {c}", data)


def verify_syllables(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.syllables"
    w = spec.get("word")
    cs, cp = spec.get("claimed_syllables"), spec.get("claimed_phonemes")
    if w is None or (cs is None and cp is None):
        return na(name)
    pron = spec.get("pronunciation")
    source = "pronunciation given in the spec"
    if not pron:
        found = _pronunciation_of(str(w))
        if not found:
            return na(name, f"{w!r} is not on the keeping's pronunciation shelf (or no corpus is loaded) — declined, not judged")
        pron, source = found
    syll, phon = arpabet_counts(pron)
    data = {"word": w, "pronunciation": pron, "actual_syllables": syll, "actual_phonemes": phon, "source": source,
            "convention": "ARPABET: one syllable per vowel phoneme (each carries a stress digit); phonemes = tokens"}
    bad = []
    if cs is not None:
        try:
            if int(float(cs)) != syll:
                bad.append(f"syllables {syll}, claimed {int(float(cs))}")
        except (TypeError, ValueError):
            return error(name, "claimed_syllables must be a whole number")
    if cp is not None:
        try:
            if int(float(cp)) != phon:
                bad.append(f"phonemes {phon}, claimed {int(float(cp))}")
        except (TypeError, ValueError):
            return error(name, "claimed_phonemes must be a whole number")
    if not bad:
        return confirm(name, f"{w!r} = {pron}: {syll} syllable(s), {phon} phoneme(s) (matches claim; {source})", data)
    return mismatch(name, f"{w!r} = {pron}: " + "; ".join(bad) + f" ({source})", data)


def verify_alphabet(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.alphabet"
    alpha, claimed = spec.get("alphabet"), spec.get("claimed_alphabet_letters")
    if alpha is None or claimed is None:
        return na(name)
    key = re.sub(r"\s+", " ", str(alpha).strip().lower())
    entry = ALPHABETS.get(key)
    if entry is None:
        return na(name, f"the {alpha!r} alphabet is not in the table — declined, not judged")
    try:
        c = int(float(claimed))
    except (TypeError, ValueError):
        return error(name, "claimed_alphabet_letters must be a whole number")
    n, note = entry
    data = {"alphabet": alpha, "actual_letters": n, "claimed_letters": c, "note": note, "source": ALPHABETS_SOURCE}
    if n == c:
        return confirm(name, f"the {key} alphabet has {n} letters ({note}; matches claim)", data)
    return mismatch(name, f"the {key} alphabet has {n} letters ({note}), claimed {c}", data)


def verify_plural(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.plural"
    sing, claimed = spec.get("singular"), spec.get("claimed_plural")
    if sing is None or claimed is None:
        return na(name)
    s = str(sing).strip().lower()
    c = str(claimed).strip().lower()
    reg = regular_plural(s)
    data = {"singular": s, "claimed_plural": c, "regular_rule": reg, "irregular": IRREGULAR_PLURALS.get(s)}
    if s in IRREGULAR_PLURALS:
        if c == IRREGULAR_PLURALS[s]:
            return confirm(name, f"the plural of {s!r} is {c!r} (irregular; matches claim)", data)
        return mismatch(name, f"the plural of {s!r} is {IRREGULAR_PLURALS[s]!r} (irregular), claimed {c!r}", data)
    if c == reg:
        return confirm(name, f"the plural of {s!r} is {c!r} by the regular rule (matches claim)", data)
    return na(name, f"{s!r} is not in the irregular table and the regular rule gives {reg!r}, not {c!r} — declined, not judged "
                    "(a noun with a plural the table does not hold is never called wrong)")


def verify_letter_rank(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.letter_rank"
    letter, claimed = spec.get("letter"), spec.get("claimed_rank")
    if letter is None or claimed is None:
        return na(name)
    ch = str(letter).strip().lower()
    if len(ch) != 1 or ch not in LETTER_RANK_EN:
        return na(name, f"{letter!r} is not a letter a-z")
    try:
        c = int(float(claimed))
    except (TypeError, ValueError):
        return error(name, "claimed_rank must be a whole number (1 = most common)")
    actual = LETTER_RANK_EN.index(ch) + 1
    data = {"letter": ch, "actual_rank": actual, "claimed_rank": c, "order": LETTER_RANK_EN, "source": LETTER_RANK_SOURCE}
    if actual == c:
        return confirm(name, f"{ch.upper()} is the {actual}{'st' if actual == 1 else 'nd' if actual == 2 else 'rd' if actual == 3 else 'th'} most common letter in English ({LETTER_RANK_SOURCE}; matches claim)", data)
    return mismatch(name, f"{ch.upper()} ranks {actual} of 26 in English letter frequency, claimed {c} ({LETTER_RANK_SOURCE})", data)


_RULES = [
    (lambda wv: "word" in wv and any(k in wv for k in ("claimed_letters", "claimed_vowels", "claimed_consonants")), verify_letters),
    (lambda wv: "word_a" in wv and "word_b" in wv and "claimed_anagram" in wv, verify_anagram),
    (lambda wv: "word" in wv and "claimed_palindrome" in wv, verify_palindrome),
    (lambda wv: "word_a" in wv and "word_b" in wv and "claimed_edit_distance" in wv, verify_edit_distance),
    (lambda wv: "word" in wv and ("claimed_syllables" in wv or "claimed_phonemes" in wv), verify_syllables),
    (lambda wv: "alphabet" in wv and "claimed_alphabet_letters" in wv, verify_alphabet),
    (lambda wv: "singular" in wv and "claimed_plural" in wv, verify_plural),
    (lambda wv: "letter" in wv and "claimed_rank" in wv, verify_letter_rank),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "WORD_VERIFY", _RULES, domain="wordcraft", none_reason="no WORD_VERIFY artifacts present")
