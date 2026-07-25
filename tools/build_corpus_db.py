#!/usr/bin/env python3
"""Compile the corpus into small SQLite FTS shards — multiple files, unfreeze as needed.

Matt, 2026-07-25: "Free up space without adding. Small, for a variety of devices … we need them in
MULTIPLE FILES so we can unfreeze as needed … refreeze and rebalance the loads." This loads the same
merged+bridged corpus once and writes ONE compact SQLite FTS5 file per shard (core / word / science /
world / dictionary / books). A device unfreezes only the shards it needs (concordance.corpus_db);
frozen shards cost only disk. Runtime query RAM is tens of MB (memory-mapped), vs ~2.7 GB in-RAM.

    PYTHONPATH=src python tools/build_corpus_db.py                 # -> data/shards/*.db + manifest.json
    PYTHONPATH=src python tools/build_corpus_db.py --out D:/nh/shards
    PYTHONPATH=src python tools/build_corpus_db.py --single        # one data/corpus.db (everything)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_DDL = ("pragma journal_mode=off; pragma synchronous=off;"
        "create table cards (id text primary key, shelf text, surface text, title text, json text);"
        "create virtual table fts using fts5(id unindexed, text, tokenize='porter unicode61');")


def _new(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    c = sqlite3.connect(str(path))
    c.executescript(_DDL)
    return c


def _write(db: sqlite3.Connection, cid: str, c: dict, text: str):
    db.execute("insert or ignore into cards values (?,?,?,?,?)",
               (cid, c.get("shelf"), c.get("surface"), c.get("title"),
                json.dumps(c, ensure_ascii=False, separators=(",", ":"))))
    db.execute("insert into fts values (?,?)", (cid, text))


def _finish(db: sqlite3.Connection):
    db.commit()
    db.execute("insert into fts(fts) values('optimize')")
    db.commit()
    db.execute("vacuum")
    db.close()


def main() -> int:
    from concordance import corpus, corpus_db
    single = "--single" in sys.argv
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else (
        Path("data/corpus.db") if single else Path("data/shards"))

    t0 = time.time()
    print("loading the full merged+bridged corpus (heavy, one-time) …")
    cards = corpus.load_cards()
    print(f"  {len(cards):,} cards in {time.time()-t0:.0f}s")

    if single:
        out.parent.mkdir(parents=True, exist_ok=True)
        db = _new(out)
        for cid, c in cards.items():
            _write(db, cid, c, corpus._card_text(c))
        _finish(db)
        print(f"BUILT {out}  |  {len(cards):,} cards  |  {out.stat().st_size/1e6:,.1f} MB")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    conns: dict = {}
    counts: dict = {}
    shelves_of: dict = {}
    for cid, c in cards.items():
        name = corpus_db.shard_of(c.get("shelf"))
        if name not in conns:
            conns[name] = _new(out / f"{name}.db"); counts[name] = 0; shelves_of[name] = set()
        _write(conns[name], cid, c, corpus._card_text(c))
        counts[name] += 1
        shelves_of[name].add(c.get("shelf") or "?")
    manifest = {"shards": {}, "mode": "shards", "total": len(cards)}
    for name, db in conns.items():
        _finish(db)
        size = (out / f"{name}.db").stat().st_size
        manifest["shards"][name] = {"file": f"{name}.db", "cards": counts[name],
                                    "mb": round(size / 1e6, 1), "core": (name == corpus_db.CORE),
                                    "shelves": sorted(shelves_of[name])}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nBUILT {len(conns)} shards -> {out}/  ({manifest['total']:,} cards)")
    for name, info in sorted(manifest["shards"].items(), key=lambda kv: -kv[1]["mb"]):
        tag = " (core, always thawed)" if info["core"] else ""
        print(f"  {name:12s} {info['cards']:>8,} cards  {info['mb']:>7.1f} MB{tag}")
    core_mb = manifest["shards"].get(corpus_db.CORE, {}).get("mb", 0)
    print(f"\nA minimal device thaws only 'core' (~{core_mb} MB); it unfreezes more as needed and "
          f"refreezes to rebalance. The whole ark is the sum, carried in the pocket.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
