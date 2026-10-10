#!/usr/bin/env python3
"""Biology on the one map (Matt, 2026-10-09, down the domain list).

Life is self-replicating chemistry - the next rung of the emergence ladder. A floor standing on chemistry,
connecting the tree of life into the physics-chemistry region. Four pillars:
  * THE GENETIC CODE - DNA, a triplet code (4^3 = 64 codons). Rests on chemistry (DNA is a molecule) and the
    instruments (the code is information).
  * EVOLUTION - common descent, variation and selection. Rests on the tree of life.
  * POPULATION GENETICS - Hardy-Weinberg, frequencies sum to one. Rests on the capstone.
  * METABOLISM - life runs on free energy; a local entropy decrease paid globally. Rests on thermodynamics.
The stick (stick_biology_the_genetic_code_and_the_tree_of_life) seals the codon count and Hardy-Weinberg.
MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_biology.py           # merge
    PYTHONPATH=src python tools/seed_biology.py --check   # validate, write nothing
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

FLOOR = "card_floor_biology"
SPINE = "card_spine_biology"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_biology_the_genetic_code_and_the_tree_of_life"

F_CHEM = "card_floor_chemistry"
F_INSTR = "card_floor_the_instruments"
F_TOL = "card_floor_tree_of_life"
F_CAP = "card_floor_the_capstone"
F_THERMO = "card_floor_thermodynamics"

PILLARS = [
    dict(key="genetic_code", title="The genetic code — DNA, a triplet code",
         body="DNA spells proteins in three-letter words: four bases in triplets give 4^3 = 64 codons (sealed) for "
              "20 amino acids plus stop, read almost the same in every organism. The molecule is chemistry; the code "
              "it carries is information.",
         rests=[(F_CHEM, "DNA and proteins are molecules - the genetic code is chemistry"),
                (F_INSTR, "the genetic code is digital information - 64 codons, read by the information instrument")]),
    dict(key="evolution", title="Evolution — common descent and selection",
         body="All life descends from one root (LUCA); variation and natural selection build the tree. The "
              "near-universal genetic code and the universal genes are the evidence. Rests on the tree of life.",
         rests=[(F_TOL, "common descent - the tree of life from one root, the universal genes the evidence")]),
    dict(key="population_genetics", title="Population genetics — Hardy-Weinberg",
         body="In a non-evolving population the genotype frequencies p^2 + 2pq + q^2 sum to 1 (sealed). Departures "
              "measure evolution - selection, drift, migration, mutation. Many genotypes, one total: the capstone's "
              "sum-to-one in a gene pool.",
         rests=[(F_CAP, "allele and genotype frequencies sum to one - 'many possibilities, one total'")]),
    dict(key="metabolism", title="Metabolism — life runs on free energy",
         body="A cell copies itself and runs on free energy. Life does not break the second law: it is a local "
              "decrease in entropy paid for by a larger increase around it (heat, waste). Rests on thermodynamics.",
         rests=[(F_THERMO, "life is a local entropy decrease paid for globally - the second law, not broken")]),
]


def _pid(key: str) -> str:
    return f"card_bio_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — biology", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "biology", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Biology — life is self-replicating chemistry",
        ("The next rung of the emergence ladder: physics -> chemistry -> life. A cell is chemistry organized to copy "
         "itself and run on free energy; DNA spells proteins in a triplet code (64 codons), and evolution builds the "
         "tree of life from one root. Four pillars rest on chemistry and the instruments (the genetic code), the "
         "tree of life (evolution), the capstone (Hardy-Weinberg sums to one), and thermodynamics (metabolism). The "
         "stick (" + STICK + ") seals the codon count and Hardy-Weinberg (tools/seed_biology.py)."),
        ["floor", "biology", "life", "genetic code", "evolution", "emergence", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Biology — a spine", "The pillars of biology.", ["biology", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the world of life on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["biology", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of biology ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, F_CHEM, "connects_at", "life is self-replicating chemistry - biology stands on the chemistry floor"))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the world of life on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_chemistry as CH
        import seed_instruments as SI
        import seed_tree_of_life as TOL
        import seed_the_capstone as CAP
        import seed_thermodynamics as TH
        ids |= {c["id"] for c in CH.CARDS} | {c["id"] for c in SI.CARDS} | {c["id"] for c in TOL.CARDS}
        ids |= {c["id"] for c in CAP.CARDS} | {c["id"] for c in TH.CARDS}
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
