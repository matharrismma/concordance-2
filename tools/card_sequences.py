#!/usr/bin/env python3
"""Card the foundational integer sequences — COMPUTED, public domain.

The sequences deck was pending: OEIS is CC-BY-NC-SA (non-commercial + share-alike), refused by the
license gate (on `corpus._DISALLOWED_SOURCE`). But the SEQUENCES THEMSELVES are mathematical facts —
the primes are the primes; Fibonacci is Fibonacci — computable deterministically from their classical
definitions, which are public domain. So we do not copy OEIS's compilation (its A-numbers, its edited
annotations); we COMPUTE the foundational sequences ourselves and card each with its common name, its
first terms, and its plain definition. `generated=False` in the project's sense: not authored by a
model, but derived by deterministic arithmetic — the same discipline as the-works.

Shelf `sequences` (the honest name; the OEIS shelf stays empty and the deck is rerouted here). Nested
under a sequences spine → the Floor of Discovery. Idempotent; re-runnable; no network, no dependency.

    python tools/card_sequences.py    # -> data/sequence_cards.jsonl (+1 spine)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_sequences"
SRC = "Computed — classical number theory (public domain)"
_slug = re.compile(r"[^a-z0-9]+")
N = 18   # terms per sequence — enough to identify, not a data dump


def _sk(s: str) -> str:
    return _slug.sub("_", s.lower()).strip("_")


# ── generators (each returns the first `n` terms) — verified against standard values ──────────────

def naturals(n): return list(range(1, n + 1))
def evens(n): return [2 * i for i in range(1, n + 1)]
def odds(n): return [2 * i - 1 for i in range(1, n + 1)]


def primes(n):
    out, c = [], 1
    while len(out) < n:
        c += 1
        if all(c % p for p in out if p * p <= c):
            out.append(c)
    return out


def _linrec(first, coeffs, n):
    """Linear recurrence: terms = `first`, then each = sum(coeffs[i]*prev[i])."""
    s = list(first)
    while len(s) < n:
        s.append(sum(c * s[-i - 1] for i, c in enumerate(coeffs)))
    return s[:n]


def fibonacci(n): return _linrec([0, 1], [1, 1], n)
def lucas(n): return _linrec([2, 1], [1, 1], n)
def tribonacci(n): return _linrec([0, 0, 1], [1, 1, 1], n)
def pell(n): return _linrec([0, 1], [2, 1], n)
def jacobsthal(n): return _linrec([0, 1], [1, 2], n)
def triangular(n): return [i * (i + 1) // 2 for i in range(1, n + 1)]
def squares(n): return [i * i for i in range(1, n + 1)]
def cubes(n): return [i ** 3 for i in range(1, n + 1)]
def tetrahedral(n): return [i * (i + 1) * (i + 2) // 6 for i in range(1, n + 1)]
def pentagonal(n): return [i * (3 * i - 1) // 2 for i in range(1, n + 1)]
def hexagonal(n): return [i * (2 * i - 1) for i in range(1, n + 1)]
def lazy_caterer(n): return [i * (i + 1) // 2 + 1 for i in range(0, n)]
def powers_of_two(n): return [2 ** i for i in range(n)]
def mersenne(n): return [2 ** i - 1 for i in range(1, n + 1)]
def factorial(n):
    out, f = [], 1
    for i in range(n):
        if i: f *= i
        out.append(f)
    return out
def double_factorial(n):
    out = []
    for k in range(n):
        p = 1
        while k > 1:
            p *= k; k -= 2
        out.append(p)
    return out


def catalan(n):
    out, c = [], 1
    for i in range(n):
        out.append(c)
        c = c * 2 * (2 * i + 1) // (i + 2)
    return out


def central_binomial(n):
    from math import comb
    return [comb(2 * i, i) for i in range(n)]


def motzkin(n):
    m = [1, 1]
    for k in range(2, n):
        m.append((m[-1] * (2 * k + 1) + m[-2] * (3 * k - 3)) // (k + 2))
    return m[:n]


def bell(n):
    row = [1]
    bells = [1]
    for _ in range(1, n):
        nxt = [row[-1]]
        for x in row:
            nxt.append(nxt[-1] + x)
        row = nxt
        bells.append(row[0])
    return bells[:n]


def partitions(n):
    p = [1] + [0] * (n - 1)
    for k in range(1, n):
        for i in range(k, n):
            p[i] += p[i - k]
    return p[:n]


def primorial(n):
    out, prod = [], 1
    for p in primes(n):
        prod *= p
        out.append(prod)
    return out


def perfect(n):
    """Even perfect numbers via Euclid–Euler: 2^(p-1)(2^p - 1) for Mersenne primes 2^p-1. Perfect
    numbers are extremely sparse, so the exponent search is BOUNDED (beyond ~p=31 the trial-division
    primality test is infeasible here); this returns the few that are cheaply computable, not `n`."""
    out, p = [], 1
    while len(out) < n and p < 32:
        p += 1
        m = 2 ** p - 1
        if all(m % q for q in range(2, int(m ** 0.5) + 1)):   # m prime
            out.append(2 ** (p - 1) * m)
    return out


def derangements(n):
    d = [1, 0]
    for k in range(2, n):
        d.append((k - 1) * (d[-1] + d[-2]))
    return d[:n]


SEQUENCES = [
    ("Natural numbers", "The counting numbers 1, 2, 3, … .", naturals),
    ("Even numbers", "The positive even numbers, 2n.", evens),
    ("Odd numbers", "The positive odd numbers, 2n−1.", odds),
    ("Prime numbers", "Integers > 1 divisible only by 1 and themselves.", primes),
    ("Fibonacci numbers", "F(n) = F(n−1) + F(n−2), from 0, 1.", fibonacci),
    ("Lucas numbers", "L(n) = L(n−1) + L(n−2), from 2, 1.", lucas),
    ("Tribonacci numbers", "T(n) = T(n−1) + T(n−2) + T(n−3), from 0, 0, 1.", tribonacci),
    ("Pell numbers", "P(n) = 2·P(n−1) + P(n−2), from 0, 1.", pell),
    ("Jacobsthal numbers", "J(n) = J(n−1) + 2·J(n−2), from 0, 1.", jacobsthal),
    ("Triangular numbers", "n(n+1)/2 — dots in a triangle.", triangular),
    ("Square numbers", "n² — dots in a square.", squares),
    ("Cubes", "n³.", cubes),
    ("Tetrahedral numbers", "n(n+1)(n+2)/6 — a triangular pyramid.", tetrahedral),
    ("Pentagonal numbers", "n(3n−1)/2.", pentagonal),
    ("Hexagonal numbers", "n(2n−1).", hexagonal),
    ("Lazy caterer numbers", "Most pieces from n straight cuts of a disc: n(n+1)/2 + 1.", lazy_caterer),
    ("Powers of two", "2ⁿ.", powers_of_two),
    ("Mersenne numbers", "2ⁿ − 1.", mersenne),
    ("Factorials", "n! = 1·2·…·n.", factorial),
    ("Double factorials", "n!! — the product of every other integer down to 1 or 2.", double_factorial),
    ("Catalan numbers", "C(2n,n)/(n+1) — countless combinatorial families.", catalan),
    ("Central binomial coefficients", "C(2n, n).", central_binomial),
    ("Motzkin numbers", "Paths, chords, and non-crossing partitions.", motzkin),
    ("Bell numbers", "The number of ways to partition a set of n elements.", bell),
    ("Partition numbers", "p(n) — the ways to write n as a sum of positive integers.", partitions),
    ("Primorials", "The product of the first n primes.", primorial),
    ("Perfect numbers", "Equal to the sum of their proper divisors (Euclid–Euler).", perfect),
    ("Derangements", "Permutations of n items leaving none fixed (subfactorial).", derangements),
]


def main() -> int:
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    spine = {
        "id": SPINE, "kind": "reference", "title": "The foundational integer sequences",
        "body": ("The integer sequences the whole of number theory keeps returning to — the primes, "
                 "Fibonacci, Catalan, the partitions, and more — each computed from its classical "
                 "definition, not copied from any database. A spine of the Floor of Discovery."),
        "source": {"label": SRC, "url": "", "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["sequences", "integer sequences", "number theory", "mathematics", "spine"],
        "subject": "the foundational integer sequences",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the number-line's own recurring forms, a spine of the Floor"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "sequence_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n", encoding="utf-8")

    n = 0
    tmp = out / "sequence_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for name, definition, gen in SEQUENCES:
            terms = gen(N)
            preview = ", ".join(str(t) for t in terms)
            body = f"{name}: {preview}, … — {definition}"
            card = {
                "id": f"card_seq_{_sk(name)}", "kind": "reference", "title": name, "body": body,
                "source": {"label": SRC, "url": "", "domain": "mathematics", "authority_tier": "reference"},
                "shelf": "sequences", "box": "source",
                "bands": [_sk(name).replace("_", " "), "sequence", "integer sequence", "number theory"],
                "subject": name,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": "a foundational integer sequence"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"terms": terms, "definition": definition, "computed": True},
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    import os
    os.replace(tmp, out / "sequence_cards.jsonl")
    print(f"carded {n} foundational integer sequences (computed, public domain) "
          f"-> data/sequence_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
