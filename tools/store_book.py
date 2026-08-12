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
    # The ARK anchor — where NEW acquisitions land. NEVER a mirror/backup target: the old
    # default (D:/nh-backup/mirror/...) was owned by the nightly "NH Substrate Backup" task,
    # whose delete-sync WIPED 497 stored books on 2026-08-05. A mirror target holds only what
    # its source holds; new content anchors in a directory nothing else considers authoritative.
    b = os.environ.get("CONCORDANCE_ARK_BASE", "").strip()
    return Path(b) if b else Path("D:/NarrowHighway-Sources")


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


# ── the archive.org side of the storekeeper ──────────────────────────────────────────────────
# US federal publications (USDA bulletins, military field manuals, NIST/USGS pubs) are public
# domain under 17 USC §105. Same ark, same waybill discipline, its own store beside gutenberg.

def _ia_ctx():
    """Python 3.13+ turns on VERIFY_X509_STRICT, which rejects archive.org's CA ("Basic
    Constraints not marked critical"). Chain and hostname verification stay ON — only the
    new strictness bit is cleared, for the Archive's chain specifically."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def _ia_db() -> sqlite3.Connection:
    d = _base() / "archive_org"
    d.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(d / "texts.db"), timeout=60)
    c.execute("pragma busy_timeout=60000")             # docs and docs_pd share this file — a
    c.execute("create table if not exists docs (identifier text primary key, title text, "  # concurrent
              "query text, raw_bytes integer, gz blob, stored_at text, url text, sha256 text)")  # writer
    c.commit()                                         # waits for the lock, it does not fail
    return c


def ia_search(query: str, rows: int = 200) -> list:
    """[(identifier, title)] from the archive.org advanced-search API, texts only."""
    url = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(query) +
           "&fl%5B%5D=identifier&fl%5B%5D=title" +
           f"&rows={rows}&page=1&output=json&sort%5B%5D=downloads+desc")
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30, context=_ia_ctx()) as r:
        docs = json.load(r).get("response", {}).get("docs", [])
    return [(d["identifier"], str(d.get("title", ""))[:200]) for d in docs if d.get("identifier")]


def _ia_fetch_text(ident: str) -> tuple[bytes, str] | None:
    """The item's plain-text derivative and its exact URL — waybill needs both."""
    req = urllib.request.Request(f"https://archive.org/metadata/{ident}",
                                 headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30, context=_ia_ctx()) as r:
        meta = json.load(r)
    name = next((f["name"] for f in meta.get("files", [])
                 if str(f.get("name", "")).endswith("_djvu.txt")), None)
    if not name:
        return None
    url = f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=60, context=_ia_ctx()) as r:
        data = r.read()
    return (data, url) if data and len(data) > 500 else None


def ia_store(query: str, limit: int = 200, delay: float = 2.0) -> int:
    c = _ia_db()
    have = {r[0] for r in c.execute("select identifier from docs")}
    n = 0
    for ident, title in ia_search(query, rows=limit):
        if ident in have:
            print(f"  {ident}: already held"); continue
        try:
            got = _ia_fetch_text(ident)
        except Exception as e:  # noqa: BLE001 — item without a text derivative, move on
            print(f"  {ident}: fetch failed ({e})"); continue
        if not got:
            print(f"  {ident}: no text derivative"); continue
        data, url = got
        gz = gzip.compress(data, 6)
        c.execute("insert or replace into docs values (?,?,?,?,?,?,?,?)",
                  (ident, title, query, len(data), gz,
                   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   url, hashlib.sha256(data).hexdigest()))
        c.commit()
        n += 1
        print(f"  {ident}: stored {len(data):>9,}B -> {len(gz):>9,}B gz  {title[:48]}")
        time.sleep(delay)                              # polite to the Archive
    c.close()
    return n


# ── the age-PD side: pre-1929 COMMERCIAL books (handyman encyclopedias, trade manuals,
# ancient technologies). These are public domain by copyright EXPIRY, not by 17 USC 105.
# Because the basis differs, they anchor in a SEPARATE table (docs_pd) with the PD basis
# recorded per row — never blurred with the federal shelf. PD is VERIFIED at acquisition:
# archive.org's own NOT_IN_COPYRIGHT determination, or a conservative pre-1929 age ceiling;
# a restrictive (CC/other) licenseurl disqualifies. Strict PD-only, and the trail says why.

_PD_YEAR_CEILING = 1928       # unambiguously PD in the US as of 2026 (1928 works PD since 2024)


def _ia_meta(ident: str) -> dict:
    req = urllib.request.Request(f"https://archive.org/metadata/{ident}",
                                 headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30, context=_ia_ctx()) as r:
        return json.load(r)


def _one(v) -> str:
    """archive.org metadata values are sometimes a list — take the first, as a string."""
    if isinstance(v, list):
        v = v[0] if v else ""
    return str(v or "")


def _pd_decision(meta: dict) -> tuple[bool, str, str]:
    """Conservative, auditable public-domain gate. Returns (ok, year, basis). Default DENY."""
    import re as _re
    md = meta.get("metadata", {})
    status = _one(md.get("possible-copyright-status")).upper()
    lic = _one(md.get("licenseurl")).lower()
    year = ""
    for key in ("year", "date", "publicdate"):
        m = _re.search(r"\b(1[5-9]\d\d|20\d\d)\b", _one(md.get(key)))
        if m:
            year = m.group(1); break
    if "NOT_IN_COPYRIGHT" in status:
        return True, year, "archive.org copyright status: NOT_IN_COPYRIGHT"
    # a license URL that is not itself a public-domain mark means the item is *licensed*
    # (e.g. CC-BY) rather than public domain — we ship PD only, so it is disqualified.
    if lic and not any(k in lic for k in ("publicdomain", "/mark/", "cc0", "/zero/")):
        return False, year, f"restrictive license ({lic}) — not shipped"
    if "IN_COPYRIGHT" in status:                       # explicit copyright, no override
        return False, year, "archive.org copyright status: IN_COPYRIGHT"
    if year and year.isdigit() and int(year) <= _PD_YEAR_CEILING:
        return True, year, f"public domain by copyright expiry (published {year}, pre-1929)"
    return False, year, "no public-domain basis established"


def _ia_pd_db() -> sqlite3.Connection:
    d = _base() / "archive_org"
    d.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(d / "texts.db"), timeout=60)
    c.execute("pragma busy_timeout=60000")             # shares texts.db with docs — wait, don't fail
    c.execute("create table if not exists docs_pd (identifier text primary key, title text, "
              "query text, raw_bytes integer, gz blob, stored_at text, url text, sha256 text, "
              "pd_year text, pd_basis text)")
    c.commit()
    return c


def ia_store_pd(query: str, limit: int = 200, delay: float = 2.0) -> int:
    """Store only what we can VERIFY is public domain, recording the basis per row."""
    c = _ia_pd_db()
    have = {r[0] for r in c.execute("select identifier from docs_pd")}
    n = skipped = 0
    for ident, title in ia_search(query, rows=limit):
        if ident in have:
            print(f"  {ident}: already held"); continue
        try:
            meta = _ia_meta(ident)
        except Exception as e:  # noqa: BLE001
            print(f"  {ident}: metadata failed ({e})"); continue
        ok, year, basis = _pd_decision(meta)
        if not ok:
            skipped += 1
            print(f"  {ident}: SKIP not-PD — {basis}"); time.sleep(delay); continue
        name = next((f["name"] for f in meta.get("files", [])
                     if str(f.get("name", "")).endswith("_djvu.txt")), None)
        if not name:
            print(f"  {ident}: no text derivative"); continue
        url = f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=60, context=_ia_ctx()) as r:
                data = r.read()
        except Exception as e:  # noqa: BLE001
            print(f"  {ident}: text fetch failed ({e})"); continue
        if not data or len(data) <= 500:
            print(f"  {ident}: text too small"); continue
        gz = gzip.compress(data, 6)
        c.execute("insert or replace into docs_pd values (?,?,?,?,?,?,?,?,?,?)",
                  (ident, title, query, len(data), gz,
                   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   url, hashlib.sha256(data).hexdigest(), year, basis))
        c.commit()
        n += 1
        print(f"  {ident}: stored {len(data):>9,}B -> {len(gz):>9,}B gz  [{year or '?'}] {title[:44]}")
        time.sleep(delay)                              # polite to the Archive
    c.close()
    print(f"  (PD gate: {n} stored, {skipped} skipped as not-verifiably-PD)")
    return n


def main() -> int:
    # Titles carry accents/diacritics (French trade manuals, Latin, etc.). When stdout is a
    # redirected file, Windows defaults to cp1252, which cannot encode '́' and friends — a
    # bare print() then raises UnicodeEncodeError and kills a long acquisition mid-run, truncating
    # every query at its first foreign title. Force UTF-8 with replacement so the log is cosmetic,
    # never fatal. (Progress lives in the DB, not the print, but the print must not crash the run.)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 — older/odd streams without reconfigure; carry on
            pass
    a = sys.argv[1:]
    if "--ia-query" in a:
        limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 200
        n = ia_store(a[a.index("--ia-query") + 1], limit=limit)
        print(f"stored {n} archive.org documents"); return 0
    if "--ia-pd-query" in a:
        limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 200
        n = ia_store_pd(a[a.index("--ia-pd-query") + 1], limit=limit)
        print(f"stored {n} age-PD archive.org documents"); return 0
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
