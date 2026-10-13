#!/usr/bin/env python3
"""The double-slit experiment on the one map — the result CARD that hangs its stick on the floors
(gap analysis 2026-10-13: the stick was rooted to Scripture but was a floor-map ORPHAN — no card
referenced it, zero bridges). Mirrors tools/seed_chirality_autocatalysis.py.

Places `card_double_slit` (kind reference), cited to Young / Jönsson / Tonomura, `ref`→the sealed stick
`stick_the_double_slit_experiment`; bridges it part_of OPTICS, connects_at QUANTUM MECHANICS (the Born-rule
measurement) and the CAPSTONE (one source, many potential paths, one outcome), part_of the Floor of
Discovery; rooted (on the box) to 1 Corinthians 13:12 ("we see in part").

    PYTHONPATH=src python tools/seed_double_slit.py            # merge into the two map files
    PYTHONPATH=src python tools/seed_double_slit.py --check    # validate, write nothing
    PYTHONPATH=src python tools/seed_double_slit.py --anchor   # merge + root the card to Scripture (box)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

NODE = "card_double_slit"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_the_double_slit_experiment"

F_OPTICS = "card_floor_optics"
F_QM = "card_floor_quantum_mechanics"
F_CAP = "card_floor_the_capstone"
KNOWN_FLOORS = {F_OPTICS, F_QM, F_CAP, GLOBAL_FLOOR}

ROOT_REFS = ["1 Corinthians 13:12"]
ROOT_WHY = ("now we see in part: the measurement reveals one outcome from many potential paths; what happens "
            "in the collapse stays the open question (1 Cor 13:12)")

BODY = (
    "Light (and matter) sent through two slits from one source makes an interference pattern — the wave "
    "signature (fringe spacing Δy = λL/d). Yet it arrives in discrete hits whose probabilities are the "
    "squared amplitudes — the Born rule, P = |a|²/Σ|a|². And a single electron fired one at a time still "
    "builds the fringes — wave-particle duality (λ = h/p). One source, many potential paths, one outcome "
    "observed; what HAPPENS at the measurement (collapse, branching, pilot wave) is an empirically-equivalent "
    "Babel, declined, charted on the Schrödinger stick. Checkable here: optics.double_slit, "
    "quantum_computing.born_rule, optics.de_broglie. Cited: Young 1804, Jönsson 1961, Tonomura 1989."
)


def _card(cid: str, title: str, body: str, bands: List[str]) -> dict:
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": "The double-slit experiment (Young 1804; Jönsson 1961; Tonomura 1989)",
                   "url": "", "authority_tier": "reference", "ref": STICK},
        "shelf": "codex", "box": "optics", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [
    _card(NODE, "The double-slit experiment — one source, many paths, one outcome", BODY,
          ["double slit", "interference", "fringe", "Born rule", "wave-particle duality", "de Broglie",
           "Young", "measurement", "optics", "quantum mechanics", "one map"]),
]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES: List[dict] = [
    _edge(NODE, F_OPTICS, "part_of", "two-slit interference — the fringe spacing Δy = λL/d, wave optics"),
    _edge(NODE, F_QM, "connects_at", "the measured outcome is the Born rule P = |a|²/Σ|a|² — superposition to one hit"),
    _edge(NODE, F_CAP, "connects_at", "one source, many potential paths, one outcome observed"),
    _edge(NODE, GLOBAL_FLOOR, "part_of", "a proven result on the one map, rooted in the Floor of Discovery"),
]


def _validate() -> List[str]:
    errs: List[str] = []
    card_ids = {c["id"] for c in CARDS}
    if len(card_ids) != len(CARDS):
        errs.append("duplicate card ids")
    for e in BRIDGES:
        if e["a"] not in card_ids:
            errs.append(f"edge source not carded in this seed: {e['a']}")
        if e["b"] not in KNOWN_FLOORS:
            errs.append(f"edge target is not a known floor: {e['b']} (from {e['a']})")
    return errs


def _anchor() -> None:
    from concordance import roots
    print("  anchor:", roots.anchor(NODE, ROOT_REFS, why=ROOT_WHY, by="operator", data_dir=DATA))


def main() -> int:
    argv = sys.argv[1:]
    check = "--check" in argv
    anchor = "--anchor" in argv
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} card + {len(BRIDGES)} edges, root {ROOT_REFS}; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged chain_cards ({n['cards']} total, {len(CARDS)} from this seed) and "
          f"chain_bridges ({n['bridges']} total, {len(BRIDGES)} from this seed)")
    if anchor:
        _anchor()
    else:
        print(f"  (run with --anchor on the box to root {NODE} to {ROOT_REFS})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
