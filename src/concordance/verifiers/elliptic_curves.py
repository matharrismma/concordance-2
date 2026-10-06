"""Elliptic curves over Q — the L-value door for the Birch and Swinnerton-Dyer stick (tick stick, 2026-10-05).

What the engine can honestly compute for a curve E/Q given by its a-invariants [a1, a2, a3, a4, a6] and its
conductor N (Cremona's tables are the source for the famous curves):

  * a_p for good primes by counting points on the reduction mod p (a1 ≠ 0 / a3 ≠ 0 handled by completing the
    square: #E(F_p) = p + 1 - a_p with a_p = -Σ_x χ((2y+a1x+a3)² discriminant)); for a multiplicative bad prime
    p ≥ 5 (p ‖ N), a_p = +1 split / -1 non-split by the Legendre symbol of -c6; additive primes (p² | N) a_p = 0.
    Bad primes 2 and 3 are DECLINED here (Tate's algorithm is not implemented): the curve must have N coprime to 6.
  * a_n multiplicatively; L(E, 1) by the approximate functional equation
        L(E,1) = Σ a_n/n [ e^{-2πn/(A√N)} + w·e^{-2πnA/√N} ]
    whose value must not depend on the free parameter A — so the root number w the caller supplies is CHECKED
    (A = 1 and A = 1.3 must agree), never trusted; L'(E,1) when w = -1 by 2·Σ a_n/n·E1(2πn/√N).
  * the analytic rank bound these give: L(E,1) ≠ 0 → analytic rank 0 → rank E(Q) = 0 (Kolyvagin 1989);
    L(E,1) = 0, L'(E,1) ≠ 0 → analytic rank 1 → rank 1 (Gross–Zagier 1986 + Kolyvagin 1989). Analytic rank ≥ 2 is
    reported as "≥ 2 numerically" — no theorem settles the algebraic rank there, and the verifier says so.

ELLIPTIC_VERIFY packet shape:
    {"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1,
     "claimed_L1": 0.253842, "claimed_analytic_rank": 0}            (either claim, or both)

Checks: elliptic_curves.l_value — L(E,1) (and L'(E,1) for w = -1) against the claims, with the rank consequence
and the theorem it rests on. Deterministic; sources: Cohen, A Course in Computational Algebraic Number Theory
§7 (the AFE); Kolyvagin, Gross–Zagier as cited in the result.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from .base import VerifierResult, clamp_tol, confirm, dispatch, error, mismatch, na


def _primes(n: int) -> List[int]:
    s = bytearray([1]) * (n + 1)
    s[0] = s[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]


def _legendre(a: int, p: int) -> int:
    a %= p
    if a == 0:
        return 0
    return 1 if pow(a, (p - 1) // 2, p) == 1 else -1


def _ap_good(p: int, a1: int, a2: int, a3: int, a4: int, a6: int) -> int:
    """a_p = p + 1 - #E(F_p). For ODD p, #E(F_p) = 1 (infinity) + Σ_x (1 + χ(D(x))) with
    D(x) = (a1 x + a3)² + 4(x³ + a2 x² + a4 x + a6) — the discriminant in y after completing the square.
    At p = 2 that square-completion (dividing by 2) is invalid, so count the points of the Weierstrass equation
    directly: y² + a1 x y + a3 y = x³ + a2 x² + a4 x + a6 over F_2, plus the point at infinity."""
    if p == 2:
        cnt = sum(1 for x in (0, 1) for y in (0, 1)
                  if (y * y + a1 * x * y + a3 * y - (x ** 3 + a2 * x * x + a4 * x + a6)) % 2 == 0)
        return 2 + 1 - (cnt + 1)                          # a_2 = 3 - #E(F_2)
    total = 0
    for x in range(p):
        d = ((a1 * x + a3) ** 2 + 4 * (x * x * x + a2 * x * x + a4 * x + a6)) % p
        total += _legendre(d, p)
    return -total


def _c4_c6(a1, a2, a3, a4, a6):
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    c4 = b2 * b2 - 24 * b4
    c6 = -b2 ** 3 + 36 * b2 * b4 - 216 * b6
    disc = -b2 * b2 * b8 - 8 * b4 ** 3 - 27 * b6 * b6 + 9 * b2 * b4 * b6
    return c4, c6, disc


def _an(M: int, N: int, ainv) -> List[int]:
    a1, a2, a3, a4, a6 = ainv
    c4, c6, disc = _c4_c6(*ainv)
    ap: Dict[int, int] = {}
    for p in _primes(M):
        if N % p == 0:
            if (N // p) % p == 0:
                ap[p] = 0                                   # additive
            else:
                ap[p] = _legendre(-c6, p)                   # multiplicative: split (+1) or non-split (-1)
        else:
            ap[p] = _ap_good(p, a1, a2, a3, a4, a6)
    an = [0] * (M + 1)
    an[1] = 1
    for n in range(2, M + 1):
        m, p = n, 2
        while p * p <= m and m % p:
            p += 1
        if m % p:
            p = m
        k = 0
        while m % p == 0:
            m //= p
            k += 1
        if N % p == 0:
            apk = ap[p] ** k
        else:
            x0, x1 = 1, ap[p]
            for _ in range(k - 1):
                x0, x1 = x1, ap[p] * x1 - p * x0
            apk = x1
        an[n] = apk * an[m]
    return an


def _L1(an: List[int], N: int, w: int, A: float) -> float:
    s = 0.0
    c = 2 * math.pi / math.sqrt(N)
    for n in range(1, len(an)):
        if an[n]:
            s += an[n] / n * (math.exp(-c * n / A) + w * math.exp(-c * n * A))
    return s


def _Lprime1(an: List[int], N: int) -> float:
    import mpmath as mp
    c = 2 * math.pi / math.sqrt(N)
    s = mp.mpf(0)
    for n in range(1, len(an)):
        if an[n]:
            s += mp.mpf(an[n]) / n * mp.e1(c * n)
    return float(2 * s)


def verify_l_value(spec: Dict[str, Any]) -> VerifierResult:
    name = "elliptic_curves.l_value"
    try:
        ainv = [int(x) for x in spec.get("a_invariants")]
        N = int(spec.get("conductor"))
        w = int(spec.get("root_number"))
    except (TypeError, ValueError):
        return error(name, "a_invariants (five integers), conductor (an integer) and root_number (±1) are required")
    if len(ainv) != 5 or w not in (-1, 1) or N < 11:
        return error(name, "a_invariants must be [a1,a2,a3,a4,a6]; root_number must be +1 or -1; the conductor is at least 11")
    if N % 2 == 0 or N % 3 == 0:
        return na(name, f"conductor {N} is divisible by 2 or 3: the reduction type at 2 and 3 (Tate's algorithm) is not held here — declined, not judged")
    if N > 200000:
        return error(name, f"conductor {N} is beyond this door (≤ 200000)")
    c4, c6, disc = _c4_c6(*ainv)
    if disc == 0:
        return error(name, "the discriminant is zero: not an elliptic curve")
    M = int(10 * math.sqrt(N)) + 200
    try:
        an = _an(M, N, ainv)
        L1a, L1b = _L1(an, N, w, 1.0), _L1(an, N, w, 1.3)
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failed: {type(e).__name__}: {e}")
    data: Dict[str, Any] = {"curve": {"a_invariants": ainv, "conductor": N, "c4": c4, "c6": c6, "discriminant": disc},
                            "root_number": w, "terms": M, "L1": L1a, "L1_other_cutoff": L1b,
                            "a_p": {str(p): an[p] for p in _primes(30)}}
    # the functional equation's consistency check: the AFE value must not move with the cutoff
    if abs(L1a - L1b) > 1e-6 * max(1.0, abs(L1a)):
        return mismatch(name, f"the L-value depends on the cutoff ({L1a:.8f} vs {L1b:.8f}): the root number {w:+d} is wrong "
                              f"for this curve (or the conductor is)", data)
    L1 = L1a
    rank_bound: Any
    if abs(L1) > 1e-8:
        rank_bound, theorem = 0, "L(E,1) ≠ 0 ⇒ rank E(Q) = 0 (Kolyvagin 1989, with Gross–Zagier 1986)"
    elif w == -1:
        Lp = _Lprime1(an, N)
        data["Lprime1"] = Lp
        if abs(Lp) > 1e-8:
            rank_bound, theorem = 1, "L(E,1) = 0, L'(E,1) ≠ 0 ⇒ rank E(Q) = 1 (Gross–Zagier 1986 + Kolyvagin 1989)"
        else:
            rank_bound, theorem = ">=3 numerically", "analytic rank ≥ 3 by the vanishing found here; no theorem settles the algebraic rank"
    else:
        rank_bound, theorem = ">=2 numerically", "L(E,1) = 0 with w = +1: analytic rank ≥ 2 numerically; no theorem settles the algebraic rank"
    data["analytic_rank"] = rank_bound
    data["theorem"] = theorem
    tol = clamp_tol(spec, "tolerance_relative", 1e-4)
    problems = []
    if spec.get("claimed_L1") is not None:
        try:
            cl = float(spec["claimed_L1"])
        except (TypeError, ValueError):
            return error(name, "claimed_L1 must be numeric")
        data["claimed_L1"] = cl
        if abs(L1 - cl) > max(1e-6, tol * abs(L1)):
            problems.append(f"L(E,1) = {L1:.6f}, claimed {cl:.6f}")
    if spec.get("claimed_analytic_rank") is not None:
        try:
            cr = int(spec["claimed_analytic_rank"])
        except (TypeError, ValueError):
            return error(name, "claimed_analytic_rank must be an integer")
        data["claimed_analytic_rank"] = cr
        if isinstance(rank_bound, int):
            if cr != rank_bound:
                problems.append(f"analytic rank {rank_bound}, claimed {cr}")
        elif cr < 2:
            problems.append(f"analytic rank {rank_bound}, claimed {cr}")
    if spec.get("claimed_L1") is None and spec.get("claimed_analytic_rank") is None:
        return na(name, "nothing claimed: give claimed_L1 and/or claimed_analytic_rank")
    if problems:
        return mismatch(name, "; ".join(problems), data)
    return confirm(name, f"L(E,1) = {L1:.6f} (cutoff-independent, so w = {w:+d} is right); analytic rank {rank_bound}; {theorem}", data)


_RULES = [
    (lambda ev: all(k in ev for k in ("a_invariants", "conductor", "root_number")), verify_l_value),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "ELLIPTIC_VERIFY", _RULES, domain="elliptic_curves", none_reason="no ELLIPTIC_VERIFY artifacts present")
