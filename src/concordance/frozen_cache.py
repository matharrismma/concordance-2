"""THE FROZEN CACHE — persist what the boot re-derives from unchanged files (2026-10-08).

The launch roll-call measured the corpus warm at ~40 s / ~1 GB on the box, 98% of boot time. Phased, the bulk
is `load_cards` tokenizing the full text of every FROZEN card — hundreds of thousands of them — only to count
document frequency (`_df_extra`) and to keep a compact (call, title, surface) index of the public frozen ids
(`_frozen`). Both are pure functions of the frozen cards' files and the freeze set: they change only when those
files change. So they are built once and persisted here, and a boot whose inputs are unchanged LOADS them.

What makes this honest rather than a stale read:
  * The key covers exactly the files that CONTRIBUTED frozen cards at the cold build (identity = name, size,
    mtime_ns), the freeze set, the format version and the Python version. Any change to any of them misses.
    It deliberately does NOT cover files that contributed no frozen card — receipt_cards.jsonl grows with every
    seal and would miss on every boot — and a frozen card that later appears in such a file is still handled
    LIVE by load_cards and merged, so nothing is ever silently missing (see corpus.default_corpus).
  * A corrupt, truncated, foreign-version or wrong-key file is a miss, never an exception, never a partial read.
  * CONCORDANCE_FROZEN_CACHE=0 turns it off entirely (the safety valve); the cold path is byte-for-byte the
    old one.
Format: marshal (stdlib, fast; version-bound, hence the key). Stored under the data dir (untracked).
"""
from __future__ import annotations

import hashlib
import marshal
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = 2   # v2: + skip_files — cached contributors with no resident cards, skipped wholesale on a hit
FILE = "frozen_df.cache"
# Only a file that contributes at least this many frozen cards is cached and skipped on a hit. Smaller
# contributors — receipt_cards.jsonl and verified_cards.jsonl carry a few domain-shelf (frozen) cards and
# grow with every seal — are processed LIVE on every boot (cheap by definition) and merged, so the key
# stays stable across seals and nothing is ever missing. Overridable for tests (a tiny corpus is all small).
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
    """(name, size, mtime_ns) — what must be unchanged for a file's frozen contribution to be unchanged."""
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


def peek_contributors(path: Path) -> Optional[List[str]]:
    """The contributor file NAMES a cache was built from — read without trusting anything else in it, so the
    caller can compute today's key over those same files and decide hit or miss. None if unreadable."""
    try:
        with open(path, "rb") as f:
            obj = marshal.load(f)
        if not isinstance(obj, dict) or obj.get("version") != VERSION:
            return None
        names = obj.get("contributors")
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            return None
        return names
    except Exception:  # noqa: BLE001 — unreadable is a miss, never an error
        return None


def load(path: Path, key: str) -> Optional[Dict[str, Any]]:
    """{df, fz, contributors} when the file is whole and was built from exactly these inputs; else None."""
    try:
        with open(path, "rb") as f:
            obj = marshal.load(f)
        if not isinstance(obj, dict) or obj.get("version") != VERSION or obj.get("key") != key:
            return None
        df, fz, names = obj.get("df"), obj.get("fz"), obj.get("contributors")
        if not isinstance(df, dict) or not isinstance(fz, dict) or not isinstance(names, list):
            return None
        skip = obj.get("skip_files") or []
        if not isinstance(skip, list) or not set(skip) <= set(names):
            return None
        return {"df": df, "fz": fz, "contributors": names, "skip_files": skip}
    except Exception:  # noqa: BLE001
        return None


def save(path: Path, key: str, df: Dict[str, int], fz: Dict[str, tuple], contributors: List[str],
         skip_files: Optional[List[str]] = None) -> bool:
    """Atomic (tmp + replace); never raises — a cache that cannot be written simply is not there next boot.
    `skip_files`: the cached contributors that hold NO resident card, so a hit need not open them at all."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "wb") as f:
            marshal.dump({"version": VERSION, "key": key, "contributors": list(contributors),
                          "skip_files": list(skip_files or []), "df": dict(df), "fz": dict(fz)}, f)
        os.replace(tmp, path)
        return True
    except Exception:  # noqa: BLE001
        try:
            tmp.unlink()  # type: ignore[possibly-undefined]
        except Exception:  # noqa: BLE001
            pass
        return False
