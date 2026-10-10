#!/usr/bin/env python3
"""Chemistry on the one map (Matt, 2026-10-09: "chemistry too").

The world of substances, placed as a floor standing on the physics region. Chemistry is quantum mechanics
applied to atoms, with thermodynamics deciding direction. Four pillars rest on the floors already seeded:
  * THE PERIODIC TABLE - electrons fill quantum shells (2n^2) under Pauli exclusion; many elements, one rule.
    Rests on quantum mechanics.
  * THE CHEMICAL BOND - electrons shared or transferred; the bond is electromagnetic. Rests on Maxwell.
  * REACTION DIRECTION - a reaction runs when Delta G = Delta H - T Delta S < 0. Rests on thermodynamics.
  * CONSERVATION - atoms and mass are conserved; every equation balances. Rests on Noether.
The stick (stick_chemistry_quantum_mechanics_applied_the_periodic_table) seals the shell capacity and water's
molar mass, and cites the reactions/Gibbs/pH already sealed on the chemistry stick. MERGE-writes through
chains.merge_seed.

    PYTHONPATH=src python tools/seed_chemistry.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_chemistry.py --check   # validate, write nothing
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

FLOOR = "card_floor_chemistry"
SPINE = "card_spine_chemistry"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_chemistry_quantum_mechanics_applied_the_periodic_table"

F_QM = "card_floor_quantum_mechanics"
F_MAX = "card_floor_maxwells_equations"
F_THERMO = "card_floor_thermodynamics"
F_NOE = "card_floor_noethers_theorem"

PILLARS = [
    dict(key="periodic_table",
         title="The periodic table — electrons in quantum shells",
         body="The elements are ordered by how electrons fill quantum shells (shell n holds 2n^2, sealed) under the "
              "Pauli exclusion principle. Helium closes 2, neon closes 8 (the octet), the third shell opens 18 (the "
              "transition metals). Many elements, one filling rule. Rests on quantum mechanics.",
         rests=[(F_QM, "the periodic table is the Schrodinger equation plus Pauli exclusion: 2n^2 per shell")]),
    dict(key="chemical_bond",
         title="The chemical bond — electrons shared or transferred",
         body="A bond is electrons shared (covalent) or transferred (ionic) between atoms; it is an electromagnetic "
              "interaction, the same force Maxwell unified. Every molecule's shape and every reaction's energy is "
              "electromagnetism among electrons and nuclei. Rests on Maxwell.",
         rests=[(F_MAX, "the chemical bond is electromagnetic - electrons bound by the Coulomb force")]),
    dict(key="reaction_direction",
         title="Reaction direction — Gibbs and the second law",
         body="A reaction runs when Delta G = Delta H - T Delta S < 0 (sealed on the chemistry stick): the second "
              "law, deciding direction. Chemistry rests on the quantum for what is possible and on thermodynamics "
              "for what actually happens. Rests on thermodynamics.",
         rests=[(F_THERMO, "Delta G = Delta H - T Delta S decides which reactions run - the second law")]),
    dict(key="conservation",
         title="Conservation — atoms and mass balance",
         body="Atoms are conserved in every reaction, so every equation balances (2 H2 + O2 -> 2 H2O, sealed) and "
              "mass is conserved (water's molar mass, 18.016 g/mol, sealed). Chemistry's first law, and Noether's "
              "conserved quantity in a chemical frame. Rests on Noether.",
         rests=[(F_NOE, "conservation of atoms and mass - the balanced equation is a Noether conservation law")]),
]


def _pid(key: str) -> str:
    return f"card_chem_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — chemistry", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "chemistry", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Chemistry — quantum mechanics applied, the periodic table",
        ("The world of substances, standing on the physics region. Chemistry is the Schrodinger equation for "
         "electrons around nuclei, plus Pauli exclusion, plus electromagnetism; the periodic table falls out of the "
         "quantum shells, thermodynamics decides which reactions run, and conservation of atoms makes every equation "
         "balance. Four pillars rest on quantum mechanics (the periodic table), Maxwell (the bond), thermodynamics "
         "(Delta G), and Noether (conservation). The stick (" + STICK + ") seals the shell capacity and water's molar "
         "mass; reactions, Gibbs and pH are cited from the chemistry stick (tools/seed_chemistry.py)."),
        ["floor", "chemistry", "periodic table", "bonding", "emergence", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Chemistry — a spine", "The pillars of chemistry.",
              ["chemistry", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the world of substances on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["chemistry", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of chemistry ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the world of substances on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_quantum_mechanics as QM
        import seed_maxwells_equations as MAX
        import seed_thermodynamics as TH
        import seed_noethers_theorem as NOE
        ids |= {c["id"] for c in QM.CARDS} | {c["id"] for c in MAX.CARDS}
        ids |= {c["id"] for c in TH.CARDS} | {c["id"] for c in NOE.CARDS}
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
