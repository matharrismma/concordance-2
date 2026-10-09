#!/usr/bin/env python3
"""The tree of life on the one map: phylogeny is the comparative method for genes.

Matt, 2026-10-09: "We will cover every domain. Starting with genomics". Phylogeny is the EXACT parallel of the
Indo-European floor. The floor is LUCA, the last universal common ancestor. The trees are the three DOMAINS of life
(Bacteria, Archaea, Eukaryota). A homologous GENE - one present in every lineage, descended from a single ancestral
gene - is the confluence where the domains meet, as 'father' is the cognate shared by every Indo-European branch. The
chain's rule is molecular evolution (substitution, conserved residues), the genetic counterpart of a sound law.

Honest line: the domains and the gene homologies are ATTESTED (shared sequence/structure); the ancestral sequences
are RECONSTRUCTIONS - postulates, cited, never sealed. floor_map reads: parts = the domains, confluences =
intersect(domain, domain) = the universal gene they share. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_tree_of_life.py [--check]
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

FLOOR = "card_floor_tree_of_life"
GLOBAL_FLOOR = "card_k_floor_of_discovery"

DOMAINS = [
    ("bacteria", "Bacteria", "the prokaryotes without a nucleus; E. coli, cyanobacteria, the gut flora"),
    ("archaea", "Archaea", "prokaryotes distinct from bacteria; methanogens, halophiles, thermophiles - Woese's third domain"),
    ("eukaryota", "Eukaryota", "cells with a nucleus; animals, plants, fungi, protists"),
]

# slug, gene, function, the domains it is found in (all three = universal), the conservation note
GENES = [
    ("ssu_rrna", "small-subunit ribosomal RNA", "the RNA core of the small ribosomal subunit (16S in prokaryotes, "
     "18S in eukaryotes)", ["bacteria", "archaea", "eukaryota"],
     "the molecule Carl Woese used to draw the three-domain tree - universal, slow-changing, in every cell"),
    ("ef_tu", "elongation factor (EF-Tu / EF-1alpha)", "delivers each aminoacyl-tRNA to the ribosome during translation",
     ["bacteria", "archaea", "eukaryota"], "one of the most conserved proteins in all of life"),
    ("atp_synthase", "ATP synthase", "the rotary enzyme that makes ATP from a proton gradient (F-type / A-type / V-type)",
     ["bacteria", "archaea", "eukaryota"], "the same rotary machine, homologous across all three domains"),
    ("aars", "aminoacyl-tRNA synthetases", "charge each tRNA with its correct amino acid - the enzymes that READ the "
     "genetic code", ["bacteria", "archaea", "eukaryota"],
     "present in every cell; the physical implementation of the code the genomics stick seals"),
]


def _did(slug: str) -> str:
    return f"card_tol_domain_{slug}"


def _gid(slug: str) -> str:
    return f"card_gene_{slug}"


def domain_card(slug, name, desc) -> dict:
    return {
        "id": _did(slug), "kind": "reference", "title": f"{name} — a domain of life",
        "body": f"{name}: {desc}. A primary branch of the tree of life, descended from the last universal common "
                f"ancestor; the universal genes below are shared with the other domains and meet them at their "
                f"ancestral form.",
        "source": {"label": "the tree of life (molecular phylogenetics; Woese 1990)", "url": "", "domain": "biology",
                   "authority_tier": "reference"},
        "shelf": "codex", "box": "domain_of_life",
        "bands": ["tree of life", "domain", slug, "biology", "phylogeny"],
        "subject": name, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def gene_card(slug, gene, func, domains, note) -> dict:
    where = ", ".join(d.capitalize() for d in domains)
    return {
        "id": _gid(slug), "kind": "reference", "title": f"{gene} — a universal gene (a homolog across the domains)",
        "body": (f"{gene}: {func}. Found in {where} - a homologous gene descended from a single ancestral gene in "
                 f"LUCA, so it is the confluence where those lineages meet, the way a cognate is shared across "
                 f"language branches. {note}. The homology is attested; the ancestral sequence is a reconstruction "
                 f"(a postulate, not sealed)."),
        "source": {"label": "molecular phylogenetics; universal homologs of LUCA", "url": "",
                   "ref": "stick_genomics_the_genetic_code_verified_and_sealed", "domain": "biology",
                   "authority_tier": "reference"},
        "shelf": "codex", "box": "universal_gene",
        "bands": ["tree of life", "homolog", "universal gene", slug, "biology", "phylogeny"],
        "subject": gene, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def floor_card() -> dict:
    return {
        "id": FLOOR, "kind": "note", "title": "The tree of life — chains from LUCA, homologous genes where domains meet",
        "body": ("The tree of life as a floor on the one map, the exact parallel of the Indo-European floor. The floor "
                 "is LUCA, the last universal common ancestor. The trees are the three DOMAINS (Bacteria, Archaea, "
                 "Eukaryota). A universal GENE - the small-subunit ribosomal RNA, elongation factor, ATP synthase, the "
                 "aminoacyl-tRNA synthetases - is the confluence where the domains meet, descended from one ancestral "
                 "gene, as 'father' is the cognate shared by every Indo-European branch. The chain's rule is molecular "
                 "evolution. The homologies are attested; the ancestral sequences are reconstructions - postulates, "
                 "cited, never sealed. Found, never generated (tools/seed_tree_of_life.py)."),
        "source": {"label": "Narrow Highway — the tree of life (molecular phylogenetics)", "url": "",
                   "ref": "stick_genomics_the_genetic_code_verified_and_sealed", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor",
        "bands": ["floor", "tree of life", "phylogeny", "genomics", "two trees", "biology", "one map"],
        "subject": "The tree of life", "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


CARDS: List[dict] = ([floor_card()]
                     + [domain_card(*d) for d in DOMAINS]
                     + [gene_card(*g) for g in GENES])


def _edge(a, b, rel, ev) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out = [_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the tree of life rests on the one Floor of Discovery")]
    for slug, name, _ in DOMAINS:
        out.append(_edge(_did(slug), FLOOR, "part_of", f"a domain (branch) of the tree of life: {name}"))
    for slug, gene, func, domains, note in GENES:
        for d in domains:
            out.append(_edge(_gid(slug), _did(d), "builds_on", f"{gene}: present in {d.capitalize()}"))
    return out


BRIDGES: List[dict] = _bridges()


def _validate() -> List[str]:
    errs = []
    ids = {c["id"] for c in CARDS}
    doms = {_did(s) for s, _, _ in DOMAINS}
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']}")
    for slug, gene, func, domains, note in GENES:
        for d in domains:
            if _did(d) not in doms:
                errs.append(f"{gene}: domain not declared: {d}")
    if len(ids) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(DOMAINS)} domains + {len(GENES)} genes + floor), "
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
