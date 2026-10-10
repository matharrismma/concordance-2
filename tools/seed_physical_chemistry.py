#!/usr/bin/env python3
"""Physical chemistry on the one map (Matt, 2026-10-09: "deeper in chemistry").

Deeper in chemistry: the laws that make it predictive beyond 'possible' (the quantum) and 'which way'
(thermodynamics). A floor standing on the chemistry floor, four pillars:
  * KINETICS - how fast (the first-order half-life). Rests on chemistry.
  * EQUILIBRIUM - the balance point, Delta G = -RT ln K. Rests on thermodynamics.
  * ACID-BASE - pKa + pKb = pKw = 14. Rests on chemistry.
  * ELECTROCHEMISTRY - the cell potential (the Daniell battery). Rests on Maxwell (redox is electrons moving).
The stick (stick_physical_chemistry_rate_equilibrium_acid_base_redox) seals one number per pillar. MERGE-writes
through chains.merge_seed.

    PYTHONPATH=src python tools/seed_physical_chemistry.py           # merge
    PYTHONPATH=src python tools/seed_physical_chemistry.py --check   # validate, write nothing
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

FLOOR = "card_floor_physical_chemistry"
SPINE = "card_spine_physical_chemistry"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_physical_chemistry_rate_equilibrium_acid_base_redox"

F_CHEM = "card_floor_chemistry"
F_THERMO = "card_floor_thermodynamics"
F_MAX = "card_floor_maxwells_equations"

PILLARS = [
    dict(key="kinetics", title="Kinetics — how fast",
         body="Thermodynamics says which way; kinetics says how fast. The first-order half-life t_1/2 = ln 2 / k is "
              "independent of the starting amount (sealed, 6.93 s for k = 0.1/s) - the same law as radioactive "
              "decay. Rate is its own science on top of direction.",
         rests=[(F_CHEM, "the rate of the reactions chemistry describes")]),
    dict(key="equilibrium", title="Equilibrium — Delta G = -RT ln K",
         body="A reaction settles where the equilibrium constant K is fixed by the free energy: Delta G-naught = "
              "-RT ln K (sealed, -5.71 kJ/mol for K = 10 at 298 K). The bridge from thermodynamics to the measured "
              "ratio of products to reactants. Rests on thermodynamics.",
         rests=[(F_THERMO, "the equilibrium constant is set by the free energy: Delta G = -RT ln K")]),
    dict(key="acid_base", title="Acid-base — pKa + pKb = 14",
         body="For an acid and its conjugate base, pKa + pKb = pKw = 14 at 25 C (sealed). This is Ka * Kb = Kw, the "
              "autoionization of water, in logarithms - the backbone of pH, buffers and titrations. Rests on "
              "chemistry (pH is sealed on the chemistry stick).",
         rests=[(F_CHEM, "pH and the conjugate pair - the acid-base chemistry on the chemistry floor")]),
    dict(key="electrochemistry", title="Electrochemistry — the cell potential",
         body="A redox reaction splits into two half-cells; the cell potential is E-cathode - E-anode. The Daniell "
              "cell (copper, zinc) gives 1.10 V (sealed) - the first practical battery. Redox is electrons moving, so "
              "it rests on electromagnetism.",
         rests=[(F_MAX, "redox is electrons moving - the cell potential is an electrical process")]),
]


def _pid(key: str) -> str:
    return f"card_pchem_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — physical chemistry", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "physical_chemistry", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Physical chemistry — rate, equilibrium, acid-base, redox",
        ("Deeper in chemistry: the laws that make it predictive. Kinetics (how fast), equilibrium (the balance point, "
         "Delta G = -RT ln K), acid-base (pKa + pKb = 14), and electrochemistry (the cell potential). Four pillars "
         "rest on chemistry (kinetics, acid-base), thermodynamics (equilibrium), and Maxwell (electrochemistry - "
         "redox is electrons moving). The laws that turn chemistry from a description into a prediction. The stick (" +
         STICK + ") seals one number per pillar (tools/seed_physical_chemistry.py)."),
        ["floor", "physical chemistry", "kinetics", "equilibrium", "electrochemistry", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Physical chemistry — a spine", "The pillars of physical chemistry.",
              ["physical chemistry", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the predictive laws of chemistry on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["physical chemistry", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a branch of physical chemistry ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, F_CHEM, "connects_at", "physical chemistry stands on the chemistry floor"))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the predictive laws of chemistry on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_chemistry as CH
        import seed_thermodynamics as TH
        import seed_maxwells_equations as MAX
        ids |= {c["id"] for c in CH.CARDS} | {c["id"] for c in TH.CARDS} | {c["id"] for c in MAX.CARDS}
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
