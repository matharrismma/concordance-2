#!/usr/bin/env python3
"""Card the original-language Scripture — the plumb-line. Academics first.

Matt, 2026-07-25: "Also, keep expanding the corpus. Academics first." And the standing mission:
"Everything through Hebrew and Greek. We are the tool to bring the academics and Jewish people to
Christ through logic and complete coherency." The stored HD sources hold the whole Bible in the
tongues it was given in — the Greek New Testament (greek.db, 137,554 words) and the Hebrew Bible
(hebrew.db, 306,785 words), word by word with Strong's numbers and lemmas.

This mints one card per VERSE (7,927 Greek + 23,213 Hebrew = 31,140) — the original text plus its
Strong's numbers, findable and rooted in the Word. Conduit, not source: each card is the verse as it
stands in the source, attributed, generated=False. Nested under a Greek/Hebrew spine → the Word (the
plumb-line roots in special revelation, not the Floor). The large card file is gitignored (like the
other stored-source cards); the two spines are git-tracked content. Re-runnable + idempotent.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_scripture.py
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

WORD = "card_k_spine_the_word"
_slug = re.compile(r"[^a-z0-9]+")

_OT = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
       "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
       "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
       "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
       "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
       "Malachi"]                                                     # book_num 1..39
_NT = ["Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
       "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
       "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
       "1 John", "2 John", "3 John", "Jude", "Revelation"]            # book_num 40..66


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _conn(name: str) -> sqlite3.Connection:
    dbs = list(_base().glob(f"{name}/*.db"))
    if not dbs:
        raise FileNotFoundError(f"no db under {name}")
    return sqlite3.connect(f"file:{dbs[0]}?mode=ro", uri=True)


def _spine(cid, title, body, bands):
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": "The original-language Scripture", "url": "", "domain": "", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": bands, "subject": title,
        "connections": [{"to_card_id": WORD, "relationship": "part_of",
                         "evidence": "Scripture in the original tongue, rooted in the Word"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


SPINES = [
    _spine("card_spine_greek_nt", "The Greek New Testament — SBLGNT",
           "Every verse of the New Testament in the Greek it was given in, word by word with Strong's "
           "numbers. The plumb-line for the academy and the church.",
           ["greek", "new testament", "sblgnt", "scripture", "original language", "spine"]),
    _spine("card_spine_hebrew_ot", "The Hebrew Bible — Westminster Leningrad Codex",
           "Every verse of the Hebrew Scriptures in the tongue they were given in, word by word with "
           "Strong's numbers. The Scriptures the Jewish people hold, measured true.",
           ["hebrew", "old testament", "tanakh", "leningrad", "scripture", "original language", "spine"]),
]


def _verses(source, col, books, base_num, shelf, spine, lang, source_label):
    c = _conn(source)
    cur = c.execute(
        f"select book_num,chapter,verse,{col},strongs,lemma from words order by book_num,chapter,verse,rowid")
    key = None
    words, strongs, lemmas = [], [], []

    def build():
        bk, ch, vs = key
        name = books[bk - base_num] if 0 <= bk - base_num < len(books) else f"Book {bk}"
        ref = f"{name} {ch}:{vs}"
        text = " ".join(words)
        uniq = list(dict.fromkeys(s for s in strongs if s))
        body = f"{text}  —  {ref} ({lang}, original). Strong's: {', '.join(uniq)}."
        card = {
            "id": f"card_src_{shelf}_{_sk(name, ch, vs)}", "kind": "reference",
            "title": f"{ref} ({lang})"[:180], "body": body,
            "source": {"label": source_label, "url": "", "domain": lang.lower(), "authority_tier": "reference"},
            "shelf": shelf, "box": "source",
            "bands": [name.lower(), f"chapter {ch}", lang.lower(), "original", "scripture"]
                     + [s.lower() for s in uniq][:20],
            "subject": ref,
            "connections": [{"to_card_id": spine, "relationship": "member_of",
                             "evidence": f"a verse of {lang} Scripture"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
            "extra": {"book": name, "book_num": bk, "chapter": ch, "verse": vs, "text": text,
                      "strongs": uniq, "lemmas": [l for l in lemmas if l]},
        }
        return card

    for bn, ch, vs, w, s, lem in cur:
        k = (bn, ch, vs)
        if k != key:
            if key is not None and words:
                yield build()
            key, words, strongs, lemmas = k, [], [], []
        if w:
            words.append(w)
        strongs.append(str(s) if s else "")
        lemmas.append(str(lem) if lem else "")
    if key is not None and words:
        yield build()
    c.close()


def main() -> int:
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    (out / "scripture_spines.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in SPINES) + "\n", encoding="utf-8")
    n = {"greek": 0, "hebrew": 0}
    tmp = out / "scripture_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for card in _verses("greek_nt", "grk", _NT, 40, "greek_nt", "card_spine_greek_nt", "Greek",
                            "SBLGNT — the Greek New Testament (Society of Biblical Literature; free use with attribution)"):
            f.write(json.dumps(card, ensure_ascii=False) + "\n"); n["greek"] += 1
        for card in _verses("hebrew_ot", "heb", _OT, 1, "hebrew_ot", "card_spine_hebrew_ot", "Hebrew",
                            "Westminster Leningrad Codex — the Hebrew Bible (public domain)"):
            f.write(json.dumps(card, ensure_ascii=False) + "\n"); n["hebrew"] += 1
    os.replace(tmp, out / "scripture_cards.jsonl")
    print(f"carded {n['greek']:,} Greek + {n['hebrew']:,} Hebrew = {sum(n.values()):,} verse cards "
          f"-> data/scripture_cards.jsonl  (+2 spines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
