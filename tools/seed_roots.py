#!/usr/bin/env python3
"""SEED THE ROOTS — propose a Scripture anchor for each floor whose root in the Word is plain.

These are PROPOSALS (by='proposed'): the engine offering the verse a floor answers to, for the operator
to keep, edit, or refuse. Only the clear, defensible anchors are here — where the connection is already
the Word's own frame (Babel for the language family, "let there be light" for the unification of light,
"prove all things" for the verifiers). The abstract math floors and the evolution-adjacent ones are left
OPEN on purpose: those are the operator's discernment, not the engine's to presume. Every open floor is a
want (roots.coverage names them).

    PYTHONPATH=src python tools/seed_roots.py            # dry run — prints the proposals + coverage, writes nothing
    PYTHONPATH=src python tools/seed_roots.py --apply     # keep them to data/roots.jsonl (refs verified against the WEB)

Runs where the Bible lives (the box) so each proposed ref is verified to resolve before it is kept.
Found, never generated — every anchor is a real verse the engine can already cite.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from concordance import roots  # noqa: E402

# (floor id, [references], why) — the proposed anchor and the discernment behind it.
PROPOSED = [
    ("card_floor_the_capstone", ["Ephesians 2:20", "Psalm 118:22", "Colossians 1:17"],
     "Christ the cornerstone the builders rejected — one source in whom all things hold together; the floor the others stand on."),
    ("card_floor_standard_model", ["Genesis 1:1", "Colossians 1:16-17", "Hebrews 1:3"],
     "In the beginning God created; by Him all things were made and in Him hold together, upheld by the word of His power — the fundamental constituents and forces."),
    ("card_floor_maxwells_equations", ["Genesis 1:3", "1 John 1:5"],
     "The first unification is light — 'Let there be light'; 'God is light.'"),
    ("card_floor_thermodynamics", ["Psalm 102:25-26", "Romans 8:20-21"],
     "The arrow of time and the one end — the heavens wear out like a garment; creation subjected to decay, in hope of release."),
    ("card_floor_relativity", ["2 Peter 3:8", "Psalm 90:4"],
     "Time is not absolute — a thousand years are as one day with the Lord."),
    ("card_floor_quantum_mechanics", ["Hebrews 11:3", "Colossians 1:17"],
     "What is seen was made from what is unseen; the framework beneath the visible, He holding it together."),
    ("card_floor_noethers_theorem", ["Malachi 3:6", "Hebrews 13:8"],
     "Symmetry is the source of conservation — 'I the LORD do not change'; the invariance from which what is conserved flows."),
    ("card_floor_biology", ["Genesis 2:7", "Acts 17:25"],
     "Life is the breath given — the LORD God breathed into man the breath of life; He gives to all life and breath."),
    ("card_floor_the_mind", ["Genesis 1:27", "1 Corinthians 2:11"],
     "Matter aware of itself — made in the image of God; the spirit of man which is in him."),
    ("card_floor_earth_science", ["Job 38:4-6", "Genesis 1:9-10"],
     "The foundations of the earth and the gathering of the dry land — 'Where were you when I laid the earth's foundations?'"),
    ("card_floor_astronomy", ["Psalm 19:1", "Psalm 147:4", "Isaiah 40:26"],
     "The heavens declare the glory of God — He counts the number of the stars and calls them each by name."),
    ("card_floor_indo_european", ["Genesis 11:1-9"],
     "The one tongue scattered into families at Babel — the language family's own origin in the Word."),
    ("card_floor_the_instruments", ["1 Thessalonians 5:21", "Proverbs 18:17"],
     "Prove all things; hold fast the good — the first to plead his case seems right until another examines him. The verifiers test every claim."),
    ("card_floor_the_solve_path", ["Matthew 7:13-14"],
     "The narrow way between two errors — exclude the barriers, converge on the one end; strait is the gate."),
    ("card_floor_cryptography", ["Deuteronomy 29:29", "Proverbs 25:2"],
     "The secret things belong to the LORD; it is the glory of God to conceal a thing — hidden things and hard problems."),
    ("card_floor_statistics", ["Proverbs 16:33"],
     "The lot is cast into the lap, but its every decision is from the LORD — chance under providence, the normal law."),
    ("card_floor_chemistry", ["Genesis 3:19", "Colossians 1:17"],
     "The world of substances — 'dust you are, and to dust you shall return'; in Him all things hold together."),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="keep the proposals to data/roots.jsonl (default: dry run)")
    a = ap.parse_args(argv)

    kept = refused = 0
    for fid, refs, why in PROPOSED:
        node = roots.node_id("floor", fid)
        if a.apply:
            r = roots.anchor(node, refs, why=why, by="proposed", verify=True)
            if r.get("ok"):
                kept += 1
                print(f"  kept   {node:42s} -> {', '.join(refs)}")
            else:
                refused += 1
                print(f"  REFUSED {node:42s} -> {r.get('refused')} ({r.get('why')})")
        else:
            print(f"  would anchor {node:42s} -> {', '.join(refs)}")
    print(f"\n{len(PROPOSED)} proposed anchors" + (f"; kept {kept}, refused {refused}" if a.apply else " (dry run — nothing written)"))

    cov = roots.coverage()
    print(f"\nCOVERAGE: {cov['anchored']}/{cov['total_nodes']} nodes rooted ({cov['pct']}%); kept_by={cov['kept_by']}")
    for k, v in cov["by_kind"].items():
        print(f"  {k:7s}: {v['anchored']}/{v['total']} anchored, {len(v['open'])} open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
