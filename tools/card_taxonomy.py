#!/usr/bin/env python3
"""Card the tree of life — the recognizable organisms. Academics (biology) first.

Matt: "Keep expanding the corpus. Academics first." NCBI Taxonomy holds 2.8M taxa; carding all of it
would swamp the corpus with obscure microbial strains. Mirroring the OEIS-core choice, this cards the
RECOGNIZABLE life — every taxon that has a COMMON NAME (lion → Panthera leo, human → Homo sapiens,
E. coli), ~38,000 organisms — the ones a person would actually search, with their scientific name,
rank, and place in the tree.

Conduit, not source: each card is a real NCBI taxon (attributed, generated=False). Nested under a
life-of-earth spine → the created order → the Floor. Card file gitignored (generated from the HD);
spine git-tracked. Re-runnable.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_taxonomy.py
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
        "body": ("Every creature with a common name — mammals, birds, fish, plants, the microbes we "
                 "know by name — with its scientific name, rank and place in the tree of life. A spine "
                 "of the created order at the scale of the living kinds (Genesis 1: after their kind)."),
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

    c = _conn()
    cur = c.cursor()
    # common names by taxid
    common: dict = {}
    for taxid, name in cur.execute(
            f"select taxid,name from altnames where name_class in {_COMMON}"):
        common.setdefault(taxid, [])
        if name not in common[taxid]:
            common[taxid].append(name)
    # the taxa that have one, with their parent's scientific name for a little lineage
    q = c.cursor()
    rows = q.execute(
        f"""select t.taxid, t.sci_name, t.rank, p.sci_name
            from taxa t left join taxa p on p.taxid = t.parent
            where t.taxid in (select distinct taxid from altnames where name_class in {_COMMON})""")
    n = 0
    tmp = out / "taxonomy_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for taxid, sci, rank, parent_sci in rows:
            names = common.get(taxid, [])
            primary = names[0] if names else sci
            rank = (rank or "taxon").replace("_", " ")
            body = (f"{primary} ({sci}) — a {rank}."
                    + (f" In the tree of life under {parent_sci}." if parent_sci else "")
                    + (f" Also known as: {', '.join(names[:6])}." if len(names) > 1 else ""))
            card = {
                "id": f"card_src_taxon_{taxid}", "kind": "reference",
                "title": f"{sci} — {primary}"[:180], "body": body,
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
    print(f"carded {n:,} organisms (with common names) -> data/taxonomy_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
