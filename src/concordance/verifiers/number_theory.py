"""Number theory verifier (formal-reasoning grid axis sibling to math + logic).

Primality, GCD, factorial, and modular inverse. All deterministic via
stdlib math; no external dependency.

Checks:
  * number_theory.primality       — claimed prime/composite matches
  * number_theory.gcd             — Euclid's algorithm
  * number_theory.factorial       — n! exact
  * number_theory.modular_inverse — a · inv ≡ 1 mod m

NUM_VERIFY shape (any subset):
    {
      "n_prime": 17, "claimed_prime": true,
      "gcd_a": 12, "gcd_b": 18, "claimed_gcd": 6,
      "factorial_n": 5, "claimed_factorial": 120,
      "mod_a": 3, "mod_m": 11, "claimed_inverse": 4,   # 3·4 = 12 ≡ 1 mod 11
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error
from .base import dispatch  # declarative run() driver


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    r = int(math.isqrt(n))
    for i in range(3, r + 1, 2):
        if n % i == 0:
            return False
    return True


def verify_primality(spec: Dict[str, Any]) -> VerifierResult:
    name = "number_theory.primality"
    n = spec.get("n_prime")
    claimed = spec.get("claimed_prime")
    if n is None or claimed is None:
        return na(name)
    try:
        nf = int(n)
    except (TypeError, ValueError):
        return error(name, f"n_prime must be an integer, got {n!r}")
    if nf < 0:
        return error(name, "primality is defined for non-negative integers")
    actual = _is_prime(nf)
    data = {"n": nf, "actual_prime": actual, "claimed_prime": bool(claimed),
            "rule": "primality via trial division up to √n"}
    if actual == bool(claimed):
        return confirm(name, f"{nf} is{' ' if actual else ' NOT '}prime (matches claim)", data)
    return mismatch(name, f"{nf} is{' ' if actual else ' NOT '}prime, claimed {bool(claimed)}", data)


def verify_gcd(spec: Dict[str, Any]) -> VerifierResult:
    name = "number_theory.gcd"
    a = spec.get("gcd_a")
    b = spec.get("gcd_b")
    claimed = spec.get("claimed_gcd")
    if a is None or b is None or claimed is None:
        return na(name)
    try:
        af, bf, c = int(a), int(b), int(claimed)
    except (TypeError, ValueError):
        return error(name, "gcd inputs must be integers")
    actual = math.gcd(af, bf)
    data = {"a": af, "b": bf, "actual_gcd": actual, "claimed_gcd": c,
            "rule": "Euclidean algorithm (math.gcd)"}
    if actual == c:
        return confirm(name, f"gcd({af}, {bf}) = {actual} (matches claim)", data)
    return mismatch(name, f"gcd({af}, {bf}) = {actual}, claimed {c}", data)


def verify_factorial(spec: Dict[str, Any]) -> VerifierResult:
    name = "number_theory.factorial"
    n = spec.get("factorial_n")
    claimed = spec.get("claimed_factorial")
    if n is None or claimed is None:
        return na(name)
    try:
        nf = int(n)
        c = int(claimed)
    except (TypeError, ValueError):
        return error(name, "factorial inputs must be integers")
    if nf < 0:
        return error(name, f"factorial undefined for negative n, got {nf}")
    if nf > 1000:
        return error(name, f"factorial input {nf} too large for this verifier")
    actual = math.factorial(nf)
    data = {"n": nf, "actual_factorial": actual, "claimed_factorial": c}
    if actual == c:
        return confirm(name, f"{nf}! = {actual} (matches claim)", data)
    return mismatch(name, f"{nf}! = {actual}, claimed {c}", data)


def verify_modular_inverse(spec: Dict[str, Any]) -> VerifierResult:
    """Verify a · claimed ≡ 1 (mod m). Inverse exists iff gcd(a, m) = 1."""
    name = "number_theory.modular_inverse"
    a = spec.get("mod_a")
    m = spec.get("mod_m")
    claimed = spec.get("claimed_inverse")
    if a is None or m is None or claimed is None:
        return na(name)
    try:
        af, mf, c = int(a), int(m), int(claimed)
    except (TypeError, ValueError):
        return error(name, "modular inverse inputs must be integers")
    if mf <= 1:
        return error(name, f"modulus must be >= 2, got {mf}")
    if math.gcd(af, mf) != 1:
        return mismatch(name,
                        f"gcd({af}, {mf}) = {math.gcd(af, mf)} ≠ 1; modular inverse does not exist",
                        {"a": af, "m": mf, "gcd": math.gcd(af, mf)})
    product_mod = (af * c) % mf
    actual_inverse = pow(af, -1, mf)
    data = {"a": af, "m": mf, "claimed_inverse": c,
            "actual_inverse": actual_inverse,
            "a_times_claimed_mod_m": product_mod,
            "rule": "a · inv ≡ 1 (mod m)"}
    if product_mod == 1:
        return confirm(name,
                       f"{af}·{c} mod {mf} = 1; {c} is the modular inverse",
                       data)
    return mismatch(name,
                    f"{af}·{c} mod {mf} = {product_mod} ≠ 1; correct inverse is {actual_inverse}",
                    data)


# ── OEIS-style integer sequence checks ─────────────────────────────────
# These are deterministic stdlib computations. Each is keyed to its OEIS
# A-number so the data field carries the canonical reference.

def _fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("Fibonacci undefined for negative index")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _nth_prime(n: int) -> int:
    """The n-th prime, 1-indexed: nth(1)=2, nth(5)=11. Bounded by the sequence cap in the caller."""
    if n < 1:
        raise ValueError("the n-th prime is 1-indexed (n >= 1)")
    count, cand = 0, 1
    while count < n:
        cand += 1
        if _is_prime(cand):
            count += 1
    return cand


def _catalan(n: int) -> int:
    if n < 0:
        raise ValueError("Catalan undefined for negative index")
    # C(n) = (2n)! / (n! * (n+1)!)  — exact via math.comb
    return math.comb(2 * n, n) // (n + 1)


def _triangular(n: int) -> int:
    if n < 0:
        raise ValueError("Triangular undefined for negative index")
    return n * (n + 1) // 2


def _is_perfect_number(n: int) -> bool:
    """Sum of proper divisors equals n. The known perfect numbers are
    6, 28, 496, 8128, 33550336, ... (OEIS A000396)."""
    if n < 2:
        return False
    total = 1
    r = int(math.isqrt(n))
    for i in range(2, r + 1):
        if n % i == 0:
            total += i
            if i != n // i:
                total += n // i
    return total == n


_SEQUENCES: Dict[str, Dict[str, Any]] = {
    "prime":       {"oeis": "A000040", "fn": _nth_prime, "name": "prime"},        # 1-indexed: 2,3,5,7,11,…
    "fibonacci":   {"oeis": "A000045", "fn": _fibonacci, "name": "Fibonacci"},
    "catalan":     {"oeis": "A000108", "fn": _catalan,   "name": "Catalan"},
    "triangular":  {"oeis": "A000217", "fn": _triangular,"name": "triangular"},
}


def verify_sequence_term(spec: Dict[str, Any]) -> VerifierResult:
    """Check a claim of the form 'the n-th term of <sequence> is X'."""
    name = "number_theory.sequence"
    seq_name = (spec.get("sequence") or "").strip().lower()
    n = spec.get("sequence_index")
    claimed = spec.get("claimed_term")
    if not seq_name or n is None or claimed is None:
        return na(name)
    entry = _SEQUENCES.get(seq_name)
    if not entry:
        return na(name)
    try:
        ni = int(n); ct = int(claimed)
    except (TypeError, ValueError):
        return error(name, "sequence_index and claimed_term must be integers")
    if ni < 0 or ni > 2000:
        return error(name, f"sequence_index out of supported range [0, 2000]: {ni}")
    try:
        actual = entry["fn"](ni)
    except Exception as exc:
        return error(name, f"sequence eval failed: {exc}")
    data = {
        "sequence": seq_name,
        "oeis": entry["oeis"],
        "index": ni,
        "actual_term": actual,
        "claimed_term": ct,
        "source": f"OEIS {entry['oeis']}",
    }
    if actual == ct:
        return confirm(
            name,
            f"{entry['name']}({ni}) = {actual} (matches claim, OEIS {entry['oeis']})",
            data,
        )
    return mismatch(
        name,
        f"{entry['name']}({ni}) = {actual}, claimed {ct}",
        data,
    )


def verify_perfect_number(spec: Dict[str, Any]) -> VerifierResult:
    """Verify a claim that n is (or isn't) a perfect number. OEIS A000396."""
    name = "number_theory.perfect_number"
    n = spec.get("n_perfect")
    claimed = spec.get("claimed_perfect")
    if n is None or claimed is None:
        return na(name)
    try:
        nf = int(n)
    except (TypeError, ValueError):
        return error(name, "n_perfect must be integer")
    if nf < 1 or nf > 10_000_000:
        return error(name, "n_perfect out of supported range")
    actual = _is_perfect_number(nf)
    cl = bool(claimed)
    data = {"n": nf, "actual_perfect": actual, "claimed_perfect": cl,
            "source": "OEIS A000396", "rule": "sum of proper divisors equals n"}
    if actual == cl:
        return confirm(name, f"is_perfect({nf}) = {actual} (matches claim)", data)
    return mismatch(name, f"is_perfect({nf}) = {actual}, claimed {cl}", data)


def verify_prime_counting(spec: Dict[str, Any]) -> VerifierResult:
    """The Prime Number Theorem — the bridge from the primes to the logarithm.

    pi(x), the count of primes <= x, is computed EXACTLY by sieve, and the claim is checked against
    it. The worked trail shows the PNT asymptotic pi(x) ~ x/ln(x): the discrete count of the primes
    is governed, in the large, by a continuous logarithm. This is the one calculation that joins
    number theory to the analytic (log) world — the seam analytic number theory lives on, and (by
    the Atlas's own topology) the single connection that closes its one irreducible void.
    """
    import math
    name = "number_theory.prime_counting"
    x = spec.get("limit")
    claimed = spec.get("claimed_prime_count")
    if x is None or claimed is None:
        return na(name)
    try:
        x = int(x)
        claimed = int(claimed)
    except (TypeError, ValueError):
        return error(name, "limit and claimed_prime_count must be integers")
    if x < 2:
        actual = 0
    elif x > 20_000_000:
        return na(name, "limit exceeds the exact-sieve cap (2e7); the PNT is an asymptotic law")
    else:
        sieve = bytearray([1]) * (x + 1)
        sieve[0] = sieve[1] = 0
        for i in range(2, int(x ** 0.5) + 1):
            if sieve[i]:
                sieve[i * i::i] = bytearray(len(range(i * i, x + 1, i)))
        actual = sum(sieve)
    est = x / math.log(x) if x > 1 else 0.0  # PNT asymptotic pi(x) ~ x/ln(x)
    data = {"pi": actual, "pnt_estimate_x_over_lnx": est, "claimed": claimed,
            "law": "pi(x) ~ x / ln(x)  (Prime Number Theorem)"}
    if actual == claimed:
        return confirm(name, f"pi({x}) = {actual}; PNT estimate x/ln(x) = {est:.1f} (matches claim)", data)
    return mismatch(name, f"pi({x}) = {actual}, claimed {claimed}; PNT estimate x/ln(x) = {est:.1f}", data)


def _divisors(n: int):
    out = []
    d = 1
    while d * d <= n:
        if n % d == 0:
            out.append(d)
            if d != n // d:
                out.append(n // d)
        d += 1
    return sorted(out)


def verify_divisor_count(spec):
    """τ(n): the number of positive divisors of n — "12 has 6 divisors", "the number of divisors of 60 is 12".
    Exact and deterministic (2026-10-03; the reason 12 and 60 organize wholes: the most divisors for their
    size). Optionally the divisors themselves (claimed_divisors) are compared as a set."""
    name = "number_theory.divisor_count"
    try:
        n = int(spec.get("divisors_of"))
    except (TypeError, ValueError):
        return error(name, "divisors_of must be an integer")
    if n < 1 or n > 10**12:
        return error(name, f"divisors_of {n} out of range (1..1e12)")
    actual = _divisors(n)
    data = {"n": n, "divisors": actual if len(actual) <= 64 else actual[:64], "actual_count": len(actual)}
    claimed_count = spec.get("claimed_divisor_count")
    claimed_set = spec.get("claimed_divisors")
    problems = []
    if claimed_count is not None:
        try:
            cc = int(claimed_count)
            data["claimed_divisor_count"] = cc
            if cc != len(actual):
                problems.append(f"{n} has {len(actual)} divisors, not {cc}")
        except (TypeError, ValueError):
            return error(name, "claimed_divisor_count must be an integer")
    if claimed_set is not None:
        try:
            cs = sorted(int(x) for x in claimed_set)
            data["claimed_divisors"] = cs
            if cs != actual:
                problems.append(f"divisors of {n} are {actual}, not {cs}")
        except (TypeError, ValueError):
            return error(name, "claimed_divisors must be integers")
    if claimed_count is None and claimed_set is None:
        return na(name)
    if problems:
        return mismatch(name, "; ".join(problems), data)
    return confirm(name, f"{n} has {len(actual)} divisors: {actual if len(actual) <= 16 else str(actual[:16]) + '…'}", data)


_TWO_PI = 6.283185307179586
_RS_FLOAT_FROM = 500.0          # below this the first-order Riemann–Siegel error (~ t^-3/4) is too large; mpmath there
_DIP = 0.08                     # |Z| this small at two neighbouring samples without a crossing: look closer, exactly
_MAX_HEIGHT = 1000000.0


def _theta(t: float) -> float:
    import math
    return t / 2 * math.log(t / _TWO_PI) - t / 2 - math.pi / 8 + 1 / (48 * t) + 7 / (5760 * t ** 3)


def _rs_z(t: float) -> float:
    """Hardy's Z(t) by the Riemann–Siegel formula in floats: the main sum and the first correction term
    (error ~ t^(-3/4)). A hundred times faster than mpmath; wherever |Z| is small the exact function decides."""
    import math
    a = math.sqrt(t / _TWO_PI)
    m = int(a)
    th = _theta(t)
    acc = 0.0
    for n in range(1, m + 1):
        acc += math.cos(th - t * math.log(n)) / math.sqrt(n)
    q = a - m
    c0 = math.cos(_TWO_PI * (q * q - q - 1 / 16)) / math.cos(_TWO_PI * q)
    return 2 * acc + (-1) ** (m - 1) * a ** -0.5 * c0


def _z(t: float) -> float:
    """Exact (mpmath) below the seam and one step past it, so no span ever mixes the two methods."""
    import mpmath as mp
    return float(mp.siegelz(t)) if t < _RS_FLOAT_FROM + 1.0 else _rs_z(t)


def _changes(vals) -> int:
    return sum(1 for i in range(1, len(vals)) if (vals[i - 1] < 0) != (vals[i] < 0))


def _exact_changes(a: float, b: float, n: int = 48) -> int:
    import mpmath as mp
    vals = [float(mp.siegelz(a + (b - a) * k / n)) for k in range(n + 1)]
    return _changes(vals)


def _grid(a: float, b: float, h: float):
    """The scan grid from a to b: a quarter apart below the seam, h above — streamed, never stored."""
    t = a
    yield t
    while t < b:
        t = min(t + (0.25 if t < _RS_FLOAT_FROM + 1.0 else h), b)
        yield t


def _count_changes(a: float, b: float, h: float) -> int:
    """Sign changes of Z on the grid from a to b, with one exact correction: a span whose two samples both sit
    within the formula's own error (3·t^(-3/4); 0.05 below the seam) without a crossing is recounted with mpmath,
    so the formula's error can never hide or invent a pair. One grid, one count — streamed in O(1) memory, so a
    million-high scan does not need a million-long list."""
    count = 0
    prev_t = None
    prev = 0.0
    for t in _grid(a, b, h):
        v = _z(t)
        if prev_t is not None:
            if (prev < 0) != (v < 0):
                count += 1
            else:
                tol = 0.05 if t < _RS_FLOAT_FROM + 1.0 else 3.0 * t ** -0.75
                if max(abs(prev), abs(v)) < tol:
                    count += _exact_changes(prev_t, t, 64)
        prev_t, prev = t, v
    return count


def _zeros_on_line(T: float, step: float = 0.25) -> int:
    """Zeros ON the critical line in (0, T]: sign changes of Z on ONE grid — mpmath a quarter apart below the
    seam (t < 501, where the float formula's error is too large), the float Riemann–Siegel formula a
    twenty-fourth of the mean spacing apart above it — with the exact correction of _count_changes. What a pair
    closer than the grid could still hide, Backlund's strip count exposes; the caller then localises by that
    count and rescans exactly."""
    import math
    spacing = _TWO_PI / math.log(max(T, 20.0) / _TWO_PI)
    return _count_changes(1.0, T, min(step, spacing / 24))


def _zeros_on_line_checked(T: float):
    """(zeros on the line, N(T) in the strip, S(T), localised rescans): the scan, then the independent count; where
    the scan is short, bisect by the strip count (cheap) until the deficit sits in a narrow span and rescan it
    exactly. Returns the final on-line count — which may still be short: then nothing is certified."""
    import math
    n_strip, S = _zeros_in_strip(T)
    on_line = _zeros_on_line(T)
    want = int(round(n_strip))
    rescans = 0
    if on_line < want:
        spacing = _TWO_PI / math.log(max(T, 20.0) / _TWO_PI)
        h = min(0.25, spacing / 24)

        def seg(a: float, b: float) -> int:
            return _count_changes(a, b, h)

        def nstrip(t: float) -> float:
            return 0.0 if t <= 14.0 else _zeros_in_strip(t)[0]

        budget = [64]

        def localise(a: float, b: float, na: float, nb: float) -> int:
            have = seg(a, b)
            need = int(round(nb - na))
            if have >= need or budget[0] <= 0:
                return have
            if b - a <= 6 * h:
                nonlocal_rescans[0] += 1
                return _exact_changes(a, b, 96)
            m = (a + b) / 2
            nm = nstrip(m)
            budget[0] -= 1
            return localise(a, m, na, nm) + localise(m, b, nm, nb)

        nonlocal_rescans = [0]
        on_line = localise(1.0, T, 0.0, n_strip)
        rescans = nonlocal_rescans[0]
    return on_line, n_strip, S, rescans


def _zeros_in_strip(T: float, sigma_steps: int = 0):
    """Backlund's count by the argument principle, independent of the line: N(T) = θ(T)/π + 1 + S(T), with
    S(T) = (1/π)·arg ζ(½ + iT) followed continuously from σ = 2 (where the argument is small) down to σ = ½.
    The step count grows with T; if N(T) does not land on an integer the steps are doubled once."""
    import math
    import mpmath as mp
    steps = sigma_steps or min(2000, 120 + int(T / 400))
    th = mp.siegeltheta(T)
    for attempt in range(2):
        prev = mp.arg(mp.zeta(mp.mpc(2.0, T)))
        total = prev
        ds = 1.5 / steps
        for k in range(1, steps + 1):
            a = mp.arg(mp.zeta(mp.mpc(2.0 - k * ds, T)))
            d = a - prev
            while d > math.pi:
                d -= 2 * math.pi
            while d < -math.pi:
                d += 2 * math.pi
            total += d
            prev = a
        S = float(total / math.pi)
        N = float(th / math.pi + 1 + S)
        if abs(N - round(N)) < 0.05:
            break
        steps *= 2
    return N, S


def verify_critical_line(spec):
    """THE FIRST MARK ON THE RIEMANN STICK (tick stick, 2026-10-05): every zero of ζ with 0 < t ≤ T lies on the
    critical line. Two INDEPENDENT counts must agree — the zeros found ON the line (sign changes of Hardy's Z)
    and the zeros IN the strip (Backlund's argument-principle count N(T)) — and both must equal the claim.
    This is Turing's/Backlund's method, the way every published verification is done; ours is small and
    re-checkable. It is a verification up to a height, never a proof of the hypothesis.
      NUM_VERIFY: {"critical_line_height": 100, "claimed_zeros_on_line": 29}      (T ≤ 2000 here)"""
    name = "number_theory.critical_line"
    try:
        T = float(spec.get("critical_line_height"))
        claimed = int(spec.get("claimed_zeros_on_line"))
    except (TypeError, ValueError):
        return error(name, "critical_line_height (a number) and claimed_zeros_on_line (an integer) are required")
    if not (14 < T <= _MAX_HEIGHT):
        return error(name, f"height {T} out of range: the first zero is at t ≈ 14.13; this door computes up to T = {_MAX_HEIGHT:g}")
    try:
        on_line, n_strip, S, rescans = _zeros_on_line_checked(T)
    except Exception as e:  # noqa: BLE001 — a computation that fails is an error, never a verdict
        return error(name, f"computation failed: {type(e).__name__}: {e}")
    if abs(n_strip - round(n_strip)) > 0.05:
        return error(name, f"the strip count did not land on an integer (N(T) = {n_strip:.4f}); refine and retry")
    n_strip_i = int(round(n_strip))
    data = {"height": T, "zeros_on_line": on_line, "zeros_in_strip": n_strip_i, "S_T": round(S, 4), "claimed": claimed,
            "localised_rescans": rescans,
            "method": ("sign changes of Hardy's Z on the line (Riemann–Siegel in floats above t = 300, exact where |Z| dips, "
                       "deficits localised by the strip count and rescanned exactly) vs Backlund's argument-principle count"),
            "means": "every zero with 0 < Im(s) <= T lies on Re(s) = 1/2 — a verification to this height, not a proof"}
    if on_line != n_strip_i:
        return mismatch(name, f"{on_line} zeros found on the line but N({T:g}) = {n_strip_i} in the strip — the line "
                              f"count is short (a close pair, or a zero off the line); nothing is certified", data)
    if claimed != on_line:
        return mismatch(name, f"up to T = {T:g} there are {on_line} zeros, all on the line; claimed {claimed}", data)
    return confirm(name, f"up to T = {T:g}: {on_line} zeros on the line = N(T) = {n_strip_i} in the strip; "
                         f"every zero to this height is on the critical line", data)


_RULES = [
    (lambda nv: ("critical_line_height" in nv and "claimed_zeros_on_line" in nv), verify_critical_line),
    (lambda nv: ("divisors_of" in nv and ("claimed_divisor_count" in nv or "claimed_divisors" in nv)), verify_divisor_count),
    (lambda nv: ("n_prime" in nv and "claimed_prime" in nv), verify_primality),
    (lambda nv: ("limit" in nv and "claimed_prime_count" in nv), verify_prime_counting),
    (lambda nv: (all(k in nv for k in ("gcd_a", "gcd_b", "claimed_gcd"))), verify_gcd),
    (lambda nv: ("factorial_n" in nv and "claimed_factorial" in nv), verify_factorial),
    (lambda nv: (all(k in nv for k in ("mod_a", "mod_m", "claimed_inverse"))), verify_modular_inverse),
    (lambda nv: (all(k in nv for k in ("sequence", "sequence_index", "claimed_term"))), verify_sequence_term),
    (lambda nv: ("n_perfect" in nv and "claimed_perfect" in nv), verify_perfect_number),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, 'NUM_VERIFY', _RULES, domain='number_theory', none_reason='no NUM_VERIFY artifacts present')
