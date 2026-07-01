"""Prophecy / signposts — pointers to Jesus Christ, curated and attributed, never a proof.

A trace links a prophecy or cross-cultural fragment to its fulfillment in Christ, as recorded in an
ATTRIBUTED source (Plato's Republic, the Shatapatha Brahmana, the Great Isaiah Scroll, etc.). The
verdict is CONCORDANT or MIXED — a SIGNPOST, NEVER HOLDS: fulfillment is not a deterministic proof,
so nothing here is sealed as math. Found + cited, never generated (these are the operator's curated
signposts, ported from 1.0; each names its own sources). The destination is always Jesus Christ —
the engine points, it does not manufacture the fulfillment (1 John 4:1-3 the discriminator).

Store (sovereign JSONL, gitignored; ported by tools/migrate_prophecy.py from the 1.0 almanac):
    data/prophecy/signposts.jsonl   # {id, title, verdict, verification, wisdom, triggers, ...}
Env: CONCORDANCE_PROPHECY_DIR / CONCORDANCE_DATA_DIR.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

NOTE = ("A signpost, not a proof. Verdict CONCORDANT/MIXED, never HOLDS — fulfillment is not a "
        "deterministic seal. Found + attributed; the destination is Jesus Christ.")

_VERSE_RE = re.compile(r"\b([1-3]?\s?[A-Z][a-zA-Z]+\.?\s+\d{1,3}:\d{1,3}(?:-\d{1,3})?)\b")

_INDEX: List[Dict[str, Any]] = []
_MTIME: float = 0.0


def _file() -> Path:
    env = os.environ.get("CONCORDANCE_PROPHECY_DIR", "").strip()
    if env:
        return Path(env) / "signposts.jsonl"
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "prophecy" / "signposts.jsonl"


def _load() -> List[Dict[str, Any]]:
    global _INDEX, _MTIME
    p = _file()
    if not p.exists():
        return []
    mtime = p.stat().st_mtime
    if _INDEX and mtime == _MTIME:
        return _INDEX
    out: List[Dict[str, Any]] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return _INDEX
    _INDEX, _MTIME = out, mtime
    return out


def _keywords(rec: Dict[str, Any]) -> List[str]:
    """Keywords, tolerant of both schemas: triggers={keywords:[...]} or triggers=[...]."""
    t = rec.get("triggers")
    if isinstance(t, dict):
        kw = t.get("keywords", [])
        return kw if isinstance(kw, list) else []
    if isinstance(t, list):
        return t
    return []


def _refs(rec: Dict[str, Any]) -> List[str]:
    text = " ".join([rec.get("verification", ""), rec.get("wisdom", "")])
    seen, out = set(), []
    for m in _VERSE_RE.findall(text):
        r = re.sub(r"\s+", " ", m).strip()
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def list_traces() -> Dict[str, Any]:
    """Brief of every signpost trace — id, title, verdict."""
    items = [{"id": r.get("id"), "title": r.get("title"), "verdict": r.get("verdict"),
              "keywords": _keywords(r)}
             for r in _load()]
    return {"total": len(items), "note": NOTE, "traces": items}


def get(trace_id: str) -> Optional[Dict[str, Any]]:
    """One full trace: the evidence (verification), the pointing (wisdom), the verdict, the refs."""
    key = (trace_id or "").strip().lower()
    for r in _load():
        if str(r.get("id", "")).lower() == key:
            return {"id": r.get("id"), "title": r.get("title"), "verdict": r.get("verdict"),
                    "verification": r.get("verification", ""), "wisdom": r.get("wisdom", ""),
                    "scripture_refs": _refs(r),
                    "keywords": _keywords(r),
                    "domains": r.get("domains", []), "note": NOTE}
    return None


def search(q: str, limit: int = 20) -> Dict[str, Any]:
    """Find traces by keyword / title / text."""
    needle = (q or "").strip().lower()
    out = []
    for r in _load():
        hay = " ".join([r.get("title", ""), r.get("verification", ""), r.get("wisdom", ""),
                        " ".join(_keywords(r))]).lower()
        if not needle or needle in hay:
            out.append({"id": r.get("id"), "title": r.get("title"), "verdict": r.get("verdict")})
        if len(out) >= max(1, int(limit)):
            break
    return {"query": q, "total": len(out), "note": NOTE, "traces": out}


__all__ = ["list_traces", "get", "search", "NOTE"]
