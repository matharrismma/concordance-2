#!/usr/bin/env python3
"""Medicine on the one map (Matt, 2026-10-10, down the domain list). The body measured and mended.
Three pillars rest on biology (physiology), physical chemistry (pharmacokinetics) and statistics (epidemiology).
The stick (stick_medicine_the_body_measured_and_mended) seals a BMI, a drug half-life fraction and the
herd-immunity threshold. MERGE-writes through chains.merge_seed.
    PYTHONPATH=src python tools/seed_medicine.py [--check]
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_medicine"
SPINE = "card_spine_medicine"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_medicine_the_body_measured_and_mended"
F_BIO = "card_floor_biology"; F_PCHEM = "card_floor_physical_chemistry"; F_STATS = "card_floor_statistics"

PILLARS = [
    dict(key="physiology", title="Physiology — measured biology",
         body="The body read as data: vitals, the blood panel, the body-mass index (sealed). Medicine is biology at "
              "the scale of organs. Rests on biology.",
         rests=[(F_BIO, "physiology is biology at the scale of organs")]),
    dict(key="pharmacology", title="Pharmacology — the kinetics of a dose",
         body="Drugs clear by first-order decay, the half-life setting dosing and toxicity (sealed). Chemistry's "
              "kinetics, in the bloodstream. Rests on physical chemistry.",
         rests=[(F_PCHEM, "pharmacokinetics is first-order decay - the half-life sealed on physical chemistry")]),
    dict(key="epidemiology", title="Epidemiology — statistics on populations",
         body="Outbreaks, trials and risk are statistics: the herd-immunity threshold 1 - 1/R0 (sealed), incidence, "
              "confidence intervals. Rests on statistics and biology.",
         rests=[(F_STATS, "epidemiology is statistics on populations"), (F_BIO, "disease is biology in a population")]),
]


def _pid(k): return f"card_med_{k}"


def _card(cid, kind, title, body, bands, ref=""):
    src = {"label": "Narrow Highway — medicine", "url": "", "authority_tier": "engine_derived"}
    if ref: src["ref"] = ref
    return {"id": cid, "kind": kind, "title": title, "body": body, "source": src, "shelf": "codex", "box": "medicine",
            "bands": bands, "subject": title, "connections": [], "author": "engine", "created_at": 0.0,
            "updated_at": 0.0, "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False}


def floor_card():
    return _card(FLOOR, "note", "Medicine — the body measured and mended",
                 ("Physiology is measured biology, pharmacology is chemistry's kinetics, epidemiology is statistics "
                  "on populations. Three pillars rest on biology, physical chemistry and statistics. The engine "
                  "seals the arithmetic and DECLINES the clinical call (diagnosis, prescription, personal advice). "
                  "The stick (" + STICK + ") seals a BMI, a drug half-life fraction and the herd-immunity threshold "
                  "(tools/seed_medicine.py)."),
                 ["floor", "medicine", "physiology", "pharmacology", "epidemiology", "one map"], ref=STICK)


def spine_card():
    c = _card(SPINE, "reference", "Medicine — a spine", "The pillars of medicine.", ["medicine", "spine", "one map"])
    c["shelf"] = "spine"; c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the care of the body on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()] + [
    _card(_pid(p["key"]), "reference", p["title"], p["body"], ["medicine", "pillar", p["key"], "one map"]) for p in PILLARS]


def _edge(a, b, rel, ev): return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges():
    out = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of medicine ({p['title'].split(' — ')[0]})"))
        for t, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), t, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the care of the body on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes():
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_biology as B, seed_physical_chemistry as PC, seed_statistics as ST
        ids |= {c["id"] for c in B.CARDS} | {c["id"] for c in PC.CARDS} | {c["id"] for c in ST.CARDS}
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
