#!/usr/bin/env python3
"""Maxwell's equations on the one map (Matt, 2026-10-09: "Maxwell's equations too").

The FIRST unification - electricity, magnetism, and light are one electromagnetic field - placed as a floor.
No new stick: c = 1/sqrt(mu0 eps0), the flux quantum and the pairing factor are ALREADY sealed on
stick_maxwell_s_equations_and_superconductivity, which this floor cites (source.ref). Four pillars rest on the
floors already seeded:
  * THE FIRST UNIFICATION - two forces (electric, magnetic) and light become one field; the archetype of 'many
    into one' and the first rung of the one force. Rests on the capstone and the Standard Model (U(1)).
  * GAUGE SYMMETRY -> CHARGE - electromagnetism is the U(1) gauge theory; its Noether current is conservation of
    charge (the continuity equation built into Maxwell). Rests on Noether's theorem.
  * FOUR EQUATIONS, ONE FIELD; LORENTZ-COVARIANT -> RELATIVITY - the four become one relativistic equation; their
    invariance (the constancy of c) is why special relativity. Rests on the Lagrangian.
  * THE QUANTUM FORM - in a superconductor the field becomes a macroscopic quantum state and the photon gains mass
    (Meissner = Anderson-Higgs on a bench, the same mechanism that gives the W and Z mass). Rests on the Standard
    Model.
MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_maxwells_equations.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_maxwells_equations.py --check   # validate, write nothing
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

FLOOR = "card_floor_maxwells_equations"
SPINE = "card_spine_maxwells_equations"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_maxwell_s_equations_and_superconductivity"   # already minted; this floor CITES it

F_CAP = "card_floor_the_capstone"
F_SM = "card_floor_standard_model"
F_NOE = "card_floor_noethers_theorem"
F_LAG = "card_floor_the_lagrangian"

PILLARS = [
    dict(key="first_unification",
         title="The first unification — electricity, magnetism and light, one field",
         body="Maxwell showed that electricity and magnetism are one electromagnetic field, and that its waves travel "
              "at c = 1/sqrt(mu0 eps0) - the speed of light, so light IS electromagnetism (sealed on "
              "stick_maxwell_s_equations_and_superconductivity). Two forces and light become one: the archetype of "
              "'many into one' and the first rung of the one force.",
         rests=[(F_CAP, "the archetype of 'many into one' - the first rung of the one force"),
                (F_SM, "the U(1) of electromagnetism is part of the Standard Model's gauge group")]),
    dict(key="gauge_charge",
         title="U(1) gauge symmetry → conservation of charge",
         body="Electromagnetism is the U(1) gauge theory, and by Noether its symmetry gives conservation of electric "
              "charge - the continuity equation d(rho)/dt + div J = 0 is built into Maxwell's equations. The symmetry "
              "IS the source of the conserved charge.",
         rests=[(F_NOE, "the U(1) gauge symmetry -> conserved charge, via Noether's theorem")]),
    dict(key="covariance_relativity",
         title="Four equations, one field — Lorentz-covariant, the root of relativity",
         body="The four equations (Gauss, no monopoles, Faraday, Ampere-Maxwell) become a single relativistic "
              "equation, and their invariance - the constancy of c in every frame - is exactly what forced special "
              "relativity. The electromagnetic field has a Lagrangian, so it rests on the Lagrangian floor.",
         rests=[(F_LAG, "the EM field Lagrangian; manifest Lorentz covariance -> special relativity")]),
    dict(key="quantum_form",
         title="The quantum form — a macroscopic quantum state, a massive photon",
         body="In a superconductor the electromagnetic field becomes a macroscopic quantum state: flux is quantized "
              "in units h/2e and the photon gains mass (the Meissner effect = the Anderson-Higgs mechanism on a "
              "bench, the same that gives the W and Z their mass). Sealed on "
              "stick_maxwell_s_equations_and_superconductivity.",
         rests=[(F_SM, "the Anderson-Higgs mechanism: the massive photon in a superconductor, the W/Z mass in the SM")]),
]


def _pid(key: str) -> str:
    return f"card_maxwell_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — Maxwell's equations", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "maxwell", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Maxwell's equations — the first unification",
        ("Electricity, magnetism and light are one electromagnetic field, and its waves travel at the speed of light "
         "(c = 1/sqrt(mu0 eps0), sealed on " + STICK + "). The archetype of the whole project - the first time many "
         "forces became one - and the first rung of the one force. Four pillars rest on the floors already seeded: "
         "the first unification (on the capstone and the Standard Model), U(1) gauge symmetry giving charge "
         "conservation (on Noether), four equations as one Lorentz-covariant field giving relativity (on the "
         "Lagrangian), and the quantum form (on the Standard Model). No new stick - this floor cites the sealed "
         "electromagnetic constants (tools/seed_maxwells_equations.py)."),
        ["floor", "maxwell", "electromagnetism", "unification", "gauge", "relativity", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Maxwell's equations — a spine", "The pillars of the electromagnetic unification.",
              ["maxwell", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the first unification on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["maxwell", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of the electromagnetic unification ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the first unification on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_capstone as CAP
        import seed_noethers_theorem as NOE
        import seed_the_lagrangian as LAG
        import seed_standard_model_chain as SM
        ids |= {c["id"] for c in CAP.CARDS} | {c["id"] for c in NOE.CARDS}
        ids |= {c["id"] for c in LAG.CARDS} | {c["id"] for c in SM.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']} (from {e['a']})")
    if len({c["id"] for c in CARDS}) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + floor + spine), "
              f"{len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
