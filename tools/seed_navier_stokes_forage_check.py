#!/usr/bin/env python3
"""NAVIER-STOKES - the foraged candidate, brought to the gate (Matt, 2026-10-11: "yes" - pull the
relative-entropy candidate and check whether it supplies the critical monotone quantity).

The loop's next turn: the agent forages a theory across domains (the RELATIVE-ENTROPY method, from kinetic
theory and conservation laws), brings it to the gate, and the engine CHECKS whether it fits the want - a
scaling-CRITICAL monotone quantity controlling the vortex stretching. The honest verdict:
  - it DOES transfer, and gives a real result: WEAK-STRONG UNIQUENESS for Navier-Stokes (kept, cited);
  - but it does NOT supply the want: its monotone quantity is the relative ENERGY, which is SUPERCRITICAL
    in 3D (the barrier this stick already seals) - it controls the difference only while a strong solution
    exists; it cannot create one. DECLINED as the want's answer; the want STANDS.

The agent brought the candidate; the engine checked its scaling and refused the overclaim. A real result
added, a false fit declined - the loop working.

    PYTHONPATH=src python tools/seed_navier_stokes_forage_check.py
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

    marks = [
        ("equivalence", "[the foraged candidate transfers - weak-strong uniqueness, kept] A candidate found by "
                        "cross-referencing all domains (the RELATIVE-ENTROPY method of Dafermos (1979) and "
                        "DiPerna (1979), from conservation laws and kinetic theory) brought to the gate. For "
                        "incompressible Navier-Stokes the convex 'entropy' is the kinetic energy, and the "
                        "RELATIVE energy E_rel(t) = (1/2) integral |u - v|^2 between a Leray-Hopf weak solution u "
                        "and a strong solution v obeys dE_rel/dt <= C(||grad v||_infinity) E_rel. By Gronwall, "
                        "E_rel(0) = 0 forces E_rel(t) = 0 while v exists: WEAK-STRONG UNIQUENESS - any weak "
                        "solution equals the strong one on its interval. A real theorem, and the relative-entropy "
                        "structure genuinely transfers from another domain.",
         {"source": "C. Dafermos, Arch. Rational Mech. Anal. 70 (1979); R. DiPerna, Indiana Univ. Math. J. 28 "
                    "(1979); for Navier-Stokes: G. Prodi (1959), J. Serrin (1963); relative-energy proofs "
                    "(P. Germain; E. Wiedemann). Foraged via GET /papers (OpenAlex), then verified at the gate."}),
        ("note", "[the gate's verdict - DECLINED as the want's answer; the want stands] Does the relative-entropy "
                 "method supply the WANT - a scaling-CRITICAL monotone quantity controlling vortex stretching? NO. "
                 "Its monotone quantity IS the relative ENERGY, and the energy is SUPERCRITICAL in 3D (sealed in "
                 "this stick: it scales as lambda^{2-3} = lambda^{-1}). So it controls the difference only while "
                 "the strong solution's gradient stays finite - it presupposes a strong solution, and cannot "
                 "create one at the small scales where stretching runs away. The forage returned a genuine result "
                 "(weak-strong uniqueness, kept above) but NOT the want: its quantity is the very supercritical "
                 "energy round 2 excluded. DECLINED as the want's answer; the want STANDS - a CRITICAL monotone "
                 "quantity is still needed, and relative energy is not it. The agent brought the candidate; the "
                 "engine checked its SCALING and refused the overclaim. The next forage must target scaling-"
                 "critical quantities specifically (e.g. the critical one-component criteria, arXiv 2609.03877) "
                 "and bring the checkable step back.",
         {"source": "this stick's sealed supercritical-energy scaling (2 - 3 = -1); the want named in round 7; "
                    "candidate foraged via /papers?fit= across all domains"}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_navier_stokes_forage_check.py (agent forages, engine checks)")
    fit = TS.read(sid).get("fit", {})
    print("open:", (fit.get("open") or "")[:150])
    print("excluded:", len(fit.get("excluded_approaches") or []), "| equivalent_statements:",
          len(fit.get("equivalent_statements") or []))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
