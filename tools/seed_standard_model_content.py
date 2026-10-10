#!/usr/bin/env python3
"""The Standard Model's content, charted onto the existing floor (Matt, 2026-10-09: "standard model").

card_floor_standard_model already exists (the electroweak confluence where the two trees meet) and is the hub
that Maxwell, Noether, relativity and quantum mechanics rest on. NO new floor. This seed charts the gauge-content
stick (stick_the_standard_model_gauge_forces_and_quarks - the quark charges and the SU(3)x SU(2)x U(1) gauge
group) onto that floor, the way tools/seed_charts.py places a stick at its node. MERGE-writes through
chains.merge_seed.

    PYTHONPATH=src python tools/seed_standard_model_content.py           # merge
    PYTHONPATH=src python tools/seed_standard_model_content.py --check   # validate, write nothing
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

CHART = "card_chart_standard_model_content"
STICK = "stick_the_standard_model_gauge_forces_and_quarks"
FLOOR = "card_floor_standard_model"            # already seeded by seed_standard_model_chain
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def chart_card() -> dict:
    return {
        "id": CHART, "kind": "reference",
        "title": "The Standard Model — gauge forces and quarks",
        "body": ("A chart on the one map: the tick stick " + STICK + ", placed on the Standard-Model floor. It seals "
                 "the quark charges (the proton's +1 from +2/3, +2/3, -1/3) and the gauge group's gluon count "
                 "(SU(3) -> 8 gluons); the Standard Model is SU(3) x SU(2) x U(1), three of the four forces as gauge "
                 "theories, and it is quantum field theory - quantum mechanics married to relativity. The stick keeps "
                 "its seals (read live at /stick?id=" + STICK + "); this card is a cited pointer, not a copy. Found, "
                 "never generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": STICK, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart",
        "bands": ["chart", "stick", "standard model", "gauge", "quarks", "one map"],
        "subject": "The Standard Model - gauge forces and quarks",
        "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [chart_card()]
BRIDGES: List[dict] = [
    {"a": CHART, "b": FLOOR, "relationship": "charts",
     "evidence": "the gauge content and the quark model, charted onto the electroweak floor"},
    {"a": CHART, "b": GLOBAL_FLOOR, "relationship": "part_of",
     "evidence": "a chart on the one map, rooted in the Floor of Discovery"},
]


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_standard_model_chain as SM
        ids |= {c["id"] for c in SM.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seed:", e)
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
