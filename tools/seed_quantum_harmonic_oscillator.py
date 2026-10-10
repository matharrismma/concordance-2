#!/usr/bin/env python3
"""The quantum harmonic oscillator, charted onto the quantum-mechanics floor (Matt, 2026-10-09).

The QHO is a system, not a domain - so, like Hermitian operators, it charts onto the quantum-mechanics floor
rather than making a new floor. It carries a connects_at to the Standard Model (the field-as-oscillators bridge:
a particle is a quantum of a field's oscillator). MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_quantum_harmonic_oscillator.py           # merge
    PYTHONPATH=src python tools/seed_quantum_harmonic_oscillator.py --check   # validate, write nothing
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

CHART = "card_chart_quantum_harmonic_oscillator"
STICK = "stick_the_quantum_harmonic_oscillator_zero_point_and_the_ladder"
FLOOR = "card_floor_quantum_mechanics"
SM = "card_floor_standard_model"
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def chart_card() -> dict:
    return {
        "id": CHART, "kind": "reference",
        "title": "The quantum harmonic oscillator — zero-point and the ladder",
        "body": ("A chart on the one map: the tick stick " + STICK + ", placed on the quantum-mechanics floor. The "
                 "oscillator's ground state is 1/2 hbar omega (the zero-point, forced by uncertainty), its levels an "
                 "evenly-spaced ladder E_n = (n + 1/2) hbar omega. Every potential near its minimum is a QHO, and "
                 "every quantum field is a set of oscillators whose rungs are particles - the bridge to the Standard "
                 "Model. The stick keeps its seals (read live at /stick?id=" + STICK + "); this card is a cited "
                 "pointer, not a copy. Found, never generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": STICK, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart",
        "bands": ["chart", "stick", "quantum harmonic oscillator", "zero-point", "one map"],
        "subject": "The quantum harmonic oscillator - zero-point and the ladder",
        "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [chart_card()]
BRIDGES: List[dict] = [
    {"a": CHART, "b": FLOOR, "relationship": "charts",
     "evidence": "the zero-point and the ladder - the oscillator forced by uncertainty, on the quantum floor"},
    {"a": CHART, "b": SM, "relationship": "connects_at",
     "evidence": "the field-as-oscillators bridge: a particle is a quantum of a field's harmonic oscillator"},
    {"a": CHART, "b": GLOBAL_FLOOR, "relationship": "part_of",
     "evidence": "a chart on the one map, rooted in the Floor of Discovery"},
]


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_quantum_mechanics as QM
        import seed_standard_model_chain as SMC
        ids |= {c["id"] for c in QM.CARDS} | {c["id"] for c in SMC.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] not in (GLOBAL_FLOOR, FLOOR, SM):
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
        print(f"[check] {len(CARDS)} card (the chart), {len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
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
