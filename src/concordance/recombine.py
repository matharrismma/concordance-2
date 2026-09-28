"""RECOMBINE — the expressive half of the Cubo model: say it by RECOMBINING found instances over the
frame, never by generating. The bumblebee principle (recombine, don't generate) and "found, not authored,"
applied to speech.

Comprehension by the cube already works (decode a real sentence by the anchor it carries — `readwith`).
This is the other direction: given an intent and a pool of REAL, verbatim instances (sentences the keeping
holds, each tagged with the embodied anchor it carries), assemble a coherent answer by SELECTING and
ORDERING those fragments along the frame — existence → identity → motion — most relevant first. Every word
traces to a found instance; nothing is sampled from weights, nothing is composed to fit. If the pool holds
too little to answer, it says so (an honest gap) rather than inventing.

TWO GRAINS:
  • `compose` (v0) — EXTRACTIVE: select + frame-order whole verbatim SENTENCES.
  • `weave`  (v0.1) — CLAUSE-level: shrink the unit to the verbatim CLAUSE (a sharper answer, still a
    contiguous substring of ONE source), and join clauses with FRAME joints that assert nothing. The
    truth guard a verification engine must keep: no clause is altered, the frame joints carry no claim,
    and two clauses from DIFFERENT sources are held apart by a boundary (never fused by a conjunction), so
    the weave can never assert what no single source said. Per-clause provenance rides in `pieces`.

Still not yet the full frontier: resolving reference and inflecting a found word (which would modify the
verbatim) are the deeper craft, deliberately NOT done here — every content token stays real and cited.

`compose` is a pure function (instances are injected), so it is offline-testable and reaches for nothing on
its own; a caller gathers the instances (e.g. via `readwith.decodable` over the cards a search returned).
GATED for wiring by CONCORDANCE_RECOMBINE; the pure core always runs.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

_WORD = re.compile(r"[a-z0-9]+")

# The frame's narrative order: set the scene (what exists) → say what it is → what one does. An anchor the
# instance carries places it; an unknown/other-tongue anchor takes the middle (identity) role.
_ROLE = {
    "there is": 0, "there are": 0, "here is": 0, "il y a": 0, "es gibt": 0, "sunt": 0, "hay": 0,
    "i am": 1, "it is": 1, "this is": 1, "je suis": 1, "c'est": 1, "il est": 1, "ich bin": 1,
    "das ist": 1, "sum": 1, "est": 1, "soy": 1, "estoy": 1,
    "i go": 2, "je vais": 2, "ich gehe": 2, "eo": 2, "voy": 2,
}
_DEFAULT_ROLE = 1


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_RECOMBINE", "").strip().lower() in ("1", "true", "yes", "on")


def _toks(s: str) -> set:
    return {w for w in _WORD.findall(str(s or "").lower()) if len(w) > 2}


def compose(query: str, instances: List[Dict[str, Any]], *, limit: int = 5) -> Dict[str, Any]:
    """Assemble an answer from found, verbatim `instances` (each `{text, source, anchor}`), ordered along
    the frame and by relevance to `query`. Returns the composed passage + every fragment with its source.
    Honest empty when nothing fits — never invents to fill the gap."""
    qt = _toks(query)
    ranked = []
    for ins in instances:
        text = str((ins.get("text") if isinstance(ins, dict) else ins) or "").strip()
        if not text:
            continue
        anchor = str((ins.get("anchor") if isinstance(ins, dict) else "") or "").strip().lower()
        role = _ROLE.get(anchor, _DEFAULT_ROLE)
        rel = len(_toks(text) & qt)                       # overlap with the intent
        ranked.append((role, -rel, len(text), text, ins))
    ranked.sort(key=lambda x: (x[0], x[1], x[2], x[3]))    # frame order → relevance → shortest → stable
    chosen: List[Dict[str, Any]] = []
    seen = set()
    for _role, _nrel, _ln, text, ins in ranked:
        if text in seen:
            continue
        seen.add(text)
        chosen.append({"text": text,
                       "source": (ins.get("source") if isinstance(ins, dict) else None),
                       "anchor": (ins.get("anchor") if isinstance(ins, dict) else None)})
        if len(chosen) >= max(1, int(limit)):
            break
    if not chosen:
        return {"passage": "", "fragments": [], "found": False,
                "means": "the keeping holds nothing that answers this by the frame — an honest gap, not a guess"}
    return {"passage": " ".join(c["text"] for c in chosen), "fragments": chosen, "found": True,
            "means": (f"composed from {len(chosen)} found, verbatim fragment(s), ordered by the frame "
                      "(existence → identity → motion); every word is real and cited — nothing generated")}


# ── v0.1 — clause-level weaving ────────────────────────────────────────────────────────────────────

# Clause boundaries: strong punctuation and a comma before a joining word. Splitting HERE keeps each piece
# a contiguous, verbatim span of the source — we never reach inside a clause.
_CLAUSE_SPLIT = re.compile(r"\s*[;:]\s*|\s+[—–]\s+|\s+-\s+|,\s+(?=and |but |so |then |or |for |yet |because |which |that |when |while |where )", re.I)
_TRIM = " \t\r\n,.;:—–-\"'()[]"


def _spans(text: str, anchor: str = "") -> List[Dict[str, Any]]:
    """Split a found sentence into verbatim clause spans (each a contiguous substring), tagging each with
    the embodied anchor it carries. Spans with too little content are dropped; if it will not split, the
    whole sentence rides as one span."""
    text = str(text or "").strip()
    if not text:
        return []
    out: List[Dict[str, Any]] = []
    for raw in _CLAUSE_SPLIT.split(text):
        span = str(raw or "").strip(_TRIM).strip()
        if len(_WORD.findall(span)) < 3:                  # a real clause, not a stray fragment
            continue
        low = span.lower()
        a = next((p for p in _ROLE if p in low), (anchor or "").strip().lower())
        out.append({"span": span, "anchor": a, "role": _ROLE.get(a, _DEFAULT_ROLE), "toks": _toks(span)})
    if not out:
        low = text.lower()
        a = next((p for p in _ROLE if p in low), (anchor or "").strip().lower())
        out.append({"span": text, "anchor": a, "role": _ROLE.get(a, _DEFAULT_ROLE), "toks": _toks(text)})
    return out


def weave(query: str, instances: List[Dict[str, Any]], *, limit: int = 4) -> Dict[str, Any]:
    """Weave an answer from found CLAUSES over the frame. Sharper than `compose` (clause, not sentence),
    with frame joints that assert nothing and a cross-source boundary so no two clauses fuse into a claim
    a source did not make. `pieces` carries per-clause provenance; `passage` is the rendered convenience."""
    qt = _toks(query)
    spans: List[Dict[str, Any]] = []
    for ins in instances:
        text = str((ins.get("text") if isinstance(ins, dict) else ins) or "")
        src = ins.get("source") if isinstance(ins, dict) else None
        anch = str((ins.get("anchor") if isinstance(ins, dict) else "") or "")
        for sp in _spans(text, anch):
            sp["source"] = src
            sp["rel"] = len(sp["toks"] & qt)
            spans.append(sp)
    spans.sort(key=lambda s: (s["role"], -s["rel"], len(s["span"]), s["span"]))   # frame → relevance → tight
    chosen: List[Dict[str, Any]] = []
    seen = set()
    for s in spans:
        if s["span"] in seen:
            continue
        if qt and s["rel"] == 0 and chosen:               # after the first, require a tie to the intent
            continue
        seen.add(s["span"])
        chosen.append(s)
        if len(chosen) >= max(1, int(limit)):
            break
    if not chosen:
        return {"passage": "", "pieces": [], "found": False,
                "means": "the keeping holds no clause that answers this by the frame — an honest gap, not a guess"}
    pieces: List[Dict[str, Any]] = []
    for i, s in enumerate(chosen):
        if i > 0:
            prev = chosen[i - 1]
            same = prev.get("source") is not None and prev.get("source") == s.get("source")
            # smooth WITHIN a source (it already related its own clauses); a BOUNDARY across sources so two
            # verbatim clauses are never fused into a single assertion no source made
            pieces.append({"text": ", " if same else "; ", "kind": "frame"})
        pieces.append({"text": s["span"], "kind": "found", "source": s.get("source"), "anchor": s.get("anchor")})
    passage = "".join(p["text"] for p in pieces).strip()
    n_src = len({s.get("source") for s in chosen})
    return {"passage": passage, "pieces": pieces, "found": True,
            "means": (f"woven from {len(chosen)} found clause(s) across {n_src} source(s), ordered by the "
                      "frame; the joints assert nothing and clauses from different sources are held apart — "
                      "no claim is made that a source did not make; nothing is generated or altered")}
