#!/usr/bin/env python3
"""Seal the SEMANTIC RETRIEVAL index (data/semantic_index.json) — offline, reproducible, no LLM.

Step 5 of docs/THE_WATCH.md: wire the deterministic answer-path into the live surface. A question in
WORDS THE KEEPING NEVER USED should still land on the node that answers it. The instrument is the same
one the crisis backstop uses (src/concordance/crisis_semantic.py): a PPMI distributional model counted
from the keeping, projected to a small dense space (fixed seeded +-1 — Johnson-Lindenstrauss, so cosine
survives), quantized to int8. On top of the word vectors this tool also seals, per word, its nearest
neighbours by meaning — the expansion table the live search uses to reach paraphrase matches.

Deterministic: same keeping + same SEED -> same artifact. Stdlib + numpy (numpy only for the all-pairs
neighbour matmul, an offline convenience; the runtime needs no numpy). The runtime
(src/concordance/semantic.py) only LOADS and scores; nothing is built in the request path.

    PYTHONPATH=src python tools/build_semantic_index.py [K]
"""
import base64
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from concordance import semantic as S   # noqa: E402  the ONE tokenizer (build == runtime)

DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or (ROOT / "data"))
SEED = 20261006
WINDOW = 5
MIN_COUNT = 6
NEIGHBORS = 10          # top-k related stems sealed per word (the expansion table)
CARD_CAP = 12000
# A broad, bounded slice of the keeping: Scripture + the main card shelves. More corpus = better
# meaning, but the vectors stay sovereign — only what the keeping contains can be encoded.
CORPUS_FILES = [
    "encyclopedia_cards.jsonl", "cards.jsonl", "science_cards.jsonl", "works_cards.jsonl",
    "source_cards.jsonl", "religions_cards.jsonl", "doctrine_cards.jsonl", "food_cards.jsonl",
]


def docs():
    b = DATA / "bible_en.jsonl"
    if b.exists():
        for line in open(b, encoding="utf-8"):
            try:
                yield S.content(json.loads(line).get("text", ""))
            except Exception:
                continue
    for name in CORPUS_FILES:
        p = DATA / name
        if not p.exists():
            continue
        n = 0
        for line in open(p, encoding="utf-8"):
            if n >= CARD_CAP:
                break
            try:
                c = json.loads(line)
            except Exception:
                continue
            toks = S.content(c.get("body") or c.get("text") or "")
            if toks:
                n += 1
                yield toks


def build_ppmi():
    uni = Counter()
    cooc = defaultdict(Counter)
    total = 0
    kept = []
    for toks in docs():
        if toks:
            uni.update(set(toks))
            kept.append(toks)
    vocab = {w for w, c in uni.items() if c >= MIN_COUNT}
    for toks in kept:
        ts = [t for t in toks if t in vocab]
        for i, a in enumerate(ts):
            for j in range(max(0, i - WINDOW), min(len(ts), i + WINDOW + 1)):
                if j != i:
                    cooc[a][ts[j]] += 1
                    total += 1
    ctx = {w: sum(cooc[w].values()) for w in cooc}
    vec = {}
    for w in cooc:
        v = {}
        for cw, n in cooc[w].items():
            pmi = math.log((n * total) / (ctx[w] * ctx.get(cw, 1)) + 1e-12)
            if pmi > 0:
                v[cw] = pmi
        if v:
            vec[w] = v
    return vec


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 256
    print(f"counting PPMI over the keeping (window={WINDOW}, min_count={MIN_COUNT})…", flush=True)
    vec = build_ppmi()
    words = sorted(vec)
    idx = {w: i for i, w in enumerate(words)}
    V = len(words)
    print(f"  vocab {V}", flush=True)
    if V < 500:
        print("too little corpus present — refusing to seal a thin index"); return 1

    # Johnson-Lindenstrauss: project each sparse PPMI vector to K dims with a fixed seeded +-1 matrix.
    import numpy as np
    rng = np.random.default_rng(SEED)
    # project context dimensions: assign each context-word a stable K-vector of +-1
    ctx_words = sorted({cw for w in vec for cw in vec[w]})
    cidx = {cw: i for i, cw in enumerate(ctx_words)}
    R = rng.integers(0, 2, size=(len(ctx_words), K)).astype(np.float32) * 2 - 1    # +-1
    dense = np.zeros((V, K), dtype=np.float32)
    for w, i in idx.items():
        for cw, p in vec[w].items():
            dense[i] += p * R[cidx[cw]]
    norms = np.linalg.norm(dense, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit = dense / norms
    print(f"  projected to {K} dims; finding neighbour candidates (dense) then scoring exactly (sparse)…", flush=True)

    # Neighbours: the dense projection finds CANDIDATES fast (one matmul), then each candidate is
    # re-scored with the EXACT sparse-PPMI cosine and the best kept. Approximate-then-exact: dense speed,
    # sparse quality (the 256-d projection alone gave noisy neighbours; the sparse cosine does not).
    snorm = {w: math.sqrt(sum(x * x for x in vec[w].values())) or 1.0 for w in vec}

    def sparse_cos(a, b):
        va, vb = vec[a], vec[b]
        if len(vb) < len(va):
            va, vb = vb, va
        dot = 0.0
        for k, x in va.items():
            y = vb.get(k)
            if y:
                dot += x * y
        return dot / (snorm[a] * snorm[b])

    CAND = 60
    neighbors = {}
    B = 1024
    for s in range(0, V, B):
        sims = unit[s:s + B] @ unit.T                 # (b, V) dense candidate scores
        for r in range(sims.shape[0]):
            row = sims[r]; wi = s + r; w = words[wi]
            row[wi] = -2.0
            cand = np.argpartition(row, -CAND)[-CAND:]
            rescored = sorted(((sparse_cos(w, words[j]), words[j]) for j in cand), reverse=True)
            neighbors[w] = [o for sc, o in rescored[:NEIGHBORS] if sc > 0.12]

    # quantize the dense vectors to int8 for a compact, committable table (runtime re-rank)
    scale = float(np.abs(dense).max()) / 127.0 or 1.0
    q = np.clip(np.round(dense / scale), -127, 127).astype(np.int8)
    table_b64 = base64.b64encode(q.tobytes()).decode("ascii")

    art = {
        "_note": ("Semantic retrieval index for the live answer-path (docs/THE_WATCH.md step 5). PPMI over "
                  "the keeping, JL-projected to K dims (int8), plus top-%d meaning-neighbours per word. "
                  "Built by tools/build_semantic_index.py; loaded by src/concordance/semantic.py. No LLM." % NEIGHBORS),
        "seed": SEED, "window": WINDOW, "min_count": MIN_COUNT, "K": K, "scale": scale,
        "vocab": V, "words": words, "table_b64": table_b64, "neighbors": neighbors,
    }
    out = DATA / "semantic_index.json"
    out.write_text(json.dumps(art, ensure_ascii=False), encoding="utf-8")
    nn = sum(len(v) for v in neighbors.values()) / max(1, V)
    print(f"sealed {out} — vocab {V}, K {K}, mean neighbours {nn:.1f}, {out.stat().st_size//1024} KB")
    # a glance, so a human can audit the meaning
    for probe in ("afraid", "money", "shepherd", "sickness", "forgive", "worried"):
        st = S.stem(probe)
        print(f"  {probe:9s} -> {neighbors.get(st, [])[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
