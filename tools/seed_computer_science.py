#!/usr/bin/env python3
"""Computer science on the one map (Matt, 2026-10-10, down the domain list).

Bits, logic, and what can be computed. A floor whose pillars rest on the floors already seeded:
  * INFORMATION IS BITS - a byte is 2^8 values. Rests on the instruments (Shannon information).
  * LOGIC GATES - the 16 Boolean functions of two inputs. Rests on the instruments (formal logic).
  * ALGORITHMS - good beats bad (merge sort's n log n vs n^2). Rests on P vs NP.
  * COMPUTABILITY/COMPLEXITY - Turing, the halting problem, P vs NP. Rests on P vs NP and the mind.
The stick (stick_computer_science_bits_logic_and_what_can_be_computed) seals the byte, the Boolean-gate count, and
the merge-sort comparison count. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_computer_science.py           # merge
    PYTHONPATH=src python tools/seed_computer_science.py --check   # validate, write nothing
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

FLOOR = "card_floor_computer_science"
SPINE = "card_spine_computer_science"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_computer_science_bits_logic_and_what_can_be_computed"

F_INSTR = "card_floor_the_instruments"
F_PNP = "card_floor_p_vs_np"
F_MIND = "card_floor_the_mind"

PILLARS = [
    dict(key="bits", title="Information is bits — the byte",
         body="Everything digital is bits, and n bits name 2^n things: a byte is 2^8 = 256 values (sealed). The bit "
              "is the atom of information (the Shannon bit, on the instruments); computing is what you do with enough "
              "of them. Rests on the instruments.",
         rests=[(F_INSTR, "the bit is Shannon information - the instruments measure it")]),
    dict(key="logic_gates", title="Logic gates — the 16 functions of two inputs",
         body="Of two inputs there are exactly 2^(2^2) = 16 Boolean functions (sealed) - AND, OR, XOR, NAND and the "
              "rest; NAND alone builds them all. From gates come adders, memory and processors. All computation is "
              "wired from this finite logic. Rests on the instruments (formal logic).",
         rests=[(F_INSTR, "Boolean logic is the formal-logic instrument - gates from truth functions")]),
    dict(key="algorithms", title="Algorithms — good beats bad",
         body="The same task costs wildly different work: merge sort takes ~n log n (24 comparisons for 8 items, "
              "sealed), the naive way n^2 (64). As n grows the gap explodes - algorithms, not just faster hardware, "
              "are the heart of the field. Rests on P vs NP.",
         rests=[(F_PNP, "algorithmic cost and complexity classes - the P vs NP region")]),
    dict(key="computability", title="Computability and complexity — Turing to P vs NP",
         body="A Turing machine defines what is computable; the universal machine runs any program (the engine, the "
              "laptop, the brain's computation). Some problems are undecidable (the halting problem); among the "
              "decidable, how fast is the open P vs NP question. Rests on P vs NP and the mind.",
         rests=[(F_PNP, "computability and complexity - the halting problem and P vs NP"),
                (F_MIND, "the brain computes - neural networks borrow its shape")]),
]


def _pid(key: str) -> str:
    return f"card_cs_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — computer science", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "computer_science", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Computer science — bits, logic, and what can be computed",
        ("Information is bits (a byte is 2^8 = 256 values); logic gates build from the 16 Boolean functions of two "
         "inputs; good algorithms beat bad ones (merge sort's n log n against n^2); and computability and complexity "
         "say what a machine can do at all and how fast (the halting problem undecidable; P vs NP open). Four pillars "
         "rest on the instruments (information, logic), P vs NP (complexity), and the mind (which computes). The "
         "engine is itself one such machine. The stick (" + STICK + ") seals the byte, the Boolean-gate count and "
         "the merge-sort comparisons (tools/seed_computer_science.py)."),
        ["floor", "computer science", "computation", "algorithms", "bits", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Computer science — a spine", "The pillars of computer science.",
              ["computer science", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "computation on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["computer science", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of computer science ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "computation on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_instruments as SI
        import seed_chains as S3
        import seed_the_mind as MIND
        ids |= {c["id"] for c in SI.CARDS} | {c["id"] for c in S3.CARDS} | {c["id"] for c in MIND.CARDS}
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
