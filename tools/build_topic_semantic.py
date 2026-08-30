#!/usr/bin/env python3
"""Seal the TOPIC SEMANTIC model (data/topic_semantic.json) — a general distributional word->vector
table counted from the FIELD-RICH keeping, for topical similarity in retrieval.

WHY. Surface word-overlap cannot tell "raise hogs" (husbandry) from "hog cholera" (disease) — both
carry "hog" — so a tangential card can be served for a real how-to gap, and a stricter noun match then
wrongly rejects "honeybees" -> "beekeeping". The answer is DISTRIBUTIONAL: a word IS the company it
keeps in the keeping. "raise/keep/grow" sit among husbandry words; "cholera/treatment/disease" sit
elsewhere; "honeybee" and "beekeeping" sit together. Cosine of averaged word-vectors then separates
intent where surface overlap can't, and joins related forms where a strict match can't.

HOW. The SAME proven machinery as the crisis backstop (PPMI over the keeping, projected to K dims by a
fixed seeded +/-1 Johnson-Lindenstrauss matrix so the cosine survives, quantized int8), but:
  * sourced from the PRACTICAL / field card files (not bible+crisis), so the field vocabulary is
    actually covered ("cheese" was absent from the crisis model; here it is counted from ~519 cards);
  * NO crisis centroid and NO threshold — this is a general topical space, read by topical.similarity.
The crisis model is left untouched (its threshold is tuned for benign=0%); this is a separate artifact.

Deterministic: same keeping + same SEED -> same artifact. No LLM, no numpy — stdlib only. Tokenization
is imported from crisis_semantic so build and runtime agree exactly.

    PYTHONPATH=src python tools/build_topic_semantic.py [K]
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

from concordance import crisis_semantic as cs  # noqa: E402  the ONE tokenizer (build == runtime)

DATA = ROOT / "data"
SEED = 20260830
WINDOW = 5
MIN_COUNT = 5            # a word must appear in >= this many documents to earn a vector (stable, bounded)

# The field-rich sources, each (filename, cap-or-None). The practical vocabulary lives in these card
# files, NOT in bible+crisis. The two giants (taxonomy, source_cards) are capped for a tractable build
# on the small box; the cap still admits far more field vocabulary than the crisis model ever saw.
SOURCES = [
    ("bible_en.jsonl", 8000),          # a general-language backbone — CAPPED so 31k verses do not
                                       # dominate the doc count and skew shared verbs (a "raise" among
                                       # hogs must not be pulled toward "raise the dead")
    ("topical_cards.jsonl", None),
    ("source_spines.jsonl", None),
    ("survival_cards.jsonl", None),
    ("theory_cards.jsonl", None),
    ("systems_cards.jsonl", None),
    ("water_cards.jsonl", None),
    ("works_cards.jsonl", None),
    ("study_cards.jsonl", None),
    ("verified_cards.jsonl", None),
    ("witnesses.jsonl", None),
    ("web_cache.jsonl", None),
    ("taxonomy_cards.jsonl", 35000),
    ("source_cards.jsonl", 60000),     # the tortoise's public-domain manual excerpts — sampled
]                                       # (giants capped: the build runs beside the services on a 7.7GB box)


def _toks_of(name, line):
    if name == "bible_en.jsonl":
        try:
            return cs.content(json.loads(line).get("text", ""))
        except Exception:  # noqa: BLE001
            return []
    try:
        c = json.loads(line)
    except Exception:  # noqa: BLE001
        return []
    return cs.content((c.get("body") or c.get("text") or "") + " " + (c.get("title") or ""))


def docs():
    for name, cap in SOURCES:
        p = DATA / name
        if not p.exists():
            continue
        n = 0
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if cap and n >= cap:
                    break
                toks = _toks_of(name, line)
                if toks:
                    n += 1
                    yield toks


def build_ppmi():
    uni = Counter()
    kept = []
    for toks in docs():
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
    print(f"counting PPMI over the field-rich keeping (K={K}, seed={SEED})…", flush=True)
    vec = build_ppmi()
    print(f"  vocab {len(vec)}", flush=True)

    # fixed seeded +/-1 projection, regenerated per context word (never stored) — same as the crisis build
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

    peak = max((abs(x) for row in dense for x in row), default=1.0) or 1.0
    scale = peak / 127.0

    def q(row):
        return bytes((max(-127, min(127, round(x / scale))) & 0xFF) for x in row)

    table = b"".join(q(row) for row in dense)

    out = {
        "_note": "Topic semantic model — deterministic PPMI over the field-rich keeping, JL-projected, "
                 "int8. Built by tools/build_topic_semantic.py. Runtime: src/concordance/topical.py.",
        "K": K, "seed": SEED, "window": WINDOW, "min_count": MIN_COUNT,
        "scale": scale, "vocab": len(words), "words": words,
        "table_b64": base64.b64encode(table).decode("ascii"),
    }
    path = DATA / "topic_semantic.json"
    path.write_text(json.dumps(out), encoding="utf-8")
    mb = path.stat().st_size / 1e6
    print(f"\nsealed {path}  ({mb:.1f} MB, {len(words)} words × {K} dims int8)")


if __name__ == "__main__":
    main()
