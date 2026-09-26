"""The Thesaurus — synonyms and broader terms, offline and near-free.

Built once by tools/build_thesaurus.py from WordNet into a small, read-only SQLite file
(data/thesaurus.db), memory-mapped exactly like the corpus shards: near-zero RAM, works offline on
any device. Opt-in — if the file is absent, everything here returns empty and nothing changes.

Two uses:
  * a reference lookup — `synonyms(word)`, `broader(word)`, `related(word)` — "the words that stand
    with it", the thesaurus of the reference section;
  * recall — `expand_subject(word)` hands search a BOUNDED set of a subject's synonyms so a query for
    "automobile" can reach material that only says "car". Recall-safe: the caller keeps the literal
    query first and only APPENDS synonym hits (see corpus.search_question), so precision never drops.

Conduit, not author: every pair came from WordNet. Read-only; no connection is held across a thread
boundary (the shard-handle leak lesson), so a fresh immutable connection is opened per distinct word
and the RESULT is cached — repeated words never reopen, and no file descriptor lingers.
"""
from __future__ import annotations

import json
import os
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import List, Optional


def _db_path() -> Optional[Path]:
    env = os.environ.get("CONCORDANCE_THESAURUS_DB", "").strip()
    if env:
        p = Path(env)
        return p if p.exists() else None
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    cand = (Path(data) if data else Path("data")) / "thesaurus.db"
    return cand if cand.exists() else None


def available() -> bool:
    return _db_path() is not None


def _norm(word: str) -> str:
    return " ".join(str(word or "").strip().lower().split())


@lru_cache(maxsize=8192)
def _row(word: str) -> tuple:
    """(synonyms, broader) for a word — a fresh read-only connection, opened and closed per distinct
    word, its result cached. ('','') when the word or the file is absent."""
    p = _db_path()
    w = _norm(word)
    if not p or not w:
        return ("[]", "[]")
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro&immutable=1", uri=True, timeout=5.0)
        try:
            r = c.execute("select syn, broader from thes where word = ?", (w,)).fetchone()
        finally:
            c.close()
    except sqlite3.Error:
        return ("[]", "[]")
    return (r[0], r[1]) if r else ("[]", "[]")


def _parse(blob: str) -> List[str]:
    try:
        v = json.loads(blob)
        return [str(x) for x in v] if isinstance(v, list) else []
    except (ValueError, TypeError):
        return []


def synonyms(word: str, limit: int = 12) -> List[str]:
    """The words that stand with `word` (WordNet synonyms, across senses). Empty if unknown."""
    out = _parse(_row(word)[0])
    return out[:max(0, int(limit))] if limit else out


def broader(word: str, limit: int = 8) -> List[str]:
    """The broader (IS-A hypernym) terms above `word` — the upward 'connect the dots' links."""
    out = _parse(_row(word)[1])
    return out[:max(0, int(limit))] if limit else out


def related(word: str, limit: int = 16) -> List[str]:
    """Synonyms first, then broader terms — the neighbourhood of a word, deduped, order-stable."""
    seen: set = set()
    out: List[str] = []
    for w in synonyms(word, limit=0) + broader(word, limit=0):
        if w and w not in seen:
            seen.add(w)
            out.append(w)
        if limit and len(out) >= int(limit):
            break
    return out


def expand_subject(word: str, limit: int = 4) -> List[str]:
    """A BOUNDED set of a subject word's synonyms, for recall-safe query broadening. Kept small on
    purpose — a subject's closest synonyms widen what can be FOUND without redefining the question
    (the caller always searches the literal query too and appends these, never replaces)."""
    return synonyms(word, limit=max(0, int(limit)))
