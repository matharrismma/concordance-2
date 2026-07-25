#!/usr/bin/env python3
"""Card the OEIS core — the foundational integer sequences. Academics (mathematics) first.

Matt, 2026-07-25: "Keep expanding the corpus. Academics first" → OEIS core subset. The On-Line
Encyclopedia of Integer Sequences holds 396,600 sequences; the LOW A-numbers are its own foundational
entries (A000040 the primes, A000045 Fibonacci, A000108 Catalan, A000041 the partitions, …). This
mints the first N (default 6,000: A000001–A006000) as cards — the mathematically important ones,
without swamping the corpus with the full set.

Conduit, not source: each card is a real OEIS entry (anum, name, terms), attributed, generated=False.
Nested under an OEIS spine → the Floor of Discovery (mathematics is discovered, not authored). The
card file is gitignored (generated from the HD); the spine is git-tracked content. Re-runnable.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_oeis.py
    ... --limit 6000
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_oeis"
_slug = re.compile(r"[^a-z0-9]+")
_STOP = {"the", "of", "and", "a", "n", "with", "for", "number", "numbers", "by", "in", "to"}


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _conn() -> sqlite3.Connection:
    dbs = list(_base().glob("oeis/*.db"))
    if not dbs:
        raise FileNotFoundError("no oeis db under the source base")
    return sqlite3.connect(f"file:{dbs[0]}?mode=ro", uri=True)


def main() -> int:
    limit = 6000
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    spine = {
        "id": SPINE, "kind": "reference", "title": "The integer sequences — the OEIS core",
        "body": ("The foundational integer sequences from the On-Line Encyclopedia of Integer "
                 "Sequences: the primes, Fibonacci, Catalan, the partitions, and thousands more — "
                 "the low-numbered entries the whole of number theory keeps returning to. A spine of "
                 "the Floor of Discovery at the scale of pure number."),
        "source": {"label": "OEIS — On-Line Encyclopedia of Integer Sequences (oeis.org)", "url": "",
                   "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["oeis", "sequences", "integer", "mathematics", "number theory", "spine"],
        "subject": "the integer sequences",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "pure number, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "oeis_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n", encoding="utf-8")

    c = _conn()
    rows = c.execute("select anum,name,terms from sequences order by anum limit ?", (limit,))
    n = 0
    tmp = out / "oeis_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for anum, name, terms in rows:
            terms = str(terms or "").strip().lstrip(",")
            first = terms.split(",")[:24]
            name = str(name or "").strip()
            words = [w for w in _slug.sub(" ", name.lower()).split() if w not in _STOP and len(w) > 2][:8]
            body = f"{name}  First terms: {', '.join(first)}."
            card = {
                "id": f"card_src_oeis_{_sk(anum)}", "kind": "reference",
                "title": f"{anum} — {name}"[:180], "body": body,
                "source": {"label": "OEIS — On-Line Encyclopedia of Integer Sequences (oeis.org)",
                           "url": f"https://oeis.org/{anum}", "domain": "mathematics", "authority_tier": "reference"},
                "shelf": "oeis", "box": "source",
                "bands": [anum.lower(), "sequence", "integer", "oeis", "mathematics"] + words,
                "subject": anum,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": "a foundational integer sequence"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"anum": anum, "name": name, "terms": ",".join(terms.split(",")[:60])},
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "oeis_cards.jsonl")
    print(f"carded {n:,} OEIS core sequences -> data/oeis_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
