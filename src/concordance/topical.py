"""Topical similarity from the keeping's own distributional statistics — no LLM.

A word IS the company it keeps in the keeping. `data/topic_semantic.json` holds a word->vector table
(PPMI over the field-rich keeping, projected to K dims by a fixed seeded +/-1 Johnson-Lindenstrauss
matrix, int8, sealed by tools/build_topic_semantic.py). `similarity(a, b)` averages each text's
word-vectors and takes the cosine, so it can tell "raise hogs" (husbandry) from "hog cholera"
(disease) where surface word-overlap cannot — both carry "hog" — and JOIN "honeybees" with
"beekeeping" where a strict noun match cannot. That is the exact pair of failures the surface matcher
could not thread at once.

This only ever ADDS a signal the caller can weigh; it renders no verdict and generates nothing —
conduit, not source. Sovereign, deterministic, auditable: same artifact -> same score; an absent or
malformed artifact makes every function return a neutral None, and the caller falls back to the
surface heuristics, never a crash and never a single point of failure. Tokenization is shared with
crisis_semantic so the two distributional spaces agree on exactly what a word is.
"""
from __future__ import annotations

import base64
import json
import math
import os
import threading
from pathlib import Path
from typing import List, Optional, Tuple

from . import crisis_semantic as _cs   # the ONE tokenizer, shared so build == runtime == crisis

_LOCK = threading.Lock()
_ART: Optional[dict] = None
_LOADED = False


def _artifact_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR") or str(Path(__file__).resolve().parents[2] / "data")
    return Path(base) / "topic_semantic.json"


def _load() -> Optional[dict]:
    """Load the sealed word->vector table once. Returns {K, scale, index:{stem:row}, blob:bytes} or
    None if absent/malformed. Keeps the raw int8 table and dequantizes only a text's own rows at score
    time (never unpacks the whole table into RAM), exactly as the crisis backstop does."""
    global _ART, _LOADED
    if _LOADED:
        return _ART
    with _LOCK:
        if _LOADED:
            return _ART
        _LOADED = True
        try:
            raw = json.loads(_artifact_path().read_text(encoding="utf-8"))
            K = int(raw["K"])
            scale = float(raw["scale"])
            words = raw["words"]
            blob = base64.b64decode(raw["table_b64"])
            if len(blob) != len(words) * K:
                _ART = None
                return None
            _ART = {"K": K, "scale": scale,
                    "index": {w: i for i, w in enumerate(words)}, "blob": bytes(blob)}
        except Exception:  # noqa: BLE001 — a malformed artifact must never break retrieval
            _ART = None
        return _ART


def available() -> bool:
    return _load() is not None


def _vec(text: str) -> Optional[Tuple[List[float], int]]:
    """(mean word-vector, number of covered words) for a text, or None if it covers no word."""
    art = _load()
    if not art:
        return None
    K, blob, scale, idx = art["K"], art["blob"], art["scale"], art["index"]
    acc = [0.0] * K
    n = 0
    for w in _cs.content(text):
        r = idx.get(w)
        if r is not None:
            n += 1
            off = r * K
            for j in range(K):
                b = blob[off + j]
                acc[j] += ((b - 256) if b > 127 else b) * scale
    if not n:
        return None
    return [a / n for a in acc], n


def similarity(a: str, b: str) -> Optional[float]:
    """Cosine of the two texts' mean word-vectors, in [-1, 1] — or None when either text covers no word
    in the model (the caller then falls back to surface matching rather than trust a blind score)."""
    va = _vec(a)
    vb = _vec(b)
    if not va or not vb:
        return None
    x, y = va[0], vb[0]
    dx = math.sqrt(sum(v * v for v in x))
    dy = math.sqrt(sum(v * v for v in y))
    if not dx or not dy:
        return None
    return sum(p * q for p, q in zip(x, y)) / (dx * dy)


__all__ = ["similarity", "available"]
