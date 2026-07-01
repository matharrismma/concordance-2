"""Characters / Bible dictionary — people, places, and terms from Easton's Bible Dictionary (1897, PD).

Chart a figure: their summary + every verse that speaks of them — MECHANICAL and attributed (Easton's
own words + the neuu-org parse), found, never generated. The Bible is the focus; this restores some
of the "who and what" a native reader knew.

NOTE ON CATEGORY: the 1.0 parse's category tags are UNRELIABLE (e.g. Moses is tagged "concept",
Paul "place"), so lookup is category-AGNOSTIC — every figure resolves regardless of its (imperfect)
tag. The category is surfaced only as Easton's own label, not trusted for filtering.

Store (sovereign JSONL, gitignored; built by tools/migrate_characters.py from Easton's entries):
    data/characters/easton.jsonl   # {id, name, text, scripture_refs, category, source, ...}
Env: CONCORDANCE_CHARACTERS_DIR / CONCORDANCE_DATA_DIR.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import os

SOURCE = "Easton's Bible Dictionary (1897, public domain)"
LICENSE = "Public Domain (original text); CC-BY 4.0 (neuu-org parse)"
ATTRIBUTION = "Easton's Bible Dictionary (1897, PD); parse from neuu-org/bible-dictionary-dataset (CC BY 4.0)"

_INDEX: Dict[str, Dict[str, Any]] = {}
_NAME2SLUG: Dict[str, str] = {}
_MTIME: float = 0.0


def _file() -> Path:
    env = os.environ.get("CONCORDANCE_CHARACTERS_DIR", "").strip()
    if env:
        return Path(env) / "easton.jsonl"
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "characters" / "easton.jsonl"


def _slug_of(rec: Dict[str, Any]) -> str:
    rid = rec.get("id", "")
    for pre in ("easton_", "person_"):
        if rid.startswith(pre):
            return rid[len(pre):]
    return rid or re.sub(r"[^a-z0-9]+", "-", (rec.get("name") or "").lower()).strip("-")


def _index() -> Dict[str, Dict[str, Any]]:
    global _INDEX, _NAME2SLUG, _MTIME
    p = _file()
    if not p.exists():
        return {}
    mtime = p.stat().st_mtime
    if _INDEX and mtime == _MTIME:
        return _INDEX
    idx: Dict[str, Dict[str, Any]] = {}
    name2: Dict[str, str] = {}
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            slug = _slug_of(rec)
            if not slug:
                continue
            idx[slug] = rec
            nm = (rec.get("name") or "").strip().lower()
            if nm and nm not in name2:
                name2[nm] = slug
    except OSError:
        return _INDEX
    _INDEX, _NAME2SLUG, _MTIME = idx, name2, mtime
    return idx


def _summary(text: str, sentences: int = 2, cap: int = 400) -> str:
    parts = re.split(r"(?<=[.!?])\s", text or "")
    return " ".join(parts[:sentences])[:cap]


def get(name: str) -> Optional[Dict[str, Any]]:
    """Chart one character by name or slug — summary + every verse Easton cites for them."""
    idx = _index()
    key = (name or "").strip().lower()
    if not key:
        return None
    slug = key if key in idx else _NAME2SLUG.get(key)
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-")  # last try: slugify the input
    rec = idx.get(slug)
    if rec is None:
        return None
    refs = rec.get("scripture_refs") or []
    return {"slug": slug, "name": rec.get("name") or slug, "summary": _summary(rec.get("text") or ""),
            "text": rec.get("text") or "", "scripture_refs": refs, "ref_count": len(refs),
            "category": rec.get("category"),  # Easton's own (imperfect) label
            "source": SOURCE, "license": LICENSE, "attribution": ATTRIBUTION}


def browse(letter: Optional[str] = None, search: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """Index of characters — A-Z / substring; briefs for a scannable directory."""
    idx = _index()
    init = (letter or "").strip().upper()[:1]
    needle = (search or "").strip().lower()
    items: List[Dict[str, Any]] = []
    for slug, rec in sorted(idx.items(), key=lambda kv: (kv[1].get("name") or kv[0])):
        name = rec.get("name") or slug
        if init and not name.upper().startswith(init):
            continue
        if needle and needle not in name.lower() and needle not in (rec.get("text") or "").lower():
            continue
        items.append({"slug": slug, "name": name, "preview": _summary(rec.get("text") or "", 1, 200),
                      "ref_count": len(rec.get("scripture_refs") or [])})
        if len(items) >= max(1, int(limit)):
            break
    return {"total": len(items), "source": SOURCE, "items": items}


def count() -> int:
    return len(_index())


__all__ = ["get", "browse", "count", "SOURCE", "LICENSE", "ATTRIBUTION"]
