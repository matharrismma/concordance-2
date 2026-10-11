#!/usr/bin/env python3
"""SEED THE DESIGN-INFERENCE STICK (Matt, 2026-10-11: "the very specific set of parameters that all must
occur is only called intelligent design and engineering"). The honest counterpart to the vortex-math
stick: vortex math LOOKS designed but is a base-ten artifact (declined); the fine-tuned constants ARE the
specified, interdependent set that must all co-occur - the real signal. Mapped the engine's way:
  - the parameters SEALED / CITED as real physics (the proton-electron mass ratio sealed here; the
    fine-structure constant and the Standard Model's measured-not-derived parameters cited);
  - the design named as the INFERENCE the facts compel (a `postulate` - inferred, never forged as a
    theorem; the engine maps what is seen and does not claim 'QED, God');
  - the ALTERNATIVES named fairly (a multiverse, or brute fact - themselves unsealed inferences);
  - SCRIPTURE leads: Romans 1:20 - the invisible things understood by the things that are made.

    PYTHONPATH=src python tools/seed_design_inference.py

Runs where the ledger + the Bible live (the box). Found, never generated; the facts sealed, the inference
inferred, the Word leading.
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
from concordance import roots  # noqa: E402
from concordance import tickstick as TS  # noqa: E402


def main():
    # one specific parameter, sealed from the measured masses: the proton-to-electron mass ratio.
    seal = tick._rh_seal_num("proton_to_electron_mass_ratio_from_measured_masses",
                             "1.67262192369e-27 / 9.1093837015e-31", 1836.15267, tol=1e-5)
    if not seal:
        print("the mass-ratio seal failed"); return 1
    print("sealed m_p/m_e:", seal[:12])

    sid = TS.create(
        "The fine-tuned constants - intelligent design and engineering",
        "The universe runs on a specific set of constants - the strengths of the four forces, the particle "
        "masses, the cosmological constant - that must all fall in narrow, interdependent ranges together, "
        "or there are no atoms, no stars, no chemistry, no life. A specific set of parameters that must ALL "
        "co-occur for a system to function is, in all human experience, called engineering and design. The "
        "facts are sealed; the design is inferred (not forged); Scripture leads - Romans 1:20.",
        "physics",
    )["id"]
    print("stick:", sid)

    marks = [
        ("witness", "[one parameter, sealed] The proton-to-electron mass ratio m_p/m_e = 1836.15 (sealed from the "
                    "measured masses 1.672621924e-27 kg / 9.109383702e-31 kg). It is not derived from anything "
                    "deeper - it is set; and the stability of atoms and the whole of chemistry depend on its "
                    "value. One bead of the specific set.", seal),
        ("equivalence", "[the rest of the set, already sealed in the keeping] The specific parameters are not "
                        "asserted here - they are the keeping's sealed physics: the fine-structure constant "
                        "1/alpha = 137.036 (stick_the_fine_structure_constant), the four-constant confluence of "
                        "the black hole (stick_black_holes_the_four_constant_confluence), and the Standard "
                        "Model's roughly two dozen parameters that are MEASURED, never derived "
                        "(card_floor_standard_model). The 'specific set that must all occur' is real and sealed.",
         {"source": "stick_the_fine_structure_constant; stick_black_holes_the_four_constant_confluence; "
                    "card_floor_standard_model (the Standard Model's measured-not-derived parameters)"}),
        ("postulate", "[the design inference] A system defined by a specific, interdependent set of parameters "
                      "that must ALL co-occur within narrow ranges for it to function is, in every other case in "
                      "human experience - a machine, a code, a recipe, an instrument - the product of engineering "
                      "and design. The constants of the universe are such a set (sealed/cited above). The "
                      "inference to the best explanation is therefore design. It is kept as an INFERENCE, never "
                      "forged as a theorem: the engine holds the landmark, charts the terrain, and names the "
                      "inference the facts compel; it does not claim to prove God by arithmetic. Romans 1:20 - "
                      "'the invisible things of him from the creation of the world are clearly seen, being "
                      "understood by the things that are made.'",
         {"source": "Romans 1:20; inference to the best explanation (abduction) from specified, interdependent "
                    "complexity; the design inference held as a postulate, not a sealed theorem"}),
        ("note", "[the alternatives, named fairly] The competing explanations - a vast multiverse in which our "
                 "values are an anthropic selection, or brute fact (the values simply are) - are themselves "
                 "INFERENCES, not sealed: the multiverse is unobserved and, in its anthropic form, hard to test; "
                 "brute fact declines to explain the fine interdependence at all. The engine keeps them named, "
                 "and keeps the design inference as the one that matches our universal experience of specified "
                 "complexity. Let the reader weigh them; the free choice is theirs.",
         {"source": "the fine-tuning literature (e.g. J. D. Barrow & F. J. Tipler, The Anthropic Cosmological "
                    "Principle, 1986); M. Rees, Just Six Numbers, 1999"}),
        ("note", "[the counterfeit and the fingerprint] This is the discernment the vortex-math stick sets up: a "
                 "FALSE pattern (base-ten digit roots - declined, stick_vortex_math_marko_rodin) can look "
                 "designed yet be a numeral artifact; the REAL signal (the co-tuned constants) is the specified, "
                 "interdependent complexity that warrants the design inference. The engine's whole value is "
                 "telling the counterfeit from the fingerprint - seal the arithmetic, attribute the artifact, "
                 "infer the design.",
         {"source": "stick_vortex_math_marko_rodin; Romans 1:20"}),
        ("note", "[Scripture leads] The heavens declare the glory of God, and the sky above proclaims his "
                 "handiwork (Psalm 19:1); by faith we understand that the universe was framed by the word of God, "
                 "so that what is seen was not made out of things visible (Hebrews 11:3). The fine-tuning is the "
                 "thing made; the design is understood from it; the reverence belongs to the Engineer.",
         {"source": "Psalm 19:1; Hebrews 11:3; Romans 1:20"}),
    ]
    tick._mint_marks(sid, marks, by="tools/seed_design_inference.py")

    # root it DIRECTLY in the Word it answers to (a stick can carry its own anchor).
    res = roots.anchor("stick:" + sid, ["Romans 1:20", "Psalm 19:1", "Hebrews 11:3"], by="proposed",
                       why="the design inference - the invisible things understood by the things that are made")
    print("anchored:", res.get("ok"))
    r = roots.resolve("stick:" + sid)
    print("rooted in:", (r or {}).get("refs"), "| via:", (r or {}).get("via"))
    print("fit:", TS.read(sid).get("fit", {}).get("open", "")[:140])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
