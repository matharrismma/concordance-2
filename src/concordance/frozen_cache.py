"""THE FROZEN CACHE — persist what the boot re-derives from unchanged files (2026-10-08).

The launch roll-call measured the corpus warm at ~40 s / ~1 GB on the box, 98% of boot time. Phased, the bulk
is `load_cards` over the FROZEN shelves' files — hundreds of thousands of cards tokenized only to count
document frequency (`_df_extra`), parsed and shelved only to be discarded, and a compact (call, title,
surface) index of the public frozen ids kept (`_frozen`). All of it is a pure function of those files and the
freeze set: it changes only when they change. So it is built once and persisted here, and a boot whose inputs
are unchanged LOADS it — and, as of v3, reads from each cached file ONLY the lines that stayed resident, by
recorded byte offset (a file with none is never opened).

What makes this honest rather than a stale read:
  * The key covers exactly the files that CONTRIBUTED frozen cards at the cold build (identity = name, size,
    mtime_ns), the freeze set, the format version and the Python version. Any change to any of them misses —
    and the offsets are only ever used under that same key, against a byte-identical file.
  * Only BIG contributors (>= min_contribution() frozen cards) are cached; small, volatile ones —
    receipt_cards.jsonl and verified_cards.jsonl carry a few domain-shelf cards and grow with every seal —
    are processed live every boot and merged, so the key holds still across seals and nothing is missing.
  * A corrupt, truncated, foreign-version or wrong-key file is a miss, never an exception, never a partial read.
  * CONCORDANCE_FROZEN_CACHE=0 turns it off entirely (the safety valve); the cold path is the old one.
Format: marshal (stdlib, fast; version-bound, hence the key). Shared strings (interned call numbers and
surfaces) keep their sharing across dump/load — marshal writes refs for identical objects — so the memory
cut made at the cold build survives the cache. Stored under the data dir (untracked).
"""
from __future__ import annotations

import hashlib
import marshal
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = 4   # v3: per-contributor resident-line OFFSETS (a hit seeks to resident lines; [] = never opened)
              # v4: the contributor names + key live in a JSON SIDECAR, so peek never decodes the big file
FILE = "frozen_df.cache"
META = "frozen_df.meta.json"
MIN_CONTRIBUTION = 1000


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_FROZEN_CACHE", "1").strip() != "0"


def min_contribution() -> int:
    try:
        return max(1, int(os.environ.get("CONCORDANCE_FROZEN_CACHE_MIN", "").strip() or MIN_CONTRIBUTION))
    except ValueError:
        return MIN_CONTRIBUTION


def cache_path(data_dir: Path) -> Path:
    return Path(data_dir) / FILE


def file_identity(p: Path) -> Tuple[str, int, int]:
    """(name, size, mtime_ns) — what must be unchanged for a file's frozen contribution AND its resident-line
    offsets to be unchanged."""
    st = p.stat()
    return (p.name, int(st.st_size), int(st.st_mtime_ns))


def make_key(contributors: Iterable[Path], frozen: Iterable[str]) -> str:
    """The identity of the inputs: contributor files, the freeze set, the format and the interpreter."""
    h = hashlib.sha256()
    h.update(f"v{VERSION};py{sys.version_info[0]}.{sys.version_info[1]};".encode())
    h.update(("frozen=" + ",".join(sorted(set(frozen))) + ";").encode())
    for ident in sorted(file_identity(Path(p)) for p in contributors):
        h.update(("%s:%d:%d;" % ident).encode())
    return h.hexdigest()


def meta_path(path: Path) -> Path:
    return path.with_name(META)


def peek_contributors(path: Path) -> Optional[List[str]]:
    """The contributor file NAMES a cache was built from — from the tiny JSON sidecar (measured 2026-10-08:
    peeking by decoding the 85 MB marshal cost ~2.9 s of a 3.7 s cache load). Read without trusting anything
    else, so the caller can compute today's key over those same files and decide hit or miss. None if absent
    or unreadable (then the cache misses and is rebuilt)."""
    try:
        import json
        with open(meta_path(path), "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict) or obj.get("version") != VERSION:
            return None
        names = obj.get("contributors")
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            return None
        return names
    except Exception:  # noqa: BLE001 — unreadable is a miss, never an error
        return None


def load(path: Path, key: str) -> Optional[Dict[str, Any]]:
    """{df, fz, contributors, offsets, read_ms, decode_ms} when the file is whole and was built from exactly
    these inputs; else None. `offsets[name]` = the byte offsets of that contributor's RESIDENT lines ([] = none)."""
    try:
        t0 = time.perf_counter()
        with open(path, "rb") as f:
            obj = marshal.load(f)           # streamed: never the raw bytes AND the decoded tables at once
        t1 = t2 = time.perf_counter()
        if not isinstance(obj, dict) or obj.get("version") != VERSION or obj.get("key") != key:
            return None
        df, fz, names, offs = obj.get("df"), obj.get("fz"), obj.get("contributors"), obj.get("offsets")
        if not isinstance(df, dict) or not isinstance(fz, dict) or not isinstance(names, list) or not isinstance(offs, dict):
            return None
        if not set(offs) <= set(names):
            return None
        if not all(isinstance(v, list) and all(isinstance(o, int) for o in v) for v in offs.values()):
            return None
        return {"df": df, "fz": fz, "contributors": names, "offsets": offs,
                "read_ms": round((t1 - t0) * 1000.0, 1), "decode_ms": round((t2 - t1) * 1000.0, 1)}
    except Exception:  # noqa: BLE001
        return None


def save(path: Path, key: str, df: Dict[str, int], fz: Dict[str, tuple], contributors: List[str],
         offsets: Dict[str, List[int]]) -> bool:
    """Atomic (tmp + replace); never raises — a cache that cannot be written simply is not there next boot.
    `offsets`: per cached contributor, the byte offsets of its resident lines ([] = nothing resident)."""
    tmp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "wb") as f:
            marshal.dump({"version": VERSION, "key": key, "contributors": list(contributors),
                          "offsets": {n: list(v) for n, v in offsets.items()}, "df": dict(df), "fz": dict(fz)}, f)
        os.replace(tmp, path)
        import json
        mtmp = meta_path(path).with_suffix(".json.tmp")
        mtmp.write_text(json.dumps({"version": VERSION, "key": key, "contributors": list(contributors)}), encoding="utf-8")
        os.replace(mtmp, meta_path(path))
        return True
    except Exception:  # noqa: BLE001
        try:
            if tmp is not None:
                tmp.unlink()
        except Exception:  # noqa: BLE001
            pass
        return False
