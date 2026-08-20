"""Lens — Matt's writing as the way of seeing. The soul of discernment.

Matt, 2026-08-20: *"I had seen my writing as the lens."* The build plan named three layers — substrate,
wiring, and **lens** ("the way of seeing: what proposes what to check and how to read a claim"). `discern`
is the SHAPE of the lens (kind, necessity, route…); this is what it sees WITH: Matt's own writing, his
witness. A lens with no way of seeing is just a hole in the glass; his writing is the ground it is tuned
to.

THREE SENSES, ONE PRIMITIVE. His writing is the lens in three ways, and all three stand on `see()`:
  DISCERNMENT — his writing proposes what matters and how to read a claim.
  VOICE       — his own words frame the answer (never a generated imitation — his actual writing speaks).
  MAP         — his writing is the structure of how things connect and point to Christ.

`see(text)` proposes a way of seeing: the passages from Matt's writing that frame the input, with their
provenance. The laws it keeps, every one:
  * PROPOSES, NEVER CONFIRMS — the lens offers a way of seeing; the gate still disposes. Authority is
    never granted here.
  * NOTHING GENERATED — it retrieves his REAL words; it never writes in his voice. Gather, don't author.
  * ATTRIBUTED — every passage carries its work and reference; his witness is never anonymized into the
    engine's own voice.
  * HIS WITNESS ONLY — a DISTINCT layer, not the general keeping. The lens is his writing, not the world's.
  * NEVER TRUSTED ALONE — it points; it does not verify.

The lens corpus is PLUGGABLE, because the lens is living: it grows as we gather his writing (map as we
go) and as he writes more (circulation feeds the lens). Today a seed — an empty or small corpus — and
`see()` honestly proposes nothing where his writing is not yet gathered; tomorrow the whole body of it.
Stdlib only, offline.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

# A passage of Matt's writing: his words + where they come from. The lens holds only these.
#   {"text": "...", "work": "Apokalypsis", "ref": "ch.3", "id": "..."}
_STOP = {"the", "a", "an", "to", "of", "and", "or", "is", "it", "in", "on", "for", "with", "that",
         "this", "as", "at", "by", "be", "are", "was", "were", "he", "she", "they", "we", "you", "i",
         "his", "her", "their", "our", "my", "me", "not", "no", "but", "so", "if", "than", "then"}


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in _STOP}


def _passages_path() -> str:
    """Where the lens corpus lives — his gathered writing. Overridable as we map the writing in."""
    return os.environ.get("CONCORDANCE_LENS", "").strip() or "data/lens.jsonl"


def load(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load the lens corpus (Matt's writing) from a jsonl of passages. Returns [] if not yet gathered —
    an honest empty lens, never a fabricated one."""
    p = path or _passages_path()
    out: List[Dict[str, Any]] = []
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if str(row.get("text") or "").strip():
                out.append(row)
    return out


def see(text: str, *, corpus: Optional[List[Dict[str, Any]]] = None, k: int = 3) -> Dict[str, Any]:
    """Propose a WAY OF SEEING: the passages from Matt's writing that most frame `text`, with provenance.

    Ranked by shared subject words (his words that speak to what was brought). Returns his ACTUAL words,
    never a generation, always attributed — and an honest empty list where his writing does not yet
    reach. This one primitive serves all three senses: the DISCERNMENT (how his witness reads this), the
    VOICE (the words to frame with), and the MAP (the connections his writing draws).

    Proposes; never confirms. `corpus` is injectable (tests, or a scoped body of his writing); it defaults
    to the gathered lens corpus."""
    q = _tokens(text)
    body = corpus if corpus is not None else load()
    scored = []
    for i, p in enumerate(body):
        pt = _tokens((p.get("text") or "") + " " + (p.get("work") or ""))
        overlap = len(q & pt)
        if overlap:
            scored.append((overlap, -i, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    seeing = [{"text": p.get("text"), "work": p.get("work"), "ref": p.get("ref"), "id": p.get("id")}
              for _o, _i, p in scored[:max(1, int(k))]]
    return {
        "seeing": seeing,                       # his words that frame this — the way of seeing
        "proposes": True, "confirms": False,    # the lens proposes; the gate disposes
        "gathered": len(body),                  # how much of his writing the lens can yet see through
        "note": ("the lens proposes how Matt's writing sees this — his words, attributed, never a verdict"
                 if seeing else
                 "his writing does not yet reach this — the lens is still being gathered (map as we go)"),
    }


def available() -> bool:
    """True if any of Matt's writing has been gathered into the lens yet."""
    return len(load()) > 0


__all__ = ["see", "load", "available"]
