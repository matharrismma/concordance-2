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
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.parse
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
    # the WAYBILL (two-tier distribution): every held book carries its origin URL and the
    # sha256 of the exact bytes fetched, so any copy can be re-verified and re-fetched from
    # what the drive HOLDS. Idempotent column adds for stores minted before the waybill.
    for col in ("url text", "sha256 text"):
        try:
            c.execute(f"alter table books add column {col}")
        except sqlite3.OperationalError:
            pass                                        # already present
    c.commit()
    return c


def _fetch(gid: int) -> tuple[bytes, str] | None:
    """The bytes AND the exact mirror URL they came from — the waybill needs both."""
    for url in (f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
                f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
                f"https://www.gutenberg.org/files/{gid}/{gid}.txt"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    data = r.read()
                    if data and len(data) > 200:
                        return data, url
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
        got = _fetch(gid)
        if not got:
            print(f"  {gid}: not found"); continue
        data, url = got
        text = data.decode("utf-8", errors="replace")
        gz = gzip.compress(data, 6)
        digest = hashlib.sha256(data).hexdigest()
        c.execute("insert or replace into books (id,title,raw_bytes,gz,stored_at,url,sha256) "
                  "values (?,?,?,?,?,?,?)",
                  (gid, _title(text), len(data), gz,
                   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), url, digest))
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


def topic_ids(query: str, pages: int = 2) -> list[int]:
    """Mine Gutenberg ids for a topic via the Gutendex catalog (any language) — the
    want-list builder for the technical-first drive fill. Popularity-ordered."""
    ids: list[int] = []
    # topic= matches SUBJECTS and BOOKSHELVES (where the technical canon is filed);
    # search= only matches titles/authors and misses most of it
    url = "https://gutendex.com/books?topic=" + urllib.parse.quote(query)
    for _ in range(max(1, pages)):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                page = json.load(r)
        except Exception as e:  # noqa: BLE001
            print(f"  gutendex: {e}"); break
        ids.extend(int(b["id"]) for b in page.get("results", []) if b.get("id"))
        url = page.get("next") or ""
        if not url:
            break
        time.sleep(1.0)                                # polite to the catalog too
    return ids


def main() -> int:
    a = sys.argv[1:]
    if "--stats" in a:
        stats(); return 0
    if "--ids" in a:
        ids = [int(x) for x in a[a.index("--ids") + 1].split(",") if x.strip().isdigit()]
    elif "--topic" in a:
        ids = topic_ids(a[a.index("--topic") + 1])
        print(f"  topic matched {len(ids)} books")
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
