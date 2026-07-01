"""Commentary — public-domain, attributed exposition on a reference (the father's OWN words).

Serves real public-domain commentary (Matthew Henry) FOUND, never generated — the bumblebee
discipline: play the father's own recorded words, attributed, and never speak our own opinion as
his. The Bible is the focus; this restores some of the inherent context a modern reader lacks.
Cite-fair: attribution + license travel with every response.

Store (sovereign JSON, gitignored; built by tools/migrate_commentary.py from bible.helloao.org):
    data/commentary/<source>/_books.json            # [{code,name,commonName,chapters}]
    data/commentary/<source>/<CODE>/<chapter>.json  # {introduction, blocks:[{verse,text}], ...}
Environment: CONCORDANCE_COMMENTARY_DIR / CONCORDANCE_DATA_DIR.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SOURCE_META: Dict[str, Dict[str, str]] = {
    "matthew-henry": {
        "name": "Matthew Henry's Commentary (An Exposition of the Old and New Testaments)",
        "author": "Matthew Henry (1662–1714)",
        "license": "Public Domain (Public Domain Mark 1.0)",
        "via": "bible.helloao.org",
    },
}
DEFAULT_SOURCE = "matthew-henry"

_REF_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z. ]+?)\s+(\d+)(?::(\d+))?\s*$")


def _dir() -> Path:
    env = os.environ.get("CONCORDANCE_COMMENTARY_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "commentary"


def parse_chapter(chapter_json: Dict[str, Any]) -> Dict[str, Any]:
    """Extract {introduction, blocks:[{verse,text}]} from a helloao chapter object. Pure — used by
    the migrator and unit-testable without the network."""
    intro = (chapter_json.get("introduction") or "").strip()
    blocks: List[Dict[str, Any]] = []
    for item in (chapter_json.get("content") or []):
        if not isinstance(item, dict) or item.get("type") != "verse":
            continue
        parts = item.get("content") or []
        text = "\n\n".join(str(p) for p in parts if isinstance(p, str) and p.strip()).strip()
        if text:
            blocks.append({"verse": item.get("number"), "text": text})
    return {"introduction": intro, "blocks": blocks}


def _books_index(source: str) -> List[Dict[str, Any]]:
    p = _dir() / source / "_books.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _name_to_code(source: str) -> Dict[str, str]:
    idx: Dict[str, str] = {}
    for b in _books_index(source):
        code = b.get("code")
        for nm in (b.get("name"), b.get("commonName")):
            if nm and code:
                idx[re.sub(r"[^a-z0-9]", "", nm.lower())] = code
    return idx


def _resolve_code(source: str, book_raw: str) -> Optional[str]:
    """Resolve a book name/abbreviation to this source's book code, robustly: exact match, then a
    singular/plural nudge (Psalm↔Psalms), then Scripture's own alias map (Jn→John) when data is present."""
    idx = _name_to_code(source)
    key = re.sub(r"[^a-z0-9]", "", (book_raw or "").lower())
    if not key:
        return None
    if key in idx:
        return idx[key]
    for alt in (key + "s", key.rstrip("s")):   # Psalm -> Psalms, etc.
        if alt in idx:
            return idx[alt]
    try:  # reuse the verifier's alias table (handles jn, ps, 1co, ...) when the Bible is provisioned
        from .verifiers.scripture import default_bible
        canon = default_bible().alias.get(key)
        if canon:
            return idx.get(re.sub(r"[^a-z0-9]", "", canon.lower()))
    except Exception:  # noqa: BLE001
        pass
    return None


def _load_chapter(source: str, code: str, chapter: int) -> Optional[Dict[str, Any]]:
    p = _dir() / source / code / f"{chapter}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def sources() -> List[str]:
    base = _dir()
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())


def for_ref(ref: str, source: str = DEFAULT_SOURCE) -> Dict[str, Any]:
    """Commentary on a reference. With a verse, return the block covering it; otherwise the whole
    chapter's blocks + introduction. Attributed + licensed; found, never generated."""
    meta = SOURCE_META.get(source, {"name": source})
    base = {"ref": ref, "source": source, "attribution": meta.get("name"),
            "author": meta.get("author"), "license": meta.get("license"), "via": meta.get("via"),
            "note": "The commentator's own public-domain words — found and attributed, never generated."}
    m = _REF_RE.match(ref or "")
    if not m:
        return {**base, "status": "not_found", "detail": "could not parse reference", "commentary": []}
    book_raw, chapter = m.group(1), int(m.group(2))
    verse = int(m.group(3)) if m.group(3) else None
    code = _resolve_code(source, book_raw)
    if not code:
        return {**base, "status": "no_source",
                "detail": f"no {meta.get('name', source)} available for {book_raw!r} yet (not migrated)",
                "commentary": []}
    ch = _load_chapter(source, code, chapter)
    if ch is None:
        return {**base, "status": "no_source",
                "detail": f"{book_raw} {chapter} not migrated for this source yet", "commentary": []}
    blocks = ch.get("blocks") or []
    if verse is not None and blocks:
        covering = None
        for b in blocks:
            bv = b.get("verse")
            if isinstance(bv, int) and bv <= verse:
                covering = b
            elif isinstance(bv, int) and bv > verse:
                break
        chosen = [covering] if covering else [blocks[0]]
        return {**base, "status": "ok", "chapter": chapter, "verse": verse,
                "introduction": None, "commentary": chosen}
    return {**base, "status": "ok", "chapter": chapter,
            "introduction": ch.get("introduction") or None, "commentary": blocks}


__all__ = ["parse_chapter", "for_ref", "sources", "SOURCE_META", "DEFAULT_SOURCE"]
