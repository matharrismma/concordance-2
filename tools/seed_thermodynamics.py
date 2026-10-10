#!/usr/bin/env python3
"""Thermodynamics on the one map (Matt, 2026-10-09: "Thermodynamics too").

The four laws, placed as a floor. The second law is the arrow of time and the one-way flow - the physical form
of 'the story ends the same way'. Four pillars rest on the floors already seeded:
  * THE FIRST LAW - energy is conserved; = Noether's energy from time-translation symmetry. Rests on Noether.
  * THE SECOND LAW - entropy never decreases; the arrow of time; of the many microstates almost all reach the one
    maximum-entropy macrostate. Rests on the capstone (the one end, the one-way geometry).
  * STATISTICAL MECHANICS - many microstates, one macrostate (Boltzmann S = k ln W); the bridge from the reversible
    microscopic law (the Hamiltonian) to the irreversible macrostate. Rests on the Hamiltonian.
  * ENTROPY IS INFORMATION - Boltzmann, Shannon, Landauer; entropy in joules-per-kelvin and in bits are one. Rests
    on the instruments (the information-theory verifier).
The stick (stick_thermodynamics_the_arrow_and_the_one_end) seals Carnot and the first-law balance, and cites the
already-sealed second-law/Landauer and Boltzmann/Bekenstein sticks. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_thermodynamics.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_thermodynamics.py --check   # validate, write nothing
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

FLOOR = "card_floor_thermodynamics"
SPINE = "card_spine_thermodynamics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_thermodynamics_the_arrow_and_the_one_end"

F_NOE = "card_floor_noethers_theorem"
F_CAP = "card_floor_the_capstone"
F_HAM = "card_floor_the_hamiltonian"
F_INSTR = "card_floor_the_instruments"

PILLARS = [
    dict(key="first_law",
         title="The first law — energy is conserved",
         body="dU = dQ - dW: energy is conserved, counted now as heat and work. This is exactly the conserved energy "
              "Noether derives from time-translation symmetry - the same invariant, bookkept for a thermal system. "
              "Rests on Noether.",
         rests=[(F_NOE, "the first law is Noether's conserved energy, accounting heat and work")]),
    dict(key="second_law",
         title="The second law — entropy increases, the arrow, the one end",
         body="Entropy of an isolated system never decreases. The microscopic laws are time-reversible; this is where "
              "irreversibility enters - the arrow of time. Of the vast many microstates almost all flow to the one "
              "maximum-entropy macrostate: many possibilities, the same end, as a law. The one-way geometry itself "
              "(the Tesla valve). Rests on the capstone.",
         rests=[(F_CAP, "the second law is the one-way flow to the one end - 'many possibilities, the same end'")]),
    dict(key="statistical_mechanics",
         title="Statistical mechanics — many microstates, one macrostate",
         body="The bridge from the reversible microscopic law to the irreversible macrostate: 10^23 particles, one "
              "temperature and one pressure. Boltzmann S = k_B ln W counts the microstates; the macrostate is what "
              "almost all the Hamiltonian's trajectories reach. 'Many into one', statistically. Rests on the "
              "Hamiltonian.",
         rests=[(F_HAM, "statistical mechanics bridges the microscopic Hamiltonian flow to the one macrostate")]),
    dict(key="entropy_information",
         title="Entropy is information — Boltzmann, Shannon, Landauer",
         body="Entropy in joules-per-kelvin and entropy in bits are the same quantity. Landauer's limit - erasing one "
              "bit costs at least k_B T ln2 - is the bridge, and where Maxwell's demon is exorcised (sealed on "
              "stick_entropy_is_never_decreased_only_concentrated_maxwell_s_demon). Rests on the instruments, where "
              "the information-theory verifier lives.",
         rests=[(F_INSTR, "entropy = information: the information-theory instrument measures the same quantity in bits")]),
]


def _pid(key: str) -> str:
    return f"card_thermo_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — thermodynamics", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "thermodynamics", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Thermodynamics — the arrow and the one end",
        ("The four laws. The first law is energy conservation (Noether's energy, now counting heat and work). The "
         "second law - entropy never decreases - is the one place physics is not time-reversible: the arrow of time, "
         "the one-way flow, the engine of 'the story ends the same way' (of the many microstates almost all reach the "
         "one maximum-entropy macrostate). Four pillars rest on the floors already seeded: the first law (on "
         "Noether), the second law (on the capstone), statistical mechanics (on the Hamiltonian), and entropy = "
         "information (on the instruments). The stick (" + STICK + ") seals the Carnot bound and the first-law "
         "balance; the second-law/Landauer and Boltzmann/Bekenstein seals are cited (tools/seed_thermodynamics.py)."),
        ["floor", "thermodynamics", "entropy", "arrow of time", "second law", "quantum", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Thermodynamics — a spine", "The pillars of thermodynamics.",
              ["thermodynamics", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the arrow of time on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["thermodynamics", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a law of thermodynamics ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the arrow of time on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_noethers_theorem as NOE
        import seed_the_capstone as CAP
        import seed_the_hamiltonian as HAM
        import seed_instruments as SI
        ids |= {c["id"] for c in NOE.CARDS} | {c["id"] for c in CAP.CARDS}
        ids |= {c["id"] for c in HAM.CARDS} | {c["id"] for c in SI.CARDS}
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
