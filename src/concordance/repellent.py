"""REPELLENT — the no-entry pheromone (the negative pole of stigmergy). Pharaoh ants do not only lay
recruiting trails; they lay a REPELLENT that marks an unrewarding branch so the colony learns to avoid
it (Robinson et al., Nature 2005). Our positive trail (stigmergy) strengthens what serves; this marks
what LEADS ASTRAY, so it is not amplified into paths it does not belong on.

The trigger is DISCERNMENT, not popularity — a source is repelled only when the front-door discernment
judges it primary material under the test (an occult text the PD ingest holds, surfaced next to the chart
that tests it; 1 John 4:1-3). Such a card stays fully retrievable — never deleted, never hidden (that is
quarantine, a heavier and human-judged act) — but carries a bounded DOWN-weight so it stops crowding
queries it does not answer (the observed problem: an occult source out-ranking on an unrelated query).
The mark FADES: a source not flagged again recovers over time (a long half-life) — avoidance, not a curse.

Aggregate and content-free (a decaying number per card — never who, never the query). Deposits are rare
(only when discernment fires), so a single lock-guarded read-merge-write is enough; the shared lock is
filelock (self-healing). GATED OFF by default (CONCORDANCE_REPELLENT): repel is a no-op and damp_factor
is exactly 1.0, so ranking is byte-for-byte unchanged until a node opts in. Held for review.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Dict, Iterable

from . import filelock

_RHO = 0.5
_HALFLIFE_S = 60 * 86400        # a repellent fades slowly — avoidance persists, but is not permanent
_W = 0.2                        # down-weight strength
_FLOOR = 0.5                    # a repelled card ranks at worst half — down-weighted, never zeroed
_DROP = 0.05
_MAX = 4000

_REPEL: Dict[str, float] = {}
_LAST_EVAP = [0.0]
_LOADED = [False]
_MTIME = [0.0]


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_REPELLENT", "").strip().lower() in ("1", "true", "yes", "on")


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "repellent.json"


def _read_disk() -> tuple[Dict[str, float], float]:
    p = _path()
    try:
        if p.is_file():
            d = json.loads(p.read_text(encoding="utf-8"))
            return ({str(k): float(v) for k, v in (d.get("repel") or {}).items()},
                    float(d.get("last_evap") or time.time()))
    except Exception:  # noqa: BLE001 — a bad store is not a crash
        pass
    return {}, time.time()


def _evap(trails: Dict[str, float], last_evap: float, now: float) -> Dict[str, float]:
    dt = now - last_evap
    if dt <= 0:
        return dict(trails)
    factor = _RHO ** (dt / _HALFLIFE_S)
    return {k: v * factor for k, v in trails.items() if v * factor >= _DROP}


def _load() -> None:
    if _LOADED[0]:
        return
    _LOADED[0] = True
    trails, last_evap = _read_disk()
    _REPEL.clear()
    _REPEL.update(trails)
    _LAST_EVAP[0] = last_evap
    try:
        _MTIME[0] = _path().stat().st_mtime
    except OSError:
        _MTIME[0] = 0.0


def _resync(now: float) -> None:
    """Cheap freshness: re-read if another worker wrote the shared store since we last looked."""
    try:
        mt = _path().stat().st_mtime
    except OSError:
        return
    if mt <= _MTIME[0]:
        return
    trails, last_evap = _read_disk()
    _REPEL.clear()
    _REPEL.update(_evap(trails, last_evap, now))
    _LAST_EVAP[0] = now
    _MTIME[0] = mt


def repel(card_ids: Iterable[str], amount: float = 1.0) -> None:
    """Mark cards as leading-astray — a no-entry deposit. Merges onto the shared store under a lock so
    a concurrent worker's marks are never clobbered. No-op when gated off."""
    ids = [str(c) for c in card_ids if c]
    if not enabled() or not ids:
        return
    _load()
    lock = _path().parent / (_path().stem + ".lock")
    _path().parent.mkdir(parents=True, exist_ok=True)
    with filelock.locked(lock) as got:
        if not got:
            return                                    # skip this write; a later deposit retries
        now = time.time()
        disk, last_evap = _read_disk()
        merged = _evap(disk, last_evap, now)
        for cid in ids:
            merged[cid] = min(merged.get(cid, 0.0) + amount, 1e6)
        if len(merged) > _MAX:
            merged = dict(sorted(merged.items(), key=lambda x: -x[1])[:_MAX])
        p = _path()
        tmp = p.parent / f"{p.stem}.{os.getpid()}.tmp"
        tmp.write_text(json.dumps({"repel": merged, "last_evap": now}), encoding="utf-8")
        tmp.replace(p)
        _REPEL.clear()
        _REPEL.update(merged)
        _LAST_EVAP[0] = now
        try:
            _MTIME[0] = p.stat().st_mtime
        except OSError:
            pass


def strength(card_id: str) -> float:
    if not enabled():
        return 0.0
    _load()
    now = time.time()
    _resync(now)
    return _evap(_REPEL, _LAST_EVAP[0], now).get(str(card_id), 0.0)


def damp_factor(card_id: str) -> float:
    """A multiplier in [_FLOOR, 1.0] for the ranker's `_finalize` — down-weights a repelled card WITHIN
    its tier (never zeroes it: it stays retrievable for discernment). Exactly 1.0 when off or unmarked."""
    if not enabled():
        return 1.0
    s = strength(card_id)
    if s <= 0:
        return 1.0
    return max(_FLOOR, 1.0 - _W * math.log1p(s))
