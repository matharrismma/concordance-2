#!/usr/bin/env python3
"""Compute the music<->rest-of-reality bridges, so the write-up rests on numbers, not on poetry.

Every figure here is recomputed from first principles. Nothing is taken from a source's own number.
"""
from fractions import Fraction
import math

print("=" * 78)
print("1. EVERY MUSICAL INTERVAL IS A QUOTIENT OF TWO HARMONICS")
print("   music._INTERVAL_RATIOS vs acoustics.harmonic_frequency (f_n = n*f0)")
print("=" * 78)
RAT = {"unison": Fraction(1), "octave": Fraction(2), "fifth": Fraction(3, 2),
       "fourth": Fraction(4, 3), "major_third": Fraction(5, 4), "minor_third": Fraction(6, 5),
       "major_sixth": Fraction(5, 3), "minor_sixth": Fraction(8, 5)}
for name, r in RAT.items():
    a, b = r.numerator, r.denominator
    print("   %-13s %-6s = harmonic %2d / harmonic %2d   -> both integers <= 8: %s"
          % (name, str(r), a, b, a <= 8 and b <= 8))
print("\n   ALL %d intervals are f_a/f_b with a,b small integers. The acoustics verifier computes"
      % len(RAT))
print("   f_a and f_b; the music verifier stores the quotient. Same arithmetic, no shared edge.")

print()
print("=" * 78)
print("2. WHY TWELVE NOTES: A CONTINUED-FRACTION CONVERGENT OF log2(3/2)")
print("=" * 78)
x = math.log2(1.5)
print("   log2(3/2) = %.12f  (fifths per octave)" % x)
# continued fraction expansion
terms, v = [], x
for _ in range(9):
    a = math.floor(v)
    terms.append(int(a))
    frac = v - a
    if frac < 1e-12:
        break
    v = 1.0 / frac
print("   continued fraction: %s" % terms)
# convergents
h0, k0, h1, k1 = 0, 1, 1, 0
print("   convergents (fifths/octaves -> notes per octave):")
for a in terms[:8]:
    h0, k0, h1, k1 = h1, k1, a * h1 + h0, a * k1 + k0
    if k1 == 0:
        continue
    approx = h1 / k1
    err_cents = 1200 * (x - approx) * k1 if k1 else 0
    print("      %2d/%-3d = %.9f   denominator %2d  -> a %2d-note scale   (err %+8.4f cents/fifth)"
          % (h1, k1, approx, k1, k1, 1200 * (x - approx)))
print("\n   The convergent 7/12 is why the scale has TWELVE steps: 12 fifths ~ 7 octaves.")
print("   This is Diophantine approximation, not aesthetics.")

print()
print("=" * 78)
print("3. THE PYTHAGOREAN COMMA — EXACT, THE PRICE OF THAT APPROXIMATION")
print("=" * 78)
comma = Fraction(3, 2) ** 12 / Fraction(2, 1) ** 7
print("   (3/2)^12 / 2^7 = %s" % comma)
print("   as a ratio      = %d/%d" % (comma.numerator, comma.denominator))
print("   = 3^12/2^19     = %d/%d" % (3 ** 12, 2 ** 19))
print("   in cents        = %.6f" % (1200 * math.log2(float(comma))))
print("   -> you cannot have pure fifths AND pure octaves. Something must be tempered.")
print("   This is the same FAMILY of argument as the crystallographic restriction, and NOT the same")
print("   theorem. Section 7 states both and refuses the conflation.")

print()
print("=" * 78)
print("4. EQUAL TEMPERAMENT vs JUST — the error the comma forces, per interval")
print("=" * 78)
SEMI = {"unison": 0, "minor_third": 3, "major_third": 4, "fourth": 5, "fifth": 7,
        "minor_sixth": 8, "major_sixth": 9, "octave": 12}
print("   %-13s %-8s %-12s %-12s %s" % ("interval", "just", "12-TET", "diff(cents)", "verdict"))
for name, n in sorted(SEMI.items(), key=lambda kv: kv[1]):
    just = float(RAT[name])
    tet = 2 ** (n / 12)
    cents = 1200 * math.log2(tet / just)
    verdict = "exact" if abs(cents) < 1e-9 else ("audible" if abs(cents) > 5 else "subtle")
    print("   %-13s %-8.5f %-12.5f %+12.4f %s" % (name, just, tet, cents, verdict))
print("\n   Only unison and the octave survive tempering exactly. Everything else is a")
print("   deliberate, measured error -- a tuning residual you can read.")

print()
print("=" * 78)
print("5. ORBITAL RESONANCE IS THE SAME TEST AS CONSONANCE (integer period ratios)")
print("   Jupiter's Galilean moons -- periods in days (IAU/JPL mean values)")
print("=" * 78)
MOONS = [("Io", 1.769137786), ("Europa", 3.551181), ("Ganymede", 7.154553)]
for (n1, p1), (n2, p2) in zip(MOONS, MOONS[1:]):
    r = p2 / p1
    print("   %-9s/%-9s period ratio = %.6f   vs 2:1 = %+.4f%%   (= a musical OCTAVE)"
          % (n2, n1, r, 100 * (r / 2.0 - 1)))
print("   Io:Europa:Ganymede = 1:2:4 -> the Laplace resonance IS two stacked octaves.")
print("   ephemeris.orbital_period computes the periods; music.frequency_ratio tests 2:1.")
print("   Neither verifier knows the other exists.")

print()
print("=" * 78)
print("6. KEPLER'S HARMONICE MUNDI V, RECOMPUTED from ((1+e)/(1-e))^2")
print("   (his claim: extreme angular velocity ratios are musical intervals)")
print("=" * 78)
ECC = {"Mercury": 0.205630, "Venus": 0.006772, "Earth": 0.016709, "Mars": 0.093405,
       "Jupiter": 0.048498, "Saturn": 0.054509}
CLAIM = {"Mercury": Fraction(12, 5), "Venus": Fraction(25, 24), "Earth": Fraction(16, 15),
         "Mars": Fraction(3, 2), "Jupiter": Fraction(6, 5), "Saturn": Fraction(5, 4)}
for p, e in ECC.items():
    ratio = ((1 + e) / (1 - e)) ** 2
    cl = CLAIM[p]
    err = 100 * (ratio / float(cl) - 1)
    print("   %-8s e=%.6f  ratio=%.4f  vs %-5s=%.4f   %+7.2f%%  %s"
          % (p, e, ratio, str(cl), float(cl), err, "HOLDS" if abs(err) < 1.5 else "FAILS"))
print("\n   At the 1.5% line (MINE, not Kepler's): holds at Earth/Saturn/Jupiter/Venus, fails at")
print("   Mars/Mercury. The percentages are the result; the pass/fail verdict is my threshold.")
print("   So this is a claim with a MEASURED boundary -- exactly the 'parallel twin' shape:")
print("   same subject, different conditions.")

print()
print("=" * 78)
print("7. ONE FAMILY, TWO THEOREMS -- stated carefully, because the overclaim is tempting")
print("=" * 78)
print("   A. the comma: no stack of pure fifths closes an octave.")
print("      (3/2)^m = 2^n would need 3^m = 2^(n+m); unique factorization forbids it for EVERY m.")
chk = [m for m in range(1, 40) if ((3 ** m) & (3 ** m - 1)) == 0]
print("      m <= 39 with 3^m a power of two: %s  (empty, as the theorem requires)" % chk)
print()
print("   B. the crystallographic restriction: a periodic lattice admits an n-fold rotation")
print("      only when 2*cos(2*pi/n) is an integer.")
for n in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12):
    v = 2 * math.cos(2 * math.pi / n)
    ok = abs(v - round(v)) < 1e-12
    print("      n=%-3d 2cos(2pi/n) = %+.6f  integer? %-5s %s"
          % (n, v, ok, "ALLOWED" if ok else "forbidden"))
print("      n=5 -> %.6f = (sqrt(5)-1)/2 = %.6f, irrational: 5-fold periodicity cannot exist,"
      % (2 * math.cos(2 * math.pi / 5), (math.sqrt(5) - 1) / 2))
print("      which is why a quasicrystal needs cut-and-project instead of a lattice.")
print()
print("   VERDICT: both say 'a required commensurability has no integer solution'. The comma rests")
print("   on unique factorization, the crystal ban on an irrationality. SAME FAMILY, DIFFERENT")
print("   THEOREM. Writing them as one theorem is the overclaim this section exists to refuse.")
