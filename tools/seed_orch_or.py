#!/usr/bin/env python3
"""Orch OR, charted onto the mind floor beside the receiver chart (2026-11-27: the brain-as-instrument reading
corrected from fluid to quantum - Penrose and Hameroff's Orchestrated Objective Reduction).

A chart on card_floor_the_mind, connected to its open end (card_question_the_hard_problem), to the receiver chart
(card_chart_consciousness_receiver) and to the quantum mechanics floor. The physics is sealed on the stick
(data/sticks/orch_or.json); the hypothesis is cited and declined (the hard problem stays open). No new floor.
MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_orch_or.py           # merge
    PYTHONPATH=src python tools/seed_orch_or.py --check   # validate, write nothing
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

CHART = "card_chart_orch_or"
STICK = "stick_orch_or_consciousness_as_quantum_vibrations_in_microtubules"
FLOOR = "card_floor_the_mind"
HARD = "card_question_the_hard_problem"
RECEIVER = "card_chart_consciousness_receiver"
QM = "card_floor_quantum_mechanics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def chart_card() -> dict:
    return {
        "id": CHART, "kind": "reference",
        "title": "Orch OR - the receiver read quantum",
        "body": ("A chart on the one map: the tick stick " + STICK + ", placed on the mind floor at its open end, the "
                 "hard problem, beside the receiver chart. The brain as an instrument, read quantum, is Penrose and "
                 "Hameroff's Orchestrated Objective Reduction (Orch OR): quantum processes in neuronal microtubules, each "
                 "ending in a gravity-related reduction, with the EEG as their slow beat. The PHYSICS is sealed: at 37 C "
                 "body heat is 0.0267 eV, the energy of a 6.46 THz quantum, so a 40 Hz rhythm is classical (1.6e11 "
                 "thermal quanta) while tryptophan's ultraviolet is quantum (166 k_B T); one 25 ms reduction needs "
                 "E_G = 4.2e-33 J; the decoherence gap is 2.5e11 on Tegmark's figure and 250 on the reply's "
                 "recalculation, closed only by shielding that is proposed, not measured. The hypothesis is cited and "
                 "DECLINED - the hard problem held open, never laundered into a theorem. The stick keeps its seals "
                 "(read live at /stick?id=" + STICK + "); this card is a cited pointer. Found, never generated."),
        "source": {"label": "Narrow Highway - a chart: a tick stick placed on the one map", "url": "",
                   "ref": STICK, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "chart",
        "bands": ["chart", "stick", "consciousness", "orch or", "quantum", "microtubules", "receiver", "one map"],
        "subject": "Orch OR - the receiver read quantum",
        "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [chart_card()]
BRIDGES: List[dict] = [
    {"a": CHART, "b": FLOOR, "relationship": "charts",
     "evidence": "Orch OR (the receiver read quantum) - charted on the mind floor"},
    {"a": CHART, "b": HARD, "relationship": "connects_at",
     "evidence": "a cited hypothesis for the hard problem: consciousness as quantum reduction in microtubules - "
                 "DECLINED as proof"},
    {"a": CHART, "b": RECEIVER, "relationship": "connects_at",
     "evidence": "the receiver chart read quantum: a fast quantum carrier, the EEG its slow classical envelope"},
    {"a": CHART, "b": QM, "relationship": "connects_at",
     "evidence": "where a quantum state survives body heat (h nu against k_B T) and how long it lasts (decoherence)"},
    {"a": CHART, "b": GLOBAL_FLOOR, "relationship": "part_of",
     "evidence": "a chart on the one map, rooted in the Floor of Discovery"},
]


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_consciousness_receiver as RECV
        import seed_quantum_mechanics as QUANT
        import seed_the_mind as MIND
        ids |= {c["id"] for c in MIND.CARDS} | {c["id"] for c in RECV.CARDS} | {c["id"] for c in QUANT.CARDS}
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
