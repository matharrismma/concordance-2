"""Migrate openbible.info cross-references (CC-BY expansion of the public-domain TSK) into the store.

One bounded download (~2 MB zip) + build (~340k rows, a few seconds). A timeout on the fetch means
it can't hang; --limit caps rows for a quick/test build. Attributed; never engine-authored.
Ported from the 1.0 build_xrefs_index.py.

    python -m tools.migrate_xrefs
    python -m tools.migrate_xrefs --limit 5000     # quick partial build
"""
from __future__ import annotations

import argparse
import io
import sqlite3
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import xrefs  # noqa: E402

URL = "https://a.openbible.info/data/cross-references.zip"

OSIS_ORDER = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam",
    "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov",
    "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos",
    "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph",
    "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb",
    "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
]
OSIS2NUM = {a: i + 1 for i, a in enumerate(OSIS_ORDER)}


def _parse_ref(ref):
    parts = ref.split(".")
    if len(parts) != 3:
        return None
    bn = OSIS2NUM.get(parts[0])
    if bn is None:
        return None
    try:
        return bn, int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _parse_to(tov):
    if "-" in tov:
        lo, hi = tov.split("-", 1)
        a, b = _parse_ref(lo), _parse_ref(hi)
        if a is None:
            return None
        end = b[2] if (b is not None and b[0] == a[0] and b[1] == a[1] and b[2] >= a[2]) else a[2]
        return a[0], a[1], a[2], end
    a = _parse_ref(tov)
    return (a[0], a[1], a[2], a[2]) if a else None


def build(out: Path, limit=None, timeout: int = 60) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    req = urllib.request.Request(URL, headers={"User-Agent": "narrow-highway/xrefs-migrate"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        blob = r.read()
    z = zipfile.ZipFile(io.BytesIO(blob))
    text = z.read(z.namelist()[0]).decode("utf-8", "replace")
    rows, skipped = [], 0
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("From Verse"):
            continue
        cols = line.split("\t")
        if len(cols) < 2:
            skipped += 1
            continue
        frm, to = _parse_ref(cols[0]), _parse_to(cols[1])
        if frm is None or to is None:
            skipped += 1
            continue
        try:
            votes = int(cols[2]) if len(cols) > 2 and cols[2].strip() else 0
        except ValueError:
            votes = 0
        rows.append((frm[0], frm[1], frm[2], to[0], to[1], to[2], to[3], votes))
        if limit and len(rows) >= limit:
            break
    con = sqlite3.connect(str(out))
    cur = con.cursor()
    cur.execute("CREATE TABLE cross_refs (from_book INT, from_chapter INT, from_verse INT, "
                "to_book INT, to_chapter INT, to_verse_start INT, to_verse_end INT, votes INT)")
    cur.execute("CREATE TABLE meta (k TEXT, v TEXT)")
    cur.executemany("INSERT INTO cross_refs VALUES (?,?,?,?,?,?,?,?)", rows)
    cur.execute("CREATE INDEX idx_from ON cross_refs(from_book, from_chapter, from_verse)")
    cur.executemany("INSERT INTO meta VALUES (?,?)",
                    [("source", xrefs.SOURCE), ("license", xrefs.LICENSE),
                     ("attribution", xrefs.ATTRIBUTION), ("n_rows", str(len(rows)))])
    con.commit()
    con.close()
    return {"rows": len(rows), "skipped": skipped,
            "from_verses": len({(r[0], r[1], r[2]) for r in rows})}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Migrate openbible.info cross-references (CC-BY / PD TSK).")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else xrefs._db_path()
    print(build(out, limit=a.limit))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
