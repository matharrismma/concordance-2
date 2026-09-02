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


# A physical MEASUREMENT / conversion question is never a cry, but the distributional score reads one as
# close to crisis: "how much does a gallon of water weigh" scored 0.694 (> 0.657) — the model conflates
# physical "how much does X WEIGH" with emotional "how much more can I bear / the weight I carry"
# (measured live 2026-08-31, query 96 of a 100-pass run: a benign lookup met with a helpline). This is
# the documented topic≈intent limit of a distributional model; correct it deterministically. The guard
# is TIGHT — verified to match 0 of the curated CRISIS_FLOOR and 0 of the blind RED_TEAM set, so the
# recall floor cannot shrink; a veiled cry the backstop exists to catch carries no unit, no measure verb.
_BENIGN_MEASUREMENT = re.compile(
    r"\bhow (?:much|many|long|far|tall|wide|deep|heavy|hot|cold)\b.{0,60}\b"
    r"(?:weigh|weighs|weight|cost|costs|measure|measures|gallon|ounce|pound|teaspoon|tablespoon|cup|"
    r"quart|liter|litre|mile|kilomet|kilogram|gram|meter|metre|inch|foot|feet|celsius|fahrenheit|"
    r"degree|calorie|acre|volt|watt|amp|psi|horsepower|bushel)\b"
    r"|\bconvert\b.{0,40}\b(?:to|into)\b"
    r"|\bhow many\b.{0,40}\bin (?:a|an|one)\b", re.I)

# A THEODICY question — the problem of evil, "why does God allow suffering" — is the seeker's oldest
# question, not a cry. The distributional score read one as crisis (0.691 > 0.657; measured live
# 2026-08-31: a seeker's deepest question met with a helpline). It is the SAME topic≈intent limit:
# "suffering / allow" sits near the crisis cluster. The frame is unmistakably ABOUT God permitting evil
# in the world, never first-person distress — "i am suffering and want it to end" (0.757) and "why does
# god hate me" carry no such frame and still fire. Verified: 0 hits on CRISIS_FLOOR, 0 on RED_TEAM. The
# ultimate/seeker/comfort paths answer this with Scripture and point to Christ and to real people.
_THEODICY = re.compile(
    r"\bwhy (?:does|would|did|do|is|are) .*\bgod\b.*\b(?:allow|permit|let|cause)\b"
    # God named, then referred to by pronoun — "who is God and why does HE allow suffering". Anchored to
    # an ABSTRACT object (evil/suffering/…) so a first-person cry ("why does he let ME suffer") never
    # matches; and this only suppresses the backstop — the substring net still catches any explicit cry.
    r"|\bgod\b.*\bwhy (?:does|would|did|do) (?:he|she|they|it)\b.*\b(?:allow|permit|let|cause)\s+"
    r"(?:so much |such |all this |the )?(?:evil|suffering|pain|injustice|death|sin)\b"
    r"|\bproblem of (?:evil|suffering|pain)\b"
    r"|\bwhy (?:is there|does).{0,20}(?:evil|suffering) (?:in|exist)", re.I)


def flags(text: str) -> bool:
    """True when the semantic backstop judges this a cry. Only ever ADDS to the substring net."""
    art = _load()
    if not art:
        return False
    t = text or ""
    if _BENIGN_MEASUREMENT.search(t):
        return False                      # a physical measurement/conversion is never a cry (see note)
    if _THEODICY.search(t):
        return False                      # a theodicy question is the seeker's, not a cry (see note)
    return score(text) > art["threshold"]
