"""RECOMBINE — the expressive half of the Cubo model: say it by RECOMBINING found instances over the
frame, never by generating. The bumblebee principle (recombine, don't generate) and "found, not authored,"
applied to speech.

Comprehension by the cube already works (decode a real sentence by the anchor it carries — `readwith`).
This is the other direction: given an intent and a pool of REAL, verbatim instances (sentences the keeping
holds, each tagged with the embodied anchor it carries), assemble a coherent answer by SELECTING and
ORDERING those fragments along the frame — existence → identity → motion — most relevant first. Every word
traces to a found instance; nothing is sampled from weights, nothing is composed to fit. If the pool holds
too little to answer, it says so (an honest gap) rather than inventing.

HONEST SCOPE (v0): this is EXTRACTIVE recombination — selection + frame-ordering of whole verbatim
fragments, with full provenance. It does not yet weave novel sentences (splice clauses, resolve reference,
inflect) — that is the frontier the engine grows toward. v0 is the seed: a grounded, non-generative
utterance whose every piece is real and cited.

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
