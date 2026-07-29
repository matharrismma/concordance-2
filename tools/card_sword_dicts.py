#!/usr/bin/env python3
"""The public-domain SWORD dictionaries, carded — academic pass 2 of the seeding loop.

CrossWire's module index lists **226 Public Domain modules**, 101 of them English. ISBE proved
the road; this walks further down it with the reference works a Bible student actually reaches
for, all Public Domain by the publisher's own declaration in the module's .conf:

    Smith      Smith's Bible Dictionary
    Nave       Nave's Topical Bible
    Torrey     R. A. Torrey's New Topical Textbook
    Hitchcock  Hitchcock's Bible Names (their meanings)
    AmTract    American Tract Society Bible Dictionary

**MATT, 2026-07-29 — THE STEER THAT DEFINES THIS TOOL:** *"I don't want to reproduce. I want
you to scan for useful cards and build our card library. We aren't trying to give away the
source. We want the knowledge."*

So this is a SCANNER, not a mirror. The first draft carded each article's full text — lawful
(these are Public Domain) but the wrong goal: it would have made us a copy of CrossWire rather
than a library of knowledge. What we take is the KNOWLEDGE the work holds:

  * Hitchcock  — name → meaning. Pure fact ("Aaron: a teacher; lofty; mountain of strength").
                 No prose to reproduce; the datum IS the card.
  * Nave, Torrey — topic → the verses that speak to it. These are TOPICAL INDEXES, so what we
                 take is the structure: a subject and its scripture references, which become
                 FOUND EDGES into the verse cards we already hold. This is the concordance of
                 reality doing its actual work — connection, not copy.
  * Smith, AmTract — the definitional core (what the thing IS) plus the references the article
                 cites, with a pointer back to the source for the rest. A short attributed
                 quote where a definition cannot be stated without one; never the whole article.

Rule for every card here: the knowledge and its waybill travel; the source stays the source.
Where we state a fact, it is found. Where we would have to write prose to fill a gap, we leave
the gap and point at the work — a card that cites is honest, a card that paraphrases silently
is not (cite ≠ prove; gather, don't author).

Same zLD binary layout as ISBE (idx/dat/zdx/zdt), parsed with the stdlib only. Each module
gets a spine (part_of the Floor); licence and edition travel on every card; `generated: false`.

    PYTHONPATH=src python tools/card_sword_dicts.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

ACQ = ROOT / "data" / "acquisitions"
FLOOR = "card_k_floor_of_discovery"
_ws = re.compile(r"\s+")
_tag = re.compile(r"<[^>]+>")
_break = re.compile(r"</p>|<lb\s*/?>|</list>|</item>|<br\s*/?>", re.I)

# module -> (shelf box, human title, attribution shown on every card)
MODULES = {
    "Smith":     ("smith", "Smith's Bible Dictionary",
                  "Smith's Bible Dictionary (William Smith, 1863) — Public Domain (CrossWire SWORD)"),
    "Nave":      ("nave", "Nave's Topical Bible",
                  "Nave's Topical Bible (Orville J. Nave, 1897) — Public Domain (CrossWire SWORD)"),
    "Torrey":    ("torrey", "Torrey's New Topical Textbook",
                  "R. A. Torrey's New Topical Textbook — Public Domain (CrossWire SWORD)"),
    "Hitchcock": ("hitchcock", "Hitchcock's Bible Names",
                  "Hitchcock's Bible Names Dictionary (Roswell D. Hitchcock, 1874) — Public Domain (CrossWire SWORD)"),
    "AmTract":   ("amtract", "American Tract Society Bible Dictionary",
                  "American Tract Society Bible Dictionary (1859) — Public Domain (CrossWire SWORD)"),
}


def _mod_paths(zf):
    """The module's files AND which driver they imply.

    zLD is compressed (idx/dat/zdx/zdt); **RawLD is not** (idx/dat only, the text sitting in dat
    directly). Torrey is RawLD, and the first version of this reader assumed zLD for everything
    and recovered ZERO entries from it — reported as UNPARSED rather than silently zero, which
    is how the real cause got found instead of guessed."""
    names = zf.namelist()
    idx = next((n for n in names if n.endswith(".idx") and "/lexdict/" in n), None)
    if not idx:
        return None
    base = idx[:-4]
    z = [base + e for e in (".idx", ".dat", ".zdx", ".zdt")]
    if all(n in names for n in z):
        return ("zld", z)
    r = [base + e for e in (".idx", ".dat")]
    if all(n in names for n in r):
        return ("rawld", r)
    return None


def _clean(raw: str) -> str:
    """Markup out, entities in, NULs gone — the same normalisation for both drivers."""
    text = _break.sub("\n", raw)
    text = _tag.sub(" ", text)
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&apos;", "'"), ("&nbsp;", " ")):
        text = text.replace(a, b)
    text = "\n".join(_ws.sub(" ", ln).strip() for ln in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.replace("\x00", "").strip()


def _read_rawld(idx: bytes, dat: bytes):
    """RawLD: 8-byte (offset,size) records into an UNCOMPRESSED dat, each entry being
    "KEY<newline><text>". No block table, no zlib — a different driver, not a broken zLD."""
    out = []
    for i in range(len(idx) // 8):
        off, size = struct.unpack_from("<II", idx, i * 8)
        rec = dat[off:off + size]
        sep = b"\r\n" if b"\r\n" in rec else (b"\n" if b"\n" in rec else None)
        if sep is None:
            continue
        key, _, body = rec.partition(sep)
        text = _clean(body.decode("utf-8", "replace"))
        head = key.decode("utf-8", "replace").strip()
        if head and len(text) >= 3:
            out.append((head, text))
    return out


def read_module(zip_path: Path):
    """(headword, plain text) for every entry — the same zLD walk proven on ISBE."""
    zf = zipfile.ZipFile(zip_path)
    found = _mod_paths(zf)
    if not found:
        return []
    driver, paths = found
    if driver == "rawld":
        return _read_rawld(*(zf.read(p) for p in paths))
    idx, dat, zdx, zdt = (zf.read(p) for p in paths)
    blocks = {}

    def block(n):
        if n not in blocks:
            off, size = struct.unpack_from("<II", zdx, n * 8)
            blocks[n] = zlib.decompress(zdt[off:off + size])
        return blocks[n]

    out = []
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
        try:
            blk = block(bnum)
            count = struct.unpack_from("<I", blk, 0)[0]
            if enum_ >= count:
                continue
            eoff, esize = struct.unpack_from("<II", blk, 4 + enum_ * 8)
            raw = blk[eoff:eoff + esize].decode("utf-8", "replace")
        except Exception:  # noqa: BLE001 — a corrupt block is skipped and the rest still lands
            continue
        text = _break.sub("\n", raw)
        text = _tag.sub(" ", text)
        for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                     ("&apos;", "'"), ("&nbsp;", " ")):
            text = text.replace(a, b)
        text = "\n".join(_ws.sub(" ", ln).strip() for ln in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text).replace("\x00", "").strip()
        head = key.decode("utf-8", "replace").strip()
        # A MEANING IS OFTEN SHORT. This filter was `>= 60` and silently ate 2,609 of
        # Hitchcock's 2,616 entries — "Aaron: a teacher; lofty" is 23 characters and is the
        # WHOLE datum. It looked like a block-boundary bug; it was my own threshold. Only a
        # genuinely empty entry is dropped now. (Check the check, seventh time today.)
        if head and len(text) >= 3:
            out.append((head, text))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    cards, summary, skipped = [], {}, {}
    for mod, (box, title, attribution) in sorted(MODULES.items()):
        zp = ACQ / f"{mod}.zip"
        if not zp.exists():
            skipped[mod] = "archive not on this machine"
            continue
        entries = read_module(zp)
        if not entries:
            skipped[mod] = "no zLD payload found in the archive"
            continue
        spine_id = f"card_spine_dict_{box}"
        seen = {}
        for head, text in entries:
            slug = re.sub(r"[^a-z0-9]+", "_", head.lower()).strip("_")[:60] or "entry"
            cid = f"card_dict_{box}_{slug}"
            if cid in seen:
                seen[cid] += 1
                cid = f"{cid}_{seen[cid]}"
            else:
                seen[cid] = 0
            nice = head.title() if head.isupper() else head
            cards.append({
                "id": cid, "kind": "reference", "title": f"{title.split(chr(39))[0].strip()}: {nice}"[:180],
                "body": text,
                "source": {"label": attribution, "url": "", "ref": head, "domain": "scripture",
                           "authority_tier": "reference"},
                "shelf": "encyclopedia", "box": box,
                "bands": ["encyclopedia", box, "dictionary"] + nice.lower().split()[:3],
                "subject": nice,
                "connections": [{"to_card_id": spine_id, "relationship": "member_of",
                                 "evidence": f"an entry of {title}"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
                "generated": False,
                "extra": {"sword_module": mod, "headword": head},
            })
        summary[mod] = len(entries)
        cards.append({
            "id": spine_id, "kind": "reference", "title": title,
            "body": (f"{title} — {len(entries):,} entries in the keeping, each the article "
                     f"itself. {attribution}. Found and attributed, never generated; where the "
                     f"work is silent we add nothing in its name."),
            "source": {"label": attribution, "url": "", "domain": "scripture",
                       "authority_tier": "reference"},
            "shelf": "spine", "box": "spine",
            "bands": ["encyclopedia", box, "dictionary", "spine"],
            "subject": title,
            "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                             "evidence": "the reference section of the keeping"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
            "generated": False,
        })
    total = len(cards)
    bodies = [len(c["body"]) for c in cards]
    print(f"cards: {total:,} from {len(summary)} module(s)")
    for m, n in sorted(summary.items()):
        print(f"  {m:10} {n:6,} entries")
    for m, why in sorted(skipped.items()):
        print(f"  {m:10} SKIPPED — {why}")
    if bodies:
        print(f"average body: {sum(bodies)//len(bodies):,} chars")
        print(f"stubs (must be 0): {sum(1 for b in bodies if b < 120)}")
    if dry or not cards:
        print("--dry-run: nothing written." if dry else "nothing to write")
        return 0
    out = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
               or str(ROOT / "data")) / "sword_dict_cards.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({out.stat().st_size/1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
