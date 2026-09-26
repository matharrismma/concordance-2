#!/usr/bin/env python3
"""Card the tree of life — the recognizable organisms and the backbone of the tree.

Matt: "Keep expanding the corpus. Academics first." NCBI Taxonomy holds 2.8M taxa; carding all of it
would swamp the corpus with obscure microbial STRAINS. The gate stays: RECOGNIZABLE life only. Three
nets, chosen by CONCORDANCE_TAXON_NET (default `backbone`):

  common   — only taxa with a COMMON NAME (lion, human, E. coli), ~38k. The original set.
  backbone — common names PLUS every named GROUP above species (genus, family, order, class, phylum,
             kingdom, …), ~159k. The tree's skeleton — every entry a real named clade a person would
             search (Panthera, Felidae, Carnivora). No strains. (Quality-first, ~838k corpus.)
  full     — backbone PLUS every SPECIES/subspecies in the VISIBLE kingdoms (animals=Metazoa,
             plants=Viridiplantae, fungi=Fungi), ~1.75M. Excludes bacteria/archaea/viruses/microbial
             protist species — the "swamp" Matt warned of stays out. (Toward the 3M horizon.)

Conduit, not source: each card is a real NCBI taxon (attributed, generated=False). Nested under a
life-of-earth spine → the created order → the Floor. Card file gitignored (generated from the HD);
spine git-tracked. Re-runnable. Card ids/shape are STABLE across nets — widening the net only ADDS.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_taxonomy.py
    CONCORDANCE_TAXON_NET=full python tools/card_taxonomy.py     # the species too
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CREATED_ORDER = "card_k_spine_created_order"
SPINE = "card_spine_taxonomy"
_slug = re.compile(r"[^a-z0-9]+")
_COMMON = ("common name", "genbank common name")

# The visible kingdoms — the recognizable organisms (NCBI taxids).
_VISIBLE_ROOTS = {33208: "Metazoa (animals)", 33090: "Viridiplantae (plants)", 4751: "Fungi"}
# Ranks that are NOT a named group above species — the noise a backbone net must exclude.
_NONBACKBONE = {"species", "subspecies", "varietas", "forma", "subvariety", "form", "no rank",
                "strain", "isolate", "serotype", "serogroup", "biotype", "genotype", "morph",
                "pathogroup", "forma specialis", "clade"}
# Species-level ranks the `full` net admits (only under a visible kingdom).
_SPECIESISH = {"species", "subspecies", "varietas", "forma"}


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _conn() -> sqlite3.Connection:
    dbs = list(_base().glob("ncbi_taxonomy/*.db"))
    if not dbs:
        raise FileNotFoundError("no taxonomy db under the source base")
    return sqlite3.connect(f"file:{dbs[0]}?mode=ro", uri=True)


def main() -> int:
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    spine = {
        "id": SPINE, "kind": "reference", "title": "The tree of life — the recognizable organisms",
        "body": ("The named kinds and the backbone of the tree — every genus, family, order and higher "
                 "group, the recognizable organisms and the creatures we know by common name — each with "
                 "its scientific name, rank and place in the tree of life. A spine of the created order "
                 "at the scale of the living kinds (Genesis 1: after their kind)."),
        "source": {"label": "NCBI Taxonomy (public domain)", "url": "", "domain": "biology", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["taxonomy", "life", "organisms", "biology", "created order", "spine"],
        "subject": "the tree of life",
        "connections": [{"to_card_id": CREATED_ORDER, "relationship": "part_of",
                         "evidence": "the living kinds, a spine of the created order"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "taxonomy_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n", encoding="utf-8")

    net = os.environ.get("CONCORDANCE_TAXON_NET", "backbone").strip().lower() or "backbone"
    if net not in ("common", "backbone", "full"):
        print(f"unknown CONCORDANCE_TAXON_NET={net!r} (use common|backbone|full)", file=sys.stderr)
        return 2

    c = _conn()
    cur = c.cursor()
    # common names by taxid
    common: dict = {}
    for taxid, name in cur.execute(
            f"select taxid,name from altnames where name_class in {_COMMON}"):
        common.setdefault(taxid, [])
        if name not in common[taxid]:
            common[taxid].append(name)

    # For `full` we must know each species' kingdom — build the parent+rank maps once and
    # memoize the walk to a visible root (animals/plants/fungi). backbone/common need neither.
    parent_of: dict = {}
    rank_of: dict = {}
    if net == "full":
        for taxid, rk, par in c.execute("select taxid, rank, parent from taxa"):
            parent_of[taxid] = par
            rank_of[taxid] = rk
    _vis_memo: dict = {}

    def _under_visible(t) -> bool:
        seen = []
        while t and t not in _vis_memo:
            if t in _VISIBLE_ROOTS:
                for s in seen:
                    _vis_memo[s] = True
                return True
            seen.append(t)
            nt = parent_of.get(t)
            if nt == t or nt is None:
                break
            t = nt
        res = _vis_memo.get(t, False)
        for s in seen:
            _vis_memo[s] = res
        return res

    def _keep(taxid, rk) -> bool:
        if taxid in common:
            return True                              # famous by name — always kept
        if net == "common":
            return False
        rk = rk or "no rank"
        if rk not in _NONBACKBONE:
            return True                              # a named group above species — the backbone
        if net == "full" and rk in _SPECIESISH and _under_visible(taxid):
            return True                              # a recognizable organism in a visible kingdom
        return False

    # every taxon, with its parent's scientific name for a little lineage; kept per the net
    q = c.cursor()
    rows = q.execute(
        """select t.taxid, t.sci_name, t.rank, p.sci_name
           from taxa t left join taxa p on p.taxid = t.parent""")
    n = 0
    tmp = out / "taxonomy_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for taxid, sci, rank, parent_sci in rows:
            if not _keep(taxid, rank):
                continue
            names = common.get(taxid, [])
            primary = names[0] if names else sci
            rank = (rank or "taxon").replace("_", " ")
            # a named group with no common name reads as its scientific name alone — no "X (X)"
            head = f"{primary} ({sci})" if names else sci
            title = f"{sci} — {primary}" if names else sci
            body = (f"{head} — a {rank}."
                    + (f" In the tree of life under {parent_sci}." if parent_sci else "")
                    + (f" Also known as: {', '.join(names[:6])}." if len(names) > 1 else ""))
            card = {
                "id": f"card_src_taxon_{taxid}", "kind": "reference",
                "title": title[:180], "body": body,
                "source": {"label": "NCBI Taxonomy (public domain)", "url": f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={taxid}",
                           "domain": "biology", "authority_tier": "reference"},
                "shelf": "taxonomy", "box": "source",
                "bands": [str(sci).lower(), rank, "organism", "life", "biology"]
                         + [nm.lower() for nm in names[:6]],
                "subject": sci,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": f"a {rank} in the tree of life"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"taxid": taxid, "sci_name": sci, "rank": rank, "common_names": names,
                          "parent": parent_sci},
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "taxonomy_cards.jsonl")
    print(f"[net={net}] carded {n:,} taxa -> data/taxonomy_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
