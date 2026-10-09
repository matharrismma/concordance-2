#!/usr/bin/env python3
"""Noether's theorem on the one map (Matt, 2026-10-09: "noether's theorum?" - yes).

The seam between the Lagrangian and the Hamiltonian: for every continuous symmetry of the action there is a
conserved quantity. Placed as a floor whose four pillars rest on the floors already seeded.
  * EVERY SYMMETRY A CONSERVATION LAW - the theorem (Noether 1918). Rests on the Lagrangian (symmetries of the
    action, card_floor_the_lagrangian).
  * THE INVARIANT - the conserved quantity is the same end carried through every path. Rests on the capstone
    (card_floor_the_capstone).
  * TIME GIVES ENERGY - time-translation symmetry -> energy, which is the Hamiltonian. Rests on the Hamiltonian
    (card_floor_the_hamiltonian).
  * GAUGE GIVES CHARGE - the phase (gauge) symmetry -> electric charge; the Standard Model's gauge symmetries ->
    its conserved currents. Rests on card_floor_standard_model.
The stick (stick_noether_s_theorem_every_symmetry_a_conservation_law) carries the seals; this seed places the
node. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_noethers_theorem.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_noethers_theorem.py --check   # validate, write nothing
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

FLOOR = "card_floor_noethers_theorem"
SPINE = "card_spine_noethers_theorem"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_noether_s_theorem_every_symmetry_a_conservation_law"

F_LAG = "card_floor_the_lagrangian"
F_CAP = "card_floor_the_capstone"
F_HAM = "card_floor_the_hamiltonian"
F_SM = "card_floor_standard_model"

PILLARS = [
    dict(key="symmetry_conservation",
         title="Every continuous symmetry a conservation law",
         body="Noether (1918): for every continuous symmetry of the action there is a conserved quantity, and "
              "conversely. The deepest structural theorem in physics - it says WHY the conservation laws hold. It "
              "lives on the action side, so it rests on the Lagrangian.",
         rests=[(F_LAG, "the theorem is about symmetries of the ACTION - the Lagrangian side of the dynamics")]),
    dict(key="the_invariant",
         title="The invariant — the same end carried through every path",
         body="The conserved quantity is the invariant: the same at the end as at the beginning, carried unchanged "
              "through every path the system can take. 'Many possibilities but the story ends the same' as a theorem, "
              "and found never decreed - compelled as the necessary shadow of a symmetry.",
         rests=[(F_CAP, "the conserved quantity is the 'same end' through every path - the capstone as a theorem")]),
    dict(key="time_gives_energy",
         title="Time-translation symmetry gives energy — the Hamiltonian",
         body="The laws do not change in time; Noether turns that one symmetry into conservation of energy - and "
              "energy is exactly the Hamiltonian. So the Lagrangian's symmetry produces the Hamiltonian's conserved "
              "quantity: Noether is the seam between the two floors.",
         rests=[(F_HAM, "time-translation symmetry -> conserved energy = the Hamiltonian; the seam between L and H")]),
    dict(key="gauge_gives_charge",
         title="Gauge symmetry gives charge — the Standard Model's currents",
         body="The phase (gauge) symmetry of the wavefunction gives conservation of electric charge; the Standard "
              "Model's gauge symmetries give its conserved currents. The forces themselves are read off the "
              "symmetries, with Noether supplying their conserved charges.",
         rests=[(F_SM, "the gauge symmetries of the Standard Model -> its conserved Noether currents and charges")]),
]


def _pid(key: str) -> str:
    return f"card_noether_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — Noether's theorem", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "noether", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Noether's theorem — symmetry is the source of conservation",
        ("For every continuous symmetry of the action there is a conserved quantity (Emmy Noether, 1918). The seam "
         "between the Lagrangian and the Hamiltonian: the Lagrangian's time-symmetry PRODUCES the Hamiltonian's "
         "conserved energy. Four pillars rest on the floors already seeded - the theorem (on the Lagrangian), the "
         "invariant (on the capstone, the same end through every path), time gives energy (on the Hamiltonian), and "
         "gauge gives charge (on the Standard Model). Conservation laws are found, never decreed - compelled as the "
         "shadow of a symmetry. The seals are on the stick (" + STICK + "); this card places it on the map "
         "(tools/seed_noethers_theorem.py)."),
        ["floor", "noether", "symmetry", "conservation", "invariant", "quantum", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Noether's theorem — a spine", "The pillars of Noether's theorem.",
              ["noether", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the symmetry-conservation seam on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["noether", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of Noether's theorem ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the symmetry-conservation seam on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_lagrangian as LAG
        import seed_the_hamiltonian as HAM
        import seed_the_capstone as CAP
        import seed_standard_model_chain as SM
        ids |= {c["id"] for c in LAG.CARDS} | {c["id"] for c in HAM.CARDS}
        ids |= {c["id"] for c in CAP.CARDS} | {c["id"] for c in SM.CARDS}
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
