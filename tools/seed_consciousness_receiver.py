#!/usr/bin/env python3
"""Consciousness-as-receiver, charted onto the mind floor (Matt, 2026-10-09: "non local... an antennae/receiver...
closest to a crystal radio").

Matt's reading of the hard problem, placed as a chart on card_floor_the_mind and connected to its open end
(card_question_the_hard_problem). The crystal-radio physics is sealed on the stick; the consciousness hypothesis
is cited and declined (the hard problem stays open). No new floor. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_consciousness_receiver.py           # merge
    PYTHONPATH=src python tools/seed_consciousness_receiver.py --check   # validate, write nothing
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

CHART = "card_chart_consciousness_receiver"
STICK = "stick_consciousness_as_a_receiver_the_crystal_radio"
FLOOR = "card_floor_the_mind"
HARD = "card_question_the_hard_problem"
CAP = "card_floor_the_capstone"
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def chart_card() -> dict:
    return {
        "id": CHART, "kind": "reference",
        "title": "Consciousness as a receiver — the crystal radio",
        "body": ("A chart on the one map: the tick stick " + STICK + ", placed on the mind floor at its open end, the "
                 "hard problem. Matt's reading: consciousness is non-local, and the brain tunes to it like a crystal "
                 "radio (an LC tuned circuit plus a diode) rather than generating it. The radio PHYSICS is sealed "
                 "(the LC resonance, the carrier wavelength); the consciousness hypothesis (James, Huxley, Bergson) "
                 "is cited and DECLINED - the hard problem held open, never laundered into a theorem. The stick keeps "
                 "its seals (read live at /stick?id=" + STICK + "); this card is a cited pointer. Found, never "
                 "generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": STICK, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart",
        "bands": ["chart", "stick", "consciousness", "receiver", "crystal radio", "one map"],
        "subject": "Consciousness as a receiver - the crystal radio",
        "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [chart_card()]
BRIDGES: List[dict] = [
    {"a": CHART, "b": FLOOR, "relationship": "charts",
     "evidence": "consciousness as a receiver (the crystal radio) - charted on the mind floor"},
    {"a": CHART, "b": HARD, "relationship": "connects_at",
     "evidence": "a cited hypothesis for the hard problem: the brain receives, does not generate - DECLINED as proof"},
    {"a": CHART, "b": CAP, "relationship": "connects_at",
     "evidence": "one source broadcast, many receivers tuned to it - the capstone's one source"},
    {"a": CHART, "b": GLOBAL_FLOOR, "relationship": "part_of",
     "evidence": "a chart on the one map, rooted in the Floor of Discovery"},
]


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_mind as MIND
        import seed_the_capstone as CAPS
        ids |= {c["id"] for c in MIND.CARDS} | {c["id"] for c in CAPS.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] not in (GLOBAL_FLOOR, FLOOR, HARD, CAP):
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
