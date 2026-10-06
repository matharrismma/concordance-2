"""THE TRAJECTORY OF A PATH — measure what works, honestly, so the path narrows with use.

Matt, 2026-10-06: *"Success guides. We focus on what works. Success dictates future paths. Failure allows
us to better define parameters and the path narrows for future use."* And: *"We need a good method to
measure the trajectory of each path."*

A PATH is any named choice the engine can reuse — a tool, a technique, a strategy, a biblical type, or a
whole discerned route. Each USE of a path has an OUTCOME: success or failure. This measures the path's
trajectory from its outcomes, with real statistics, not a made-up score:

  * rate        — the raw success fraction s/n.
  * floor       — the WILSON score lower bound: a CONSERVATIVE success rate that accounts for how little
                  evidence there is. 3/3 scores lower than 30/30; success must be EARNED by repetition.
                  This is the honest "success dictates future paths" ranking value, and it RISES toward the
                  rate as n grows — the path narrows for future use.
  * width       — the Wilson interval width, which shrinks like 1/sqrt(n): literally how narrow the path is.
  * trend       — an EWMA of recent outcomes vs the overall rate: the DIRECTION (improving / steady /
                  declining) and the drift. The "is the group walking off the target" watch, per path.

The guard (so success cannot be self-graded): a SUCCESS is recorded only with a witness — a HOLDS seal in
this node's keeping, or a named external witness (the BROTHERS gate). A FAILURE is recorded freely; a miss
is cheap to keep and it is the thing that narrows the path. Found, never generated; outcomes ride the sync.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_Z = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.575829303548901}


def _path(data_dir: Optional[Path] = None) -> Path:
    d = Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
    return d / "path_outcomes.jsonl"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")[:80]


def wilson(s: int, n: int, confidence: float = 0.95):
    """The Wilson score interval (lower, centre, upper) for s successes in n trials. The lower bound is the
    conservative, evidence-weighted success rate; the width shrinks like 1/sqrt(n)."""
    if n <= 0:
        return 0.0, 0.0, 1.0
    z = _Z.get(round(confidence, 2), 1.959963984540054)
    p = s / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return max(0.0, centre - half), centre, min(1.0, centre + half)


def _events(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    p = _path(data_dir)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def record(path: str, success: bool, *, seal: str = "", witness: str = "", note: str = "",
           data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Record one outcome of a path. A SUCCESS needs a witness — a HOLDS seal in this keeping, or a named
    external witness — so success is never self-graded. A FAILURE is recorded freely (it narrows the path)."""
    pid = _slug(path)
    if not pid:
        return {"ok": False, "error": "a path name is required"}
    success = bool(success)
    seal = (seal or "").strip().lower()
    witness = (witness or "").strip()
    if success:
        sealed_ok = bool(re.fullmatch(r"[0-9a-f]{64}", seal))
        if sealed_ok:
            from . import tickstick
            if tickstick._seal_holds(seal, data_dir) is None:
                return {"ok": False, "error": f"seal {seal[:12]}… is not a HOLDS verification in this keeping"}
        if not sealed_ok and len(witness) < 3:
            return {"ok": False, "error": "a SUCCESS needs a witness: a 64-hex HOLDS seal, or a named "
                                          "external witness — success is never self-graded"}
    ev = {"event": "outcome", "path": pid, "success": success, "seal": seal, "witness": witness[:120],
          "note": (note or "")[:300], "at": int(time.time())}
    p = _path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return {"ok": True, "path": pid, "recorded": {"success": success}, "trajectory": measure(pid, data_dir=data_dir)}


def measure(path: str, *, confidence: float = 0.95, alpha: float = 0.3,
            data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The trajectory of one path: the conservative success floor (Wilson), how narrow it is (interval
    width), and the trend (EWMA of recent outcomes vs the overall rate — the direction it is heading)."""
    pid = _slug(path)
    evs = [e for e in _events(data_dir) if e.get("event") == "outcome" and e.get("path") == pid]
    evs.sort(key=lambda e: e.get("at", 0))
    n = len(evs)
    if n == 0:
        return {"path": pid, "n": 0, "detail": "no outcomes recorded for this path yet"}
    outcomes = [1 if e.get("success") else 0 for e in evs]
    s = sum(outcomes)
    rate = s / n
    lb, centre, ub = wilson(s, n, confidence)
    # EWMA of outcomes (recent-weighted) — the current direction of travel
    ewma = outcomes[0]
    for x in outcomes[1:]:
        ewma = alpha * x + (1 - alpha) * ewma
    drift = ewma - rate
    direction = "improving" if drift > 0.05 else ("declining" if drift < -0.05 else "steady")
    verdict = ("proven" if (lb >= 0.70 and n >= 5) else
               "failing" if (rate < 0.5 or (direction == "declining" and n >= 5)) else
               "promising" if rate >= 0.6 else "provisional")
    return {"path": pid, "n": n, "successes": s, "failures": n - s,
            "rate": round(rate, 4), "floor": round(lb, 4), "ceiling": round(ub, 4),
            "width": round(ub - lb, 4), "ewma": round(ewma, 4), "drift": round(drift, 4),
            "direction": direction, "verdict": verdict, "confidence": confidence,
            "means": ("floor is the Wilson lower bound (success earned by evidence; rises toward the rate as "
                      "n grows); width shrinks like 1/sqrt(n) — the path narrowing; direction is the EWMA "
                      "trend. Success guides, failure narrows.")}


def rank(paths: List[str], *, data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Order paths by the conservative floor (success dictates the path, earned by evidence)."""
    rows = [measure(p, data_dir=data_dir) for p in paths]
    rows = [r for r in rows if r.get("n")]
    rows.sort(key=lambda r: (-r.get("floor", 0.0), -r.get("n", 0)))
    return rows
