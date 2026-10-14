"""VOICE — Matt's own words, gathered as the house shepherd's voice (composition layer #4, 2026-10-14).

The engine finds and checks the CLAIMS; the connective tissue that meets a person and draws the thread
should sound like Matt shepherding. So it is composed from his OWN writing — a verbatim unit SELECTED to
fit the moment, never generated — and his ElevenLabs clone speaks it. This is the house tier of "the
voice"; the public-domain witness cloud (witness.py) stands beside it as the gathered wisdom of the past.
All verbatim, all attributed, all fit — the craft is choosing which of his words meets this burden.

Source: data/voice_lines.jsonl (built by tools/seed_voice.py from his Christian writing). His personal
content — box-side data like witnesses.jsonl, never committed, never treated as public-domain.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

_STOP = frozenset((
    "the a an of to and but in on for is are was were be am his her my your their our its it he she they "
    "we you i do does did not no as at by or if with from about into over under out up down this that these "
    "those his who what when where why how so all any can could would should will me us him them not").split())

_CACHE: Dict[str, Any] = {"rows": None, "mtime": 0.0}
_REFKEY = re.compile(r"^\s*(\d?\s?[A-Za-z][A-Za-z ]*?)\s+(\d+)\s*:")


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "voice_lines.jsonl"


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in _STOP}


def _ref_key(ref: str) -> str:
    """'Matthew 6:25-34' -> 'matthew 6' — the book+chapter, so a shared Scripture theme reads as fit."""
    m = _REFKEY.match(ref or "")
    return (m.group(1).strip().lower() + " " + m.group(2)) if m else ""


def _rows() -> List[Dict[str, Any]]:
    p = _path()
    try:
        mt = p.stat().st_mtime
    except OSError:
        return []
    if _CACHE["rows"] is not None and _CACHE["mtime"] == mt:
        return _CACHE["rows"]
    rows: List[Dict[str, Any]] = []
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if str(r.get("text") or "").strip():
                    rows.append(r)
    except Exception:  # noqa: BLE001 — no corpus is an honest silence, never a crash
        rows = []
    _CACHE["rows"], _CACHE["mtime"] = rows, mt
    return rows


def see(text: str, *, ref: str = "", k: int = 1) -> Dict[str, Any]:
    """Matt's own words that most fit this moment — his verbatim unit, attributed, or honestly empty where
    his writing does not reach it. `ref` is the anchor the Word landed on; a unit that sits on the same
    Scripture (book+chapter) is a strong fit. Ranked by shared subject words; a candidate must share the
    theme (>=2), so a stray word cannot pull an off-key reflection. Proposes; never confirms."""
    q = _tokens(text) | _tokens(ref)
    anchor = _ref_key(ref)
    rows = _rows()
    scored = []
    for i, r in enumerate(rows):
        ut = _tokens((r.get("text") or "") + " " + (r.get("ref") or ""))
        overlap = len(q & ut)
        if anchor and _ref_key(r.get("ref") or "") == anchor:   # same Scripture theme — a strong fit
            overlap += 3
        if overlap >= 2:
            scored.append((overlap, -i, r))
    scored.sort(key=lambda x: (-x[0], x[1]))
    seeing = [{"text": r.get("text"), "source": r.get("source"), "ref": r.get("ref"), "by": r.get("by")}
              for _o, _i, r in scored[:max(1, int(k))]]
    return {"seeing": seeing, "gathered": len(rows), "proposes": True, "confirms": False,
            "note": ("his own words, fit to this and spoken in his voice" if seeing else
                     "his writing does not reach this one yet")}
