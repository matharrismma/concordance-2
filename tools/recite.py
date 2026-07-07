#!/usr/bin/env python3
"""Chapter:verse re-citer — restore GENUINE 'cites' edges, cite-fair and mechanical.

The auto-detected book-name co-mentions were demoted to 'references' (they name a book, they
don't cite a passage — see tools/demote_cites.py). This tool creates the real thing: where a
card's own text carries a genuine "Book chapter:verse" reference (e.g. "Acts 19:22"), it links
that card to the referenced book card with relationship_kind 'cites', recording the exact ref.
Nothing is generated or guessed — only refs literally present in the card text become edges.

For each (card, book) with a genuine ref:
  * if a connection between them already exists (a demoted 'references' co-mention), UPGRADE it
    in place to 'cites' + attach the ref(s) — no duplicate edge, id preserved;
  * else CREATE a new 'cites' connection card (deterministic id -> idempotent/re-runnable).

This also un-orphans the ~800 orphan cards that cite a passage but had no edge. Deterministic,
idempotent (a second run changes 0), atomic write, unchanged lines passed through byte-for-byte.

    python tools/recite.py [path/to/cards.jsonl] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "cards.jsonl")

BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
         "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
         "Nehemiah", "Esther", "Job", "Psalms", "Psalm", "Proverbs", "Ecclesiastes",
         "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea",
         "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
         "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
         "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
         "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
         "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"]
_BOOK_ALT = "|".join(re.escape(b) for b in sorted(BOOKS, key=len, reverse=True))
REF_RE = re.compile(r"\b(" + _BOOK_ALT + r")\s+(\d{1,3}):(\d{1,3})(?:[-,]\d{1,3})?\b")
# Psalm/Psalms both map to the "Psalms" book card.
_CANON = {"Psalm": "Psalms"}


def _is_public(c: dict) -> bool:
    return (c.get("visibility") == "public" or c.get("lifecycle_stage") in ("public", "featured"))


def _refs_in(card: dict):
    """Ordered unique 'Book ch:v' refs found in the card's title+body; {book: [refs]}."""
    text = f"{card.get('title', '')}\n{card.get('body', '')}"
    out = {}
    for bk, ch, vs in REF_RE.findall(text):
        book = _CANON.get(bk, bk)
        ref = f"{book} {ch}:{vs}"
        lst = out.setdefault(book, [])
        if ref not in lst:
            lst.append(ref)
    return out


def _edge_id(left: str, right: str) -> str:
    return "card_c_" + hashlib.sha256(f"{left}|{right}|cites".encode()).hexdigest()[:12]


def _new_edge(left: str, left_title: str, right: str, book: str, refs, now: str) -> dict:
    ref_str = "; ".join(refs)
    low = book.lower().replace(" ", "_")
    return {
        "id": _edge_id(left, right), "kind": "connection",
        "title": f"{left_title} cites {book}",
        "body": f"Cites {ref_str} — a chapter:verse reference found in the card text.",
        "source": {"label": "Chapter:verse citation", "url": "", "ref": ref_str,
                   "authority_tier": "engine_derived"},
        "shelf": "connections", "box": f"citation_{low}",
        "bands": ["cites", "chapter_verse", low],
        "connections": [{"to_card_id": right, "relationship": "see_also"}],
        "author": "engine", "created_at": now, "updated_at": now,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "stable",
        "metrics": {"paperclips_count": 0, "helpful_count": 0, "not_helpful_count": 0,
                    "cite_count": 0, "walks_through_count": 0, "flagged_count": 0},
        "extra": {"left_card_id": left, "right_card_id": right, "relationship_kind": "cites",
                  "ref": refs[0], "refs": refs, "bidirectional": False,
                  "explanation": f"Cites {ref_str} (chapter:verse found in the card text)."},
        "witnesses": [],
    }


def _upgrade(edge: dict, book: str, refs, now: str) -> bool:
    """Upgrade an existing edge to 'cites' + attach refs. Return True if it changed."""
    ex = edge.get("extra") or {}
    ref_str = "; ".join(refs)
    already = ex.get("relationship_kind") == "cites" and ex.get("refs") == refs
    if already:
        return False
    ex["relationship_kind"] = "cites"
    ex["ref"] = refs[0]
    ex["refs"] = refs
    ex["explanation"] = f"Cites {ref_str} (chapter:verse found in the card text)."
    edge["extra"] = ex
    low = book.lower().replace(" ", "_")
    t = edge.get("title") or ""
    for verb in (" references ", " cites "):
        if verb in t:
            edge["title"] = t.replace(verb, " cites ", 1)
            break
    edge["body"] = f"Cites {ref_str} — a chapter:verse reference found in the card text."
    src = edge.get("source")
    if isinstance(src, dict):
        src["label"] = "Chapter:verse citation"
        src["ref"] = ref_str
    bands = edge.get("bands")
    if isinstance(bands, list):
        edge["bands"] = ["cites" if b in ("references", "cites") else b for b in bands]
        if "chapter_verse" not in edge["bands"]:
            edge["bands"].append("chapter_verse")
    if isinstance(edge.get("box"), str):
        edge["box"] = edge["box"].replace("_references_", "_citation_").replace("dictionary_references", "citation")
    edge["updated_at"] = now
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=DEFAULT_PATH)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if not os.path.exists(args.path):
        print(f"ERROR: no such file: {args.path}", file=sys.stderr)
        return 2

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    raw_lines = []
    cards = {}
    with open(args.path, encoding="utf-8") as f:
        for raw in f:
            raw_lines.append(raw)
            s = raw.strip()
            if s:
                c = json.loads(s)
                cards[c.get("id")] = c

    book_card = {c.get("title").strip(): cid for cid, c in cards.items()
                 if c.get("kind") == "note" and _is_public(c) and (c.get("title") or "").strip() in BOOKS}
    # index existing connections by (left,right) -> card id
    pair_index = {}
    for cid, c in cards.items():
        if c.get("kind") != "connection":
            continue
        ex = c.get("extra") or {}
        a, b = ex.get("left_card_id"), ex.get("right_card_id")
        if a and b:
            pair_index[(a, b)] = cid

    upgraded = 0
    created = []
    changed_ids = set()
    for cid, c in list(cards.items()):
        if c.get("kind") != "note" or not _is_public(c):
            continue
        refs_by_book = _refs_in(c)
        if not refs_by_book:
            continue
        left_title = (c.get("title") or cid)
        for book, refs in refs_by_book.items():
            right = book_card.get(book)
            if not right or right == cid:
                continue
            existing = pair_index.get((cid, right)) or pair_index.get((right, cid))
            if existing:
                if _upgrade(cards[existing], book, refs, now):
                    upgraded += 1
                    changed_ids.add(existing)
            else:
                edge = _new_edge(cid, left_title, right, book, refs, now)
                if edge["id"] not in cards:
                    cards[edge["id"]] = edge
                    created.append(edge)
                    pair_index[(cid, right)] = edge["id"]

    print(f"file:               {args.path}")
    print(f"book link targets:  {len(book_card)}/66")
    print(f"edges UPGRADED references->cites: {upgraded}")
    print(f"edges CREATED (new genuine cites): {len(created)}")
    if args.dry_run:
        print("(dry-run — nothing written)")
        return 0
    if not upgraded and not created:
        print("(no change — already re-cited; nothing written)")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for raw in raw_lines:
            s = raw.strip()
            if not s:
                f.write(raw if raw.endswith("\n") else raw + "\n")
                continue
            cid = json.loads(s).get("id")
            if cid in changed_ids:
                f.write(json.dumps(cards[cid], ensure_ascii=False) + "\n")
            else:
                f.write(s + "\n")
        for edge in created:  # append the new edges
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")
    os.replace(tmp, args.path)
    print(f"OK — {upgraded} upgraded, {len(created)} created in {args.path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
