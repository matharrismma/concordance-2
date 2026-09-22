"""READ WITH THE COACH — the learner's chosen text becomes the decodable surface of the cube.

Matt, 2026-09-22: "choose the text." The cube (Cubo) teaches five embodied anchors — I am · there is
· this is · I go · from/through/to. Those are the FRAME. The learner then chooses a real public-domain
work, and this finds the sentences in THAT work they can already read by the cube: real sentences,
pulled verbatim from the book, each carrying one of the anchors the learner has been taught. The frame
is fixed; the chosen text supplies the words. This is where the reader (the tortoise) and the coach
(the cube) become one thing.

FOUND, NOT GENERATED — the whole discipline of the keeping, applied to reading:
  • Every sentence returned is VERBATIM from the work (the tortoise reads it through, off the drive /
    the Internet Archive); it is SELECTED, never composed.
  • The cube's own anchor phrases are the lens. A sentence earns its place by CARRYING one of the five
    anchors — not by being written to fit. Nothing is paraphrased or simplified.
  • Honest when a book yields few. A scanned trade manual is not a graded reader; if it holds little at
    the learner's level, we say what we found and point back to the whole work and the cube.

Conduit, not source: the author's own sentences, found and handed to a reader who can now decode them.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from . import tortoise

# The five anchors, as the text markers to look THROUGH — the lead phrases of each cube, curated per
# tongue. Latin-script markers match case-insensitively on word boundaries; native-script markers
# (grc/he/zh) match as substrings. Bare prepositions (from/through/to) are deliberately NOT markers —
# they match everything and would drown the signal.
ANCHORS: Dict[str, List[str]] = {
    "en":  ["I am", "there is", "there are", "this is", "it is", "here is", "I go"],
    "fr":  ["je suis", "il y a", "c'est", "je vais", "voici", "il est"],
    "de":  ["ich bin", "es gibt", "das ist", "ich gehe", "hier ist"],
    "la":  ["sum", "est", "sunt", "hic est", "haec est", "hoc est", "eo"],
    "es":  ["estoy", "soy", "hay", "esto es", "esta es", "voy"],
    "pt":  ["estou", "sou", "há", "isto é", "vou"],
    "grc": ["εἰμι", "ἔστιν", "εἰσίν", "οὗτος", "αὕτη", "τοῦτο", "ὑπάγω"],
    "he":  ["אני", "יש", "זה", "הולך", "הולכת"],
    "zh":  ["我在", "有", "这是", "我去"],
}

# The work's own language tag (from the trades card) -> the cube that teaches it, so the reader can
# default the lens to the tongue the book is actually in.
LANG_TO_SUBJECT = {
    "english": "en", "french": "fr", "german": "de", "latin": "la", "spanish": "es",
    "portuguese": "pt", "greek": "grc", "hebrew": "he", "chinese": "zh", "mandarin": "zh",
}

_ROMAN = {"en", "fr", "de", "la", "es", "pt"}
_SENT = re.compile(r"[^.!?]*[.!?]")
_WS = re.compile(r"\s+")
# OCR wraps a word across a line as "impor- tant" (hyphen + line break -> hyphen + space). Rejoin only
# lowercase-to-lowercase, which restores the scanned word without touching real compounds (home-grown,
# no space) or a genuine dash between words (" - ", spaces on both sides).
_HYPHEN_WRAP = re.compile(r"([a-zà-ÿ])- ([a-zà-ÿ])")


def subjects_for_language(language: str) -> str:
    return LANG_TO_SUBJECT.get((language or "").strip().lower(), "en")


def _norm(s: str) -> str:
    s = _WS.sub(" ", s.replace("\n", " ")).strip()
    return _HYPHEN_WRAP.sub(r"\1\2", s)


def _clean_enough(s: str) -> bool:
    """Guard against OCR debris — index rows, tables of figures, running heads — which are not
    sentences a learner can read. A real sentence is mostly letters."""
    if not s:
        return False
    letters = sum(ch.isalpha() for ch in s)
    return letters >= 0.62 * len(s)


def _fold(s: str) -> str:
    """Diacritic-insensitive, lowercase form for MATCHING only (the verbatim sentence is untouched).
    Greek is written with accents that vary — οὗτος vs οὗτός — and Spanish/French carry accents a
    scan may drop; folding both the marker and the text lets an anchor be recognised through them."""
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def decodable(card: Dict[str, Any], subject: str = "en", *, limit: int = 12,
              min_words: int = 3, max_words: int = 16, scan_chars: int = 500_000) -> Dict[str, Any]:
    """Find the sentences in `card`'s work that a learner of `subject` can read by the cube.

    Returns the head (title, subject, detail_url) plus `found`: verbatim sentences, shortest first
    (short = most decodable), each with the anchor it carries. Honest empty when the book holds few.
    """
    subject = (subject or "en").strip().lower()
    markers = ANCHORS.get(subject) or ANCHORS["en"]
    roman = subject in _ROMAN

    op = tortoise.open_work(card)
    head = {"card": card.get("id"), "title": op.get("title"), "subject": subject,
            "detail_url": op.get("detail_url"), "language": op.get("language"),
            "discipline": op.get("discipline")}
    if op.get("status") != "read":
        return {**head, "status": op.get("status", "not_available"), "reason": op.get("reason"),
                "found": [], "count": 0}

    text = (op.get("text") or "")[:scan_chars]
    # Match against a diacritic-folded form; keep the display marker for the UI to bold.
    if roman:
        pats = [(m, re.compile(r"\b" + re.escape(_fold(m)) + r"\b")) for m in markers]
    else:
        pats = [(m, _fold(m)) for m in markers]

    found: List[Dict[str, Any]] = []
    seen = set()
    for raw in _SENT.findall(text):
        s = _norm(raw)
        n = len(s.split())
        if not (min_words <= n <= max_words):
            continue
        if not _clean_enough(s):
            continue
        key = s.lower()
        if key in seen:
            continue
        fs = _fold(s)
        anchor = None
        for m, pat in pats:
            if (pat.search(fs) if roman else (pat in fs)):
                anchor = m
                break
        if not anchor:
            continue
        seen.add(key)
        found.append({"text": s, "anchor": anchor, "words": n})

    found.sort(key=lambda x: x["words"])   # shortest first — the most decodable
    found = found[:limit]
    return {**head, "status": "read", "found": found, "count": len(found),
            "note": ("Real sentences from this work you can read by the cube — found in the book, "
                     "not written for you." if found else
                     "This scanned work holds few sentences at your level yet — read it whole above, "
                     "or choose another text.")}


__all__ = ["decodable", "subjects_for_language", "ANCHORS", "LANG_TO_SUBJECT"]
