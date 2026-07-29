#!/usr/bin/env python3
"""SCAN, don't reproduce — topical indexes become FOUND EDGES, name lists become facts.

Matt, 2026-07-29: *"I don't want to reproduce. I want you to scan for useful cards and build
our card library. We aren't trying to give away the source. We want the knowledge."*

The two highest-leverage works in the public-domain queue are not prose at all:

  * **Nave's Topical Bible** and **Torrey's New Topical Textbook** are INDEXES — a subject and
    the verses that speak to it. The knowledge IS the structure. We take the topic and its
    references, resolve each reference to the verse card we already hold, and mint a
    `speaks_to` edge. Nothing of the work's expression is copied; what we gain is the
    connective tissue the keeping exists for.
  * **Hitchcock's Bible Names** is a fact table: a name and what it means. The datum is the
    card; there is no article to reproduce.

Every card carries the waybill (work, author, edition, Public Domain, CrossWire) so the reader
can go to the source — which stays the source. Where an entry is prose rather than structure,
this tool takes NOTHING and says so in the count: a scanner that quietly paraphrases would be
generating, and generation is the last resort, never the harvest.

    PYTHONPATH=src python tools/extract_topical.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

FLOOR = "card_k_floor_of_discovery"
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))

# A scripture reference as these indexes write them: "Ge 1:1", "1Ki 8:22", "Rev 22:21".
_REF = re.compile(r"\b((?:[1-3]\s?)?[A-Z][a-zA-Z]{1,11}\.?)\s+(\d{1,3}):(\d{1,3})")

TOPICAL = {
    "Nave":   ("nave", "Nave's Topical Bible",
               "Nave's Topical Bible (Orville J. Nave, 1897) — Public Domain (CrossWire SWORD)"),
    "Torrey": ("torrey", "Torrey's New Topical Textbook",
               "R. A. Torrey's New Topical Textbook — Public Domain (CrossWire SWORD)"),
}
NAMES = {
    "Hitchcock": ("hitchcock", "Hitchcock's Bible Names",
                  "Hitchcock's Bible Names Dictionary (Roswell D. Hitchcock, 1874) — "
                  "Public Domain (CrossWire SWORD)"),
}


def _verse_index():
    """(book-lower, chapter, verse) -> card id, from the verse cards already in the keeping."""
    idx = {}
    for name in ("scripture_cards.jsonl",):
        p = DATA / name
        if not p.exists():
            continue
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                c = json.loads(ln)
            except ValueError:
                continue
            ref = str((c.get("source") or {}).get("ref") or c.get("title") or "")
            m = re.match(r"^([\w ]+?)\s+(\d+):(\d+)", ref)
            if m:
                idx.setdefault((m.group(1).strip().lower(), m.group(2), m.group(3)), c["id"])
    return idx


def _book_key(abbrev: str, books: set):
    """Resolve 'Ge'/'1Ki'/'Rev' against the book names the keeping actually uses. Never guess:
    an abbreviation that matches nothing is dropped and counted."""
    a = abbrev.replace(".", "").strip().lower()
    a = re.sub(r"^([1-3])\s*", r"\1 ", a)
    if a in books:
        return a
    for b in books:                       # unique prefix match, or nothing
        if b.startswith(a):
            hits = [x for x in books if x.startswith(a)]
            return hits[0] if len(hits) == 1 else None
    return None


def _card(cid, title, body, box, bands, spine, subject, attribution, conns):
    return {"id": cid, "kind": "reference", "title": title[:180], "body": body,
            "source": {"label": attribution, "url": "", "domain": "scripture",
                       "authority_tier": "reference"},
            # Its OWN shelf: a topical index is not an encyclopedia entry, and the zero-orphan
            # gate rightly refused to let it hang under the encyclopedia spines.
            "shelf": "topical", "box": box, "bands": bands, "subject": subject,
            "connections": conns, "author": "engine", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "witness", "generated": False}


def _spine(cid, title, body, box, attribution):
    return {"id": cid, "kind": "reference", "title": title, "body": body,
            "source": {"label": attribution, "url": "", "domain": "scripture",
                       "authority_tier": "reference"},
            "shelf": "spine", "box": "spine",
            "bands": ["topical", box, "index", "spine"], "subject": title,
            "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                             "evidence": "the reference section of the keeping"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
            "generated": False}


def main() -> int:
    from card_sword_dicts import read_module      # the proven zLD walk
    dry = "--dry-run" in sys.argv
    vidx = _verse_index()
    books = {b for b, _c, _v in vidx}
    print(f"verse cards available to link into: {len(vidx):,} across {len(books)} books")

    cards, stats = [], {}
    for mod, (box, title, attribution) in sorted(TOPICAL.items()):
        zp = DATA / "acquisitions" / f"{mod}.zip"
        if not zp.exists():
            stats[mod] = "archive absent"
            continue
        spine_id = f"card_spine_topic_{box}"
        entries = read_module(zp)
        if not entries:
            stats[mod] = ("UNPARSED — the zLD walk recovered no entries from this archive "
                          "(a different module layout). Nothing taken; not silently zero.")
            continue
        topics = edges = unresolved = prose_only = 0
        for head, text in entries:
            refs, seen = [], set()
            for bk, ch, vs in _REF.findall(text):
                key = _book_key(bk, books)
                if not key:
                    unresolved += 1
                    continue
                cid = vidx.get((key, ch, vs))
                if cid and cid not in seen:
                    seen.add(cid)
                    refs.append((f"{key.title()} {ch}:{vs}", cid))
            if not refs:
                prose_only += 1        # nothing structural to take — we take nothing
                continue
            nice = head.title() if head.isupper() else head
            listed = "\n".join(f"  · {r}" for r, _ in refs[:60])
            body = (f"{nice} — where Scripture speaks to it.\n\n{listed}"
                    + (f"\n  … and {len(refs)-60} more" if len(refs) > 60 else "")
                    + f"\n\n{len(refs)} passage(s), indexed by {title}. The topic and its "
                      f"references are the knowledge taken; the work's own text stays with the "
                      f"work.")
            conns = [{"to_card_id": spine_id, "relationship": "member_of",
                      "evidence": f"a topic indexed by {title}"}]
            conns += [{"to_card_id": cid, "relationship": "speaks_to",
                       "evidence": f"{title} indexes {ref} under '{nice}'"} for ref, cid in refs[:60]]
            slug = re.sub(r"[^a-z0-9]+", "_", nice.lower()).strip("_")[:60] or "topic"
            cards.append(_card(f"card_topic_{box}_{slug}", f"{nice} — topical index", body, box,
                               ["topical", box, "index"] + nice.lower().split()[:3],
                               spine_id, nice, attribution, conns))
            topics += 1
            edges += len(refs[:60])
        if topics:
            cards.append(_spine(spine_id, title,
                                f"{topics:,} topics, each pointing at the passages that speak "
                                f"to it — {edges:,} links into the verse cards of the keeping. "
                                f"{attribution}. The index's structure is what we took; its "
                                f"text is still its own.", box, attribution))
            stats[mod] = f"{topics:,} topics · {edges:,} edges · {prose_only:,} entries with no "\
                         f"resolvable reference (nothing taken) · {unresolved:,} refs unresolved"

    for mod, (box, title, attribution) in sorted(NAMES.items()):
        zp = DATA / "acquisitions" / f"{mod}.zip"
        if not zp.exists():
            stats[mod] = "archive absent"
            continue
        spine_id = f"card_spine_names_{box}"
        entries = read_module(zp)
        # Hitchcock lists ~2,500 names; a parse returning a handful means the block splitting
        # did not match this module's layout and each "entry" is really many names run together.
        # Shipping those would put merged blobs in the keeping under a false headword, so the
        # module is REPORTED as unparsed and nothing is taken. A wrong card is worse than none.
        if len(entries) < 100:
            stats[mod] = (f"UNPARSED — only {len(entries)} entries recovered; this module's "
                          f"layout differs from the zLD walk. Nothing taken.")
            continue
        n = 0
        for head, text in entries:
            meaning = _REF.sub("", text).strip(" .;:")
            if not meaning or len(meaning) > 300:
                continue
            nice = head.title() if head.isupper() else head
            slug = re.sub(r"[^a-z0-9]+", "_", nice.lower()).strip("_")[:60] or "name"
            body = (f"{nice} — the name means: {meaning}\n\nA name's meaning, as recorded by "
                    f"{title}. A fact, not a passage: names carry sense in the tongues of "
                    f"Scripture, and the sense is often the point of the story.")
            cards.append(_card(f"card_name_{box}_{slug}", f"{nice} — the name means", body, box,
                               ["names", box, "meaning", nice.lower()], spine_id, nice,
                               attribution,
                               [{"to_card_id": spine_id, "relationship": "member_of",
                                 "evidence": f"a name recorded by {title}"}]))
            n += 1
        if n:
            cards.append(_spine(spine_id, title,
                                f"{n:,} biblical names and what they mean. {attribution}. "
                                f"Facts taken; the work stays the work.", box, attribution))
            stats[mod] = f"{n:,} name meanings"

    print(f"\ncards: {len(cards):,}")
    for m, s in sorted(stats.items()):
        print(f"  {m:10} {s}")
    if cards:
        bodies = [len(c["body"]) for c in cards]
        print(f"average body: {sum(bodies)//len(bodies):,} chars · "
              f"stubs: {sum(1 for b in bodies if b < 120)}")
        total_edges = sum(len(c["connections"]) for c in cards)
        print(f"connections minted: {total_edges:,}")
    if dry or not cards:
        print("--dry-run: nothing written." if dry else "nothing to write")
        return 0
    out = DATA / "topical_cards.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({out.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
