#!/usr/bin/env python3
"""Quantum mechanics on the one map (Matt, 2026-10-09: "What about Quantum mechanics?").

Not another floor beside the others - the FRAMEWORK they inhabit. Placed as a floor whose four pillars rest on
the floors already seeded; the three foundations it adds (quantization, uncertainty, entanglement) are sealed on
its stick.
  * QUANTIZATION - the quantum of action hbar; light in lumps (E = hf); the discrete spectrum. Rests on the
    Hamiltonian (the discrete eigenvalues) and Maxwell (the photon = the EM field quantized).
  * SUPERPOSITION & MEASUREMENT - the wavefunction, the Born rule, the measurement gap. Rests on the capstone.
  * UNCERTAINTY - Delta x Delta p >= hbar/2; a proven limit, not an ignorance. Rests on the instruments (the found
    limit, the physical cousin of the engine's decline).
  * ENTANGLEMENT - Bell/Tsirelson: the world is not locally real; an entangled pair is ONE state. Rests on the
    capstone (one state, many parts) and relativity (no faster-than-light signal).
The stick (stick_quantum_mechanics_the_quantum_and_its_limits) seals hbar, the photon, and the Bell bound.
MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_quantum_mechanics.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_quantum_mechanics.py --check   # validate, write nothing
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

FLOOR = "card_floor_quantum_mechanics"
SPINE = "card_spine_quantum_mechanics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_quantum_mechanics_the_quantum_and_its_limits"

F_HAM = "card_floor_the_hamiltonian"
F_MAX = "card_floor_maxwells_equations"
F_CAP = "card_floor_the_capstone"
F_INSTR = "card_floor_the_instruments"
F_REL = "card_floor_relativity"

PILLARS = [
    dict(key="quantization",
         title="Quantization — the quantum of action, light in lumps",
         body="The quantum is real and discrete: the quantum of action hbar = h/(2 pi) (sealed), energy in quanta "
              "E = hf (a green photon, 2.25 eV, sealed), the sharp spectrum of every atom. Where it matters the world "
              "is granular. Rests on the Hamiltonian (the discrete eigenvalues) and Maxwell (the photon).",
         rests=[(F_HAM, "the discrete energy spectrum - the Hamiltonian's eigenvalues come in quanta"),
                (F_MAX, "the photon is the electromagnetic field quantized; E = hf")]),
    dict(key="superposition_measurement",
         title="Superposition & measurement — the wavefunction and the Born rule",
         body="The state is a superposition of potentials, weighted by the Born rule; measurement actualizes one. "
              "Already placed on the capstone (many potentials, one end; the measurement gap). Rests on the capstone.",
         rests=[(F_CAP, "superposition = many potentials; the Born rule and the measurement gap")]),
    dict(key="uncertainty",
         title="Uncertainty — a proven limit, not an ignorance",
         body="Position and momentum cannot both be sharp: Delta x Delta p >= hbar/2. Not a failure of measurement - "
              "the two are non-commuting observables ([x, p] = i hbar), so a particle does not HAVE both at once. A "
              "proven limit, found in the structure - the physical cousin of the engine's refusal to assert beyond "
              "what it can check. Rests on the instruments.",
         rests=[(F_INSTR, "a proven limit on what can be known - the physical cousin of the moat's decline")]),
    dict(key="entanglement",
         title="Entanglement — the world is not locally real",
         body="An entangled pair is ONE state, not two; measuring one fixes the other. Bell: no locally-real theory "
              "matches quantum predictions - CHSH is capped at 2 classically but reaches 2 sqrt(2) = 2.83 quantumly "
              "(sealed, Tsirelson), and experiment agrees (Aspect; 2022 Nobel). Many parts, one indivisible state - "
              "'one source, states of that force'. No faster-than-light signal, so it answers to relativity.",
         rests=[(F_CAP, "one indivisible state, many parts - 'one source, states of that force'"),
                (F_REL, "entanglement correlates without signalling: no faster-than-light message, so relativity holds")]),
]


def _pid(key: str) -> str:
    return f"card_qm_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — quantum mechanics", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "quantum_mechanics", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Quantum mechanics — the quantum and its limits",
        ("Not a floor beside the others - the framework they inhabit. Superposition and the Born rule are on the "
         "capstone, the Schrodinger equation on the Hamiltonian, the path integral on the Lagrangian. This floor "
         "gathers them and adds the three foundations not yet placed: quantization (the quantum of action, light in "
         "lumps), uncertainty (a proven limit, not an ignorance), and entanglement (the world is not locally real; "
         "one indivisible state). Four pillars rest on the Hamiltonian, Maxwell, the capstone, the instruments and "
         "relativity. The stick (" + STICK + ") seals hbar, the photon, and the Bell bound "
         "(tools/seed_quantum_mechanics.py)."),
        ["floor", "quantum mechanics", "quantum", "uncertainty", "entanglement", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Quantum mechanics — a spine", "The pillars of quantum mechanics.",
              ["quantum mechanics", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the framework of the physics region on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["quantum mechanics", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a foundation of quantum mechanics ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the framework of the physics region on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_hamiltonian as HAM
        import seed_maxwells_equations as MAX
        import seed_the_capstone as CAP
        import seed_instruments as SI
        import seed_relativity as REL
        ids |= {c["id"] for c in HAM.CARDS} | {c["id"] for c in MAX.CARDS} | {c["id"] for c in CAP.CARDS}
        ids |= {c["id"] for c in SI.CARDS} | {c["id"] for c in REL.CARDS}
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
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + floor + spine), "
              f"{len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
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
