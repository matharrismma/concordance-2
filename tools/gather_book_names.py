#!/usr/bin/env python3
"""THE WORD IN THE READER'S TONGUE (Gen 3 · 4) — gather the 66 books' names in every held language.

Gathered, never authored: the names come from Wikidata (CC0) — each book's item found by its English name
with a Bible disambiguation, VERIFIED by its description (Bible / Testament / gospel / epistle / book of …),
then its labels and aliases read in the languages this node holds a Bible for (data/bible_<lang>.jsonl).
Writes data/bible_book_names.json:

    {"gathered_at": …, "source": "wikidata (CC0)", "qids": {"John": "Q36766", …},
     "names": {"es": {"juan": "John", "evangelio de juan": "John", …}, "zh": {...}, …}}

Keys are normalised (casefold, punctuation stripped); values are the English canonical book names the reader
already resolves. A language missing a book is REPORTED, never filled in by hand.

    PYTHONPATH=src python tools/gather_book_names.py            # gather for every held language
    PYTHONPATH=src python tools/gather_book_names.py --langs es zh
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
API = "https://www.wikidata.org/w/api.php"
UA = "narrowhighway-gather/1 (public-domain Bible book names; https://narrowhighway.org)"

# How each English canonical name is searched (the disambiguation is the search string; the match is
# VERIFIED by the item's description, never trusted from the search alone).
_SEARCH = {
    "Genesis": "Book of Genesis", "Exodus": "Book of Exodus", "Leviticus": "Book of Leviticus",
    "Numbers": "Book of Numbers", "Deuteronomy": "Book of Deuteronomy", "Joshua": "Book of Joshua",
    "Judges": "Book of Judges", "Ruth": "Book of Ruth", "1 Samuel": "Books of Samuel", "2 Samuel": "Books of Samuel",
    "1 Kings": "Books of Kings", "2 Kings": "Books of Kings", "1 Chronicles": "Books of Chronicles",
    "2 Chronicles": "Books of Chronicles", "Ezra": "Book of Ezra", "Nehemiah": "Book of Nehemiah",
    "Esther": "Book of Esther", "Job": "Book of Job", "Psalms": "Psalms", "Proverbs": "Book of Proverbs",
    "Ecclesiastes": "Ecclesiastes", "Song of Solomon": "Song of Songs", "Isaiah": "Book of Isaiah",
    "Jeremiah": "Book of Jeremiah", "Lamentations": "Book of Lamentations", "Ezekiel": "Book of Ezekiel",
    "Daniel": "Book of Daniel", "Hosea": "Book of Hosea", "Joel": "Book of Joel", "Amos": "Book of Amos",
    "Obadiah": "Book of Obadiah", "Jonah": "Book of Jonah", "Micah": "Book of Micah", "Nahum": "Book of Nahum",
    "Habakkuk": "Book of Habakkuk", "Zephaniah": "Book of Zephaniah", "Haggai": "Book of Haggai",
    "Zechariah": "Book of Zechariah", "Malachi": "Book of Malachi",
    "Matthew": "Gospel of Matthew", "Mark": "Gospel of Mark", "Luke": "Gospel of Luke", "John": "Gospel of John",
    "Acts": "Acts of the Apostles", "Romans": "Epistle to the Romans", "1 Corinthians": "First Epistle to the Corinthians",
    "2 Corinthians": "Second Epistle to the Corinthians", "Galatians": "Epistle to the Galatians",
    "Ephesians": "Epistle to the Ephesians", "Philippians": "Epistle to the Philippians",
    "Colossians": "Epistle to the Colossians", "1 Thessalonians": "First Epistle to the Thessalonians",
    "2 Thessalonians": "Second Epistle to the Thessalonians", "1 Timothy": "First Epistle to Timothy",
    "2 Timothy": "Second Epistle to Timothy", "Titus": "Epistle to Titus", "Philemon": "Epistle to Philemon",
    "Hebrews": "Epistle to the Hebrews", "James": "Epistle of James", "1 Peter": "First Epistle of Peter",
    "2 Peter": "Second Epistle of Peter", "1 John": "First Epistle of John", "2 John": "Second Epistle of John",
    "3 John": "Third Epistle of John", "Jude": "Epistle of Jude", "Revelation": "Book of Revelation",
}
_BIBLE_WORDS = ("bible", "testament", "gospel", "epistle", "book of", "books of", "hebrew", "tanakh", "canonical", "psalms",
                "letter", "apostle")
_SPLIT = {"1 Samuel": ("Books of Samuel", 1), "2 Samuel": ("Books of Samuel", 2), "1 Kings": ("Books of Kings", 1),
          "2 Kings": ("Books of Kings", 2), "1 Chronicles": ("Books of Chronicles", 1), "2 Chronicles": ("Books of Chronicles", 2)}


def _get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(dict(params, format="json"))
    req = urllib.request.Request(url, headers={"user-agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:   # noqa: S310 — a known public CC0 endpoint
        return json.loads(r.read().decode("utf-8"))


def norm(s: str) -> str:
    """casefold; strip accents, Hebrew points and Arabic harakat; punctuation to space — the same rule as
    scripture._norm_name, so "Génesis", "genesis" and "GÉNESIS" are one key."""
    import unicodedata
    s = unicodedata.normalize("NFKD", (s or "").casefold())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[֑-ׇ]", "", s)                         # Hebrew points
    s = re.sub(r"[ً-ْٰ]", "", s)                   # Arabic harakat
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def find_qid(english: str) -> tuple:
    """(qid, label, description) for a book, verified by its description; (None, why) when not found."""
    search = _SEARCH.get(english, english)
    try:
        res = _get({"action": "wbsearchentities", "search": search, "language": "en", "type": "item", "limit": 8})
    except Exception as e:  # noqa: BLE001
        return None, f"search failed: {e}"
    for hit in res.get("search") or []:
        desc = (hit.get("description") or "").lower()
        label = (hit.get("label") or "")
        if any(w in desc for w in _BIBLE_WORDS) and "film" not in desc and "album" not in desc and "song" not in desc:
            return hit["id"], label, desc
    return None, f"no verified item among {[h.get('label') for h in (res.get('search') or [])][:5]}"


def labels_for(qids: list, langs: list) -> dict:
    out = {}
    for i in range(0, len(qids), 40):
        chunk = qids[i:i + 40]
        res = _get({"action": "wbgetentities", "ids": "|".join(chunk), "props": "labels|aliases",
                    "languages": "|".join(langs)})
        for qid, ent in (res.get("entities") or {}).items():
            out[qid] = {"labels": {k: v["value"] for k, v in (ent.get("labels") or {}).items()},
                        "aliases": {k: [a["value"] for a in v] for k, v in (ent.get("aliases") or {}).items()}}
        time.sleep(0.5)
    return out


def held_languages() -> list:
    return sorted(p.stem[len("bible_"):] for p in DATA.glob("bible_*.jsonl") if p.stem[len("bible_"):] != "en")


def main() -> int:
    a = sys.argv[1:]
    langs = a[a.index("--langs") + 1:] if "--langs" in a else held_languages()
    if not langs:
        print("no held languages (data/bible_<lang>.jsonl) — nothing to gather")
        return 2
    from concordance.strongs.concordance import BOOK_NAMES
    books = [BOOK_NAMES[k] for k in sorted(BOOK_NAMES)]
    qids, misses = {}, {}
    for b in books:
        qid, *rest = find_qid(b)
        if qid:
            qids[b] = qid
        else:
            misses[b] = rest[0]
        time.sleep(0.3)
    print(f"items found: {len(qids)}/{len(books)}" + (f"; not found: {misses}" if misses else ""))
    # Wikidata keeps Chinese under zh, zh-hans and zh-hant (the CUV we hold is simplified): gather all three
    # into "zh"; the normaliser treats them as one language.
    wd_langs = sorted(set(langs) | ({"zh-hans", "zh-hant"} if "zh" in langs else set()))
    ents = labels_for(sorted(set(qids.values())), wd_langs)
    names = {lang: {} for lang in langs}
    missing = {lang: [] for lang in langs}
    for b, qid in qids.items():
        ent = ents.get(qid) or {}
        for lang in langs:
            variants = [lang] + (["zh-hans", "zh-hant"] if lang == "zh" else [])
            label = next(((ent.get("labels") or {}).get(v) for v in variants if (ent.get("labels") or {}).get(v)), None)
            als = [a for v in variants for a in ((ent.get("aliases") or {}).get(v) or [])]
            als += [(ent.get("labels") or {}).get(v) for v in variants[1:] if (ent.get("labels") or {}).get(v)]
            if not label and not als:
                missing[lang].append(b)
                continue
            n = int(b[0]) if b[:1].isdigit() and b in _SPLIT else None
            for raw in ([label] if label else []) + als:
                key = norm(raw)
                if not key:
                    continue
                # an abbreviation in Latin script shorter than three letters ("Is", "Am", "Mt") is prose, not a
                # name: "what is 2 + 2" became Isaiah 2 in French on the first live run (2026-10-05)
                if re.fullmatch(r"[a-z ]+", key) and len(key.replace(" ", "")) < 3:
                    continue
                if n and b in _SPLIT:
                    # "Books of Samuel" is one item for two books: the shared name is kept NUMBERED only
                    names[lang][f"{n} {key}"] = b
                else:
                    names[lang][key] = b
    # THE SHORT NAMES, DERIVED NOT AUTHORED: a reader writes "Juan 3:16", not "Evangelio de Juan 3:16". For each
    # language, a token that occurs in one book's names and in no other book's is that book's short name; a token
    # shared only with the book's numbered siblings ("juan": John, 1 John, 2 John, 3 John) names the unnumbered
    # book, and "<n> token" names each sibling. Nothing is typed in: the tokens are Wikidata's own words.
    books_by_eng = {}
    for lang in langs:
        # token -> {root book: how many of that root's names carry the token}; numbered siblings fold into
        # their root ("1 John" -> "John"), the way the English reader already treats a bare "John".
        tok_hits, root_names = {}, {}
        for key, eng in names[lang].items():
            root = eng[2:] if eng[:1].isdigit() and eng[1:2] == " " else eng
            root_names[root] = root_names.get(root, 0) + 1
            for tok in set(key.split()):
                if tok.isdigit() or len(tok) < 2 or (tok.isascii() and len(tok) < 3):
                    continue                                              # the same rule as the raw keys: no short Latin fragments
                tok_hits.setdefault(tok, {}).setdefault(root, 0)
                tok_hits[tok][root] += 1
        for tok, by_root in tok_hits.items():
            # the token names the root in whose names it appears MOST (as a share of that root's names);
            # "juan" is in most of John's names and in a few of Revelation's ("Apocalipsis de Juan")
            scored = sorted(((cnt / root_names[r], r) for r, cnt in by_root.items()), reverse=True)
            best_share, best = scored[0]
            runner = scored[1][0] if len(scored) > 1 else 0.0
            if best_share < 0.5 or runner >= 0.5:
                continue
            if best in books:                                            # a bare name means the unnumbered book …
                names[lang][tok] = best                                  # … and a derived short name overrides an alias collision
            for eng in {e for e in names[lang].values() if e[:1].isdigit() and e[2:] == best}:
                names[lang].setdefault(f"{eng[0]} {tok}", eng)           # "1 samuel", "2 juan": the numbered siblings
        books_by_eng[lang] = len({v for v in names[lang].values()})
    for lang in langs:
        print(f"  {lang}: {len(names[lang])} names for {books_by_eng[lang]} books" + (f"; missing {len(missing[lang])}: {missing[lang][:6]}" if missing[lang] else ""))
    out = {"gathered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "wikidata (CC0)",
           "languages": langs, "qids": qids, "names": names, "missing": {k: v for k, v in missing.items() if v}}
    p = DATA / "bible_book_names.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
