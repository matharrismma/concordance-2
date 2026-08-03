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


# ══════════════════════════════════════════════════════════════════════════════════════════
# PARALLEL ALIGNMENT — read a work across two languages without translating either.
#
# THIS IS COMPOSITION, NOT GENERATION, which is why it is permitted where translation is not.
# Both sides already exist and were written by people; alignment only says WHICH PART of one
# corresponds to WHICH PART of the other. No new sentence is produced and every unit shown is
# quoted from a held source. A reader who cannot read Greek but can read English can then study
# the Greek of a particular line, because the line has been LOCATED rather than rendered.
#
# TWO MODES, and the honest one is preferred:
#   BY ADDRESS — when both sides carry the same reference scheme (verse, section), alignment is
#                EXACT and is not an inference at all. Scripture is this case.
#   BY LENGTH  — otherwise, Gale & Church (1993): translations preserve LENGTH closely, so a
#                dynamic program over character counts recovers the correspondence with no
#                dictionary and no model. Deterministic, offline, language-independent.
#
# The length method is a STATISTICAL INFERENCE and is labelled as one. Each pairing carries its
# cost, and a pairing that fits badly is FLAGGED rather than smoothed over — an alignment nobody
# can check is worth less than a gap somebody can see.
# ══════════════════════════════════════════════════════════════════════════════════════════

# Gale & Church bead types: how many units on the left pair with how many on the right, and the
# prior cost of each. 1-1 dominates real translations; the rest exist because translators split
# and merge sentences, and a model that forbids that mis-aligns everything after the first split.
_BEADS = (
    (1, 1, 0.0),      # substitution — the normal case
    (1, 0, 4.0),      # deletion: a unit with no counterpart
    (0, 1, 4.0),      # insertion
    (2, 1, 3.4),      # two units rendered as one
    (1, 2, 3.4),      # one unit rendered as two
    (2, 2, 6.8),      # a genuine tangle
)


def paragraphs(text: str) -> List[str]:
    """Split into units on blank lines, falling back to lines. Structure, not semantics."""
    if not text:
        return []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) > 1:
        return blocks
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _bead_cost(la: int, lb: int, ratio: float) -> float:
    """Cost of pairing la characters with lb, given the corpus's own mean length ratio.

    The ratio is MEASURED from the two texts rather than assumed, because it is
    language-specific — Greek runs longer than English, Hebrew much shorter — and a hard-coded
    constant would silently mis-align every pair in a language it was not tuned on.
    """
    # A DELETION OR INSERTION CARRIES NO LENGTH EVIDENCE, and charging it anyway was a real bug.
    # For a 1-0 or 0-1 bead the length difference IS the whole unit by definition, so the old
    # formula returned ~12 on top of the 4.0 prior — about 16 — which made a genuine omission
    # more expensive than merging two unrelated units. Found by driving a stress case: with one
    # Greek verse removed, the aligner chose a 1-2 merge (4.98) over the correct 1-1 plus 0-1,
    # because the correct answer had been priced out. The prior alone must carry these beads.
    if la == 0 or lb == 0:
        return 0.0
    expected = la * ratio
    denom = max(1.0, (expected + lb) / 2.0)
    return abs(expected - lb) / denom * 6.0


def align(a_units: List[str], b_units: List[str],
          a_addresses: Optional[List[str]] = None,
          b_addresses: Optional[List[str]] = None) -> Dict[str, Any]:
    """Pair the units of two parallel texts. Exact by address where possible, else by length.

    Every pairing carries its cost, and units that could not be paired are returned explicitly —
    an unaligned unit is a fact about the texts, not an error to hide.
    """
    a_units = [u for u in (a_units or []) if u and u.strip()]
    b_units = [u for u in (b_units or []) if u and u.strip()]
    if not a_units or not b_units:
        return {"status": "empty", "pairs": [],
                "coverage": {"a_units": len(a_units), "b_units": len(b_units), "paired": 0}}

    # ── exact mode: both sides addressed, so correspondence is looked up, never inferred ──
    if a_addresses and b_addresses and len(a_addresses) == len(a_units) \
            and len(b_addresses) == len(b_units):
        bmap = {addr: (i, b_units[i]) for i, addr in enumerate(b_addresses)}
        pairs, unmatched_a = [], []
        for i, addr in enumerate(a_addresses):
            hit = bmap.pop(addr, None)
            if hit:
                pairs.append({"address": addr, "a": a_units[i], "b": hit[1],
                              "method": "address", "cost": 0.0})
            else:
                unmatched_a.append({"address": addr, "a": a_units[i]})
        return {
            "status": "ok", "method": "address", "pairs": pairs,
            "unaligned_a": unmatched_a,
            "unaligned_b": [{"address": k, "b": v[1]} for k, v in bmap.items()],
            "coverage": {"a_units": len(a_units), "b_units": len(b_units),
                         "paired": len(pairs),
                         "pct": round(100.0 * len(pairs) / len(a_units), 1)},
            "confidence": ("EXACT — both sides carry the same reference scheme, so this is a "
                           "lookup rather than an inference. Nothing here was guessed."),
        }

    # ── length mode: Gale & Church dynamic programming ──
    la = [len(u) for u in a_units]
    lb = [len(u) for u in b_units]
    ratio = (sum(lb) / sum(la)) if sum(la) else 1.0

    n, m = len(a_units), len(b_units)
    INF = float("inf")
    d = [[INF] * (m + 1) for _ in range(n + 1)]
    back: Dict[Any, Any] = {}
    d[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if d[i][j] == INF:
                continue
            for da, db, prior in _BEADS:
                ni, nj = i + da, j + db
                if ni > n or nj > m:
                    continue
                step = prior + _bead_cost(sum(la[i:ni]), sum(lb[j:nj]), ratio)
                if d[i][j] + step < d[ni][nj]:
                    d[ni][nj] = d[i][j] + step
                    back[(ni, nj)] = (i, j, da, db, step)

    if d[n][m] == INF:
        return {"status": "no_alignment", "pairs": [],
                "coverage": {"a_units": n, "b_units": m, "paired": 0},
                "detail": "no path through the bead model — the texts may not be parallel"}

    path, i, j = [], n, m
    while (i, j) != (0, 0):
        pi, pj, da, db, step = back[(i, j)]
        path.append((pi, i, pj, j, da, db, step))
        i, j = pi, pj
    path.reverse()

    pairs, paired = [], 0
    for ai, aj, bi, bj, da, db, step in path:
        if da and db:
            paired += da
        pairs.append({
            "a_index": list(range(ai, aj)), "b_index": list(range(bi, bj)),
            "a": "\n".join(a_units[ai:aj]) or None,
            "b": "\n".join(b_units[bi:bj]) or None,
            "bead": "%d-%d" % (da, db), "cost": round(step, 3), "method": "length",
            # ANY BEAD THAT IS NOT 1-1 IS FLAGGED, whatever its cost. A split, a merge or an
            # omission is inherently a weaker claim than a clean substitution — the same reason
            # a prefix-stripped gloss is labelled weaker than a direct hit. Relying on a cost
            # threshold alone let the single genuinely doubtful pairing through at 4.98 against
            # a 5.0 cutoff, which is precisely the case the flag exists to catch.
            "flag": (("weak — a %d-%d bead is a split, merge or omission rather than a clean "
                      "one-to-one pairing, and should be read with suspicion" % (da, db))
                     if (da, db) != (1, 1) else
                     ("weak — fits the length model poorly" if step > 5.0 else None)),
        })

    weak = sum(1 for p in pairs if p["flag"])
    return {
        "status": "ok", "method": "length", "pairs": pairs,
        "length_ratio": round(ratio, 3),
        "coverage": {"a_units": n, "b_units": m, "paired": paired,
                     "pct": round(100.0 * paired / n, 1) if n else 0.0,
                     "weak_pairings": weak},
        "confidence": ("INFERRED — Gale & Church length correspondence (1993), deterministic and "
                       "dictionary-free. Reliable for prose, weaker for verse, lists and heavy "
                       "paraphrase. %d pairing(s) fit poorly and are flagged." % weak),
        "boundary": ("Alignment LOCATES text; it does not render it. Both sides are quoted from "
                     "held sources and no sentence was composed by this engine."),
    }
