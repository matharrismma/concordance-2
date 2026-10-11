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
    # batch 2 (2026-10-11) — the remaining floors whose root in the Word is well-established.
    ("card_floor_the_calendar", ["Genesis 1:14"],
     "The lights for signs and seasons — 'let them be for signs and for seasons, and for days and years.'"),
    ("card_floor_metrology", ["Proverbs 11:1", "Leviticus 19:36"],
     "Just measure — 'a false balance is an abomination to the LORD, but a just weight is his delight.'"),
    ("card_floor_acoustics", ["Psalm 150:3-5"],
     "Sound and harmony — praise him with trumpet, harp, strings, and the clash of cymbals."),
    ("card_floor_music", ["Psalm 96:1", "Job 38:7", "Colossians 3:16"],
     "Sing a new song — the morning stars sang together; sing with grace in your hearts to the Lord."),
    ("card_floor_agriculture", ["Genesis 8:22", "Galatians 6:7"],
     "Seedtime and harvest — 'whatever a man sows, that he will also reap.'"),
    ("card_floor_soil_science", ["Matthew 13:3-8", "Matthew 13:18-23"],
     "The living skin of the earth — the parable of the soils: the same seed, four grounds, four yields."),
    ("card_floor_ecology", ["Genesis 2:15", "Genesis 1:28"],
     "To tend and keep the garden — the stewardship of the living world given to man."),
    ("card_floor_nutrition", ["Genesis 1:29"],
     "The food given — 'I have given you every plant yielding seed... you shall have them for food.'"),
    ("card_floor_hydrology", ["Ecclesiastes 1:7", "Job 36:27-28"],
     "The water cycle — 'all the streams run to the sea... to the place where they flow, there they flow again.'"),
    ("card_floor_meteorology", ["Job 38:22-30", "Matthew 5:45"],
     "The storehouses of snow and rain — 'he sends rain on the just and on the unjust.'"),
    ("card_floor_oceanography", ["Psalm 104:25", "Job 38:16"],
     "The great and wide sea — 'have you entered into the springs of the sea?'"),
    ("card_floor_geography", ["Acts 17:26"],
     "The boundaries of dwelling — 'he determined allotted periods and the boundaries of their dwelling place.'"),
    ("card_floor_medicine", ["Jeremiah 8:22", "Proverbs 17:22"],
     "Healing — 'is there no balm in Gilead?'; 'a joyful heart is good medicine.'"),
    ("card_floor_optics", ["Matthew 6:22", "1 Corinthians 13:12"],
     "Light and the eye — 'the eye is the lamp of the body'; 'now we see through a glass, darkly.'"),
    ("card_floor_materials_science", ["Isaiah 64:8"],
     "The clay and the potter — 'we are the clay, and you our potter; we are all the work of your hand.'"),
    ("card_floor_nuclear_physics", ["2 Peter 3:10", "Colossians 1:17"],
     "The bound nucleus and the one end — 'the elements will melt with fervent heat'; in Him all holds together."),
    ("card_floor_economics", ["Matthew 25:14-30", "Luke 16:10-11"],
     "Stewardship of what is entrusted — the talents; 'faithful in little, faithful in much.'"),
    ("card_floor_logistics", ["Genesis 41:48-49"],
     "Store in the plenty for the lack — Joseph gathering grain through the seven years of abundance."),
    ("card_floor_law", ["Exodus 20:1-17", "Deuteronomy 16:20"],
     "The Law given — the Ten Commandments; 'justice, justice shall you pursue.'"),
    ("card_floor_education", ["Proverbs 22:6", "Deuteronomy 6:6-7"],
     "Train up a child — 'teach them diligently to your children, and talk of them when you sit in your house.'"),
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
