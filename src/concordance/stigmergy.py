"""STIGMERGY — the keeping's pheromone layer (Ant Colony Optimization, applied to recall).

Ants coordinate with no central plan by leaving pheromone in the shared environment: trails that prove
useful strengthen (deposit), unused ones fade (evaporation), and the colony self-organizes onto the
good paths. The keeping is our shared environment; this makes the CARDS the trails. A card retrieved in
a result deposits a little pheromone; all trails evaporate over time; a small, capped ranking boost
lets a well-travelled card lead WITHIN the tier it already earned (never smuggling an off-subject hit
up — same discipline as the other _finalize boosts).

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
from typing import Dict, Iterable, List

_RHO = 0.5              # evaporation: a trail halves every half-life if not refreshed
_HALFLIFE_S = 30 * 86400
_W = 0.15               # boost weight
_CAP = 1.6              # a trail can lift a card at most 1.6x WITHIN its tier — never across tiers
_MAX = 4000             # keep only the strongest N trails resident/persisted (bounded)
_FLUSH_EVERY = 25       # throttle disk writes: flush after this many deposits
_EVAP_MIN_S = 3600      # evaporate at most hourly (lazy)

_TRAILS: Dict[str, float] = {}
_LAST_EVAP = [0.0]
_LOADED = [False]
_DIRTY = [0]


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_STIGMERGY", "").strip().lower() in ("1", "true", "yes", "on")


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "stigmergy.json"


def _load() -> None:
    if _LOADED[0]:
        return
    _LOADED[0] = True
    p = _path()
    try:
        if p.is_file():
            d = json.loads(p.read_text(encoding="utf-8"))
            _TRAILS.update({str(k): float(v) for k, v in (d.get("trails") or {}).items()})
            _LAST_EVAP[0] = float(d.get("last_evap") or time.time())
            return
    except Exception:  # noqa: BLE001 — a bad store is not a crash; start fresh
        _TRAILS.clear()
    _LAST_EVAP[0] = time.time()


def _evaporate(now: float | None = None) -> None:
    now = now or time.time()
    dt = now - _LAST_EVAP[0]
    if dt < _EVAP_MIN_S:
        return
    factor = _RHO ** (dt / _HALFLIFE_S)
    for k in list(_TRAILS):
        v = _TRAILS[k] * factor
        if v < 0.05:
            del _TRAILS[k]          # a faded trail is forgotten — the keeping does not hoard dead paths
        else:
            _TRAILS[k] = v
    _LAST_EVAP[0] = now


def deposit(card_ids: Iterable[str], amount: float = 1.0) -> None:
    """A retrieval deposits pheromone on each card it returned — aggregate, no identity, no query."""
    if not enabled():
        return
    _load()
    _evaporate()
    for cid in card_ids:
        if cid:
            _TRAILS[str(cid)] = min(_TRAILS.get(str(cid), 0.0) + amount, 1e6)
    _DIRTY[0] += 1
    if _DIRTY[0] >= _FLUSH_EVERY:
        flush()


def flush() -> None:
    if not enabled():
        return
    if len(_TRAILS) > _MAX:                       # bounded: keep the strongest trails only
        for k, _v in sorted(_TRAILS.items(), key=lambda x: -x[1])[_MAX:]:
            _TRAILS.pop(k, None)
    try:
        p = _path()
        tmp = p.with_suffix(".json.tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({"trails": _TRAILS, "last_evap": _LAST_EVAP[0]}), encoding="utf-8")
        tmp.replace(p)
        _DIRTY[0] = 0
    except Exception:  # noqa: BLE001 — a failed flush never breaks a search
        pass


def strength(card_id: str) -> float:
    if not enabled():
        return 0.0
    _load()
    _evaporate()
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
    _evaporate()
    return [{"card_id": k, "strength": round(v, 3)}
            for k, v in sorted(_TRAILS.items(), key=lambda x: -x[1])[:max(1, int(n))]]
