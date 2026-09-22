#!/usr/bin/env python3
"""The trades shelf — a CARD CATALOGUE for the public-domain practical-arts texts held in the ark.

Matt, 2026-09-21: "I want to hold the knowledge that is PD. There are many great textbooks. There is
knowledge spread across languages." → "We will be the card catalogue. We won't hold the texts on
board. We will keep that on the external hard drive. We can send the whole source but it will be the
tortoise."

So this is the CATALOGUE, not the library floor. The full texts stay on the drive
(D:/NarrowHighway-Sources/archive_org/texts.db → docs_pd: verified public-domain, pre-1929, scanned
from the Internet Archive) and ship only on demand — the TORTOISE (sources.py fetches
archive.org/details/<id> live when a reader opens the work). Each card here is the HARE: a light
entry — title, discipline, language, PD provenance, and a pointer — that makes the work findable and
walkable without carrying a byte of it on board.

DISCIPLINE (the same gate the rest of the keeping carries):
  • STRICT PD ONLY — reads `docs_pd` (rows carrying pd_year + pd_basis), never the unverified `docs`.
  • Gather, don't author — every field comes from the held record; generated=False; provenance kept.
  • NO ORPHANS — every card is member_of the trades SPINE, part_of the Floor of Discovery.
  • LANGUAGE is a first-class band — the knowledge is spread across tongues; a light heuristic tags
    German/French/Latin where the title shows it, else english (most Archive PD scans). Best-effort,
    labelled as such; a metadata pass can sharpen it.

Runs where the drive is (this working device), because the drive is the source; the cards it mints
(data/trades_cards.jsonl) are then carried to the box and served. The box never needs the drive — its
tortoise fetches the full text live from the Internet Archive.

    python tools/card_archive_pd.py            # -> data/trades_cards.jsonl (reads the drive)
    python tools/card_archive_pd.py --check    # count + preview by discipline/language, write nothing
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

TEXTS_DB = os.environ.get("CONCORDANCE_ARCHIVE_DB", "").strip() or \
    "D:/NarrowHighway-Sources/archive_org/texts.db"
FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_trades"
_SUBJECT_RE = re.compile(r'subject:\(\s*"?([^)"]+?)"?\s*\)', re.I)


def discipline_of(query: str) -> str:
    m = _SUBJECT_RE.search(query or "")
    return re.sub(r"[^a-z0-9]+", "_", (m.group(1) if m else "trades").strip().lower()).strip("_") or "trades"


def language_of(title: str) -> str:
    """A light, honest heuristic — the title's own tongue where it shows, else english."""
    t = (title or "")
    tl = " " + t.lower() + " "
    if re.search(r"[äöüß]", t) or re.search(r"\b(der|die|das|und|für|technische|lehre|handbuch|über|kunst)\b", tl):
        return "german"
    if (re.search(r"[àâçéèêîôûœ]", t) or re.search(r"\b(le|la|les|des|du|au|aux|une|traité|manuel|nouvelle)\b", tl)
            or re.search(r"\b[ld]['’]", tl)):   # French elision: l'art, d'un
        return "french"
    if re.search(r"\b(de|et|liber|artis|opera|libri)\b", tl) and not re.search(r"\b(the|of|and|to)\b", tl):
        return "latin"
    if re.search(r"[áéíóúñ]", t) or re.search(r"\b(el|los|las|tratado|manual)\b", tl):
        return "spanish"
    return "english"


def rows():
    con = sqlite3.connect("file:" + TEXTS_DB + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    for r in con.execute("SELECT identifier,title,query,url,sha256,pd_year,pd_basis FROM docs_pd"):
        yield r
    con.close()


def card_for(r) -> dict:
    ident = r["identifier"]
    title = (r["title"] or ident or "Untitled").strip()
    disc = discipline_of(r["query"])
    lang = language_of(title)
    year = r["pd_year"]
    basis = (r["pd_basis"] or "public domain").strip()
    url = f"https://archive.org/details/{ident}"
    cid = "card_arch_" + hashlib.sha256((ident or title).encode("utf-8")).hexdigest()[:16]
    disc_h = disc.replace("_", " ")
    body = (f"{title} — a public-domain work on {disc_h}"
            + (f", published {year}" if year else "") + ". "
            + "Held in the ark; the full text is the TORTOISE — fetched on demand from the Internet "
            + f"Archive, not carried on board. Provenance: {basis}.")
    bands = [disc_h, "trades", "public domain", "pre-1929", lang]
    bands += [w for w in re.split(r"[^a-z0-9]+", title.lower()) if len(w) >= 4][:12]
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": f"Internet Archive — {ident} (public domain)", "url": url,
                   "domain": "trades", "authority_tier": "reference",
                   "identifier": ident, "sha256": r["sha256"], "pd_year": year, "pd_basis": basis,
                   "held": "external drive (durability mirror); served on demand via the tortoise",
                   "license": "public-domain"},
        "shelf": "trades", "box": disc,
        "bands": bands[:24], "subject": title, "language": lang,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": f"a public-domain {disc_h} work, catalogued"}],
        "author": "the trades catalogue (public domain, held in the ark)",
        "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
        "extra": {"discipline": disc, "language": lang, "tortoise": url, "held_off_board": True},
    }


def spine_card() -> dict:
    return {
        "id": SPINE, "kind": "reference",
        "title": "The trades — the practical arts, held in the ark",
        "body": ("The card catalogue of the public-domain practical arts — mechanics, carpentry, "
                 "masonry, blacksmithing, handicraft, industrial arts, agriculture — gathered from the "
                 "Internet Archive's pre-1929 texts (verified public domain). We hold the CATALOGUE; "
                 "the full texts stay on the drive and ship only on demand, the tortoise. Knowledge "
                 "spread across tongues, kept for the maker and the homesteader. Beside the field library."),
        "source": {"label": "The trades shelf (catalogue, public domain)", "url": "",
                   "domain": "trades", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["trades", "practical arts", "maker", "public domain", "archive", "field", "spine"],
        "subject": "the practical arts",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the practical arts, a spine of the Floor of Discovery"}],
        "author": "the trades catalogue", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }


def main() -> int:
    if not os.path.exists(TEXTS_DB):
        print(f"archive texts.db not found at {TEXTS_DB} (set CONCORDANCE_ARCHIVE_DB) — run where the drive is.",
              file=sys.stderr)
        return 2
    check = "--check" in sys.argv
    cards = [spine_card()]
    disc = Counter()
    lang = Counter()
    for r in rows():
        c = card_for(r)
        cards.append(c)
        disc[c["box"]] += 1
        lang[c["language"]] += 1
    print(f"catalogued {len(cards)-1} public-domain trades works (+1 spine)")
    print("  by discipline:", dict(disc.most_common(12)))
    print("  by language  :", dict(lang.most_common()))
    if check:
        print("\n  --check: nothing written. Sample:")
        for c in cards[1:6]:
            print(f"    · {c['title'][:56]}  [{c['box']}/{c['language']}] → {c['source']['url']}")
        return 0
    out = Path("data") / "trades_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"\n  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
