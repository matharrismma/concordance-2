#!/usr/bin/env python3
"""ISBE 1915 — the International Standard Bible Encyclopedia, carded into the keeping (D5).

Matt, 2026-07-28 (decision D5): acquisitions in order — ISBE first, then Gill, then Clarke.

Source: CrossWire SWORD module "ISBE" v2.2 (data/acquisitions/ISBE.zip) — Public Domain,
TEI-encoded, 9,380 headword entries. Parsed here with the STDLIB ONLY (the zLD layout,
reverse-verified against the real offsets before this was written):

    isbe.idx  8-byte LE (offset,size) records into isbe.dat
    isbe.dat  entries "KEY\r\n" + u32 block + u32 entry-in-block
    isbe.zdx  8-byte LE (offset,size) records into isbe.zdt — one per zlib block
    isbe.zdt  zlib blocks; each opens u32 count, then count x (u32 offset, u32 size), then text

What this mints (the Easton pattern, exactly — stub + link, never a resident heavyweight):
  * data/acquisitions/isbe.db — compact read-only SQLite with the FULL entries (mmap'd at
    serve time; the card page renders the whole article from here — the guarantee reaches
    the reader while the resident card stays ~600 bytes).
  * data/isbe_cards.jsonl — 1 spine (part_of the Floor) + 9,380 stub cards, member_of the
    spine, shelf "encyclopedia", box "isbe". Found and attributed, never generated.

Scripture cites are left inline in the text for the existing re-citer/grafting tools —
this builder mints membership only (0-FP discipline: no guessed edges).

    PYTHONPATH=src python tools/card_isbe.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import struct
import sys
import zipfile
import zlib
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

ZIP = ROOT / "data" / "acquisitions" / "ISBE.zip"
MOD = "modules/lexdict/zld/isbe/isbe"
SPINE = "card_spine_isbe"
SOURCE_LABEL = ("International Standard Bible Encyclopedia (1915), ed. James Orr — "
                "Public Domain (CrossWire SWORD module ISBE v2.2)")

_ws = re.compile(r"\s+")
_tag = re.compile(r"<[^>]+>")
_break = re.compile(r"</p>|<lb\s*/?>|</list>|</item>", re.I)


def read_module(zf: zipfile.ZipFile) -> List[Tuple[str, str]]:
    """(headword, plain_text) for every entry, in module order."""
    idx = zf.read(f"{MOD}.idx")
    dat = zf.read(f"{MOD}.dat")
    zdx = zf.read(f"{MOD}.zdx")
    zdt = zf.read(f"{MOD}.zdt")
    blocks: Dict[int, bytes] = {}

    def block(n: int) -> bytes:
        if n not in blocks:
            off, size = struct.unpack_from("<II", zdx, n * 8)
            blocks[n] = zlib.decompress(zdt[off:off + size])
        return blocks[n]

    out: List[Tuple[str, str]] = []
    for i in range(len(idx) // 8):
        off, size = struct.unpack_from("<II", idx, i * 8)
        rec = dat[off:off + size]
        try:
            key, tail = rec.split(b"\r\n", 1)
        except ValueError:
            continue
        if len(tail) < 8:
            continue
        bnum, enum_ = struct.unpack_from("<II", tail, 0)
        blk = block(bnum)
        count = struct.unpack_from("<I", blk, 0)[0]
        if enum_ >= count:
            continue
        eoff, esize = struct.unpack_from("<II", blk, 4 + enum_ * 8)
        tei = blk[eoff:eoff + esize].decode("utf-8", "replace")
        text = _break.sub("\n", tei)
        text = _tag.sub(" ", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
                   .replace("&quot;", '"').replace("&apos;", "'")
        text = "\n".join(_ws.sub(" ", ln).strip() for ln in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        head = key.decode("utf-8", "replace").strip()
        if head and text:
            out.append((head, text))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    if not ZIP.exists():
        print(f"missing {ZIP} — fetch: crosswire.org rawzip ISBE.zip")
        return 2
    entries = read_module(zipfile.ZipFile(ZIP))
    total_chars = sum(len(t) for _h, t in entries)
    print(f"parsed {len(entries)} entries, {total_chars/1e6:.1f} MB of text")

    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The International Standard Bible Encyclopedia (1915)",
        "body": (f"The reference section deepens: {len(entries):,} scholarly entries — persons, "
                 "places, doctrines, customs, languages, and things of Scripture — from the "
                 "International Standard Bible Encyclopedia, edited by James Orr (1915). Each "
                 "card opens into the full public-domain article. Found and attributed, never "
                 "generated."),
        "source": {"label": SOURCE_LABEL, "url": "", "domain": "scripture",
                   "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["encyclopedia", "isbe", "reference", "spine", "orr"],
        "subject": "The International Standard Bible Encyclopedia",
        "connections": [{"to_card_id": "card_k_floor_of_discovery", "relationship": "part_of",
                         "evidence": "the reference section of the keeping, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
        "generated": False,
    }
    cards: List[dict] = [spine]
    for head, text in entries:
        slug = re.sub(r"[^a-z0-9]+", "_", head.lower()).strip("_")[:60]
        title = head.title() if head.isupper() else head
        stub = text[:280] + ("…" if len(text) > 280 else "")
        cards.append({
            "id": f"card_isbe_{slug}", "kind": "reference", "title": f"ISBE: {title}"[:180],
            "body": stub + "\n\nThe full 1915 article renders on this card's page.",
            "source": {"label": SOURCE_LABEL, "url": "", "domain": "scripture",
                       "authority_tier": "reference"},
            "shelf": "encyclopedia", "box": "isbe",
            "bands": ["encyclopedia", "isbe"] + [w for w in title.lower().split()[:4]],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": "an entry of the ISBE in the keeping"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
            "generated": False,
            "extra": {"isbe_headword": head},
        })
    # duplicate slugs (rare headword collisions) — last one wins in the corpus dict; refuse
    # silently dropping instead: suffix collisions so every entry stays reachable
    seen: Dict[str, int] = {}
    for c in cards[1:]:
        cid = c["id"]
        if cid in seen:
            seen[cid] += 1
            c["id"] = f"{cid}_{seen[cid]}"
        else:
            seen[cid] = 0
    print(f"cards to mint: {len(cards)} (1 spine + {len(cards)-1} entries)")
    if dry:
        print("--dry-run: nothing written.")
        return 0

    db_path = ROOT / "data" / "acquisitions" / "isbe.db"
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(str(db_path))
    db.executescript("pragma journal_mode=off; pragma synchronous=off;"
                     "create table entries (headword text primary key, title text, text text);")
    for (head, text), card in zip(entries, cards[1:]):
        db.execute("insert or replace into entries values (?,?,?)",
                   (head, card["subject"], text))
    db.commit()
    db.execute("vacuum")
    db.close()
    print(f"wrote {db_path} ({db_path.stat().st_size/1e6:.1f} MB)")

    base = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
    out = base / "isbe_cards.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
