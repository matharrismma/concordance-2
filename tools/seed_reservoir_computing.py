#!/usr/bin/env python3
"""Reservoir computing among the instruments — and OUR USE of it (Matt, 2026-10-31: "mint the card, but also find our
use of reservoir computing. Any of the things that fit mean they are efficient.").

A reservoir computer is the next low-tech instrument in the lineage (tools/seed_instruments_lineage.py): a FIXED
substrate — a random recurrent net, a bucket of water, a silicon circuit — that computes by STRUCTURE, with the only
trained part a linear READOUT. The sealed marks live on the stick (data/sticks/reservoir_computing.json; run
`tick.py reservoir_computing`); this seed puts the card in the keeping and declares its edges on the one map.
MERGE-writes through chains.merge_seed (idempotent; run on the box, then restart).

    PYTHONPATH=src python tools/seed_reservoir_computing.py            # merge
    PYTHONPATH=src python tools/seed_reservoir_computing.py --check    # validate, write nothing
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

F_INSTR = "card_floor_the_instruments"
F_LOG = "card_floor_logarithm"
F_CS = "card_floor_computer_science"
F_MIND = "card_floor_the_mind"
DOCTRINE = "card_doctrine_reservoir_manifold"          # Matt: value is in the routing layer, not the engine
ENGINE = "card_tool_the_engine_among_the_instruments"  # our place, from the instruments lineage
GLOBAL_FLOOR = "card_k_floor_of_discovery"
EXTERNAL = {F_INSTR, F_LOG, F_CS, F_MIND, DOCTRINE, ENGINE, GLOBAL_FLOOR}


def _card(cid: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — the instruments", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": "reference", "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "instruments", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [
    _card(
        "card_tool_reservoir_computing",
        "Reservoir computing — a fixed substrate, a trained readout; our use of it",
        "A reservoir computer never trains its dynamical system. A FIXED, random, high-dimensional substrate "
        "is driven by the input and only a LINEAR READOUT y = sum w_i x_i learns, by one closed-form regression "
        "(Jaeger 2001, echo state networks; Maass, Natschlaeger and Markram 2002, liquid state machines). The "
        "substrate may be hardware: a bucket of water solved XOR and spoken digits from a photograph of its "
        "ripples (Fernando and Sojakka 2003); silicon, optics and spintronics since (Tanaka et al. 2019). Of a "
        "100-unit reservoir with one readout the trained weights are 1/101 of the whole - sealed on the "
        "reservoir_computing stick (run tick.py reservoir_computing), with the readout's arithmetic: it is a "
        "RIEMANN SUM, and zero times infinity is a number only because the width is bound to the count - the "
        "left-sum error 1/(2n) - 1/(6n^2), the midpoint error 1/(12n^2), the Darboux gap 1/n (the integral "
        "exists iff floor meets ceiling), the UNBOUND sum diverging, Monte Carlo at 1/sqrt(n). "
        "OUR USE: the keeping is the reservoir - 933,479 found, verified, cited and sealed cards that are never "
        "retrained - and the readout is the only thing that moves: the pheromone trail (one decaying number per "
        "card, 0.25 left after two thirty-day half-lives, 49.97 bytes a trail measured on the box), the faces' "
        "scope weights and the winning-ticket mask, the chains' priced cost bands, the trajectory of a path "
        "(Wilson floor, width 1/sqrt(n)), the physiology load tally (six-hour half-life), the quorum and the "
        "elders' counts; in the fuel layer a frozen base with a rank-16 adapter (1/272 trained, sealed). Every "
        "one of these fits, and a fit is efficient for one reason: training is a thin linear readout over a fixed "
        "substrate, never the substrate itself. The boundary: a model inside the answering loop would be "
        "retraining the reservoir, and an unbound weight is a hub. Rests on the instruments, the computer, the "
        "mind and the logarithm (fading memory is e^(-t/tau)); Matt's reservoir-and-manifold doctrine says the "
        "same in energy terms - the manifold is the readout, and it is linear.",
        ["reservoir computing", "reservoir computer", "echo state network", "echo state", "liquid state machine",
         "readout", "linear readout", "fading memory", "riemann sum", "zero times infinity", "darboux",
         "stigmergy", "pheromone", "winning ticket", "lora", "instrument", "no-code", "one map", "our use"],
        ref=F_CS),
]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES: List[dict] = [
    _edge("card_tool_reservoir_computing", F_INSTR, "part_of",
          "a low-tech instrument: a bucket of water computes by structure; only the readout is trained"),
    _edge("card_tool_reservoir_computing", F_CS, "connects_at",
          "a fixed substrate plus a trained linear readout is a complete computer (Jaeger 2001; Maass 2002)"),
    _edge("card_tool_reservoir_computing", F_LOG, "connects_at",
          "the echo state property is fading memory e^(-t/tau); a half-life is ln 2 over the rate"),
    _edge("card_tool_reservoir_computing", F_MIND, "connects_at",
          "the liquid state machine models a cortical microcircuit as the reservoir, readouts as the learners"),
    _edge("card_tool_reservoir_computing", DOCTRINE, "connects_at",
          "the reservoir and the manifold: the manifold (routing layer) is the readout, and it is linear"),
    _edge("card_tool_reservoir_computing", ENGINE, "connects_at",
          "our place: the keeping is the reservoir, the faces and trails are the readout - each fit is efficient"),
]


def _validate() -> List[str]:
    errs: List[str] = []
    ids = {c["id"] for c in CARDS} | EXTERNAL
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids:
            errs.append(f"edge target unknown: {e['b']}")
    if len({c["id"] for c in CARDS}) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards, {len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
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
