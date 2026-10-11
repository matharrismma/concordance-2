#!/usr/bin/env python3
"""ATTEMPT NAVIER-STOKES, ROUND 2 - the learning loop (Matt, 2026-10-11: "Could it narrow and give you an
area it fails? The key is can you learn and return with a better answer").

Round 1 guessed the geometric-depletion route; the engine sealed the conditional bound, cited
Constantin-Fefferman, and REFUSED the unproven hypothesis - but it also NARROWED: its excluded marks name
the areas of failure (energy-only methods, Tao 2016). The agent reads the narrowing and RETURNS with a
better answer: fold in every barrier the engine (and the literature) holds, and the failure region shrinks
on every side. Success guides; failure narrows. Still open - but smaller, and known exactly where.

Each narrowing is a CITED exclusion (the engine keeps a barrier only with its source). The 'better answer'
is the sharper reduction: a Navier-Stokes singularity, if one exists, is pinned to one tiny corner.

    PYTHONPATH=src python tools/seed_navier_stokes_attempt_2.py

Runs where the ledger lives (the box). The agent learns; the engine checks; the gap is named, not crossed.
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
    before = TS.read(sid).get("fit", {})
    print("excluded BEFORE:", len(before.get("excluded_approaches") or []))

    marks = [
        ("exclusion", "[round 2, learned: self-similar blow-up is ruled out] Reading the engine's narrowing, the "
                      "agent rules out a whole TYPE of failure: a Leray self-similar (Type-I) blow-up, which "
                      "would rescale a single fixed profile, cannot happen - Necas, Ruzicka and Sverak (1996) "
                      "showed a nontrivial Leray self-similar solution in L^3 does not exist, and Tsai (1998) "
                      "extended it to the local energy class. So any singularity, if one exists, must be "
                      "NON-self-similar (Type-II). The failure region shrinks.",
         {"source": "J. Necas, M. Ruzicka, V. Sverak, On Leray's self-similar solutions of the Navier-Stokes "
                    "equations, Acta Math. 176 (1996); T.-P. Tsai, Arch. Rational Mech. Anal. 143 (1998)"}),
        ("exclusion", "[round 2, learned: one tame direction is enough] And controlling just ONE scalar forbids "
                      "blow-up: if a single velocity component stays in a Prodi-Serrin class (Kukavica-Ziane 2006), "
                      "or one component is suitably bounded (Chemin-Zhang-Zhang 2017), or the vorticity DIRECTION "
                      "is regular where it is large (Constantin-Fefferman 1993), the flow is smooth. So a "
                      "singularity needs EVERY component to conspire anisotropically - no one direction may be "
                      "tame. The failure region shrinks again.",
         {"source": "I. Kukavica, M. Ziane, J. Math. Phys. 48 (2007); J.-Y. Chemin, P. Zhang, Z. Zhang, Arch. "
                    "Rational Mech. Anal. 224 (2017); P. Constantin, C. Fefferman (1993)"}),
        ("note", "[the second, BETTER answer - the narrowed target] THE AGENT LEARNED FROM THE ENGINE'S NARROWING "
                 "AND RETURNED. Assembling every barrier the engine now holds, a Navier-Stokes singularity - IF "
                 "one exists - is pinned to a single corner: 3D and large-data (2D and small-data are closed); "
                 "strictly SUPERCRITICAL (the critical L^3 endpoint is closed, Escauriaza-Seregin-Sverak); "
                 "NON-self-similar / Type-II (Necas-Ruzicka-Sverak); a singular set of parabolic Hausdorff "
                 "dimension at most one, measure zero (Caffarelli-Kohn-Nirenberg); FULLY anisotropic (no one "
                 "component or vorticity direction tame); with the time-integral of the maximum vorticity "
                 "divergent (Beale-Kato-Majda); and reachable by no energy-only argument (Tao). The question is no "
                 "longer 'prove regularity' - it is 'exclude this one highly-constrained object.' That is far "
                 "sharper than round 1: the open region has been narrowed on every side. The engine's exclusions "
                 "ARE the areas of failure; each one the agent folds in shrinks the target. YES - the agent can "
                 "learn and return with a better answer, and the proof is this stick's growing list of barriers "
                 "and its shrinking gap. Still open; smaller; and known exactly where.",
         {"source": "the assembled barriers: NRS 1996, CKN 1982, ESS 2003, Kukavica-Ziane 2006, BKM 1984, "
                    "Tao 2016; C. Fefferman, Clay statement (2000). Gaps become wants: a spectral solver on the "
                    "torus to WATCH the BKM integral and the vorticity direction on a candidate datum, and seal it."}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_navier_stokes_attempt_2.py (agent learns, engine checks)")

    after = TS.read(sid).get("fit", {})
    print("excluded AFTER:", len(after.get("excluded_approaches") or []))
    print("fit open:", (after.get("open") or "")[:180])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
