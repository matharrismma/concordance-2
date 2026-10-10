#!/usr/bin/env python3
"""Materials science on the one map (Matt, 2026-10-10, down the domain list). How atoms pack and solids behave.
Three pillars rest on chemistry (the lattice), physical chemistry (mechanical/phase behaviour) and quantum
mechanics (the band structure). The stick (stick_materials_science_how_atoms_pack_and_solids_behave) seals the FCC
packing factor and an elastic strain. MERGE-writes through chains.merge_seed.
    PYTHONPATH=src python tools/seed_materials_science.py [--check]
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_materials_science"
SPINE = "card_spine_materials_science"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_materials_science_how_atoms_pack_and_solids_behave"
F_CHEM = "card_floor_chemistry"; F_PCHEM = "card_floor_physical_chemistry"; F_QM = "card_floor_quantum_mechanics"

PILLARS = [
    dict(key="lattice", title="The lattice — how atoms pack",
         body="Crystals pack with a definite efficiency: the FCC atomic packing factor pi/(3 sqrt2) = 0.74 (sealed), "
              "the densest packing of equal spheres. The lattice sets density, cleavage and strength. Rests on "
              "chemistry.",
         rests=[(F_CHEM, "the crystal lattice is chemistry arranged in a repeating cell")]),
    dict(key="mechanical", title="Mechanical behaviour — Hooke and beyond",
         body="Solids deform in proportion to stress (strain = stress / Young's modulus, sealed), elastic below the "
              "yield point and plastic above; phase changes (melting, annealing) are thermodynamics. Rests on "
              "physical chemistry.",
         rests=[(F_PCHEM, "stress-strain and phase behaviour - the thermodynamics and kinetics of solids")]),
    dict(key="electronic", title="Electronic behaviour — bands",
         body="Conductor, insulator or semiconductor is set by the electron band structure - the quantum mechanics "
              "of electrons in the periodic lattice. Silicon's gap is why the digital age exists. Rests on quantum "
              "mechanics.",
         rests=[(F_QM, "band theory - the quantum mechanics of electrons in the lattice")]),
]


def _pid(k): return f"card_mat_{k}"


def _card(cid, kind, title, body, bands, ref=""):
    src = {"label": "Narrow Highway — materials science", "url": "", "authority_tier": "engine_derived"}
    if ref: src["ref"] = ref
    return {"id": cid, "kind": kind, "title": title, "body": body, "source": src, "shelf": "codex",
            "box": "materials_science", "bands": bands, "subject": title, "connections": [], "author": "engine",
            "created_at": 0.0, "updated_at": 0.0, "visibility": "public", "lifecycle_stage": "public",
            "volatility": "permanent", "surface": "secular", "generated": False}


def floor_card():
    return _card(FLOOR, "note", "Materials science — how atoms pack and solids behave",
                 ("Crystals pack with a definite efficiency (the FCC factor 0.74); solids deform by Hooke's law; and "
                  "whether a solid conducts is set by its electron bands. Three pillars rest on chemistry (the "
                  "lattice), physical chemistry (mechanical and phase behaviour) and quantum mechanics (the bands). "
                  "The stick (" + STICK + ") seals the packing factor and an elastic strain "
                  "(tools/seed_materials_science.py)."),
                 ["floor", "materials science", "crystallography", "solid state", "one map"], ref=STICK)


def spine_card():
    c = _card(SPINE, "reference", "Materials science — a spine", "The pillars of materials science.",
              ["materials science", "spine", "one map"])
    c["shelf"] = "spine"; c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the science of solids on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()] + [
    _card(_pid(p["key"]), "reference", p["title"], p["body"], ["materials science", "pillar", p["key"], "one map"]) for p in PILLARS]


def _edge(a, b, rel, ev): return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges():
    out = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of materials science ({p['title'].split(' — ')[0]})"))
        for t, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), t, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the science of solids on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes():
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_chemistry as C, seed_physical_chemistry as PC, seed_quantum_mechanics as QM
        ids |= {c["id"] for c in C.CARDS} | {c["id"] for c in PC.CARDS} | {c["id"] for c in QM.CARDS}
    except Exception as e:
        print("could not load siblings:", e)
    return ids


def _validate():
    errs = []; ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids: errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR: errs.append(f"edge target unknown: {e['b']}")
    if len({c["id"] for c in CARDS}) != len(CARDS): errs.append("duplicate card ids")
    return errs


def main():
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs: print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards, {len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs: return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged ({n['cards']} cards, {len(CARDS)} from this seed; {n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
