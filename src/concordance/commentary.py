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
    # D5 (Matt, 2026-07-28): the registry widens — Clarke and Gill, same road as Henry.
    "adam-clarke": {
        "name": "Adam Clarke's Commentary on the Bible",
        "author": "Adam Clarke (1762–1832)",
        "license": "Public Domain",
        "via": "bible.helloao.org",
    },
    "john-gill": {
        "name": "John Gill's Exposition of the Old and New Testaments",
        "author": "John Gill (1697–1771)",
        "license": "Public Domain",
        "via": "bible.helloao.org",
    },
}
DEFAULT_SOURCE = "matthew-henry"

# The Catena Aurea (run 2026-11-11-fathers-shelf): the Fathers and later writers that Thomas Aquinas gathered on the
# four Gospels, in the English edition of 1841-45, as tools/build_catena.py builds them on the box from two scanned
# copies of that printing. It is read ONLY from the pinned build (src/concordance/builds.py); no build is "not built".
CATENA = "catena-aurea"
SOURCE_META[CATENA] = {
    "name": ("Catena Aurea: Commentary on the Four Gospels, collected out of the works of the Fathers by S. Thomas "
             "Aquinas (Oxford: John Henry Parker, 1841-45)"),
    "author": ("The Fathers and later writers that Thomas Aquinas gathered, each named as the edition prints him; "
               "translated for the edition, St. Mark by John Dobree Dalgairns and St. Luke by Thomas Dudley Ryder, as "
               "those volumes' prefaces name them"),
    "license": "Public Domain (printed 1841-45)",
    "via": "archive.org scans of the 1841-45 printing, each excerpt read alike in two copies",
}
_CATENA_NOTE = ("The Fathers' and later writers' own words as the English edition of 1841-45 prints them: found in "
                "two scanned copies that read alike, attributed as printed, never generated. Each excerpt names its "
                "writer as printed; a later writer is labelled so.")

_REF_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z. ]+?)\s+(\d+)(?::(\d+))?\s*$")

# source reaches _books_index()/_load_chapter() straight from api.py's GET /commentary?source=
# query param, unauthenticated and unvalidated, and was used to build _dir()/source/... — a
# caller could read files outside the commentary directory (e.g. source="../other_place").
# Every real source directory name matches this shape (SOURCE_META's own keys do too).
_SOURCE_RE = re.compile(r"[a-z0-9_\-]{1,64}\Z")


def _valid_source(source: Any) -> bool:
    return isinstance(source, str) and bool(_SOURCE_RE.match(source))


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
    if not _valid_source(source):
        return []
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
    if not _valid_source(source):
        return None
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
    if source == CATENA:
        return _catena_for_ref(ref)
    meta = SOURCE_META.get(source, {"name": source})
    base = {"ref": ref, "source": source, "attribution": meta.get("name"),
            "author": meta.get("author"), "license": meta.get("license"), "via": meta.get("via"),
            "note": "The commentator's own public-domain words — found and attributed, never generated."}
    # found: "ref or ''" only substitutes the fallback for a FALSY ref — a truthy non-string
    # (an int from an uncoerced MCP tool call arg) survives past that guard and crashes
    # re.match() ("expected string or bytes-like object"). Matches corpus.search()'s fix.
    m = _REF_RE.match(str(ref) if ref else "")
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


# ── the Catena Aurea, from its pinned build ─────────────────────────────────────────────────────────

_KIND_LABEL = {"later_writer": "a later writer", "father": "a Father", "father_age_writer": "a writer of the age of the Fathers",
               "pseudo": "a work under a Father's name", "council": "a council", "anonymous": "an unnamed writer",
               "jewish_historian": "a Jewish historian", "idem": "the same writer as the excerpt before",
               "unresolved": "named as printed"}


def _catena_dir() -> Optional[Path]:
    from . import builds
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or None
    return builds.built_dir(CATENA, data)


def _catena_json(root: Path, rel: str) -> Optional[Any]:
    p = root.joinpath(*rel.split("/"))
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _catena_item(block: Dict[str, Any], exc: Dict[str, Any], who: Dict[str, Any]) -> Dict[str, Any]:
    a = who.get(exc.get("author_key"), {})
    return {"verse": block.get("verse"), "range": block.get("range"), "text": exc.get("text"),
            "author_as_printed": exc.get("author_as_printed"), "author": a.get("identified_as"),
            "writer": _KIND_LABEL.get(a.get("kind"), "named as printed"), "citation": exc.get("citation"),
            "page": exc.get("page"), **({"editors_mark": exc["editors_mark"]} if exc.get("editors_mark") else {})}


def _catena_for_ref(ref: str) -> Dict[str, Any]:
    meta = SOURCE_META[CATENA]
    base = {"ref": ref, "source": CATENA, "attribution": meta["name"], "author": meta["author"],
            "license": meta["license"], "via": meta["via"], "note": _CATENA_NOTE}
    m = _REF_RE.match(str(ref) if ref else "")
    if not m:
        return {**base, "status": "not_found", "detail": "could not parse reference", "commentary": []}
    root = _catena_dir()
    if root is None:
        return {**base, "status": "not_built", "detail": "the Catena Aurea build is not on this machine",
                "commentary": []}
    book_raw, chapter = m.group(1), int(m.group(2))
    verse = int(m.group(3)) if m.group(3) else None
    key = re.sub(r"[^a-z0-9]", "", book_raw.lower())
    books = _catena_json(root, "_books.json") or []
    code = None
    for b in books:
        names = {re.sub(r"[^a-z0-9]", "", str(b.get(k) or "").lower()) for k in ("name", "commonName")}
        if key in names or key.rstrip("s") in names:
            code = b.get("code")
    if code is None:
        try:
            from .verifiers.scripture import default_bible
            canon = default_bible().alias.get(key)
            for b in books:
                if canon and re.sub(r"[^a-z0-9]", "", canon.lower()) == re.sub(r"[^a-z0-9]", "", str(b.get("name")).lower()):
                    code = b.get("code")
        except Exception:  # noqa: BLE001
            pass
    if code is None:
        return {**base, "status": "none", "detail": f"the Catena Aurea is on the four Gospels; not {book_raw!r}",
                "commentary": []}
    ch = _catena_json(root, f"{code}/{chapter}.json")
    who = _catena_json(root, "_authors.json") or {}
    blocks = (ch or {}).get("blocks") or []
    if verse is not None:
        items = [_catena_item(b, e, who) for b in blocks
                 if (b.get("covers_in_this_chapter") or [0, -1])[0] <= verse <= (b.get("covers_in_this_chapter") or [0, -1])[1]
                 for e in (b.get("excerpts") or [])]
    else:
        items = [_catena_item(b, e, who) for b in blocks for e in (b.get("excerpts") or [])]
    if not items:
        where = f"{book_raw} {chapter}" + (f":{verse}" if verse is not None else "")
        return {**base, "status": "none", "chapter": chapter, "verse": verse,
                "detail": f"no Catena excerpt served for {where}: none reaches it, or none was read alike in both copies",
                "commentary": []}
    return {**base, "status": "ok", "chapter": chapter, "verse": verse, "introduction": None, "commentary": items}


def sources_for(ref: str) -> Dict[str, Any]:
    """Which sources hold commentary on a reference: a separate answer (GET /commentary?sources=1), never a change to
    the default response."""
    out = []
    for slug, meta in SOURCE_META.items():
        r = for_ref(ref, source=slug)
        out.append({"source": slug, "name": meta.get("name"), "status": r.get("status"),
                    "covers": r.get("status") == "ok" and bool(r.get("commentary"))})
    return {"ref": ref, "sources": out, "covering": [o["source"] for o in out if o["covers"]]}


__all__ = ["parse_chapter", "for_ref", "sources", "sources_for", "SOURCE_META", "DEFAULT_SOURCE", "CATENA"]
