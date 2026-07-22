"""The Almanac — what the engine has WORKED THROUGH, re-sealed on 2.0.

Every entry was recovered from the 1.0 almanac and RE-VERIFIED through the live 2.0 engine.
The original 1.0 receipts were retired with the old seal ledger, so for each checkable claim the
engine minted a FRESH 2.0 seal. Verified-only: an entry appears here ONLY if it re-sealed with a
live receipt — nothing archived-pending, nothing asserted. The wisdom line is the human note; the
seal is the proof. Conduit, not author: the engine did not write these verdicts, it re-checked them.

Store: data/almanac/resealed.jsonl (same-shape records; env CONCORDANCE_ALMANAC_DIR / CONCORDANCE_DATA_DIR).
Record shape: {id, title, kind, situation, domains, category, wisdom, orig_verdict, packet, seal}.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

NOTE = ("Verified-only: every entry re-minted a LIVE 2.0 receipt. The 1.0 seals were retired with the "
        "old ledger; these are fresh re-checks. The wisdom is the human note; the seal is the proof. "
        "The Almanac keeps what survived re-verification — it does not panic.")

_ENTRIES: List[Dict[str, Any]] = []
_MTIME: float = 0.0


def _file() -> Path:
    env = os.environ.get("CONCORDANCE_ALMANAC_DIR", "").strip()
    if env:
        return Path(env) / "resealed.jsonl"
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "almanac" / "resealed.jsonl"


def _load() -> List[Dict[str, Any]]:
    global _ENTRIES, _MTIME
    p = _file()
    if not p.exists():
        return []
    mtime = p.stat().st_mtime
    if _ENTRIES and mtime == _MTIME:
        return _ENTRIES
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
        return _ENTRIES
    out.sort(key=lambda r: (r.get("title") or r.get("id") or "").lower())
    _ENTRIES, _MTIME = out, mtime
    return _ENTRIES


def _brief(r: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": r.get("id"), "title": r.get("title") or r.get("id"),
            "category": r.get("category") or "other", "domains": r.get("domains") or [],
            "verdict": "HOLDS", "seal": r.get("seal")}


def categories() -> List[Dict[str, Any]]:
    cc = Counter(str(r.get("category") or "other") for r in _load())
    return [{"category": k, "count": v} for k, v in sorted(cc.items())]


def list_entries(category: str = "", limit: int = 2000) -> Dict[str, Any]:
    """Brief of every re-sealed entry; optionally filtered by category."""
    c = (category or "").strip().lower()
    items = [_brief(r) for r in _load() if not c or c == str(r.get("category", "")).lower()]
    return {"total": len(items), "note": NOTE, "categories": categories(),
            "entries": items[: max(1, int(limit))]}


def get(entry_id: str) -> Optional[Dict[str, Any]]:
    """One full entry: the claim, the wisdom, the re-verification packet, and the live seal."""
    key = (entry_id or "").strip().lower()
    for r in _load():
        if str(r.get("id", "")).lower() == key:
            out = dict(r)
            out["verdict"] = "HOLDS"
            out["note"] = NOTE
            return out
    return None


def search(q: str, limit: int = 40) -> Dict[str, Any]:
    """Find entries by title / situation / wisdom / category / domain."""
    needle = (q or "").strip().lower()
    out: List[Dict[str, Any]] = []
    for r in _load():
        hay = " ".join(str(r.get(k) or "") for k in ("title", "situation", "wisdom", "category"))
        hay = (hay + " " + " ".join(r.get("domains") or [])).lower()
        if not needle or needle in hay:
            out.append(_brief(r))
        if len(out) >= max(1, int(limit)):
            break
    return {"query": q, "total": len(out), "note": NOTE, "entries": out}


__all__ = ["list_entries", "get", "search", "categories", "NOTE"]
