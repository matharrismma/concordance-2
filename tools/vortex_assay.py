#!/usr/bin/env python3
"""VORTEX MATH THROUGH THE ASSAY — keep the arithmetic, name the dead end.

    PYTHONPATH=src python tools/vortex_assay.py

"Vortex math" (Marko Rodin) claims that reducing numbers to their digital roots and drawing the
result on a circle of nine reveals the underlying structure of energy, and that a coil wound to
the resulting pattern does something no ordinary coil does. It circulates widely among exactly
the people this library is built to serve -- makers, homesteaders, radio people, anyone who
distrusts institutional science for reasons that are often good.

THE POINT OF THIS FILE IS NOT TO SNEER. It is to do the thing we ask of every other claim: run
it, keep whatever survives, and say plainly where it stops. Two failures are available here and
both are ours to avoid. We could dismiss the whole thing and throw away real arithmetic along
with the overreach -- which is what "debunking" usually does, and it is why people stop
listening to debunkers. Or we could nod along at the mystical part because the arithmetic part
checked out, which is how a fragment gets silently upgraded into authority.

So: three states, never two. CONFIRMED for what computes, DEAD END for what does not, and the
line between them stated out loud.

WHAT IS ACTUALLY TRUE, and it is not nothing:
  * The digital root is real arithmetic: dr(n) = 1 + (n-1) mod 9 for n > 0. It is exactly n mod 9
    with 9 in place of 0, which is why "casting out nines" has checked arithmetic since antiquity.
  * Doubling from 1 really does cycle 1-2-4-8-7-5 forever, and really does skip 3, 6 and 9.
  * That is not mysticism. It is the multiplicative order of 2 modulo 9, which is 6, and 3/6/9
    are the multiples of 3 that share a factor with 9 and therefore cannot appear in the orbit of
    a unit. The pattern is a THEOREM about base ten.
  * Which is the load-bearing point: change the base and the "universal" pattern changes with it.
    A property of our notation is being read as a property of the universe.

WHERE IT DIES:
  * "3, 6, 9 are the key to the universe" -- 3/6/9 are the non-units mod 9. In base 12 the special
    residues are different. Nothing about energy follows.
  * The Rodin coil -- toroidal windings are ordinary and well understood; the claimed anomalous
    output has no published, replicated measurement. This assay makes no claim either way about
    an unmeasured device; it records that the evidence required is a measurement nobody has
    produced, which is CANNOT_CHECK, not FALSE.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def digital_root(n: int) -> int:
    """dr(n) = 1 + (n-1) mod 9 for n > 0; dr(0) = 0. Real, ancient, and useful."""
    if n == 0:
        return 0
    n = abs(n)
    return 1 + (n - 1) % 9


def doubling_orbit(start: int = 1, base: int = 10):
    """The famous 1-2-4-8-7-5. It is the orbit of 2 in the units of Z/(base-1)."""
    m = base - 1
    seen, x = [], start % m or m
    while x not in seen:
        seen.append(x)
        x = (x * 2) % m or m
    return seen


def multiplicative_order(a: int, m: int):
    x, k = a % m, 1
    while x != 1:
        x = (x * a) % m
        k += 1
        if k > m:
            return None
    return k


def main() -> int:
    print("VORTEX MATH — THE ASSAY")
    print("=" * 78)

    print("\n1. THE DIGITAL ROOT IS REAL ARITHMETIC                              [CONFIRMED]")
    ok = all(digital_root(n) == (n % 9 or 9) for n in range(1, 100000))
    print(f"   dr(n) == n mod 9 (with 9 for 0), checked n = 1..99,999 : {ok}")
    print("   This is casting out nines. It has checked ledgers for a thousand years and it")
    print("   still works. Nothing here is being taken away.")

    print("\n2. THE 1-2-4-8-7-5 CYCLE IS REAL                                    [CONFIRMED]")
    orbit = doubling_orbit()
    print(f"   doubling from 1, reduced by digital root : {'-'.join(map(str, orbit))}")
    print(f"   length {len(orbit)}, and it never touches 3, 6 or 9 : "
          f"{not ({3, 6, 9} & set(orbit))}")

    print("\n3. WHY — AND THIS IS WHERE THE CLAIM STOPS                          [THEOREM]")
    ordr = multiplicative_order(2, 9)
    print(f"   the multiplicative order of 2 mod 9 is {ordr}, so the orbit MUST have {ordr} terms")
    print("   3, 6 and 9 share the factor 3 with 9, so they are not units mod 9 and cannot")
    print("   appear in the orbit of one. The pattern is forced by arithmetic, not by energy.")

    print("\n4. THE TEST THAT DECIDES IT: CHANGE THE BASE                        [DEAD END]")
    print("   If 3-6-9 were a property of the universe it would survive a change of notation.")
    print(f"   {'base':>6s}  {'modulus':>8s}  {'doubling orbit':38s} {'excluded':>16s}")
    for base in (10, 8, 12, 14, 16):
        m = base - 1
        orb = doubling_orbit(1, base)
        excluded = sorted(set(range(1, m + 1)) - set(orb))
        print(f"   {base:>6d}  {m:>8d}  {'-'.join(map(str, orb)):38s} "
              f"{','.join(map(str, excluded)):>16s}")
    print("   The 'universal key' changes when we change how we write numbers down. It is a")
    print("   property of base ten -- that is, of our ten fingers -- and not of the world.")

    print("\n5. THE COIL                                                    [CANNOT_CHECK]")
    print("   Toroidal windings are ordinary engineering and well characterised. The claim of")
    print("   anomalous output is not refuted here; it is UNMEASURED. No published replicated")
    print("   measurement exists to check against, so the honest verdict is that the evidence")
    print("   required has never been produced -- which is not the same as false.")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("  KEEP    : the digital root, casting out nines, the doubling orbit, and the")
    print("            observation that the orbit has period 6 and excludes the non-units.")
    print("            This is genuine modular arithmetic and a good doorway into it.")
    print("  DEAD END: '3-6-9 is the key to the universe'. The pattern is a fact about base")
    print("            ten. Write the same numbers in base 12 and the special residues move.")
    print("  UNMEASURED: the coil. Nobody has produced the measurement, ours included.")
    print()
    print("  Said plainly because the people who find this compelling are not fools -- they are")
    print("  pattern-seers who were right that there is structure here. There IS structure. It")
    print("  is modular arithmetic, it is beautiful, and it is smaller than the claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
