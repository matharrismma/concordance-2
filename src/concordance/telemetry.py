"""Sovereign activity log — so the operator can SEE the engine working.

Append-only JSONL beside the engine (gitignored). Best-effort: a logging failure NEVER
breaks a request. Privacy-preserving: strings are truncated, and only what's needed to
see activity is kept (action, surface, verdict, a short claim/query) — no secrets.
The keep dashboard reads this. Sovereign: stdlib only.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

_MAX_STR = 140


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "activity.jsonl"


def record(action: str, surface: str = "secular", **detail: Any) -> None:
    """Append one activity event. Best-effort — swallows all errors."""
    try:
        ev: Dict[str, Any] = {"t": int(time.time()), "action": action, "surface": surface}
        for k, v in detail.items():
            if isinstance(v, str) and len(v) > _MAX_STR:
                v = v[:_MAX_STR] + "…"
            ev[k] = v
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass  # the engine never fails because telemetry did


def recent(n: int = 50) -> List[Dict[str, Any]]:
    """The last n events (newest last). Empty if none."""
    p = _path()
    if not p.exists():
        return []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
        out = []
        for line in lines[-n:]:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out
    except OSError:
        return []


def stats(window: int = 2000) -> Dict[str, Any]:
    """Aggregate over the recent window: counts by action, by verdict, by surface."""
    evs = recent(window)
    return {
        "events": len(evs),
        "by_action": dict(Counter(e.get("action") for e in evs)),
        "by_verdict": dict(Counter(e.get("verdict") for e in evs if e.get("verdict"))),
        "by_surface": dict(Counter(e.get("surface") for e in evs)),
        "first_t": evs[0]["t"] if evs else None,
        "last_t": evs[-1]["t"] if evs else None,
    }
