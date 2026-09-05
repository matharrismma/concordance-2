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

# ...AND A CONNECTION PER THREAD MUST BE CLOSED WHEN THE THREAD ENDS, or the fix above becomes a
# worse bug than the one it cured.
#
# Found by pressure test 2026-08-01, and it is the most serious defect this project has had.
# 250 rapid, innocent reads of /search took the secular engine's file-descriptor table to 1023 of
# 1024, and then EVERY /verify answered 500 — not because verification broke, but because Python
# could no longer open `receipts.py` to import it. A burst of reading knocked out proving.
#
# The arithmetic is the whole story: ThreadingHTTPServer opens a THREAD PER CONNECTION, this module
# opens a CONNECTION PER THREAD PER SHARD, and nothing ever closed one. Thread-per-request times
# connection-per-thread is unbounded by construction; the only question was how many minutes of
# traffic it took. 255 handles each on dictionary.db and books.db, 254 each on world.db and word.db.
#
# Raising LimitNOFILE would only have bought time — a leak refills. So the count is now BOUNDED at
# the source (a thread closes what it opened, in Handler.handle's finally) and, because a number
# nobody can see is a number that climbs again, it is COUNTABLE: `open_connections()` is reported by
# GET /health, so the next climb is visible before it is fatal.
#
# A REGISTRY OF THREADS, NOT A COUNTER OF CONNECTIONS — and it took two wrong instruments to get
# here, both caught by tests rather than by reasoning.
#
#   1st: an integer, incremented on open and decremented on close. It read 16 open when 0 files
#        were held, because a thread that touched a shard and exited without closing had its
#        connection reclaimed by the collector, and a hand-kept integer never learns about a
#        collection. It drifts UP and never comes back down. A number on /health that drifts is
#        worse than no number — it cries wolf, and the next real climb gets ignored.
#   2nd: a weakref.WeakSet, so entries would vanish with the object. `sqlite3.Connection` cannot be
#        weak-referenced: every shard read raised TypeError. tests/test_shard_concurrency.py failed
#        12 of 12 readers within seconds of the change. I had assumed, not checked.
#
# What is registered instead is the THREAD and its cache. Liveness is then a fact we can ask the
# runtime about (`Thread.is_alive()`), not a number we maintain and hope is right — so the count
# cannot drift in either direction.
#
# And the reaper does real work rather than only measuring: a dead thread's handles are CLOSED, not
# merely forgotten. `close_this_thread()` is the fast path for the HTTP handler; this is the
# backstop for every other thread that ever touches a shard, which is what the original leak was.
_LIVE_LOCK = threading.Lock()
_CACHES: Dict[int, tuple] = {}                # thread ident -> (thread, {shard: connection})
_PEAK = 0                                     # the high-water mark since boot — what nearly happened
_OPENED = 0                                   # LIFETIME opens; monotonic, never decremented
# `_OPENED` answers a different question from `open`/`peak`, and conflating them cost a gate run.
# `open` is a gauge (how many now) and `peak` is its high-water mark — both say what the WHOLE
# PROCESS holds, so neither can tell you whether one particular burst did any work: a test whose
# burst opened 5 connections could not push a peak another test had already driven to 16, and the
# coverage guard rightly refused the verdict. A monotonic total can. For an operator it is also the
# churn rate — opens per hour is what says whether keep-alive is working.


def _reap_dead_threads() -> int:
    """Close shard handles left behind by threads that have exited. Caller holds _LIVE_LOCK."""
    closed = 0
    for ident, (t, cache) in list(_CACHES.items()):
        if t.is_alive():
            continue
        for c in list(cache.values()):
            try:
                c.close()
                closed += 1
            except Exception:  # noqa: BLE001 — one bad close must not strand the rest
                pass
        cache.clear()
        _CACHES.pop(ident, None)
    return closed


def _live_count() -> int:
    return sum(len(cache) for _t, cache in _CACHES.values())


def open_connections() -> Dict[str, int]:
    """How many shard connections are open right now, and the worst it has been.

    Reaps dead threads' handles first, so the number is current rather than remembered. The leak
    that motivated this was invisible until the process could not open a file; this makes it a
    number on /health instead of a 500 with no explanation.
    """
    with _LIVE_LOCK:
        reaped = _reap_dead_threads()
        return {"open": _live_count(), "peak": _PEAK, "shards_thawed": len(_OPEN),
                "reaped": reaped, "opened_total": _OPENED}


def _conn(name: str) -> Optional[sqlite3.Connection]:
    """This thread's connection to a thawed shard, opened on first use."""
    global _PEAK, _OPENED
    path = _OPEN.get(name)
    if not path:
        return None
    cache = getattr(_TL, "conns", None)
    if cache is None:
        cache = _TL.conns = {}
        with _LIVE_LOCK:
            t = threading.current_thread()
            _CACHES[t.ident] = (t, cache)
    # KEYED BY NAME **AND PATH**. Keying on the name alone means a shard re-registered at a new
    # file — refrozen and rethawed elsewhere, or rebuilt and shipped to a different directory —
    # keeps being served from the OLD file by every thread that already had it open, silently and
    # forever. Found 2026-08-01 when two test modules each registered a shard called `core` at
    # different paths and the second was served the first one's cards. On a live box the same shape
    # is a reader getting a stale corpus with no error anywhere, which is the failure this module
    # exists to prevent: a library confidently handing over the wrong thing.
    paths = getattr(_TL, "paths", None)
    if paths is None:
        paths = _TL.paths = {}
    if paths.get(name) != path and name in cache:
        try:
            cache.pop(name).close()
        except Exception:  # noqa: BLE001
            pass
    paths[name] = path
    c = cache.get(name)
    if c is None:
        try:
            c = cache[name] = _open_db(path)
        except sqlite3.Error:
            return None
        with _LIVE_LOCK:
            # Reap opportunistically: a process that never serves /health must still self-heal, and
            # the registry is where dead threads pile up. Cheap — it walks idents, not files.
            if len(_CACHES) > 64:
                _reap_dead_threads()
            _OPENED += 1
            _PEAK = max(_PEAK, _live_count())
    return c


def close_this_thread() -> int:
    """Close every shard connection THIS thread opened. Returns how many were closed.

    Called from the HTTP handler's `finally` when a connection is finished — once per client
    connection, not once per request, so keep-alive still reuses an open shard. Safe to call on a
    thread that never opened one (returns 0), and safe to call twice.
    """
    cache = getattr(_TL, "conns", None)
    if not cache:
        return 0
    n = 0
    for c in list(cache.values()):
        try:
            c.close()
            n += 1
        except Exception:  # noqa: BLE001 — a close that fails must not strand the rest
            pass
    cache.clear()
    # Drop the thread-local entirely, not just its contents: `_conn` registers a thread in _CACHES
    # only when it creates the cache, so a thread that closed and then read again would rebuild an
    # UNREGISTERED cache — invisible to the reaper and to /health, which is the original leak wearing
    # a different hat. Clearing the local forces re-registration on the next read.
    _TL.conns = None
    _TL.paths = None
    with _LIVE_LOCK:
        _CACHES.pop(threading.get_ident(), None)   # this thread holds nothing now
    return n


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
    """Where the FTS shards live. An explicit `CONCORDANCE_CORPUS_SHARDS` wins; otherwise the shards
    sit beside the data at `<CONCORDANCE_DATA_DIR>/shards` (or `data/shards`), so the memory-efficient
    freeze design is DISCOVERABLE by default wherever the shards were built — not gated behind a second
    env var that has to be remembered separately.

    2026-09-05: on the live box `CONCORDANCE_FREEZE_SHELVES` was set but `CONCORDANCE_CORPUS_SHARDS`
    was not, so `available()` was False, `frozen_shelves()` returned empty, and the WHOLE corpus loaded
    resident (~3.5 GB/process) with freezing silently off — one env var quietly disarming the other.
    The fallback closes that trap: `CONCORDANCE_DATA_DIR` (already set for the data) now suffices.
    Still returns None when no built shards are present, so nothing changes where they don't exist."""
    d = os.environ.get("CONCORDANCE_CORPUS_SHARDS", "").strip()
    if d:
        return Path(d)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    cand = (Path(data) if data else Path("data")) / "shards"
    return cand if (cand / "manifest.json").exists() else None


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
    """Re-freeze (close) shards to release their file handles / mmap. `core` cannot be frozen.

    THIS FUNCTION USED TO CLAIM "nothing leaks: a connection dies with its thread." That sentence
    was the bug. Freezing drops the shard from `_OPEN` and closes the CALLING thread's handle; every
    other thread's handle to the same file is simply orphaned — unreachable through `_OPEN`, still
    holding a descriptor. Under thread-per-connection that is one leaked handle per live thread per
    freeze, on top of the leak fixed in `close_this_thread`. Both were the same false belief written
    twice, and on 2026-08-01 they took the engine to 1023 of 1024 descriptors.

    A thread's handles are now released by `close_this_thread()` when its connection ends, so the
    orphans here are bounded and short-lived rather than permanent — and the count is decremented so
    `open_connections()` stays true.
    """
    with _LOCK:
        for name in names:
            if name != CORE and name in _OPEN:
                _OPEN.pop(name, None)
                try:
                    c = (getattr(_TL, "conns", None) or {}).pop(name)
                except Exception:  # noqa: BLE001 — this thread may never have opened it
                    continue
                try:
                    c.close()
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


# Words that carry no subject. A query is what remains after these are removed.
_STOP = frozenset("""
a an the of and or to in on at by for from with as is are was were be been being am do does did
this that these those there here it its it's his her hers their theirs our ours your yours my mine
me i you he she they we us him them who whom whose which what where when why how whether if then
than so such about into over under again more most other some any all each own same very can could
should would will shall may might must have has had not no nor only just also too both few
""".split())


def _match(query: str, mode: str = "all") -> str:
    """Build the FTS expression. `mode="all"` requires every content word; `"any"` is the fallback.

    THE BUG THIS FIXES — found by the 1,000-probe ancient assay, 2026-08-01, and it is a doctrinal
    failure, not a ranking nicety:

        q="Mahavira"          -> 0 results, and the want_hint offers to record the miss.  CORRECT.
        q="what is Mahavira"  -> 3 results: Aurelius Meditations 8.51, 8.10, Boethius §boe_03_10.

    The old expression was `" OR ".join(every token)`, stopwords included, so a natural-language
    question matched any card containing "what" or "is". Three classics cards surfaced across ~250
    unrelated queries — Sumerian cities, Chinese philosophers, Vedic texts — because they happen to
    contain common English words.

    THE HARM IS NOT THAT THE RANKING IS POOR. It is that a MISS IS RENDERED AS AN ANSWER. The
    library says "here is what I have" when the truth is "I do not have that", and because results
    came back, `want_hint` never fires and the miss is never recorded. The shepherd loop is fed by
    misses; this silently starved it. It is the same error as sealing our own failure as a verdict:
    a gap is a third state, and it must be allowed to say so.

    A question made only of stopwords ("what is it") returns "" — no subject was asked about, and
    matching everything is not an answer.
    """
    terms = [t.lower() for t in _WORD.findall(query or "")]
    content = [t for t in terms if t not in _STOP]
    if not content:
        return ""
    join = " AND " if mode == "all" else " OR "
    return join.join(f'"{t}"' for t in content)


def search(query: str, limit: int = 25, include_witness: bool = True) -> List[dict]:
    """Search across the THAWED shards (unfreeze more first to widen the horizon). FTS5 bm25 ranked."""
    _ensure_core()
    where = "where fts match ?" + ("" if include_witness else " and c.surface != 'witness'")
    sql = f"select bm25(fts) as s, c.json from fts join cards c on c.id = fts.id {where} order by s limit ?"

    def _run(expr: str) -> List[tuple]:
        got: List[tuple] = []
        for name, conn in _conns():
            try:
                rows = conn.execute(sql, (expr, int(limit))).fetchall()
                if rows:
                    _touch(name)
                got.extend(rows)
            except sqlite3.Error:
                continue
        return got

    # ALL the content words first, ANY of them only as a fallback. Precision before recall, because
    # a wrong answer costs more than no answer: an empty result tells the truth and offers to record
    # the want, while a loose match buries the gap under something irrelevant.
    hits: List[tuple] = []
    m = _match(query, "all")
    if m:
        hits = _run(m)
    if not hits:
        m_any = _match(query, "any")
        # Only worth a second pass when there were several content words to loosen.
        if m_any and m_any != m:
            hits = _run(m_any)
    if not hits:
        return []

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
