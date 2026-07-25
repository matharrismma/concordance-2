#!/usr/bin/env python3
"""Fill the Great Books gap — card the Project Gutenberg catalogue. The card maps to the source.

Matt, 2026-07-25: "Look for the most obvious gaps and begin finding source material to store and
creating cards. The hard drive can hold the source. The cards have a map to the source … which can
be the link." The corpus had only ~1,420 'classics'; Project Gutenberg holds ~77,700 public-domain
books. The full catalogue is now STORED on the HD (00_source/gutenberg/pg_catalog.csv); this mints
one lightweight STUB card per book — title, author, subjects, language — whose link
(gutenberg.org/ebooks/<id>) IS the map to the full text. The hare: a light card that points to heavy
source, fetched only when wanted.

Conduit, not source: each card is a real catalogue row, attributed, generated=False. Nested under a
Great Books spine → the Floor. Card file gitignored; spine git-tracked. Re-runnable (re-download the
catalogue to grow).

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_gutenberg.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_gutenberg"
_slug = re.compile(r"[^a-z0-9]+")
_STOP = {"the", "of", "and", "a", "an", "to", "in", "on", "or", "by", "with", "for", "de", "la"}


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _words(s, k=6):
    return [w for w in _slug.sub(" ", str(s or "").lower()).split() if w not in _STOP and len(w) > 2][:k]


def _first_author(authors: str) -> str:
    a = (authors or "").split(";")[0].strip()
    a = re.sub(r",\s*\d{3,4}\??\s*-\s*\d{0,4}\??\s*$", "", a).strip()  # drop trailing (birth-death)
    if "," in a:
        last, _, first = a.partition(",")
        return f"{first.strip()} {last.strip()}".strip()
    return a


def main() -> int:
    src = _base() / "gutenberg" / "pg_catalog.csv"
    if not src.exists():
        print(f"catalogue not found: {src}"); return 1
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    spine = {
        "id": SPINE, "kind": "reference", "title": "The Great Books — Project Gutenberg",
        "body": ("The public-domain library of the world: some 77,000 books whose full text is a click "
                 "away. Each card is a map to the source — the catalogue is held on the drive, the text "
                 "is fetched when wanted. A spine of the Floor of Discovery at the scale of the written word."),
        "source": {"label": "Project Gutenberg (public domain)", "url": "https://www.gutenberg.org/",
                   "domain": "literature", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["gutenberg", "books", "literature", "classics", "public domain", "spine"],
        "subject": "the great books",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the written word, a spine of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "gutenberg_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n", encoding="utf-8")

    n = 0
    tmp = out / "gutenberg_cards.jsonl.tmp"
    with src.open(encoding="utf-8") as fin, tmp.open("w", encoding="utf-8") as f:
        for row in csv.DictReader(fin):
            if row.get("Type") != "Text":
                continue
            gid = (row.get("Text#") or "").strip()
            if not gid.isdigit():
                continue
            title = (row.get("Title") or "").replace("\n", " ").strip()
            authors = (row.get("Authors") or "").strip()
            author = _first_author(authors)
            lang = (row.get("Language") or "").strip()
            subjects = (row.get("Subjects") or "").strip()
            url = f"https://www.gutenberg.org/ebooks/{gid}"
            body = (f"{title}" + (f", by {author}" if author else "")
                    + (f" (in {lang})" if lang and lang != "en" else "") + "."
                    + (f" Subjects: {subjects}." if subjects else "")
                    + f" Read the full text (public domain): {url}")
            card = {
                "id": f"card_src_book_{gid}", "kind": "reference",
                "title": (f"{title} — {author}" if author else title)[:180], "body": body[:1200],
                "source": {"label": "Project Gutenberg (public domain)", "url": url,
                           "domain": "literature", "authority_tier": "reference"},
                "shelf": "gutenberg", "box": "source",
                "bands": (_words(title) + _words(author, 3) + _words(subjects, 6)
                          + [lang.lower(), "book", "literature", "gutenberg"]),
                "subject": title,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": "a public-domain book of the great library"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"gutenberg_id": int(gid), "authors": authors, "language": lang,
                          "subjects": subjects, "loc": (row.get("LoCC") or "").strip(),
                          "bookshelves": (row.get("Bookshelves") or "").strip(),
                          "issued": (row.get("Issued") or "").strip(), "text_url": url,
                          "hd_source": "00_source/gutenberg/pg_catalog.csv"},
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "gutenberg_cards.jsonl")
    print(f"carded {n:,} Great Books (stub -> link) -> data/gutenberg_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
