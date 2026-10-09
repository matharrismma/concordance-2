#!/usr/bin/env python3
"""The capstone on the one map (Matt, 2026-10-09: "Yes. On the map").

The floor the others stand on: one source, many potentials, one end - the reply to Copenhagen. It closes no
chain. Three pillars rest on the floors already seeded:
  * ONE SOURCE, MANY POTENTIALS, ONE END - the ontology. Rests on the one force (card_floor_standard_model, the
    proven electroweak rung) and the tree of life (card_floor_tree_of_life, one root - LUCA).
  * THE NARROW WAY - exclude, narrow, converge to one (Matthew 7:13-14, the name on the door). Rests on the solve
    path (card_floor_the_solve_path) and the instruments' moat (card_floor_the_instruments, 0 false positives).
  * JUDGED BY THE FRUIT - predicted-and-fails is excluded (Deut 18:21-22; Matt 7:16-20). Rests on the same moat:
    the fruit test enforced in code.
The narrow way threads between two marked BARRIERS: Copenhagen's silence (refuse to say what is real) and
many-worlds' excess (everything real, nothing excluded). The stick (stick_the_capstone_one_source_many_potentials_one_end)
carries the seals and the postulates; this seed places the node on the map. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_the_capstone.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_the_capstone.py --check   # validate, write nothing
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

FLOOR = "card_floor_the_capstone"
SPINE = "card_spine_the_capstone"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_the_capstone_one_source_many_potentials_one_end"

# the floors this capstone rests on (connects_at): each resolves in a sibling seed
F_SM = "card_floor_standard_model"
F_TOL = "card_floor_tree_of_life"
F_SOLVE = "card_floor_the_solve_path"
F_INSTR = "card_floor_the_instruments"

# pillar key, title, body, and the floors it rests on (connects_at)
PILLARS = [
    dict(key="one_source",
         title="One source, many potentials, one end",
         body="The ontology. 'For of him, and through him, and to him, are all things' (Romans 11:36): from one "
              "source, states of that one, to the same end. The quantum superposition is potentia (Heisenberg) - "
              "real, weighted possibilities - not many realized worlds; one actualizes. The end is named: Alpha and "
              "Omega (Revelation 22:13). Proven where it can be (the electroweak), inferred where it cannot, never "
              "kept as fact.",
         rests=[(F_SM, "the proven rung: electromagnetism and the weak force are ONE above ~100 GeV (electroweak, sealed)"),
                (F_TOL, "one source in biology: all life from one root (LUCA), homologous genes the confluences")]),
    dict(key="narrow_way",
         title="The narrow way — exclude, narrow, converge to one",
         body="'Strait is the gate, and narrow is the way, which leadeth unto life' (Matthew 7:13-14) - the name on "
              "the door. The broad way multiplies and excludes nothing; the narrow way discerns, excludes, and "
              "arrives. The engine's actual mechanism: cut the dead branches, converge on the one answer, decline "
              "what cannot be verified. A method that never excludes never arrives.",
         rests=[(F_SOLVE, "the method: two jaws converge on the one answer"),
                (F_INSTR, "the moat: 0 false positives - the narrowing enforced in code")]),
    dict(key="fruit",
         title="Judged by the fruit — predicted-and-fails is excluded",
         body="'All you can use is the fruit.' If a thing is foretold and does not come to pass it is not from Him "
              "(Deuteronomy 18:21-22); 'by their fruits ye shall know them' (Matthew 7:16-20), the very next verses "
              "after the gate. We do not seal the source; we chain what bears good fruit and exclude the "
              "predicted-but-failed. The proof is the working whole - a complete system that works at any level.",
         rests=[(F_INSTR, "the fruit test enforced in code: a false positive is a predicted thing that does not hold")]),
]

# the two wide errors the narrow way passes between (marked barriers, connects_at from the narrow-way pillar)
BARRIERS = [
    dict(key="copenhagen",
         title="Copenhagen — the silence (a marked barrier)",
         body="The orthodox interpretation refuses to say what is real between measurements and draws an arbitrary "
              "cut between quantum system and classical apparatus, without saying where the cut is or why the "
              "wavefunction collapses. Instrumentalist silence. Not disproven - marked as the broad way of silence, "
              "the error the narrow way passes on one side. Decoherence supplies the physics it left as a mystery.",
         side="the silence side: refuses to say what is real"),
    dict(key="many_worlds",
         title="Many-worlds — the excess (a marked barrier)",
         body="Everett keeps every branch as a real, realized world: nothing excluded, no outcome more real than "
              "another, no single end - bought with an unobservable infinity of worlds. Not disproven - marked as the "
              "broad way of excess, the error the narrow way passes on the other side. Objective-collapse tests could "
              "someday decide it; we hold that open.",
         side="the excess side: everything is real, nothing narrows"),
]


def _pid(key: str) -> str:
    return f"card_capstone_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — the capstone", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "capstone", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "The capstone — one source, many potentials, one end",
        ("The floor the others stand on, and the reply to Copenhagen. We came from one source; we are states of that "
         "one; we have many potentials, but the story ends the same way. The narrow way threads between two wide "
         "errors - Copenhagen's silence (refuse to say what is real) and many-worlds' excess (everything real, "
         "nothing excluded) - keeping every result, removing both mysteries, paying the least ontology. Proven where "
         "it can be, inferred where it cannot, professed where it must be. It closes no chain; it names the floor the "
         "one force, the tree of life, the solve path and the moat all rest on. The seals and postulates are on the "
         "stick (" + STICK + "); this card places it on the map (tools/seed_the_capstone.py)."),
        ["floor", "capstone", "one source", "many potentials", "one end", "narrow way", "quantum", "two trees", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "The capstone — a spine", "The pillars of the capstone.",
              ["capstone", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the floor the one map stands on, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["capstone", "pillar", _p["key"], "one map"]))
for _b in BARRIERS:
    CARDS.append(_card(_pid(_b["key"]), "reference", _b["title"], _b["body"],
                       ["capstone", "barrier", _b["key"], "quantum", "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of the capstone ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    for b in BARRIERS:
        out.append(_edge(_pid("narrow_way"), _pid(b["key"]), "connects_at",
                         f"the narrow way passes between two wide errors - {b['side']}"))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the capstone is the floor the one map stands on"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_standard_model_chain as SM
        import seed_solve_path as SP
        import seed_tree_of_life as TOL
        import seed_instruments as SI
        ids |= {c["id"] for c in SM.CARDS} | {c["id"] for c in SP.CARDS}
        ids |= {c["id"] for c in TOL.CARDS} | {c["id"] for c in SI.CARDS}
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
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + {len(BARRIERS)} barriers + floor + spine), "
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
