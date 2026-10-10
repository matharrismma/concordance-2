#!/usr/bin/env python3
"""Game theory on the one map (Matt, 2026-10-10, down the domain list - after computer science).

The mathematics of strategic choice. A floor whose pillars rest on the floors already seeded:
  * NASH EQUILIBRIUM - a fixed point of best-response. Rests on the solve path (converge) and economics.
  * THE PRISONER'S DILEMMA - rational play reaches a worse outcome than cooperation. Rests on economics and mind.
  * ZERO-SUM / MINIMAX - the mixed-strategy value (von Neumann). Rests on the solve path.
  * EVOLUTIONARY GAMES - fitness as payoff; the ESS. Rests on biology.
The stick (stick_game_theory_equilibrium_dilemmas_and_strategy) seals the fair zero-sum mixed value and the
dilemma's cooperation gap. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_game_theory.py           # merge
    PYTHONPATH=src python tools/seed_game_theory.py --check   # validate, write nothing
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

FLOOR = "card_floor_game_theory"
SPINE = "card_spine_game_theory"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_game_theory_equilibrium_dilemmas_and_strategy"

F_SOLVE = "card_floor_the_solve_path"
F_ECON = "card_floor_economics"
F_MIND = "card_floor_the_mind"
F_BIO = "card_floor_biology"

PILLARS = [
    dict(key="nash", title="Nash equilibrium — a fixed point",
         body="A profile where no player gains by deviating alone - a fixed point of best-response, which Nash "
              "proved always exists in mixed strategies (by Brouwer). Finding it is the solve path's converge step. "
              "Rests on the solve path and economics.",
         rests=[(F_SOLVE, "the equilibrium is a fixed point - the solve path's converge step"),
                (F_ECON, "the payoffs are incentives - strategic economics")]),
    dict(key="prisoners_dilemma", title="The prisoner's dilemma — the price of rationality",
         body="Each player does better to defect whatever the other does, so both defect (1 each) though cooperation "
              "would give 3 each (gap sealed as 2). The Nash outcome is not the best: self-interest reaches a worse "
              "place than trust. The tragedy of the commons. Rests on economics and the mind.",
         rests=[(F_ECON, "dominant strategies and incentives - the dilemma is an economics of trust"),
                (F_MIND, "players reason about each other - rational agents")]),
    dict(key="zero_sum", title="Zero-sum and minimax — the mixed value",
         body="When no pure choice wins (matching pennies), players randomize, and the game still has a value "
              "(0 for the fair case, sealed) - von Neumann's minimax theorem. Many moves, one value. Rests on the "
              "solve path.",
         rests=[(F_SOLVE, "the minimax value is an optimization - converge on the saddle point")]),
    dict(key="evolutionary", title="Evolutionary games — fitness is the payoff",
         body="Replace rational choice with reproduction and the same math governs biology: an evolutionarily stable "
              "strategy is a Nash equilibrium no mutant can invade (hawk-dove, the evolution of cooperation). Rests "
              "on biology.",
         rests=[(F_BIO, "the ESS - a Nash equilibrium in the gene pool; evolutionary game theory")]),
]


def _pid(key: str) -> str:
    return f"card_game_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — game theory", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "game_theory", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Game theory — equilibrium, dilemmas, and strategy",
        ("The mathematics of strategic choice. A Nash equilibrium is a fixed point where no one gains by deviating "
         "alone; the prisoner's dilemma shows rational players reaching a worse outcome than cooperation; zero-sum "
         "games have a minimax value reached by mixed strategies. Four pillars rest on the solve path (equilibrium "
         "is a fixed point), economics (payoffs are incentives), the mind (players reason), and biology "
         "(evolutionary games). The stick (" + STICK + ") seals the fair zero-sum value and the dilemma's "
         "cooperation gap (tools/seed_game_theory.py)."),
        ["floor", "game theory", "nash", "strategy", "equilibrium", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Game theory — a spine", "The pillars of game theory.",
              ["game theory", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "strategic choice on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["game theory", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of game theory ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "strategic choice on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_solve_path as SP
        import seed_economics as ECON
        import seed_the_mind as MIND
        import seed_biology as BIO
        ids |= {c["id"] for c in SP.CARDS} | {c["id"] for c in ECON.CARDS}
        ids |= {c["id"] for c in MIND.CARDS} | {c["id"] for c in BIO.CARDS}
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
