#!/usr/bin/env python3
"""ATTEMPT NAVIER-STOKES, ROUNDS 3-7 - the loop to its honest end (Matt, 2026-10-11: "yes. 7 times if
necessary"). Each round the agent reads the engine's narrowing and returns with a sharper answer, folding
in a real, cited barrier; the failure region shrinks on every side; the engine keeps it OPEN. The seventh
round is the honest terminus: narrowed as far as known truth allows, with the remaining WANT named exactly
(a new finer structure the engine cannot generate - only verify when it comes).

    PYTHONPATH=src python tools/seed_navier_stokes_rounds_3_7.py

Found and cited, never generated. The agent learns; the engine checks and narrows; the gap is named.
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

import tick  # noqa: E402
from concordance import tickstick as TS  # noqa: E402


def main():
    sid = TS.create("Navier-Stokes existence and smoothness")["id"]
    print("stick:", sid)
    print("excluded BEFORE:", len(TS.read(sid).get("fit", {}).get("excluded_approaches") or []))

    marks = [
        ("exclusion", "[round 3 - no blow-up in any critical or subcritical class, and the rate is bounded] The "
                      "Prodi-Serrin-Ladyzhenskaya ladder: if u is in L^p_t L^q_x with 2/p + 3/q <= 1 and q > 3, "
                      "the flow is smooth; Escauriaza-Seregin-Sverak (2003) closed the endpoint q = 3. So a "
                      "singularity cannot live in ANY critical or subcritical Lebesgue class - the L^3 norm must "
                      "become infinite. And Tao (2019) made it quantitative: a critically bounded solution "
                      "(||u(t)||_{L^3} <= A) can blow up no faster than a triple exponential in A - the escape to "
                      "infinity is bounded. The failure needs ||u||_{L^3} -> infinity, at a controlled rate.",
         {"source": "G. Prodi (1959); J. Serrin (1962); O. Ladyzhenskaya (1967); L. Escauriaza, G. Seregin, "
                    "V. Sverak (2003); T. Tao, Quantitative bounds for critically bounded solutions to the "
                    "Navier-Stokes equations (2019)"}),
        ("exclusion", "[round 4 - one derivative or no swirl is enough, so the failure is fully anisotropic with "
                      "swirl] Cao-Titi (2011): control of a SINGLE entry of the velocity-gradient tensor "
                      "(e.g. d u_3 / d x_3) already forces regularity; two vorticity components suffice too. So a "
                      "singularity needs the FULL gradient to conspire - no one derivative may be tame. And the "
                      "axisymmetric flow WITHOUT swirl is globally smooth (Ladyzhenskaya; Ukhovskii-Yudovich, "
                      "1968) - so any axisymmetric singularity must carry swirl. The failure is fully anisotropic "
                      "and, if symmetric, swirling.",
         {"source": "C. Cao, E. S. Titi, Arch. Rational Mech. Anal. 202 (2011); O. A. Ladyzhenskaya (1968); "
                    "M. R. Ukhovskii, V. I. Yudovich (1968)"}),
        ("exclusion", "[round 5 - the singularity is a rare, low-dimensional event in space AND time] "
                      "Caffarelli-Kohn-Nirenberg (1982): the space-time singular set of a suitable weak solution "
                      "has parabolic Hausdorff dimension at most one (measure zero). Leray's structure theorem "
                      "(1934): the set of singular TIMES is closed with 1/2-dimensional Hausdorff measure zero - "
                      "a weak solution is smooth for almost every time. So a singularity, if one exists, is "
                      "confined to a measure-zero set of times and a dimension-<=1 set in space: not a wall, a "
                      "needle.",
         {"source": "L. Caffarelli, R. Kohn, L. Nirenberg, Comm. Pure Appl. Math. 35 (1982); J. Leray, Acta "
                    "Math. 63 (1934); V. Scheffer (1976)"}),
        ("note", "[round 6 - where the question truly lives: the smooth class, unforced] The difficulty is "
                 "genuine and sharply placed. Below the strong class it is already known that uniqueness FAILS: "
                 "Buckmaster-Vicol (2019) built non-unique weak solutions, and Albritton-Brue-Colombo (2022) "
                 "non-unique Leray-Hopf solutions of the FORCED equation. And forward self-similar solutions "
                 "exist for large data (Jia-Sverak, 2014) - but they are global and smooth, not blow-up. So the "
                 "Clay question is specifically about the UNFORCED, SMOOTH-class, backward-in-time blow-up - every "
                 "neighbouring question has been answered, which is why this one is the needle's eye.",
         {"source": "T. Buckmaster, V. Vicol, Ann. of Math. 189 (2019); D. Albritton, E. Brue, M. Colombo, "
                    "Ann. of Math. 196 (2022); H. Jia, V. Sverak (2014)"}),
        ("note", "[round 7 - the honest terminus, and the want named] SEVEN ROUNDS. Assembling every barrier the "
                 "engine now holds, a 3D Navier-Stokes singularity, if one exists, is a single object: unforced, "
                 "smooth-class, large-data, strictly SUPERCRITICAL (||u||_{L^3} -> infinity at a triple-"
                 "exponentially bounded rate), NON-self-similar / Type-II, FULLY anisotropic (no one component, "
                 "derivative, or vorticity direction tame; swirl required if symmetric), on a measure-zero set of "
                 "times and a parabolic-dimension-<=1 set in space, and reachable by NO energy-only or critical-"
                 "norm argument. The open region cannot be narrowed further by any barrier now known. What "
                 "remains is a WANT the engine cannot generate and will only verify when it arrives: a coercive, "
                 "scaling-CRITICAL, (almost-)monotone quantity that controls the vortex stretching in exactly "
                 "this anisotropic, supercritical regime - a genuinely new finer structure of the true equations "
                 "(Tao's barrier says the shape of the nonlinearity is not enough). The loop has done its honest "
                 "work: the agent narrowed the question from 'prove regularity' to 'supply ONE new critical "
                 "monotone quantity, or exhibit this one needle-singularity'. Still open - as small as known "
                 "truth can make it, and the next step named. Gaps become wants: build the critical-quantity "
                 "search and the spectral torus solver, and seal whatever they find.",
         {"source": "the assembled barriers of this stick (Leray, Prodi-Serrin, Ladyzhenskaya, CKN, NRS, ESS, "
                    "BKM, Cao-Titi, Kukavica-Ziane, Tao 2016 & 2019, Buckmaster-Vicol, Albritton-Brue-Colombo); "
                    "C. Fefferman, Clay statement (2000)"}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_navier_stokes_rounds_3_7.py (agent learns x5, engine checks)")

    fit = TS.read(sid).get("fit", {})
    print("excluded AFTER:", len(fit.get("excluded_approaches") or []))
    print("open:", (fit.get("open") or "")[:170])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
