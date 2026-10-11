#!/usr/bin/env python3
"""SEED THE VORTEX MATH STICK (Matt, 2026-10-11: "yes" - keep it, told the honest way; "Hinge is
fractalization"). Marko Rodin's vortex math, mapped the engine's way:
  - the REAL arithmetic SEALED: the digit roots of the powers of two, mod 9 - the 1-2-4-8-7-5 orbit;
  - the universal claim BARRED: it is an artifact of base ten - in base twelve the doubling hits 3, 6
    and 9 (sealed);
  - the HINGE named: fractalization - self-similarity across scales is real and deep, but this one is a
    shadow of base ten; the true fractal lives in the mathematics the engine seals elsewhere;
  - the energetic and divine claims DECLINED: over-unity breaks conservation; reading destiny from
    numerals is numerology.

    PYTHONPATH=src python tools/seed_vortex_math.py

Runs where the ledger lives (the box) - every seal is a real HOLDS verification. Found, never generated;
seal the arithmetic, attribute the pattern, decline the mysticism.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

import tick  # the shared seal + mint helpers, used by every stick  # noqa: E402
from concordance import roots  # noqa: E402
from concordance import tickstick as TS  # noqa: E402


def main():
    S = {}
    # Each seal uses only ** - * (the numeric verifier's plain ops): n mod m written as n - q*m.
    seals = [
        ("orbit", "vortex_two_is_a_primitive_root_mod9", "2**6 - 7*9", 1),     # 64 = 7*9 + 1  -> order of 2 is 6
        ("d16",   "vortex_sixteen_digit_root_mod9",      "2**4 - 9",    7),     # 16 -> 7
        ("d32",   "vortex_thirtytwo_digit_root_mod9",    "2**5 - 3*9",  5),     # 32 -> 5
        ("b12_9", "vortex_base12_doubling_reaches_nine", "2**6 - 5*11", 9),     # 64 mod 11 = 9
        ("b12_3", "vortex_base12_doubling_reaches_three","2**8 - 23*11", 3),    # 256 mod 11 = 3
        ("b12_6", "vortex_base12_doubling_reaches_six",  "2**9 - 46*11", 6),    # 512 mod 11 = 6
    ]
    for key, nid, expr, val in seals:
        S[key] = tick._rh_seal_num(nid, expr, float(val))
        if not S[key]:
            print("a seal failed:", nid)
            return 1
    print("sealed", len(S), "vortex numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))

    sid = TS.create(
        "Vortex math (Marko Rodin)",
        "Marko Rodin's vortex math: the doubling sequence 1-2-4-8-7-5 and the 3-6-9 'control' numbers, "
        "claimed as the mathematical fingerprint of God and the key to over-unity energy. What is real is "
        "the arithmetic - the digit roots of the powers of two, mod 9; what is false is the universal and "
        "energetic claim. The hinge is fractalization: self-similarity is real and deep, but this one is a "
        "shadow of base ten.",
        "number_theory",
    )["id"]
    print("stick:", sid)

    marks = [
        ("witness", "[the orbit IS the digit roots, mod 9] Rodin's 1-2-4-8-7-5 is the digit root (n mod 9) of the "
                    "powers of two. 2 is a primitive root mod 9: its order is 6 (2^6 = 64 = 7*9 + 1, sealed as "
                    "64 - 63 = 1), so doubling from 1 sweeps all six units of Z/9 - exactly {1, 2, 4, 8, 7, 5}. "
                    "Elementary, and every step checkable.", S["orbit"]),
        ("witness", "[a step: 16 -> 7] 2^4 = 16 has digit root 7 (16 - 9 = 7, sealed) - the fourth bead of the "
                    "orbit.", S["d16"]),
        ("witness", "[a step: 32 -> 5] 2^5 = 32 has digit root 5 (32 - 3*9 = 5, sealed) - the fifth bead, after "
                    "which the cycle returns to 1.", S["d32"]),
        ("witness", "[base twelve breaks it - it reaches 9] Digit roots are n mod (base - 1); in base twelve that "
                    "is mod 11, and there the doubling of two reaches 9: 2^6 = 64 = 5*11 + 9 (sealed). The "
                    "'3-6-9 are untouchable' claim is a fact of base ten alone.", S["b12_9"]),
        ("witness", "[base twelve - it reaches 3] 2^8 = 256 = 23*11 + 3 (sealed): in base twelve the doubling "
                    "lands on 3, which base ten forbids.", S["b12_3"]),
        ("witness", "[base twelve - it reaches 6] 2^9 = 512 = 46*11 + 6 (sealed): and on 6. In base twelve the "
                    "doubling runs straight through 3, 6 and 9.", S["b12_6"]),
        ("exclusion", "[the barrier - base-relative] The whole 'vortex' is a property of base ten (digit root = "
                      "n mod 9), not of reality: sealed above, in base twelve the doubling hits 3, 6 and 9. So no "
                      "claim that vortex math is a universal or divine law of the cosmos can stand - it is the "
                      "arithmetic of ten fingers, told as metaphysics. The universal reading is excluded.",
         {"source": "elementary modular arithmetic: digit_root(n) = n mod (base - 1); base 10 -> mod 9, "
                    "base 12 -> mod 11 (both sealed in the witnesses of this stick)"}),
        ("note", "[the hinge - fractalization] What gives such numeral patterns their pull is real: "
                 "self-similarity across scales - fractalization - is a genuine, deep principle (the Mandelbrot "
                 "set, power laws, renormalization; the scale-invariance this engine treats as a mark of truth). "
                 "The doubling is self-similar as a cycle, and that recursion is the grain of truth worth keeping. "
                 "But self-similarity in base-ten digit roots is a shadow; the real fractal structure lives in the "
                 "mathematics the engine seals elsewhere. Keep the hinge, not the mysticism.",
         {"source": "stick_the_mandelbrot_set; self-similarity / scale-invariance (scale-invariance = a mark of truth)"}),
        ("note", "[declined - over-unity] A Rodin coil does not produce free or over-unity energy. That would "
                 "violate the conservation of energy (the first law of thermodynamics); no such device has ever "
                 "been demonstrated under measurement. The engine seals arithmetic, not perpetual motion. A miss "
                 "stays a miss.",
         {"source": "the first law of thermodynamics (conservation of energy); card_floor_thermodynamics"}),
        ("note", "[declined - numerology] Reading divine or cosmic destiny from a base-ten numeral artifact is "
                 "numerology. The engine declines it, and Scripture leads away from divining by numbers "
                 "(Deuteronomy 18:10-12). Reverence belongs to God, who made number, not to a pattern in base "
                 "ten. Let the math determine the truth: real arithmetic, base-dependent, no free energy.",
         {"source": "Deuteronomy 18:10-12; the no-gematria discipline (seal the arithmetic, attribute the pattern)"}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_vortex_math.py")

    # ROOT it on the one map: filed under the instruments - 'prove all things, hold fast the good'
    # (exactly what this stick does: proved the claim, kept the arithmetic, released the mysticism).
    res = roots.place("stick:" + sid, "card_floor_the_instruments", by="proposed",
                      why="vortex math, proved and sifted - the arithmetic kept, the claims declined; 'prove all things'")
    print("placed under the_instruments:", res.get("ok"))
    r = roots.resolve("stick:" + sid)
    print("rooted in:", (r or {}).get("refs"), "via", (r or {}).get("through"))
    print("fit:", TS.read(sid).get("fit", {}).get("open", "")[:140])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
