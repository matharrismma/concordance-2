#!/usr/bin/env python3
"""Gather the CLOUD OF WITNESSES — the fathers, reformers, and founders since the church of Acts 2, in
their own public-domain words (Matt, 2026-08-30: "all texts from denomination or religious founders
since the church of Acts 2"). A curated manifest run through tools/gather_witness.py (idempotent,
strict-PD, verbatim). Extends the seed (Ellen G. White's Steps to Christ) toward the whole cloud.

THE PD TRAP, held explicitly: `pub_year` below is the PD EDITION / TRANSLATION year (pre-1929), NOT the
author's death — a MODERN translation of Augustine is copyrighted even though Augustine is not. Every
source is a pre-1929 public-domain edition: CCEL's clean caches of the classic Beveridge / Dods / Pusey
translations and Schaff's ANF/NPNF, and Project Gutenberg (whose license envelope gather_witness strips).
Each URL was verified reachable + plaintext before it was added here.

    PYTHONPATH=src python tools/gather_founders.py --check   # counts + samples, writes nothing
    PYTHONPATH=src python tools/gather_founders.py           # gather (append to data/witnesses.jsonl)

Verbatim in, verbatim out. Net-grow, never overwrite. Nothing generated; nothing imitated.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATHER = ROOT / "tools" / "gather_witness.py"

# (witness, work, PD-edition pub_year, plaintext source url). Witness names match mentors.py so the
# named "way of seeing" and the gathered "own words" connect. Fathers, reformers, a founder, Bunyan.
MANIFEST = [
    ("Augustine", "Confessions", 1876,
     "https://ccel.org/ccel/a/augustine/confessions/cache/confessions.txt"),
    ("Athanasius", "On the Incarnation of the Word", 1892,
     "https://ccel.org/ccel/a/athanasius/incarnation/cache/incarnation.txt"),
    ("John Chrysostom", "Homilies on the Gospel of Matthew", 1888,
     "https://ccel.org/ccel/s/schaff/npnf110/cache/npnf110.txt"),
    ("Thomas Aquinas", "Summa Theologica (Part I)", 1920,
     "https://www.gutenberg.org/cache/epub/17611/pg17611.txt"),
    # (Luther pending: Gutenberg 50051 is NOT Bondage of the Will — the --check caught a mislabeled
    #  car novel there. Add a verified PD Luther source before gathering him — a gap stays a gap.)
    ("John Calvin", "Institutes of the Christian Religion", 1845,
     "https://ccel.org/ccel/c/calvin/institutes/cache/institutes.txt"),
    ("John Wesley", "Sermons", 1872,
     "https://ccel.org/ccel/w/wesley/sermons/cache/sermons.txt"),
    ("John Bunyan", "The Pilgrim's Progress", 1678,
     "https://www.gutenberg.org/cache/epub/131/pg131.txt"),
]


def main() -> int:
    check = "--check" in sys.argv[1:]
    total_ran = 0
    for witness, work, year, url in MANIFEST:
        args = [sys.executable, str(GATHER), "--witness", witness, "--work", work,
                "--pub-year", str(year), "--source", url, "--url", url]
        if check:
            args.append("--check")
        print("== %s — %s ==" % (witness, work), flush=True)
        rc = subprocess.run(args, cwd=str(ROOT)).returncode
        if rc not in (0,):
            print("   (non-zero exit %d — see message above; continuing)" % rc, flush=True)
        total_ran += 1
    print("\ndone: %d works %s" % (total_ran, "checked" if check else "gathered"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
