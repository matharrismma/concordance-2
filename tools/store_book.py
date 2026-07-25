#!/usr/bin/env python3
"""An efficient method for storing PD books on the hard drive — compressed + indexed.

Matt, 2026-07-25: "We want an efficient method of storing PD books." The Gutenberg CARDS already map
to the source (the link); this holds the full TEXT sovereignly, so the ark carries the books even off
the grid. The method: one indexed SQLite store (00_source/gutenberg/texts.db) with per-book GZIP blobs
— compact (~3-4x), single file, O(1) lookup by id, idempotent (skip what's held). Fetch on demand or
seed a set; a full 77k crawl runs slowly over time, polite to Project Gutenberg's servers.

    python tools/store_book.py --seed              # store a set of famous books
    python tools/store_book.py --ids 1342,84,11    # store specific Gutenberg ids
    python tools/store_book.py --stats             # what is held, and how compact
"""
from __future__ import annotations

import gzip
import os
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

_UA = "NarrowHighway/1.0 (sovereign PD-book archive; contact mesh@narrowhighway.org)"
# A seed of the famous public-domain books — enough to prove the store and carry the canon.
_SEED = [1342, 84, 1661, 11, 2701, 1400, 98, 74, 76, 345, 1260, 158, 205, 46, 174, 1727, 6130,
         768, 1952, 5200, 100, 10, 1497, 3207, 3300, 2542, 25344, 244, 1080, 2600]


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _db() -> sqlite3.Connection:
    d = _base() / "gutenberg"
    d.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(d / "texts.db"))
    c.execute("create table if not exists books (id integer primary key, title text, "
              "raw_bytes integer, gz blob, stored_at text)")
    c.commit()
    return c


def _fetch(gid: int) -> bytes | None:
    for url in (f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
                f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
                f"https://www.gutenberg.org/files/{gid}/{gid}.txt"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    data = r.read()
                    if data and len(data) > 200:
                        return data
        except Exception:  # noqa: BLE001 — try the next mirror form
            continue
    return None


def _title(text: str) -> str:
    for line in text.splitlines()[:60]:
        if line.strip().lower().startswith("title:"):
            return line.split(":", 1)[1].strip()[:200]
    return ""


def store(ids, delay: float = 1.5) -> int:
    c = _db()
    have = {r[0] for r in c.execute("select id from books")}
    n = 0
    for gid in ids:
        if gid in have:
            print(f"  {gid}: already held"); continue
        data = _fetch(gid)
        if not data:
            print(f"  {gid}: not found"); continue
        text = data.decode("utf-8", errors="replace")
        gz = gzip.compress(data, 6)
        c.execute("insert or replace into books (id,title,raw_bytes,gz,stored_at) values (?,?,?,?,?)",
                  (gid, _title(text), len(data), gz, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        c.commit()
        n += 1
        print(f"  {gid}: stored {len(data):>9,}B -> {len(gz):>9,}B gz ({len(data)/max(1,len(gz)):.1f}x)  {_title(text)[:48]}")
        time.sleep(delay)                              # polite to Gutenberg
    c.close()
    return n


def read_book(gid: int) -> str | None:
    c = _db()
    row = c.execute("select gz from books where id=?", (gid,)).fetchone()
    c.close()
    return gzip.decompress(row[0]).decode("utf-8", errors="replace") if row else None


def stats():
    c = _db()
    n, raw, gz = c.execute("select count(*), coalesce(sum(raw_bytes),0), coalesce(sum(length(gz)),0) from books").fetchone()
    c.close()
    print(f"held: {n:,} books | raw {raw/1e6:.1f} MB -> gz {gz/1e6:.1f} MB "
          f"({raw/max(1,gz):.1f}x compression)")


def main() -> int:
    a = sys.argv[1:]
    if "--stats" in a:
        stats(); return 0
    if "--ids" in a:
        ids = [int(x) for x in a[a.index("--ids") + 1].split(",") if x.strip().isdigit()]
    elif "--seed" in a:
        ids = _SEED
    else:
        print(__doc__); return 0
    print(f"storing {len(ids)} books to {_base()/'gutenberg'/'texts.db'} …")
    store(ids)
    stats()
    return 0


if __name__ == "__main__":
    sys.exit(main())
