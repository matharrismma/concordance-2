#!/usr/bin/env python3
"""The tesseract, charted onto the capstone (Matt, 2026-10-09: "tesseract").

An object, not a domain - so it charts onto an existing floor. Its deepest tie is the shadow theme: we see a 3D
projection of a 4D object, as we see projections of a higher reality, so it charts onto the capstone, with a
connects_at to relativity (the 4th dimension made rigorous). No new floor. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_tesseract.py           # merge
    PYTHONPATH=src python tools/seed_tesseract.py --check   # validate, write nothing
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

CHART = "card_chart_tesseract"
STICK = "stick_the_tesseract_the_4_cube_and_its_shadow"
CAP = "card_floor_the_capstone"
REL = "card_floor_relativity"
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def chart_card() -> dict:
    return {
        "id": CHART, "kind": "reference",
        "title": "The tesseract — the 4-cube and its shadow",
        "body": ("A chart on the one map: the tick stick " + STICK + ", placed on the capstone. The 4-cube has 16 "
                 "vertices, 32 edges, 24 faces, 8 cubic cells, and its 4D Euler sum V-E+F-C = 0 (all sealed). We see "
                 "it only as a 3D shadow - the project's image of seeing projections of a higher reality, 'through a "
                 "glass, darkly'; many 3D shadows, one 4D object. The stick keeps its seals (read live at "
                 "/stick?id=" + STICK + "); this card is a cited pointer. Found, never generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": STICK, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart",
        "bands": ["chart", "stick", "tesseract", "hypercube", "shadow", "one map"],
        "subject": "The tesseract - the 4-cube and its shadow",
        "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [chart_card()]
BRIDGES: List[dict] = [
    {"a": CHART, "b": CAP, "relationship": "charts",
     "evidence": "the 4-cube and its 3D shadow - many projections of one higher object, the capstone's many-and-one"},
    {"a": CHART, "b": REL, "relationship": "connects_at",
     "evidence": "the 4th dimension made rigorous - distinct from spacetime's time axis, the same lesson of dimensions beyond three"},
    {"a": CHART, "b": GLOBAL_FLOOR, "relationship": "part_of",
     "evidence": "a chart on the one map, rooted in the Floor of Discovery"},
]


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_capstone as CAPS
        import seed_relativity as REL_S
        ids |= {c["id"] for c in CAPS.CARDS} | {c["id"] for c in REL_S.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] not in (GLOBAL_FLOOR, CAP, REL):
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
