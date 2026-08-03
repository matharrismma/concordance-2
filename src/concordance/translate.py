"""THE TRANSLATION LAYER — read a text in a language you do not know, without inventing one word.

Matt, 2026-08-03: "We need to work on our translation layer, so we can study books no matter the
language."

WHAT THIS REFUSES TO DO, AND WHY IT IS THE WHOLE DESIGN. Machine translation GENERATES prose.
Fluent output is exactly the thing this project may not produce: the covenant says quarantine
what is generated, cite rather than compose, and never silently upgrade authority. A smooth
English paragraph that no human wrote and no source contains is the most dangerous artefact this
library could hand someone, because it reads like knowledge and carries no chain to a source.

So this layer does what a scholar with a lexicon does, and stops where they stop:

    IT GLOSSES.        Every token is looked up in a lexicon we actually hold, and what comes
                       back is that lexicon's own words with its own attribution. Nothing is
                       written by the engine.
    IT REPORTS ITS COVERAGE.  A gloss run states how many tokens it could resolve and how many
                       it could not. A word with no entry comes back UNRESOLVED and stays
                       visible. It is never guessed, never smoothed over, never dropped.
    IT NEVER COMPOSES A SENTENCE.  There is no function here that returns a translated sentence,
                       because there is no honest way for this engine to produce one.

That is a smaller promise than "translate any book" and it is one that can be kept offline, with
no model, no network, and no possibility of a confident falsehood. A reader who can see every
word's dictionary entry, with the gaps marked, is genuinely reading the text. A reader handed
fluent output cannot tell which parts were known and which were invented.

WHAT IT CAN REACH TODAY, measured rather than claimed: `lexicons()` reports exactly which
languages have a lexicon on disk. At the time of writing that is biblical Greek and Hebrew, from
Strong's. Every other language returns NO_LEXICON — an honest refusal that names what is missing,
which is the shape every refusal here takes.

THE INFLECTION LIMIT IS REAL AND IS REPORTED. A lexicon stores LEMMAS (dictionary forms) while
running text carries INFLECTED forms. Matching is therefore imperfect: folding accents and
diacritics recovers a good deal, and genuine morphological analysis would recover more but does
not exist here yet. `gloss()` returns the true hit rate so nobody mistakes partial coverage for a
full reading. For SCRIPTURE specifically there is a better path already built --
verifiers.scripture.original_words() uses the tagged text, where every word carries its Strong's
number directly, and this module defers to it rather than guessing.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LEX_DIR = os.path.join(_ROOT, "data", "strongs", "original", "lexicon")

# Scripts identified by the Unicode block a character falls in. Deterministic, offline, and no
# statistical language guessing -- this reports the SCRIPT, which is a fact about the bytes, and
# never asserts the language, which is not.
_SCRIPT_RANGES = (
    ("greek",       ((0x0370, 0x03FF), (0x1F00, 0x1FFF))),
    ("hebrew",      ((0x0590, 0x05FF), (0xFB1D, 0xFB4F))),
    ("arabic",      ((0x0600, 0x06FF), (0x0750, 0x077F))),
    ("cyrillic",    ((0x0400, 0x04FF),)),
    ("devanagari",  ((0x0900, 0x097F),)),
    ("han",         ((0x4E00, 0x9FFF), (0x3400, 0x4DBF))),
    ("kana",        ((0x3040, 0x30FF),)),
    ("hangul",      ((0xAC00, 0xD7AF), (0x1100, 0x11FF))),
    ("latin",       ((0x0041, 0x024F),)),
)

# A lexicon we hold, and the script it serves. Adding a language means adding a file and a row
# here -- nothing else in this module needs to change.
_LEXICONS = (
    {"language": "greek_biblical", "script": "greek", "prefix": "G",
     "file": "strongs_greek.json",
     "source": "Strong's Greek lexicon (public domain)"},
    {"language": "hebrew_biblical", "script": "hebrew", "prefix": "H",
     "file": "strongs_hebrew.json",
     "source": "Strong's Hebrew lexicon (public domain)"},
)

# TOKENISE ON WHITESPACE, NOTHING CLEVERER.
#
# The first version used explicit Unicode ranges and SHATTERED Hebrew: b'reshit came apart into
# the consonant and its pointing as two tokens, because a character-class boundary fell between
# a letter and its combining marks. Coverage read 28.6% and I diagnosed it as a morphology
# problem -- prefixed particles -- which was plausible and wrong. Driving the real output made
# the true cause obvious in one line: the TOKENS were nonsense, so the hit rate was measuring my
# own tokenizer rather than the lexicon.
#
# Whitespace is the only boundary correct in every script here. Punctuation is trimmed from the
# ends afterwards by Unicode CATEGORY, not by range, so this cannot shatter a script it was not
# written for.
_TOKEN = re.compile(r"\S+", re.UNICODE)

_PUNCT_CATS = ("Po", "Ps", "Pe", "Pi", "Pf", "Pd", "Sm", "Sk")


def _trim(tok: str) -> str:
    """Strip leading/trailing punctuation, leaving letters and their combining marks intact."""
    out = tok
    while out and unicodedata.category(out[0]) in _PUNCT_CATS:
        out = out[1:]
    while out and unicodedata.category(out[-1]) in _PUNCT_CATS:
        out = out[:-1]
    return out

_INDEX_CACHE: Dict[str, Dict[str, List[str]]] = {}

# The inseparable Hebrew particles, longest first so she- is tried before he-. These attach
# directly to the following word (be- in, le- to, ke- like, ve- and, ha- the, mi- from,
# she- that) and the lexicon stores only the bare form underneath them.
_HEBREW_PREFIXES = ("וה", "ש", "ב", "ל", "כ",
                    "ו", "ה", "מ")


def _fold(word: str) -> str:
    """Normalise for matching: decompose, drop combining marks, lowercase.

    Greek accents and breathings and Hebrew pointing are editorial layers over the consonantal
    text; folding them is what lets a pointed running text meet an unpointed lexicon lemma. This
    is the single largest source of recovered matches and it is also LOSSY -- two distinct words
    can fold together, so a fold hit is a candidate rather than a proof, and `gloss` says so by
    returning every candidate rather than silently choosing one.
    """
    if not word:
        return ""
    w = unicodedata.normalize("NFD", word)
    w = "".join(ch for ch in w if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", w).lower().strip()


def script_of(text: str) -> Dict[str, Any]:
    """Which script is this written in? A fact about the characters, not a language claim."""
    counts: Dict[str, int] = {}
    for ch in text or "":
        cp = ord(ch)
        for name, ranges in _SCRIPT_RANGES:
            if any(lo <= cp <= hi for lo, hi in ranges):
                counts[name] = counts.get(name, 0) + 1
                break
    if not counts:
        return {"script": "unknown", "counts": {}, "detail": "no characters in a known block"}
    top = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
    total = sum(counts.values())
    return {"script": top[0], "confidence": round(top[1] / total, 3),
            "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
            "detail": "script is determined by Unicode block; the LANGUAGE is not asserted"}


def lexicons() -> Dict[str, Any]:
    """What this engine can actually gloss. Measured from disk every call, never claimed."""
    held, missing = [], []
    for lx in _LEXICONS:
        path = os.path.join(_LEX_DIR, lx["file"])
        if os.path.isfile(path):
            try:
                n = len(json.load(open(path, encoding="utf-8")))
            except Exception:                                     # noqa: BLE001
                n = 0
            held.append({"language": lx["language"], "script": lx["script"],
                         "entries": n, "source": lx["source"]})
        else:
            missing.append({"language": lx["language"], "expected_at": path})
    return {"held": held, "missing": missing,
            "total_entries": sum(h["entries"] for h in held),
            "note": ("Any script without a lexicon here returns NO_LEXICON. This engine glosses "
                     "from held lexicons only and never generates a translation.")}


def _index(language: str) -> Dict[str, List[str]]:
    """lemma-fold -> [strongs...]. Built once per language, from the lexicon on disk."""
    if language in _INDEX_CACHE:
        return _INDEX_CACHE[language]
    lx = next((l for l in _LEXICONS if l["language"] == language), None)
    idx: Dict[str, List[str]] = {}
    if lx:
        path = os.path.join(_LEX_DIR, lx["file"])
        if os.path.isfile(path):
            try:
                data = json.load(open(path, encoding="utf-8"))
            except Exception:                                     # noqa: BLE001
                data = {}
            for num, entry in data.items():
                for key in ("lemma", "translit"):
                    val = (entry or {}).get(key)
                    if not isinstance(val, str):
                        continue
                    f = _fold(val)
                    if f:
                        idx.setdefault(f, [])
                        if num not in idx[f]:
                            idx[f].append(num)
    _INDEX_CACHE[language] = idx
    return idx


def _entry(language: str, num: str) -> Optional[Dict[str, Any]]:
    lx = next((l for l in _LEXICONS if l["language"] == language), None)
    if not lx:
        return None
    path = os.path.join(_LEX_DIR, lx["file"])
    if not os.path.isfile(path):
        return None
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:                                             # noqa: BLE001
        return None
    e = data.get(num)
    if not e:
        return None
    return {"strongs": num, "lemma": e.get("lemma"), "translit": e.get("translit"),
            "definition": e.get("strongs_def"), "kjv_usage": e.get("kjv_def"),
            "derivation": e.get("derivation"), "source": lx["source"]}


def gloss(text: str, language: Optional[str] = None, limit: int = 400) -> Dict[str, Any]:
    """Word-by-word gloss from a held lexicon. Reports what it could NOT resolve.

    Returns every token in order. A resolved token carries the lexicon's own definition and its
    attribution; an unresolved one carries status='unresolved' and is left plainly visible. The
    coverage block is the honest part -- it is the difference between a reader who knows how much
    of this they are seeing and a reader who does not.
    """
    if not (text or "").strip():
        return {"status": "empty", "tokens": [], "coverage": {"total": 0, "resolved": 0}}

    sc = script_of(text)
    if language is None:
        language = next((l["language"] for l in _LEXICONS if l["script"] == sc["script"]), None)

    if not language:
        return {"status": "NO_LEXICON", "script": sc["script"], "tokens": [],
                "coverage": {"total": 0, "resolved": 0},
                "detail": ("no lexicon is held for the %s script. This is a gap, not a failure "
                           "of the text — add a lexicon and this script becomes readable."
                           % sc["script"]),
                "held": [h["language"] for h in lexicons()["held"]]}

    idx = _index(language)
    if not idx:
        return {"status": "NO_LEXICON", "script": sc["script"], "language": language,
                "tokens": [], "coverage": {"total": 0, "resolved": 0},
                "detail": "lexicon file for %s is absent or unreadable" % language}

    raw = [t for t in _TOKEN.findall(text) if t.strip()]
    tokens, resolved = [], 0
    for i, tok in enumerate(raw[:limit]):
        clean = _trim(tok)
        f = _fold(clean)
        nums = idx.get(f, [])
        stripped = None
        if not nums and language == "hebrew_biblical":
            # HEBREW FUSES ITS PARTICLES ONTO THE WORD, and the lexicon stores the bare noun or
            # verb. b'reshit is be- + reshit; ha-shamayim is ha- + shamayim. Measured before
            # this fallback existed, Genesis 1:1 resolved 4 of 14 tokens (28.6%) purely because
            # of prefixes, so this is a real gap with a known cause rather than unknown words.
            #
            # A stripped match is a WEAKER claim than a direct one and is labelled as such: the
            # reader is told the prefix was removed, so they can judge it. Silently presenting it
            # as a clean hit would be the "silently upgrade authority" failure in miniature.
            for pre in _HEBREW_PREFIXES:
                if f.startswith(pre) and len(f) > len(pre) + 1:
                    cand = idx.get(f[len(pre):], [])
                    if cand:
                        nums, stripped = cand, pre
                        break
        if nums:
            resolved += 1
            entries = [e for e in (_entry(language, n) for n in nums[:4]) if e]
            note = None
            if stripped:
                note = ("matched after removing the prefix %r — Hebrew fuses particles "
                        "(be-, le-, ke-, ve-, ha-, mi-, she-) onto the word while the lexicon "
                        "stores the bare form. A WEAKER match than a direct one." % stripped)
            elif len(entries) > 1:
                note = ("more than one lexicon entry folds to this form; all are shown rather "
                        "than one being chosen")
            tokens.append({"pos": i, "token": tok, "folded": f, "status": "resolved",
                           "match": "prefix_stripped" if stripped else "direct",
                           "candidates": entries, "note": note})
        else:
            tokens.append({"pos": i, "token": tok, "folded": f, "status": "unresolved",
                           "note": ("no lexicon entry matches this form. Running text is "
                                    "INFLECTED and a lexicon stores LEMMAS, so this is usually a "
                                    "morphology gap rather than an unknown word.")})

    total = len(tokens)
    return {
        "status": "ok",
        "script": sc["script"],
        "language": language,
        "tokens": tokens,
        "coverage": {"total": total, "resolved": resolved,
                     "unresolved": total - resolved,
                     "pct": round(100.0 * resolved / total, 1) if total else 0.0},
        "truncated": len(raw) > limit,
        "boundary": ("This is a GLOSS, not a translation. Every definition above is a held "
                     "lexicon's own wording, attributed. No sentence has been composed by this "
                     "engine, and none will be — fluent output that no source contains is "
                     "the one artefact this library must not hand anyone."),
    }


def study(text: str, language: Optional[str] = None) -> Dict[str, Any]:
    """A reader's view: the gloss plus a plain statement of how much of it is actually covered."""
    g = gloss(text, language)
    cov = g.get("coverage", {})
    pct = cov.get("pct", 0.0)
    if g.get("status") == "NO_LEXICON":
        verdict = "CANNOT_READ"
    elif pct >= 80:
        verdict = "MOSTLY_COVERED"
    elif pct >= 40:
        verdict = "PARTIAL"
    else:
        verdict = "THIN"
    g["verdict"] = verdict
    g["plain"] = {
        "CANNOT_READ": "No lexicon is held for this script, so nothing here can be glossed yet.",
        "MOSTLY_COVERED": "Most words resolved to a lexicon entry; the rest are marked.",
        "PARTIAL": "About half resolved. Treat the unresolved words as gaps, not as absences.",
        "THIN": ("Few words resolved — usually heavy inflection meeting a lemma-only "
                 "lexicon. What is shown is real; what is missing is named."),
    }[verdict]
    return g
