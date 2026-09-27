"""STIGMERGY — the keeping's pheromone layer (Ant Colony Optimization, applied to recall).

Ants coordinate with no central plan by leaving pheromone in the shared environment: trails that prove
useful strengthen (deposit), unused ones fade (evaporation), and the colony self-organizes onto the
good paths. The keeping is our shared environment; this makes the CARDS the trails. A card retrieved in
a result deposits a little pheromone; all trails evaporate over time; a small, capped ranking boost
lets a well-travelled card lead WITHIN the tier it already earned (never smuggling an off-subject hit
up — same discipline as the other _finalize boosts).

ONE SHARED TRAIL, MANY WORKERS. The two faces (.org witness, .com secular) are two processes over ONE
keeping, so they share one pheromone store. A naive "write my whole in-memory view" would let each
process clobber the other's deposits (last writer wins — the colony forgets half its work). Instead each
process holds only its PENDING deltas since its last flush, and a flush MERGES them onto the on-disk
trail under a cross-process lock: read the shared state, evaporate it to now, add my deltas, write. No
deposit is lost, whoever laid it. Reads resync from the shared store on a bound, so a trail worn by one
face is felt by the other. This is the stigmergic medium done honestly — the environment is the memory,
and the memory is shared.

PRIVACY: the trail is AGGREGATE — a single decaying number per card, a pheromone CONCENTRATION. It never
records who searched, what they asked, or that anyone READ anything (the shelf's covenant, kept). It is
the engine's own path-reinforcement, not surveillance.

GATED OFF by default (CONCORDANCE_STIGMERGY): deposit is a no-op and the boost is exactly 1.0, so the
ranking is byte-for-byte unchanged until a node opts in. Held for review.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

_RHO = 0.5              # evaporation: a trail halves every half-life if not refreshed
_HALFLIFE_S = 30 * 86400
_W = 0.15               # boost weight
_CAP = 1.6              # a trail can lift a card at most 1.6x WITHIN its tier — never across tiers
_MAX = 4000             # keep only the strongest N trails resident/persisted (bounded)
_FLUSH_EVERY = 25       # throttle disk writes: flush after this many deposits
_EVAP_MIN_S = 3600      # evaporate at most hourly (lazy)
_RESYNC_MIN_S = 300     # re-read the shared store at most this often on reads (bounds I/O)
_LOCK_TIMEOUT_S = 5.0   # wait at most this long for the shared-store lock (else keep pending, retry)
_LOCK_STALE_S = 15.0    # a lock older than this is presumed abandoned by a dead worker, and stolen

_TRAILS: Dict[str, float] = {}   # local read cache: the shared store merged with our own pending
_PENDING: Dict[str, float] = {}  # deposits made in THIS process since its last successful flush (raw)
_LAST_EVAP = [0.0]               # clock for lazy evaporation of the read cache
_LAST_SYNC = [0.0]               # last time the cache was resynced from the shared store
_LOADED = [False]
_LOADED_MTIME = [0.0]            # mtime of the store at our last read — detects another worker's write
_DIRTY = [0]


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_STIGMERGY", "").strip().lower() in ("1", "true", "yes", "on")


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "stigmergy.json"


def _lockpath() -> Path:
    p = _path()
    return p.parent / (p.stem + ".lock")


def _read_disk() -> Tuple[Dict[str, float], float]:
    """The shared store as it is on disk right now. A bad/absent store is not a crash — start empty."""
    p = _path()
    try:
        if p.is_file():
            d = json.loads(p.read_text(encoding="utf-8"))
            trails = {str(k): float(v) for k, v in (d.get("trails") or {}).items()}
            return trails, float(d.get("last_evap") or time.time())
    except Exception:  # noqa: BLE001
        pass
    return {}, time.time()


def _evap_map(trails: Dict[str, float], last_evap: float, now: float) -> Dict[str, float]:
    """Evaporate a whole trail map from `last_evap` to `now`; a faded trail is forgotten, not hoarded."""
    dt = now - last_evap
    if dt <= 0:
        return dict(trails)
    factor = _RHO ** (dt / _HALFLIFE_S)
    out: Dict[str, float] = {}
    for k, v in trails.items():
        nv = v * factor
        if nv >= 0.05:
            out[k] = nv
    return out


def _load() -> None:
    if _LOADED[0]:
        return
    _LOADED[0] = True
    trails, last_evap = _read_disk()
    _TRAILS.clear()
    _TRAILS.update(trails)
    _LAST_EVAP[0] = last_evap
    now = time.time()
    _LAST_SYNC[0] = now
    try:
        _LOADED_MTIME[0] = _path().stat().st_mtime
    except OSError:
        _LOADED_MTIME[0] = 0.0


def _evaporate(now: float | None = None) -> None:
    """Lazily evaporate the local read cache (bounded to hourly) so reads reflect fading without I/O."""
    now = now or time.time()
    dt = now - _LAST_EVAP[0]
    if dt < _EVAP_MIN_S:
        return
    factor = _RHO ** (dt / _HALFLIFE_S)
    for k in list(_TRAILS):
        v = _TRAILS[k] * factor
        if v < 0.05:
            del _TRAILS[k]
        else:
            _TRAILS[k] = v
    _LAST_EVAP[0] = now


def _maybe_resync(now: float) -> None:
    """Keep the read cache in step with the SHARED store: if another worker has written since we last
    looked, re-read it, evaporate to now, and re-apply our own not-yet-flushed pending on top. Bounded
    to at most once per _RESYNC_MIN_S so reads stay cheap. Read-only — no lock, no write."""
    if now - _LAST_SYNC[0] < _RESYNC_MIN_S:
        return
    _LAST_SYNC[0] = now
    try:
        mt = _path().stat().st_mtime
    except OSError:
        return
    if mt <= _LOADED_MTIME[0]:
        return                                  # no other worker has written; our cache is current
    trails, last_evap = _read_disk()
    merged = _evap_map(trails, last_evap, now)
    for k, dv in _PENDING.items():              # our own deposits not yet on disk stay visible locally
        merged[k] = min(merged.get(k, 0.0) + dv, 1e6)
    _TRAILS.clear()
    _TRAILS.update(merged)
    _LAST_EVAP[0] = now
    _LOADED_MTIME[0] = mt


def deposit(card_ids: Iterable[str], amount: float = 1.0) -> None:
    """A retrieval deposits pheromone on each card it returned — aggregate, no identity, no query. The
    deposit is recorded as a PENDING delta (merged onto the shared trail at flush), and mirrored into the
    local cache so this process sees its own trail immediately."""
    if not enabled():
        return
    _load()
    for cid in card_ids:
        if cid:
            k = str(cid)
            _PENDING[k] = _PENDING.get(k, 0.0) + amount
            _TRAILS[k] = min(_TRAILS.get(k, 0.0) + amount, 1e6)
    _DIRTY[0] += 1
    if _DIRTY[0] >= _FLUSH_EVERY:
        flush()


def _acquire_lock(lockpath: Path) -> bool:
    """A portable cross-process lock: whoever creates the lock file (O_EXCL) holds it. A lock older than
    _LOCK_STALE_S is presumed left by a dead worker and stolen, so a crash can never deadlock the trail.
    Returns False if it cannot be had within the timeout — the caller keeps its pending and retries."""
    start = time.time()
    while True:
        try:
            fd = os.open(str(lockpath), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode())
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(str(lockpath)) > _LOCK_STALE_S:
                    try:
                        os.unlink(str(lockpath))
                    except OSError:
                        pass
                    continue
            except OSError:
                continue
            if time.time() - start > _LOCK_TIMEOUT_S:
                return False
            time.sleep(0.02)
        except OSError:
            return False


def _release_lock(lockpath: Path) -> None:
    try:
        os.unlink(str(lockpath))
    except OSError:
        pass


def flush() -> None:
    """Merge this process's pending deltas onto the SHARED store under a lock — never clobber another
    worker's deposits. Read disk, evaporate to now, add our deltas, bound, write atomically."""
    if not enabled():
        return
    if not _PENDING and _DIRTY[0] == 0:
        return
    lock = _lockpath()
    if not _acquire_lock(lock):
        return                                  # keep pending; a later deposit will retry the flush
    try:
        now = time.time()
        trails, last_evap = _read_disk()
        merged = _evap_map(trails, last_evap, now)
        for k, dv in _PENDING.items():
            merged[k] = min(merged.get(k, 0.0) + dv, 1e6)
        if len(merged) > _MAX:                  # bounded: keep the strongest trails only
            merged = dict(sorted(merged.items(), key=lambda x: -x[1])[:_MAX])
        p = _path()
        tmp = p.parent / f"{p.stem}.{os.getpid()}.tmp"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({"trails": merged, "last_evap": now}), encoding="utf-8")
        tmp.replace(p)
        _TRAILS.clear()
        _TRAILS.update(merged)
        _LAST_EVAP[0] = now
        _LAST_SYNC[0] = now
        _PENDING.clear()
        _DIRTY[0] = 0
        try:
            _LOADED_MTIME[0] = p.stat().st_mtime
        except OSError:
            pass
    except Exception:  # noqa: BLE001 — a failed flush never breaks a search; pending is kept
        pass
    finally:
        _release_lock(lock)


def strength(card_id: str) -> float:
    if not enabled():
        return 0.0
    _load()
    now = time.time()
    _maybe_resync(now)
    _evaporate(now)
    return _TRAILS.get(str(card_id), 0.0)


def boost_factor(card_id: str) -> float:
    """A multiplier in [1.0, _CAP] for the ranker's `_finalize` — reorders WITHIN a tier only. Exactly
    1.0 when disabled or when the card has no trail, so an unopted node ranks byte-for-byte as before."""
    if not enabled():
        return 1.0
    s = strength(card_id)
    if s <= 0:
        return 1.0
    return min(_CAP, 1.0 + _W * math.log1p(s))


def top(n: int = 20) -> List[Dict[str, float]]:
    """The strongest trails — the paths the keeping has worn smooth. Read-only, for a health view."""
    if not enabled():
        return []
    _load()
    now = time.time()
    _maybe_resync(now)
    _evaporate(now)
    return [{"card_id": k, "strength": round(v, 3)}
            for k, v in sorted(_TRAILS.items(), key=lambda x: -x[1])[:max(1, int(n))]]
