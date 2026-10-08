#!/usr/bin/env python3
"""Card the etymologies — Webster's Revised Unabridged Dictionary (1913), the Project Gutenberg eBook
#29765, public domain. One card per headword that carries an "Etym: [...]" bracket: shelf "etymology",
id card_src_etym_<word>, the bracket text kept as the source wrote it (OCR warts and all), attributed.
Found and attributed, never generated.

Matt, 2026-10-08: "Etymology and phonics." Measured first: no shelf in the keeping carried a word's
origin (WordNet glosses, the partial Webster definitions and Easton carry none), so "salary comes from
Latin" could reach nothing. Webster 1913 writes the origin of ~53k headwords in its own abbreviations
(L. Latin, Gr. Greek, F. French, OF. Old French, AS. Anglo-Saxon, OE. Old English, Icel. Icelandic — the
Old Norse of the sagas, Ar. Arabic, Skr. Sanskrit ...); verifiers/wordcraft.verify_origin reads them.

    python -I tools/card_etymology.py --source /home/nh/ark_untrusted/webster1913/pg29765.txt
    python -I tools/card_etymology.py --source ... --dry-run          # stats and samples, nothing written

Writes <CONCORDANCE_DATA_DIR or data>/etymology_cards.jsonl: 1 spine (part_of the Floor) + the cards.
The source text is never committed (29 MB; the drive and the box's ark hold it).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
SPINE = "card_spine_etymology"
FLOOR = "card_k_floor_of_discovery"
SOURCE_LABEL = ("Webster's Revised Unabridged Dictionary (1913), Project Gutenberg eBook #29765 — public domain")
SOURCE_URL = "https://www.gutenberg.org/ebooks/29765"

_HEAD = re.compile(r"^[A-Z][A-Z0-9 '\-\.,;]*$")          # a headword line: ALL CAPS ("SALARY", "AB OVO")
_ETYM = re.compile(r"Etym:\s*\[")
_POS = re.compile(r"\b(v\. t\. & v\. i|v\. t|v\. i|p\. p|p\. pr|n\. pl|n|v|a|adv|prep|conj|interj|pron|pl)\.")
_slug = re.compile(r"[^a-z0-9]+")
ETYM_CAP = 700


def _sk(word: str) -> str:
    return _slug.sub("_", word.lower()).strip("_")


def _bracket(text: str, start: int) -> Tuple[str, int]:
    """The balanced bracket body beginning at text[start] == '['; returns (inner, end_index)."""
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i
        i += 1
    return text[start + 1:], len(text)


def parse_entries(text: str) -> Dict[str, List[Tuple[str, str]]]:
    """headword -> [(part of speech or '', etymology text)] for every entry that carries Etym: [...].
    An entry runs from a headword line to the next; the bracket may span lines (joined with spaces)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: Dict[str, List[Tuple[str, str]]] = {}
    head = None
    block: List[str] = []

    def flush():
        if head is None or not block:
            return
        body = " ".join(ln.strip() for ln in block)
        for m in _ETYM.finditer(body):
            inner, _end = _bracket(body, m.end() - 1)
            inner = re.sub(r"\s+", " ", inner).strip()
            if not inner:
                continue
            before = body[max(0, m.start() - 80):m.start()]
            # the part of speech follows the headword form (Sal"a*ry, n.; pl. Salaries.): the first POS after
            # the last marked form in the window, never the "pl." of the plural note
            forms = [fm.end() for fm in re.finditer(r"[A-Za-z\"*'\-]*[\"*][A-Za-z\"*'\-]*", before)]
            tail = before[forms[-1]:] if forms else before
            pm = [x for x in _POS.finditer(tail) if x.group(1) != "pl"]
            pos = pm[0].group(1) + "." if pm else ""
            pair = (pos, inner)
            if pair not in out.setdefault(head, []):
                out[head].append(pair)

    for ln in lines:
        s = ln.rstrip()
        if s and _HEAD.match(s) and len(s) <= 60 and not s.startswith("*** "):
            flush()
            head, block = s.strip(), []
        elif head is not None:
            block.append(s)
    flush()
    return out


def etym_body(word: str, etyms: List[Tuple[str, str]]) -> str:
    parts = []
    for pos, et in etyms[:4]:
        et = et.replace("[", "(").replace("]", ")")            # the body's brackets delimit the etymologies
        if len(et) > ETYM_CAP:
            et = et[:ETYM_CAP].rstrip() + "…"
        parts.append((f"{pos}: " if pos else "") + "[" + et + "]")
    # the abbreviation key lives ONCE, on the spine card (49k copies of it would be 25 MB of the same sentence);
    # the verifier's detail names the convention beside every verdict
    return f"{word}: etymology (Webster 1913) — " + "; ".join(parts) + ". From Webster's Revised Unabridged Dictionary (1913), public domain."


def spine_card(n: int) -> dict:
    return {
        "id": SPINE, "kind": "reference", "title": "The etymologies — where the words came from",
        "body": (f"The origin of {n:,} English headwords as Webster's Revised Unabridged Dictionary (1913) wrote "
                 "them: the languages and forms each word came through, in Webster's own abbreviations. "
                 "Public domain (Project Gutenberg eBook #29765). Found and attributed, never generated; the "
                 "wordcraft verifier reads these cards to judge 'X comes from Latin'. Webster's abbreviations: "
                 "L. Latin, LL. Late Latin, NL. New Latin, Gr. Greek, F. French, OF. Old French, AS. Anglo-Saxon, "
                 "OE. Old English, ME. Middle English, Icel. Icelandic (the Old Norse of the sagas), G. German, "
                 "OHG. Old High German, MHG. Middle High German, D. Dutch, LG. Low German, Goth. Gothic, Dan. Danish, "
                 "Sw. Swedish, It. Italian, Sp. Spanish, Pg. Portuguese, Pr. Provençal, Ar. Arabic, Heb. Hebrew, "
                 "Chald. Chaldee, Syr. Syriac, Per. Persian, Skr. Sanskrit, Hind. Hindustani, Turk. Turkish, "
                 "Russ. Russian, W. Welsh, Ir. Irish, Gael. Gaelic, Chin. Chinese, Jap. Japanese; 'cf.' and "
                 "'akin to' compare cognates, they do not derive."),
        "source": {"label": SOURCE_LABEL, "url": SOURCE_URL, "domain": "linguistics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["etymology", "origin", "words", "language", "webster", "spine"],
        "subject": "The etymologies",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "a spine of the corpus, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def card(head: str, etyms: List[Tuple[str, str]]) -> dict:
    word = head.lower()
    return {
        "id": f"card_src_etym_{_sk(word)}", "kind": "reference", "title": word[:180],
        "body": etym_body(word, etyms),
        "source": {"label": SOURCE_LABEL, "url": SOURCE_URL, "domain": "linguistics", "authority_tier": "reference"},
        "shelf": "etymology", "box": "source",
        "bands": [word, "etymology", "origin", "webster", "language"],
        "subject": word,
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "an entry of Webster 1913 that states the word's origin"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="the Gutenberg pg29765.txt (Webster's Unabridged, 1913)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    src = Path(args.source)
    if not src.exists():
        print(f"missing {src}")
        return 2
    text = src.read_text(encoding="utf-8", errors="replace")
    if "Webster's Unabridged Dictionary" not in text[:4000]:
        print("the source does not look like the Gutenberg Webster's Unabridged — refusing")
        return 2
    entries = parse_entries(text)
    cards = [card(h, e) for h, e in entries.items() if _sk(h)]
    seen: Dict[str, int] = {}
    for c in cards:
        cid = c["id"]
        if cid in seen:
            seen[cid] += 1
            c["id"] = f"{cid}_{seen[cid]}"
        else:
            seen[cid] = 0
    n_ety = sum(len(e) for e in entries.values())
    print(f"headwords with an etymology: {len(entries):,}; etymologies: {n_ety:,}; cards: {len(cards):,} (+1 spine)")
    for w in ("SALARY", "STRENGTH", "WINDOW", "ALGEBRA", "MUSCLE"):
        if w in entries:
            print(f"  {w}: {entries[w][0][0]} {entries[w][0][1][:110]}")
    if args.dry_run:
        print("--dry-run: nothing written.")
        return 0
    base = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
    out = base / "etymology_cards.jsonl"
    tmp = out.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:      # the same bytes on every platform
        f.write(json.dumps(spine_card(len(cards)), ensure_ascii=False) + "\n")
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    if out.exists():
        old_n = sum(1 for _ in open(out, encoding="utf-8"))
        if len(cards) + 1 < old_n and "--shrink-ok" not in sys.argv:
            print(f"REFUSING to replace: new {len(cards) + 1:,} < held {old_n:,} — the keeping stays")
            tmp.unlink()
            return 1
    os.replace(tmp, out)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
