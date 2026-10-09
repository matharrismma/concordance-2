#!/usr/bin/env python3
"""The solve path on the one map (Matt, 2026-10-09: "put both doors on the map solve path").

The set path for solving a hard problem, as a floor on the one map: two jaws that close on the answer.
  * EXCLUDE from outside - the barriers (card_floor_p_vs_np) and the moat (0 false positives) cut every branch
    proven dead. Narrows from the outside.
  * CONVERGE from inside - anchor on a point known exactly, then the two DOORS:
      - GET CLOSE (approximation): a bounded estimate, one step from the anchor, the error a Taylor/Lipschitz
        remainder (stick_get_fairly_close_with_a_proven_bound; the approximation instrument).
      - CHANGE OF DOMAIN (spectral): the exact flip - put it in the eigenbasis where it diagonalizes, solve as
        independent scalars, map back (stick_change_of_domain_solve_in_the_eigenbasis_map_back; the spectral
        instrument).
    then REFINE - tighten the bound in a monotone loop, each step sealed, stopping at the decision's precision.
  * The two jaws meet at the ANSWER: a value with a proven bound, small enough to decide (or a proven limit saying
    it cannot shrink further - the inapproximability floor).

Both doors are already instruments on card_floor_the_instruments; here they take their place as STEPS of the method.
The cards are cited pointers (a door's card carries its stick in source.ref); the code keeps the logic. MERGE-writes
through chains.merge_seed.

    PYTHONPATH=src python tools/seed_solve_path.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_solve_path.py --check   # validate, write nothing
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

FLOOR = "card_floor_the_solve_path"
SPINE = "card_spine_solve_path"
GLOBAL_FLOOR = "card_k_floor_of_discovery"

# step id, title, body, source.ref (a stick, or a doc), and the nodes elsewhere on the map it cites (connects_at)
STEPS = [
    dict(key="exclude", title="Exclude from outside — the barriers and the moat",
         body="The first jaw. Cut every branch proven dead: the three barriers of P vs NP (relativization, natural "
              "proofs, algebrization) say where a proof cannot come from, and the moat (0 false positives) rejects "
              "every candidate a verifier breaks. Narrows the space from the outside, monotonically — once out, out.",
         ref="docs/MILLENNIUM_PREPAREDNESS.md", cites=["card_floor_p_vs_np"], root=True),
    dict(key="converge", title="Converge from inside — anchor on what you know exactly",
         body="The second jaw. Do not search from nothing: start from a point held with certainty — a solved "
              "neighbour in the keeping, or an easy surrogate (relax the hard constraint, keep the first term) — and "
              "step toward the target by an amount you can bound. The anchor carries the truth; the step carries the "
              "error.",
         ref="", cites=[], root=True),
    dict(key="get_close", title="Get close — a bounded estimate (the approximate flip)",
         body="One step from the anchor, with a proven error: estimate f0 + f1·(x−x0), bound the remainder by Taylor "
              "(sup|f''|·(x−x0)^2/2) or Lipschitz. Fairly close, with a proven bound, is often the answer. The door is "
              "src/concordance/verifiers/approximation.py; 0 false positives — a closeness claim the truth does not "
              "satisfy is refused.",
         ref="stick_get_fairly_close_with_a_proven_bound", cites=["card_instr_approximation"]),
    dict(key="change_domain", title="Change of domain — solve in the eigenbasis, map back (the exact flip)",
         body="Put the problem in the space where it diagonalizes (its eigenbasis, the frequency basis), solve it as "
              "independent scalars, map back — exact when the basis is known and cheap (Fourier, diagonalization; "
              "Fibonacci becomes Binet). The door is src/concordance/verifiers/spectral.py; the engine checks the flip "
              "(A v = λ v) before trusting it. Where no cheap basis exists, fall through to get close.",
         ref="stick_change_of_domain_solve_in_the_eigenbasis_map_back", cites=["card_instr_spectral"]),
    dict(key="refine", title="Refine — tighten the bound, each step sealed",
         body="A monotone loop: one more term of the series, one more Newton step, one more zero counted — each "
              "tightening sealed, the window shrinking. Success guides the direction, failure narrows by proving the "
              "bound cannot tighten here. Runs only if the decision needs more than the first estimate gave.",
         ref="", cites=[]),
    dict(key="answer", title="The answer — the surviving window closes",
         body="Where the two jaws meet: a value with a proven bound, small enough to decide — or a proven limit "
              "(the inapproximability floor) saying it cannot shrink further. The proposer stayed free the whole way; "
              "the bounds carried all the certainty. Not an exact answer by rule, but a decided one, honestly bounded.",
         ref="", cites=[]),
]

# the chain: a step BUILDS_ON the step(s) before it (reciprocal `enables` lets the floor be walked forward)
EDGES = [
    ("get_close", "converge"), ("change_domain", "converge"),
    ("refine", "get_close"), ("refine", "change_domain"),
    ("answer", "refine"), ("answer", "exclude"),
]


def _sid(key: str) -> str:
    return f"card_solve_{key}"


def step_card(s: Dict) -> dict:
    src = {"label": "Narrow Highway — a step of the solve path", "url": "", "authority_tier": "engine_derived"}
    if s.get("ref"):
        src["ref"] = s["ref"]
    return {
        "id": _sid(s["key"]), "kind": "note" if s["key"] == "answer" else "reference", "title": s["title"],
        "body": s["body"], "source": src, "shelf": "codex", "box": "solve_step",
        "bands": ["solve path", "method", s["key"]], "subject": s["title"],
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return {
        "id": FLOOR, "kind": "note", "title": "The solve path — two jaws that close on the answer",
        "body": ("How the engine solves a hard problem when no rule finds the exact answer (the barriers). Two jaws: "
                 "EXCLUDE from outside (the barriers, the moat — cut the dead branches) and CONVERGE from inside "
                 "(anchor, then the two doors — GET CLOSE, the bounded estimate, and CHANGE OF DOMAIN, the eigenbasis "
                 "flip — then REFINE). They meet at the ANSWER: a value with a proven bound, small enough to decide. "
                 "The proposer stays free; the checks and the bounds carry the certainty. Found, never generated — "
                 "the steps point at the doors (tools/seed_solve_path.py)."),
        "source": {"label": "Narrow Highway — the solve path (operator seed)", "url": "",
                   "ref": "project_the_solve_path_get_close_and_change_of_domain", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor",
        "bands": ["floor", "solve path", "method", "two trees", "approximation", "spectral", "one map"],
        "subject": "The solve path",
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def spine_card() -> dict:
    return {
        "id": SPINE, "kind": "reference", "title": "The solve path — a spine", "body": "The steps of the solve path.",
        "source": {"label": "The solve path — a spine", "url": "", "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["solve path", "spine", "one map"], "subject": "The solve path",
        "connections": [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "a spine of the one map, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [floor_card(), spine_card()] + [step_card(s) for s in STEPS]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for s in STEPS:
        if s.get("root"):
            out.append(_edge(_sid(s["key"]), FLOOR, "part_of", f"a jaw of the solve path ({s['title'].split(' — ')[0]})"))
        else:
            out.append(_edge(_sid(s["key"]), SPINE, "member_of", "a step of the solve path"))
        for c in s.get("cites", []):
            out.append(_edge(_sid(s["key"]), c, "connects_at", f"{s['title'].split(' — ')[0]}: uses {c}"))
    for later, earlier in EDGES:
        out.append(_edge(_sid(later), _sid(earlier), "builds_on", f"{later} follows {earlier} on the solve path"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_chains as S3
        import seed_instruments as SI
        import seed_millennium_chain as S2
        ids |= {c["id"] for c in S2.CARDS} | {c["id"] for c in S3.CARDS} | {c["id"] for c in SI.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs = []
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
        print(f"[check] {len(CARDS)} cards ({len(STEPS)} steps + floor + spine), {len(BRIDGES)} edges; "
              f"{'OK' if not errs else 'ERRORS'}")
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
