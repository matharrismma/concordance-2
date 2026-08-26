#!/usr/bin/env python3
"""
THE GENESIS FLOOD — chiasm, measured (catalog target #1). Wenham's classic palistrophe of the flood
narrative (Genesis 6:9–9:19), centred on **8:1 "God remembered Noah"**, with numeric mirrors (7 / 40 /
150 days) and repeated vocabulary (ark, waters, mountains, covenant, sons) across the mirror pairs.
The assay is the same as Revelation/SoM: does the proposed mirror pairing echo above a random
re-pairing of the same units? Reads data/bible_en.jsonl. Pure stdlib, seeded.

Pairs are a defensible reading of Wenham (1978); the null tests the aggregate, robust to a stray pair.
"""
from __future__ import annotations

import json
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIBLE = ROOT / "data" / "bible_en.jsonl"
_STOP = set(("the a an of to and but in on for is are was were be his her my your their our its he "
             "she it they we you i o that this these those which who whom with as from by at into unto "
             "out up down shall will not no nor them him us me all there so then when have has had do "
             "did does said say came come go went every after upon also").split())

# (label, left ref, right ref) — the palistrophe, outer → centre (8:1).
PAIRS = [
    ("A  Noah & three sons",        "6:9-10",  "9:18-19"),
    ("B  earth's violence / covenant","6:11-12", "9:8-17"),
    ("C  build the ark / blood-life", "6:13-16", "9:1-7"),
    ("D  flood decreed / altar",     "6:17-22", "8:20-22"),
    ("E  enter the ark / leave it",  "7:1-5",   "8:15-19"),
    ("F  flood comes, 7 days / dove, 7 days, dried", "7:6-10", "8:10-14"),
    ("G  windows of heaven / window opened, raven", "7:11-16", "8:6-9"),
    ("H  40 days rise, mountains covered / abate, mountains seen", "7:17-20", "8:3-5"),
    ("I  all flesh dies, 150 days prevail / fountains stopped", "7:21-24", "8:2"),
]
CENTER = ("8:1", "God remembered Noah")


def _stem(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    for s in ("ing", "eth", "est", "ed", "es", "s"):
        if w.endswith(s) and len(w) - len(s) >= 3:
            return w[: -len(s)]
    return w


def load_gen():
    g = {}
    for line in open(BIBLE, encoding="utf-8"):
        c = json.loads(line)
        if c["book"] == "Genesis":
            g[(int(c["chapter"]), int(c["verse"]))] = c.get("text", "")
    return g


def stems_of(ref, gen):
    c, rng = ref.split(":")
    c = int(c)
    v1, v2 = (int(x) for x in rng.split("-")) if "-" in rng else (int(rng), int(rng))
    text = " ".join(gen.get((c, v), "") for v in range(v1, v2 + 1))
    return frozenset(s for s in (_stem(w) for w in text.split())
                     if s and s not in _STOP and len(s) >= 3)


def _jac(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


def main():
    if not BIBLE.exists():
        print("corpus not present")
        return
    gen = load_gen()
    left = [stems_of(l, gen) for _lab, l, _r in PAIRS]
    right = [stems_of(r, gen) for _lab, _l, r in PAIRS]
    echoes = [(_jac(left[i], right[i]), PAIRS[i]) for i in range(len(PAIRS))]
    proposed = statistics.mean(e for e, _ in echoes)

    rng = random.Random(1)
    null = []
    for _ in range(5000):
        perm = right[:]
        rng.shuffle(perm)
        null.append(statistics.mean(_jac(left[i], perm[i]) for i in range(len(left))))
    p = sum(1 for x in null if x >= proposed) / len(null)
    verdict = "CONFIRMED" if p < 0.01 else "PLAUSIBLE" if p < 0.05 else "RESONANCE" if p < 0.25 else "COINCIDENCE"

    print(f"Genesis Flood (6:9–9:19) — {len(PAIRS)} mirror pairs, centre 8:1 'God remembered Noah'\n")
    print(f"mean mirror-echo (chiastic pairing): {proposed:.3f}")
    print(f"mean mirror-echo (random re-pairing): {statistics.mean(null):.3f}")
    print(f"permutation p(random ≥ chiastic) = {p:.4f}   verdict {verdict}\n")
    print("the mirror pairs, by echo:")
    for e, (lab, l, r) in sorted(echoes, reverse=True):
        print(f"   {e:.2f}  {l:>9} <-> {r:<9}  {lab}")

    out = Path(__file__).with_name("RESULTS_FLOOD.md")
    lines = ["# The Genesis Flood — chiasm, measured", "",
             "Wenham's palistrophe of the flood narrative (Genesis 6:9–9:19), centred on **8:1 'God",
             "remembered Noah'**. Assay: does the proposed mirror pairing echo above a random re-pairing",
             "of the same units? Echo = Jaccard of content stems; null = permute the pairing 5000×.", "",
             f"- **mean mirror-echo, chiastic pairing: {proposed:.3f}**",
             f"- mean mirror-echo, random re-pairing: {statistics.mean(null):.3f}",
             f"- permutation p(random ≥ chiastic) = {p:.4f} → **{verdict}**", "",
             "The mirror pairs, by measured echo:", "", "| echo | refs | pairing |", "|---|---|---|"]
    for e, (lab, l, r) in sorted(echoes, reverse=True):
        lines.append(f"| {e:.2f} | {l} ↔ {r} | {lab} |")
    lines += ["",
              "**Honest reading: RESONANCE, not the clean CONFIRMED of Revelation.** The chiasm's lexical",
              "SPINE is clearly real — the three-sons frame (6:9-10↔9:18-19, 0.29), the 7-days/dove mirror",
              "(0.17), enter/leave the ark (0.13), waters-rise/abate + mountains (0.13), the windows",
              "(0.10). But three proposed pairs are lexically weak (violence↔covenant, ark-build↔blood,",
              "and the one-verse 8:2), and at only 9 pairs the null is wide, so the aggregate lands at",
              "RESONANCE (p≈0.13). Why weaker than Revelation: fewer pairs (9 vs 51), some mirrors are",
              "NUMERIC/thematic (150 days, covenant) rather than repeated words, and my unit boundaries",
              "for the weak pairs may not match Wenham's finer palistrophe. A finer pairing (Wenham's full",
              "~16 elements) would tighten the null and likely lift it. Three books, three honest",
              "verdicts: Revelation CONFIRMED (global lexical, p=0), Flood RESONANCE (real spine, fewer",
              "pairs), Sermon COINCIDENCE-global-but-local-frames — the measure is calibrated, not a",
              "rubber stamp. Next by the roadmap: Colossians 1:15–20 (the fascia's own 'in him all things",
              "hold together')."]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
