#!/usr/bin/env python3
"""The Lagrangian on the one map (Matt, 2026-10-09: "Lagrangian too?" - yes).

The Hamiltonian's Legendre dual, placed as a floor whose four pillars rest on the floors already seeded. The
Lagrangian's principle (least action) and its quantum form (the path integral) are ALREADY sealed on
stick_the_principle_of_least_action; the H<->L bridge on the Legendre-transform stick. This floor gathers them
and sits beside the Hamiltonian.
  * LEAST ACTION - delta S = 0, of all paths the one that makes the action stationary. Rests on the capstone
    (many paths) and the solve path (a stationary point is an optimization).
  * THE LEGENDRE DUAL - H = p q' - L; L is T - V, H is T + V. Rests on the Hamiltonian (card_floor_the_hamiltonian).
  * THE PATH INTEGRAL - all paths weighted by e^(iS/hbar), the classical one by interference. Rests on the capstone.
  * ONE SCALAR FOR ALL OF PHYSICS - the Standard Model is a Lagrangian; Lorentz-covariant. Rests on
    card_floor_standard_model.
The stick (stick_the_lagrangian_the_hamiltonian_s_dual_and_the_path) carries the seals; this seed places the node.
MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_the_lagrangian.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_the_lagrangian.py --check   # validate, write nothing
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

FLOOR = "card_floor_the_lagrangian"
SPINE = "card_spine_the_lagrangian"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_the_lagrangian_the_hamiltonian_s_dual_and_the_path"

F_HAM = "card_floor_the_hamiltonian"
F_CAP = "card_floor_the_capstone"
F_SOLVE = "card_floor_the_solve_path"
F_SM = "card_floor_standard_model"

PILLARS = [
    dict(key="least_action",
         title="Least action — of all paths, the stationary one",
         body="delta S = 0: of all conceivable paths, nature takes the one where the action S = integral L dt is "
              "stationary. Euler-Lagrange gives Newton's F = ma from L = T - V, and the same one principle gives "
              "Maxwell and general relativity. 'Many potentials, one end' as a law of the path. Sealed on "
              "stick_the_principle_of_least_action.",
         rests=[(F_CAP, "the many paths among which one is chosen"),
                (F_SOLVE, "a stationary point is an optimization: exclude the non-stationary, converge on delta S = 0")]),
    dict(key="legendre_dual",
         title="The Legendre dual of the Hamiltonian — H = p q' − L",
         body="L and H are Legendre transforms of one another: L = T - V (the generator of the path), H = T + V (the "
              "generator of time). Free particle: L = (1/2) m v^2, p = m v, H = p v - L. Sealed on this stick and on "
              "stick_the_legendre_transform_mark_the_points_create_the_line.",
         rests=[(F_HAM, "the two faces of one dynamics: L is T - V, H is T + V, joined by the Legendre transform")]),
    dict(key="path_integral",
         title="The path integral — all paths, e^(iS/ℏ), the classical one by interference",
         body="Feynman: a quantum system takes ALL paths, each weighted by e^(iS/hbar); they interfere, and where the "
              "action is stationary the phases reinforce (the classical path), elsewhere they cancel; as hbar -> 0 "
              "only the least-action path survives. The many paths are real; the one emerges by interference. Sealed "
              "on stick_the_principle_of_least_action.",
         rests=[(F_CAP, "the many paths are real; the classical one emerges by interference")]),
    dict(key="field_theory",
         title="One scalar for all of physics — the Standard Model is a Lagrangian",
         body="The Lagrangian is a single scalar, and the whole Standard Model is defined by its Lagrangian. Unlike "
              "the Hamiltonian, which singles out time, the Lagrangian treats space and time together "
              "(Lorentz-covariant), so it is the native language of relativity and quantum field theory.",
         rests=[(F_SM, "the Standard Model is defined by its Lagrangian; the Lorentz-covariant face of the dynamics")]),
]


def _pid(key: str) -> str:
    return f"card_lag_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — the Lagrangian", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "lagrangian", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "The Lagrangian — the Hamiltonian's dual, the path chosen",
        ("L = T - V, and the action S = integral L dt. Its law is the principle of least action: of all paths, nature "
         "takes the one where the action is stationary. Four pillars rest on the floors already seeded - least action "
         "(on the capstone and the solve path), the Legendre dual (on the Hamiltonian), the path integral (on the "
         "capstone), and one scalar for all of physics (on the Standard Model). The Lagrangian is the Hamiltonian's "
         "other face: H generates time, L governs the path. The seals and the fits are on the stick (" + STICK + "); "
         "this card places it on the map (tools/seed_the_lagrangian.py)."),
        ["floor", "lagrangian", "least action", "action", "path integral", "quantum", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "The Lagrangian — a spine", "The pillars of the Lagrangian.",
              ["lagrangian", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the path side of the dynamics on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["lagrangian", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of the Lagrangian ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the path side of the dynamics on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_hamiltonian as HAM
        import seed_the_capstone as CAP
        import seed_solve_path as SP
        import seed_standard_model_chain as SM
        ids |= {c["id"] for c in HAM.CARDS} | {c["id"] for c in CAP.CARDS}
        ids |= {c["id"] for c in SP.CARDS} | {c["id"] for c in SM.CARDS}
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
