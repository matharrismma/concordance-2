#!/usr/bin/env python3
"""Seed the Standard-Model discovery chain (Matt, 2026-10-07: 'chains that began with a floor ... where two
trees connect'). Writes two size-aware data files:

  * data/chain_cards.jsonl   — the floor spine + the lightweight discovery (builder) cards for the lineage
                               Fermi -> Yang-Mills -> Lee/Wu -> Nambu -> Higgs -> Weinberg/Salam ->
                               Gell-Mann -> Gross/Politzer. Maxwell already exists (card_builder_james_
                               clerk_maxwell) and is REUSED, not recreated.
  * data/chain_bridges.jsonl — the edges only (id -> id), folded into the cards by corpus._apply_bridges:
                               part_of (to the floor), and builds_on (the chain; reciprocal 'enables' lets
                               it be walked forward from the floor). No card body is duplicated.

The connection where the two trees meet is Weinberg (electroweak unification): he builds_on both the weak
lineage (Higgs/Yang) AND Maxwell's electromagnetism, so chains.intersect(Fermi, Maxwell) over 'enables'
returns him.

    PYTHONPATH=src python tools/seed_standard_model_chain.py           # write the two files
    PYTHONPATH=src python tools/seed_standard_model_chain.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

SPINE = "card_spine_builders"
FLOOR = "card_floor_standard_model"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
MAXWELL = "card_builder_james_clerk_maxwell"   # already in data/contributors_cards.jsonl — reused


def _builder(slug: str, name: str, era: str, gift: str) -> dict:
    return {
        "id": f"card_builder_{slug}", "kind": "reference", "title": name,
        "body": (f"{name} ({era}) - physics. {gift} (A builder of the Floor of Discovery, credited with "
                 f"love and calibrated to the one plumb-line - honored for the truth kept, not judged.)"),
        "source": {"label": "The builders of the Floor - credited with love, calibrated to the plumb-line",
                   "url": "", "domain": "history of ideas", "authority_tier": "reference"},
        "shelf": "builders", "box": "science",
        "bands": ["builder", "contributor", "science", "standard model", slug.replace("_", " ")],
        "subject": name,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "a builder of the Floor, credited with love"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"field": "physics", "era": era, "gift": gift}, "call": "builders.science",
    }


FLOOR_CARD = {
    "id": FLOOR, "kind": "note",
    "title": "The floor of the Standard Model - where two trees meet",
    "body": ("The Standard Model of particle physics stands on two roots: Maxwell's electromagnetism (the "
             "electromagnetic tree) and Fermi's 1933 theory of the weak interaction (the weak tree), both on "
             "quantum mechanics and special relativity. The path from this floor is a chain of builders, and "
             "the two trees CONNECT at electroweak unification (Glashow-Weinberg-Salam), hinged on the "
             "Weinberg angle cos(theta_W) = m_W/m_Z. A chain begins from a floor; the connections are where "
             "two chains become one."),
    "source": {"label": "Narrow Highway - the Standard-Model chain (operator seed)", "url": "",
               "ref": "stick_the_standard_model_chain_where_two_trees_connect", "authority_tier": "engine_derived"},
    "shelf": "codex", "box": "floor",
    "bands": ["floor", "standard model", "electroweak", "chain", "two trees", "physics"],
    "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
    "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
}

BUILDERS = [
    _builder("enrico_fermi", "Enrico Fermi", "1901-1954 AD",
             "the first theory of the weak interaction (beta decay, 1933) - the root of the weak tree"),
    _builder("chen_ning_yang", "Chen Ning Yang", "1922-2024 AD",
             "non-abelian gauge theory with Mills (1954), and with Lee the prediction of parity violation "
             "(1956) - the trunk of the Standard Model"),
    _builder("tsung_dao_lee", "Tsung-Dao Lee", "1926-2024 AD",
             "with Yang, the prediction that parity is not conserved in the weak interaction (1956)"),
    _builder("chien_shiung_wu", "Chien-Shiung Wu", "1912-1997 AD",
             "the experiment that confirmed parity violation in beta decay (1957)"),
    _builder("yoichiro_nambu", "Yoichiro Nambu", "1921-2015 AD",
             "spontaneous symmetry breaking in particle physics - the mechanism later used to give gauge "
             "bosons mass"),
    _builder("peter_higgs", "Peter Higgs", "1929-2024 AD",
             "the mechanism (1964) by which gauge bosons acquire mass through spontaneous symmetry breaking "
             "- the Higgs field"),
    _builder("steven_weinberg", "Steven Weinberg", "1933-2021 AD",
             "electroweak unification (1967) - the theory that joins electromagnetism and the weak force, "
             "where the two trees connect"),
    _builder("abdus_salam", "Abdus Salam", "1926-1996 AD",
             "electroweak unification (1968), independently with Weinberg and Glashow"),
    _builder("murray_gell_mann", "Murray Gell-Mann", "1929-2019 AD",
             "quarks and the eightfold way - the foundation of quantum chromodynamics, the strong-force "
             "gauge theory"),
    _builder("david_gross", "David Gross", "1941- AD",
             "asymptotic freedom of quantum chromodynamics (1973) - quarks free at short distance, confined "
             "at long"),
    _builder("hugh_david_politzer", "Hugh David Politzer", "1949- AD",
             "asymptotic freedom of quantum chromodynamics (1973), independently"),
]

CARDS = [FLOOR_CARD] + BUILDERS


def _b(slug: str) -> str:
    return f"card_builder_{slug}"


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES = [
    # the floor hangs under the one Floor of Discovery; the two roots are part_of this path's floor
    _edge(FLOOR, GLOBAL_FLOOR, "part_of", "the Standard-Model path rests on the one Floor of Discovery"),
    _edge(MAXWELL, FLOOR, "part_of", "electromagnetism - the EM root of the Standard-Model floor"),
    _edge(_b("enrico_fermi"), FLOOR, "part_of", "the weak interaction - the weak root of the floor"),
    # the chain: a later work builds_on an earlier one (reciprocal 'enables' = floor forward)
    _edge(_b("chen_ning_yang"), _b("enrico_fermi"), "builds_on", "non-abelian gauge theory extends the weak interaction"),
    _edge(_b("tsung_dao_lee"), _b("chen_ning_yang"), "builds_on", "parity violation predicted in the weak sector (1956)"),
    _edge(_b("chien_shiung_wu"), _b("tsung_dao_lee"), "builds_on", "experimental confirmation of parity violation (1957)"),
    _edge(_b("yoichiro_nambu"), _b("chen_ning_yang"), "builds_on", "spontaneous symmetry breaking in gauge theory"),
    _edge(_b("peter_higgs"), _b("yoichiro_nambu"), "builds_on", "the mass mechanism from spontaneous symmetry breaking (1964)"),
    _edge(_b("steven_weinberg"), _b("peter_higgs"), "builds_on", "electroweak unification uses the Higgs mechanism (1967)"),
    _edge(_b("steven_weinberg"), _b("chen_ning_yang"), "builds_on", "electroweak is a non-abelian gauge theory"),
    _edge(_b("steven_weinberg"), MAXWELL, "builds_on", "electroweak UNIFIES electromagnetism with the weak force - where the two trees connect"),
    _edge(_b("abdus_salam"), _b("peter_higgs"), "builds_on", "electroweak unification (1968)"),
    _edge(_b("murray_gell_mann"), _b("chen_ning_yang"), "builds_on", "QCD is a non-abelian gauge theory (quarks, the eightfold way)"),
    _edge(_b("david_gross"), _b("murray_gell_mann"), "builds_on", "asymptotic freedom of QCD (1973)"),
    _edge(_b("hugh_david_politzer"), _b("murray_gell_mann"), "builds_on", "asymptotic freedom of QCD (1973)"),
]


def _validate() -> list:
    errs = []
    ids = {c["id"] for c in CARDS} | {MAXWELL, GLOBAL_FLOOR, SPINE}
    for c in CARDS:
        for k in ("id", "kind", "title", "body", "shelf", "connections"):
            if k not in c:
                errs.append(f"{c.get('id')}: missing {k}")
        json.dumps(c)  # must serialize
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"bridge endpoint not seeded (ok if live): {e['a']}")
        # b may be an existing live card (maxwell/global floor) — not an error
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    if errs:
        print("VALIDATION:")
        for e in errs:
            print("  " + e)
    if check:
        print(f"[check] {len(CARDS)} cards, {len(BRIDGES)} bridges; "
              f"{'OK' if not [e for e in errs if 'missing' in e] else 'ERRORS'}")
        return 1 if [e for e in errs if "missing" in e] else 0
    # THE ONE MAP (2026-10-09): the two files are shared with every other floor's seed - MERGE, never overwrite
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
