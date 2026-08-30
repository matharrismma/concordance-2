"""OT prophecy -> NT fulfillment — the NT-explicit map, verified and sourced (Matt, 2026-08-30: "run
all prophecies in the Old Testament, find how they are met in the New Testament").

CONDUIT, NOT INTERPRETER. Every pair here is one the NEW TESTAMENT ITSELF names as fulfilled ("that it
might be fulfilled…", or a direct quotation); the interpretive link is Scripture's own witness, carried
in `source`, never asserted by us. Both verses are public-domain WEB text, and the build tool
(tools/build_prophecy_fulfillments.py) OMITTED, never guessed, any pair whose references did not
resolve. Verdict is CONCORDANT — a signpost the New Testament affirms, NEVER "HOLDS": fulfillment is
not a deterministic proof, and the destination is Jesus Christ, not this map.

Kept separate from the cross-cultural signposts (prophecy.py) — a different concept. Read-only, stdlib.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

NOTE = ("The New Testament itself names each fulfillment; the pairing is Scripture's own witness, not "
        "ours. Verdict CONCORDANT, never HOLDS — a signpost to Jesus Christ, not a proof. Read the "
        "verses and discern.")


def _file() -> Path:
    env = os.environ.get("CONCORDANCE_PROPHECY_MESSIANIC", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "prophecy" / "messianic.jsonl"


_CACHE: Optional[List[Dict[str, Any]]] = None


def _load() -> List[Dict[str, Any]]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    rows: List[Dict[str, Any]] = []
    try:
        p = _file()
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        rows = []
    _CACHE = rows
    return rows


def available() -> bool:
    return bool(_load())


def _brief(r: Dict[str, Any]) -> Dict[str, Any]:
    # Carries the verse TEXT (both sides), so a caller can render OT | NT together in one request —
    # the verses ARE the witness; a bare ref would make the reader take the pairing on our say-so.
    return {"id": r.get("id"), "title": r.get("title"), "theme": r.get("theme"),
            "ot": r.get("ot"),                                   # {ref, text}
            "nt_fulfillments": r.get("nt_fulfillments") or [],   # [{ref, text}, ...]
            "ot_ref": (r.get("ot") or {}).get("ref"),
            "nt_refs": [f.get("ref") for f in (r.get("nt_fulfillments") or [])],
            "source": r.get("source"), "verdict": r.get("verdict")}


def list_all() -> Dict[str, Any]:
    """The whole map, grouped by theme (birth, ministry, passion, resurrection, apostles, epistles)."""
    rows = _load()
    themes: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        themes.setdefault(r.get("theme") or "other", []).append(_brief(r))
    return {"count": len(rows), "note": NOTE, "conduit": True, "generated": False,
            "themes": themes}


def get(fid: str) -> Optional[Dict[str, Any]]:
    """One fulfillment, whole: both verses' text, the NT's citation, the verdict + the standing note."""
    for r in _load():
        if r.get("id") == fid:
            out = dict(r)
            out["note"] = r.get("note") or NOTE
            return out
    return None


def _bc(ref: str) -> str:
    """A reference's book+chapter, lowercased, Psalms->Psalm: 'Isaiah 53:7' -> 'isaiah 53'. So a reader
    on a whole chapter, or on one verse of it, finds the fulfillments that touch that chapter."""
    s = " ".join((ref or "").lower().replace("psalms", "psalm").split())
    return s.rsplit(":", 1)[0] if ":" in s else s


def for_ref(ref: str) -> Dict[str, Any]:
    """Every fulfillment touching a verse or chapter — matched book+chapter against the OT ref and each
    NT ref. The shape the VISION_PLAN names (/prophecy?ref=): stand on Isaiah 53 and see what the NT
    takes up from it."""
    key = _bc(ref)
    out: List[Dict[str, Any]] = []
    if key:
        for r in _load():
            refs = [(r.get("ot") or {}).get("ref", "")] + \
                   [f.get("ref", "") for f in (r.get("nt_fulfillments") or [])]
            if any(_bc(x) == key for x in refs):
                out.append(_brief(r))
    return {"ref": ref, "count": len(out), "matches": out, "note": NOTE, "conduit": True}


__all__ = ["available", "list_all", "get", "for_ref", "NOTE"]
