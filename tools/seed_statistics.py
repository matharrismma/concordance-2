#!/usr/bin/env python3
"""Statistics on the one map (Matt, 2026-10-09, down the domain list).

How we draw one conclusion from many noisy measurements - the method of empirical science. A floor whose pillars
rest on the floors already seeded:
  * DESCRIBE - mean, variance, standard deviation. Rests on the instruments.
  * THE NORMAL LAW / CLT - sums tend to the bell curve; many into one shape. Rests on the capstone.
  * INFER - z-scores, hypothesis tests, p-values. Rests on the instruments.
  * THE METHOD OF SCIENCE - testing claims against data. Rests on biology (Hardy-Weinberg) and the capstone.
The stick (stick_statistics_the_normal_law_and_the_method_of_science) seals a standard deviation, a z-score and
the standard error. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_statistics.py           # merge
    PYTHONPATH=src python tools/seed_statistics.py --check   # validate, write nothing
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

FLOOR = "card_floor_statistics"
SPINE = "card_spine_statistics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_statistics_the_normal_law_and_the_method_of_science"

F_INSTR = "card_floor_the_instruments"
F_CAP = "card_floor_the_capstone"
F_BIO = "card_floor_biology"

PILLARS = [
    dict(key="describe", title="Describe — mean, variance, standard deviation",
         body="The first thing data tells you: the mean (the centre) and the standard deviation (the typical "
              "distance from it, sealed as 2 for a textbook sample). The ruler of spread. Rests on the instruments.",
         rests=[(F_INSTR, "descriptive statistics - the probability machinery of the instruments")]),
    dict(key="normal_law", title="The normal law — the central limit theorem",
         body="Sum or average enough independent things, whatever their shapes, and the result tends to the SAME "
              "bell curve, and the standard error shrinks as sigma/sqrt(n) (sealed). Many possibilities converging "
              "to one form. Rests on the capstone.",
         rests=[(F_CAP, "the central limit theorem is many-into-one; a distribution integrates to one")]),
    dict(key="infer", title="Infer — z-scores and hypothesis tests",
         body="Put every measurement on one scale (the z-score, sealed as 1), then test a claim: a test statistic, a "
              "p-value, a confidence interval. Turning noisy data into a verdict. Rests on the instruments.",
         rests=[(F_INSTR, "inference - z-scores, p-values, confidence intervals on the probability machinery")]),
    dict(key="method_of_science", title="The method of science — testing claims against data",
         body="Statistics is how every empirical science tests itself: Hardy-Weinberg in biology, measurement error "
              "in physics, trials in medicine. The discipline that turns data into a verdict - the same job the "
              "engine does deterministically. Rests on biology and the capstone.",
         rests=[(F_BIO, "the method of empirical science - Hardy-Weinberg is its biology face"),
                (F_CAP, "testing a claim against data to reach one verdict")]),
]


def _pid(key: str) -> str:
    return f"card_stats_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — statistics", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "statistics", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Statistics — the normal law and the method of science",
        ("How we draw one conclusion from many noisy measurements. Describe (mean, standard deviation); the central "
         "limit theorem makes sums tend to the normal law (the standard error shrinks as 1/sqrt(n)); infer "
         "(z-scores, hypothesis tests). Four pillars rest on the instruments (the probability machinery), the "
         "capstone (the CLT is many-into-one; a distribution sums to one), and biology (the method of empirical "
         "science). The stick (" + STICK + ") seals a standard deviation, a z-score and the standard error "
         "(tools/seed_statistics.py)."),
        ["floor", "statistics", "normal law", "inference", "central limit theorem", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Statistics — a spine", "The pillars of statistics.",
              ["statistics", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the method of empirical science on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["statistics", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of statistics ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the method of empirical science on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_instruments as SI
        import seed_the_capstone as CAP
        import seed_biology as BIO
        ids |= {c["id"] for c in SI.CARDS} | {c["id"] for c in CAP.CARDS} | {c["id"] for c in BIO.CARDS}
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
