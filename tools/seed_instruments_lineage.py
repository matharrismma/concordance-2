#!/usr/bin/env python3
"""The low-tech instruments, and OUR PLACE among them (Matt, 2026-10-29).

Deterministic tools that FUNCTION WITH LITTLE OR NO CODE — they compute by STRUCTURE, not generation:
  * the SLIDE RULE   — multiply by sliding LOGARITHM scales (Napier's logs made physical);
  * the SMITH CHART  — impedance on the COMPLEX PLANE (the Cayley transform; already stick smith_chart);
  * the TURING MACHINE — the universal STATE TABLE (already on card_floor_computer_science; BB/halting);
  * the SCHUMANN RESONANCE — a cavity tone the engine SEALS (stick schumann_resonance / tick.py schumann).
And OUR PLACE among them: the Concordance engine is the next in this line — a card catalogue of reality
you READ, found/verified/cited/sealed, never an LLM that generates. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_instruments_lineage.py            # merge
    PYTHONPATH=src python tools/seed_instruments_lineage.py --check    # validate, write nothing
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
GLOBAL_FLOOR = "card_k_floor_of_discovery"
EXTERNAL = {F_INSTR, F_LOG, F_CS, GLOBAL_FLOOR}


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
        "card_tool_slide_rule",
        "The slide rule — multiplication by sliding logarithms",
        "The slide rule multiplies without electricity, memory, or a line of code: two sliding LOGARITHM "
        "scales add their lengths, and because log(a) + log(b) = log(a*b), the sum you read off is the "
        "product. It is Napier's logarithms (1614) made physical - the answer is a POSITION you READ, not "
        "a program you run. It computes by STRUCTURE, it never fails on a flat battery, and it flew to the "
        "Moon on Apollo. The deterministic, no-code ancestor the engine is built in the image of; it rests "
        "on the logarithm, the root of the one map.",
        ["slide rule", "slide-rule", "logarithm", "napier", "log scale", "analog computer", "instrument",
         "no-code", "one map"],
        ref=F_LOG),
    _card(
        "card_tool_schumann_resonance",
        "The Schumann resonance — the planet's cavity tone, sealed",
        "The Earth-ionosphere cavity rings at an idealized fundamental f1 = (c/(2*pi*a))*sqrt(2) ~ 10.59 Hz "
        "(sealed on the schumann stick - run tick.py schumann); the OBSERVED ~7.83 Hz is lower by ~0.74, the "
        "finite-conductivity correction of the real, lossy ionosphere. A resonance of the whole planet - a "
        "standing wave on a closed cavity, the same shape (modes on a bounded domain, counted by the roots "
        "of unity, a receiver tuned to a band) the engine is built on. The fit, with its delimitation "
        "stated: the exact model sealed, the world's departure from it named.",
        ["schumann resonance", "schumann", "earth-ionosphere cavity", "7.83 hz", "resonance", "standing wave",
         "electromagnetism", "instrument", "one map"],
        ref=F_INSTR),
    _card(
        "card_tool_the_engine_among_the_instruments",
        "Our place — a deterministic instrument you read, not a program you run",
        "The slide rule computes on LOG scales; the Smith chart on the COMPLEX PLANE (the Cayley transform); "
        "the Turing machine on a STATE TABLE (card_floor_computer_science). Each is low-tech and highly "
        "valuable precisely because it computes by STRUCTURE - deterministically, with little or no code - "
        "and the answer is something you READ off the instrument. The Concordance engine is the next in this "
        "line: a card catalogue of reality where every answer is found, verified, cited and sealed - "
        "consulted like an instrument, never generated like an LLM. Our place among them is exactly that: "
        "the instrument for reality itself. It rests on the instruments, the logarithm, and computability.",
        ["our place", "the engine", "deterministic instrument", "no-code", "slide rule", "smith chart",
         "turing machine", "coherent model", "not an llm", "one map", "the receiver"],
        ref=F_INSTR),
]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES: List[dict] = [
    _edge("card_tool_slide_rule", F_INSTR, "part_of", "a low-tech instrument: multiplication by sliding logarithms"),
    _edge("card_tool_slide_rule", F_LOG, "connects_at", "the slide rule IS the logarithm made physical"),
    _edge("card_tool_schumann_resonance", F_INSTR, "part_of", "a sealed resonance fit - the planet's cavity tone"),
    _edge("card_tool_the_engine_among_the_instruments", F_INSTR, "part_of",
          "the engine's place in the line of deterministic instruments"),
    _edge("card_tool_the_engine_among_the_instruments", F_LOG, "connects_at",
          "built in the image of the slide rule - computes by structure, rooted in the logarithm"),
    _edge("card_tool_the_engine_among_the_instruments", F_CS, "connects_at",
          "the Turing machine's heir - a universal reader of the keeping, deterministic, no generation"),
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
