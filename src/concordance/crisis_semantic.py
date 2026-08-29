"""The crisis SEMANTIC BACKSTOP — a deterministic second net UNDER the substring matcher.

ask.is_crisis catches the words despair uses plainly. It cannot catch the veiled/behavioral cries that
share no keyword with the list — "I just want to be wherever my wife is now", "there's nothing keeping
me here since he passed", "how peaceful it would be to just stop". This backstop does, from the keeping
alone: a deterministic distributional model (PPMI over the keeping) projected to a small dense space
(Johnson–Lindenstrauss), sealed once by tools/build_crisis_semantic.py into data/crisis_semantic.json.

At runtime we do NOT build or project anything — we load the sealed word→vector table, average a
message's word-vectors, and take the cosine against a fixed crisis centroid. Above a conservative
threshold (set so the known benign set never fires), it flags. It only ever ADDS a catch — is_crisis
unions it with the substring list — so it can widen the net but never narrow it, and the deliberate
asymmetry stands (an unnecessary helpline is a small cost; a missed person is not).

Sovereign, auditable, no LLM: the vectors are counted from the verified keeping; the projection is a
fixed seeded ±1 matrix; the whole artifact is a committed JSON you can read. If the artifact is absent
or malformed, flags() returns False and the engine falls back to the substring net — never a crash,
never a single point of failure. See docs/CRISIS_BACKSTOP.md.
"""
from __future__ import annotations

import base64
import json
import math
import os
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional

# ── tokenization: identical to the model the artifact was built with (build tool imports THESE) ──────
_STOP = set(("the a an of to and but in on for is are was were be his her my your their our its he she "
             "it they we you i o thou thy thee that this these those which who whom with as from by at "
             "into unto out up down shall will not no nor them him us me all there so then when when have "
             "has had do did whether or thing things came come go went upon also let us may might would "
             "should could yet if because therefore now even said say says loud great one man men "
             "children people day days made make thus behold saying").split())


def stem(w: str) -> str:
    w = re.sub(r"[^a-z]", "", w.lower())
    for s in ("ing", "eth", "est", "ed"):
        if w.endswith(s) and len(w) - len(s) >= 3:
            return w[: -len(s)]
    if w.endswith("es") and len(w) - 2 >= 3:
        return w[:-2] if (w[-3] in "sxzo" or w.endswith(("ches", "shes"))) else w[:-1]
    if w.endswith("s") and len(w) - 1 >= 3:
        return w[:-1]
    return w


def content(text: str) -> List[str]:
    return [s for s in (stem(w) for w in (text or "").split()) if s and s not in _STOP and len(s) >= 3]


# ── the sealed artifact, loaded once ────────────────────────────────────────────────────────────────
_LOCK = threading.Lock()
_ART: Optional[dict] = None
_LOADED = False


def _artifact_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR") or str(Path(__file__).resolve().parents[2] / "data")
    return Path(base) / "crisis_semantic.json"


def _load() -> Optional[dict]:
    """Load + unpack the artifact once. Returns a dict with {K, scale, threshold, centroid[K],
    words: {stem: rowindex}, table: [count][K] floats}, or None if absent/malformed."""
    global _ART, _LOADED
    if _LOADED:
        return _ART
    with _LOCK:
        if _LOADED:
            return _ART
        _LOADED = True
        p = _artifact_path()
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            K = int(raw["K"])
            scale = float(raw["scale"])
            words = raw["words"]                                  # list[str], row order
            centroid = [float(x) for x in raw["crisis_centroid"]]
            blob = base64.b64decode(raw["table_b64"])            # count*K signed int8, kept RAW
            n = len(words)
            if len(blob) != n * K or len(centroid) != K:
                _ART = None
                return None
            # Keep the ~1.5MB byte table as-is and dequantize ONLY a message's own word-rows at score
            # time — never unpack all n×K floats into RAM (that would cost ~50MB on a small box).
            cnorm = math.sqrt(sum(x * x for x in centroid)) or 1.0
            _ART = {"K": K, "threshold": float(raw["threshold"]), "centroid": centroid,
                    "cnorm": cnorm, "scale": scale, "index": {w: i for i, w in enumerate(words)},
                    "blob": bytes(blob)}
        except Exception:  # noqa: BLE001 — a malformed artifact must never break the safety check
            _ART = None
        return _ART


def available() -> bool:
    return _load() is not None


def score(text: str) -> float:
    """Cosine of the message's mean word-vector against the crisis centroid; 0.0 if unavailable/empty."""
    art = _load()
    if not art:
        return 0.0
    K, blob, scale = art["K"], art["blob"], art["scale"]
    idx, C, cn = art["index"], art["centroid"], art["cnorm"]
    acc = [0.0] * K
    n = 0
    for w in content(text):
        r = idx.get(w)
        if r is not None:
            n += 1
            off = r * K
            for j in range(K):
                b = blob[off + j]
                acc[j] += ((b - 256) if b > 127 else b) * scale
    if not n:
        return 0.0
    dot = 0.0
    na = 0.0
    for j in range(K):
        a = acc[j] / n
        dot += a * C[j]
        na += a * a
    na = math.sqrt(na)
    return dot / (na * cn) if na else 0.0


def flags(text: str) -> bool:
    """True when the semantic backstop judges this a cry. Only ever ADDS to the substring net."""
    art = _load()
    if not art:
        return False
    return score(text) > art["threshold"]
