"""Cross-references (editorial) — Scripture linked to Scripture by the openbible.info dataset.

A community-voted expansion of the PUBLIC-DOMAIN Treasury of Scripture Knowledge (TSK), from
openbible.info (licensed CC BY — ATTRIBUTED, never engine-authored). This is the EDITORIAL
cross-reference layer; it complements the deterministic Strong's-based cross-refs (which link verses
by shared original words). Found + cited, never generated; ranked by the dataset's relevance votes.

Store (sovereign SQLite, gitignored; built by tools/migrate_xrefs.py):
    data/xrefs/xrefs.db
      cross_refs(from_book,from_chapter,from_verse, to_book,to_chapter,to_verse_start,to_verse_end, votes)
      meta(k,v)
book_num: Genesis=1 .. Malachi=39, Matthew=40 .. Revelation=66.
Env: CONCORDANCE_XREFS_DIR / CONCORDANCE_DATA_DIR.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

SOURCE = "openbible.info cross-references (CC BY) — a community-voted expansion of the public-domain Treasury of Scripture Knowledge (TSK)"
LICENSE = "CC BY (openbible.info); underlying TSK is public domain"
ATTRIBUTION = "Cross-reference data courtesy of openbible.info (CC BY), based on the public-domain Treasury of Scripture Knowledge"

BOOK_NAMES = {
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy", 6: "Joshua",
    7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel", 11: "1 Kings", 12: "2 Kings",
    13: "1 Chronicles", 14: "2 Chronicles", 15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job",
    19: "Psalms", 20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel", 28: "Hosea", 29: "Joel",
    30: "Amos", 31: "Obadiah", 32: "Jonah", 33: "Micah", 34: "Nahum", 35: "Habakkuk",
    36: "Zephaniah", 37: "Haggai", 38: "Zechariah", 39: "Malachi", 40: "Matthew", 41: "Mark",
    42: "Luke", 43: "John", 44: "Acts", 45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians",
    48: "Galatians", 49: "Ephesians", 50: "Philippians", 51: "Colossians", 52: "1 Thessalonians",
    53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy", 56: "Titus", 57: "Philemon",
    58: "Hebrews", 59: "James", 60: "1 Peter", 61: "2 Peter", 62: "1 John", 63: "2 John",
    64: "3 John", 65: "Jude", 66: "Revelation",
}
_NAME_TO_NUM = {re.sub(r"[^a-z0-9]", "", n.lower()): b for b, n in BOOK_NAMES.items()}
# common abbreviations / singular-plural nudges handled by _resolve_book below
_ABBREV = {"gen": 1, "ex": 2, "exod": 2, "lev": 3, "num": 4, "deut": 5, "dt": 5, "josh": 6,
           "ps": 19, "psa": 19, "psalm": 19, "pr": 20, "prov": 20, "eccl": 21, "isa": 23,
           "jer": 24, "ezek": 26, "dan": 27, "mt": 40, "matt": 40, "mk": 41, "mar": 41,
           "lk": 42, "luk": 42, "jn": 43, "jhn": 43, "rom": 45, "1co": 46, "2co": 47,
           "gal": 48, "eph": 49, "phil": 50, "php": 50, "col": 51, "heb": 58, "jas": 59,
           "1pe": 60, "2pe": 61, "1jn": 62, "rev": 66, "song": 22}

_REF_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z. ]+?)\s+(\d+):(\d+)\s*$")


def _db_path() -> Path:
    env = os.environ.get("CONCORDANCE_XREFS_DIR", "").strip()
    if env:
        return Path(env) / "xrefs.db"
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "xrefs" / "xrefs.db"


def _resolve_book(raw: str) -> Optional[int]:
    key = re.sub(r"[^a-z0-9]", "", (raw or "").lower())
    if key in _NAME_TO_NUM:
        return _NAME_TO_NUM[key]
    if key in _ABBREV:
        return _ABBREV[key]
    for alt in (key + "s", key.rstrip("s")):  # Psalm <-> Psalms
        if alt in _NAME_TO_NUM:
            return _NAME_TO_NUM[alt]
    return None


def _fmt(tb: int, tc: int, tvs: int, tve: int) -> str:
    book = BOOK_NAMES.get(tb, str(tb))
    return f"{book} {tc}:{tvs}" + (f"-{tve}" if tve and tve > tvs else "")


def for_ref(ref: str, limit: int = 20) -> Dict[str, Any]:
    """Editorial cross-references for a verse, ranked by relevance votes. Attributed; found."""
    base = {"ref": ref, "source": SOURCE, "license": LICENSE, "attribution": ATTRIBUTION,
            "cross_references": []}
    m = _REF_RE.match(ref or "")
    if not m:
        return {**base, "status": "not_found", "detail": "could not parse reference"}
    bn = _resolve_book(m.group(1))
    if not bn:
        return {**base, "status": "not_found", "detail": f"unknown book {m.group(1)!r}"}
    ch, v = int(m.group(2)), int(m.group(3))
    db_path = _db_path()
    if not db_path.exists():
        return {**base, "status": "source_missing",
                "detail": "xrefs.db not built (run tools/migrate_xrefs.py)"}
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT to_book,to_chapter,to_verse_start,to_verse_end,votes FROM cross_refs "
            "WHERE from_book=? AND from_chapter=? AND from_verse=? ORDER BY votes DESC, to_book, to_chapter, to_verse_start "
            "LIMIT ?", (bn, ch, v, max(1, int(limit)))).fetchall()
    finally:
        con.close()
    refs = [{"ref": _fmt(tb, tc, tvs, tve), "votes": votes} for (tb, tc, tvs, tve, votes) in rows]
    return {**base, "ref": _fmt(bn, ch, v, v), "status": "ok", "count": len(refs), "cross_references": refs}


# ── Book×book aggregate (the cross-reference MAP) ───────────────────────────────────────────────
# Display abbreviations for the matrix axes (Gen, Ex, ... Rev) — not the OSIS codes, not the input
# aliases; the short labels a reader expects on a cross-reference chart.
BOOK_ABBREV = {
    1: "Gen", 2: "Ex", 3: "Lev", 4: "Num", 5: "Deut", 6: "Josh", 7: "Jdg", 8: "Ruth", 9: "1Sa",
    10: "2Sa", 11: "1Kg", 12: "2Kg", 13: "1Ch", 14: "2Ch", 15: "Ezra", 16: "Neh", 17: "Est",
    18: "Job", 19: "Ps", 20: "Pr", 21: "Eccl", 22: "Son", 23: "Isa", 24: "Jer", 25: "Lam",
    26: "Ezk", 27: "Dan", 28: "Hos", 29: "Joel", 30: "Am", 31: "Ob", 32: "Jon", 33: "Mic",
    34: "Nah", 35: "Hab", 36: "Zep", 37: "Hag", 38: "Zec", 39: "Mal", 40: "Mat", 41: "Mar",
    42: "Luk", 43: "Jn", 44: "Acts", 45: "Rom", 46: "1Co", 47: "2Co", 48: "Gal", 49: "Eph",
    50: "Phil", 51: "Col", 52: "1Th", 53: "2Th", 54: "1Ti", 55: "2Ti", 56: "Titus", 57: "Phm",
    58: "Heb", 59: "Jas", 60: "1Pe", 61: "2Pe", 62: "1Jn", 63: "2Jn", 64: "3Jn", 65: "Jude",
    66: "Rev",
}
# The sections of the canon, in order (the matrix's axis groups). By book number.
BOOK_GROUPS = [
    {"label": "Law", "books": list(range(1, 6))},                        # Genesis–Deuteronomy
    {"label": "History", "books": list(range(6, 18))},                   # Joshua–Esther
    {"label": "Poetry", "books": list(range(18, 23))},                   # Job–Song of Solomon
    {"label": "Major Prophets", "books": list(range(23, 28))},           # Isaiah–Daniel
    {"label": "Minor Prophets", "books": list(range(28, 40))},           # Hosea–Malachi
    {"label": "Gospels & Acts", "books": list(range(40, 45))},           # Matthew–Acts
    {"label": "Pauline Epistles", "books": list(range(45, 58))},         # Romans–Philemon
    {"label": "General Epistles & Revelation", "books": list(range(58, 67))},  # Hebrews–Revelation
]

_MATRIX_CACHE: Optional[Dict[str, Any]] = None


def _connect_ro(db_path: Path) -> "sqlite3.Connection":
    try:
        return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return sqlite3.connect(str(db_path))


def book_matrix() -> Dict[str, Any]:
    """The book→book cross-reference MATRIX (66×66), aggregated from the openbible/TSK links by ONE SQL
    GROUP BY — SQLite streams the ~340k rows on disk and returns only the grouped pairs, so this is
    sub-second and tiny in memory (never fetchall() the raw rows). Memoized per process (the DB is
    immutable under a running service). `votes` = summed relevance weight source-book→target-book;
    `links` = number of verse links. Found + cited, never generated; honest source_missing when absent."""
    global _MATRIX_CACHE
    if _MATRIX_CACHE is not None:
        return _MATRIX_CACHE
    books = [{"n": i, "name": BOOK_NAMES[i], "abbr": BOOK_ABBREV[i], "testament": "OT" if i <= 39 else "NT"}
             for i in range(1, 67)]
    base = {"source": SOURCE, "license": LICENSE, "attribution": ATTRIBUTION,
            "books": books, "groups": BOOK_GROUPS}
    db_path = _db_path()
    if not db_path.exists():
        return {**base, "status": "source_missing", "cells": [], "n_cells": 0, "total_links": 0}
    con = _connect_ro(db_path)
    try:
        rows = con.execute(
            "SELECT from_book, to_book, SUM(votes), COUNT(*) FROM cross_refs "
            "GROUP BY from_book, to_book").fetchall()
    finally:
        con.close()
    cells = [{"from": int(fb), "to": int(tb), "votes": int(v or 0), "links": int(n or 0)}
             for (fb, tb, v, n) in rows if fb and tb]
    _MATRIX_CACHE = {**base, "status": "ok", "n_books": 66, "n_cells": len(cells),
                     "total_links": sum(c["links"] for c in cells), "cells": cells}
    return _MATRIX_CACHE


def book_pair(from_book: int, to_book: int, limit: int = 60) -> Dict[str, Any]:
    """The actual verse links from one book to another, ranked by votes — the drill-down behind a
    matrix cell. from_book/to_book are book numbers (1–66). Found + cited, never generated."""
    base = {"from": BOOK_NAMES.get(int(from_book) if str(from_book).isdigit() else 0, str(from_book)),
            "to": BOOK_NAMES.get(int(to_book) if str(to_book).isdigit() else 0, str(to_book)),
            "source": SOURCE, "attribution": ATTRIBUTION, "links": []}
    try:
        fb, tb = int(from_book), int(to_book)
    except (TypeError, ValueError):
        return {**base, "status": "not_found", "detail": "from/to must be book numbers 1-66"}
    if not (1 <= fb <= 66 and 1 <= tb <= 66):
        return {**base, "status": "not_found", "detail": "book numbers are 1-66"}
    base["from"], base["to"] = BOOK_NAMES[fb], BOOK_NAMES[tb]
    db_path = _db_path()
    if not db_path.exists():
        return {**base, "status": "source_missing"}
    con = _connect_ro(db_path)
    try:
        rows = con.execute(
            "SELECT from_chapter, from_verse, to_chapter, to_verse_start, to_verse_end, votes "
            "FROM cross_refs WHERE from_book=? AND to_book=? "
            "ORDER BY votes DESC, from_chapter, from_verse LIMIT ?",
            (fb, tb, max(1, min(int(limit), 500)))).fetchall()
    finally:
        con.close()
    links = [{"from": f"{BOOK_NAMES[fb]} {fc}:{fv}", "to": _fmt(tb, tc, tvs, tve), "votes": int(votes or 0)}
             for (fc, fv, tc, tvs, tve, votes) in rows]
    return {**base, "status": "ok", "count": len(links), "links": links}


def book_of(ref: str) -> Optional[int]:
    """The book number (1–66) a reference names, or None — robust to ranges and bare names
    ('Ephesians 4:4-6' → 49, '1 John 4:1' → 62, 'Genesis' → 1). Reuses the book resolver."""
    m = re.match(r"^\s*([1-3]?\s*[A-Za-z][A-Za-z. ]*?)\s+\d", ref or "")
    return _resolve_book(m.group(1) if m else (ref or ""))


def book_connections(book_num: int, limit: int = 8) -> Dict[str, Any]:
    """The strongest OUTGOING book connections from a given book — for weaving a verse's book context
    into the Console / map. Reads the memoized matrix; no extra query."""
    try:
        bn = int(book_num)
    except (TypeError, ValueError):
        return {"book": str(book_num), "status": "not_found", "connections": []}
    m = book_matrix()
    name = BOOK_NAMES.get(bn, str(bn))
    if m.get("status") != "ok":
        return {"book": name, "status": m.get("status", "source_missing"), "connections": []}
    out = sorted((c for c in m["cells"] if c["from"] == bn and c["to"] != bn),
                 key=lambda c: c["votes"], reverse=True)[:max(1, int(limit))]
    conns = [{"book": BOOK_NAMES[c["to"]], "abbr": BOOK_ABBREV[c["to"]], "votes": c["votes"], "links": c["links"]}
             for c in out]
    return {"book": name, "status": "ok", "connections": conns}


__all__ = ["for_ref", "book_matrix", "book_pair", "book_connections", "book_of", "SOURCE", "LICENSE",
           "ATTRIBUTION", "BOOK_NAMES", "BOOK_ABBREV", "BOOK_GROUPS"]
