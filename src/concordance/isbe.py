"""ISBE 1915 reader — full articles from the compact acquisition db (D5). Read-only, mmap'd.

The keeping holds 9,380 STUB cards (shelf "encyclopedia", box "isbe" — ~600 bytes each,
minted by tools/card_isbe.py); the full public-domain articles live in
data/acquisitions/isbe.db (~25 MB on disk, tens of MB mmap'd, near-zero resident RAM —
the stub+link discipline, and a capacitor: the heavy text sits in the reservoir until a
reader actually asks). The card page renders the whole article from here, so the resident
corpus stays light while the reader never gets less than the whole entry.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Dict, Optional

_LOCK = threading.Lock()
_CONN: Optional[sqlite3.Connection] = None
_CONN_PATH: Optional[str] = None

SOURCE = ("International Standard Bible Encyclopedia (1915), ed. James Orr — "
          "Public Domain (CrossWire SWORD module ISBE v2.2)")


def _db_path() -> Path:
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(data) / "acquisitions" / "isbe.db"


def available() -> bool:
    return _db_path().exists()


def get(headword: str) -> Optional[Dict[str, str]]:
    """The full article for a headword, or None. Never raises on a missing/locked db —
    the caller falls back to the stub (a shorter answer, never a broken page)."""
    global _CONN, _CONN_PATH
    if not headword:
        return None
    p = str(_db_path())
    try:
        with _LOCK:
            if _CONN is None or _CONN_PATH != p:
                if not available():
                    return None
                if _CONN is not None:
                    try:
                        _CONN.close()
                    except Exception:  # noqa: BLE001
                        pass
                _CONN = sqlite3.connect(f"file:{p}?mode=ro", uri=True, check_same_thread=False)
                _CONN.execute("pragma query_only=on")
                _CONN.execute("pragma mmap_size=67108864")
                _CONN_PATH = p
            row = _CONN.execute("select headword, title, text from entries where headword = ?",
                                (headword.strip(),)).fetchone()
    except sqlite3.Error:
        return None
    if not row:
        return None
    return {"headword": row[0], "title": row[1], "text": row[2], "source": SOURCE}


__all__ = ["available", "get", "SOURCE"]
