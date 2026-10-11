#!/usr/bin/env python3
"""SEED THE PLACEMENTS — file each uncharted stick and unmapped domain UNDER the floor whose subject it
shares, so it can inherit that floor's Scripture root (move 3 of the connection layer: close connectivity).

A placement is a TAXONOMY edge, not a proof: 'acoustics is a part of the acoustics floor', read straight
off the node's own name or title. It is NOT a chart (a chart cites a specific sealed mark and becomes a
corpus card); inheritance needs only the floor, so a node too far from the map to chart can still be
filed. Proposals (by='proposed'): the engine offering the filing, for the operator to keep or refuse. A
node whose subject matches NO floor confidently is left OPEN on purpose — a want, never a forced fit
(combinatorics, geometry, linear algebra, philosophy, archaeology have no floor yet; they stay open).

    PYTHONPATH=src python tools/seed_placements.py           # dry run — proposals + coverage, writes nothing
    PYTHONPATH=src python tools/seed_placements.py --apply    # keep them to data/placements.jsonl

Runs where the data lives (the box). Found on the node's own name, never declared past it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from concordance import chains, roots, tickstick  # noqa: E402

# subject keyword -> floor id. Keys are matched at a word start against the node's name / title lead,
# longest first, so a specific key (electrochem) wins over a general one (chem). Only confident
# categorizations: where the floor genuinely IS the home of the subject.
F = "card_floor_"
SUBJECT_FLOOR = {
    # life
    "biology": F+"biology", "genetic": F+"biology", "genetics": F+"biology", "genome": F+"biology",
    "protein": F+"biology", "alphafold": F+"biology", "enzyme": F+"biology", "metabolism": F+"biology",
    "cell": F+"biology", "microb": F+"biology", "physiology": F+"biology",
    "ecology": F+"ecology", "nutrition": F+"nutrition", "agriculture": F+"agriculture",
    "medicine": F+"medicine", "medical": F+"medicine", "exercise_science": F+"medicine", "disease": F+"medicine",
    "neuro": F+"the_mind", "neuroscience": F+"the_mind", "consciousness": F+"the_mind", "brain": F+"the_mind",
    "cognition": F+"the_mind", "perception": F+"the_mind",
    # matter / chemistry
    "electrochem": F+"chemistry", "periodic_table": F+"chemistry", "periodic": F+"chemistry",
    "molecular_geometry": F+"chemistry", "molecular": F+"chemistry", "chemistry": F+"chemistry",
    "chemical": F+"chemistry", "reaction": F+"chemistry",
    "physical_chemistry": F+"physical_chemistry", "electrochemistry": F+"physical_chemistry",
    "materials": F+"materials_science", "material": F+"materials_science", "architecture": F+"materials_science",
    "construction": F+"materials_science", "manufacturing": F+"materials_science",
    # physics
    "standard_model": F+"standard_model", "particle": F+"standard_model", "atomic": F+"standard_model",
    "condensed_matter": F+"quantum_mechanics", "quantum_computing": F+"quantum_computing",
    "quantum": F+"quantum_mechanics", "photonics": F+"optics", "optics": F+"optics", "photography": F+"optics",
    "maxwell": F+"maxwells_equations", "electrical": F+"maxwells_equations", "electromagnet": F+"maxwells_equations",
    "relativity": F+"relativity", "black_hole": F+"relativity", "black hole": F+"relativity",
    "thermodynam": F+"thermodynamics", "entropy": F+"thermodynamics", "energy": F+"thermodynamics",
    "nuclear": F+"nuclear_physics", "acoustics": F+"acoustics", "sound": F+"acoustics",
    "physical_constants": F+"metrology", "metrology": F+"metrology", "units": F+"metrology", "measurement": F+"metrology",
    # earth / sky
    "astronomy": F+"astronomy", "orbit": F+"astronomy", "ephemeris": F+"astronomy", "stellar": F+"astronomy",
    "planet": F+"astronomy", "celestial": F+"astronomy",
    "geology": F+"earth_science", "mineral": F+"earth_science", "tectonic": F+"earth_science",
    "soil": F+"soil_science", "hydrology": F+"hydrology", "oceanograph": F+"oceanography", "ocean": F+"oceanography",
    "meteorolog": F+"meteorology", "weather": F+"meteorology", "geography": F+"geography",
    # mind-made systems
    "economics": F+"economics", "finance": F+"economics", "labor": F+"economics", "real_estate": F+"economics",
    "logistics": F+"logistics", "operations_research": F+"logistics",
    "game": F+"game_theory", "chess": F+"game_theory", "pressure_fighting": F+"game_theory",
    "sports_analytics": F+"game_theory", "law": F+"law", "governance": F+"law", "education": F+"education",
    "music": F+"music", "music_theory": F+"music",
    # language
    "linguistics": F+"indo_european", "language": F+"indo_european", "phonics": F+"indo_european",
    "etymology": F+"indo_european", "wordcraft": F+"indo_european", "rhetoric": F+"indo_european",
    "grammar": F+"indo_european", "syntax": F+"indo_european", "morpholog": F+"indo_european",
    "semantic": F+"indo_european",
    # computation / information
    "computer": F+"computer_science", "computation": F+"computer_science", "algorithm": F+"computer_science",
    "information_theory": F+"computer_science", "formal_logic": F+"computer_science", "retrieval": F+"computer_science",
    "networking": F+"networking", "network": F+"networking",
    "cryptograph": F+"cryptography", "cybersecurity": F+"cryptography", "document_validation": F+"cryptography",
    # number (unanchored floors are valid placements; they inherit once their floor is anchored)
    "riemann": F+"riemann", "zeta": F+"riemann", "elliptic_curves": F+"bsd", "elliptic": F+"bsd",
    "statistics": F+"statistics", "probability": F+"statistics",
    "calendar": F+"the_calendar", "history_chronology": F+"the_calendar", "chronology": F+"the_calendar",
}
_KEYS = sorted(SUBJECT_FLOOR, key=len, reverse=True)
_FLOORS = set(chains.FLOORS)


def floor_for(text: str):
    s = re.sub(r"[_]+", " ", (text or "").lower())
    lead = re.split(r"\s[-–]\s", s)[0]   # for a stick title, the subject before ' - '
    for k in _KEYS:
        if re.search(r"(?<![a-z])" + re.escape(k), lead) and SUBJECT_FLOOR[k] in _FLOORS:
            return SUBJECT_FLOOR[k]
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    si = roots.stick_floor_index()                 # already-charted sticks (skip — a chart beats a filing)
    doms = list(json.load(open("data/domain_goldens.json", encoding="utf-8")).keys())
    sticks = tickstick.listing()["sticks"]

    proposals = []   # (node, floor, why)
    for d in doms:
        if f"{F}{d}" in _FLOORS:
            continue                                # already name-matches a floor
        fl = floor_for(d)
        if fl:
            proposals.append((roots.node_id("domain", d), fl, f"the {d.replace('_',' ')} domain is a part of {fl.replace(F,'')}"))
    for r in sticks:
        sid = r["id"]
        if sid in si:
            continue                                # already charted onto the map
        fl = floor_for(r.get("question") or sid)
        if fl:
            proposals.append((roots.node_id("stick", sid), fl, f"'{(r.get('question') or sid)[:50]}' is a part of {fl.replace(F,'')}"))

    kept = 0
    for node, fl, why in proposals:
        if a.apply:
            res = roots.place(node, fl, why=why, by="proposed", verify=True)
            kept += 1 if res.get("ok") else 0
        print(f"  {'placed' if a.apply else 'would place'} {node[:48]:48s} -> {fl.replace(F,'')}")
    print(f"\n{len(proposals)} placements proposed" + (f"; kept {kept}" if a.apply else " (dry run)"))

    cov = roots.resolved_coverage()
    print(f"\nRESOLVED: {cov['resolved']}/{cov['total_nodes']} ({cov['pct']}%) — direct {cov['direct']}, "
          f"inherited {cov['inherited']}, open {cov['open']}, unconnected {cov['unconnected']}")
    for k, v in cov["by_kind"].items():
        print(f"  {k:7s}: direct {v['direct']}, inherited {v['inherited']}, open {v['open']} (unconnected {v['unconnected']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
