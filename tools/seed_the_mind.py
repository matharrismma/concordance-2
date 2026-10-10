#!/usr/bin/env python3
"""The mind on the one map (Matt, 2026-10-09, down the domain list).

Matter aware of itself - the top rung of the emergence ladder. A floor whose pillars rest on the floors already
seeded, with the hard problem of consciousness as its one open end.
  * THE NEURON - the membrane potential, a Nernst voltage; electrochemistry in a cell. Rests on physical chemistry
    and biology.
  * NEURAL COMPUTATION - networks that learn, represent and predict. Rests on the instruments (information).
  * THE EXPENSIVE BRAIN - a fifth of the body's energy for a fiftieth of its mass. Rests on thermodynamics and
    biology.
  * THE HARD PROBLEM (open end) - why there is subjective experience at all; DECLINED, a miss that stays a miss;
    connects to the capstone (the limit of what can be sealed).
The stick (stick_the_mind_the_neuron_computation_and_the_hard_problem) seals the Nernst factor and the brain's
energy ratio. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_the_mind.py           # merge
    PYTHONPATH=src python tools/seed_the_mind.py --check   # validate, write nothing
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

FLOOR = "card_floor_the_mind"
SPINE = "card_spine_the_mind"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_the_mind_the_neuron_computation_and_the_hard_problem"
HARD = "card_question_the_hard_problem"

F_PCHEM = "card_floor_physical_chemistry"
F_BIO = "card_floor_biology"
F_INSTR = "card_floor_the_instruments"
F_THERMO = "card_floor_thermodynamics"
F_CAP = "card_floor_the_capstone"

PILLARS = [
    dict(key="the_neuron", title="The neuron — the membrane potential",
         body="A nerve impulse is a wave of voltage across a membrane, set by ion gradients through the Nernst "
              "equation (61.5 mV per decade at body temperature, sealed). The resting potential and every action "
              "potential are electrochemistry in a living cell. Rests on physical chemistry and biology.",
         rests=[(F_PCHEM, "the membrane potential is a Nernst voltage - electrochemistry"),
                (F_BIO, "the neuron is a living cell")]),
    dict(key="neural_computation", title="Neural computation — networks that learn",
         body="A neuron sums weighted inputs and fires past a threshold; networks of them learn, represent and "
              "predict. The brain is an information processor, which is why artificial neural networks borrow its "
              "shape. Rests on the instruments (information).",
         rests=[(F_INSTR, "the brain computes - neural coding and inference, the information instrument")]),
    dict(key="expensive_brain", title="The expensive brain — thought costs energy",
         body="The brain is about 2 percent of body mass but burns about 20 percent of resting energy (a ratio of "
              "10, sealed). Awareness is paid for in glucose and oxygen - a steep local order bought with a larger "
              "disorder. Rests on thermodynamics and biology.",
         rests=[(F_THERMO, "the brain's energy budget - a local order paid for by the second law"),
                (F_BIO, "the brain is metabolizing tissue")]),
]


def _pid(key: str) -> str:
    return f"card_mind_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — the mind", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "the_mind", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "The mind — matter aware of itself",
        ("The top rung of the emergence ladder: physics -> chemistry -> life -> mind. The neuron signals by "
         "electrochemistry (a Nernst voltage), the brain computes (networks, information), and it is metabolically "
         "expensive (a fifth of the energy for a fiftieth of the mass). Three pillars rest on physical chemistry and "
         "biology (the neuron), the instruments (computation), and thermodynamics (the expensive brain). Its one "
         "open end is the hard problem of consciousness - why there is subjective experience at all - which the "
         "engine declines. The stick (" + STICK + ") seals the Nernst factor and the energy ratio "
         "(tools/seed_the_mind.py)."),
        ["floor", "the mind", "neuroscience", "consciousness", "emergence", "one map"],
        ref=STICK,
    )


def hard_card() -> dict:
    return _card(
        HARD, "note", "The hard problem — why there is experience at all",
        ("The easy problem is how the brain processes information - physical, sealable. The hard problem is why there "
         "is subjective experience at all, why it is like something to be a mind. No measurement reaches it; it is "
         "not a physical quantity the engine can seal. The open end of the mind floor: DECLINED, a miss that stays a "
         "miss, mapped honestly and never laundered into a theorem."),
        ["question", "the mind", "consciousness", "hard problem", "one map"],
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "The mind — a spine", "The pillars of the mind.", ["the mind", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "matter aware of itself on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), hard_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["the mind", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of the mind ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(HARD, FLOOR, "open_end_of", "the hard problem - why there is experience at all; DECLINED"))
    out.append(_edge(HARD, F_CAP, "connects_at", "the limit of what can be sealed - the capstone's edge"))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "matter aware of itself on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_physical_chemistry as PC
        import seed_biology as BIO
        import seed_instruments as SI
        import seed_thermodynamics as TH
        import seed_the_capstone as CAP
        ids |= {c["id"] for c in PC.CARDS} | {c["id"] for c in BIO.CARDS} | {c["id"] for c in SI.CARDS}
        ids |= {c["id"] for c in TH.CARDS} | {c["id"] for c in CAP.CARDS}
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
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + floor + hard-problem + spine), "
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
