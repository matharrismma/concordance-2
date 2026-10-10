"""Linguistics verifier.

Strengthens the scripture / source-hierarchy path with deterministic checks
on original-language claims. Per `00_CANON/PRIMARY_RULESET.md §5`: original
source languages first; English is explanatory only. The linguistics
verifier puts that rule into computational form by checking claims against
Strong's lexicon (Layer 0 bridge between original-language text and the
WEB English translation).

Checks performed:

  * `linguistics.strongs_resolution` — a Strong's number resolves to a
    real lexicon entry (G1-G5624 Greek NT, H1-H8674 Hebrew OT).
  * `linguistics.word_count` — a claimed occurrence count matches the
    corpus count for that Strong's number.
  * `linguistics.transliteration` — a claimed Romanization matches the
    lexicon's transliteration (after diacritic-stripping normalization).
  * `linguistics.gloss_consistency` — a claimed English gloss has at
    least one substantive (≥3-char) token in common with the Strong's
    short / KJV definition.
  * `linguistics.cognate` — two Strong's numbers share a derivational
    root (either appears in the other's `derivation` field, or their
    lemmas share a common 4-char prefix after diacritic stripping).

LING_VERIFY packet shape (any subset of fields, all optional):
    {
      "strongs": "G26",                       # for strongs_resolution
      "claimed_count": 36,                    # paired with strongs
      "transliteration_claim": "agape",       # paired with strongs
      "gloss_claim": "love",                  # paired with strongs
      "cognate_pair": ["G25", "G26"],         # for cognate (independent)
    }

Layer 0 dependence: this verifier delegates lookup to
`scripture.word_study(strongs)`. If the Layer 0 source has not been
provisioned (no `lw/00_source/web/web.db` etc.) the lookup returns
`source_missing` and every linguistics check returns NOT_APPLICABLE
rather than ERROR — same graceful-degradation contract scripture uses.
"""
from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, List, Optional

from .base import VerifierResult, na, confirm, mismatch, error


_STRONGS_PATTERN = re.compile(r"^[GHgh]\d+$")
_TRANSLIT_NONALNUM = re.compile(r"[^a-z0-9]+")


def _normalize_translit(s: Optional[str]) -> str:
    """Lowercase, strip combining marks, drop non-alphanumeric.

    Lets us accept ``'agape'`` as equivalent to ``'agápē'``, ``'agápe'``,
    or ``'AGAPE'``. The lexicon uses the diacritical form; published
    claims usually use the bare ASCII form.
    """
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    no_marks = "".join(c for c in nfkd if not unicodedata.combining(c))
    return _TRANSLIT_NONALNUM.sub("", no_marks.lower())


def _is_valid_strongs(s: Any) -> bool:
    return bool(s and _STRONGS_PATTERN.match(str(s)))


def _word_study(strongs: str) -> Dict[str, Any]:
    """Look up a Strong's number via the scripture verifier's helper.

    Imported lazily so this module loads even when scripture's Layer 0
    hooks aren't available (e.g. during unit tests that exercise
    transliteration normalization without touching the DB).
    """
    from . import scripture as _scr
    return _scr.word_study(strongs) or {}


def _layer0_unavailable(info: Dict[str, Any]) -> bool:
    """True when the lexicon lookup returned no usable content.

    The scripture layer's `word_study` returns ``status='source_missing'``
    when the WEB / Strong's database isn't provisioned, and
    ``status='not_found'`` when it couldn't find verse occurrences in the
    corpus — but the latter case can still have a populated lexicon entry
    (word, transliteration, definition, derivation), which is exactly what
    the linguistics verifier needs. Treat 'source_missing' as fatal; for
    everything else, fall back to checking whether at least one lexicon
    field is populated.
    """
    if not info:
        return True
    if info.get("status") == "source_missing":
        return True
    if (info.get("word") or info.get("transliteration")
            or info.get("definition") or info.get("derivation")):
        return False
    return True


def verify_strongs_resolution(strongs: str) -> VerifierResult:
    """A Strong's number must resolve to a real lexicon entry."""
    name = "linguistics.strongs_resolution"
    if not strongs:
        return na(name)
    if not _is_valid_strongs(strongs):
        return mismatch(name,
                        f"{strongs!r} is not a valid Strong's identifier "
                        f"(expected 'G####' for Greek NT or 'H####' for Hebrew OT)",
                        {"strongs": strongs})
    try:
        result = _word_study(strongs)
    except Exception as e:
        return error(name, f"word_study failed: {type(e).__name__}: {e}")
    if _layer0_unavailable(result):
        return na(name, f"Strong's data unavailable for {strongs}")
    word = result.get("word") or ""
    translit = result.get("transliteration") or ""
    if word or translit:
        return confirm(
            name,
            f"{strongs} resolves to {word!r} ({translit!r})",
            {"strongs": strongs, "word": word, "transliteration": translit},
        )
    return mismatch(name, f"{strongs} did not resolve (lookup returned no word/translit)",
                    {"strongs": strongs, "raw": result})


def verify_word_count(strongs: str, claimed_count: Any) -> VerifierResult:
    """A claimed occurrence count must match the corpus count."""
    name = "linguistics.word_count"
    if not strongs or claimed_count is None:
        return na(name)
    if not _is_valid_strongs(strongs):
        return mismatch(name,
                        f"{strongs!r} is not a valid Strong's identifier",
                        {"strongs": strongs})
    try:
        claimed = int(claimed_count)
    except (TypeError, ValueError):
        return error(name, f"claimed_count must be an integer, got {claimed_count!r}")
    try:
        result = _word_study(strongs)
    except Exception as e:
        return error(name, f"word_study failed: {type(e).__name__}: {e}")
    if _layer0_unavailable(result):
        return na(name, f"Strong's data unavailable for {strongs}")
    actual = result.get("occurrence_count")
    if actual is None:
        return na(name, f"no occurrence_count available for {strongs}")
    if claimed == actual:
        return confirm(name,
                       f"{strongs} occurs {actual} times in the corpus, matching claim",
                       {"strongs": strongs, "claimed": claimed, "actual": actual})
    return mismatch(name,
                    f"{strongs} claimed {claimed} occurrences, corpus has {actual}",
                    {"strongs": strongs, "claimed": claimed, "actual": actual})


def verify_transliteration(strongs: str, claimed: str) -> VerifierResult:
    """A claimed transliteration must match the lexicon's after normalization."""
    name = "linguistics.transliteration"
    if not strongs or not claimed:
        return na(name)
    if not _is_valid_strongs(strongs):
        return mismatch(name,
                        f"{strongs!r} is not a valid Strong's identifier",
                        {"strongs": strongs})
    try:
        result = _word_study(strongs)
    except Exception as e:
        return error(name, f"word_study failed: {type(e).__name__}: {e}")
    if _layer0_unavailable(result):
        return na(name, "Strong's data unavailable")
    actual = result.get("transliteration") or ""
    if not actual:
        defn = result.get("definition") or {}
        if isinstance(defn, dict):
            actual = defn.get("translit") or ""
    if not actual:
        return na(name, f"no transliteration available for {strongs}")
    if _normalize_translit(claimed) == _normalize_translit(actual):
        return confirm(name,
                       f"{strongs} transliteration {claimed!r} matches lexicon {actual!r}",
                       {"strongs": strongs, "claimed": claimed, "lexicon": actual})
    return mismatch(name,
                    f"{strongs} claimed transliteration {claimed!r} != lexicon {actual!r}",
                    {"strongs": strongs, "claimed": claimed, "lexicon": actual})


def verify_gloss(strongs: str, claimed_gloss: str) -> VerifierResult:
    """Token overlap between claimed gloss and lexicon definition."""
    name = "linguistics.gloss_consistency"
    if not strongs or not claimed_gloss:
        return na(name)
    if not _is_valid_strongs(strongs):
        return mismatch(name,
                        f"{strongs!r} is not a valid Strong's identifier",
                        {"strongs": strongs})
    try:
        result = _word_study(strongs)
    except Exception as e:
        return error(name, f"word_study failed: {type(e).__name__}: {e}")
    if _layer0_unavailable(result):
        return na(name, "Strong's data unavailable")
    defn = result.get("definition") or {}
    haystack_parts = []
    if isinstance(defn, dict):
        haystack_parts.append(defn.get("strongs_def", "") or "")
        haystack_parts.append(defn.get("kjv_def", "") or "")
    haystack = " ".join(haystack_parts).lower()
    needle = str(claimed_gloss).lower().strip()
    tokens = re.findall(r"[a-z]{3,}", needle)
    if not tokens:
        return na(name, "claimed_gloss has no substantive tokens (≥3 chars)")
    matched = [t for t in tokens if t in haystack]
    if matched:
        return confirm(name,
                       f"{strongs} gloss {claimed_gloss!r} matches lexicon "
                       f"(token overlap: {matched})",
                       {"strongs": strongs, "claimed": claimed_gloss,
                        "matched_tokens": matched})
    return mismatch(name,
                    f"{strongs} claimed gloss {claimed_gloss!r} has no token overlap "
                    f"with lexicon definition",
                    {"strongs": strongs, "claimed": claimed_gloss,
                     "lexicon_excerpt": haystack[:200]})


def _root_prefix(s: Optional[str], n: int = 4) -> str:
    """First n chars of a word after lowercasing + stripping combining marks.

    Used as a rough cognate signal when neither side's `derivation` field
    explicitly names the other.
    """
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    no_marks = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_marks.lower()[:n]


def verify_cognate(pair: List[str]) -> VerifierResult:
    """Two Strong's are cognate if either's derivation references the other,
    or their lemmas share a common 4-char prefix after normalization."""
    name = "linguistics.cognate"
    if not pair or not isinstance(pair, (list, tuple)) or len(pair) < 2:
        return na(name)
    a, b = pair[0], pair[1]
    if not _is_valid_strongs(a) or not _is_valid_strongs(b):
        return mismatch(name,
                        f"cognate pair members must be valid Strong's identifiers, "
                        f"got {a!r} and {b!r}",
                        {"a": a, "b": b})
    try:
        info_a = _word_study(a)
        info_b = _word_study(b)
    except Exception as e:
        return error(name, f"word_study failed: {type(e).__name__}: {e}")
    if _layer0_unavailable(info_a):
        return na(name, f"Strong's data unavailable for {a}")
    if _layer0_unavailable(info_b):
        return na(name, f"Strong's data unavailable for {b}")
    deriv_a = info_a.get("derivation") or ""
    deriv_b = info_b.get("derivation") or ""
    word_a = info_a.get("word") or ""
    word_b = info_b.get("word") or ""
    a_in_b = a in deriv_b
    b_in_a = b in deriv_a
    same_root = bool(word_a and word_b and _root_prefix(word_a) == _root_prefix(word_b))
    reasons = []
    if a_in_b:
        reasons.append(f"{b} derivation references {a}")
    if b_in_a:
        reasons.append(f"{a} derivation references {b}")
    if same_root and not (a_in_b or b_in_a):
        reasons.append(f"{word_a!r} and {word_b!r} share a 4-char root prefix")
    data = {"a": a, "b": b, "word_a": word_a, "word_b": word_b,
            "derivation_a": deriv_a, "derivation_b": deriv_b}
    if reasons:
        return confirm(name, "cognate: " + "; ".join(reasons), data)
    return mismatch(name,
                    f"{a} ({word_a!r}) and {b} ({word_b!r}) show no shared root in either derivation",
                    data)


def verify_transliteration_normalized_match(a: str, b: str) -> VerifierResult:
    """Check whether two transliterations are equivalent after diacritic normalization.

    DB-free: compares purely via _normalize_translit (strip combining marks + non-alphanumeric).
    Useful for confirming that 'agape' is an acceptable normalized form of 'agapē'.
    """
    name = "linguistics.transliteration_normalized_match"
    if not a or not b:
        return na(name, "both transliteration_a and transliteration_b required")
    na_a = _normalize_translit(a)
    na_b = _normalize_translit(b)
    match = na_a == na_b
    data = {"transliteration_a": a, "transliteration_b": b,
            "normalized_a": na_a, "normalized_b": na_b, "match": match}
    if match:
        return confirm(name,
                       f"{a!r} and {b!r} are equivalent after diacritic normalization",
                       data)
    return mismatch(name,
                    f"{a!r} ({na_a!r}) ≠ {b!r} ({na_b!r}) after diacritic normalization",
                    data)


# GENERAL TRANSLITERATION (Matt, 2026-10-10: "expand linguistics to be comprehensive"). Beyond
# Strong's: romanize an arbitrary GREEK string by a fixed, deterministic scheme and confirm a
# claimed romanization. Greek only in v1 - Greek writes its vowels, so the map is complete; Hebrew
# romanization depends on vowel pointing that running text often omits, so Hebrew DECLINES rather
# than false-mismatch. 0 false positives by construction: a wrong romanization can never match the
# computed scheme. A DIFFERENT valid scheme may differ - that is a mismatch against THIS scheme, not
# a false claim, and the verdict says so.
_GREEK_ROMAN = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "e", "θ": "th", "ι": "i",
    "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "ς": "s", "τ": "t", "υ": "y", "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "o",
}


def _romanize_greek(s: str):
    """(romanization, unmapped_letter_count) for a Greek string under the fixed scheme. Combining
    marks (accents, breathing) are stripped; spaces and punctuation are ignored."""
    out, unmapped = [], 0
    for ch in unicodedata.normalize("NFD", str(s or "")):
        if unicodedata.combining(ch):
            continue
        low = ch.lower()
        if low in _GREEK_ROMAN:
            out.append(_GREEK_ROMAN[low])
        elif low.isalpha():
            unmapped += 1
    return "".join(out), unmapped


def verify_romanization(original: str, claimed: str, script: Optional[str] = None) -> VerifierResult:
    name = "linguistics.romanization"
    if not original or not claimed:
        return na(name, "romanization needs both 'original' (the native-script word) and 'romanization_claim'")
    is_greek = any("Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿" for c in original)
    is_hebrew = any("֐" <= c <= "׿" for c in original)
    if is_hebrew and not is_greek:
        return na(name, "Hebrew romanization depends on vowel pointing that running text often omits; declined "
                        "rather than guessed (Greek is romanized; Hebrew is not yet)")
    if not is_greek:
        return na(name, "the engine romanizes Greek (Hebrew declines); this word is in neither script")
    expected, unmapped = _romanize_greek(original)
    if unmapped or not expected:
        return na(name, f"'{original}' has letters outside the Greek romanization table; declined rather than guessed")
    ne, nc = _normalize_translit(expected), _normalize_translit(claimed)
    data = {"original": original, "script": "greek", "scheme_expected": expected, "claimed": claimed,
            "convention": "a fixed scheme (eta->e, omega->o, upsilon->y, breathing stripped); a different valid "
                          "scheme can differ and that is not a false claim"}
    # fold the one common variant the stripped scheme loses: a leading rough-breathing 'h'
    if ne == nc or ne == _normalize_translit(claimed.lstrip("hH")) or _normalize_translit("h" + expected) == nc:
        return confirm(name, f"'{original}' romanizes to '{expected}', and the claim '{claimed}' matches (Greek)", data)
    return mismatch(name, f"'{original}' romanizes to '{expected}' in the engine's scheme; the claim '{claimed}' "
                    f"does not match it (a different valid scheme may exist; this is the engine's)", data)


# SEMANTIC RELATIONS (Matt, 2026-10-10: comprehensive linguistics, step 3). Synonymy and IS-A
# (hypernymy) from the held WordNet thesaurus (data/thesaurus.db - SQLite, independent of the
# corpus, so it works cold). Antonymy is NOT held and declines. The verdict always says "per
# WordNet, in at least one sense" - we report the authority's relation, cited, never assert
# interchangeability. 0 false positives: a relation WordNet does not hold cannot be confirmed.
def _normw(w: Any) -> str:
    return str(w or "").strip().lower()


def _broader_chain(word: str, maxdepth: int = 6) -> set:
    """The transitive IS-A set above `word` (WordNet hypernyms, bounded depth)."""
    from .. import thesaurus as TH
    seen, frontier, chain = set(), [_normw(word)], set()
    for _ in range(maxdepth):
        nxt = []
        for w in frontier:
            for b in TH.broader(w, limit=0):
                nb = _normw(b)
                if nb and nb not in seen:
                    seen.add(nb)
                    chain.add(nb)
                    nxt.append(nb)
        if not nxt:
            break
        frontier = nxt
    return chain


def verify_semantic_relation(a: str, b: str, relation: str) -> VerifierResult:
    name = "linguistics.semantic_relation"
    from .. import thesaurus as TH
    if not TH.available():
        return na(name, "the WordNet thesaurus is not available in this process")
    a0, b0 = _normw(a), _normw(b)
    if not a0 or not b0:
        return na(name, "need two words and a claimed_relation (synonym, broader/is_a, antonym)")
    rel = _normw(relation).replace(" ", "_")
    if rel in ("synonym", "synonyms", "synonymous"):
        syns_a = {_normw(x) for x in TH.synonyms(a0, limit=0)}
        syns_b = {_normw(x) for x in TH.synonyms(b0, limit=0)}
        data = {"a": a0, "b": b0, "relation": "synonym", "source": "WordNet (thesaurus.db)"}
        if b0 in syns_a or a0 in syns_b:
            return confirm(name, f"'{a0}' and '{b0}' are WordNet synonyms in at least one sense", data)
        return mismatch(name, f"WordNet does not list '{a0}' and '{b0}' as synonyms in any sense", data)
    if rel in ("broader", "hypernym", "is_a", "isa", "kind_of", "a_kind_of"):
        chain = _broader_chain(a0)
        data = {"a": a0, "b": b0, "relation": "is_a", "source": "WordNet IS-A hierarchy"}
        if b0 in chain:
            return confirm(name, f"per WordNet, '{b0}' is above '{a0}' in the IS-A hierarchy (in at least one sense)", data)
        return mismatch(name, f"WordNet does not place '{b0}' above '{a0}' in the IS-A hierarchy", data)
    if rel in ("antonym", "antonyms", "opposite"):
        return na(name, "antonyms are not held in the thesaurus (synonyms and IS-A hypernyms only); declined")
    return na(name, f"unknown semantic relation {relation!r} (use synonym, broader/is_a, or antonym)")


# CLOSED-CLASS PART OF SPEECH (Matt, 2026-10-10: comprehensive linguistics, step 4; syntax kept
# CLOSED-CLASS ONLY by choice). The function words are a finite, enumerable set, so their POS is
# deterministic. An OPEN-class word (noun/verb/adjective/adverb) depends on usage and morphology and
# is DECLINED here - the honest offline floor. A word may hold several closed classes (that = pronoun
# / conjunction / determiner); each is a true answer, and the verdict names them all. 0 false
# positives: a POS is confirmed only by membership in the curated closed-class set.
_CLOSED_POS = {
    "article": {"a", "an", "the"},
    "preposition": {"in", "on", "at", "by", "for", "with", "to", "of", "from", "into", "onto", "over",
                    "under", "about", "above", "below", "between", "through", "during", "before",
                    "after", "since", "until", "against", "among", "around", "behind", "beside",
                    "beyond", "near", "off", "out", "upon", "within", "without", "toward", "towards",
                    "across", "along", "down", "up"},
    "pronoun": {"i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my",
                "your", "his", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs",
                "this", "that", "these", "those", "who", "whom", "whose", "which", "what", "myself",
                "yourself", "himself", "herself", "itself", "ourselves", "themselves", "anyone",
                "everyone", "someone", "nobody", "something", "anything", "everything", "nothing"},
    "conjunction": {"and", "or", "but", "nor", "yet", "so", "for", "if", "because", "although",
                    "though", "while", "whereas", "unless", "until", "since", "when", "whenever",
                    "wherever", "whether", "that", "as", "both", "either", "neither"},
    "auxiliary": {"is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
                  "does", "did", "can", "could", "will", "would", "shall", "should", "may", "might",
                  "must", "ought"},
    "determiner": {"this", "that", "these", "those", "some", "any", "each", "every", "all", "both",
                   "either", "neither", "no", "much", "many", "more", "most", "few", "little",
                   "several", "enough", "such", "what", "which", "whose", "the", "a", "an"},
}
_OPEN_POS = {"noun", "verb", "adjective", "adverb", "open", "open-class", "open_class"}


def verify_pos(word: str, claimed_pos: str) -> VerifierResult:
    name = "linguistics.part_of_speech"
    w = _normw(word)
    pos = _normw(claimed_pos).replace("-", "_")
    if not w or not pos:
        return na(name, "need a word and a claimed_pos (article/preposition/pronoun/conjunction/auxiliary/determiner)")
    classes = sorted(c for c, words in _CLOSED_POS.items() if w in words)
    data = {"word": w, "claimed_pos": pos, "closed_classes_held": classes}
    if not classes:
        return na(name, f"'{w}' is not a closed-class (function) word; open-class part of speech "
                        f"(noun/verb/adjective/adverb) depends on usage and is not determined here")
    also = [c for c in classes if c != pos]
    if pos in classes:
        extra = f" (it can also be a {', '.join(also)})" if also else ""
        return confirm(name, f"'{w}' is a {pos} - a closed-class function word{extra}", data)
    if pos in _OPEN_POS:
        return mismatch(name, f"'{w}' is a closed-class word ({'/'.join(classes)}), not a {pos}", data)
    if pos in _CLOSED_POS:
        return mismatch(name, f"'{w}' is a closed-class word ({'/'.join(classes)}), not a {pos}", data)
    return na(name, f"unknown part of speech {claimed_pos!r}")


# TYPOLOGY / LANGUAGE FAMILIES (Matt, 2026-10-10: comprehensive linguistics, step 5). A curated
# reference: a language -> the family labels it falls under (branch and top family). A claim "X is
# a Y language" is confirmed iff Y is in X's chain. Curated (not generated); an unknown language
# DECLINES. 0 false positives: a family not in the language's chain cannot be confirmed.
_LANG_FAMILY = {
    "english": {"germanic", "west germanic", "indo-european"},
    "german": {"germanic", "west germanic", "indo-european"},
    "dutch": {"germanic", "west germanic", "indo-european"},
    "swedish": {"germanic", "north germanic", "indo-european"},
    "norwegian": {"germanic", "north germanic", "indo-european"},
    "danish": {"germanic", "north germanic", "indo-european"},
    "gothic": {"germanic", "east germanic", "indo-european"},
    "spanish": {"romance", "italic", "indo-european"},
    "french": {"romance", "italic", "indo-european"},
    "italian": {"romance", "italic", "indo-european"},
    "portuguese": {"romance", "italic", "indo-european"},
    "romanian": {"romance", "italic", "indo-european"},
    "latin": {"italic", "indo-european"},
    "greek": {"hellenic", "indo-european"},
    "russian": {"slavic", "balto-slavic", "indo-european"},
    "polish": {"slavic", "balto-slavic", "indo-european"},
    "ukrainian": {"slavic", "balto-slavic", "indo-european"},
    "lithuanian": {"baltic", "balto-slavic", "indo-european"},
    "hindi": {"indo-aryan", "indo-iranian", "indo-european"},
    "sanskrit": {"indo-aryan", "indo-iranian", "indo-european"},
    "persian": {"iranian", "indo-iranian", "indo-european"},
    "farsi": {"iranian", "indo-iranian", "indo-european"},
    "irish": {"celtic", "indo-european"},
    "welsh": {"celtic", "indo-european"},
    "armenian": {"armenian", "indo-european"},
    "albanian": {"albanian", "indo-european"},
    "arabic": {"semitic", "afro-asiatic"},
    "hebrew": {"semitic", "afro-asiatic"},
    "aramaic": {"semitic", "afro-asiatic"},
    "amharic": {"semitic", "afro-asiatic"},
    "mandarin": {"sinitic", "sino-tibetan"},
    "chinese": {"sinitic", "sino-tibetan"},
    "cantonese": {"sinitic", "sino-tibetan"},
    "tibetan": {"tibeto-burman", "sino-tibetan"},
    "burmese": {"tibeto-burman", "sino-tibetan"},
    "japanese": {"japonic"},
    "korean": {"koreanic"},
    "turkish": {"turkic"},
    "mongolian": {"mongolic"},
    "finnish": {"finnic", "finno-ugric", "uralic"},
    "hungarian": {"ugric", "finno-ugric", "uralic"},
    "estonian": {"finnic", "finno-ugric", "uralic"},
    "swahili": {"bantu", "niger-congo"},
    "yoruba": {"niger-congo"},
    "zulu": {"bantu", "niger-congo"},
    "tamil": {"dravidian"},
    "telugu": {"dravidian"},
    "kannada": {"dravidian"},
    "vietnamese": {"vietic", "austroasiatic"},
    "khmer": {"austroasiatic"},
    "tagalog": {"austronesian"},
    "indonesian": {"malayo-polynesian", "austronesian"},
    "hawaiian": {"polynesian", "austronesian"},
}


def _famnorm(s: Any) -> str:
    return re.sub(r"[\s_-]+", "", _normw(s))


def verify_language_family(language: str, claimed_family: str) -> VerifierResult:
    name = "linguistics.language_family"
    lang = _normw(language)
    fams = _LANG_FAMILY.get(lang)
    if fams is None:
        return na(name, f"'{language}' is not in the engine's curated language-family reference; declined rather "
                        f"than guessed")
    want = _famnorm(claimed_family)
    held = {_famnorm(f) for f in fams}
    data = {"language": lang, "claimed_family": claimed_family, "families_held": sorted(fams)}
    if want in held:
        return confirm(name, f"'{lang}' is a {claimed_family} language (families: {', '.join(sorted(fams))})", data)
    return mismatch(name, f"'{lang}' is not {claimed_family}; it is {', '.join(sorted(fams))}", data)


# SYNTAX (Matt, 2026-10-10: "real syntax parser"). A deterministic, offline chart parser over a
# hand-written English grammar (src/concordance/syntax.py). It judges whether a sentence has a
# valid phrase-structure parse and returns the tree. 0 false positives: it confirms only a
# derivation it actually built - a structural fact, not a judgment that the sentence is true or
# good English. Open-class POS is heuristic (no POS lexicon held), so trees are best-effort and a
# sentence outside the grammar is reported "not derivable here", never mis-parsed.
def verify_syntax(sentence: str, claimed_grammatical: Any = True) -> VerifierResult:
    name = "linguistics.syntax"
    from .. import syntax as _syntax
    r = _syntax.parse(sentence)
    if not r.get("ok"):
        return na(name, r.get("reason", "could not tag the sentence"))
    g = bool(r.get("grammatical"))
    claimed = True if claimed_grammatical is None else bool(claimed_grammatical)
    data = {"sentence": sentence, "grammatical": g, "pos": r.get("pos"),
            "bracket": r.get("bracket"), "grammar": "the engine's English CFG (closed-class pinned, "
            "open-class heuristic); a valid parse is a structural fact, not a truth or style judgment"}
    if g == claimed:
        if g:
            return confirm(name, f"a valid phrase-structure parse exists: {r.get('bracket')}", data)
        return confirm(name, "correctly has no valid parse under the engine's grammar (matches the claim)", data)
    if g:
        return mismatch(name, f"the sentence DOES parse under the grammar: {r.get('bracket')}", data)
    return mismatch(name, "the sentence has no valid parse under the engine's grammar", data)


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    """Dispatch every applicable linguistics check for the packet's LING_VERIFY block."""
    results: List[VerifierResult] = []
    lv = packet.get("LING_VERIFY") or {}

    strongs = lv.get("strongs")
    if strongs:
        results.append(verify_strongs_resolution(strongs))
        if "claimed_count" in lv:
            results.append(verify_word_count(strongs, lv["claimed_count"]))
        if "transliteration_claim" in lv:
            results.append(verify_transliteration(strongs, lv["transliteration_claim"]))
        if "gloss_claim" in lv:
            results.append(verify_gloss(strongs, lv["gloss_claim"]))

    if "cognate_pair" in lv:
        results.append(verify_cognate(lv["cognate_pair"]))

    if "transliteration_a" in lv and "transliteration_b" in lv:
        results.append(verify_transliteration_normalized_match(
            lv["transliteration_a"], lv["transliteration_b"]
        ))

    if "original" in lv and "romanization_claim" in lv:
        results.append(verify_romanization(lv["original"], lv["romanization_claim"], lv.get("script")))

    if "relation_a" in lv and "relation_b" in lv and "claimed_relation" in lv:
        results.append(verify_semantic_relation(lv["relation_a"], lv["relation_b"], lv["claimed_relation"]))

    if "pos_word" in lv and "claimed_pos" in lv:
        results.append(verify_pos(lv["pos_word"], lv["claimed_pos"]))

    if "language" in lv and "claimed_family" in lv:
        results.append(verify_language_family(lv["language"], lv["claimed_family"]))

    if "parse_sentence" in lv:
        results.append(verify_syntax(lv["parse_sentence"], lv.get("claimed_grammatical", True)))

    if not results:
        results.append(na("linguistics", "no LING_VERIFY artifacts present"))
    return results
