#!/usr/bin/env python3
"""Earth science on the one map (Matt, 2026-10-09, down the domain list).

The planet that life stands on. A floor whose four pillars rest on the floors already seeded:
  * RADIOMETRIC DATING - deep time from first-order decay. Rests on physical chemistry and chemistry.
  * PLATE TECTONICS - the mantle as a heat engine. Rests on thermodynamics.
  * MINERALS - crystal chemistry, the rock cycle. Rests on chemistry.
  * DEEP TIME - the 4.5-billion-year stage evolution needs. Rests on biology.
The stick (stick_earth_science_the_planet_read_in_deep_time) seals the radiometric fraction and the Richter
energy factor. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_earth_science.py           # merge
    PYTHONPATH=src python tools/seed_earth_science.py --check   # validate, write nothing
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

FLOOR = "card_floor_earth_science"
SPINE = "card_spine_earth_science"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_earth_science_the_planet_read_in_deep_time"

F_PCHEM = "card_floor_physical_chemistry"
F_CHEM = "card_floor_chemistry"
F_THERMO = "card_floor_thermodynamics"
F_BIO = "card_floor_biology"

PILLARS = [
    dict(key="radiometric_dating", title="Radiometric dating — deep time from decay",
         body="A radioactive isotope halves every half-life; after two half-lives a quarter remains (sealed). The "
              "parent-to-daughter ratio dates a rock - uranium-lead gives the age of the Earth, 4.54 billion years. "
              "It is the first-order decay law, borrowed from chemical kinetics.",
         rests=[(F_PCHEM, "radiometric dating is first-order decay - the half-life sealed on physical chemistry"),
                (F_CHEM, "isotopes and daughter products are chemistry")]),
    dict(key="plate_tectonics", title="Plate tectonics — the mantle heat engine",
         body="The crust rides plates driven by convection in the mantle - the Earth's internal heat rising and "
              "sinking, a heat engine bounded by the second law. Continents drift, oceans open, mountains rise. "
              "Rests on thermodynamics.",
         rests=[(F_THERMO, "mantle convection is a heat engine - plate tectonics runs on the second law")]),
    dict(key="minerals", title="Minerals — crystal chemistry, the rock cycle",
         body="Rocks are assemblages of minerals, and minerals are crystal chemistry - silicates, carbonates, "
              "oxides, each a definite composition and lattice. The rock cycle is chemistry and physics over deep "
              "time. Rests on chemistry.",
         rests=[(F_CHEM, "minerals are crystal chemistry - definite composition and lattice")]),
    dict(key="deep_time", title="Deep time — the stage evolution needs",
         body="Radiometric dating proves the 4.5-billion-year stage on which the tree of life grew. Geology hands "
              "biology the one thing evolution requires: time, and a great deal of it. Rests on biology.",
         rests=[(F_BIO, "deep time is what evolution needs - geology dates the stage life grew on")]),
]


def _pid(key: str) -> str:
    return f"card_earth_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — earth science", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "earth_science", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Earth science — the planet, read in deep time",
        ("The rock that life stands on. Radiometric dating reads deep time from decay; plate tectonics is the mantle "
         "as a heat engine; minerals are crystal chemistry; and deep time is the stage evolution needs. Four pillars "
         "rest on physical chemistry and chemistry (the decay clock, minerals), thermodynamics (the mantle engine), "
         "and biology (deep time). The stick (" + STICK + ") seals the radiometric fraction and the Richter energy "
         "factor (tools/seed_earth_science.py)."),
        ["floor", "earth science", "geology", "radiometric", "plate tectonics", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Earth science — a spine", "The pillars of earth science.",
              ["earth science", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the planet on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["earth science", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of earth science ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the planet on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_physical_chemistry as PC
        import seed_chemistry as CH
        import seed_thermodynamics as TH
        import seed_biology as BIO
        ids |= {c["id"] for c in PC.CARDS} | {c["id"] for c in CH.CARDS}
        ids |= {c["id"] for c in TH.CARDS} | {c["id"] for c in BIO.CARDS}
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
