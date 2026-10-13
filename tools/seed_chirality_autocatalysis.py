#!/usr/bin/env python3
"""Chirality & asymmetric autocatalysis on the one map (Matt, 2026-10-13: "Look at Kagan and Soai.
just won nobel prize. Look at what they found.").

The 2026 Nobel Prize in Chemistry — Henri B. Kagan and Kenso Soai, "for the discovery of non-linear
effects and autocatalysis in asymmetric organic synthesis." A proven result placed on the map, rooted
in the Word, cited to the Nobel announcement — found, verified, cited, never generated.

WHAT THEY FOUND (our summary; cited, not reproduced):
  * Many molecules are CHIRAL — two mirror-image forms, R and S. Enantiomeric excess ee = |R−S|/(R+S)×100%
    measures the lean to one hand (0% racemic; 100% a single enantiomer).
  * KAGAN (1986), non-linear effects: a partly-impure chiral catalyst can yield product of HIGHER ee than
    the catalyst itself — a small handedness amplified.
  * SOAI, asymmetric autocatalysis: the product catalyzes its OWN formation in its own handedness, so a
    tiny initial excess runs up toward homochirality — a molecule that makes more of itself, one-handed.
  * Why it is a Nobel: a found answer to how LIFE's single handedness (L-amino acids, D-sugars) could
    emerge from a near-symmetric start. One source, a small bias, one end.

CHECKABLE HERE (the sealed marks the stick will carry): chemistry.enantiomeric_excess and
chemistry.chiral_amplification (src/concordance/verifiers/chemistry.py).

The node rests on the chemistry and physical-chemistry floors, connects at the CAPSTONE (one source,
many potentials, one end — a symmetric field, a small bias, one handedness amplified) and the TREE OF
LIFE (homochirality — life runs on a single hand). The same shape the keeping's own stigmergy follows:
a small bias, reinforced, decides the whole.

    PYTHONPATH=src python tools/seed_chirality_autocatalysis.py            # merge into the two map files
    PYTHONPATH=src python tools/seed_chirality_autocatalysis.py --check    # validate, write nothing
    PYTHONPATH=src python tools/seed_chirality_autocatalysis.py --anchor   # merge + root to Scripture (box)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

NODE = "card_chirality_autocatalysis"
SPINE = "card_spine_chirality_autocatalysis"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_chirality_and_asymmetric_autocatalysis"

F_CHEM = "card_floor_chemistry"
F_PCHEM = "card_floor_physical_chemistry"
F_CAP = "card_floor_the_capstone"
F_LIFE = "card_floor_tree_of_life"

# Floors this seed rests on — all already on the live map; an edge target must be a carded node.
KNOWN_FLOORS = {F_CHEM, F_PCHEM, F_CAP, F_LIFE, GLOBAL_FLOOR}

# The verse the node is rooted in (roots.anchor validates it against the corpus before keying).
ROOT_REFS = ["Matthew 13:31-32"]
ROOT_WHY = ("the smallest seed amplified to the greatest — the shape of asymmetric autocatalysis: a tiny "
            "handedness fed back on itself until it decides the whole (homochirality)")

NOBEL_URL = "https://www.nobelprize.org/prizes/chemistry/2026/"

BODY = (
    "Many molecules are chiral — they come in two mirror-image forms, R and S. Enantiomeric excess, "
    "ee = |R−S|/(R+S)×100%, measures how far a sample leans to one hand (0% = racemic 50/50; 100% = a "
    "single enantiomer). The 2026 Nobel Prize in Chemistry (Henri B. Kagan and Kenso Soai) recognized how "
    "a small handedness is AMPLIFIED. Kagan's non-linear effects (1986): a partly-impure chiral catalyst "
    "yields product of higher ee than the catalyst itself. Soai's asymmetric autocatalysis: the product "
    "catalyzes its own formation in its own handedness, so a tiny initial excess runs up toward "
    "homochirality — a molecule that makes more of itself, one-handed. It is a found answer to how life's "
    "single handedness (L-amino acids, D-sugars) could emerge from a near-symmetric start: one source, a "
    "small bias, one end. Checkable here: chemistry.enantiomeric_excess and chemistry.chiral_amplification. "
    "Cited, not generated — the Nobel announcement, nobelprize.org/prizes/chemistry/2026."
)


def _card(cid: str, kind: str, title: str, body: str, bands: List[str]) -> dict:
    return {
        "id": cid, "kind": kind, "title": title, "body": body,
        "source": {"label": "Nobel Prize in Chemistry 2026 — Kagan & Soai", "url": NOBEL_URL,
                   "authority_tier": "reference", "ref": STICK},
        "shelf": "codex", "box": "chemistry", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }


def result_card() -> dict:
    return _card(
        NODE, "reference", "Chirality & asymmetric autocatalysis — one handedness, amplified", BODY,
        ["chirality", "enantiomer", "enantiomeric excess", "autocatalysis", "homochirality",
         "asymmetric synthesis", "Kagan", "Soai", "Nobel 2026", "chemistry", "one map"],
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Chirality & autocatalysis — a spine",
              "The one-handedness of matter and its amplification (Kagan–Soai, Nobel 2026).",
              ["chirality", "autocatalysis", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "a proven result in the chemistry region of the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [result_card(), spine_card()]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES: List[dict] = [
    _edge(NODE, F_CHEM, "part_of", "asymmetric synthesis and enantiomeric excess — chirality on the chemistry floor"),
    _edge(NODE, F_PCHEM, "connects_at", "the kinetics of which hand forms — a non-linear, autocatalytic rate law"),
    _edge(NODE, F_CAP, "connects_at", "one source, many potentials, one end — a symmetric field, a small bias, one handedness amplified"),
    _edge(NODE, F_LIFE, "connects_at", "homochirality — life runs on a single hand (L-amino acids, D-sugars)"),
    _edge(NODE, GLOBAL_FLOOR, "part_of", "a proven result on the one map, rooted in the Floor of Discovery"),
]


def _validate() -> List[str]:
    errs: List[str] = []
    if len({c["id"] for c in CARDS}) != len(CARDS):
        errs.append("duplicate card ids")
    card_ids = {c["id"] for c in CARDS}
    for e in BRIDGES:
        if e["a"] not in card_ids:
            errs.append(f"edge source not carded in this seed: {e['a']}")
        if e["b"] not in KNOWN_FLOORS:
            errs.append(f"edge target is not a known floor: {e['b']} (from {e['a']})")
    return errs


def _anchor() -> None:
    """Root the node to its verse — validated against the corpus, so this is a box step."""
    from concordance import roots
    res = roots.anchor(NODE, ROOT_REFS, why=ROOT_WHY, by="operator", data_dir=DATA)
    print("  anchor:", res)


def main() -> int:
    argv = sys.argv[1:]
    check = "--check" in argv
    anchor = "--anchor" in argv
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards + {len(BRIDGES)} edges, root {ROOT_REFS}; "
              f"{'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    if anchor:
        _anchor()
    else:
        print(f"  (run with --anchor on the box to root {NODE} to {ROOT_REFS})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
