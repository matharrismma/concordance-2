#!/usr/bin/env python3
"""The Biblical Encyclopedia, built AS Cards in the keeping — not a separate structure.

Contract §6 item 9: "Biblical Encyclopedia — built AS Cards in the existing corpus/Cards system
(not a separate structure), with a clean card-catalog browsing interface." The source is already
in the house: Easton's Bible Dictionary (1897, public domain) — 3,962 entries the characters
module has served for weeks (persons, places, concepts, objects). What was missing is the
NESTING: the entries lived only behind /characters, absent from the keeping — /search could not
find them, the graph could not show them, the Floor did not nest them.

This mints, deterministically and idempotently, from the SAME store characters.py serves
(data/characters/easton.jsonl — one source of truth, no second copy to drift):

  * 1 spine card, part_of the Floor of Discovery.
  * 1 stub card per entry -> member_of the spine, boxed by Easton's own category (person / place /
    concept / object — the card-catalog drawers), body = the entry's opening + a pointer to the
    full text at /characters.html. Stub + link, the same lazy pattern as the Gutenberg deck: the
    keeping holds the card; the full entry stays where it already lives.
  * `cites` edges to the book cards a reader can walk — resolved BY TITLE against the live corpus
    (never assumed ids; the book-card lesson), capped at 3 per entry so the map stays legible.

Writes only data/encyclopedia_cards.jsonl (registered in corpus.py's extra-sources list).
Re-running replaces it wholesale; ids are stable, so the graph does not churn.

    PYTHONPATH=src python tools/card_encyclopedia.py --dry-run
    PYTHONPATH=src python tools/card_encyclopedia.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_encyclopedia"
SOURCE_LABEL = "Easton's Bible Dictionary (1897, public domain)"

_ws = re.compile(r"\s+")
_book_re = re.compile(r"^([1-3]?\s*[A-Za-z][A-Za-z. ]*?)\s*\d", re.A)


def _book_card_index() -> Dict[str, str]:
    """lower-cased book title -> card id, resolved against the LIVE corpus (never assumed)."""
    from concordance import corpus
    cards = corpus.default_corpus().cards
    out: Dict[str, str] = {}
    for cid, c in cards.items():
        t = (c.get("title") or "").strip().lower()
        if c.get("kind") == "note" and c.get("visibility", "public") == "public" and t:
            out.setdefault(t, cid)
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    src = ROOT / "data" / "characters" / "easton.jsonl"
    if not src.exists():
        print(f"source missing: {src} — run tools/migrate_characters.py first")
        return 1

    books = _book_card_index()
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The Biblical Encyclopedia — Easton's Bible Dictionary (1897)",
        "body": ("The reference section of the library in a card catalog: 3,962 entries — persons, "
                 "places, concepts, and objects of Scripture — each a card in the keeping, each "
                 "opening into the full public-domain entry and the verses that speak of it. "
                 "Found and attributed, never generated."),
        "source": {"label": SOURCE_LABEL, "url": "", "domain": "scripture", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["encyclopedia", "dictionary", "easton", "reference", "spine"],
        "subject": "The Biblical Encyclopedia",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the reference section of the keeping, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
        "generated": False,
    }

    cards: List[dict] = [spine]
    cites_minted = 0
    with open(src, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            e = json.loads(ln)
            eid, name = e.get("id"), (e.get("name") or "").strip()
            if not eid or not name:
                continue
            text = _ws.sub(" ", (e.get("text") or "")).strip()
            stub = text[:280] + ("…" if len(text) > 280 else "")
            cat = (e.get("category") or "concept").strip().lower()
            conns = [{"to_card_id": SPINE, "relationship": "member_of",
                      "evidence": "an entry of the Biblical Encyclopedia in the keeping"}]
            seen_books: set = set()
            for r in (e.get("scripture_refs") or []):
                m = _book_re.match(str(r).strip())
                if not m:
                    continue
                bk = _ws.sub(" ", m.group(1)).strip().lower()
                bid = books.get(bk)
                if bid and bk not in seen_books and len(seen_books) < 3:
                    seen_books.add(bk)
                    conns.append({"to_card_id": bid, "relationship": "cites",
                                  "evidence": f"the entry cites {r}"})
                    cites_minted += 1
            cards.append({
                "id": f"card_enc_{eid}", "kind": "reference", "title": name[:180],
                "body": (stub + f"\n\nFull entry: {SOURCE_LABEL} — /characters.html?search="
                         + name.replace(" ", "+")),
                "source": {"label": SOURCE_LABEL, "url": "", "domain": "scripture",
                           "authority_tier": "reference"},
                "shelf": "encyclopedia", "box": cat,
                "bands": ["encyclopedia", cat] + [w for w in name.lower().split()[:4]],
                "subject": name,
                "connections": conns,
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
                "generated": False,
                "extra": {"easton_id": eid, "category": cat,
                          "refs": (e.get("scripture_refs") or [])[:12]},
            })

    from collections import Counter
    boxes = Counter(c.get("box") for c in cards[1:])
    print(f"cards to mint: {len(cards)} (1 spine + {len(cards)-1} entries)")
    print(f"drawers: {dict(boxes)}")
    print(f"cites edges to book cards: {cites_minted}")
    if dry:
        print("--dry-run: nothing written.")
        return 0

    base = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
    out = base / "encyclopedia_cards.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
