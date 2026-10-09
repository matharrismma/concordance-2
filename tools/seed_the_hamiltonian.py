#!/usr/bin/env python3
"""The Hamiltonian on the one map (Matt, 2026-10-09: "How does Hamiltonian fit?" - "Go").

The law of the flow: the energy operator and the generator of time evolution, placed as a floor whose four
pillars rest on the floors already seeded, with the measurement gap as its one open end.
  * THE GENERATOR - Hermitian H -> unitary evolution -> the total probability is conserved. Rests on the capstone
    (card_floor_the_capstone, the sum-to-one it preserves through time).
  * THE EIGENBASIS - the stationary states; diagonalizing H IS the change-of-domain door. Rests on the solve path
    (card_floor_the_solve_path).
  * THE CONSERVED INVARIANT - Noether: time-translation symmetry -> energy conserved; the same end through the flow.
  * THE NO-CUT BRIDGE - one generator classical<->quantum; the scale-invariant reply to Copenhagen. Rests on the
    capstone.
The OPEN END: the measurement gap - H never selects a single outcome; what it does not describe is the
actualization, answered by the capstone's single-actualization postulate, not by H. The stick
(stick_the_hamiltonian_the_law_of_the_flow) carries the seals; this seed places the node. MERGE-writes through
chains.merge_seed.

    PYTHONPATH=src python tools/seed_the_hamiltonian.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_the_hamiltonian.py --check   # validate, write nothing
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

FLOOR = "card_floor_the_hamiltonian"
SPINE = "card_spine_the_hamiltonian"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_the_hamiltonian_the_law_of_the_flow"
GAP = "card_question_measurement_gap"

F_CAP = "card_floor_the_capstone"
F_SOLVE = "card_floor_the_solve_path"

PILLARS = [
    dict(key="generator",
         title="The generator of time evolution — unitary, conserves the total",
         body="H is Hermitian, so time evolution e^(-iHt/hbar) is unitary, and unitary evolution conserves total "
              "probability. The capstone's 'many potentials sum to one' is not just an instant - the Hamiltonian "
              "preserves it at every moment of the flow. The law that keeps the many adding to one, through time.",
         rests=[(F_CAP, "the sum-to-one it preserves: Hermitian H -> unitary e^(-iHt/hbar) -> probability conserved")]),
    dict(key="eigenbasis",
         title="The energy eigenbasis — the stationary states",
         body="H psi = E psi: the eigenvectors are the stationary states, the eigenvalues the allowed energies "
              "(hydrogen's ground state 13.6057 eV, the 1/n^2 ladder - sealed on the stick). Diagonalizing H is "
              "exactly the solve path's change-of-domain door: 'go to the eigenbasis' = 'go to the Hamiltonian's "
              "frame'.",
         rests=[(F_SOLVE, "the change-of-domain door IS diagonalizing H; eigenvectors = the stationary states")]),
    dict(key="noether",
         title="The conserved invariant — energy, the same end through the flow",
         body="By Noether's theorem, time-translation symmetry gives one conserved quantity: the Hamiltonian, the "
              "energy. It is the invariant along every path the system can take. 'Many possibilities but the story "
              "ends the same way' has a precise echo - whatever path the potentials flow, H is conserved.",
         rests=[]),
    dict(key="no_cut",
         title="The no-cut bridge — one generator, classical to quantum",
         body="The same generator - energy - runs classical mechanics (Hamilton's equations) and quantum mechanics "
              "(Schrodinger). The correspondence is continuous (Ehrenfest; Poisson bracket -> commutator). No scale "
              "where energy stops being the Hamiltonian, so the quantum-to-classical passage needs no Heisenberg cut "
              "- the scale-invariant reply to Copenhagen, in one operator.",
         rests=[(F_CAP, "the no-cut, scale-invariant reply: one generator classical<->quantum, no Heisenberg cut")]),
]


def _pid(key: str) -> str:
    return f"card_ham_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — the Hamiltonian", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "hamiltonian", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "The Hamiltonian — the law of the flow",
        ("The energy operator and the generator of time evolution: it governs how the many potentials develop "
         "between the one source and the one end. Four pillars rest on the floors already seeded - the generator "
         "(unitary, conserves the total, on the capstone), the eigenbasis (the change-of-domain door, on the solve "
         "path), the conserved invariant (Noether's energy), and the no-cut bridge (one generator classical to "
         "quantum, the reply to Copenhagen). Its one open end is the measurement gap: H never selects a single "
         "outcome. The seals and the four fits are on the stick (" + STICK + "); this card places it on the map "
         "(tools/seed_the_hamiltonian.py)."),
        ["floor", "hamiltonian", "energy", "time evolution", "quantum", "one map"],
        ref=STICK,
    )


def gap_card() -> dict:
    return _card(
        GAP, "note", "The measurement gap — what the Hamiltonian does not determine",
        ("Unitary H evolution never selects a single outcome; it flows the whole superposition forward, "
         "deterministically and reversibly. What the Hamiltonian does not describe is the actualization - which one "
         "outcome occurs (von Neumann's second process). Every interpretation agrees on H and differs only here. The "
         "open edge of the Hamiltonian floor, answered by the capstone's single-actualization postulate, not by H."),
        ["question", "hamiltonian", "measurement problem", "quantum", "one map"],
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "The Hamiltonian — a spine", "The pillars of the Hamiltonian.",
              ["hamiltonian", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the law of the flow on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), gap_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["hamiltonian", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of the Hamiltonian ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(GAP, FLOOR, "open_end_of", "the measurement gap - the one outcome H does not select"))
    out.append(_edge(GAP, F_CAP, "connects_at", "answered by the capstone's single-actualization postulate, not by H"))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the law of the flow on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_capstone as CAP
        import seed_solve_path as SP
        ids |= {c["id"] for c in CAP.CARDS} | {c["id"] for c in SP.CARDS}
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
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + floor + gap + spine), "
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
