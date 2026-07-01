"""Pronounce — a sovereign, deterministic pronunciation GUIDE from a transliteration.

There is no native-speaker audio in the lexicon, and the Greek entries carry no pronunciation
field — only a transliteration. This turns that transliteration into an APPROXIMATE reading guide:
a diacritic-stripped plain form, a light syllable-broken respelling, and a conservative IPA
approximation from a fixed letter map.

HONEST BY CONSTRUCTION: it is explicitly a SYNTHESIZED GUIDE, not a native speaker — every result
carries that caveat, and IPA is emitted only from the known map (approximate), never fabricated
beyond it. The transliteration (and above it, the original Hebrew/Greek word) remains the authority.
This is the sovereign floor; the ElevenLabs voice is the optional ceiling.

Stdlib only (unicodedata).
"""
from __future__ import annotations

import unicodedata
from typing import Any, Dict, List

_VOWELS = frozenset("aeiouy")

_GUIDE_NOTE = ("An approximate, synthesized pronunciation guide — not a native speaker. The "
               "transliteration (and above it, the original word) is the authority.")

# Conservative transliteration→IPA. Digraphs first, then single letters. Approximate by design.
_DIGRAPHS = {"ch": "x", "ph": "f", "th": "θ", "ps": "ps", "kh": "x", "ng": "ŋ"}
_LETTERS = {
    "a": "a", "e": "e", "i": "i", "o": "o", "u": "u", "y": "y",
    "b": "b", "c": "k", "d": "d", "f": "f", "g": "ɡ", "h": "h", "j": "dʒ", "k": "k",
    "l": "l", "m": "m", "n": "n", "p": "p", "q": "k", "r": "r", "s": "s", "t": "t",
    "v": "v", "w": "w", "x": "ks", "z": "z",
}
# combining macron / circumflex mark a long vowel in the standard transliteration schemes.
_LONG_MARKS = ("̄", "̂")


def _ascii(s: str) -> str:
    """Base letters with combining diacritics stripped (NFD)."""
    nfd = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in nfd if not unicodedata.combining(c))


def plain(translit: str) -> str:
    """The diacritic-stripped, lowercase base form — a rough plain reading."""
    return _ascii(translit).lower()


def _long_positions(translit: str) -> set:
    """Indices (into the ascii base form) whose vowel carries a macron/circumflex = long."""
    nfd = unicodedata.normalize("NFD", translit or "")
    longs: set = set()
    base_i = -1
    for c in nfd:
        if unicodedata.combining(c):
            if c in _LONG_MARKS and base_i >= 0:
                longs.add(base_i)
        else:
            base_i += 1
    return longs


def syllables(word: str) -> List[str]:
    """Rough syllable split of an ascii word by vowel groups (approximate, deterministic).
    Each vowel group starts a syllable; a single consonant between vowels becomes the next
    syllable's onset (V-CV), and the last syllable takes the remainder."""
    w = (word or "").lower()
    if not w:
        return []
    groups: List[tuple] = []
    i = 0
    while i < len(w):
        if w[i] in _VOWELS:
            j = i
            while j < len(w) and w[j] in _VOWELS:
                j += 1
            groups.append((i, j))
            i = j
        else:
            i += 1
    if not groups:
        return [w]
    syls: List[str] = []
    start = 0
    for idx, (_gs, ge) in enumerate(groups):
        if idx == len(groups) - 1:
            syls.append(w[start:])
            break
        next_gs = groups[idx + 1][0]
        cons = next_gs - ge  # consonants between this vowel group and the next
        keep = ge + (cons - 1 if cons >= 1 else 0)  # leave one consonant as the next onset
        syls.append(w[start:keep])
        start = keep
    return [s for s in syls if s]


def respell(translit: str) -> str:
    """A hyphen-broken approximate respelling of the plain form, e.g. 'agape' -> 'a-ga-pe'."""
    return "-".join(syllables(plain(translit)))


def ipa(translit: str) -> str:
    """A conservative IPA approximation from the fixed letter map. '' if nothing maps."""
    w = plain(translit)
    longs = _long_positions(translit)
    out: List[str] = []
    i = 0
    while i < len(w):
        two = w[i:i + 2]
        if two in _DIGRAPHS:
            out.append(_DIGRAPHS[two])
            i += 2
            continue
        ch = w[i]
        sym = _LETTERS.get(ch, "")
        if ch in _VOWELS and i in longs:
            sym += "ː"
        out.append(sym)
        i += 1
    s = "".join(out)
    return f"/{s}/" if s else ""


def guide(text: str) -> Dict[str, Any]:
    """The full synthesized guide for a transliteration/word — honestly labeled."""
    t = (text or "").strip()
    p = plain(t)
    return {
        "input": t,
        "plain": p,
        "respelling": respell(t),
        "ipa": ipa(t),
        "speakable": p,          # what browser Web Speech can approximate aloud
        "synthesized": True,
        "note": _GUIDE_NOTE,
    }


__all__ = ["plain", "syllables", "respell", "ipa", "guide"]
