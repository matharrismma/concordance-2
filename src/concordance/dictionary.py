"""The Dictionary — definitions, offline and near-free.

The peer of the Thesaurus (synonyms) and the lexicon (original-language word study): this is the
one place for "what does this English word MEAN." Built once by tools/build_dictionary.py from
Webster's 1913 Unabridged (public domain) plus our gathered supplement, into a small read-only
SQLite file (data/dictionary_en.db), memory-mapped exactly like the corpus shards and the thesaurus:
near-zero RAM, works offline on any device. Opt-in — if the file is absent, everything here returns
empty and nothing changes.

Conduit, not author: every definition came from a public-domain dictionary, and each sense records
WHICH (webster-1913 or supplement), so the reader always knows the source and the vintage. One
excellent tool for one situation; it points to its peers rather than duplicating them — synonyms are
the thesaurus's work, pronunciation is `pronounce`, and a word's use in Scripture is `word_study`.
"""
from __future__ import annotations

import os
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional


def _db_path() -> Optional[Path]:
    env = os.environ.get("CONCORDANCE_DICTIONARY_DB", "").strip()
    if env:
        p = Path(env)
        return p if p.exists() else None
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    cand = (Path(data) if data else Path("data")) / "dictionary_en.db"
    return cand if cand.exists() else None


def available() -> bool:
    return _db_path() is not None


def _norm(word: str) -> str:
    return " ".join(str(word or "").strip().lower().split())


@lru_cache(maxsize=4096)
def _rows(word: str) -> tuple:
    """((definition, source), ...) for a word — a fresh read-only connection opened and closed per
    distinct word, its result cached. Empty when the word or the file is absent. Webster's senses
    come before the supplement so the base reads first."""
    p = _db_path()
    w = _norm(word)
    if not p or not w:
        return ()
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro&immutable=1", uri=True, timeout=5.0)
        try:
            cur = c.execute(
                "SELECT definition, source FROM entries WHERE word=? "
                "ORDER BY CASE source WHEN 'webster-1913' THEN 0 ELSE 1 END", (w,))
            return tuple((d, s) for d, s in cur.fetchall())
        finally:
            c.close()
    except sqlite3.Error:
        return ()


def define(word: str) -> Dict[str, object]:
    """Define an English word. -> {word, found, senses:[{definition, source}], see_also}. `found`
    is False (and senses empty) when the word is not in the dictionary or no dictionary is loaded —
    an honest miss, never a guess. `see_also` points to the peer tools, so each situation has one."""
    w = _norm(word)
    senses = [{"definition": d, "source": s} for d, s in _rows(w)]
    return {
        "word": w,
        "found": bool(senses),
        "senses": senses,
        "see_also": {"synonyms": "thesaurus", "pronunciation": "pronounce",
                     "in_scripture": "word_study"},
    }


def definitions(word: str) -> List[str]:
    """Just the definition strings for a word (convenience for callers that want text only)."""
    return [d for d, _s in _rows(word)]
