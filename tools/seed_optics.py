#!/usr/bin/env python3
"""Optics on the one map (Matt, 2026-10-10, down the domain list). How light bends, focuses, and slows.
Three pillars rest on Maxwell (light is an electromagnetic wave) and quantum mechanics (the photon). The stick
(stick_optics_how_light_bends_focuses_and_slows) seals a thin-lens image distance and the speed of light in glass.
MERGE-writes through chains.merge_seed.
    PYTHONPATH=src python tools/seed_optics.py [--check]
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_optics"
SPINE = "card_spine_optics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_optics_how_light_bends_focuses_and_slows"
F_MAX = "card_floor_maxwells_equations"; F_QM = "card_floor_quantum_mechanics"

PILLARS = [
    dict(key="refraction", title="Refraction — light slows and bends",
         body="Light travels at c/n in a medium (2.0e8 m/s in glass, sealed); the slowing bends it at a boundary "
              "(Snell), splits a prism (n varies with colour), and traps light in a fibre at the critical angle. "
              "Rests on Maxwell.",
         rests=[(F_MAX, "refraction is a Maxwell wave slowing in matter - light is electromagnetism")]),
    dict(key="lenses", title="Lenses — focusing by the thin-lens equation",
         body="A lens focuses by 1/f = 1/do + 1/di (image at 15 cm for the sealed example); magnification is the "
              "ratio of distances. Every camera, eye and telescope is this geometry of rays. Rests on Maxwell.",
         rests=[(F_MAX, "ray optics is the short-wavelength limit of Maxwell's light")]),
    dict(key="the_photon", title="The photon — optics is also quantum",
         body="A beam is also a stream of photons (E = hf, on the quantum floor); the photoelectric effect, lasers "
              "and single-photon experiments live here. Classical rays and quantum photons are one light. Rests on "
              "quantum mechanics.",
         rests=[(F_QM, "the photon - the quantum of light; wave-particle duality")]),
]


def _pid(k): return f"card_opt_{k}"


def _card(cid, kind, title, body, bands, ref=""):
    src = {"label": "Narrow Highway — optics", "url": "", "authority_tier": "engine_derived"}
    if ref: src["ref"] = ref
    return {"id": cid, "kind": kind, "title": title, "body": body, "source": src, "shelf": "codex", "box": "optics",
            "bands": bands, "subject": title, "connections": [], "author": "engine", "created_at": 0.0,
            "updated_at": 0.0, "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False}


def floor_card():
    return _card(FLOOR, "note", "Optics — how light bends, focuses, and slows",
                 ("Light is a Maxwell wave that slows in matter (v = c/n) and bends at boundaries (refraction); "
                  "lenses focus it by the thin-lens equation; and a beam is also a stream of photons. Three pillars "
                  "rest on Maxwell (light is electromagnetism) and quantum mechanics (the photon). The stick (" +
                  STICK + ") seals a thin-lens image distance and the speed of light in glass (tools/seed_optics.py)."),
                 ["floor", "optics", "light", "lenses", "refraction", "one map"], ref=STICK)


def spine_card():
    c = _card(SPINE, "reference", "Optics — a spine", "The pillars of optics.", ["optics", "spine", "one map"])
    c["shelf"] = "spine"; c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the behaviour of light on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()] + [
    _card(_pid(p["key"]), "reference", p["title"], p["body"], ["optics", "pillar", p["key"], "one map"]) for p in PILLARS]


def _edge(a, b, rel, ev): return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges():
    out = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of optics ({p['title'].split(' — ')[0]})"))
        for t, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), t, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the behaviour of light on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes():
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_maxwells_equations as M, seed_quantum_mechanics as QM
        ids |= {c["id"] for c in M.CARDS} | {c["id"] for c in QM.CARDS}
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
