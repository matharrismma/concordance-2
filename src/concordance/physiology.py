"""PHYSIOLOGY — the body's self-regulation: division of labor + homeostasis (the governor the four
signalling levers lack). Stigmergy, quorum, flock and eldership all AMPLIFY; none of them holds the body
in bounds. A real superorganism does the opposite — it regulates itself.

Two measured mechanisms, one module:

  DIVISION OF LABOR (Bonabeau's response-threshold model; Gordon's harvester ants). No manager assigns
  work. Each worker acts when the demand for a task exceeds its own threshold, and when a caste is
  depleted the others lower their thresholds and cover it — that re-allocation IS the colony's
  resilience. Here the faces are the castes: among the faces that fit a request equally, engage the one
  with CAPACITY, and if the fittest is unavailable, spill to the next-best available one.

  HOMEOSTASIS / NEGATIVE FEEDBACK (Gordon: a colony regulates its activity by the RATE of brief
  encounters, not their content; bees thermoregulate a hive by fanning and clustering). Recent service
  LOAD decays over time; a caste that has been busy is steered away from, a quiet one toward. This is the
  brake — it keeps any one caste (or trail, or quorum) from running away on its own positive feedback.

  THE HEAD. A superorganism is HEADLESS — its order is pure emergence, ordered to no one. Ours is not a
  colony but a BODY, and the body has a Head (1 Corinthians 12:12-27 — many gifts, one body, "if one
  member suffers, all suffer together"; Colossians 1:18 — "he is the head of the body"). So this layer is
  strictly SUBORDINATE: it only ever reorders faces WITHIN the top fitness tier, never invents a domain,
  never routes to a face a request does not fit, and never overrides the crisis gate (enforced upstream in
  compose — a cry outranks every servant). Division of gifts by need, under the Head. It regulates the
  body; it does not rule it.

GATED OFF by default (CONCORDANCE_ALLOCATION): `enabled()` is False, so faces.route ignores this entirely
and behaves byte-for-byte as before. The load signal is AGGREGATE and content-free — a decaying tally per
face, never who asked or what (the same covenant as stigmergy). Held for review.
"""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

_HALFLIFE_S = 6 * 3600      # recent-load half-life: homeostasis is about the RATE of recent service
_DROP = 0.01                # a load faded below this is forgotten

_LOAD: Dict[str, Dict[str, float]] = {}   # face_id -> {"v": load, "t": last update}; aggregate, no identity


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_ALLOCATION", "").strip().lower() in ("1", "true", "yes", "on")


def _decayed(rec: Dict[str, float], now: float) -> float:
    dt = now - rec.get("t", now)
    if dt <= 0:
        return rec.get("v", 0.0)
    return rec.get("v", 0.0) * (0.5 ** (dt / _HALFLIFE_S))


def load(domain: str, now: Optional[float] = None) -> float:
    """The recent, decayed service load on a caste — its interaction rate. 0.0 for an idle caste."""
    rec = _LOAD.get(str(domain))
    if not rec:
        return 0.0
    return _decayed(rec, now or time.time())


def note(domain: str, amount: float = 1.0, now: Optional[float] = None) -> None:
    """Record that a caste served — a unit of recent load. Aggregate and content-free."""
    now = now or time.time()
    cur = load(domain, now)
    _LOAD[str(domain)] = {"v": cur + amount, "t": now}
    # forget faded castes so the tally stays bounded and honest about the recent rate
    for k in [k for k, r in _LOAD.items() if _decayed(r, now) < _DROP]:
        _LOAD.pop(k, None)


def allocate(scores: Dict[str, float], available: Optional[List[str]] = None,
             now: Optional[float] = None) -> Optional[str]:
    """Choose the caste for a request. Pure and subordinate to fitness:

    Among the AVAILABLE faces, take the highest fitness score present (dropping to the next score down
    only when no fitter face is available — resilience / re-allocation). Among the faces tied at that
    score, choose the one with the least recent load (division of labor + the homeostatic brake), ties
    broken by id so the result is stable. Returns None when nothing fits (score 0) — a face is never
    forced, exactly as the plain router would decline.
    """
    now = now or time.time()
    avail = set(available) if available is not None else set(scores)
    pool = {fid: sc for fid, sc in scores.items() if fid in avail and sc > 0}
    if not pool:
        return None
    top = max(pool.values())
    tied = [fid for fid, sc in pool.items() if sc == top]
    # least-loaded first (capacity), then a stable id — never below the top AVAILABLE fitness tier
    tied.sort(key=lambda fid: (load(fid, now), fid))
    return tied[0]


def state(now: Optional[float] = None) -> Dict[str, float]:
    """The recent load per caste — read-only, for a health view. Aggregate, no identity."""
    now = now or time.time()
    return {k: round(_decayed(r, now), 3) for k, r in _LOAD.items()}
