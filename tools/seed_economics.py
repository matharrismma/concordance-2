#!/usr/bin/env python3
"""Economics on the one map (Matt, 2026-10-10, complete the domain list).

The social rung: minds that choose, meeting scarcity. The finance arithmetic (compound interest, rule of 72,
present value, price elasticity, GDP per capita) is ALREADY sealed on the economics stick
(stick_economics_the_finance_arithmetic_verified_and_sealed), which this floor cites (source.ref) - found, never
duplicated. Four pillars rest on the floors already seeded:
  * SCARCITY AND CHOICE - agents choose under scarcity, responding to incentives. Rests on the mind.
  * THE TIME VALUE OF MONEY - compound interest, present value, the rule of 72 (sealed). Rests on the instruments.
  * MARKETS AND PRICES - supply, demand, elasticity (sealed). Rests on statistics and the mind.
  * AGGREGATES - GDP, inflation, growth (sealed). Rests on statistics.
No new stick. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_economics.py           # merge
    PYTHONPATH=src python tools/seed_economics.py --check   # validate, write nothing
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

FLOOR = "card_floor_economics"
SPINE = "card_spine_economics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_economics_the_finance_arithmetic_verified_and_sealed"   # already minted; the floor cites it

F_MIND = "card_floor_the_mind"
F_STATS = "card_floor_statistics"
F_INSTR = "card_floor_the_instruments"

PILLARS = [
    dict(key="scarcity_choice", title="Scarcity and choice — incentives",
         body="Economics begins where wants exceed means: agents choose under scarcity, weighing costs against "
              "benefits and responding to incentives. Every price is a choice summed over many minds. Rests on the "
              "mind.",
         rests=[(F_MIND, "agents who choose - economics is minds responding to incentives under scarcity")]),
    dict(key="time_value", title="The time value of money — compound interest",
         body="A dollar now is worth more than a dollar later: compound interest grows it (sealed on the economics "
              "stick), present value discounts it back, and the rule of 72 estimates the doubling time. The "
              "arithmetic of time and money. Rests on the instruments.",
         rests=[(F_INSTR, "compound interest, present value and the rule of 72 - sealed finance arithmetic")]),
    dict(key="markets_prices", title="Markets and prices — supply, demand, elasticity",
         body="Price settles where supply meets demand, and elasticity measures how quantity answers a price change "
              "(sealed). The market is a measurement instrument for value, aggregating countless private choices into "
              "one public number. Rests on statistics and the mind.",
         rests=[(F_STATS, "elasticity and price data - measured, the statistics of markets"),
                (F_MIND, "a market price is many private choices aggregated")]),
    dict(key="aggregates", title="Aggregates — GDP, inflation, growth",
         body="The whole economy measured: GDP per capita, inflation, growth (sealed). Macroeconomics is statistics "
              "applied to a nation's output - noisy, revised, and still the dashboard by which policy is steered. "
              "Rests on statistics.",
         rests=[(F_STATS, "GDP, inflation and growth - national accounts are statistics")]),
]


def _pid(key: str) -> str:
    return f"card_econ_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — economics", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "economics", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Economics — minds that choose, meeting scarcity",
        ("The social rung: minds that choose, meeting scarcity. Scarcity and choice (incentives), the time value of "
         "money (compound interest, present value), markets and prices (supply, demand, elasticity), and aggregates "
         "(GDP, inflation). Four pillars rest on the mind (agents who choose), statistics (measurement), and the "
         "instruments (the finance arithmetic). The arithmetic is cited from the economics stick (" + STICK + "); no "
         "new stick (tools/seed_economics.py)."),
        ["floor", "economics", "markets", "incentives", "social", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Economics — a spine", "The pillars of economics.",
              ["economics", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the social world of choice on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["economics", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of economics ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the social world of choice on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_the_mind as MIND
        import seed_statistics as STATS
        import seed_instruments as SI
        ids |= {c["id"] for c in MIND.CARDS} | {c["id"] for c in STATS.CARDS} | {c["id"] for c in SI.CARDS}
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
