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

# THAWED SHARDS: name -> file path. NOT name -> connection, and the difference is a real bug.
#
# This module used to hold ONE connection per shard and hand it to every thread of the threading
# HTTP server. Telemetry caught the first symptom (`OperationalError: database is locked`), but
# driving 12 concurrent readers at one shared connection showed something worse underneath:
# `InterfaceError: bad parameter or other API misuse`, and `fetchone()` returning None for a row
# that certainly exists. That is not an outage, it is a WRONG ANSWER — a card reported missing
# while it sits in the file — and a library that quietly denies holding what it holds has failed at
# the one thing it is for.
#
# A sqlite3 connection is not safe for concurrent use across threads; `check_same_thread=False`
# only silences the guard, it does not make it true. So each thread opens its own connection to the
# same file. With `immutable=1` that is nearly free: no locks to take, and the OS page cache is
# shared across them all, so N threads do not mean N copies of the shard in memory.
_OPEN: Dict[str, str] = {}                    # shard name -> path (a thawed shard)
_TL = threading.local()                       # per-thread: {shard name: connection}


def _conn(name: str) -> Optional[sqlite3.Connection]:
    """This thread's connection to a thawed shard, opened on first use."""
    path = _OPEN.get(name)
    if not path:
        return None
    cache = getattr(_TL, "conns", None)
    if cache is None:
        cache = _TL.conns = {}
    c = cache.get(name)
    if c is None:
        try:
            c = cache[name] = _open_db(path)
        except sqlite3.Error:
            return None
    return c


def _conns() -> List[tuple]:
    """(name, connection) for every thawed shard, for the CALLING thread."""
    out = []
    for name in list(_OPEN):
        c = _conn(name)
        if c is not None:
            out.append((name, c))
    return out


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
    """Open one shard, read-only and lock-free.

    THE BUG THIS FIXES, recorded by our own telemetry 2026-07-29 16:55:
    `cards_browse — OperationalError: database is locked`. One connection per shard is shared
    across every thread of a ThreadingHTTPServer (`check_same_thread=False`), and under the
    30k-request days at the end of July, concurrent readers collided on SQLite's file locks. An
    agent asked and got an error instead of the library.

    `immutable=1` is the honest fix rather than a longer timeout, because it states something TRUE
    about these files: a shard is built offline by tools/build_corpus_db.py and shipped: nothing
    writes to it while the server runs. Told that, SQLite skips locking entirely — no shared cache,
    no WAL, no lock file, no contention possible. It is also faster, but correctness is the point.

    THE ONE OBLIGATION `immutable=1` CREATES: if a shard file is REBUILT underneath a running
    process, that process may read stale pages or garbage, because it has been promised the bytes
    cannot change. So a rebuild must be followed by a restart. `tools/deploy.sh` already restarts
    both services, and shards were last rebuilt on the box during a deploy — but the requirement is
    written here because the next person rebuilding shards by hand will not know it otherwise.
    """
    c = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True,
                        check_same_thread=False, timeout=10.0)
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
                    _OPEN[name] = str(f)              # thawed = registered; threads open their own
        elif _single_db() and "all" not in _OPEN:
            _OPEN["all"] = _single_db()               # single mode: one file answers everything
        return list(_OPEN)


def freeze(*names: str) -> List[str]:
    """Re-freeze (close) shards to release their file handles / mmap. `core` cannot be frozen."""
    with _LOCK:
        for name in names:
            if name != CORE and name in _OPEN:
                _OPEN.pop(name, None)
                # Close the calling thread's handle now; other threads drop theirs when they next
                # look and find the shard unregistered. Nothing leaks: a connection dies with its
                # thread, and re-thawing simply reopens.
                try:
                    (getattr(_TL, "conns", None) or {}).pop(name).close()
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
    for name, conn in _conns():
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
    for name, conn in _conns():                           # the resident set (core, always)
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
    for _name, conn in _conns():
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
    for _name, conn in _conns():
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
