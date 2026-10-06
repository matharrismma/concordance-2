"""THE SEMANTIC RETRIEVAL LAYER — the answer-path, live (docs/THE_WATCH.md step 5).

A question phrased in words the keeping never used should still reach the node that answers it. This
module is the instrument: a sealed, deterministic distributional model (PPMI over the keeping, projected
to a small dense space, int8) with, per word, its nearest neighbours by MEANING. No LLM, no training at
runtime — the artifact (data/semantic_index.json, built by tools/build_semantic_index.py) is loaded once
and only read. It is sovereign and auditable: only what the keeping contains can be encoded, and every
neighbour list can be printed and checked.

Two services to the live search:
  expand(tokens)            -> related stems, to reach cards that share MEANING but not words
  rerank(query, items, key) -> order candidates by centroid cosine to the query

Nothing here decides truth; it only helps FIND. The verifiers and the keeping remain the authority.
"""
from __future__ import annotations

import base64
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ── the ONE tokenizer (build imports these, so build == runtime) ─────────────────────────────────────
_STOP = set(("the a an of to and but in on for is are was were be his her my your their our its he she "
             "it they we you i o thou thy thee that this these those which who whom with as from by at "
             "into unto out up down shall will not no nor them him us me all there so then when have has "
             "had do did whether or thing things came come go went upon also let us may might would "
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


# ── the sealed artifact, loaded once ─────────────────────────────────────────────────────────────────
_CACHE: Dict[str, Any] = {}


def _artifact_path() -> Path:
    d = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")
    return d / "semantic_index.json"


def _load() -> Optional[dict]:
    p = _artifact_path()
    key = str(p)
    if key in _CACHE:
        return _CACHE[key]
    art: Optional[dict] = None
    try:
        if p.exists():
            raw = json.loads(p.read_text(encoding="utf-8"))
            if raw.get("words") and raw.get("neighbors") is not None:
                raw["_vectors"] = None          # decoded lazily on first rerank
                raw["_index"] = {w: i for i, w in enumerate(raw["words"])}
                art = raw
    except (OSError, ValueError):
        art = None
    _CACHE[key] = art
    return art


def available() -> bool:
    return _load() is not None


def _vectors(art: dict):
    """Decode the int8 dense table to word -> tuple[float] on first use (runtime re-rank only)."""
    if art.get("_vectors") is not None:
        return art["_vectors"]
    words = art["words"]; K = int(art["K"]); scale = float(art["scale"])
    buf = base64.b64decode(art["table_b64"])
    import array
    a = array.array("b")                        # signed char (int8)
    a.frombytes(buf)
    vecs: Dict[str, tuple] = {}
    for i, w in enumerate(words):
        seg = a[i * K:(i + 1) * K]
        vecs[w] = tuple(x * scale for x in seg)
    art["_vectors"] = vecs
    return vecs


# ── expansion: related stems by meaning (the busy, cheap path — neighbours only, no vectors) ─────────
def expand(tokens, per: int = 6, cap: int = 24) -> List[str]:
    """Related stems for the given query tokens, drawn from the sealed meaning-neighbour table. Returns
    only NEW stems (not already among the query tokens), deterministically ordered, capped. Empty if the
    index is absent — the caller then simply gets no expansion, never an error."""
    art = _load()
    if not art:
        return []
    have = {stem(t) for t in tokens}
    nb = art["neighbors"]
    out: List[str] = []
    seen = set(have)
    for t in tokens:
        for r in nb.get(stem(t), [])[:per]:
            if r not in seen:
                seen.add(r)
                out.append(r)
                if len(out) >= cap:
                    return out
    return out


# ── centroid cosine, for re-ranking a candidate set against the query ────────────────────────────────
def _centroid(vecs: Dict[str, tuple], tokens, K: int):
    acc = [0.0] * K
    n = 0
    for t in tokens:
        v = vecs.get(stem(t))
        if v:
            n += 1
            for i in range(K):
                acc[i] += v[i]
    if n:
        acc = [x / n for x in acc]
    return acc, n


def _cos(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def similarity(query: str, text: str) -> float:
    """Centroid cosine between a query and a text, 0.0 if the index is absent or either is out-of-vocab."""
    art = _load()
    if not art:
        return 0.0
    vecs = _vectors(art); K = int(art["K"])
    qa, qn = _centroid(vecs, content(query), K)
    ta, tn = _centroid(vecs, content(text), K)
    if not qn or not tn:
        return 0.0
    return _cos(qa, ta)


def rerank(query: str, items: List[Any], key: Callable[[Any], str], top: Optional[int] = None):
    """Order items by centroid cosine of key(item) to the query (descending). Ties and out-of-vocab keep
    their original order (stable). Returns (ordered_items, scores) so the caller can threshold."""
    art = _load()
    if not art or not items:
        return list(items), {}
    vecs = _vectors(art); K = int(art["K"])
    qa, qn = _centroid(vecs, content(query), K)
    if not qn:
        return list(items), {}
    scored = []
    for i, it in enumerate(items):
        ta, tn = _centroid(vecs, content(key(it) or ""), K)
        s = _cos(qa, ta) if tn else 0.0
        scored.append((s, i, it))
    scored.sort(key=lambda z: (-z[0], z[1]))
    ordered = [it for _, _, it in scored]
    if top is not None:
        ordered = ordered[:top]
    return ordered, {id(it): s for s, _, it in scored}
