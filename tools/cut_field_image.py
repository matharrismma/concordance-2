#!/usr/bin/env python3
"""Cut the offline FIELD LIBRARY image — lever 4 of the ranked program (Matt, 2026-08-05).

Two-tier distribution made physical: cards spread cheap, sources anchor on drives. This cuts a
repeatable, verifiable image from the ark so a family with no internet holds the library:

    gutenberg/texts.db      the held books (full text, gzip blobs, per-book WAYBILL url+sha256)
    archive_org/texts.db    the held US-federal documents (17 USC 105), same waybills
    bible/web.db            the whole Bible, World English Bible translation
    search-index.json       the offline finding layer (every public seed, searchable locally)
    MANIFEST.json           every file's bytes + sha256 — the image's own seal
    verify_image.py         stdlib-only re-hasher: anyone can confirm the copy is unaltered
    README.txt              what this is, how to verify, how to heal

The MANIFEST is the healing map: a damaged copy re-fetches any item from the origin URL in its
waybill and re-verifies against the recorded sha256 — you heal from what you HOLD. Releases land
under D:/NarrowHighway-Releases/field-library/ with an append-only family manifest (the same
first/previous/current policy the site releases use: drift stays chartable).

    python tools/cut_field_image.py            # cut + self-verify
    python tools/cut_field_image.py --check    # list what would be cut, sizes only
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ARK = Path(os.environ.get("CONCORDANCE_ARK_BASE", "").strip() or "D:/NarrowHighway-Sources")
LW = Path(os.environ.get("CONCORDANCE_LW_BASE", "").strip() or "D:/nh-backup/mirror/repo/lw/00_source")
RELEASES = Path(os.environ.get("CONCORDANCE_RELEASES", "").strip() or "D:/NarrowHighway-Releases")
REPO = Path(__file__).resolve().parent.parent

SOURCES = [  # (source path, path inside the image)
    (ARK / "gutenberg" / "texts.db", "gutenberg/texts.db"),
    (ARK / "archive_org" / "texts.db", "archive_org/texts.db"),
    (LW / "web_bible" / "web.db", "bible/web.db"),
    (REPO / "site" / "search-index.json", "search-index.json"),
]

VERIFIER = '''#!/usr/bin/env python3
"""Verify this field-library image against its MANIFEST — standard library only.
    python verify_image.py            # from inside the image directory
"""
import hashlib, json, sys
from pathlib import Path
root = Path(__file__).resolve().parent
man = json.load(open(root / "MANIFEST.json", encoding="utf-8"))
bad = 0
for f in man["files"]:
    p = root / f["path"]
    if not p.is_file():
        print(f"MISSING   {f['path']}"); bad += 1; continue
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != f["sha256"]:
        print(f"ALTERED   {f['path']}"); bad += 1
    else:
        print(f"ok        {f['path']}")
print("VERIFIED: every file matches its seal" if not bad else f"FAILED: {bad} file(s) do not match")
sys.exit(1 if bad else 0)
'''

README = """THE FIELD LIBRARY — an offline keeping (Narrow Highway, narrowhighway.com)

What this is: the full text of {books:,} public-domain books and {docs:,} United States federal
publications (public domain, 17 USC 105), the whole Bible (World English Bible), and an offline
search index — cut from the ark on {date}. No account, no network, no cost. Freely given.

Verify it:   python verify_image.py
             (standard library only; re-hashes every file against MANIFEST.json)

Read a book: the texts live as gzip blobs in SQLite. In Python:
             import sqlite3, gzip
             c = sqlite3.connect("gutenberg/texts.db")
             row = c.execute("select title, gz from books where id=?", (1342,)).fetchone()
             print(row[0]); text = gzip.decompress(row[1]).decode("utf-8", "replace")

Heal it:     every book and document row carries its WAYBILL — the origin url and the sha256 of
             the exact bytes. A damaged item can be re-fetched from its url and re-checked
             against its recorded hash. You heal from what you hold.

The whole library, searchable and served: https://narrowhighway.com — this image is the anchor;
the site is the spread. Psalm 119:105.
"""


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _counts() -> dict:
    import sqlite3
    out = {}
    try:
        c = sqlite3.connect(str(ARK / "gutenberg" / "texts.db"))
        out["gutenberg_books"] = c.execute("select count(*) from books").fetchone()[0]
        c.close()
        c = sqlite3.connect(str(ARK / "archive_org" / "texts.db"))
        out["federal_documents"] = c.execute("select count(*) from docs").fetchone()[0]
        c.close()
    except Exception as e:  # noqa: BLE001
        out["count_error"] = str(e)
    return out


def main() -> int:
    check = "--check" in sys.argv
    missing = [str(src) for src, _rel in SOURCES if not src.is_file()]
    if missing:
        print("REFUSING: source(s) missing — an image cut from a partial ark would ship a hole:")
        for m in missing:
            print("  " + m)
        return 1
    total = sum(src.stat().st_size for src, _rel in SOURCES)
    counts = _counts()
    print(f"image: {len(SOURCES)} files, {total / 1e6:,.0f} MB | " +
          " · ".join(f"{k} {v:,}" for k, v in counts.items() if isinstance(v, int)))
    if check:
        return 0

    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    dest = RELEASES / "field-library" / f"field-library-v1-{stamp}"
    dest.mkdir(parents=True, exist_ok=False)
    files = []
    for src, rel in SOURCES:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        files.append({"path": rel, "bytes": target.stat().st_size, "sha256": _sha(target)})
        print(f"  cut {rel} ({files[-1]['bytes']:,} B)")

    manifest = {
        "image": "field-library", "version": "v1", "stamp": stamp,
        "counts": counts, "files": files,
        "waybills": "per-item origin url + sha256 live INSIDE the two texts.db stores",
        "policy": "append-only family manifest beside the releases; drift stays chartable",
    }
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (dest / "verify_image.py").write_text(VERIFIER, encoding="utf-8")
    (dest / "README.txt").write_text(
        README.format(books=counts.get("gutenberg_books", 0),
                      docs=counts.get("federal_documents", 0),
                      date=stamp[:10]), encoding="utf-8")

    # self-verify: re-hash everything we just wrote, from the copy, before claiming success
    bad = [f["path"] for f in files if _sha(dest / f["path"]) != f["sha256"]]
    if bad:
        print(f"CUT FAILED VERIFICATION: {bad}")
        return 1

    fam = RELEASES / "field-library" / "manifest.json"
    hist = json.loads(fam.read_text(encoding="utf-8")) if fam.exists() else {
        "policy": "append-only; every cut is recorded, none rewritten", "releases": []}
    hist["releases"].append({"stamp": stamp, "dir": dest.name,
                             "bytes": sum(f["bytes"] for f in files),
                             "manifest_sha256": _sha(dest / "MANIFEST.json")})
    fam.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    print(f"CUT + VERIFIED: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
