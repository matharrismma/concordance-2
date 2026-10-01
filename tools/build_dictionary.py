"""Build the English dictionary DB — Webster's 1913 (public domain) + our supplement.

Mirrors tools/build_thesaurus.py: one read-only SQLite file (data/dictionary_en.db),
memory-mapped like the corpus shards, opt-in (if absent, dictionary.py returns empty and nothing
changes). The 22 MB Webster's source is NEVER committed — it is fetched from its public-domain
mirror at build time (like WordNet for the thesaurus), or read from --source. OUR supplement
(data/dictionary_supplement.jsonl, tracked, tiny) is gathered PD content for terms Webster's 1913
predates — never hand-authored definitions ("gather, don't author"); it is merged as additional
senses and marked with its source, so the reader always sees which is which.

    python tools/build_dictionary.py                # fetch Webster's + merge supplement
    python tools/build_dictionary.py --source webster.json   # from a local copy

Conduit, not author: every definition came from a public-domain dictionary; the row records which.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", ROOT / "data"))
OUT = DATA / "dictionary_en.db"
SUPPLEMENT = DATA / "dictionary_supplement.jsonl"
# Webster's 1913 Unabridged, public domain — a widely-mirrored word->definition JSON.
WEBSTER_URL = "https://raw.githubusercontent.com/matthewreagan/WebstersEnglishDictionary/master/dictionary.json"


def _norm(word: str) -> str:
    return " ".join(str(word or "").strip().lower().split())


def _load_webster(source: str | None) -> dict:
    if source:
        print(f"  reading Webster's from {source}")
        return json.loads(Path(source).read_text(encoding="utf-8"))
    print(f"  fetching Webster's 1913 (public domain) from {WEBSTER_URL}")
    with urllib.request.urlopen(WEBSTER_URL, timeout=120) as r:  # noqa: S310 — fixed PD mirror
        return json.loads(r.read().decode("utf-8"))


def _load_supplement() -> list:
    """Our supplement: gathered PD entries for terms Webster's 1913 predates. Tracked, tiny, grows."""
    if not SUPPLEMENT.exists():
        return []
    out = []
    for line in SUPPLEMENT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        w, d = _norm(row.get("word", "")), str(row.get("definition", "")).strip()
        if w and d:
            out.append((w, d, row.get("source", "supplement")))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="local Webster's JSON (word->definition); default fetches the PD mirror")
    args = ap.parse_args()

    webster = _load_webster(args.source)
    supplement = _load_supplement()
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".db.tmp")
    if tmp.exists():
        tmp.unlink()
    db = sqlite3.connect(tmp)
    db.executescript(
        "PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;"
        "CREATE TABLE entries (word TEXT NOT NULL, definition TEXT NOT NULL, source TEXT NOT NULL);"
    )
    rows = []
    for word, definition in webster.items():
        w, d = _norm(word), str(definition or "").strip()
        if w and d:
            rows.append((w, d, "webster-1913"))
    rows.extend(supplement)
    db.executemany("INSERT INTO entries (word, definition, source) VALUES (?, ?, ?)", rows)
    db.execute("CREATE INDEX idx_word ON entries (word)")
    db.commit()
    n_words = db.execute("SELECT COUNT(DISTINCT word) FROM entries").fetchone()[0]
    n_rows = db.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    db.close()
    if OUT.exists():
        OUT.unlink()
    tmp.rename(OUT)
    print(f"  wrote {OUT}: {n_words} words, {n_rows} senses "
          f"({len(rows) - len(supplement)} Webster's + {len(supplement)} supplement)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
