#!/usr/bin/env python3
"""Person/place mention web — dictionary-style cross-references, curated and guarded.

Where a public note's own text mentions a person or place that has an Easton's Bible
Dictionary entry card, link the two with relationship_kind 'references' — the established
honest verb for a name co-mention (see tools/demote_cites.py). Nothing is generated or
guessed; every edge records the mentioned name, and the person/place classification is
EASTON'S OWN category field (data/easton/entries.jsonl, public domain) — not a heuristic.

Guards (all mechanical):
  * curated subjects only — Easton entries categorized person|place; concepts/objects never link;
  * book-name subjects (John, Mark, ...) are EXCLUDED — those belong to the chapter:verse
    citer (tools/recite.py), and a bare name is not a book citation;
  * MID-SENTENCE capitalized matches only — English function words ("On", "No") are
    capitalized only at sentence starts, while genuine proper-name mentions appear
    mid-sentence, so a match at a sentence/heading start is ambiguous and dropped;
  * pairs that already carry ANY connection are skipped (cites is stronger and stays).

Deterministic ids, idempotent (second run changes 0), atomic write; unchanged lines pass
through byte-for-byte.

    python tools/mention_web.py [path/to/cards.jsonl] [--easton path] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(_ROOT, "data", "cards.jsonl")
DEFAULT_EASTON = os.path.join(_ROOT, "data", "easton", "entries.jsonl")

BOOKS = {"genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua", "judges", "ruth",
         "1 samuel", "2 samuel", "1 kings", "2 kings", "1 chronicles", "2 chronicles", "ezra",
         "nehemiah", "esther", "job", "psalms", "psalm", "proverbs", "ecclesiastes",
         "song of solomon", "isaiah", "jeremiah", "lamentations", "ezekiel", "daniel", "hosea",
         "joel", "amos", "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah", "haggai",
         "zechariah", "malachi", "matthew", "mark", "luke", "john", "acts", "romans",
         "1 corinthians", "2 corinthians", "galatians", "ephesians", "philippians", "colossians",
         "1 thessalonians", "2 thessalonians", "1 timothy", "2 timothy", "titus", "philemon",
         "hebrews", "james", "1 peter", "2 peter", "1 john", "2 john", "3 john", "jude",
         "revelation"}


def _is_public(c: dict) -> bool:
    return c.get("visibility") == "public" or c.get("lifecycle_stage") in ("public", "featured")


def _load_categories(easton_path: str) -> dict:
    """Easton's OWN person/place classification: name -> 'person'|'place'."""
    cat = {}
    with open(easton_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            if e.get("category") in ("person", "place"):
                cat[str(e.get("name") or "").strip()] = e["category"]
    return cat


def _mid_sentence(text: str, start: int) -> bool:
    """True when the match follows a letter/digit/comma-ish — a genuine mid-sentence mention.
    Start-of-text, after .!?:" or a newline = a sentence/heading start — ambiguous, dropped."""
    i = start - 1
    while i >= 0 and text[i] in " \t":
        i -= 1
    return i >= 0 and (text[i].isalpha() or text[i].isdigit() or text[i] in ",;)-")


def _edge_id(left: str, right: str) -> str:
    return "card_c_" + hashlib.sha256(f"{left}|{right}|references".encode()).hexdigest()[:12]


def _new_edge(left: str, left_title: str, right: str, name: str, kind: str, now: str) -> dict:
    low = name.lower().replace(" ", "_")
    return {
        "id": _edge_id(left, right), "kind": "connection",
        "title": f"{left_title} references {name}",
        "body": f"Mentions {name} ({kind}) — the name appears in the card text; the entry is "
                f"Easton's Bible Dictionary (public domain), which classifies it as a {kind}.",
        "source": {"label": "Name mention (Easton's Bible Dictionary, PD)", "url": "",
                   "ref": name, "authority_tier": "engine_derived"},
        "shelf": "connections", "box": f"mention_{kind}",
        "bands": ["references", "mention", kind, low],
        "connections": [{"to_card_id": right, "relationship": "see_also"}],
        "author": "engine", "created_at": now, "updated_at": now,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "stable",
        "metrics": {"paperclips_count": 0, "helpful_count": 0, "not_helpful_count": 0,
                    "cite_count": 0, "walks_through_count": 0, "flagged_count": 0},
        "extra": {"left_card_id": left, "right_card_id": right,
                  "relationship_kind": "references", "mention": name, "easton_category": kind,
                  "bidirectional": False,
                  "explanation": f"Name mention: {name} (Easton category: {kind}) found "
                                 f"mid-sentence in the card text."},
        "witnesses": [],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=DEFAULT_PATH)
    ap.add_argument("--easton", default=DEFAULT_EASTON)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    for p in (args.path, args.easton):
        if not os.path.exists(p):
            print(f"ERROR: no such file: {p}", file=sys.stderr)
            return 2

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    cat_by_name = _load_categories(args.easton)

    raw_lines = []
    cards = {}
    with open(args.path, encoding="utf-8") as f:
        for raw in f:
            raw_lines.append(raw)
            s = raw.strip()
            if s:
                c = json.loads(s)
                cards[c.get("id")] = c
    notes = {cid: c for cid, c in cards.items() if c.get("kind") == "note" and _is_public(c)}

    # curated subjects that have a 2.0 entry card; book-name subjects excluded
    name_card = {}
    for cid, c in notes.items():
        t = (c.get("title") or "").strip()
        if t.startswith("Easton: "):
            subj = t[len("Easton: "):].strip()
            if subj in cat_by_name and subj.lower() not in BOOKS:
                name_card[subj] = (cid, cat_by_name[subj])
    if not name_card:
        print("ERROR: no curated subjects matched entry cards — wrong easton file?", file=sys.stderr)
        return 2

    pair_exists = set()
    for c in cards.values():
        if c.get("kind") != "connection":
            continue
        ex = c.get("extra") or {}
        a, b = ex.get("left_card_id"), ex.get("right_card_id")
        if a and b:
            pair_exists.add((a, b))
            pair_exists.add((b, a))

    pat = re.compile(r"\b(" + "|".join(re.escape(n) for n in
                                       sorted(name_card, key=len, reverse=True)) + r")\b")
    created = []
    for cid, c in notes.items():
        hit = set()
        # title and body are scanned as SEPARATE segments — joining them would hand the body's
        # first word a fake mid-sentence context (it would "follow" the title's last letter).
        for segment in (c.get("title") or "", c.get("body") or ""):
            for m in pat.finditer(segment):
                if _mid_sentence(segment, m.start()):
                    hit.add(m.group(1))
        for name in sorted(hit):
            target, kind = name_card[name]
            if target == cid or (c.get("title") or "").strip() == f"Easton: {name}":
                continue
            if (cid, target) in pair_exists:
                continue  # an edge (cites/references/...) already stands — never double-edge
            edge = _new_edge(cid, (c.get("title") or cid), target, name, kind, now)
            if edge["id"] in cards:
                continue
            cards[edge["id"]] = edge
            created.append(edge)
            pair_exists.add((cid, target))
            pair_exists.add((target, cid))

    persons = sum(1 for e in created if e["extra"]["easton_category"] == "person")
    print(f"file:              {args.path}")
    print(f"curated subjects:  {len(name_card)} (Easton person/place with an entry card)")
    print(f"mention edges CREATED: {len(created)} (person {persons} / place {len(created) - persons})")
    if args.dry_run:
        print("(dry-run — nothing written)")
        return 0
    if not created:
        print("(no change — mention web already present; nothing written)")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for raw in raw_lines:
            s = raw.strip()
            f.write((s + "\n") if s else (raw if raw.endswith("\n") else raw + "\n"))
        for edge in created:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")
    os.replace(tmp, args.path)
    print(f"OK — {len(created)} mention edges appended to {args.path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
