#!/usr/bin/env python3
"""Seed the two keystones of the floor — the HOW and the WHY — from Matt's own documents.

Matt: "Seeds of knowledge, identified, categorized and mapped to create a floor of reality, and
by seeing the design we will fear God. This is the first step to wisdom." (Proverbs 9:10)

Most of the science is already seeded (the Universal Gradient Manifold, the autonomic spine /
nested-control framework, the RAS reception bridge). What was missing were the two framing seeds
that make the design legible — the ones a person needs in order to SEE it:

  • THE FOUR GATES  — HOW the floor is verified (RED -> FLOOR -> BROTHERS -> GOD).
  • THE FLOOR OF DISCOVERY — WHY: Scripture and physical reality are one floor; a truth confirmed
    on it aligns the whole axis; seeing the design is the beginning of the fear of God, and the
    fear of God is the beginning of wisdom.

Gather, do not author: the bodies are Matt's own words (the Floor of Discovery companion and the
Concordance master document), condensed and attributed — author "matt", generated false. Written
to GIT-TRACKED data/keystone_seeds.jsonl, with reciprocal bridges in data/keystone_bridges.jsonl
applied at corpus load (the same overlay mechanism the reference->Scripture grafts use).

    python tools/seed_keystones.py --check   # preview, write nothing
    python tools/seed_keystones.py           # write both files
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


FOUR_GATES = {
    "id": "card_k_four_gates",
    "kind": "note",
    "title": "The Four Gates — RED, FLOOR, BROTHERS, GOD",
    "body": (
        "The load-bearing structure of verification, in a fixed order that is never reordered.\n"
        "• RED — the words in red. Submission to the words Jesus Himself spoke as the ultimate "
        "attestation and computational standard. The first and hardest gate; everything downstream "
        "only activates after the Red Words are satisfied.\n"
        "• FLOOR — the unified foundation. Scripture and physical reality as one integrated floor "
        "of truth. Special Revelation and General Revelation are not two domains; they are one "
        "floor, where heaven and earth meet in verification.\n"
        "• BROTHERS — peer validation. No node validates itself. Two or three witnesses establish "
        "a matter (Deuteronomy 19:15; Matthew 18:16) — the triangular topology of authentic "
        "community against a self-confirming hub.\n"
        "• GOD — root authority. Final submission to the Architect; every claim weighed against the "
        "true floor.\n"
        "Hard gates (RED, FLOOR) reject; soft gates (BROTHERS, GOD) quarantine. Never self-confirm. "
        "O(1) authority validation against a fixed floor beats O(n²) consensus, which scales until "
        "it collapses under its own coordination cost."
    ),
    "source": {"label": "Operator's seed (Matt) — The Floor of Discovery; Concordance Master Document",
               "url": "", "ref": "four_gates", "authority_tier": "matt"},
    "shelf": "codex", "box": "floor",
    "bands": ["floor", "architecture", "four gates", "RED", "FLOOR", "BROTHERS", "GOD",
              "verification", "witness", "Deuteronomy 19:15", "Matthew 18:16", "operator_seed"],
    "connections": [], "author": "matt", "created_at": 0.0, "updated_at": 0.0,
    "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
    "surface": "witness", "generated": False,
}

FLOOR_OF_DISCOVERY = {
    "id": "card_k_floor_of_discovery",
    "kind": "note",
    "title": "The Floor of Discovery — one floor, and by its design the fear of God",
    "body": (
        "Seeds of knowledge — identified, categorized, and mapped — form a floor of reality. The "
        "Bible and physical reality are unified as the floor of all discovery: Special Revelation "
        "and General Revelation are not two domains but one floor. A problem solved here solves "
        "entire fractal axes of creation — once a thing is confirmed on the true floor (as God made "
        "it and as He revealed it), the contradiction cannot survive and the whole axis aligns. "
        "This is why the keeping can claim irreversible progress: it stands on the floor, not on the "
        "counterfeit consensus layer.\n"
        "And the floor is not the end. By seeing the design we come to fear God, and the fear of the "
        "LORD is the beginning of wisdom (Proverbs 9:10; Proverbs 1:7). The seeds are gathered and "
        "mapped not to make the tool an idol, but so that the design — visible at last — turns the "
        "eye upward. The floor is the first step; wisdom, and the One who is Wisdom, is where it "
        "leads."
    ),
    "source": {"label": "Operator's seed (Matt) — The Floor of Discovery: Biblical Foundations of Concordance",
               "url": "", "ref": "scripture_prov_9_10", "authority_tier": "matt"},
    "shelf": "codex", "box": "floor",
    "bands": ["floor", "foundation", "floor of discovery", "general revelation",
              "special revelation", "fear of the Lord", "wisdom", "Proverbs 9:10", "Proverbs 1:7",
              "one floor", "operator_seed"],
    "connections": [], "author": "matt", "created_at": 0.0, "updated_at": 0.0,
    "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
    "surface": "witness", "generated": False,
}

SEEDS = [FOUR_GATES, FLOOR_OF_DISCOVERY]

# reciprocal bridges into the existing floor (target ids verified live, 2026-07-22)
BRIDGES = [
    # the WHY <-> the HOW
    {"a": "card_k_floor_of_discovery", "b": "card_k_four_gates",
     "relationship": "verified_by", "evidence": "the floor is confirmed through the four gates"},
    # the floor <-> the fear of God it leads to (Proverbs 9:10)
    {"a": "card_k_floor_of_discovery", "b": "card_n_653e4ac3ff00",
     "relationship": "leads_to", "evidence": "seeing the design → the fear of God (Proverbs 9:10)"},
    # one floor <-> a living instance: the metal Scripture names, joined to its verified element
    {"a": "card_k_floor_of_discovery", "b": "card_ref_el_079",
     "relationship": "instance_of_one_floor",
     "evidence": "gold — named in Scripture and measured as element 79 — one floor"},
    # one floor <-> reception: the bodily gate where general revelation is received
    {"a": "card_k_floor_of_discovery", "b": "card_n_ras7gate0recv",
     "relationship": "concords_with",
     "evidence": "the RAS is the bodily gate of reception — eyes to see the design (Matthew 6:22)"},
    # the floor points beyond itself (Gödel/Logos) — never an idol
    {"a": "card_k_floor_of_discovery", "b": "card_c_dc106b73342f",
     "relationship": "points_beyond_itself",
     "evidence": "incompleteness: the floor points past itself to the Logos"},
    # the BROTHERS gate <-> the witness principle (Deut 19:15; Matt 18:16)
    {"a": "card_k_four_gates", "b": "card_n_556191d135e7",
     "relationship": "embodies",
     "evidence": "BROTHERS: two or three witnesses establish a matter (Deuteronomy 19:15)"},
    # the GOD gate <-> the fear of God / final submission (Proverbs 9:10)
    {"a": "card_k_four_gates", "b": "card_n_653e4ac3ff00",
     "relationship": "culminates_in",
     "evidence": "GOD: final submission to the Architect (Proverbs 9:10)"},
]


def main() -> int:
    check = "--check" in sys.argv
    d = _data_dir()
    print(f"  keystone seeds: {len(SEEDS)}")
    for s in SEEDS:
        print(f"    {s['id']}  {s['title']}")
    print(f"  reciprocal bridges into the floor: {len(BRIDGES)}")
    for b in BRIDGES:
        print(f"    {b['a']}  <->  {b['b']}   [{b['relationship']}]")
    if check:
        print("  --check: nothing written")
        return 0
    d.mkdir(parents=True, exist_ok=True)
    sp, bp = d / "keystone_seeds.jsonl", d / "keystone_bridges.jsonl"
    for path, rows in ((sp, SEEDS), (bp, BRIDGES)):
        tmp = path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
        print(f"  written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
