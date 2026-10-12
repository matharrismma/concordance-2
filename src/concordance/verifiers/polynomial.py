"""The Rational Root Theorem — the rational roots of an integer-coefficient polynomial.

A polynomial a_n x^n + … + a_1 x + a_0 with integer coefficients has every rational root p/q (in
lowest terms) with p | a_0 and q | a_n — the Rational Root Theorem. This verifier ENUMERATES those
candidates and tests each by EXACT (fractions.Fraction) evaluation, so it returns the COMPLETE set of
rational roots — found, never guessed — and checks a claim against it. Irrational and complex roots are
out of scope (the theorem speaks only to RATIONAL roots): a claim that the rational roots are {…} is a
claim about that set, and a single "x is a root" is checked by exact evaluation.

POLY_VERIFY shape (coeffs are integers, highest degree first):
    {"coeffs": [1, -5, 6], "claimed_rational_roots": [2, 3]}       # the COMPLETE set of rational roots
    {"coeffs": [2, -1, -3], "claimed_rational_roots": ["3/2", -1]} # fractions as "p/q" strings or ints
    {"coeffs": [1, -5, 6], "claimed_root": 2}                      # a single claimed root

Pure arithmetic, no sympy: exact, deterministic, and it can never emit a false HOLDS — a wrong set or a
non-root MISMATCHES.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List

from .base import VerifierResult, confirm, dispatch, error, mismatch, na


def _divisors(n: int) -> List[int]:
    n = abs(int(n))
    return [d for d in range(1, n + 1) if n % d == 0]


def _poly_eval(coeffs: List[int], x: Fraction) -> Fraction:
    """P(x) by Horner's method, coefficients highest-degree-first — exact."""
    acc = Fraction(0)
    for c in coeffs:
        acc = acc * x + c
    return acc


def rational_roots(coeffs: List[int]) -> List[Fraction]:
    """The COMPLETE set of rational roots, by the Rational Root Theorem + exact testing."""
    c = [int(v) for v in coeffs]
    roots = set()
    while len(c) > 1 and c[-1] == 0:        # a zero constant term: 0 is a root; factor out x and reduce
        roots.add(Fraction(0))
        c = c[:-1]
    if len(c) <= 1 or c[0] == 0:
        return sorted(roots)
    a_n, a_0 = c[0], c[-1]
    for p in _divisors(a_0):                # RRT: p | a_0, q | a_n
        for q in _divisors(a_n):
            for cand in (Fraction(p, q), Fraction(-p, q)):
                if _poly_eval(c, cand) == 0:
                    roots.add(cand)
    return sorted(roots)


def _fmt(fr: Fraction) -> str:
    return str(fr.numerator) if fr.denominator == 1 else f"{fr.numerator}/{fr.denominator}"


def _as_fraction(v: Any) -> Fraction:
    if isinstance(v, str):
        return Fraction(v)
    if isinstance(v, bool):                 # guard: bool is an int subclass
        raise ValueError("boolean is not a number")
    return Fraction(v).limit_denominator(10 ** 9) if isinstance(v, float) else Fraction(v)


def _coeffs(art: Dict[str, Any]) -> List[int]:
    coeffs = [int(v) for v in art["coeffs"]]
    if len(coeffs) < 2 or coeffs[0] == 0:
        raise ValueError("need a polynomial of degree >= 1 with a nonzero leading coefficient")
    return coeffs


def verify_rational_roots(art: Dict[str, Any]) -> VerifierResult:
    name = "polynomial.rational_roots"
    if not isinstance(art.get("coeffs"), list) or art.get("claimed_rational_roots") is None:
        return na(name)
    try:
        coeffs = _coeffs(art)
        claimed = {_as_fraction(v) for v in art["claimed_rational_roots"]}
    except (TypeError, ValueError, ZeroDivisionError) as e:
        return error(name, f"bad polynomial or claimed roots: {e}")
    actual = set(rational_roots(coeffs))
    shown_a = ", ".join(_fmt(r) for r in sorted(actual)) or "none"
    shown_c = ", ".join(_fmt(r) for r in sorted(claimed)) or "none"
    data = {"coeffs": coeffs, "actual": shown_a, "claimed": shown_c, "rule": "Rational Root Theorem"}
    if actual == claimed:
        return confirm(name, f"the rational roots are {{{shown_a}}} (by the Rational Root Theorem; matches claim)", data)
    return mismatch(name, f"the rational roots are {{{shown_a}}}, not {{{shown_c}}}", data)


def verify_root(art: Dict[str, Any]) -> VerifierResult:
    name = "polynomial.root"
    if not isinstance(art.get("coeffs"), list) or art.get("claimed_root") is None:
        return na(name)
    try:
        coeffs = _coeffs(art)
        r = _as_fraction(art["claimed_root"])
    except (TypeError, ValueError, ZeroDivisionError) as e:
        return error(name, f"bad polynomial or claimed root: {e}")
    val = _poly_eval(coeffs, r)
    data = {"coeffs": coeffs, "x": _fmt(r), "value": _fmt(val)}
    if val == 0:
        return confirm(name, f"x = {_fmt(r)} is a root (the polynomial evaluates to 0)", data)
    return mismatch(name, f"x = {_fmt(r)} is not a root (the polynomial evaluates to {_fmt(val)}, not 0)", data)


_RULES = [
    (lambda cv: "coeffs" in cv and "claimed_rational_roots" in cv, verify_rational_roots),
    (lambda cv: "coeffs" in cv and "claimed_root" in cv, verify_root),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "POLY_VERIFY", _RULES, domain="polynomial",
                    none_reason="no POLY_VERIFY artifacts present")
