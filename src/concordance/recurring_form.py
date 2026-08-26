"""Recurring form — the fascia measure as an engine primitive. See docs/FASCIA.md.

A verdict was never local: a claim is held in tension by everything it connects to. This module
measures that connective tissue — whether a thing shares a *recurring form* with others — the way
Matt's `fabric_routability.py` measures whether a net's pads route with few jumpers under
placement-locality. Two things share a recurring form when they share **rare** structure; a shared
generic feature is not a form. That rarity weighting (IDF) is the apophenia dial made precise, and it
is the lesson the OEIS attack forced (`eval/recurring_form/`): naive shared-feature counting is
swamped by features nearly everything has.

CONDUIT, not source. It surfaces connections that already exist among the signatures the caller
supplies — it generates none, and renders no verdict beyond the null-tested assay
(CONFIRMED / PLAUSIBLE / RESONANCE / COINCIDENCE). A form no better than a random pairing is
COINCIDENCE, by design: everything-connects rots into faces-in-clouds without the null test.

A *signature* is a set of structural primitives (strings). Where they come from is the caller's
representation problem; `sequence_signature` is one worked deriver (integer sequences, computed
exactly), the modality our corpus lets us compute — the rest is the standing frontier (FASCIA.md §6).
"""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Dict, List, Sequence, Set, Tuple

VERDICTS = ("CONFIRMED", "PLAUSIBLE", "RESONANCE", "COINCIDENCE")

Sig = Set[str]
Item = Tuple[str, Sig]  # (key, signature)


# --- rarity weighting: a shared rare primitive is a form; a shared generic one is not -------------
def idf_of(corpus: Sequence[Sig]) -> Dict[str, float]:
    """Inverse-document-frequency weight per primitive over a corpus of signatures."""
    n = len(corpus) or 1
    cnt: Dict[str, int] = {}
    for s in corpus:
        for p in set(s):
            cnt[p] = cnt.get(p, 0) + 1
    return {p: math.log(n / k) for p, k in cnt.items()}


def _weight(shared: Sig, idf: Dict[str, float]) -> float:
    return round(sum(idf.get(p, 0.0) for p in shared), 4)


def neighbors(key: str, target: Sig, corpus: Sequence[Item], *,
              idf: Dict[str, float] = None, top: int = 12) -> List[Dict]:
    """The recurring-form connections of `target` among `corpus`, ranked by rarity-weighted shared
    structure (strongest first). The item whose key == `key` is excluded (a thing is not its own
    neighbor). Each result names WHY it connects: the shared primitives, rarest first."""
    idf = idf if idf is not None else idf_of([s for _k, s in corpus])
    out: List[Dict] = []
    for k, s in corpus:
        if k == key:
            continue
        shared = set(target) & set(s)
        if not shared:
            continue
        w = _weight(shared, idf)
        if w > 0:
            out.append({"key": k, "weight": w,
                        "shared": sorted(shared, key=lambda p: -idf.get(p, 0.0))})
    out.sort(key=lambda r: -r["weight"])
    return out[:top]


def assay(key: str, target: Sig, corpus: Sequence[Item], *,
          trials: int = 500, seed: int = 1, top: int = 8) -> Dict:
    """Is `target`'s rarity-weighted connection to its top neighbours beyond chance? Permutation
    null: random members of the corpus, scored the same way. Returns the verdict, the score, the
    p-value, and the measured connections (so the reader sees the form, not just the label)."""
    sigs = [s for _k, s in corpus]
    idf = idf_of(sigs)
    nb = neighbors(key, target, corpus, idf=idf, top=top)
    score = round(sum(n["weight"] for n in nb), 4)

    rng = random.Random(seed)
    ge = 0
    for _ in range(max(1, trials)):
        rk, rs = rng.choice(corpus)
        rn = neighbors(rk, rs, corpus, idf=idf, top=top)
        if sum(n["weight"] for n in rn) >= score:
            ge += 1
    p = ge / max(1, trials)

    verdict = "COINCIDENCE"
    if score > 0:
        if p < 0.01:
            verdict = "CONFIRMED"
        elif p < 0.05:
            verdict = "PLAUSIBLE"
        elif p < 0.25:
            verdict = "RESONANCE"
    return {"verdict": verdict, "score": score, "p": round(p, 4),
            "family_size": len(nb), "neighbors": nb}


# --- one worked deriver: integer sequences (a linear recurrence IS eigenstructure in integers) ----
def _solve(matrix: List[List[int]], rhs: List[int]):
    """Exact Gaussian elimination over Fraction; None if singular."""
    n = len(matrix)
    a = [[Fraction(x) for x in row] + [Fraction(rhs[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        piv = next((r for r in range(col, n) if a[r][col] != 0), None)
        if piv is None:
            return None
        a[col], a[piv] = a[piv], a[col]
        pv = a[col][col]
        a[col] = [x / pv for x in a[col]]
        for r in range(n):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                a[r] = [x - f * y for x, y in zip(a[r], a[col])]
    return [a[i][n] for i in range(n)]


def linear_recurrence_order(terms: Sequence[int], maxd: int = 4):
    """Minimal order d (1..maxd) of a constant-coefficient linear recurrence that fits AND verifies
    on every remaining term, computed exactly. Returns (d, coeffs) or (0, None)."""
    t = list(terms)
    n = len(t)
    for d in range(1, maxd + 1):
        if n < 2 * d + 2:
            break
        m = [[t[i - j] for j in range(1, d + 1)] for i in range(d, 2 * d)]
        rhs = [t[i] for i in range(d, 2 * d)]
        c = _solve(m, rhs)
        if c is None:
            continue
        if all(sum(c[j - 1] * t[i - j] for j in range(1, d + 1)) == t[i] for i in range(2 * d, n)):
            return d, c
    return 0, None


def sequence_signature(terms: Sequence[int]) -> Sig:
    """A COMPUTED structural signature for an integer sequence — no keyword matching."""
    t = [int(x) for x in terms]
    prims: Sig = set()
    if len(t) < 8:
        return prims
    d, _c = linear_recurrence_order(t)
    if d:
        prims.add("linrec")
        prims.add(f"order_{d}")
    prims.add("all_positive" if all(x > 0 for x in t) else "has_nonpositive")
    if any(x < 0 for x in t):
        prims.add("has_negative")
    if any(x == 0 for x in t):
        prims.add("has_zero")
    if all(b >= a for a, b in zip(t, t[1:])):
        prims.add("monotonic_inc")
    if all(b > a for a, b in zip(t, t[1:])):
        prims.add("strict_inc")
    tail = [x for x in t[-8:] if x > 0]
    if len(tail) >= 4:
        ratios = [tail[i + 1] / tail[i] for i in range(len(tail) - 1)]
        r = sorted(ratios)[len(ratios) // 2]
        if max(ratios) - min(ratios) < 0.05 and r > 1.02:
            prims.add("exp_growth")
            prims.add("integer_ratio" if abs(r - round(r)) < 0.02 else "irrational_ratio")
        elif r < 1.02:
            prims.add("poly_or_slow_growth")
    if max(abs(x) for x in t) <= 3:
        prims.add("bounded_small")
    par = [x % 2 for x in t]
    if all(x == 0 for x in par):
        prims.add("all_even")
    elif all(x == 1 for x in par):
        prims.add("all_odd")
    elif all(par[i] != par[i + 1] for i in range(len(par) - 1)):
        prims.add("alternating_parity")
    return prims


__all__ = ["VERDICTS", "idf_of", "neighbors", "assay",
           "linear_recurrence_order", "sequence_signature"]
