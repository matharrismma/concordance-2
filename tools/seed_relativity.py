#!/usr/bin/env python3
"""Relativity on the one map (Matt, 2026-10-09: "Relativity").

Many frames, one invariant - placed as a floor whose four pillars rest on the floors already seeded. Relativity
ties the whole physics region together.
  * SPECIAL RELATIVITY - the laws and c the same in every frame; many frames, one invariant interval. Rests on
    Maxwell (whose covariance forced it) and the capstone (one invariant truth under many views).
  * MASS-ENERGY - E = m c^2; mass is rest energy. Rests on the Hamiltonian (energy).
  * GENERAL RELATIVITY - gravity is the curvature of spacetime; a Lagrangian field theory (the Einstein-Hilbert
    action). Its tests are sealed on the gravity stick. Rests on the Lagrangian.
  * POINCARE SYMMETRY - boosts, rotations and translations; a continuous symmetry, so by Noether it gives the
    conserved energy, momentum and angular momentum. Rests on Noether.
The stick (stick_relativity_many_frames_one_invariant) seals the Lorentz factor and E = m c^2, and cites the
gravity stick for GR's tests. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_relativity.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_relativity.py --check   # validate, write nothing
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

FLOOR = "card_floor_relativity"
SPINE = "card_spine_relativity"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_relativity_many_frames_one_invariant"

F_MAX = "card_floor_maxwells_equations"
F_CAP = "card_floor_the_capstone"
F_HAM = "card_floor_the_hamiltonian"
F_LAG = "card_floor_the_lagrangian"
F_NOE = "card_floor_noethers_theorem"

PILLARS = [
    dict(key="special",
         title="Special relativity — many frames, one invariant",
         body="The laws and the speed of light are the same in every inertial frame; observers disagree on time and "
              "length but agree on c and on the invariant interval s^2 = (ct)^2 - x^2. A clock at 0.6c runs slow by "
              "gamma = 1.25 (sealed). Many frames, one invariant truth - the Lorentz transformation is a rotation in "
              "spacetime that preserves the interval.",
         rests=[(F_MAX, "Maxwell's Lorentz covariance and the constancy of c forced special relativity"),
                (F_CAP, "many frames, one invariant truth - the same shape as many potentials, one end")]),
    dict(key="mass_energy",
         title="Mass-energy — E = m c^2",
         body="The electron's rest energy is m_e c^2 = 0.511 MeV (sealed). Mass and energy are the same thing, and "
              "because c^2 is enormous a tiny mass is a vast energy. Mass IS rest energy - it enters the Hamiltonian "
              "as the energy a body has even at rest.",
         rests=[(F_HAM, "E = m c^2: mass is rest energy, part of the Hamiltonian")]),
    dict(key="general",
         title="General relativity — gravity is the curvature of spacetime",
         body="Mass-energy curves spacetime (the Einstein field equations) and bodies follow geodesics - the "
              "equivalence principle. Its tests (light deflection 1.75 arcsec, the gravitational redshift) are sealed "
              "on the gravity stick. GR is a Lagrangian field theory - the Einstein-Hilbert action.",
         rests=[(F_LAG, "general relativity is a Lagrangian field theory: the Einstein-Hilbert action")]),
    dict(key="poincare",
         title="Poincaré symmetry — the group that feeds Noether",
         body="The symmetry group of relativity - boosts, rotations and translations - is a continuous symmetry, so "
              "by Noether it gives the conserved energy, momentum, angular momentum and the stress-energy tensor. The "
              "symmetry of spacetime is the source of the conservation laws.",
         rests=[(F_NOE, "the Poincare symmetry group -> conserved energy, momentum, angular momentum, via Noether")]),
]


def _pid(key: str) -> str:
    return f"card_rel_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — relativity", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "relativity", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Relativity — many frames, one invariant",
        ("Special relativity: the laws and the speed of light are the same in every inertial frame; observers "
         "disagree on time and length but agree on the invariant interval - many frames, one invariant truth. "
         "General relativity: gravity is the curvature of spacetime (its tests sealed on the gravity stick). Four "
         "pillars rest on the floors already seeded: special relativity (on Maxwell and the capstone), mass-energy "
         "(on the Hamiltonian), general relativity (on the Lagrangian, the Einstein-Hilbert action), and Poincare "
         "symmetry (on Noether). Relativity ties the whole physics region. The stick (" + STICK + ") seals the "
         "Lorentz factor and E = m c^2 (tools/seed_relativity.py)."),
        ["floor", "relativity", "spacetime", "invariant", "lorentz", "quantum", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Relativity — a spine", "The pillars of relativity.",
              ["relativity", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the invariant under many frames on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["relativity", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of relativity ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the invariant under many frames on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_maxwells_equations as MAX
        import seed_the_capstone as CAP
        import seed_the_hamiltonian as HAM
        import seed_the_lagrangian as LAG
        import seed_noethers_theorem as NOE
        ids |= {c["id"] for c in MAX.CARDS} | {c["id"] for c in CAP.CARDS} | {c["id"] for c in HAM.CARDS}
        ids |= {c["id"] for c in LAG.CARDS} | {c["id"] for c in NOE.CARDS}
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
