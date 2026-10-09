#!/usr/bin/env python3
"""Let the function follow the form (Matt, 2026-10-09: "allow the function to follow the form" - "Yes. Go through each
one"). The form is the one map: floors, chains, joints, rooted in the Floor of Discovery. The function is the 82 tick
sticks - the engine's charted knowledge, in a store of their own, until now referenced by the map nowhere. This seeds
the connection I found and Matt told me to make: each stick that CHARTS a node of the one map is placed ON the map by
a cited edge, through the same card-form the questions and the chain records use.

A CHART card (card_chart_<key>) is a stub, like a question card: a human title, its stick in source.ref, a body that
says what it charts and why, member_of the charts spine (part_of the Floor), and ONE edge - `charts` -> the node it
charts (corpus._apply_bridges adds the reciprocal `charted_by`, so floor_map can collect a node's charts). The stick
keeps its seals; the card is a pointer, not a copy - map, never launder. The basis of each edge is a real mark on the
stick, verified before this was written (its first witness is quoted in the seed's comments).

    PYTHONPATH=src python tools/seed_charts.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_charts.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_charts"

# key, stick id, the node it charts, human title, the basis (a mark that is really on the stick).
CHARTS: List[Dict[str, str]] = [
    dict(key="standard_model", stick="stick_the_standard_model_chain_where_two_trees_connect",
         node="card_floor_standard_model", title="The Standard Model chain — where two trees connect",
         basis="the stick seals the Weinberg angle cos(theta_W) = m_W/m_Z = 0.8814, the hinge where the "
               "electromagnetic and weak trees become one - the same lineage this floor draws"),
    dict(key="fine_structure", stick="stick_the_fine_structure_constant",
         node="card_floor_standard_model", title="The fine structure constant",
         basis="the stick seals alpha = e^2/(2 eps0 h c), 1/alpha = 137.036 - the electromagnetic coupling of the "
               "unified theory this floor stands on, where electromagnetism emerges from the electroweak"),
    dict(key="langlands", stick="stick_the_langlands_program", node="card_joint_l_functions",
         title="The Langlands program", basis="the stick seals modularity for 11a1 - the curve side meeting the "
               "automorphic-form side - which is the general form of this joint: zeta and L(E,s), one machinery"),
    dict(key="weil_rh", stick="stick_finite_field_the_weil_riemann_hypothesis", node="card_joint_weil_conjectures",
         title="The finite-field (Weil) Riemann hypothesis", basis="the stick seals |alpha|^2 = q for a Frobenius "
               "eigenvalue over a finite field - the Riemann hypothesis over finite fields, which is exactly this joint"),
    dict(key="de_bruijn_newman", stick="stick_the_de_bruijn_newman_constant", node="card_question_riemann",
         title="The de Bruijn-Newman constant", basis="the stick seals the window 0 <= Lambda <= 0.22; RH is "
               "Lambda = 0 exactly - an equivalence the Riemann question already carries"),
    dict(key="zeta", stick="stick_the_zeta_function", node="card_question_riemann", title="The zeta function",
         basis="the stick seals zeta(2) = pi^2/6 (Basel) and the functional equation - the object the Riemann "
               "question is about"),
    dict(key="prime_waveforms", stick="stick_a_torus_and_the_waveforms_inside_the_prime_numbers_the_zeros",
         node="card_question_riemann", title="The waveforms inside the primes — the zeros",
         basis="the stick seals the explicit formula psi(x) = x - sum over zeros x^rho/rho - the zeros as the "
               "frequencies of the prime staircase, the heart of the Riemann question"),
    dict(key="ns_dispersion", stick="stick_navier_stokes_dissonance_and_dispersion",
         node="card_question_navier_stokes", title="Navier-Stokes — dissonance and dispersion",
         basis="the stick seals the supercritical scaling u_lambda = lambda u(lambda x, lambda^2 t) - why 3D is the "
               "hard case, the obstacle the regularity question names"),
    dict(key="ym_measure", stick="stick_yang_mills_the_mass_gap_is_a_measure",
         node="card_question_yang_mills", title="The Yang-Mills mass gap, as a measure",
         basis="the stick reads the gap as Delta = E1 - E0, a measured spectral difference - the quantity the "
               "existence-and-mass-gap question asks to be positive"),
    dict(key="grassmannian", stick="stick_the_positive_grassmannian", node="card_question_yang_mills",
         title="The positive Grassmannian", basis="the stick seals the amplituhedron's dimensions - the positive "
               "geometry that computes Yang-Mills scattering amplitudes, admissibility found, never generated"),
    dict(key="e", stick="stick_e_the_number_of_continuous_growth", node="card_floor_logarithm",
         title="e — the number of continuous growth", basis="the stick seals e = sum 1/k!; e is the base of the "
               "natural logarithm this floor's two trees become one function in"),
    dict(key="entropy", stick="stick_entropy_is_never_decreased_only_concentrated_maxwell_s_demon",
         node="card_floor_logarithm", title="Entropy — Maxwell's demon",
         basis="the stick seals the Maxwell-Boltzmann speeds; entropy is S = k log W (Boltzmann), the logarithm as "
               "the count of states - a root of this floor"),
    dict(key="godel", stick="stick_godel_s_incompleteness_theorems", node="card_question_p_vs_np",
         title="Gödel's incompleteness theorems", basis="the stick seals Gödel numbering, a sequence encoded as a "
               "product of prime powers - the encoding of computation into arithmetic that the limits of proof, and "
               "the P versus NP question, stand on"),
    dict(key="euler_char", stick="stick_topology_and_euler_s_formula", node="card_question_poincare",
         title="Topology and Euler's formula", basis="the stick seals V - E + F = 2 for the Platonic solids - the "
               "topological invariant; chi is the invariant the Poincaré question's sealed instances use (chi(S^3) = 0)"),
]


def chart_card(c: Dict[str, str]) -> dict:
    return {
        "id": f"card_chart_{c['key']}", "kind": "reference", "title": c["title"][:180],
        "body": (f"{c['title']}. A chart on the one map: this is the tick stick {c['stick']}, placed at the node it "
                 f"charts. Basis: {c['basis']}. The stick keeps its seals (read live at /stick?id={c['stick']}); this "
                 f"card is a cited pointer, not a copy. Found, never generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": c["stick"], "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart", "bands": ["chart", "stick", "two trees", "one map", c["key"]],
        "subject": c["title"],
        "connections": [],   # the edges live in the overlay (BRIDGES) so corpus._apply_bridges adds the reciprocals

        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def spine_card() -> dict:
    return {
        "id": SPINE, "kind": "reference", "title": "The charts — the sticks on the one map",
        "body": ("Where the engine's tick sticks take their place on the one map: each chart is a tick stick placed at "
                 "the node of reality it charts, by a cited edge. The function following the form - the sticks (number, "
                 "the Tree of Knowledge) joined to the graph (the named, the Tree of Life). Found, never generated "
                 "(tools/seed_charts.py)."),
        "source": {"label": "The charts - a spine of the one map", "url": "", "domain": "mathematics",
                   "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["charts", "sticks", "two trees", "one map", "spine"],
        "subject": "The charts",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "a spine of the one map, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [spine_card()] + [chart_card(c) for c in CHARTS]
BRIDGES: List[dict] = [{"a": f"card_chart_{c['key']}", "b": c["node"], "relationship": "charts",
                        "evidence": c["basis"][:300]} for c in CHARTS] +                       [{"a": f"card_chart_{c['key']}", "b": SPINE, "relationship": "member_of",
                        "evidence": "a chart on the one map"} for c in CHARTS]


def known_nodes() -> set:
    ids = set()
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_chains as S3
        import seed_millennium_chain as S2
        import seed_standard_model_chain as S1
        ids |= {c["id"] for c in S1.CARDS} | {c["id"] for c in S2.CARDS} | {c["id"] for c in S3.CARDS}
        ids |= {f"card_joint_{j['slug']}" for j in S2.JOINTS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs = []
    nodes = known_nodes()
    keys = set()
    for c in CHARTS:
        if c["key"] in keys:
            errs.append(f"duplicate key {c['key']}")
        keys.add(c["key"])
        if c["node"] not in nodes:
            errs.append(f"{c['key']}: node not on the map: {c['node']}")
        if not c["stick"].startswith("stick_"):
            errs.append(f"{c['key']}: not a stick id: {c['stick']}")
        if len(c["basis"]) < 20:
            errs.append(f"{c['key']}: basis too thin")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(CHARTS)} charts + 1 spine); {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
