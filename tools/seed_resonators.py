#!/usr/bin/env python3
"""Resonators among the instruments — Helmholtz, the cavity, Fabry-Perot: one shape (Matt, 2026-10-31: "Helmholtz
resonator, cavity resonator, Fabry-Perot interferometer cavity").

Standing waves on a bounded domain, counted by integers, with a Q that fades. The sealed instances live on the
stick (data/sticks/resonators.json; run `tick.py resonators`); this seed puts the card in the keeping beside the
Schumann resonance (the planet-sized cavity) and the reservoir (the cavity's ring-down IS fading memory), and
declares its edges on the one map. MERGE-writes through chains.merge_seed (idempotent; run on the box, then restart).

    PYTHONPATH=src python tools/seed_resonators.py            # merge
    PYTHONPATH=src python tools/seed_resonators.py --check    # validate, write nothing
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
SCHUMANN = "card_tool_schumann_resonance"               # the planet-sized cavity (tools/seed_instruments_lineage.py)
RESERVOIR = "card_tool_reservoir_computing"             # the cavity is a reservoir (tools/seed_reservoir_computing.py)
ENGINE = "card_tool_the_engine_among_the_instruments"   # our place
GLOBAL_FLOOR = "card_k_floor_of_discovery"
EXTERNAL = {F_INSTR, F_LOG, SCHUMANN, RESERVOIR, ENGINE, GLOBAL_FLOOR}


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
        "card_tool_resonators",
        "Resonators — Helmholtz, the cavity, Fabry-Perot: one shape, a Q that fades",
        "Three instruments, one shape. The HELMHOLTZ RESONATOR (1863) is a volume of air on a neck - the air in the "
        "neck is the mass, the air in the body the spring - f = (c/2 pi) sqrt(A/(V L')), the lumped limit where the "
        "wavelength is far longer than the body: a litre bottle with a 2 cm neck sings at 118 Hz (sealed on the "
        "resonators stick; run tick.py resonators). The CAVITY RESONATOR (Hansen 1938, the rhumbatron) is a hollow "
        "conductor whose modes carry three integers, f = (c/2) sqrt((m/a)^2 + (n/b)^2 + (p/d)^2): a ten-centimetre "
        "copper cube rings at 2.12 GHz (sealed) - the shape of every klystron, magnetron and microwave filter. The "
        "FABRY-PEROT CAVITY (1897-1899) is two mirrors: a mode fits when L = n lambda/2, so the modes form a comb "
        "spaced c/2L - 1.499 GHz for 10 cm (sealed); the mirrors' reflectivity sets the finesse, pi sqrt(R)/(1-R) = "
        "312.6 at R = 0.99 (sealed), the linewidth 4.80 MHz (sealed), Q = 4.0e7 at 1550 nm (sealed). All three are "
        "standing waves on a BOUNDED DOMAIN counted by integers; the Earth-ionosphere cavity at 7.83 Hz is the "
        "planet-sized one. And every one of them FORGETS: energy decays as e^(-t/tau), tau = 1/(2 pi linewidth) = 33 "
        "ns for that cavity (sealed), about a hundred round trips (sealed) - the ring-down is the echo state "
        "property, which is why a delay loop or a laser with a feedback cavity is a reservoir computer (Appeltant "
        "2011; Brunner 2013): the cavity is the fixed substrate, the finesse its memory depth, only the readout is "
        "trained. Our place: the engine is a receiver tuned to a band - a question excites the modes that fit and "
        "nothing else, and a high-Q instrument refuses off-band, which is the zero-false-positive discipline. Rests "
        "on the instruments, the logarithm (the logarithmic decrement delta = pi/Q), the Schumann resonance and the "
        "reservoir.",
        ["resonator", "resonators", "helmholtz resonator", "helmholtz", "cavity resonator", "cavity", "rhumbatron",
         "fabry-perot", "fabry perot", "interferometer", "free spectral range", "finesse", "linewidth",
         "quality factor", "q factor", "ring-down", "standing wave", "mode", "resonance", "echo state",
         "reservoir", "receiver", "band", "instrument", "no-code", "one map"],
        ref=F_INSTR),
]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES: List[dict] = [
    _edge("card_tool_resonators", F_INSTR, "part_of",
          "three resonators, one shape: standing waves on a bounded domain, counted by integers"),
    _edge("card_tool_resonators", SCHUMANN, "connects_at",
          "the Earth-ionosphere cavity is the planet-sized cavity resonator; same count of modes, same fit"),
    _edge("card_tool_resonators", RESERVOIR, "connects_at",
          "the ring-down is fading memory: a cavity with a delay loop or a feedback laser is a reservoir computer"),
    _edge("card_tool_resonators", F_LOG, "connects_at",
          "decay per cycle is the logarithmic decrement delta = pi/Q; a ring-down is read on a log scale"),
    _edge("card_tool_resonators", ENGINE, "connects_at",
          "our place: the engine is a receiver tuned to a band - high Q answers on resonance and refuses off-band"),
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
