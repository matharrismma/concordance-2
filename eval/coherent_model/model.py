#!/usr/bin/env python3
"""
The coherent model's SEMANTIC LAYER — one reusable, deterministic distributional model built from the
keeping by counting alone (PPMI co-occurrence). No neural net, no training, fully auditable. Shared by
every coherent-model probe so they compose on ONE model (the one-body principle), not several.

Public:
  build(docs, window=0, min_count=8)  -> Model     (docs = iterable of token-lists)
  Model.cos(w1, w2)                    -> float      cosine between two words
  Model.neighbors(w, k)                -> [(w, s)]   nearest words by meaning
  Model.centroid(tokens)               -> dict       the mean PPMI vector of a bag of words
  Model.echo(tokens_a, tokens_b)       -> float      SEMANTIC echo between two units (centroid cosine)
  stem(w), content(text)               -> tokenization used everywhere
  bible_docs(), card_docs(paths, cap)  -> corpus loaders
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
_STOP = set(("the a an of to and but in on for is are was were be his her my your their our its he she "
             "it they we you i o thou thy thee that this these those which who whom with as from by at "
             "into unto out up down shall will not no nor them him us me all there so then when have has "
             "had do did whether or thing things came come go went upon also let us may might would "
             "should could yet if because therefore now even said say says loud great one man men "
             "children people day days made make thus behold saying").split())


def stem(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    for s in ("ing", "eth", "est", "ed"):
        if w.endswith(s) and len(w) - len(s) >= 3:
            return w[: -len(s)]
    # English plural rule for -es: strip 'es' only after a sibilant (boxes→box, churches→church);
    # otherwise strip just 's' (cares→care, trees→tree) — never 'cares'→'car' (a stemmer collision).
    if w.endswith("es") and len(w) - 2 >= 3:
        return w[:-2] if (w[-3] in "sxzo" or w.endswith(("ches", "shes"))) else w[:-1]
    if w.endswith("s") and len(w) - 1 >= 3:
        return w[:-1]
    return w


def content(text):
    return [s for s in (stem(w) for w in (text or "").split()) if s and s not in _STOP and len(s) >= 3]


class Model:
    def __init__(self, vec, uni, ndocs):
        self.vec = vec            # word -> {context_word: ppmi}
        self.uni = uni            # unigram doc-frequency
        self.ndocs = ndocs
        self._norm = {w: math.sqrt(sum(x * x for x in v.values())) or 1.0 for w, v in vec.items()}

    def cos(self, a, b):
        a, b = stem(a), stem(b)
        va, vb = self.vec.get(a), self.vec.get(b)
        if not va or not vb:
            return 0.0
        dot = sum(va[k] * vb[k] for k in va.keys() & vb.keys())
        return dot / (self._norm[a] * self._norm[b])

    def centroid(self, tokens):
        acc = defaultdict(float)
        n = 0
        for t in tokens:
            v = self.vec.get(stem(t))
            if v:
                n += 1
                for k, x in v.items():
                    acc[k] += x
        if n:
            for k in acc:
                acc[k] /= n
        return acc

    @staticmethod
    def _cos_raw(a, b):
        if not a or not b:
            return 0.0
        dot = sum(a[k] * b[k] for k in a.keys() & b.keys())
        na = math.sqrt(sum(x * x for x in a.values()))
        nb = math.sqrt(sum(x * x for x in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def echo(self, ta, tb):
        return self._cos_raw(self.centroid(ta), self.centroid(tb))

    def align(self, ta, tb):
        """SOFT ALIGNMENT — each content word's best cross-match, symmetrized. Captures the specific
        word-to-word synonym correspondences of parallelism (heavens↔expanse), where centroid cosine
        only sees the general topical cloud."""
        A = [t for t in {stem(x) for x in ta} if t in self.vec]
        B = [t for t in {stem(x) for x in tb} if t in self.vec]
        if not A or not B:
            return 0.0
        ab = sum(max(self.cos(a, b) for b in B) for a in A) / len(A)
        ba = sum(max(self.cos(b, a) for a in A) for b in B) / len(B)
        return (ab + ba) / 2

    def neighbors(self, w, k=8):
        w = stem(w)
        if w not in self.vec:
            return []
        return sorted(((self.cos(w, o), o) for o in self.vec if o != w), reverse=True)[:k]


def build(docs, window=0, min_count=8):
    """docs: iterable of token-lists. window=0 → co-occur within the whole doc; window=k → within ±k."""
    uni = Counter()
    cooc = defaultdict(Counter)
    total = 0
    kept = []
    for toks in docs:
        if toks:
            uni.update(set(toks))
            kept.append(toks)
    vocab = {w for w, n in uni.items() if n >= min_count}
    ndocs = 0
    for toks in kept:
        ts = [t for t in toks if t in vocab]
        if not ts:
            continue
        ndocs += 1
        if window <= 0:
            s = set(ts)
            for a in s:
                for b in s:
                    if a != b:
                        cooc[a][b] += 1
                        total += 1
        else:
            for i, a in enumerate(ts):
                for j in range(max(0, i - window), min(len(ts), i + window + 1)):
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
    return Model(vec, uni, ndocs)


def bible_docs():
    for line in open(DATA / "bible_en.jsonl", encoding="utf-8"):
        yield content(json.loads(line).get("text", ""))


def card_docs(names, cap_per_file=20000):
    """Stream token-lists from card jsonl files (body field). cap_per_file bounds a huge file."""
    for name in names:
        p = DATA / name
        if not p.exists():
            continue
        n = 0
        for line in open(p, encoding="utf-8"):
            if n >= cap_per_file:
                break
            try:
                c = json.loads(line)
            except Exception:
                continue
            body = c.get("body") or c.get("text") or ""
            toks = content(body)
            if toks:
                n += 1
                yield toks
