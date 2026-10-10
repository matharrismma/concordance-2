#!/usr/bin/env python3
"""Hermitian operators, charted onto the quantum-mechanics floor (Matt, 2026-10-09: "hermitian operators?").

Hermitian operators are the formal object UNDER the quantum region, not a physics domain beside it - observables
(real spectra), the eigenbasis door, unitary evolution and the Born rule all rest on them. So, like the Standard
Model's content, this charts the stick (stick_hermitian_operators_real_eigenvalues_the_observables) onto the
existing quantum-mechanics floor rather than making a new floor. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_hermitian_operators.py           # merge
    PYTHONPATH=src python tools/seed_hermitian_operators.py --check   # validate, write nothing
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

CHART = "card_chart_hermitian_operators"
STICK = "stick_hermitian_operators_real_eigenvalues_the_observables"
FLOOR = "card_floor_quantum_mechanics"          # already seeded by seed_quantum_mechanics
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def chart_card() -> dict:
    return {
        "id": CHART, "kind": "reference",
        "title": "Hermitian operators — real eigenvalues, the observables",
        "body": ("A chart on the one map: the tick stick " + STICK + ", placed on the quantum-mechanics floor. A "
                 "Hermitian operator A = A-dagger has real eigenvalues (so observables are Hermitian - a measurement "
                 "returns a real number), an orthonormal eigenbasis (the change-of-domain door), and generates "
                 "unitary evolution (so probability is conserved). If the Riemann zeros were such eigenvalues they "
                 "would be real - that is Hilbert-Polya. The stick keeps its seals (read live at /stick?id=" + STICK +
                 "); this card is a cited pointer, not a copy. Found, never generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": STICK, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart",
        "bands": ["chart", "stick", "hermitian", "observables", "spectral", "one map"],
        "subject": "Hermitian operators - real eigenvalues, the observables",
        "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [chart_card()]
BRIDGES: List[dict] = [
    {"a": CHART, "b": FLOOR, "relationship": "charts",
     "evidence": "real eigenvalues, the eigenbasis door, and unitary evolution - the formal object under the quantum region"},
    {"a": CHART, "b": "card_floor_riemann", "relationship": "connects_at",
     "evidence": "Hilbert-Polya: if the Riemann zeros were eigenvalues of a Hermitian operator they would be real = RH"},
    {"a": CHART, "b": GLOBAL_FLOOR, "relationship": "part_of",
     "evidence": "a chart on the one map, rooted in the Floor of Discovery"},
]


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_quantum_mechanics as QM
        import seed_chains as S3
        ids |= {c["id"] for c in QM.CARDS} | {c["id"] for c in S3.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] not in (GLOBAL_FLOOR, FLOOR):
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
