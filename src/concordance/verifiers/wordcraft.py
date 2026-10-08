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
     "letter": "e", "claimed_rank": 1,
     # phonics (the pronunciation shelf; `pronunciation`/`pronunciation_a`/`pronunciation_b` may be given instead)
     "claimed_rhyme": true, "claimed_homophone": true, "claimed_stress_syllable": 2,
     "claimed_silent": true, "claimed_vowel_sound": "long a", "claimed_edge_sound": "f", "position": "first",
     # etymology (the etymology shelf — Webster 1913; `etymology` may be given instead)
     "claimed_language": "latin", "claimed_source_word": "salarium", "claimed_gloss": "little mouse", "claimed_origin": true}
Phonics and etymology (Matt, 2026-10-08: "Etymology and phonics") are documented at their section below.
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


_SLUG = re.compile(r"[^a-z0-9]+")


def _card_id(prefix: str, word: str) -> str:
    """The deterministic id the source shelves mint: card_src_pron_<slug>, card_src_etym_<slug>."""
    return prefix + _SLUG.sub("_", str(word or "").strip().lower()).strip("_")


def _shelf_card_of(word: str, shelf: str, prefix: str, must_have: str) -> Optional[Dict[str, Any]]:
    """The keeping's card for `word` on `shelf`, or None when the word is not held (or no corpus is loaded — a cold
    tool, a test). The shelves name their cards deterministically, so the card is read by its id first — ranking
    is not a lookup (live 2026-10-08: "encyclopedia" surfaced only "encyclopedias" in the top twelve); search
    stays as the fallback for a word whose id is spelt differently. Never raises."""
    try:
        from .. import corpus as _corpus
        if not _corpus.loaded():
            return None          # a cold process never starts the corpus build inside a verify budget: declined
        c = _corpus.default_corpus()
        w = str(word or "").strip().lower()
        cid = _card_id(prefix, w)
        direct = c.full(cid) if c.has(cid) else None
        hits = ([direct] if direct else []) + list(c.search(w, limit=12, include_witness=False) or [])
        for h in hits:
            hid = h.get("id") if isinstance(h, dict) else None
            if not hid:
                continue
            card = h if (direct is not None and h is direct) else (c.full(hid) or {})
            if (card.get("shelf") or "") != shelf:
                continue
            if str(card.get("title") or card.get("subject") or "").strip().lower() != w:
                continue
            if must_have in str(card.get("body") or ""):
                return card
    except Exception:  # noqa: BLE001 — a lookup that fails is a miss, never a verdict
        return None
    return None


def _pronunciation_of(word: str) -> Optional[Tuple[str, str]]:
    """(ARPABET, source label) — the FIRST pronunciation on the keeping's pronunciation shelf, or None."""
    card = _shelf_card_of(word, "pronunciation", "card_src_pron_", "(ARPABET)")
    if not card:
        return None
    pron = arpabet_from_body(str(card.get("body") or ""))
    if not pron:
        return None
    return pron, str((card.get("source") or {}).get("label") or "CMU Pronouncing Dictionary")


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



# ── PHONICS (Matt, 2026-10-08: "Etymology and phonics") — sound, read off the pronunciation shelf ─────────────
# Every check here reads the CMU Pronouncing Dictionary's ARPABET (North American English) and names that convention
# in its detail: a RHYME shares the tail from the last primary-stressed vowel; a HOMOPHONE is the same phoneme string
# with stress ignored; the STRESSED syllable is the vowel carrying stress 1; a SILENT letter is a letter the spelling
# has more of than the pronunciation sounds (a letter inside a digraph, a vowel letter other than a final e after a
# consonant, and y or w used as vowels are DECLINED, never judged; a letter whose sound another letter of the word
# also makes is declined rather than called sounded); the long/short VOWEL names of phonics map to ARPABET vowels; the
# FIRST and LAST sounds are the first and last phonemes. Any held variant pronunciation counts for a claim; a word not
# on the shelf (or no corpus) is declined. A spec may carry `pronunciation` / `pronunciation_a` / `pronunciation_b`
# (a string, variants split by ';') so the checks run without a corpus.

_STRESS_RE = re.compile(r"\d")
DIGRAPHS = ("ch", "sh", "th", "ph", "wh", "gh", "ck", "qu", "ng", "dg")
# the phonemes a letter can stand for (ARPABET), used only to COUNT a letter's sounds for the silent-letter check
LETTER_PHONEMES: Dict[str, frozenset] = {
    "b": frozenset({"B"}), "c": frozenset({"K", "S", "CH", "SH"}), "d": frozenset({"D", "JH", "T"}),
    "f": frozenset({"F", "V"}), "g": frozenset({"G", "JH", "NG", "F", "ZH"}), "h": frozenset({"HH"}),
    "j": frozenset({"JH", "HH", "Y"}), "k": frozenset({"K"}), "l": frozenset({"L"}), "m": frozenset({"M"}),
    "n": frozenset({"N", "NG"}), "p": frozenset({"P", "F"}), "q": frozenset({"K"}), "r": frozenset({"R", "ER"}),
    "s": frozenset({"S", "Z", "SH", "ZH"}), "t": frozenset({"T", "CH", "SH", "TH", "DH", "D"}),
    "v": frozenset({"V"}), "w": frozenset({"W", "HH"}), "x": frozenset({"K", "S", "Z", "G"}),
    "y": frozenset({"Y"}), "z": frozenset({"Z", "S", "ZH"}),
}
# the phonics names for vowel sounds -> ARPABET vowels (General American, as CMU records it)
VOWEL_SOUNDS: Dict[str, Tuple[str, ...]] = {
    "long a": ("EY",), "short a": ("AE",), "long e": ("IY",), "short e": ("EH",), "long i": ("AY",),
    "short i": ("IH",), "long o": ("OW",), "short o": ("AA", "AO"), "long u": ("UW",), "short u": ("AH",),
    "long oo": ("UW",), "short oo": ("UH",), "schwa": ("AH",),
}
VOWEL_CONVENTION = ("phonics names mapped to ARPABET (CMU, General American): long a EY, short a AE, long e IY, short e EH, "
                    "long i AY, short i IH, long o OW, short o AA or AO, long u UW (also after Y), short u AH with stress, "
                    "long oo UW, short oo UH, schwa AH0")
# the sound names people write ("the f sound", "a hard g") -> ARPABET consonants
SOUND_NAMES: Dict[str, Tuple[str, ...]] = {
    "f": ("F",), "v": ("V",), "k": ("K",), "hard c": ("K",), "soft c": ("S",), "s": ("S",), "z": ("Z",), "b": ("B",),
    "d": ("D",), "g": ("G",), "hard g": ("G",), "soft g": ("JH",), "j": ("JH",), "l": ("L",), "m": ("M",), "n": ("N",),
    "p": ("P",), "r": ("R",), "t": ("T",), "w": ("W",), "y": ("Y",), "h": ("HH",), "sh": ("SH",), "ch": ("CH",),
    "th": ("TH", "DH"), "ng": ("NG",), "zh": ("ZH",),
}


def arpabet_variants_from_body(body: str) -> List[str]:
    """Every pronunciation in a pronunciation card's body — the first, then those after '; also'."""
    s = str(body or "")
    if "(ARPABET)" not in s:
        return []
    seg = s.split("(ARPABET)", 1)[1].strip()
    seg = re.split(r"\.\s|\.$", seg, maxsplit=1)[0]
    out: List[str] = []
    for part in re.split(r";\s*also\s+|,\s*", seg):
        p = re.sub(r"\s+", " ", part.strip())
        if p and re.fullmatch(r"[A-Z]{1,2}[0-2]?(?: [A-Z]{1,2}[0-2]?)*", p) and p not in out:
            out.append(p)
    return out


def strip_stress(pron: str) -> List[str]:
    return [_STRESS_RE.sub("", t) for t in str(pron or "").split() if t]


def rhyme_tail(pron: str) -> List[str]:
    """The tail from the last primary-stressed vowel (the last vowel if none carries 1), stress stripped."""
    toks = [t for t in str(pron or "").split() if t]
    idx = [i for i, t in enumerate(toks) if t.endswith("1")] or [i for i, t in enumerate(toks) if _STRESS_RE.search(t)]
    if not idx:
        return []
    return [_STRESS_RE.sub("", t) for t in toks[idx[-1]:]]


def stressed_syllable(pron: str) -> int:
    """The 1-based syllable carrying primary stress (0 if none)."""
    n = 0
    for t in str(pron or "").split():
        if _STRESS_RE.search(t):
            n += 1
            if t.endswith("1"):
                return n
    return 0


def _spec_prons(spec: Dict[str, Any], key: str) -> Optional[List[str]]:
    v = spec.get(key)
    if v is None:
        return None
    parts = [p.strip() for p in str(v).split(";")] if isinstance(v, str) else [str(p).strip() for p in v]
    parts = [p for p in parts if p]
    return parts or None


def _prons_for(spec: Dict[str, Any], word_key: str, pron_key: str) -> Tuple[Optional[List[str]], str]:
    """Every pronunciation of spec[word_key]: from the spec when given, else from the pronunciation shelf."""
    given = _spec_prons(spec, pron_key)
    if given:
        return given, "pronunciation given in the spec"
    card = _shelf_card_of(str(spec.get(word_key)), "pronunciation", "card_src_pron_", "(ARPABET)")
    if not card:
        return None, ""
    vs = arpabet_variants_from_body(str(card.get("body") or ""))
    return (vs or None), str((card.get("source") or {}).get("label") or "CMU Pronouncing Dictionary")


def _declined_word(name: str, word: Any) -> VerifierResult:
    return na(name, f"{word!r} is not on the keeping's pronunciation shelf (or no corpus is loaded) — declined, not judged")


def verify_rhyme(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.rhyme"
    a, b, claimed = spec.get("word_a"), spec.get("word_b"), spec.get("claimed_rhyme")
    if a is None or b is None or claimed is None:
        return na(name)
    pa, sa = _prons_for(spec, "word_a", "pronunciation_a")
    if not pa:
        return _declined_word(name, a)
    pb, _sb = _prons_for(spec, "word_b", "pronunciation_b")
    if not pb:
        return _declined_word(name, b)
    pairs = [(x, y) for x in pa for y in pb if rhyme_tail(x) and rhyme_tail(x) == rhyme_tail(y)]
    actual = bool(pairs)
    x, y = pairs[0] if pairs else (pa[0], pb[0])
    identical = strip_stress(x) == strip_stress(y)
    ta, tb = " ".join(rhyme_tail(x)), " ".join(rhyme_tail(y))
    data = {"word_a": a, "word_b": b, "pronunciation_a": x, "pronunciation_b": y, "tail_a": ta, "tail_b": tb,
            "actual_rhyme": actual, "claimed_rhyme": bool(claimed), "identical_rhyme": actual and identical, "source": sa,
            "convention": "ARPABET (CMU): a rhyme shares the tail from the last primary-stressed vowel; any held variant counts"}
    how = f"{a!r} = {x}, {b!r} = {y}: tails {ta!r} / {tb!r}"
    if actual == bool(claimed):
        note = " — the same pronunciation (an identical rhyme)" if actual and identical else ""
        return confirm(name, how + note + f" ({'they rhyme' if actual else 'no rhyme'}; matches claim; {sa})", data)
    return mismatch(name, how + f" — {'they rhyme' if actual else 'they do not rhyme'}, claimed {'rhyme' if claimed else 'no rhyme'} ({sa})", data)


def verify_homophone(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.homophone"
    a, b, claimed = spec.get("word_a"), spec.get("word_b"), spec.get("claimed_homophone")
    if a is None or b is None or claimed is None:
        return na(name)
    pa, sa = _prons_for(spec, "word_a", "pronunciation_a")
    if not pa:
        return _declined_word(name, a)
    pb, _sb = _prons_for(spec, "word_b", "pronunciation_b")
    if not pb:
        return _declined_word(name, b)
    pairs = [(x, y) for x in pa for y in pb if strip_stress(x) == strip_stress(y)]
    actual = bool(pairs)
    x, y = pairs[0] if pairs else (pa[0], pb[0])
    data = {"word_a": a, "word_b": b, "pronunciation_a": x, "pronunciation_b": y, "actual_homophone": actual,
            "claimed_homophone": bool(claimed), "source": sa,
            "convention": "ARPABET (CMU): homophones share the phoneme string, stress ignored; any held variant counts"}
    how = f"{a!r} = {x}, {b!r} = {y}"
    if actual == bool(claimed):
        return confirm(name, how + f": {'the same sounds' if actual else 'different sounds'} (matches claim; {sa})", data)
    return mismatch(name, how + f": {'the same sounds' if actual else 'different sounds'}, claimed {'homophones' if claimed else 'not homophones'} ({sa})", data)


def verify_stress(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.stress"
    w, claimed = spec.get("word"), spec.get("claimed_stress_syllable")
    if w is None or claimed is None:
        return na(name)
    try:
        c = int(float(claimed))
    except (TypeError, ValueError):
        return error(name, "claimed_stress_syllable must be a whole number (1 = first; -1 = last, -2 = penultimate)")
    prons, src = _prons_for(spec, "word", "pronunciation")
    if not prons:
        return _declined_word(name, w)
    rows = []
    for p in prons:
        n_syll, _n = arpabet_counts(p)
        want = c if c > 0 else n_syll + 1 + c
        rows.append((p, stressed_syllable(p), n_syll, want))
    if all(r[1] == 0 for r in rows):
        return na(name, f"{w!r} = {prons[0]}: no primary stress is marked — declined")
    hit = [r for r in rows if r[1] and r[1] == r[3]]
    p, actual, n_syll, want = hit[0] if hit else rows[0]
    data = {"word": w, "pronunciation": p, "actual_stress_syllable": actual, "syllables": n_syll, "claimed": claimed,
            "claimed_resolved": want, "source": src, "convention": "ARPABET (CMU): the syllable whose vowel carries primary stress (1)"}
    if hit:
        return confirm(name, f"{w!r} = {p}: primary stress on syllable {actual} of {n_syll} (matches claim; {src})", data)
    return mismatch(name, f"{w!r} = {p}: primary stress on syllable {actual} of {n_syll}, claimed {want} ({src})", data)


def _silent_in(word: str, letter: str, pron: str) -> Optional[bool]:
    """True/False when the convention can tell, None when it declines (see the section note)."""
    w = _letters(word)
    L = letter
    toks = strip_stress(pron)
    if L in VOWEL_LETTERS:
        if L == "e" and w.endswith("e") and len(w) >= 2 and w[-2] not in VOWEL_LETTERS:
            v_letters = sum(1 for ch in w if ch in VOWEL_LETTERS)
            v_sounds = sum(1 for t in str(pron or "").split() if _STRESS_RE.search(t))
            last_is_vowel = bool(toks) and bool(re.search(r"\d", str(pron).split()[-1]))
            if last_is_vowel:
                return False
            return v_letters > v_sounds
        return None
    if L == "y" and not w.startswith("y"):
        return None
    if L == "w" and all(i > 0 and w[i - 1] in VOWEL_LETTERS for i, ch in enumerate(w) if ch == "w"):
        return None
    occ = [i for i, ch in enumerate(w) if ch == L]
    if occ and all((i > 0 and w[i - 1:i + 1] in DIGRAPHS) or (w[i:i + 2] in DIGRAPHS) for i in occ):
        return None
    sounds = LETTER_PHONEMES.get(L)
    if not sounds:
        return None
    n_sound = sum(1 for t in toks if t in sounds)
    if len(occ) > n_sound:
        return True
    others = [o for o in sorted(set(w)) if o != L and LETTER_PHONEMES.get(o) and (LETTER_PHONEMES[o] & sounds)]
    if others:
        return None                       # another letter of the word makes the same sound: which one sounds cannot be told
    return False


def verify_silent_letter(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.silent_letter"
    w, letter, claimed = spec.get("word"), spec.get("letter"), spec.get("claimed_silent")
    if w is None or letter is None or claimed is None:
        return na(name)
    L = str(letter).strip().lower()
    if len(L) != 1 or not L.isalpha():
        return na(name, f"{letter!r} is not a single letter")
    if L not in _letters(w):
        return na(name, f"{w!r} has no letter {L!r} — declined")
    prons, src = _prons_for(spec, "word", "pronunciation")
    if not prons:
        return _declined_word(name, w)
    verdicts = [(p, _silent_in(str(w), L, p)) for p in prons]
    known = [(p, v) for p, v in verdicts if v is not None]
    data = {"word": w, "letter": L, "pronunciations": prons, "claimed_silent": bool(claimed), "source": src,
            "convention": ("ARPABET (CMU): a letter is silent when the spelling has more of it than the pronunciation sounds; "
                           "letters inside a digraph (ch sh th ph wh gh ck qu ng dg), vowel letters other than a final e after a "
                           "consonant, y or w as vowels, and a letter whose sound another letter also makes are declined")}
    if not known:
        return na(name, f"the {L!r} in {w!r} ({prons[0]}) is not judged by the convention — declined, not judged", data)
    want = bool(claimed)
    hit = [(p, v) for p, v in known if v == want]
    if hit:
        p, v = hit[0]
        data["actual_silent"] = v
        return confirm(name, f"the {L!r} in {w!r} = {p}: {'silent' if v else 'sounded'} (matches claim; {src})", data)
    p, v = known[0]
    data["actual_silent"] = v
    return mismatch(name, f"the {L!r} in {w!r} = {p}: {'silent' if v else 'sounded'}, claimed {'silent' if want else 'sounded'} ({src})", data)


def verify_vowel_sound(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.vowel_sound"
    w, snd = spec.get("word"), spec.get("claimed_vowel_sound")
    if w is None or snd is None:
        return na(name)
    key = re.sub(r"\s+", " ", str(snd).strip().lower())
    if key not in VOWEL_SOUNDS:
        return na(name, f"{snd!r} is not a vowel sound the convention names — declined")
    claimed = spec.get("claimed", True)
    prons, src = _prons_for(spec, "word", "pronunciation")
    if not prons:
        return _declined_word(name, w)
    want = VOWEL_SOUNDS[key]

    def has(p: str) -> bool:
        for t in str(p).split():
            m = re.fullmatch(r"([A-Z]+)([0-2])", t)
            if not m or m.group(1) not in want:
                continue
            if key == "short u" and m.group(2) == "0":
                continue
            if key == "schwa" and m.group(2) != "0":
                continue
            return True
        return False

    hits = [p for p in prons if has(p)]
    actual = bool(hits)
    p = hits[0] if hits else prons[0]
    data = {"word": w, "pronunciation": p, "sound": key, "arpabet": list(want), "actual": actual, "claimed": bool(claimed),
            "source": src, "convention": VOWEL_CONVENTION}
    if actual == bool(claimed):
        return confirm(name, f"{w!r} = {p}: {'has' if actual else 'has no'} {key} sound ({'/'.join(want)}; matches claim; {src})", data)
    return mismatch(name, f"{w!r} = {p}: {'has' if actual else 'has no'} {key} sound ({'/'.join(want)}), claimed {'has' if claimed else 'has not'} ({src})", data)


def verify_edge_sound(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.edge_sound"
    w, snd = spec.get("word"), spec.get("claimed_edge_sound")
    if w is None or snd is None:
        return na(name)
    key = re.sub(r"\s+", " ", str(snd).strip().lower().strip("/"))
    if key not in SOUND_NAMES:
        return na(name, f"{snd!r} is not a sound the convention names — declined")
    pos = str(spec.get("position") or "first").lower()
    claimed = spec.get("claimed", True)
    prons, src = _prons_for(spec, "word", "pronunciation")
    if not prons:
        return _declined_word(name, w)
    want = SOUND_NAMES[key]
    hits = [p for p in prons if strip_stress(p) and (strip_stress(p)[-1] if pos == "last" else strip_stress(p)[0]) in want]
    actual = bool(hits)
    p = hits[0] if hits else prons[0]
    edge = (strip_stress(p)[-1] if pos == "last" else strip_stress(p)[0]) if strip_stress(p) else ""
    data = {"word": w, "pronunciation": p, "position": pos, "sound": key, "arpabet": list(want), "edge_phoneme": edge,
            "actual": actual, "claimed": bool(claimed), "source": src,
            "convention": "ARPABET (CMU): the first/last phoneme; sound names mapped to ARPABET consonants"}
    where = "ends" if pos == "last" else "begins"
    if actual == bool(claimed):
        return confirm(name, f"{w!r} = {p}: {where} with {edge} ({'the ' + key + ' sound' if actual else 'not the ' + key + ' sound'}; matches claim; {src})", data)
    return mismatch(name, f"{w!r} = {p}: {where} with {edge}, claimed {'' if claimed else 'not '}the {key} sound ({src})", data)


# ── ETYMOLOGY — where a word came from, as Webster 1913 wrote it (the etymology shelf) ───────────────────────
# The keeping's etymology shelf carries Webster's Revised Unabridged Dictionary (1913), public domain: the languages
# and forms each headword came through, in Webster's own abbreviations. A claim "X comes from Latin" HOLDS when the
# claimed language stands in the DERIVATION part of the held chain (the part before 'cf.' / 'akin to' / 'See', which
# compare cognates and do not derive); it is BROKEN only when the chain derives the word through languages of other
# families altogether (a wholly Germanic chain against a Latin claim); it is DECLINED when the family is present but
# the language is not named (Webster may not list the intermediary), when the language appears only as a comparison,
# or when the word is not held. A claimed source form ('the Latin word salarium') or gloss ('the Latin word for little
# mouse') must appear in the chain to confirm; absent, the check DECLINES — the chain is OCR text, never called wrong.
LANG_ABBR: Dict[str, Tuple[str, ...]] = {
    "latin": ("L", "LL", "NL", "ML"), "late latin": ("LL",), "low latin": ("LL",), "medieval latin": ("LL", "ML"),
    "new latin": ("NL",), "modern latin": ("NL",), "classical latin": ("L",),
    "greek": ("Gr", "NGr", "MGr"), "ancient greek": ("Gr",), "modern greek": ("NGr", "MGr"),
    "french": ("F", "OF"), "old french": ("OF",), "middle french": ("F",), "norman french": ("OF",),
    "old english": ("AS", "OE"), "anglo-saxon": ("AS",), "anglo saxon": ("AS",), "middle english": ("ME", "OE"),
    "old norse": ("Icel",), "norse": ("Icel",), "icelandic": ("Icel",),
    "german": ("G", "OHG", "MHG"), "old high german": ("OHG",), "middle high german": ("MHG",), "low german": ("LG",),
    "dutch": ("D", "OD"), "old dutch": ("OD",), "old saxon": ("OS",), "frisian": ("Fries", "OFries"),
    "italian": ("It",), "spanish": ("Sp",), "portuguese": ("Pg",), "provencal": ("Pr", "Prov"), "provençal": ("Pr", "Prov"),
    "arabic": ("Ar",), "hebrew": ("Heb",), "aramaic": ("Chald", "Syr"), "chaldee": ("Chald",), "syriac": ("Syr",),
    "persian": ("Per",), "sanskrit": ("Skr",), "hindi": ("Hind",), "hindustani": ("Hind",), "bengali": ("Bengalee", "Bengali"),
    "turkish": ("Turk",), "russian": ("Russ",), "polish": ("Pol",), "czech": ("Bohem",), "bohemian": ("Bohem",),
    "welsh": ("W",), "irish": ("Ir",), "gaelic": ("Gael",), "scottish gaelic": ("Gael",), "celtic": ("Celt", "W", "Ir", "Gael"),
    "chinese": ("Chin",), "japanese": ("Jap",), "malay": ("Malay",), "tamil": ("Tamil",), "gothic": ("Goth",),
    "danish": ("Dan",), "swedish": ("Sw",), "norwegian": ("Norw",),
    "scandinavian": ("Scand", "Icel", "Dan", "Sw", "Norw"),
    "germanic": ("Teut", "AS", "OE", "ME", "Icel", "G", "OHG", "MHG", "LG", "D", "OD", "OS", "Dan", "Sw", "Norw", "Goth", "Scand", "Fries", "OFries"),
    "teutonic": ("Teut", "AS", "OE", "ME", "Icel", "G", "OHG", "MHG", "LG", "D", "OD", "OS", "Dan", "Sw", "Norw", "Goth", "Scand", "Fries", "OFries"),
    "romance": ("F", "OF", "It", "Sp", "Pg", "Pr", "Prov"),
    "egyptian": ("Egypt",), "hungarian": ("Hung",), "finnish": ("Finn",), "lithuanian": ("Lith",),
    "slavic": ("Slav", "Russ", "Pol", "Bohem"), "slavonic": ("Slav", "Russ", "Pol", "Bohem"),
}
LANG_FAMILY: Dict[str, str] = {}
for _fam, _abbrs in (
        ("germanic", ("Teut", "AS", "OE", "ME", "Icel", "G", "OHG", "MHG", "LG", "D", "OD", "OS", "Dan", "Sw", "Norw", "Goth", "Scand", "Fries", "OFries")),
        ("italic", ("L", "LL", "NL", "ML", "F", "OF", "It", "Sp", "Pg", "Pr", "Prov")),
        ("hellenic", ("Gr", "NGr", "MGr")), ("semitic", ("Heb", "Ar", "Chald", "Syr")),
        ("indo-iranian", ("Skr", "Per", "Hind", "Bengalee", "Bengali")), ("celtic", ("Celt", "W", "Ir", "Gael")),
        ("slavic", ("Slav", "Russ", "Pol", "Bohem")), ("turkic", ("Turk",)), ("sinitic", ("Chin",)), ("japonic", ("Jap",)),
        ("austronesian", ("Malay",)), ("dravidian", ("Tamil",)), ("uralic", ("Hung", "Finn")), ("baltic", ("Lith",)),
        ("egyptian", ("Egypt",))):
    for _a in _abbrs:
        LANG_FAMILY[_a] = _fam
_ABBR_RE = re.compile(r"\b(" + "|".join(sorted(LANG_FAMILY, key=len, reverse=True)) + r")\.")
_BARE_RE = re.compile(r"\b(Bengalee|Bengali|Tamil|Malay)\b")
_DERIVATION_CUT = re.compile(r"\b(?:cf\.|Cf\.|akin to|Akin to|See\b|see\b|compare\b)")
ETYMOLOGY_SOURCE = "Webster's Revised Unabridged Dictionary (1913), Project Gutenberg eBook #29765 — public domain"
ETYMOLOGY_CONVENTION = ("Webster's abbreviations (L. Latin, LL. Late Latin, Gr. Greek, F. French, OF. Old French, AS. Anglo-Saxon, "
                        "OE. Old English, ME. Middle English, Icel. Icelandic = the Old Norse of the sagas, G. German, D. Dutch, It. Italian, "
                        "Sp. Spanish, Ar. Arabic, Heb. Hebrew, Skr. Sanskrit ...); 'cf.' and 'akin to' compare cognates and do not derive")


def _langs_in(text: str) -> List[str]:
    return [m.group(1) for m in _ABBR_RE.finditer(text)] + [m.group(1) for m in _BARE_RE.finditer(text)]


def derivation_part(etym: str) -> str:
    """The part of a Webster etymology that DERIVES (before the first cf. / akin to / See)."""
    m = _DERIVATION_CUT.search(etym)
    return etym[:m.start()] if m else etym


def _norm(s: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _form_in(form: str, text: str) -> bool:
    """A claimed source form stands in the chain: exact, or sharing a stem of five letters with a chain word."""
    f = _norm(form).strip("'\"")
    if not f:
        return False
    words = re.findall(r"[a-z\-]+", _norm(text))
    if f in words:
        return True
    return len(f) >= 5 and any(len(w) >= 5 and (w.startswith(f[:5]) and f.startswith(w[:5])) and (w.startswith(f) or f.startswith(w)) for w in words)


def etymologies_from_body(body: str) -> List[str]:
    """The etymology texts held in an etymology card's body: everything between [ and ]."""
    return [e.strip() for e in re.findall(r"\[(.*?)\]", str(body or "")) if e.strip()]


def _judge_origin(etym: str, lang: str, form: Optional[str], gloss: Optional[str]) -> Tuple[str, str]:
    """('yes' | 'no' | 'na', reason) for ONE etymology text against a claimed language (and form / gloss)."""
    der = derivation_part(etym)
    want = set(LANG_ABBR[lang])
    in_der = [a for a in _langs_in(der) if a in want]
    in_any = [a for a in _langs_in(etym) if a in want]
    if in_der:
        if form is not None and not _form_in(form, der):
            return "na", f"Webster derives it through {in_der[0]}. but the chain does not show the form {form!r}: [{etym}]"
        if gloss is not None and _norm(gloss) not in _norm(der):
            return "na", f"Webster derives it through {in_der[0]}. but the chain does not carry the gloss {gloss!r}: [{etym}]"
        return "yes", f"[{etym}] — {in_der[0]}. stands in the derivation"
    if in_any:
        return "na", f"Webster compares it with {in_any[0]}. ('cf.' / 'akin to') but does not derive it from {lang}: [{etym}]"
    fams = {LANG_FAMILY[a] for a in _langs_in(der) if a in LANG_FAMILY}
    my_fams = {LANG_FAMILY[a] for a in want if a in LANG_FAMILY}
    if fams and my_fams and not (fams & my_fams):
        return "no", f"Webster derives it through {', '.join(sorted(a + '.' for a in set(_langs_in(der))))} ({', '.join(sorted(fams))}), no {lang} in the chain: [{etym}]"
    return "na", f"the held chain does not name {lang}: [{etym}]"


def verify_origin(spec: Dict[str, Any]) -> VerifierResult:
    name = "wordcraft.origin"
    w, lang = spec.get("word"), spec.get("claimed_language")
    if w is None or lang is None:
        return na(name)
    key = re.sub(r"\s+", " ", str(lang).strip().lower())
    if key not in LANG_ABBR:
        return na(name, f"{lang!r} is not a language the convention names — declined")
    claimed = bool(spec.get("claimed_origin", True))
    form = spec.get("claimed_source_word")
    gloss = spec.get("claimed_gloss")
    given = spec.get("etymology")
    if given:
        etyms = [str(e).strip() for e in (given if isinstance(given, (list, tuple)) else [given]) if str(e).strip()]
        src = "etymology given in the spec"
    else:
        card = _shelf_card_of(str(w), "etymology", "card_src_etym_", "etymology")
        if not card:
            return na(name, f"{w!r} is not on the keeping's etymology shelf (or no corpus is loaded) — declined, not judged")
        etyms = etymologies_from_body(str(card.get("body") or ""))
        src = str((card.get("source") or {}).get("label") or ETYMOLOGY_SOURCE)
    if not etyms:
        return na(name, f"{w!r}: no etymology held — declined")
    judged = [_judge_origin(e, key, str(form) if form is not None else None, str(gloss) if gloss is not None else None) for e in etyms]
    data = {"word": w, "claimed_language": key, "claimed_origin": claimed, "claimed_source_word": form, "claimed_gloss": gloss,
            "etymologies": etyms, "source": src, "convention": ETYMOLOGY_CONVENTION}
    yes = [r for v, r in judged if v == "yes"]
    no = [r for v, r in judged if v == "no"]
    if claimed:
        if yes:
            return confirm(name, f"{w!r} comes from {key}: {yes[0]} (matches claim; {src})", data)
        if no and len(no) == len(judged):
            return mismatch(name, f"{w!r}: {no[0]} ({src})", data)
        return na(name, f"{w!r}: {judged[0][1]} — declined, not judged ({src})", data)
    if yes:
        return mismatch(name, f"{w!r} does come from {key}: {yes[0]} — claimed it does not ({src})", data)
    if no and len(no) == len(judged):
        return confirm(name, f"{w!r} does not come from {key}: {no[0]} (matches claim; {src})", data)
    return na(name, f"{w!r}: {judged[0][1]} — declined, not judged ({src})", data)

_RULES = [
    (lambda wv: "word" in wv and any(k in wv for k in ("claimed_letters", "claimed_vowels", "claimed_consonants")), verify_letters),
    (lambda wv: "word_a" in wv and "word_b" in wv and "claimed_anagram" in wv, verify_anagram),
    (lambda wv: "word" in wv and "claimed_palindrome" in wv, verify_palindrome),
    (lambda wv: "word_a" in wv and "word_b" in wv and "claimed_edit_distance" in wv, verify_edit_distance),
    (lambda wv: "word" in wv and ("claimed_syllables" in wv or "claimed_phonemes" in wv), verify_syllables),
    (lambda wv: "alphabet" in wv and "claimed_alphabet_letters" in wv, verify_alphabet),
    (lambda wv: "singular" in wv and "claimed_plural" in wv, verify_plural),
    (lambda wv: "letter" in wv and "claimed_rank" in wv, verify_letter_rank),
    # phonics (the pronunciation shelf) and etymology (the etymology shelf)
    (lambda wv: "word_a" in wv and "word_b" in wv and "claimed_rhyme" in wv, verify_rhyme),
    (lambda wv: "word_a" in wv and "word_b" in wv and "claimed_homophone" in wv, verify_homophone),
    (lambda wv: "word" in wv and "claimed_stress_syllable" in wv, verify_stress),
    (lambda wv: "word" in wv and "letter" in wv and "claimed_silent" in wv, verify_silent_letter),
    (lambda wv: "word" in wv and "claimed_vowel_sound" in wv, verify_vowel_sound),
    (lambda wv: "word" in wv and "claimed_edge_sound" in wv, verify_edge_sound),
    (lambda wv: "word" in wv and "claimed_language" in wv, verify_origin),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "WORD_VERIFY", _RULES, domain="wordcraft", none_reason="no WORD_VERIFY artifacts present")
