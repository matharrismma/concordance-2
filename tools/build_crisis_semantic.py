#!/usr/bin/env python3
"""Seal the crisis SEMANTIC BACKSTOP artifact (data/crisis_semantic.json) — offline, reproducible.

Counts a PPMI distributional model from the keeping, builds a crisis centroid from the confirmed crisis
corpus, projects every word to a small dense space (fixed seeded ±1 — Johnson–Lindenstrauss, so the
cosine survives), quantizes to int8, sets a CONSERVATIVE threshold so the known-benign set never fires,
and writes a committable JSON. The runtime (src/concordance/crisis_semantic.py) only loads + scores.

Deterministic: same keeping + same SEED → same artifact. No LLM, no numpy — stdlib only. Tokenization
is imported from crisis_semantic so build and runtime agree exactly.

    PYTHONPATH=src python tools/build_crisis_semantic.py [K]
"""
import base64
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from concordance import crisis_semantic as cs  # noqa: E402  the ONE tokenizer (build == runtime)
import test_crisis_coverage as T               # noqa: E402  the confirmed crisis/benign corpora

DATA = ROOT / "data"
SEED = 20260828
WINDOW = 5
MIN_COUNT = 5
CARD_FILES = ["encyclopedia_cards.jsonl", "cards.jsonl"]
CARD_CAP = 9000
MARGIN = 0.02   # headroom above the worst benign score, for safety against unseen benign


def docs():
    for line in open(DATA / "bible_en.jsonl", encoding="utf-8"):
        yield cs.content(json.loads(line).get("text", ""))
    for name in CARD_FILES:
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
            toks = cs.content(c.get("body") or c.get("text") or "")
            if toks:
                n += 1
                yield toks


def build_ppmi():
    uni = Counter()
    kept = []
    for toks in docs():
        if toks:
            uni.update(set(toks))
            kept.append(toks)
    vocab = {w for w, n in uni.items() if n >= MIN_COUNT}
    cooc = defaultdict(Counter)
    total = 0
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
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    if not (DATA / "bible_en.jsonl").exists():
        print("corpus not present"); return
    print(f"counting PPMI from the keeping (K={K}, seed={SEED})…", flush=True)
    vec = build_ppmi()
    print(f"  vocab {len(vec)}", flush=True)

    # crisis centroid = mean PPMI vector over the confirmed crisis corpus's content words
    cwords = []
    for phrase in T.CRISIS_FLOOR:
        cwords += cs.content(phrase)
    cen = defaultdict(float)
    m = 0
    for w in cwords:
        if w in vec:
            m += 1
            for k, x in vec[w].items():
                cen[k] += x
    for k in cen:
        cen[k] /= m

    # fixed seeded ±1 projection, regenerated per context word (never stored)
    ctx_idx = {c: i for i, c in enumerate(sorted({c for v in vec.values() for c in v}))}
    Rcache = {}
    def Rc(i):
        r = Rcache.get(i)
        if r is None:
            g = random.Random(SEED * 1000003 + i)
            r = [1.0 if g.random() < 0.5 else -1.0 for _ in range(K)]
            Rcache[i] = r
        return r
    s = 1.0 / math.sqrt(K)
    def project(v):
        d = [0.0] * K
        for c, val in v.items():
            i = ctx_idx.get(c)
            if i is None:
                continue
            rc = Rc(i)
            for j in range(K):
                d[j] += val * rc[j]
        return [x * s for x in d]

    print("  projecting vocabulary…", flush=True)
    words = sorted(vec)
    dense = [project(vec[w]) for w in words]
    dC = project(cen)

    # int8 quantization with one global scale
    peak = max((abs(x) for row in dense for x in row), default=1.0) or 1.0
    scale = peak / 127.0
    def q(row):
        return bytes((max(-127, min(127, round(x / scale))) & 0xFF) for x in row)
    table = b"".join(q(row) for row in dense)

    # score exactly as the runtime will (dequantized), to set a threshold the runtime reproduces
    idx = {w: i for i, w in enumerate(words)}
    deq = [[((table[r * K + j] - 256) if table[r * K + j] > 127 else table[r * K + j]) * scale
            for j in range(K)] for r in range(len(words))]
    cnorm = math.sqrt(sum(x * x for x in dC)) or 1.0
    def scoreq(text):
        acc = [0.0] * K
        n = 0
        for w in cs.content(text):
            r = idx.get(w)
            if r is not None:
                n += 1
                row = deq[r]
                for j in range(K):
                    acc[j] += row[j]
        if not n:
            return 0.0
        dot = na = 0.0
        for j in range(K):
            a = acc[j] / n
            dot += a * dC[j]; na += a * a
        na = math.sqrt(na)
        return dot / (na * cnorm) if na else 0.0

    benign = sorted((scoreq(x) for x in T.CLEARLY_BENIGN), reverse=True)
    threshold = benign[0] + MARGIN
    import importlib
    ask = importlib.import_module("concordance.ask")
    sub_missed = [x for x in T.RED_TEAM_BLIND if not ask.is_crisis(x)]
    caught = sum(1 for x in sub_missed if scoreq(x) > threshold)
    fp = sum(1 for x in T.CLEARLY_BENIGN if scoreq(x) > threshold)
    union = sum(1 for x in T.RED_TEAM_BLIND if ask.is_crisis(x) or scoreq(x) > threshold)
    floor_extra = sum(1 for x in T.CRISIS_FLOOR if scoreq(x) > threshold)

    out = {
        "_note": "Crisis semantic backstop — deterministic PPMI over the keeping, JL-projected, int8. "
                 "Built by tools/build_crisis_semantic.py. Runtime: src/concordance/crisis_semantic.py.",
        "K": K, "seed": SEED, "window": WINDOW, "min_count": MIN_COUNT,
        "scale": scale, "threshold": threshold, "vocab": len(words),
        "crisis_centroid": dC, "words": words,
        "table_b64": base64.b64encode(table).decode("ascii"),
    }
    path = DATA / "crisis_semantic.json"
    path.write_text(json.dumps(out), encoding="utf-8")
    mb = path.stat().st_size / 1e6

    print(f"\nsealed {path}  ({mb:.1f} MB, {len(words)} words × {K} dims int8)")
    print(f"threshold {threshold:.4f} (top benign {benign[0]:.4f} + margin {MARGIN})")
    print(f"benign false-positives: {fp}/{len(T.CLEARLY_BENIGN)}  (must be 0)")
    print(f"substring-MISSED cries the backstop adds: {caught}/{len(sub_missed)} "
          f"= {100*caught//max(len(sub_missed),1)}%")
    print(f"blind-set UNION (substring OR backstop): {union}/{len(T.RED_TEAM_BLIND)} "
          f"= {100*union//len(T.RED_TEAM_BLIND)}%   (substring alone caught "
          f"{len(T.RED_TEAM_BLIND)-len(sub_missed)})")
    print(f"(crisis floor also flagged by semantics: {floor_extra}/{len(T.CRISIS_FLOOR)})")


if __name__ == "__main__":
    main()
