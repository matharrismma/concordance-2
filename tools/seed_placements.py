#!/usr/bin/env python3
"""SEED THE PLACEMENTS — file each uncharted stick and unmapped domain UNDER the floor whose subject it
shares, so it can inherit that floor's Scripture root (move 3 of the connection layer: close connectivity).

A placement is a TAXONOMY edge, not a proof: 'acoustics is a part of the acoustics floor', read straight
off the node's own name or title. It is NOT a chart (a chart cites a specific sealed mark and becomes a
corpus card); inheritance needs only the floor, so a node too far from the map to chart can still be
filed. Proposals (by='proposed'): the engine offering the filing, for the operator to keep or refuse. A
node whose subject matches NO floor confidently is left OPEN on purpose — a want, never a forced fit
(combinatorics, geometry, linear algebra, philosophy, archaeology have no floor yet; they stay open).

    PYTHONPATH=src python tools/seed_placements.py           # dry run — proposals + coverage, writes nothing
    PYTHONPATH=src python tools/seed_placements.py --apply    # keep them to data/placements.jsonl

Runs where the data lives (the box). Found on the node's own name, never declared past it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from concordance import chains, roots, tickstick  # noqa: E402

# subject keyword -> floor id. Keys are matched at a word start against the node's name / title lead,
# longest first, so a specific key (electrochem) wins over a general one (chem). Only confident
# categorizations: where the floor genuinely IS the home of the subject.
F = "card_floor_"
SUBJECT_FLOOR = {
    # life
    "biology": F+"biology", "genetic": F+"biology", "genetics": F+"biology", "genome": F+"biology",
    "protein": F+"biology", "alphafold": F+"biology", "enzyme": F+"biology", "metabolism": F+"biology",
    "cell": F+"biology", "microb": F+"biology", "physiology": F+"biology",
    "ecology": F+"ecology", "nutrition": F+"nutrition", "agriculture": F+"agriculture",
    "medicine": F+"medicine", "medical": F+"medicine", "exercise_science": F+"medicine", "disease": F+"medicine",
    "neuro": F+"the_mind", "neuroscience": F+"the_mind", "consciousness": F+"the_mind", "brain": F+"the_mind",
    "cognition": F+"the_mind", "perception": F+"the_mind",
    # matter / chemistry
    "electrochem": F+"chemistry", "periodic_table": F+"chemistry", "periodic": F+"chemistry",
    "molecular_geometry": F+"chemistry", "molecular": F+"chemistry", "chemistry": F+"chemistry",
    "chemical": F+"chemistry", "reaction": F+"chemistry",
    "physical_chemistry": F+"physical_chemistry", "electrochemistry": F+"physical_chemistry",
    "materials": F+"materials_science", "material": F+"materials_science", "architecture": F+"materials_science",
    "construction": F+"materials_science", "manufacturing": F+"materials_science",
    # physics
    "standard_model": F+"standard_model", "particle": F+"standard_model", "atomic": F+"standard_model",
    "condensed_matter": F+"quantum_mechanics", "quantum_computing": F+"quantum_computing",
    "quantum": F+"quantum_mechanics", "photonics": F+"optics", "optics": F+"optics", "photography": F+"optics",
    "maxwell": F+"maxwells_equations", "electrical": F+"maxwells_equations", "electromagnet": F+"maxwells_equations",
    "relativity": F+"relativity", "black_hole": F+"relativity", "black hole": F+"relativity",
    "thermodynam": F+"thermodynamics", "entropy": F+"thermodynamics", "energy": F+"thermodynamics",
    "nuclear": F+"nuclear_physics", "acoustics": F+"acoustics", "sound": F+"acoustics",
    "physical_constants": F+"metrology", "metrology": F+"metrology", "units": F+"metrology", "measurement": F+"metrology",
    # earth / sky
    "astronomy": F+"astronomy", "orbit": F+"astronomy", "ephemeris": F+"astronomy", "stellar": F+"astronomy",
    "planet": F+"astronomy", "celestial": F+"astronomy",
    "geology": F+"earth_science", "mineral": F+"earth_science", "tectonic": F+"earth_science",
    "soil": F+"soil_science", "hydrology": F+"hydrology", "oceanograph": F+"oceanography", "ocean": F+"oceanography",
    "meteorolog": F+"meteorology", "weather": F+"meteorology", "geography": F+"geography",
    # mind-made systems
    "economics": F+"economics", "finance": F+"economics", "labor": F+"economics", "real_estate": F+"economics",
    "logistics": F+"logistics", "operations_research": F+"logistics",
    "game": F+"game_theory", "chess": F+"game_theory", "pressure_fighting": F+"game_theory",
    "sports_analytics": F+"game_theory", "law": F+"law", "governance": F+"law", "education": F+"education",
    "music": F+"music", "music_theory": F+"music",
    # language
    "linguistics": F+"indo_european", "language": F+"indo_european", "phonics": F+"indo_european",
    "etymology": F+"indo_european", "wordcraft": F+"indo_european", "rhetoric": F+"indo_european",
    "grammar": F+"indo_european", "syntax": F+"indo_european", "morpholog": F+"indo_european",
    "semantic": F+"indo_european",
    # computation / information
    "computer": F+"computer_science", "computation": F+"computer_science", "algorithm": F+"computer_science",
    "information_theory": F+"computer_science", "formal_logic": F+"computer_science", "retrieval": F+"computer_science",
    "networking": F+"networking", "network": F+"networking",
    "cryptograph": F+"cryptography", "cybersecurity": F+"cryptography", "document_validation": F+"cryptography",
    # number (unanchored floors are valid placements; they inherit once their floor is anchored)
    "riemann": F+"riemann", "zeta": F+"riemann", "elliptic_curves": F+"bsd", "elliptic": F+"bsd",
    "statistics": F+"statistics", "probability": F+"statistics",
    "calendar": F+"the_calendar", "history_chronology": F+"the_calendar", "chronology": F+"the_calendar",
}
_FLOORS = set(chains.FLOORS)

# batch 2 (2026-10-11, Matt: "connect them all") — the math tools, the method, the signals, the
# principles, the engine's own pieces. Each a subject that plainly belongs under its floor.
SUBJECT_FLOOR.update({
    # the mathematical method and its instruments
    "singular value": F+"the_instruments", "every matrix": F+"the_instruments", "tensor": F+"the_instruments",
    "lagrange multiplier": F+"the_instruments", "gradient": F+"the_instruments", "divergence": F+"the_instruments",
    "line integral": F+"the_instruments", "integrals and derivatives": F+"the_instruments",
    "lebesgue": F+"the_instruments", "trigonometry": F+"the_instruments", "fibonacci": F+"the_instruments",
    "gamma function": F+"the_instruments", "parametrization": F+"the_instruments", "parametrisation": F+"the_instruments",
    "complex number": F+"the_instruments", "using imaginary": F+"the_instruments", "mandelbrot": F+"the_instruments",
    "tesseract": F+"the_instruments", "euclid": F+"the_instruments", "scribing": F+"the_instruments",
    "higher-dimensional spheres": F+"the_instruments", "the dot abstracted": F+"the_instruments",
    "combinatorics": F+"the_instruments", "geometry": F+"the_instruments", "linear algebra": F+"the_instruments",
    "mathematics": F+"the_instruments",
    # number theory / the Riemann criteria
    "hilbert-polya": F+"riemann", "riemann hypothesis": F+"riemann", "dirichlet": F+"riemann", "number theory": F+"riemann",
    # the specific math-problem floors
    "birch": F+"bsd", "swinnerton": F+"bsd", "hodge conjecture": F+"hodge", "poincare conjecture": F+"poincare",
    "p versus np": F+"p_vs_np", "navier-stokes": F+"navier_stokes", "yang-mills": F+"yang_mills",
    # the solve path — the method of getting there
    "change of domain": F+"the_solve_path", "get fairly close": F+"the_solve_path", "proven bound": F+"the_solve_path",
    "the path": F+"the_solve_path", "where two domains connect": F+"the_solve_path",
    # quantum
    "hermitian": F+"quantum_mechanics", "schrodinger": F+"quantum_mechanics", "dirac": F+"quantum_mechanics",
    "aharonov": F+"quantum_mechanics", "quantum harmonic": F+"quantum_mechanics", "relational quantum": F+"quantum_mechanics",
    "the complex field": F+"quantum_mechanics",
    # electromagnetism / signals / optics
    "superheterodyne": F+"maxwells_equations", "transceiver": F+"maxwells_equations", "receiver": F+"maxwells_equations",
    "am and fm": F+"maxwells_equations", "smith chart": F+"maxwells_equations", "cayley transform": F+"maxwells_equations",
    "vacuum triode": F+"maxwells_equations", "fiber optic": F+"optics",
    # the standard model and the forces
    "standard model": F+"standard_model", "feynman": F+"standard_model", "the one force": F+"standard_model",
    "the symmetry": F+"standard_model", "gauge": F+"standard_model",
    # relativity
    "is gravity a force": F+"relativity", "time and space": F+"relativity", "quantum gravity": F+"relativity",
    # the physics principles and seams
    "noether": F+"noethers_theorem", "the hamiltonian": F+"the_hamiltonian", "least action": F+"the_lagrangian",
    "the lagrangian": F+"the_lagrangian", "legendre transform": F+"the_lagrangian",
    # the capstone — the engine's wholeness themes
    "the capstone": F+"the_capstone", "construct creation": F+"the_capstone", "final assembly": F+"the_capstone",
    "the symphony": F+"the_capstone", "joined bubbles": F+"the_capstone", "the clock": F+"the_capstone",
    "tourbillon": F+"the_capstone",
    # the rest
    "monte carlo": F+"statistics", "gaussian process": F+"statistics", "jevons": F+"economics",
    "resonance disaster": F+"acoustics", "spherical parallel": F+"materials_science", "three motors": F+"materials_science",
    "god works in multiplication": F+"logarithm", "genomics": F+"biology", "information theory": F+"computer_science",
})

# where a DOMAIN's name alone does not name a floor — explicit, precise, no fuzzy match. Each floor is
# anchored (batch 3) so the domain inherits a real verse.
DOMAIN_OVERRIDE = {
    "combinatorics": "the_instruments", "geometry": "the_instruments", "linear_algebra": "the_instruments",
    "mathematics": "the_instruments", "number_theory": "riemann", "formal_logic": "computer_science",
    "information_theory": "computer_science", "lagarias": "riemann", "nicolas": "riemann", "robin": "riemann",
    "schoenfeld": "riemann", "gue": "riemann", "zero_count": "riemann", "count_residual": "riemann",
    "condensed_matter": "quantum_mechanics", "physics": "the_hamiltonian", "physical_constants": "metrology",
    "exercise_science": "medicine", "operations_research": "logistics", "real_estate": "economics",
    "document_validation": "cryptography", "pressure_fighting": "game_theory", "sports_analytics": "game_theory",
    "trajectory": "the_solve_path", "archaeology": "geography", "philosophy": "the_mind",
}
# the last few sticks whose short lead matched no key — placed precisely by id (no fuzzy guess).
STICK_OVERRIDE = {
    "stick_earth_science_the_planet_read_in_deep_time": "earth_science",
    "stick_harmonics_chords_are_different_shapes_of_the_same_note_a_rol": "acoustics",
    "stick_pi_the_constant_of_the_circle_is_the_constant_of_rotation": "the_instruments",
    "stick_the_mind_the_neuron_computation_and_the_hard_problem": "the_mind",
}
_KEYS = sorted(SUBJECT_FLOOR, key=len, reverse=True)   # recompute after the update


def floor_for(text: str):
    s = re.sub(r"[_]+", " ", (text or "").lower())
    lead = re.split(r"\s[-–]\s", s)[0]   # for a stick title, the subject before ' - '
    for k in _KEYS:
        kk = re.sub(r"_+", " ", k)            # a multi-word key is stored with spaces OR underscores; match either
        if re.search(r"(?<![a-z])" + re.escape(kk), lead) and SUBJECT_FLOOR[k] in _FLOORS:
            return SUBJECT_FLOOR[k]
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    si = roots.stick_floor_index()                 # already-charted sticks (skip — a chart beats a filing)
    doms = list(json.load(open("data/domain_goldens.json", encoding="utf-8")).keys())
    sticks = tickstick.listing()["sticks"]

    proposals = []   # (node, floor, why)
    for d in doms:
        if f"{F}{d}" in _FLOORS:
            continue                                # already name-matches a floor
        fl = (F + DOMAIN_OVERRIDE[d]) if d in DOMAIN_OVERRIDE else floor_for(d)
        if fl and fl in _FLOORS:
            proposals.append((roots.node_id("domain", d), fl, f"the {d.replace('_',' ')} domain is a part of {fl.replace(F,'')}"))
    for r in sticks:
        sid = r["id"]
        if sid in si:
            continue                                # already charted onto the map
        fl = (F + STICK_OVERRIDE[sid]) if sid in STICK_OVERRIDE else floor_for(r.get("question") or sid)
        if fl and fl in _FLOORS:
            proposals.append((roots.node_id("stick", sid), fl, f"'{(r.get('question') or sid)[:50]}' is a part of {fl.replace(F,'')}"))

    kept = 0
    for node, fl, why in proposals:
        if a.apply:
            res = roots.place(node, fl, why=why, by="proposed", verify=True)
            kept += 1 if res.get("ok") else 0
        print(f"  {'placed' if a.apply else 'would place'} {node[:48]:48s} -> {fl.replace(F,'')}")
    print(f"\n{len(proposals)} placements proposed" + (f"; kept {kept}" if a.apply else " (dry run)"))

    cov = roots.resolved_coverage()
    print(f"\nRESOLVED: {cov['resolved']}/{cov['total_nodes']} ({cov['pct']}%) — direct {cov['direct']}, "
          f"inherited {cov['inherited']}, open {cov['open']}, unconnected {cov['unconnected']}")
    for k, v in cov["by_kind"].items():
        print(f"  {k:7s}: direct {v['direct']}, inherited {v['inherited']}, open {v['open']} (unconnected {v['unconnected']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
