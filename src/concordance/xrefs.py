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


__all__ = ["for_ref", "SOURCE", "LICENSE", "ATTRIBUTION", "BOOK_NAMES"]
