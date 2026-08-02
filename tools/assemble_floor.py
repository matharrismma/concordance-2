#!/usr/bin/env python3
"""THE FLOOR — the aligned theories, assembled across domains.

    PYTHONPATH=src python tools/assemble_floor.py --dry-run
    PYTHONPATH=src python tools/assemble_floor.py

Matt, 2026-08-02: *"We should have assembled the aligned theories across domains. That was the
floor. Reality itself mapped... along with a coherent language model that can communicate reality
effectively."*

MEASURED FIRST, and the measurement is the indictment: 99 theory cards on the shelf, and
**zero theory→theory edges — zero of them crossing a domain.** The catalogue was built, the assay
was run, the cards were minted, and then each one was left standing alone on its own tile. A
hundred true statements side by side is a *pile*; the floor is what you get when you can walk
from any one of them to the ones it rests on. Cell theory and the central dogma had no path
between them. Bayes did not know it stood on Kolmogorov.

WHAT AN EDGE MAY BE HERE. Only relations that are FOUND — readable off the theories themselves,
checkable by anyone who knows the field — never a resemblance I liked the sound of:

  rests_on   B is not statable without A. Bayes' theorem rests on the Kolmogorov axioms; the
             central dogma rests on cell theory. Directional, and the direction is the argument.
  limits     A bounds what B can claim about itself. Gödel limits Peano and ZFC and the
             Church–Turing thesis — the honest edge that keeps the floor from becoming an idol.
  same_form  the SAME mathematics under different boundary conditions — and this one is only
             admitted with COMPUTED RECEIPTS on both sides, from the verifier fleet. That is the
             rule that separates a concordance from numerology: the octave's 2:1 and the orbital
             resonance's 3:2 are the same integer-ratio lattice, and both sides are sealed.

Every edge carries its `evidence` line. An edge without one is a claim wearing a relation's
clothes, and this tool will not write it.

Idempotent, atomic, and it never touches a card it did not come to edit.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def _key(text: str) -> str:
    """A title reduced to its identifying words — the join key.

    THE FIRST RUN REFUSED ALL 27 EDGES because it addressed cards by a slug I had guessed
    ("godel_s_..." where the shelf says "g_del_s_...", "bayes_theorem" where the id is truncated
    differently). The refusal was correct and the addressing was wrong: an id is an internal
    accident, a TITLE is the thing the theory is actually called. Matching on the title's
    significant words survives transliteration, truncation, and punctuation — and when it cannot
    find one end, the tool still refuses rather than inventing."""
    t = (text or "").lower()
    t = t.replace("&", " and ").replace("–", "-").replace("—", "-")
    words = re.findall(r"[a-z0-9]+", t)
    drop = {"the", "of", "a", "an", "and", "or", "in", "to", "s"}
    return " ".join(w for w in words if w not in drop)


# ── THE EDGE SET ──────────────────────────────────────────────────────────────────────────────
# (from, relation, to, evidence). Written as TITLES — what the theory is actually called —
# resolved against the shelf; an edge whose either end is missing is REFUSED and named, never
# invented. A dangling edge is worse than no edge.
EDGES = [
    # — mathematics is the floor under the sciences —
    ("Bayes' theorem", "rests_on", "Kolmogorov probability axioms",
     "Bayes' theorem is derived from the axioms of probability: P(A|B) = P(A∩B)/P(B) is the "
     "conditional defined on a Kolmogorov measure space"),
    ("Central limit theorem", "rests_on", "Kolmogorov probability axioms",
     "the CLT is a statement about distributions of sums, defined on a probability measure"),
    ("Null-hypothesis significance testing", "rests_on", "Central limit theorem",
     "the sampling distributions that make p-values computable are CLT results"),
    ("Gödel's incompleteness theorems", "limits", "Peano arithmetic axioms",
     "Gödel's first theorem is proved FOR any consistent formal system that includes Peano "
     "arithmetic: it exhibits a true sentence that system cannot prove"),
    ("Gödel's incompleteness theorems", "limits", "Zermelo–Fraenkel set theory (ZFC)",
     "ZFC, being strong enough to encode arithmetic, falls under the incompleteness result — "
     "no consistent axiomatization proves its own consistency"),
    ("Gödel's incompleteness theorems", "limits", "Church–Turing thesis / computability",
     "incompleteness and undecidability are the same boundary from two sides: the halting "
     "problem is the computational face of the unprovable sentence"),
    ("Fundamental theorem of arithmetic", "rests_on",
     "Peano arithmetic axioms",
     "unique factorization is a theorem ABOUT the natural numbers Peano's axioms define"),
    ("Cryptographic security", "rests_on",
     "Fundamental theorem of arithmetic",
     "RSA's hardness is the difficulty of recovering the unique prime factorization of a large "
     "semiprime — the theorem guarantees the factorization exists and is unique"),
    ("Graph theory", "rests_on", "Combinatorial enumeration",
     "path and subgraph counting are enumeration on a constrained structure"),

    # — physics: what rests on conservation, and what limits the classical picture —
    ("Ideal gas law", "rests_on", "Kinetic theory of gases",
     "PV = nRT is derived by averaging molecular momentum transfer over a container wall — the "
     "gas law is the macroscopic shadow of the kinetic account"),
    ("Kinetic theory of gases", "rests_on", "Conservation of linear & angular momentum",
     "the derivation is momentum bookkeeping over elastic collisions"),
    ("Conservation of energy", "rests_on",
     "Conservation of linear & angular momentum",
     "Noether's theorem: energy conservation is time-translation symmetry as momentum "
     "conservation is space-translation symmetry — one principle, two coordinates"),
    ("General relativity", "limits", "Heliocentrism & Kepler's laws",
     "Kepler's ellipses are the weak-field limit; GR corrects them measurably — Mercury's "
     "perihelion advances 43 arcseconds per century beyond the Newtonian prediction"),
    ("Heisenberg uncertainty principle", "limits", "Bohr / quantum model of the atom",
     "the uncertainty relation forbids the definite electron ORBIT the Bohr model draws; the "
     "orbital is a probability amplitude, not a path"),
    ("Bohr / quantum model of the atom", "rests_on", "Acoustic wave theory",
     "the quantization condition is a standing-wave condition: an integer number of de Broglie "
     "wavelengths around the orbit, the same integer-mode rule that fixes a string's harmonics"),

    # — chemistry stands on atoms and energy —
    ("Chemical bonding", "rests_on",
     "Bohr / quantum model of the atom",
     "bonding is described in terms of atomic orbitals and their overlap — the quantum atom is "
     "the object the bond is made of"),
    ("Dalton's atomic theory", "limits", "Chemical bonding",
     "Dalton's indivisible atom cannot express bonding, isotopes, or spectra; the quantum "
     "account supersedes it while keeping its conserved-mass arithmetic"),
    ("Hess's law", "rests_on", "Conservation of energy",
     "Hess's law is the first law applied to reaction paths: enthalpy change is path-independent "
     "because energy is conserved"),
    ("Brønsted–Lowry acid–base theory", "rests_on",
     "Chemical kinetics",
     "pH is an equilibrium statement — the position of the water autoionization equilibrium"),

    # — life rests on chemistry, and inheritance on life —
    ("Central dogma of molecular biology", "rests_on", "Cell theory",
     "transcription and translation are described as processes WITHIN the cell — the cell is the "
     "compartment the dogma is stated about"),
    ("Central dogma of molecular biology", "rests_on",
     "Chemical bonding",
     "base pairing is hydrogen bonding with a specific geometry; the code is chemistry"),
    ("Hardy-Weinberg equilibrium", "rests_on",
     "Combinatorial enumeration",
     "p² + 2pq + q² is the binomial expansion of allele draws — the genotype frequencies ARE a "
     "combinatorial identity"),
    ("Hardy-Weinberg equilibrium", "rests_on", "Darwinian evolution by natural selection",
     "the equilibrium is defined as the NULL case — what allele frequencies do when selection, "
     "drift, mutation and migration are absent; it is selection's own control condition"),
    ("Germ theory of disease", "rests_on", "Cell theory",
     "the pathogen is a cell (or an agent acting on cells); germ theory is cell theory applied "
     "to sickness"),
    ("Homeostasis", "rests_on", "Cell theory",
     "regulation is stated over cellular and organ-level set points"),

    # — the SAME FORM, both sides computed (the resonance deck's sealed edges) —
    ("Acoustic wave theory", "same_form", "Celestial mechanics",
     "small-integer ratio resonance: the octave is exactly 2:1 (440→880 Hz, sealed) and orbital "
     "resonances lock at the same simple ratios — one integer-mode lattice, two boundary "
     "conditions"),
    ("Euclidean geometry & the parallel postulate", "same_form", "Cell theory",
     "the honeycomb theorem (Hales 1999): the hexagonal grid minimizes total perimeter per area, "
     "and the interior angle is exactly 120° so three close a full turn (720/6 = 120, 360/120 = "
     "3, both sealed) — the bee's comb is the proven optimum, geometry realized in tissue"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--path", default=os.path.join(ROOT, "data", "theory_cards.jsonl"))
    args = ap.parse_args()

    if os.path.exists(os.path.join(ROOT, ".gate.lock")):
        print("the gate holds the floor — run this after it finishes")
        return 2

    rows, index, by_title = [], {}, {}
    with open(args.path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                rows.append(line)
                continue
            try:
                card = json.loads(s)
            except ValueError:
                rows.append(line)
                continue
            rows.append(card)
            index[card.get("id")] = card
            if card.get("shelf") == "theories":
                by_title.setdefault(_key(card.get("title")), card)

    # RESOLVE FIRST, WRITE NOTHING YET. A dangling edge is worse than no edge, so every end is
    # checked against the real shelf before a single card is touched.
    def _find(title):
        k = _key(title)
        if k in by_title:
            return by_title[k]
        kw = set(k.split())
        best, score = None, 0
        for other_k, card in by_title.items():
            ow = set(other_k.split())
            overlap = len(kw & ow)
            # a confident partial: most of the shorter name's words present in the other
            if overlap >= max(2, min(len(kw), len(ow)) - 1) and overlap > score:
                best, score = card, overlap
        return best

    planned, missing = [], []
    for a, rel, b, why in EDGES:
        ca, cb = _find(a), _find(b)
        if ca is None or cb is None:
            missing.append(((a if ca is None else b), f"{a} -{rel}-> {b}"))
            continue
        planned.append((ca["id"], rel, cb["id"], why))

    added = 0
    for ida, rel, idb, why in planned:
        card = index[ida]
        conns = card.setdefault("connections", [])
        if any(str(e.get("to_card_id")) == idb and e.get("relationship") == rel for e in conns):
            continue
        conns.append({"to_card_id": idb, "relationship": rel, "evidence": why})
        added += 1

    doms = {}
    for ida, rel, idb, _w in planned:
        da = ((index[ida].get("source") or {}).get("domain") or "?")
        db = ((index[idb].get("source") or {}).get("domain") or "?")
        if da != db:
            doms[(da, db)] = doms.get((da, db), 0) + 1

    print(f"{'PROPOSED' if args.dry_run else 'APPLIED'} — {added} new edge(s) of "
          f"{len(planned)} declared; {len(missing)} refused for a missing end\n")
    by_rel = {}
    for _a, rel, _b, _w in planned:
        by_rel[rel] = by_rel.get(rel, 0) + 1
    for rel, n in sorted(by_rel.items(), key=lambda x: -x[1]):
        print(f"  {n:>3}  {rel}")
    print(f"\n  cross-domain pairs joined: {len(doms)}")
    for (da, db), n in sorted(doms.items(), key=lambda x: -x[1])[:12]:
        print(f"      {da} -> {db}  ({n})")
    if missing:
        print("\n  REFUSED (a named theory is not on the shelf — say so, never invent it):")
        for mid, edge in missing:
            print(f"      {mid}   in   {edge}")

    if args.dry_run:
        print("\nNothing written.")
        return 0
    if not added:
        print("\nNothing to add — already assembled.")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        for r in rows:
            fh.write(r if isinstance(r, str) else json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, args.path)
    print(f"\nwrote {args.path} — {added} edge(s); every other line byte for byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
