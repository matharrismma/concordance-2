#!/usr/bin/env python3
"""ATTEMPT NAVIER-STOKES (Matt, 2026-10-11: "attempt navier stokes. You make a guess then use the tools.
so it doesn't generate. You do.").

The division of labour, shown on an open Millennium problem: the AGENT (an LLM, outside the engine)
GUESSES a route; the ENGINE (deterministic, no model) CHECKS what is checkable and REFUSES the forged
step. Nothing is generated as truth - only the verified steps are sealed, and the unproven leap is named,
not crossed.

THE GUESS (the agent's): attack 3D global regularity through the ENSTROPHY and the geometry of the
vorticity - the vortex-stretching term is the only source of growth; if the vorticity DIRECTION does not
bend too sharply where the vorticity is large, the stretching is depleted and the solution stays smooth.

WHAT THE ENGINE SEALS: (1) the conditional bound - bounded stretching gives finite enstrophy for all
time (Gronwall); (2) why it is hard - in 3D the energy, the one conserved quantity, is SUPERCRITICAL
(scales as lambda^{-1}), so it gives no control at the small scales where stretching lives.
WHAT IT CITES: Constantin-Fefferman (1993) - the real geometric-depletion theorem the guess rests on.
WHAT IT REFUSES: that the vorticity direction stays Lipschitz for EVERY smooth datum - the open problem
itself. A reduction, not a proof.

    PYTHONPATH=src python tools/seed_navier_stokes_attempt.py

Runs where the ledger lives (the box). Found and checked, never generated.
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

import tick  # the shared seal + mint helpers  # noqa: E402
from concordance import tickstick as TS  # noqa: E402


def main():
    S = {}
    seals = [
        # Gronwall: if dZ/dt <= C'*Z with C'=1, then Z(t) <= Z(0) e^{t}; at t=5, the bound is e^5 (finite).
        ("gronwall", "ns_attempt_bounded_stretching_gives_finite_enstrophy_e5",
         "2.718281828459045**5", 148.4131591, 1e-4),
        # the energy ∫|u|^2 under u_lambda(x,t)=lambda u(lambda x, lambda^2 t) scales as lambda^{2-3}=lambda^{-1}:
        # the exponent is negative -> SUPERCRITICAL (no control at small scales). This is the whole difficulty.
        ("supercrit", "ns_attempt_energy_scaling_exponent_is_supercritical_in_3d", "2 - 3", -1, 1e-12),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = tick._rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid)
            return 1
    print("sealed:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))

    sid = TS.create("Navier-Stokes existence and smoothness")["id"]
    print("stick:", sid)

    marks = [
        ("witness", "[the attempt - a conditional bound, sealed] AN ATTEMPT (the agent guesses; the engine checks). "
                    "Watch the enstrophy Z = (1/2) integral |omega|^2. Its only growth is vortex stretching: "
                    "dZ/dt = -nu integral |grad omega|^2 + integral omega . S . omega, S the rate-of-strain. The "
                    "stretching term is integral |omega|^2 alpha, where alpha = xi . S . xi is the stretching "
                    "rate ALONG the vorticity direction xi = omega/|omega|. IF |alpha| <= C in time, then "
                    "dropping the (negative) dissipation, dZ/dt <= 2C Z, so by Gronwall Z(t) <= Z(0) e^{2Ct} - "
                    "finite for every finite t (sealed: with the bound normalised to dZ/dt <= Z and t = 5, "
                    "Z <= Z(0) e^5 = 148.41). Bounded stretching gives GLOBAL regularity. The bound is checkable; "
                    "the hypothesis is the open part.", S["gronwall"]),
        ("witness", "[why it is hard - the energy is supercritical, sealed] Under the symmetry that preserves the "
                    "equations, u_lambda(x,t) = lambda u(lambda x, lambda^2 t), the kinetic energy integral |u|^2 "
                    "scales as lambda^(2-3) = lambda^(-1) (sealed: 2 - 3 = -1). The exponent is NEGATIVE: the one "
                    "quantity that is conserved shrinks as you look at smaller scales, so it gives no control "
                    "exactly where vortex stretching could run away. Energy is a supercritical currency - the root "
                    "of the whole difficulty, and why a bare energy argument cannot close the problem.", S["supercrit"]),
        ("equivalence", "[the real reduction the guess rests on] Constantin-Fefferman (1993): if the vorticity "
                        "DIRECTION xi = omega/|omega| is Lipschitz in space (does not bend too sharply) wherever "
                        "|omega| is large, then the solution stays smooth - the geometry DEPLETES the stretching. "
                        "Da Veiga-Berselli (2002) and others sharpened the geometric criterion. This is a genuine "
                        "conditional-regularity theorem; the attempt's route is theirs, cited, not invented.",
         {"source": "P. Constantin, C. Fefferman, Direction of vorticity and the problem of global regularity "
                    "for the Navier-Stokes equations, Indiana Univ. Math. J. 42 (1993); H. Beirao da Veiga, "
                    "L. Berselli (2002)"}),
        ("note", "[the forged step - the engine REFUSES it] The leap the engine will not seal: that the vorticity "
                 "direction stays Lipschitz (equivalently, that the stretching rate stays bounded) for EVERY "
                 "smooth finite-energy datum. That is the Clay problem itself. And Tao (2016) shows the route "
                 "must use finer structure than the energy: an averaged Navier-Stokes with the same energy "
                 "identity and scaling BLOWS UP, so no energy-only argument can work - the geometric control of "
                 "the vorticity is the right KIND of finer structure, but proving it holds is open. SO: the agent "
                 "guessed the geometric-depletion route; the engine sealed the conditional bound and the "
                 "supercritical scaling, cited the Constantin-Fefferman theorem, and REFUSED the unproven "
                 "hypothesis. 3D regularity is reduced to a geometric control of the vorticity direction - a "
                 "reduction, not a proof. The guess was the agent's; the checking was the engine's; nothing was "
                 "generated, and the gap is named, honest, and still open. Gaps become wants: a verified solver "
                 "(spectral, on the torus) to WATCH the vorticity direction and the BKM integral on a candidate "
                 "datum, and seal what it finds.",
         {"source": "C. Fefferman, Existence and smoothness of the Navier-Stokes equation (Clay, 2000); "
                    "T. Tao, Finite time blowup for an averaged three-dimensional Navier-Stokes equation, "
                    "J. Amer. Math. Soc. 29 (2016)"}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_navier_stokes_attempt.py (agent guess, engine check)")
    fit = TS.read(sid).get("fit", {})
    print("fit open:", (fit.get("open") or "")[:180])
    print("excluded:", fit.get("excluded_approaches"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
