#!/usr/bin/env python3
"""Front-load the THESAURUS — one compact, memory-mapped index built once from WordNet.

The dictionary cards already ARE the Dictionary & Thesaurus reference (card_src_word_*, the
`card_spine_words` spine): each carries its synonyms in the body. What was missing is the thesaurus
as a FIRST-CLASS RELATION the engine can use to CONNECT related words and SHARPEN RECALL — a query
for "automobile" reaching material that only says "car".

Wiring 149k dictionary cards' synonym edges into the RESIDENT graph would fight the lazy-RAM freeze
(dictionary is a frozen shelf; its connections stay resident). So the thesaurus rides its OWN small
SQLite file instead — memory-mapped and read-only, exactly like the corpus shards: near-zero RAM,
works OFFLINE on any device, front-loaded once here.

Symmetric by construction: every lemma in a WordNet synset is a mutual synonym of the others, so the
map is built both ways (A<->B), not just from the headword row. Hypernyms are kept as `broader`
(the IS-A links — "connect the dots" upward). GATHER, not author: every pair comes from WordNet.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/build_thesaurus.py
    python tools/build_thesaurus.py --check     # counts + a few samples, writes nothing
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _wordnet() -> sqlite3.Connection:
    dbs = list(_base().glob("wordnet/*.db"))
    if not dbs:
        raise FileNotFoundError("no wordnet db under the source base")
    return sqlite3.connect(f"file:{dbs[0]}?mode=ro", uri=True)


def _norm(w: str) -> str:
    return " ".join(str(w or "").strip().lower().split())


def build() -> dict:
    """word_lc -> {'syn': sorted[str], 'broader': sorted[str]} — symmetric synonyms, IS-A broaders."""
    syn: dict = defaultdict(set)
    broader: dict = defaultdict(set)
    c = _wordnet()
    for lemma, data in c.execute("select lemma, data from senses"):
        try:
            senses = json.loads(data)
        except (ValueError, TypeError):
            continue
        if not isinstance(senses, list):
            continue
        head = _norm(lemma)
        if not head:
            continue
        for s in senses:
            if not isinstance(s, dict):
                continue
            syns = [_norm(x) for x in (s.get("synonyms") or []) if _norm(x)]
            group = {head, *syns}
            for w in group:                       # symmetric: each member synonymous with the rest
                syn[w] |= (group - {w})
            for h in (s.get("hypernyms") or []):
                hn = _norm(h)
                if hn and hn != head:
                    broader[head].add(hn)
    out: dict = {}
    for w in set(syn) | set(broader):
        out[w] = {"syn": sorted(syn.get(w, ())), "broader": sorted(broader.get(w, ()))}
    return out


def write_db(rows: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    db = sqlite3.connect(str(path))
    db.executescript(
        "pragma journal_mode=off; pragma synchronous=off;"
        "create table thes (word text primary key, syn text, broader text);")
    db.executemany(
        "insert or ignore into thes values (?,?,?)",
        ((w, json.dumps(d["syn"], ensure_ascii=False), json.dumps(d["broader"], ensure_ascii=False))
         for w, d in rows.items()))
    db.commit()
    db.execute("vacuum")
    db.close()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    rows = build()
    n_syn = sum(1 for d in rows.values() if d["syn"])
    n_br = sum(1 for d in rows.values() if d["broader"])
    print(f"thesaurus: {len(rows):,} words  ({n_syn:,} with synonyms, {n_br:,} with broader terms)")
    for w in ("car", "happy", "run", "lion"):
        d = rows.get(w)
        if d:
            print(f"  {w:8s} syn={d['syn'][:6]}  broader={d['broader'][:4]}")
    if "--check" in sys.argv:
        return 0
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    out = (Path(data) if data else Path("data")) / "thesaurus.db"
    write_db(rows, out)
    print(f"wrote {out}  ({out.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
