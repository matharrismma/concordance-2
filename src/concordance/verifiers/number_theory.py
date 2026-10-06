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


def _grid_divisor() -> float:
    """Samples per mean zero spacing on the critical-line scan (default 24). A coarser grid is SOUND — it can only
    FAIL to match Backlund's independent count, never falsely match — so at great heights, where the cost is the
    grid, CONCORDANCE_RIEMANN_GRID may lower it (validated against a known N(T) before it is trusted)."""
    import os as _os
    try:
        d = float(_os.environ.get("CONCORDANCE_RIEMANN_GRID", "") or 24.0)
    except ValueError:
        d = 24.0
    return d if d >= 3.0 else 24.0


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


def _above_seam_values(a: float, b: float, h: float, block: int = 1 << 18):
    """Stream (t, Z(t)) across [a, b] with step h, evaluating Z in BLOCKS through the fastest backend present
    (C, then numpy, then pure python — riemann_accel). Every backend computes the same Riemann-Siegel formula;
    near a zero the caller recounts exactly, so the count does not depend on which backend ran."""
    from . import riemann_accel
    buf: list = []
    t = a
    while True:
        buf.append(t)
        if len(buf) >= block or t >= b:
            vals = riemann_accel.z_array(buf)
            for tt, vv in zip(buf, vals):
                yield tt, float(vv)
            buf = []
            if t >= b:
                return
        t = min(t + h, b)


def _dip_crossings(t0: float, t1: float, t2: float, v0: float, v1: float, v2: float):
    """A same-sign triple can hide a CLOSE PAIR the grid stepped over: Z dips toward zero between t0 and t2 but
    no sample landed in the dip. Fit the parabola through the three points; when its vertex is predicted to reach
    below zero (a crossing the grid missed), rescan [t0, t2] EXACTLY and return the true count there — else 0.
    Local and cheap: no argument-principle count. A principled near-miss detector, not a magic threshold; the
    exact recount is the judge, and the strip count downstream is the independent authority."""
    if (v0 < 0) != (v1 < 0) or (v1 < 0) != (v2 < 0):
        return 0                                                   # a crossing already sits in this triple
    s = 1.0 if v1 > 0 else -1.0
    u0, u1, u2 = s * v0, s * v1, s * v2
    if u1 > u0 or u1 > u2:
        return 0                                                   # the middle is not a dip
    curv = u0 - 2.0 * u1 + u2
    if curv <= 0:
        return 0                                                   # concave: no interior minimum to worry about
    vertex_min = u1 - (u2 - u0) ** 2 / (8.0 * curv)
    if vertex_min >= 0.0:
        return 0                                                   # the model stays above zero: no missed pair
    return _exact_changes(t0, t2, 96)


def _count_above_np(start: float, b: float, h: float, carry_t, carry_v, block: int = 1 << 22) -> int:
    """The vectorised twin of the streamed count above the seam: sign changes on the grid, with the SAME tol and
    parabolic-dip exact corrections, but the bulk work in numpy so a half-billion-point sweep needs no
    half-billion-step python loop. Candidate spans (within-error pairs, parabola dips) are merged and recounted
    exactly once each — never twice. Identical counts to the streamed path (pinned); used only when numpy is
    present, above the seam."""
    import math
    from . import riemann_accel
    np = riemann_accel._numpy()
    count = 0
    n_total = int(math.ceil((b - start) / h)) + 1
    done = 0
    while done < n_total:
        k = min(block, n_total - done)
        ts = np.minimum(start + (done + np.arange(k)) * h, b)
        vs = np.asarray(riemann_accel.z_array(ts), float)
        if carry_t is not None:
            ts = np.concatenate(([carry_t], ts))
            vs = np.concatenate(([carry_v], vs))
        sb = vs < 0.0
        cross = sb[:-1] != sb[1:]
        count += int(cross.sum())
        tol = 3.0 * np.power(ts[1:], -0.75)
        tolpair = (~cross) & (np.maximum(np.abs(vs[:-1]), np.abs(vs[1:])) < tol)
        v0, v1, v2 = vs[:-2], vs[1:-1], vs[2:]
        same = (sb[:-2] == sb[1:-1]) & (sb[1:-1] == sb[2:])
        s = np.where(v1 > 0, 1.0, -1.0)
        u0, u1, u2 = s * v0, s * v1, s * v2
        curv = u0 - 2 * u1 + u2
        with np.errstate(divide="ignore", invalid="ignore"):
            vmin = u1 - (u2 - u0) ** 2 / (8 * curv)
        dip = same & (u1 <= u0) & (u1 <= u2) & (curv > 0) & (vmin < 0.0)
        spans = [(int(i), int(i) + 1) for i in np.nonzero(tolpair)[0]]
        spans += [(int(j), int(j) + 2) for j in np.nonzero(dip)[0]]  # triple centred at j+1 -> indices j..j+2
        if spans:
            spans.sort()
            merged = []
            for lo, hi in spans:
                if merged and lo <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
                else:
                    merged.append((lo, hi))
            for lo, hi in merged:                                    # a crossing-free span: exact replaces coarse 0
                count += _exact_changes(float(ts[lo]), float(ts[hi]), 32 * (hi - lo) + 32)
        carry_t = float(ts[-1])
        carry_v = float(vs[-1])
        done += k
    return count


def _count_changes(a: float, b: float, h: float) -> int:
    """Sign changes of Z on the grid from a to b. Two local corrections keep the float scan honest, each judged
    by exact mpmath so the formula's error can neither hide nor invent a pair:
      * a span whose two samples both sit within the formula's error without a crossing is recounted exactly;
      * a same-sign triple whose parabola dips below zero (a close pair the grid stepped over) is recounted exactly.
    The triple test fires at most once every two steps (a skip after it fires), so it can never COUNT A CROSSING
    TWICE — the worst it can do is miss a second pair in the same span, which the strip count downstream exposes.
    Below the seam Z is exact (mpmath) a quarter apart; above it the bulk sweep runs through riemann_accel."""
    import mpmath as mp
    seam = _RS_FLOAT_FROM + 1.0
    count = 0
    w_t: list = []
    w_v: list = []
    skip = 0

    def fold(t: float, v: float):
        nonlocal count, skip
        if w_t:
            if (w_v[-1] < 0) != (v < 0):
                count += 1
            else:
                tol = 0.05 if t < seam else 3.0 * t ** -0.75
                if max(abs(w_v[-1]), abs(v)) < tol:
                    count += _exact_changes(w_t[-1], t, 64)
        w_t.append(t)
        w_v.append(v)
        if len(w_t) == 3:
            if skip > 0:
                skip -= 1
            elif w_t[0] >= seam:                                   # the triple test lives above the seam
                extra = _dip_crossings(w_t[0], w_t[1], w_t[2], w_v[0], w_v[1], w_v[2])
                if extra:
                    count += extra
                    skip = 1                                       # don't let the next triple re-scan the same span
            w_t.pop(0)
            w_v.pop(0)

    # below the seam: exact (mpmath), a quarter apart — the small reference region
    t = a
    while t < seam and t < b:
        fold(t, float(mp.siegelz(t)))
        t = min(t + 0.25, b)
        if t >= b and t < seam:                                    # the whole span was below the seam
            fold(t, float(mp.siegelz(t)))
            return count
    # above the seam: vectorised when numpy is present (a half-billion-point grid needs no python loop), else
    # the streamed fold. Both make the same decisions and the same count.
    from . import riemann_accel
    if riemann_accel._numpy() is not False:
        return count + _count_above_np(t, b, h, w_t[-1] if w_t else None, w_v[-1] if w_v else None)
    for tt, vv in _above_seam_values(t, b, h):
        fold(tt, vv)
    return count


def _zeros_on_line(T: float, step: float = 0.25) -> int:
    """Zeros ON the critical line in (0, T]: sign changes of Z on ONE grid — mpmath a quarter apart below the
    seam (t < 501, where the float formula's error is too large), the float Riemann–Siegel formula a
    twenty-fourth of the mean spacing apart above it — with the exact correction of _count_changes. What a pair
    closer than the grid could still hide, Backlund's strip count exposes; the caller then localises by that
    count and rescans exactly."""
    import math
    spacing = _TWO_PI / math.log(max(T, 20.0) / _TWO_PI)
    return _count_changes(1.0, T, min(step, spacing / _grid_divisor()))


_CHECKED_MEMO: dict = {}


def _zeros_on_line_checked(T: float):
    """(zeros on the line, N(T) in the strip, S(T), localised rescans): the scan, then the independent count; where
    the scan is short, bisect by the strip count (cheap) until the deficit sits in a narrow span and rescan it
    exactly. Returns the final on-line count — which may still be short: then nothing is certified.

    Memoised within the process: minting a mark calls this once in tools/tick.py and again inside the verifier
    (the verifier is its own skeptic), and at T = 10^7 a scan is an hour — the deterministic result is the same
    both times, so the second call reuses the first rather than scanning twice."""
    key = round(float(T), 6)
    if key in _CHECKED_MEMO:
        return _CHECKED_MEMO[key]
    import math
    n_strip, S = _zeros_in_strip(T)
    on_line = _zeros_on_line(T)
    want = int(round(n_strip))
    rescans = 0
    if on_line < want:
        spacing = _TWO_PI / math.log(max(T, 20.0) / _TWO_PI)
        h = min(0.25, spacing / _grid_divisor())

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
    out = (on_line, n_strip, S, rescans)
    if len(_CHECKED_MEMO) < 64:                                   # a small bound: this is a within-process reuse, not a cache
        _CHECKED_MEMO[key] = out
    return out


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
    import os as _os
    # The cap protects the public /verify path (which sheds at 8 s but whose worker thread keeps computing):
    # a stranger cannot make the box sweep to T=1e9. The trusted operator's tool (tools/tick.py) lifts it by
    # setting CONCORDANCE_RIEMANN_MAX, because an offline mark is meant to run long. Read live, not at import.
    try:
        max_h = float(_os.environ.get("CONCORDANCE_RIEMANN_MAX", "") or _MAX_HEIGHT)
    except ValueError:
        max_h = _MAX_HEIGHT
    if not (14 < T <= max_h):
        return error(name, f"height {T} out of range: the first zero is at t ≈ 14.13; this door computes up to "
                           f"T = {max_h:g} (CONCORDANCE_RIEMANN_MAX lifts it for an offline mark)")
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


_EULER_GAMMA = 0.5772156649015329


def verify_robin(spec):
    """RH BY ELIMINATION, through the divisor sum (Robin 1984: RH <=> sigma(n) < e^gamma * n * ln ln n for every
    n > 5040). This does not confirm RH; it RULES OUT a region where RH could fail. A counterexample would be a
    number n > 5040 whose divisors sum to at least e^gamma * n * ln ln n; the sieve checks every n in (5040, N]
    and finds none, so a first Robin counterexample — and with it any RH failure by this route — must lie beyond N.
    We are looking at what it is NOT: the surviving window for a counterexample is pushed past N.
      NUM_VERIFY: {"robin_to": 1000000, "claimed_robin_holds": true, "claimed_closest_approach_n": 10080}  (N <= 2e7)"""
    import math
    name = "number_theory.robin"
    try:
        N = int(spec.get("robin_to"))
    except (TypeError, ValueError):
        return error(name, "robin_to must be an integer (the height N to eliminate below)")
    if N <= 5040:
        return error(name, "robin_to must exceed 5040 (Robin's inequality is for n > 5040; n <= 5040 has known exceptions)")
    if N > 20_000_000:
        return error(name, f"robin_to {N} exceeds the exact-sieve cap (2e7); the surviving window is charted in bounded steps")
    try:
        import numpy as np
        sigma = np.zeros(N + 1, dtype=np.int64)
        for d in range(1, N + 1):
            sigma[d::d] += d
        n = np.arange(5041, N + 1)
        bound = math.exp(_EULER_GAMMA) * n * np.log(np.log(n))
        ratio = sigma[5041:N + 1] / bound
        viol = n[ratio >= 1.0]
        idx = int(np.argmax(ratio))
        closest_n = int(n[idx]); closest_ratio = float(ratio[idx])
        violations = [int(v) for v in viol[:8]]
    except ImportError:
        return na(name, "the Robin sieve needs numpy")
    except MemoryError:
        return error(name, f"robin_to {N} is too large for memory on this node")
    holds = not violations
    data = {"robin_to": N, "robin_holds": holds, "closest_approach_n": closest_n,
            "closest_approach_ratio": round(closest_ratio, 6), "counterexamples": violations,
            "equivalent": "RH <=> sigma(n) < e^gamma * n * ln ln n for all n > 5040 (Robin 1984)",
            "eliminates": (f"no Robin counterexample in (5040, {N}] — a first RH failure by this route must exceed {N}"
                           if holds else f"a Robin counterexample at or below {N}: RH would be FALSE")}
    claimed_holds = spec.get("claimed_robin_holds")
    claimed_n = spec.get("claimed_closest_approach_n")
    if claimed_holds is None and claimed_n is None:
        return na(name, "claim claimed_robin_holds and/or claimed_closest_approach_n")
    problems = []
    if claimed_holds is not None and bool(claimed_holds) != holds:
        problems.append(f"Robin holds to {N} is {holds}, claimed {bool(claimed_holds)}")
    if claimed_n is not None:
        try:
            if int(claimed_n) != closest_n:
                problems.append(f"closest approach in (5040,{N}] is n={closest_n}, claimed {int(claimed_n)}")
        except (TypeError, ValueError):
            return error(name, "claimed_closest_approach_n must be an integer")
    if problems:
        return mismatch(name, "; ".join(problems), data)
    return confirm(name, f"Robin holds for every n in (5040, {N}] (closest approach n={closest_n}, "
                         f"sigma/(e^gamma n lnln n)={closest_ratio:.4f} < 1): no RH counterexample by this route below {N}", data)


def verify_schoenfeld(spec):
    """RH BY ELIMINATION, through the prime count (Schoenfeld 1976: RH <=> |pi(x) - li(x)| < sqrt(x)*ln(x)/(8*pi)
    for every x >= 2657). A different tool from Robin's divisor sum, pointed at the same window from another side.
    This does not confirm RH; it RULES OUT a region where RH could fail. A counterexample would be some x >= 2657
    where the prime count strays from li(x) by sqrt(x)*ln(x)/(8*pi) or more; we check every x in [2657, X] and find
    none, so a first failure by this route must lie beyond X. We are looking at what it is NOT.

    The check is exact, not a sample. pi(x) is sieved exactly; li(x) is monotone increasing and pi(x) is a step
    function, so on each unit interval [n, n+1) the supremum of |pi - li| is reached at a known endpoint. On the
    thin low window (where the inequality is tightest, which is why Schoenfeld's threshold sits at 2657) we take
    that exact per-integer supremum, li(n+1) - pi(n), and require it below the interval's least right-hand side
    RHS(n). Higher up, where the margin opens wide, an adaptive grid brackets pi and li between monotone envelopes
    and certifies each span at once. Either way the verdict is a bound that holds for ALL real x in [2657, X].
      NUM_VERIFY: {"schoenfeld_to": 1000000, "claimed_schoenfeld_holds": true, "claimed_closest_approach_n": 2658}  (X <= 2e7)"""
    import math
    name = "number_theory.schoenfeld"
    try:
        X = int(spec.get("schoenfeld_to"))
    except (TypeError, ValueError):
        return error(name, "schoenfeld_to must be an integer (the height X to eliminate below)")
    if X <= 2657:
        return error(name, "schoenfeld_to must exceed 2657 (Schoenfeld's inequality is stated for x >= 2657)")
    if X > 20_000_000:
        return error(name, f"schoenfeld_to {X} exceeds the exact-sieve cap (2e7); the surviving window is charted in bounded steps")
    eight_pi = 8.0 * math.pi
    def rhs(x):   # Schoenfeld's right-hand side, increasing on [2657, inf): least on an interval at its left end
        return math.sqrt(x) * math.log(x) / eight_pi
    try:
        import numpy as np
        import mpmath as mp
        sieve = np.ones(X + 2, dtype=bool); sieve[:2] = False
        for i in range(2, int((X + 1) ** 0.5) + 1):
            if sieve[i]:
                sieve[i * i::i] = False
        pref = np.cumsum(sieve, dtype=np.int64)        # pref[x] = pi(x), exact
        worst_ratio = 0.0; worst_n = 2657; counterexamples: List[int] = []
        with mp.workdps(20):                           # li to ~20 digits, then float: ample for the ratio
            L = min(X, 25000)                          # exact per-integer where the margin is thin
            for n in range(2657, L):
                sup = float(mp.li(n + 1)) - int(pref[n])        # sup of |pi - li| on [n, n+1): li up, pi flat
                r = sup / rhs(n)
                if r > worst_ratio:
                    worst_ratio, worst_n = r, n
                if sup >= rhs(n) and len(counterexamples) < 8:
                    counterexamples.append(n)
            if X > L:                                  # adaptive envelope above: margin wide, span many x per li call
                a = L
                li_a = float(mp.li(a))
                while a < X:
                    step = max(2, int(0.1 * math.sqrt(a) * math.log(a) * math.log(a) / eight_pi))
                    b = min(X, a + step)
                    li_b = float(mp.li(b))
                    pa, pb = int(pref[a]), int(pref[b])
                    env = max(pb - li_a, li_b - pa, abs(pa - li_a), abs(pb - li_b))  # sup|pi-li| on [a,b], monotone bracket
                    if env >= rhs(a) and len(counterexamples) < 8:   # the envelope carries slack, so it is used only to
                        counterexamples.append(a)                    # catch a violation, never to set the closest approach
                    a, li_a = b, li_b
    except ImportError:
        return na(name, "the Schoenfeld check needs numpy and mpmath")
    except MemoryError:
        return error(name, f"schoenfeld_to {X} is too large for memory on this node")
    holds = not counterexamples
    data = {"schoenfeld_to": X, "schoenfeld_holds": holds, "closest_approach_n": worst_n,
            "closest_approach_ratio": round(worst_ratio, 6), "counterexamples": counterexamples,
            "equivalent": "RH <=> |pi(x) - li(x)| < sqrt(x)*ln(x)/(8*pi) for all x >= 2657 (Schoenfeld, Math. Comp. 30 (1976) 337-360)",
            "eliminates": (f"no Schoenfeld violation in [2657, {X}] — a first RH failure by this route must exceed {X}"
                           if holds else f"a Schoenfeld violation at or below {X}: RH would be FALSE")}
    claimed_holds = spec.get("claimed_schoenfeld_holds")
    claimed_n = spec.get("claimed_closest_approach_n")
    if claimed_holds is None and claimed_n is None:
        return na(name, "claim claimed_schoenfeld_holds and/or claimed_closest_approach_n")
    problems = []
    if claimed_holds is not None and bool(claimed_holds) != holds:
        problems.append(f"Schoenfeld holds to {X} is {holds}, claimed {bool(claimed_holds)}")
    if claimed_n is not None:
        try:
            if int(claimed_n) != worst_n:
                problems.append(f"closest approach in [2657,{X}] is x={worst_n}, claimed {int(claimed_n)}")
        except (TypeError, ValueError):
            return error(name, "claimed_closest_approach_n must be an integer")
    if problems:
        return mismatch(name, "; ".join(problems), data)
    return confirm(name, f"Schoenfeld's bound holds for every x in [2657, {X}] (closest approach x={worst_n}, "
                         f"|pi-li|/(sqrt(x) ln x/8pi)={worst_ratio:.4f} < 1): no RH counterexample by the prime-count route below {X}", data)


_MAX_COUNT_HEIGHT = 1.0e13


def _s_bound(T: float) -> float:
    """A rigorous upper bound on |S(T)| (Backlund's inequality in the classical form). N(T) must land within this
    of the smooth term θ(T)/π + 1; a count that strays further is a computation that slipped, not a true count."""
    import math
    return 0.137 * math.log(T) + 0.443 * math.log(math.log(T)) + 1.588


def verify_zero_count(spec):
    """THE ZERO COUNT AT A GREAT HEIGHT (Riemann stick, 2026-10-05). How MANY non-trivial zeros of ζ have
    0 < Im(ρ) <= T — counted, cheaply, far beyond the height any on-line sweep can reach. This is NOT an
    assertion that those zeros lie on the critical line (that is verify_critical_line's slow, per-zero work); it
    is the count in the strip, and the stick records it as exactly that.

    Trustworthy by two independent routes agreeing, the stick's standing discipline: the count comes from Turing's
    method (mpmath.nzeros, which certifies that no zero was skipped), and it is cross-checked against the
    Riemann-von Mangoldt smooth term θ(T)/π + 1 — their difference is S(T), and a true count keeps |S(T)| within
    Backlund's proven bound. A count that violated that bound would be a slip in the computation, and is refused.
    (At T = 10^6 and 10^7 this count equals our own two-count on-line sweeps exactly — 1,747,146 and 21,136,125.)
      NUM_VERIFY: {"zero_count_height": 1000000000, "claimed_zero_count": 2846548032}   (T <= 1e13)"""
    import math
    name = "number_theory.zero_count"
    try:
        T = float(spec.get("zero_count_height"))
    except (TypeError, ValueError):
        return error(name, "zero_count_height must be a number (the height T to count zeros up to)")
    if not (14.0 < T <= _MAX_COUNT_HEIGHT):
        return error(name, f"height {T:g} out of range: the first zero is at t ≈ 14.13; this count goes up to "
                           f"T = {_MAX_COUNT_HEIGHT:g} (Turing's method stays cheap, but a finite door)")
    try:
        import mpmath as mp
        with mp.workdps(30):
            n_turing = int(mp.nzeros(T))                       # Turing's method: the certified count in (0, T]
        main = float(_theta(T) / math.pi + 1.0)                # Riemann-von Mangoldt smooth term
        S = n_turing - main                                    # the implied S(T)
        bound = _s_bound(T)
    except ImportError:
        return na(name, "the zero count needs mpmath")
    except Exception as e:  # noqa: BLE001 — a computation that fails is an error, never a verdict
        return error(name, f"computation failed: {type(e).__name__}: {e}")
    consistent = abs(S) <= bound
    data = {"height": T, "zero_count": n_turing, "main_term": round(main, 3), "S_T": round(S, 4),
            "s_bound": round(bound, 4), "consistent_with_bound": consistent,
            "method": "Turing's method (mpmath.nzeros), cross-checked against θ(T)/π + 1 within Backlund's bound on S(T)",
            "means": ("the number of non-trivial zeros with 0 < Im(ρ) <= T — a COUNT in the strip, NOT a verification "
                      "that they lie on the critical line")}
    if not consistent:
        return error(name, f"the count N({T:g}) = {n_turing} implies S(T) = {S:.3f}, outside Backlund's bound "
                           f"{bound:.3f} — the computation slipped; nothing is sealed")
    claimed = spec.get("claimed_zero_count")
    if claimed is None:
        return na(name, "claim claimed_zero_count (the integer count of zeros up to the height)", data)
    try:
        claimed_i = int(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed_zero_count must be an integer")
    if claimed_i != n_turing:
        return mismatch(name, f"N({T:g}) = {n_turing:,} zeros in the strip (Turing's method), claimed {claimed_i:,}", data)
    return confirm(name, f"ζ has exactly {n_turing:,} non-trivial zeros with 0 < Im(ρ) <= {T:g} (Turing's method; "
                         f"S(T) = {S:+.3f} within Backlund's bound {bound:.2f}) — the count to this height, not a "
                         f"claim they lie on the line", data)


_RULES = [
    (lambda nv: ("critical_line_height" in nv and "claimed_zeros_on_line" in nv), verify_critical_line),
    (lambda nv: ("robin_to" in nv and ("claimed_robin_holds" in nv or "claimed_closest_approach_n" in nv)), verify_robin),
    (lambda nv: ("schoenfeld_to" in nv and ("claimed_schoenfeld_holds" in nv or "claimed_closest_approach_n" in nv)), verify_schoenfeld),
    (lambda nv: ("zero_count_height" in nv and "claimed_zero_count" in nv), verify_zero_count),
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
