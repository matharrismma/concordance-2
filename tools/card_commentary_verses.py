#!/usr/bin/env python3
"""The commentaries, carded verse by verse — the largest substance seam already on disk.

GAPS.md G1: 46% of the keeping is a pointer, and the million must be counted in SUBSTANCE.
This mints the deepest substance we already hold and have not yet carded: three public-domain
commentaries stored as chapter files with per-verse blocks (Gill averages ~2,600 characters
of exposition per verse). Those words are on our disk, lawfully, attributed — and until now
they were reachable only through /commentary, never as cards in the keeping: not searchable,
not walkable in the graph, not findable by a reader who did not already know to ask.

Per source: one spine card (part_of the Floor), and one card per verse carrying the
commentator's OWN WORDS verbatim, attributed, `generated: false`. The father's own recorded
words, played back — never our opinion in his mouth (the bumblebee discipline).

Nesting (found edges only, never invented):
  * member_of  its source spine;
  * comments_on the verse card, when that verse exists in the keeping. This is FOUND — the
    commentary file itself says which verse it expounds; we assert nothing.

The `commentary` shelf is assigned to the `word` shard, so these bodies ride the freeze:
resident cost is a stub, and the full exposition rehydrates on read. REBUILD THE SHARDS after
minting, or the reader gets a title where a paragraph belongs.

    PYTHONPATH=src python tools/card_commentary_verses.py [--dry-run] [--source SLUG]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"
_ws = re.compile(r"[ \t]+")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def _books(root: Path):
    """OSIS code -> common name, from the source's own _books.json."""
    p = root / "_books.json"
    if not p.exists():
        return {}
    try:
        idx = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return {b.get("code"): (b.get("commonName") or b.get("name") or b.get("code"))
            for b in idx if isinstance(b, dict) and b.get("code")}


def main() -> int:
    from concordance import commentary
    dry = "--dry-run" in sys.argv
    only = None
    if "--source" in sys.argv:
        only = sys.argv[sys.argv.index("--source") + 1]

    base = Path(os.environ.get("CONCORDANCE_COMMENTARY_DIR", "").strip()
                or str(ROOT / "data" / "commentary"))
    # The verse cards already in the keeping, so `comments_on` points at something real.
    verse_ids = {}
    sp = ROOT / "data" / "scripture_cards.jsonl"
    if sp.exists():
        for ln in sp.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                c = json.loads(ln)
            except ValueError:
                continue
            ref = str((c.get("source") or {}).get("ref") or c.get("title") or "")
            m = re.match(r"^([\w ]+?)\s+(\d+):(\d+)", ref)
            if m:
                verse_ids.setdefault((m.group(1).strip().lower(), m.group(2), m.group(3)),
                                     c.get("id"))

    cards, per_source, linked = [], {}, 0
    for slug, meta in sorted(commentary.SOURCE_META.items()):
        if only and slug != only:
            continue
        root = base / slug
        if not root.exists():
            print(f"  {slug}: no store on this machine — skipped (a fact, not a silence)")
            continue
        names = _books(root)
        spine_id = f"card_spine_comm_{_slug(slug)}"
        n_here = 0
        for chapter_file in sorted(root.rglob("*.json")):
            if chapter_file.name == "_books.json":
                continue
            code = chapter_file.parent.name
            try:
                ch_num = int(chapter_file.stem)
            except ValueError:
                continue
            try:
                data = json.loads(chapter_file.read_text(encoding="utf-8"))
            except ValueError:
                continue
            book = names.get(code, code)
            for blk in (data.get("blocks") or []):
                text = (blk.get("text") or "").strip()
                verse = blk.get("verse")
                if not text or verse is None:
                    continue
                text = "\n".join(_ws.sub(" ", ln).strip() for ln in text.splitlines()).strip()
                ref = f"{book} {ch_num}:{verse}"
                conns = [{"to_card_id": spine_id, "relationship": "member_of",
                          "evidence": f"an entry of {meta['name']}"}]
                vid = verse_ids.get((book.strip().lower(), str(ch_num), str(verse)))
                if vid:
                    conns.append({"to_card_id": vid, "relationship": "comments_on",
                                  "evidence": f"the commentary file expounds {ref}"})
                    linked += 1
                cards.append({
                    "id": f"card_comm_{_slug(slug)}_{_slug(code)}_{ch_num}_{verse}",
                    "kind": "reference",
                    "title": f"{meta['author'].split('(')[0].strip()} on {ref}",
                    "body": text,
                    "source": {"label": f"{meta['name']} — {meta['license']}", "url": "",
                               "ref": ref, "domain": "scripture",
                               "authority_tier": "reference"},
                    "shelf": "commentary", "box": slug,
                    "bands": ["commentary", slug, book.lower(), "exposition"],
                    "subject": ref,
                    "connections": conns,
                    "author": "engine", "created_at": 0.0, "updated_at": 0.0,
                    "visibility": "public", "lifecycle_stage": "public",
                    "volatility": "permanent", "surface": "witness", "generated": False,
                    "extra": {"commentary_source": slug, "book": code, "chapter": ch_num,
                              "verse": verse, "via": meta.get("via", "")},
                })
                n_here += 1
        if n_here:
            per_source[slug] = n_here
            cards.append({
                "id": spine_id, "kind": "reference",
                "title": meta["name"],
                "body": (f"{meta['name']} — {n_here:,} verse expositions in the keeping, the "
                         f"commentator's own words, verbatim and attributed. {meta['author']}. "
                         f"{meta['license']}. Found and played back, never paraphrased and never "
                         f"spoken for: what he wrote is what you read, and where he is silent we "
                         f"say nothing in his name."),
                "source": {"label": f"{meta['name']} — {meta['license']}", "url": "",
                           "domain": "scripture", "authority_tier": "reference"},
                "shelf": "spine", "box": "spine",
                "bands": ["commentary", slug, "exposition", "spine"],
                "subject": meta["name"],
                "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                                 "evidence": "the commentary section of the keeping"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
                "generated": False,
            })

    total = len(cards)
    bodies = [len(c["body"]) for c in cards]
    print(f"cards: {total:,} ({len(per_source)} spine(s) + {total - len(per_source):,} verses)")
    for s, n in sorted(per_source.items()):
        print(f"  {s:16} {n:,}")
    if bodies:
        print(f"average body: {sum(bodies)//len(bodies):,} chars — substance, not stubs")
        print(f"linked to a verse card: {linked:,}")
    if dry:
        print("--dry-run: nothing written.")
        return 0
    out = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
               or str(ROOT / "data")) / "commentary_verse_cards.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({out.stat().st_size/1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
