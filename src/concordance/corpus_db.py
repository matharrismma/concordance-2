"""The small, sharded corpus — freeze/unfreeze retrieval so it runs on any device.

Matt, 2026-07-25: "Free up space without adding. Small, for a variety of devices. We need an
efficient retrieval method. We need them in MULTIPLE FILES so we can UNFREEZE as needed."

The default corpus holds ~478k cards in RAM (~2.7 GB). This reads the SAME corpus from compact SQLite
FTS5 SHARD files built by tools/build_corpus_db.py — one file per tier (core / word / science / world /
dictionary / books). A device UNFREEZES only the shards it needs (a phone thaws just `core`; a scholar
thaws them all); frozen shards cost nothing but disk. Search runs across the thawed shards from disk
(FTS5 bm25, memory-mapped) with tens of MB of RAM. SQLite runs everywhere — desktop, phone, Pi, and
the browser via WASM. The ark, pocket-sized.

Two modes, both stdlib-only and read-only:
  * SHARDS  — CONCORDANCE_CORPUS_SHARDS=<dir with manifest.json + *.db>  (freeze/unfreeze)
  * SINGLE  — CONCORDANCE_CORPUS_DB=<one corpus.db>                       (everything, one file)
Opt-in: if neither is set, nothing here loads. Conduit — returns stored cards verbatim; ranks, never
generates.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_OPEN: Dict[str, sqlite3.Connection] = {}     # shard name -> connection (a thawed shard)
_MANIFEST: Optional[Dict[str, Any]] = None
_WORD = re.compile(r"[A-Za-z0-9']{2,}")

# Which shard a shelf belongs to. Anything unlisted falls to `core` (the small, always-thawed map).
SHARD_ASSIGN = {
    "hebrew_ot": "word", "greek_nt": "word", "lexicon": "word", "commentary": "word", "sermons": "word",
    "taxonomy": "science", "oeis": "science", "languages": "science", "nuclear physics": "science",
    "astronomy": "science", "chemistry": "science", "physics": "science",
    "geography": "world", "economics": "world", "networking": "world", "rfcs": "world",
    "medicine": "world", "nutrition": "world", "activities": "world", "drugs": "world", "foods": "world",
    "dictionary": "dictionary",
    "gutenberg": "books", "classics": "books",
}
CORE = "core"                                  # always thawed


def shard_of(shelf: Optional[str]) -> str:
    return SHARD_ASSIGN.get((shelf or "").strip(), CORE)


def _shards_dir() -> Optional[Path]:
    d = os.environ.get("CONCORDANCE_CORPUS_SHARDS", "").strip()
    return Path(d) if d else None


def _single_db() -> Optional[str]:
    p = os.environ.get("CONCORDANCE_CORPUS_DB", "").strip()
    return p or None


def available() -> bool:
    d = _shards_dir()
    if d and (d / "manifest.json").exists():
        return True
    return bool(_single_db() and Path(_single_db()).exists())


def manifest() -> Dict[str, Any]:
    global _MANIFEST
    if _MANIFEST is None:
        d = _shards_dir()
        if d and (d / "manifest.json").exists():
            _MANIFEST = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        else:
            _MANIFEST = {"shards": {}, "mode": "single" if _single_db() else "none"}
    return _MANIFEST


def _open_db(path: str) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    c.execute("pragma query_only=on")
    c.execute("pragma mmap_size=134217728")    # 128 MB mmap window per shard — read from disk
    return c


def unfreeze(*names: str) -> List[str]:
    """Thaw (open) one or more shards so they answer queries. Idempotent. Returns what is now thawed."""
    with _LOCK:
        d = _shards_dir()
        if d:
            shards = manifest().get("shards", {})
            for name in names:
                if name in _OPEN:
                    continue
                info = shards.get(name)
                f = d / (info["file"] if info else f"{name}.db")
                if f.exists():
                    _OPEN[name] = _open_db(str(f))
        elif _single_db() and "all" not in _OPEN:
            _OPEN["all"] = _open_db(_single_db())     # single mode: one connection answers everything
        return list(_OPEN)


def freeze(*names: str) -> List[str]:
    """Re-freeze (close) shards to release their file handles / mmap. `core` cannot be frozen."""
    with _LOCK:
        for name in names:
            if name != CORE and name in _OPEN:
                try:
                    _OPEN.pop(name).close()
                except Exception:  # noqa: BLE001
                    pass
        return list(_OPEN)


# ── Rebalance the loads (the logistics layer) — thaw on demand, freeze the least-used ──
_USE: Dict[str, int] = {}     # shard -> last-use sequence number (a monotonic LRU clock)
_SEQ = 0


def _touch(name: str):
    global _SEQ
    _SEQ += 1
    _USE[name] = _SEQ


def thaw_for(*shelves: str) -> List[str]:
    """Unfreeze exactly the shards a set of shelves need — route a query's domain to its freight."""
    want = {shard_of(s) for s in shelves}
    want.discard(CORE)
    return unfreeze(*want) if want else thawed()


def rebalance(keep: int = 3) -> Dict[str, Any]:
    """Keep the load small: core stays thawed, plus the `keep` most-recently-used shards; freeze the
    rest to release their memory. The dispatcher trimming idle trucks off the yard."""
    with _LOCK:
        extra = [n for n in _OPEN if n != CORE and n != "all"]
    extra.sort(key=lambda n: _USE.get(n, 0), reverse=True)   # most-recently-used first
    to_freeze = extra[max(0, int(keep)):]
    if to_freeze:
        freeze(*to_freeze)
    return {"thawed": thawed(), "frozen": to_freeze, "keep": keep}


def _ensure_core():
    if not _OPEN:
        if _shards_dir():
            unfreeze(CORE)                             # a fresh device starts with just the core thawed
        else:
            unfreeze("all")


def thawed() -> List[str]:
    _ensure_core()
    return list(_OPEN)


def _match(query: str) -> str:
    terms = [t.lower() for t in _WORD.findall(query or "")]
    return " OR ".join(f'"{t}"' for t in terms)


def search(query: str, limit: int = 25, include_witness: bool = True) -> List[dict]:
    """Search across the THAWED shards (unfreeze more first to widen the horizon). FTS5 bm25 ranked."""
    _ensure_core()
    m = _match(query)
    if not m:
        return []
    where = "where fts match ?" + ("" if include_witness else " and c.surface != 'witness'")
    sql = f"select bm25(fts) as s, c.json from fts join cards c on c.id = fts.id {where} order by s limit ?"
    hits: List[tuple] = []
    for name, conn in list(_OPEN.items()):
        try:
            rows = conn.execute(sql, (m, int(limit))).fetchall()
            if rows:
                _touch(name)
            hits.extend(rows)
        except sqlite3.Error:
            continue
    hits.sort(key=lambda r: r[0])                      # merge shards by bm25 (lower = better)
    out = []
    for _s, blob in hits[:int(limit)]:
        try:
            out.append(json.loads(blob))
        except ValueError:
            continue
    return out


def airlock_search(query: str, limit: int = 25, shards: Optional[List[str]] = None,
                   include_witness: bool = True) -> List[dict]:
    """Airlock retrieval — the strictest load discipline. Core stays resident; every OTHER shard is
    brought into the chamber ONE at a time (thaw), searched (pull only what we need), and sealed back
    (refreeze) before the next. So at most `core` + one shard is ever open. The PULLED cards are
    returned to the caller and stay with them (the tool, available until the user is finished); the
    heavy shards never linger. Pass `shards` to bring in only certain freight; otherwise sweep all
    frozen shards. Slower than keeping shards thawed, but the smallest possible footprint."""
    _ensure_core()
    m = _match(query)
    if not m:
        return []
    where = "where fts match ?" + ("" if include_witness else " and c.surface != 'witness'")
    sql = f"select bm25(fts) as s, c.json from fts join cards c on c.id = fts.id {where} order by s limit ?"
    hits: List[tuple] = []
    for name, conn in list(_OPEN.items()):                # the resident set (core, always)
        try:
            rows = conn.execute(sql, (m, int(limit))).fetchall()
            if rows:
                _touch(name)
            hits.extend(rows)
        except sqlite3.Error:
            continue
    d = _shards_dir()
    if d:
        targets = set(shards) if shards else (set(manifest().get("shards", {})) - set(_OPEN) - {CORE})
        for name in targets:
            info = manifest().get("shards", {}).get(name)
            f = d / (info["file"] if info else f"{name}.db")
            if not f.exists():
                continue
            conn = _open_db(str(f))                        # bring the shard into the airlock
            try:
                hits.extend(conn.execute(sql, (m, int(limit))).fetchall())   # pull only what we need
            except sqlite3.Error:
                pass
            finally:
                conn.close()                               # seal it back — nothing lingers
    hits.sort(key=lambda r: r[0])
    out = []
    for _s, blob in hits[:int(limit)]:
        try:
            out.append(json.loads(blob))
        except ValueError:
            continue
    return out


def get_card(card_id: str) -> Optional[dict]:
    _ensure_core()
    for conn in list(_OPEN.values()):
        r = conn.execute("select json from cards where id = ?", (str(card_id),)).fetchone()
        if r:
            try:
                return json.loads(r[0])
            except ValueError:
                return None
    return None


def stats() -> Dict[str, Any]:
    man = manifest()
    thawed_names = thawed()
    total = 0
    for conn in _OPEN.values():
        try:
            total += int(conn.execute("select count(*) from cards").fetchone()[0])
        except sqlite3.Error:
            pass
    return {"backend": "sqlite-shards" if _shards_dir() else "sqlite-single",
            "thawed": thawed_names, "cards_thawed": total,
            "shards": {n: {"cards": i.get("cards"), "mb": i.get("mb"), "core": i.get("core", False)}
                       for n, i in man.get("shards", {}).items()},
            "note": "unfreeze more shards to widen the search; frozen shards cost only disk"}


__all__ = ["available", "manifest", "unfreeze", "freeze", "thaw_for", "rebalance", "thawed",
           "search", "airlock_search", "get_card", "stats", "shard_of", "SHARD_ASSIGN"]
