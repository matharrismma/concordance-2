"""Independently-checkable certificates — the bbchallenge (FAR/WFAR/CTL) pattern for the engine.

A verifier can CONFIRM a verdict; a CERTIFICATE lets a SEPARATE, minimal checker re-confirm it
without trusting — or even re-running — the verifier. Asymmetric by design: producing the witness
may be hard (search, factoring), re-checking it is cheap and self-contained. The trust anchor moves
from "the verifier said so" to "here is a witness anyone can check." This is how bbchallenge sealed
BB(5): every machine's (non-)halting carried a certificate a small Coq-checked decider re-verified.

PROTOTYPE domain: PRIMALITY (number_theory.primality).
  * composite n  -> witness is a nontrivial factor d; the check is one modulo (n % d == 0, 1<d<n).
  * prime n      -> a Pratt/Lucas certificate: a base a and the prime factorization of n-1, each
                    factor recursively certified prime; the check is modular exponentiation alone
                    (Lucas 1876; Pratt 1975 showed primality is in NP via exactly this witness).

The checker below NEVER calls the producer or any primality routine — it re-derives the verdict from
the witness. A FORGED certificate (a lie) fails the checker; that is the whole point. Pure arithmetic,
no I/O, no deps — a tiny trust anchor, like a Coq-checked decider.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple

SCHEMA = 1


@dataclass(frozen=True)
class Certificate:
    kind: str                 # "primality"
    claim: Dict[str, Any]     # {"n": int, "verdict": "prime" | "composite"}
    witness: Dict[str, Any]   # composite: {"factor": d}; prime: {"base": a, "factors": [[q, subcert], ...]}
    schema: int = SCHEMA


def to_dict(cert: Certificate) -> Dict[str, Any]:
    """A plain JSON-able dict — the shape that rides in VerifierResult.data and across a seal."""
    return asdict(cert)


def from_dict(d: Dict[str, Any]) -> Certificate:
    return Certificate(kind=str(d["kind"]), claim=dict(d["claim"]), witness=dict(d["witness"]),
                       schema=int(d.get("schema", SCHEMA)))


# ── the producer (may be slow; NOT the trust anchor) ────────────────────────────────────────────
def _smallest_factor(n: int) -> int:
    if n % 2 == 0:
        return 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return i
        i += 2
    return n                      # n is prime


def _distinct_prime_factors(m: int) -> List[int]:
    """The distinct prime factors of m (m >= 1), peeled smallest-first."""
    out: List[int] = []
    while m > 1:
        f = _smallest_factor(m)
        out.append(f)
        while m % f == 0:
            m //= f
    return out


def _lucas_base(n: int, qs: List[int]) -> int:
    """A base a proving n prime: a^(n-1) == 1 and a^((n-1)//q) != 1 (mod n) for each prime q | n-1."""
    for a in range(2, n):
        if pow(a, n - 1, n) != 1:
            continue
        if all(pow(a, (n - 1) // q, n) != 1 for q in qs):
            return a
    raise ValueError(f"no Lucas base for {n} (not prime?)")


def certify_primality(n: int) -> Certificate:
    """Produce a certificate for the primality verdict of n (n >= 2). Hard part: factoring / search."""
    if n < 2:
        raise ValueError("primality certificates are for n >= 2")
    d = _smallest_factor(n)
    if d != n:
        return Certificate("primality", {"n": n, "verdict": "composite"}, {"factor": d})
    if n == 2:
        return Certificate("primality", {"n": 2, "verdict": "prime"}, {"base": 1, "factors": []})
    qs = _distinct_prime_factors(n - 1)
    a = _lucas_base(n, qs)
    factors = [[q, to_dict(certify_primality(q))] for q in qs]
    return Certificate("primality", {"n": n, "verdict": "prime"}, {"base": a, "factors": factors})


# ── the INDEPENDENT checker (the trust anchor — pure, minimal, recursive) ─────────────────────────
def check(cert: Any) -> Tuple[bool, str]:
    """Re-confirm a certificate WITHOUT trusting or re-running the producer. Returns (ok, detail).

    composite -> 1 < factor < n and n % factor == 0.
    prime     -> Lucas: a^(n-1) == 1 (mod n); a^((n-1)//q) != 1 for each listed prime q; every listed
                 factor is itself a valid PRIME certificate; and the listed primes GENERATE n-1 (none
                 omitted — the completeness that makes Lucas a proof). Any gap -> not ok.

    No call to certify_primality or any primality test — only modular exponentiation and recursion on
    the given witness. A forged certificate (wrong factor, bad base, a missing prime divisor of n-1,
    a composite masquerading as prime) fails here.
    """
    c = cert if isinstance(cert, Certificate) else from_dict(cert)
    if c.kind != "primality":
        return False, f"unknown certificate kind {c.kind!r}"
    try:
        n = int(c.claim["n"])
        verdict = str(c.claim["verdict"])
    except Exception:  # noqa: BLE001
        return False, "malformed claim"
    if n < 2:
        return False, "n < 2 is neither prime nor composite"

    if verdict == "composite":
        d = c.witness.get("factor")
        if not isinstance(d, int) or isinstance(d, bool) or not (1 < d < n) or n % d != 0:
            return False, f"not a nontrivial factor of {n}: {d!r}"
        return True, f"{n} = {d} x {n // d} (composite)"

    if verdict == "prime":
        if n == 2:
            return True, "2 is prime (base case)"
        a = c.witness.get("base")
        factors = c.witness.get("factors")
        if not isinstance(a, int) or isinstance(a, bool) or not isinstance(factors, list):
            return False, "malformed prime witness"
        qs: List[int] = []
        for item in factors:
            try:
                q, sub = int(item[0]), item[1]
            except Exception:  # noqa: BLE001
                return False, "malformed factor entry"
            ok, why = check(sub)                      # the factor must itself be a certified prime
            if not ok:
                return False, f"factor {q} not certified prime: {why}"
            s = from_dict(sub)
            if int(s.claim["n"]) != q or str(s.claim["verdict"]) != "prime":
                return False, f"factor entry {q} does not certify its own primality"
            qs.append(q)
        # completeness: the listed primes must be EXACTLY the prime divisors of n-1 (none omitted)
        m = n - 1
        for q in qs:
            if q < 2 or m % q != 0:
                return False, f"{q} does not divide n-1"
            while m % q == 0:
                m //= q
        if m != 1:
            return False, "listed factors do not generate n-1 — a prime divisor is missing"
        # Lucas: a has order exactly n-1 in the multiplicative group, so n-1 | |group| = n-1 => n prime
        if pow(a, n - 1, n) != 1:
            return False, "a^(n-1) != 1 (mod n)"
        for q in set(qs):
            if pow(a, (n - 1) // q, n) == 1:
                return False, f"a^((n-1)/{q}) == 1 (mod n): base {a} is not a witness"
        return True, f"{n} is prime by Lucas (base {a}, prime factors of n-1 = {sorted(set(qs))})"

    return False, f"unknown verdict {verdict!r}"
