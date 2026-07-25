#!/usr/bin/env python3
"""Card four more stored sources — RFCs, commentary, sermons, activities. Keep pushing.

Matt: "Keep pushing." Four well-licensed, high-value sources still un-carded on the HD:
  - RFCs (9,777)      — the internet standards (RFC Editor / IETF, public domain). Technical.
  - commentary (4,124)— Matthew Henry's Bible commentary (public domain / CC0). On-mission.
  - sermons (422)     — C.H. Spurgeon's sermons, indexed by passage (public domain). On-mission.
  - activities (821)  — the 2011 Compendium of Physical Activities (MET intensities). Health.

Conduit, not source: each card is a real source row, attributed, generated=False. Scripture
commentary + sermons root in the Word; RFCs + activities root in the Floor. Card file gitignored;
the four spines are git-tracked. Re-runnable.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_reference.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
WORD = "card_k_spine_the_word"
_slug = re.compile(r"[^a-z0-9]+")

_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
          "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
          "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
          "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
          "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
          "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
          "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
          "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
          "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"]   # book_num 1..66


def _bk(n):
    return _BOOKS[n - 1] if 1 <= n <= len(_BOOKS) else f"Book {n}"


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _conn(name):
    return sqlite3.connect(f"file:{glob.glob(str(_base()/name/'*.db'))[0]}?mode=ro", uri=True)


def _spine(cid, title, body, parent, bands):
    return {"id": cid, "kind": "reference", "title": title, "body": body,
            "source": {"label": title, "url": "", "domain": "", "authority_tier": "reference"},
            "shelf": "spine", "box": "spine", "bands": bands, "subject": title,
            "connections": [{"to_card_id": parent, "relationship": "part_of", "evidence": "a spine of the corpus"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False}


def _card(cid, title, body, shelf, subject, bands, source_label, url, spine, domain, extra):
    return {"id": cid, "kind": "reference", "title": title[:180], "body": body[:4000],
            "source": {"label": source_label, "url": url, "domain": domain, "authority_tier": "reference"},
            "shelf": shelf, "box": "source", "bands": bands, "subject": subject,
            "connections": [{"to_card_id": spine, "relationship": "member_of", "evidence": f"a member of {shelf}"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False, "extra": extra}


SPINES = [
    _spine("card_spine_rfcs", "The internet standards — the RFCs",
           "Every Request for Comments: the documents that define how the networked world actually "
           "works, from RFC 1 (1969) forward. A spine of the Floor of Discovery.", FLOOR,
           ["rfc", "internet", "standards", "ietf", "networking", "spine"]),
    _spine("card_spine_commentary", "Matthew Henry's Commentary on the whole Bible",
           "The classic public-domain verse-by-verse commentary — the Body's long meditation on the "
           "Word, gathered. Not Scripture; a help toward it.", WORD,
           ["commentary", "matthew henry", "exposition", "scripture", "spine"]),
    _spine("card_spine_sermons", "The sermons — C.H. Spurgeon, by passage",
           "Spurgeon's sermons indexed to the passages they open — the Word preached, findable by "
           "verse. Public domain.", WORD,
           ["sermons", "spurgeon", "preaching", "scripture", "spine"]),
    _spine("card_spine_activities", "The Compendium of Physical Activities",
           "The measured energy cost (METs) of hundreds of activities — a reference for the keeping "
           "of the body. A spine of the Floor of Discovery.", FLOOR,
           ["activities", "exercise", "met", "fitness", "body", "spine"]),
]


def gen():
    # RFCs
    for num, doc_id, title, status, date, obs, obs_by, upd, upd_by in _conn("protocols").execute(
            "select num,doc_id,title,status,date,obsoletes,obsoleted_by,updates,updated_by from rfcs"):
        body = (f"{doc_id}: {title} ({date}). Status: {status}."
                + (f" Obsoleted by {obs_by}." if obs_by else "") + (f" Obsoletes {obs}." if obs else ""))
        yield _card(f"card_src_rfc_{num}", f"{doc_id} — {title}", body, "rfcs", doc_id,
                    [doc_id.lower(), "rfc", "internet", "standard", "networking", str(status).lower()],
                    "The RFC Index (RFC Editor / IETF) — public domain", f"https://www.rfc-editor.org/rfc/rfc{num}",
                    "card_spine_rfcs", "networking",
                    {"num": num, "status": status, "date": date, "obsoletes": obs, "obsoleted_by": obs_by,
                     "updates": upd, "updated_by": upd_by})
    # Matthew Henry commentary
    for bn, ch, vs, text in _conn("commentary").execute(
            "select book_num,chapter,verse_start,text from notes"):
        ref = f"{_bk(bn)} {ch}:{vs}"
        yield _card(f"card_src_comm_{_sk(_bk(bn), ch, vs)}", f"Matthew Henry on {ref}",
                    f"On {ref} — {str(text or '').strip()}", "commentary", ref,
                    [_bk(bn).lower(), f"chapter {ch}", "commentary", "matthew henry", "exposition"],
                    "Matthew Henry's Commentary (public domain) — via the Free Use Bible API", "",
                    "card_spine_commentary", "theology",
                    {"book": _bk(bn), "chapter": ch, "verse": vs})
    # Spurgeon sermons
    for bn, ch, vs, title, ref, url, author in _conn("sermons").execute(
            "select book_num,chapter,verse,title,reference,source_url,author from sermons"):
        yield _card(f"card_src_sermon_{_sk(_bk(bn), ch, vs, title)}"[:120],
                    f"{title} — {author} ({ref})",
                    f"A sermon by {author} on {ref}: “{title}.”", "sermons", str(title),
                    [_bk(bn).lower(), "sermon", "spurgeon", "preaching", str(ref).lower()],
                    "C.H. Spurgeon (1834-1892), public domain; index via spurgeongems.org", str(url or ""),
                    "card_spine_sermons", "theology",
                    {"reference": ref, "author": author, "source_url": url, "book": _bk(bn)})
    # METs / activities
    for code, met, cat, desc in _conn("mets").execute("select code,met,category,description from activities"):
        yield _card(f"card_src_met_{_sk(code)}", f"{desc} — {met} METs",
                    f"{desc} ({cat}) — {met} METs, the energy cost of the activity (metabolic equivalents, "
                    f"where 1 MET is resting).", "activities", str(desc),
                    [str(cat).lower(), "activity", "exercise", "met", "fitness", "energy"],
                    "2011 Compendium of Physical Activities (Ainsworth BE et al.)", "",
                    "card_spine_activities", "exercise_science",
                    {"code": code, "met": met, "category": cat})


def main() -> int:
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    (out / "reference_extra_spines.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in SPINES) + "\n", encoding="utf-8")
    n = 0
    seen = set()
    tmp = out / "reference_extra_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for card in gen():
            if card["id"] in seen:
                continue
            seen.add(card["id"])
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "reference_extra_cards.jsonl")
    print(f"carded {n:,} reference cards (RFCs + commentary + sermons + activities) "
          f"-> data/reference_extra_cards.jsonl  (+{len(SPINES)} spines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
