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



def real_period(ainv: List[int]) -> Dict[str, Any]:
    """Omega_E, the real period of the Neron differential, COMPUTED: on the short model Y^2 = X^3 - 27 c4 X - 54 c6
    (X = 36x + 3 b2, Y = 108(2y + a1 x + a3), so dX/(2Y) = omega/6), the integral 2 int_{e1}^{inf} dX / sqrt(f) over the
    unbounded real component equals 2 * Omega_short, hence Omega = 3 * that integral, times 2 when the discriminant is
    positive (two real components; the BSD period integrates over all of E(R)). Checked against Cremona's tables for
    11a1, 37a1, 389a1 and 5077a1 in tests/test_bsd_formula.py."""
    from mpmath import mp, mpf, quad, sqrt, polyroots, inf, re as _re
    c4, c6, disc = _c4_c6(*ainv)
    saved = mp.dps
    try:
        mp.dps = 25
        roots = polyroots([1, 0, -27 * c4, -54 * c6])
        real = sorted([_re(r) for r in roots if abs(r.imag) < mpf(10) ** -10])
        e1 = real[-1]
        f = lambda X: 1 / sqrt(X ** 3 - 27 * c4 * X - 54 * c6)      # noqa: E731
        I = 2 * quad(f, [e1, inf])
        comps = 2 if disc > 0 else 1
        omega = 3 * _re(I) * comps
        return {"omega": float(omega), "components": comps, "largest_real_root_short_model": float(e1)}
    finally:
        mp.dps = saved


def verify_bsd_formula(spec: Dict[str, Any]) -> VerifierResult:
    """THE FULL BIRCH-SWINNERTON-DYER FORMULA ON ONE CURVE (2026-10-09, the Millennium loop). For analytic rank 0:
    L(E,1) / Omega = |Sha| * prod c_p / |E(Q)_tors|^2; for rank 1: L'(E,1) / Omega = |Sha| * prod c_p * R / |T|^2.
    COMPUTED here: L(E,1) or L'(E,1) by the approximate functional equation, Omega by integration (real_period).
    CITED inputs (never computed here; the spec must name their source): tamagawa_product, torsion_order, sha_order
    (default 1) and, for rank 1, regulator. The check is the equality of the two sides to the AFE's precision; a
    curve of analytic rank >= 2 is DECLINED (no theorem carries it). Honest about what it is: for rank 0 and 1 the
    formula is a THEOREM for these curves once Sha is known (Kolyvagin; Gross-Zagier), so a confirmed instance is a
    sealed link of a proven case, with its cited inputs named.
      ELLIPTIC_VERIFY: {"a_invariants": [0,-1,1,-10,-20], "conductor": 11, "root_number": 1, "tamagawa_product": 5,
                        "torsion_order": 5, "sha_order": 1, "inputs_source": "Cremona's tables / LMFDB 11.a3",
                        "claimed_bsd_holds": true}"""
    name = "elliptic_curves.bsd_formula"
    try:
        ainv = [int(x) for x in spec.get("a_invariants")]
        N = int(spec.get("conductor"))
        w = int(spec.get("root_number"))
        cp = int(spec.get("tamagawa_product"))
        tors = int(spec.get("torsion_order"))
        sha = int(spec.get("sha_order", 1))
    except (TypeError, ValueError):
        return error(name, "a_invariants, conductor, root_number, tamagawa_product and torsion_order (integers) are required; sha_order defaults to 1")
    if spec.get("claimed_bsd_holds") is None:
        return na(name, "claim claimed_bsd_holds")
    if len(ainv) != 5 or w not in (-1, 1) or N < 11 or cp < 1 or tors < 1 or sha < 1:
        return error(name, "a_invariants must be five integers; root_number +1/-1; conductor >= 11; tamagawa_product, torsion_order, sha_order >= 1")
    if N % 2 == 0 or N % 3 == 0:
        return na(name, f"conductor {N} is divisible by 2 or 3: the reduction type at 2 and 3 is not held here — declined")
    if N > 200000:
        return error(name, f"conductor {N} is beyond this door (<= 200000)")
    source = str(spec.get("inputs_source") or "").strip()
    if not source:
        return error(name, "inputs_source is required: the Tamagawa product, torsion and Sha are CITED inputs, never computed here")
    c4, c6, disc = _c4_c6(*ainv)
    if disc == 0:
        return error(name, "the discriminant is zero: not an elliptic curve")
    M = int(10 * math.sqrt(N)) + 200
    try:
        an = _an(M, N, ainv)
        L1a, L1b = _L1(an, N, w, 1.0), _L1(an, N, w, 1.3)
        if abs(L1a - L1b) > 1e-6 * max(1.0, abs(L1a)):
            return mismatch(name, f"the L-value depends on the cutoff ({L1a:.8f} vs {L1b:.8f}): the root number or conductor is wrong", {})
        per = real_period(ainv)
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failed: {type(e).__name__}: {e}")
    omega = per["omega"]
    data: Dict[str, Any] = {"curve": {"a_invariants": ainv, "conductor": N, "c4": c4, "c6": c6, "discriminant": disc},
                            "computed": {"L1": L1a, "omega": omega, "real_components": per["components"]},
                            "cited": {"tamagawa_product": cp, "torsion_order": tors, "sha_order": sha, "source": source}}
    if abs(L1a) > 1e-8:
        rank = 0
        left = L1a / omega
        right = sha * cp / (tors ** 2)
        data["formula"] = "L(E,1) / Omega = |Sha| * prod c_p / |T|^2"
        data["theorem"] = "rank 0: L(E,1) != 0 => rank E(Q) = 0 and Sha finite (Kolyvagin 1989); the formula is then a theorem for this curve"
    elif w == -1:
        Lp = _Lprime1(an, N)
        data["computed"]["Lprime1"] = Lp
        if abs(Lp) <= 1e-8:
            return na(name, "L(E,1) = 0 and L'(E,1) = 0 numerically: analytic rank >= 3, no theorem carries the formula — declined")
        try:
            R = float(spec.get("regulator"))
        except (TypeError, ValueError):
            return error(name, "rank 1 needs the regulator (the canonical height of a generator) as a cited input")
        rank = 1
        data["cited"]["regulator"] = R
        left = Lp / omega
        right = sha * cp * R / (tors ** 2)
        data["formula"] = "L'(E,1) / Omega = |Sha| * prod c_p * R / |T|^2"
        data["theorem"] = "rank 1: L(E,1) = 0, L'(E,1) != 0 => rank E(Q) = 1 and Sha finite (Gross-Zagier 1986, Kolyvagin 1989); the formula is then a theorem for this curve"
    else:
        return na(name, "L(E,1) = 0 with root number +1: analytic rank >= 2, no theorem carries the formula — declined")
    data["rank"] = rank
    data["left_side"] = left
    data["right_side"] = right
    tol = clamp_tol(spec, "tolerance_relative", 1e-4)
    holds = abs(left - right) <= tol * max(abs(right), 1e-12)
    data["bsd_holds"] = holds
    if bool(spec.get("claimed_bsd_holds")) != holds:
        return mismatch(name, f"{data['formula']}: left {left:.8f}, right {right:.8f} ({'equal' if holds else 'NOT equal'} to {tol:g}); "
                              f"claimed {bool(spec.get('claimed_bsd_holds'))}", data)
    return confirm(name, f"{data['formula']} holds for this curve to {tol:g}: {left:.8f} = {right:.8f} (L computed by the AFE, "
                         f"Omega = {omega:.10f} computed by integration; Tamagawa {cp}, torsion {tors}, Sha {sha}"
                         f"{', regulator ' + format(data['cited']['regulator'], '.10f') if rank == 1 else ''} cited from {source}); {data['theorem']}", data)


_RULES = [
    (lambda ev: all(k in ev for k in ("a_invariants", "conductor", "root_number", "tamagawa_product", "torsion_order")), verify_bsd_formula),
    (lambda ev: all(k in ev for k in ("a_invariants", "conductor", "root_number")) and "tamagawa_product" not in ev, verify_l_value),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "ELLIPTIC_VERIFY", _RULES, domain="elliptic_curves", none_reason="no ELLIPTIC_VERIFY artifacts present")
