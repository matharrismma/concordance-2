"""Lens — Matt's writing as the way of seeing. The soul of discernment.

Matt, 2026-08-20: *"I had seen my writing as the lens."* The build plan named three layers — substrate,
wiring, and **lens** ("the way of seeing: what proposes what to check and how to read a claim"). `discern`
is the SHAPE of the lens (kind, necessity, route…); this is what it sees WITH: Matt's own writing, his
witness. A lens with no way of seeing is just a hole in the glass; his writing is the ground it is tuned
to.

THREE SENSES, ONE GROUND. His writing is the lens in three ways, and all three stand on `see()`:
  DISCERNMENT — his writing proposes what matters and how to read a claim.        → see()
  VOICE       — his own words frame the answer (never a generated imitation — his actual writing speaks). → voice()
  MAP         — his writing is the structure of how things connect and point to Christ.  → edges()

`see(text)` proposes a way of seeing: the passages from Matt's writing that frame the input, with their
provenance. `voice(text)` selects the single passage to lead an answer with — his verbatim words, never
imitated. `edges(text)` surfaces the connections his writing DRAWS — the Scripture his relevant passages
point to — as attributed edges, so navigation follows his map, not raw co-occurrence. The laws they keep,
every one:
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


def voice(text: str, *, corpus: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """VOICE — frame the answer with Matt's OWN words. Selects the single passage of his writing that most
    frames `text` and returns it verbatim, attributed, to lead the answer with. Nothing is generated: his
    voice is his because it IS his — never a style imitated (de-AI holds). Where his writing does not yet
    reach, the frame is honestly empty and the answer stands on its own, in no imitated voice. Proposes;
    never confirms."""
    seen = see(text, corpus=corpus, k=1)
    top = seen["seeing"][0] if seen["seeing"] else None
    return {
        "frame": (top["text"] if top else None),          # his verbatim words to lead with — or None
        "work": (top["work"] if top else None),
        "ref": (top["ref"] if top else None),
        "id": (top["id"] if top else None),
        "his_words": bool(top), "generated": False,        # never authored in his register
        "proposes": True, "confirms": False,
        "gathered": seen["gathered"],
        "note": ("Matt's own words frame this — verbatim, attributed, never imitated" if top else
                 "his writing does not reach this yet — the answer stands on its own, in no imitated voice"),
    }


# The map is built from the Scripture Matt's writing points to. Chapter-anchored references only (Book N or
# Book N:V) — a strong signal that keeps false edges out; where his writing names a book without a chapter,
# or by an abbreviation we do not yet read, the map simply under-reaches (map as we go), never invents.
_BOOKS = ("genesis exodus leviticus numbers deuteronomy joshua judges ruth samuel kings chronicles ezra "
          "nehemiah esther job psalms psalm proverbs ecclesiastes song isaiah jeremiah lamentations "
          "ezekiel daniel hosea joel amos obadiah jonah micah nahum habakkuk zephaniah haggai zechariah "
          "malachi matthew mark luke john acts romans corinthians galatians ephesians philippians "
          "colossians thessalonians timothy titus philemon hebrews james peter jude revelation").split()
_SCRIPTURE_RE = re.compile(
    r"\b(?:([1-3])\s+)?(" + "|".join(sorted(set(_BOOKS), key=len, reverse=True)) +
    r")\.?\s+(\d+)(?::(\d+(?:[-–]\d+)?))?\b", re.IGNORECASE)


def _scripture_refs(s: str) -> List[str]:
    """The chapter-anchored Scripture references a passage names, normalized and de-duplicated in order."""
    out: List[str] = []
    for m in _SCRIPTURE_RE.finditer(s or ""):
        num, book, ch, vs = m.group(1), m.group(2), m.group(3), m.group(4)
        ref = ((num + " ") if num else "") + book[:1].upper() + book[1:].lower() + " " + ch
        if vs:
            ref += ":" + vs
        if ref not in out:
            out.append(ref)
    return out


def edges(text: str, *, corpus: Optional[List[Dict[str, Any]]] = None, k: int = 5) -> Dict[str, Any]:
    """MAP — the connections Matt's writing DRAWS for what you brought: the Scripture his relevant passages
    point to, as ATTRIBUTED edges (a theme → where his writing anchors it). Nothing is invented — an edge
    exists only where his passage literally names that Scripture, so the map follows HIS way of seeing, not
    raw co-occurrence. His writing points, in the end, to Christ; the map surfaces that pointing. Honest
    empty where his writing draws no edge for this yet. Proposes; never confirms."""
    q = _tokens(text)
    body = corpus if corpus is not None else load()
    scored = []
    for i, p in enumerate(body):
        shared = q & _tokens((p.get("text") or "") + " " + (p.get("work") or ""))
        if shared:
            scored.append((len(shared), -i, p, shared))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out: List[Dict[str, Any]] = []
    for _o, _i, p, shared in scored:
        refs = _scripture_refs(p.get("text") or "")
        if not refs:
            continue                                        # a relevant passage that draws no edge draws none
        theme = sorted(shared, key=lambda w: (-len(w), w))[0]   # the strongest shared subject word
        for ref in refs:
            out.append({"theme": theme, "points_to": ref, "text": p.get("text"),
                        "work": p.get("work"), "ref": p.get("ref"), "id": p.get("id")})
        if len(out) >= max(1, int(k)):
            break
    out = out[:max(1, int(k))]
    return {
        "edges": out,                               # theme → the Scripture his writing points it to, attributed
        "proposes": True, "confirms": False,
        "gathered": len(body),
        "note": ("Matt's writing draws these — a theme to the Scripture it points to, his words, attributed"
                 if out else
                 "his writing draws no edge for this yet — the map is still being gathered (map as we go)"),
    }


def available() -> bool:
    """True if any of Matt's writing has been gathered into the lens yet."""
    return len(load()) > 0


__all__ = ["see", "voice", "edges", "load", "available"]
