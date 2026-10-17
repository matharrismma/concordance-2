"""THE CORPUS CACHE — the built index persisted whole, so a cold process LOADS instead of rebuilds (issue #10).

Measured 2026-10-16 (local, Python 3.14, cProfile + tracemalloc): a COLD `default_corpus()` took 1337 s and
5.9 GB peak for 932,544 cards from 1.41 GB of JSONL — `json.loads` 470 s, `is_public` 250 s over 2.8M calls,
`shelve` 64 s, the index build 622 s — every one of them per-card Python work that is identical on every boot.
The frozen cache (frozen_cache.py) covers only the FROZEN shelves' freight; with nothing frozen — every local
run, every CLI tool, the structural tests — the whole keeping was rebuilt from the JSONL each time.

What is kept: everything `Corpus.__init__` derives (see `Corpus._state`) — the parsed card dicts (shelved,
bridged, deduped), the token postings, the call-number tree, the per-call groups, the public order, the frozen
index and its DF table. What is NOT kept: runtime state (the search cache, the lock), made fresh on restore.
The JSONL stays the source of truth; the cache is a derived file, rebuilt whenever its inputs change.

What makes this honest rather than a stale read:
  * The key covers EVERY file `load_cards` would read (cards.jsonl, each extra that exists, the signposts, each
    bridge overlay) by (path, size, mtime_ns); the freeze set; the format version; the interpreter (marshal is
    version-bound); the index word size; and the CONTENT HASH of corpus.py itself, so a change to the shelving
    or ranking code rebuilds without anyone remembering to bump a version. Any change -> a miss -> a rebuild ->
    the superseded file pruned.
  * A corrupt, truncated, foreign-version or wrong-key file is a miss, never an exception, never a partial corpus.
  * CONCORDANCE_CORPUS_CACHE=0 turns it off (the cold path is untouched); =rebuild ignores an existing file and
    writes a fresh one. CONCORDANCE_CORPUS_CACHE_DIR relocates the files (default <data dir>/.cache, untracked).
  * Written atomically (tmp + os.replace); a reader never sees a half-written file.

Format: a magic header, then length-prefixed records — marshal for objects (measured 2026-10-17 on 20k real
cards: dump 0.04 s / load 0.12 s / 16.2 MB, vs pickle-5 0.34 s / 0.23 s / 17.3 MB), raw index arrays for the
postings. Cards ride in chunks of CHUNK, so neither side holds more than one chunk of transient bytes. The
postings, the call groups and the public order are 32-bit indexes into ONE id table, so every card id is one
string object shared by the cards dict, the postings and the public order — exactly as a fresh build shares
them. Dict KEYS and a few repeating VALUES (shelf, surface, kind, call, ...) are interned on the way out:
marshal writes interned strings as such and interns them on the way in, so a loaded keeping holds one object
per distinct key across all 932k cards, where `json.loads` gives every card its own copy of "id", "title", ...
"""
from __future__ import annotations

import hashlib
import marshal
import os
import struct
import sys
import time
from array import array
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = 1
MAGIC = b"NHCORPUS\x00\x01"
PREFIX = "corpus-"
SUFFIX = ".marshal"
CHUNK = 20_000                      # cards per record: ~16 MB of transient bytes a side, never the whole keeping
_IDX = "I"                          # index arrays: unsigned 32-bit — the keeping is far below 4.29 billion ids
_ITEMSIZE = array(_IDX).itemsize
_REC = struct.Struct(">BQ")         # record kind + payload length
_K_OBJ, _K_RAW = 0, 1
_STALE_TMP_S = 2 * 3600             # a .tmp older than this is a crashed writer's leftover, safe to prune

# card fields whose VALUES repeat across the keeping (shelf names, surfaces, kinds, call numbers, bridge
# relationships and evidence, source labels) — interned on the way out so a loaded keeping holds one object per
# distinct value, not one per card. Equality is untouched; only identity is shared.
_INTERN_VALUES = frozenset({"shelf", "surface", "kind", "box", "visibility", "lifecycle_stage", "volatility",
                            "author", "call", "relationship", "evidence", "domain", "authority_tier", "label"})


def mode() -> str:
    """'on' (default), 'off' (CONCORDANCE_CORPUS_CACHE=0) or 'rebuild' (ignore an existing file, write afresh)."""
    v = os.environ.get("CONCORDANCE_CORPUS_CACHE", "1").strip().lower()
    if v in ("0", "off", "false", "no"):
        return "off"
    if v == "rebuild":
        return "rebuild"
    return "on"


def enabled() -> bool:
    return mode() != "off"


def cache_dir(data_dir: Path) -> Path:
    env = os.environ.get("CONCORDANCE_CORPUS_CACHE_DIR", "").strip()
    return Path(env) if env else Path(data_dir) / ".cache"


def file_identity(p: Path) -> Tuple[str, int, int]:
    """(absolute path, size, mtime_ns) — what must be unchanged for a source file's contribution to be unchanged."""
    st = p.stat()
    return (os.path.abspath(p), int(st.st_size), int(st.st_mtime_ns))


def code_fingerprint(files: Iterable[Path]) -> str:
    """sha256 over the SOURCE of the modules that derive the index (corpus.py): a changed shelving or ranking
    rule changes the key, so the cache rebuilds without a manual version bump. Unreadable -> a constant, so a
    frozen/zipped deployment still caches (keyed on VERSION alone)."""
    h = hashlib.sha256()
    for p in files:
        try:
            h.update(Path(p).read_bytes())
        except OSError:
            h.update(b"?")
    return h.hexdigest()


def make_key(files: Iterable[Path], frozen: Iterable[str], code: str = "") -> str:
    """The identity of the inputs: every source file, the freeze set, the format, the interpreter, the index
    word size and the deriving code."""
    h = hashlib.sha256()
    h.update(f"v{VERSION};py{sys.version_info[0]}.{sys.version_info[1]};idx{_ITEMSIZE};code={code};".encode())
    h.update(("frozen=" + ",".join(sorted(set(frozen))) + ";").encode())
    for ident in sorted(file_identity(Path(p)) for p in files):
        h.update(("%s:%d:%d;" % ident).encode("utf-8", "surrogateescape"))
    return h.hexdigest()


def cache_path(data_dir: Path, key: str) -> Path:
    return cache_dir(data_dir) / f"{PREFIX}{key[:32]}{SUFFIX}"


# ── the records ────────────────────────────────────────────────────────────────────────────────────────

def _write(f, kind: int, payload: bytes) -> None:
    f.write(_REC.pack(kind, len(payload)))
    f.write(payload)


def _write_obj(f, obj: Any) -> None:
    _write(f, _K_OBJ, marshal.dumps(obj))


def _write_raw(f, arr: array) -> None:
    _write(f, _K_RAW, arr.tobytes())


def _read_head(f, kind: int) -> int:
    head = f.read(_REC.size)
    if len(head) != _REC.size:
        raise EOFError("truncated")
    k, n = _REC.unpack(head)
    if k != kind:
        raise ValueError("record kind")
    return n


def _read_obj(f) -> Any:
    n = _read_head(f, _K_OBJ)
    buf = f.read(n)
    if len(buf) != n:
        raise EOFError("truncated")
    return marshal.loads(buf)


def _read_raw(f) -> array:
    """One index array, read STRAIGHT into the array (no bytes copy in between)."""
    n = _read_head(f, _K_RAW)
    if n % _ITEMSIZE:
        raise ValueError("array length")
    arr = array(_IDX, [0]) * (n // _ITEMSIZE)
    if n and f.readinto(arr) != n:
        raise EOFError("truncated")
    return arr


def _compact(obj: Any, _intern=sys.intern, _iv=_INTERN_VALUES) -> Any:
    """A copy of a card with every dict KEY (and the repeating values named in _INTERN_VALUES) interned, so
    marshal writes them as interned strings and the loaded keeping shares one object per distinct key. Lists
    and dicts are rebuilt; every other value (the body text, numbers, None) is the same object. Equal, not
    identical, to the original — the live corpus that wrote it is never touched."""
    if type(obj) is dict:
        out = {}
        for k, v in obj.items():
            if type(k) is str:
                k = _intern(k)
            tv = type(v)
            if tv is str:
                if k in _iv:
                    v = _intern(v)
            elif tv is dict or tv is list:
                v = _compact(v)
            out[k] = v
        return out
    if type(obj) is list:
        return [_compact(x) if (type(x) is dict or type(x) is list) else x for x in obj]
    return obj


def _write_index(f, mapping: Dict[str, List[str]], pos: Dict[str, int]) -> None:
    """A {key: [card_id, ...]} index as three records: the keys (in order), the offsets, the flat postings as
    indexes into the id table."""
    keys = list(mapping)
    offs = array(_IDX, [0])
    post = array(_IDX)
    get = pos.__getitem__
    for lst in mapping.values():
        post.extend(map(get, lst))
        offs.append(len(post))
    if len(post) >= 1 << (8 * _ITEMSIZE):
        raise OverflowError("postings exceed the index word")
    _write_obj(f, keys)
    _write_raw(f, offs)
    _write_raw(f, post)


def _read_index(f, ids: List[str]) -> Dict[str, List[str]]:
    keys = _read_obj(f)
    offs = _read_raw(f)
    post = _read_raw(f)
    if not isinstance(keys, list) or len(offs) != len(keys) + 1 or (offs and offs[-1] != len(post)):
        raise ValueError("index shape")
    get = ids.__getitem__
    out: Dict[str, List[str]] = {}
    a = 0
    for i, k in enumerate(keys):
        b = offs[i + 1]
        out[k] = list(map(get, post[a:b]))
        a = b
    return out


# ── save / load ────────────────────────────────────────────────────────────────────────────────────────

def save(path: Path, key: str, state: Dict[str, Any]) -> bool:
    """Write `state` (as Corpus._state() gives it) under `key`. Atomic (tmp + replace); never raises — a cache
    that cannot be written simply is not there next boot. True on success."""
    tmp: Optional[Path] = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + f".tmp{os.getpid()}")
        cards: Dict[str, dict] = state["cards"]
        frozen: Dict[str, tuple] = state["frozen"]
        ids: List[str] = list(cards)
        ids.extend(frozen)
        pos = {cid: i for i, cid in enumerate(ids)}
        if len(pos) != len(ids):
            raise ValueError("an id is both resident and frozen")
        with open(tmp, "wb", buffering=1 << 20) as f:
            f.write(MAGIC)
            _write_obj(f, {"version": VERSION, "key": key,
                           "py": f"{sys.version_info[0]}.{sys.version_info[1]}", "itemsize": _ITEMSIZE,
                           "n_resident": len(cards), "n_frozen": len(frozen), "chunk": CHUNK,
                           "min_idf": float(state["min_idf"]), "n": int(state["n"]), "froze": bool(state["froze"]),
                           "written_at": time.time()})
            _write_obj(f, ids)
            buf: List[dict] = []
            for c in cards.values():
                buf.append(_compact(c))
                if len(buf) >= CHUNK:
                    _write_obj(f, buf)
                    buf = []
            if buf:
                _write_obj(f, buf)
            del buf
            _write_index(f, state["by_token"], pos)
            _write_index(f, state["cids_by_call"], pos)
            _write_raw(f, array(_IDX, map(pos.__getitem__, state["public_sorted"])))
            _write_raw(f, array(_IDX, map(pos.__getitem__, frozen)))
            _write_obj(f, list(frozen.values()))
            _write_obj(f, {"call_tree": state["call_tree"], "df_extra": state["df_extra"],
                           "frozen_shelf_counts": state["frozen_shelf_counts"]})
            _write_obj(f, {"end": True, "key": key})       # the trailer: proves the write ran to completion
        del pos, ids
        os.replace(tmp, path)
        return True
    except Exception:  # noqa: BLE001 — unwritable is "no cache", never a failed boot
        try:
            if tmp is not None and tmp.exists():
                tmp.unlink()
        except Exception:  # noqa: BLE001
            pass
        return False


def load(path: Path, key: str) -> Optional[Dict[str, Any]]:
    """The state dict for Corpus._restore when `path` is whole and was written under exactly `key`; else None.
    Never raises. Memory: one record of transient bytes at a time; the id table is shared by every structure."""
    try:
        with open(path, "rb", buffering=1 << 20) as f:
            if f.read(len(MAGIC)) != MAGIC:
                return None
            h = _read_obj(f)
            if (not isinstance(h, dict) or h.get("version") != VERSION or h.get("key") != key
                    or h.get("py") != f"{sys.version_info[0]}.{sys.version_info[1]}"
                    or h.get("itemsize") != _ITEMSIZE):
                return None
            n_res, n_fz = int(h["n_resident"]), int(h["n_frozen"])
            ids = _read_obj(f)
            if not isinstance(ids, list) or len(ids) != n_res + n_fz:
                return None
            get = ids.__getitem__
            cards: Dict[str, dict] = {}
            i = 0
            while i < n_res:
                chunk = _read_obj(f)
                if not isinstance(chunk, list) or not chunk:
                    return None
                for c in chunk:
                    cid = ids[i]
                    if type(c) is not dict or c.get("id") != cid:
                        return None
                    c["id"] = cid                    # ONE id object: the key, the card's own id, every posting
                    cards[cid] = c
                    i += 1
            by_token = _read_index(f, ids)
            cids_by_call = _read_index(f, ids)
            public_sorted = list(map(get, _read_raw(f)))
            fkeys = _read_raw(f)
            fvals = _read_obj(f)
            if len(fkeys) != n_fz or not isinstance(fvals, list) or len(fvals) != n_fz:
                return None
            frozen = dict(zip(map(get, fkeys), fvals))
            tail = _read_obj(f)
            end = _read_obj(f)
            if not isinstance(tail, dict) or not isinstance(end, dict) or end.get("key") != key:
                return None
        return {"cards": cards, "min_idf": float(h["min_idf"]), "n": int(h["n"]), "froze": bool(h["froze"]),
                "by_token": by_token, "df_extra": tail["df_extra"], "frozen": frozen,
                "frozen_shelf_counts": tail["frozen_shelf_counts"], "call_tree": tail["call_tree"],
                "cids_by_call": cids_by_call, "public_sorted": public_sorted}
    except Exception:  # noqa: BLE001 — corrupt, truncated, foreign: a miss, never an error
        return None


def prune(keep: Path) -> int:
    """Remove superseded cache files beside `keep` (other keys' files, and tmp leftovers older than two
    hours — a writer still running keeps its own). Returns how many were removed. Never raises."""
    n = 0
    try:
        now = time.time()
        for q in keep.parent.glob(PREFIX + "*" + SUFFIX + "*"):
            if q == keep:
                continue
            is_tmp = ".tmp" in q.name[len(PREFIX):]
            try:
                if is_tmp and now - q.stat().st_mtime < _STALE_TMP_S:
                    continue
                q.unlink()
                n += 1
            except OSError:
                continue
    except OSError:
        pass
    return n
