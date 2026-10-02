#!/usr/bin/env python3
"""Card the PRINCIPLES of those who repeatedly won — from their own public-domain words.

Matt, 2026-10-02: "figures like Napoleon, Churchill, and Ford … principles and patterns that have
repeatedly been proven successful. We need a mechanism to identify and tag those principles."

The mechanism is `concordance.principles` (identify → tag → prove → apply). This tool is its minting
pass: for each SOURCE below (a public-domain work on Project Gutenberg, named with its PD basis), it
reads the text, identifies maxim-shaped sentences (and author-labelled maxims), tags each to the
Strategy Concordance's patterns, and writes `data/principle_cards.jsonl` — GIT-TRACKED, small, every
card verbatim and attributed (figure, work, year, Gutenberg #, URL). Regenerable; `--check` audits.

Strict PD: only works public domain in the US (pre-1930 publication, or an author-released
translation). Churchill is represented by his 1909 book, not his later speeches (not PD).

    python tools/card_principles.py --fetch            # download the texts to data/pd_texts/ (gitignored)
    python tools/card_principles.py --mint             # (re)write data/principle_cards.jsonl
    python tools/card_principles.py --check            # counts, untagged, per-pattern proof
    python tools/card_principles.py --apply "we are small and the incumbent is slow"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import principles as P  # noqa: E402

TEXTS = ROOT / "data" / "pd_texts"
STORE = ROOT / "data" / "principle_cards.jsonl"
SPINE_ID = "card_spine_principles"
STRATEGY_SPINE = "card_spine_strategy"
UA = "concordance-2 (public-domain gathering)"

# figure, work, year, Gutenberg #, arena, PD basis, per-source cap
SOURCES = [
    ("Napoleon Bonaparte", "The Officer's Manual: Napoleon's Maxims of War (tr. D'Aguilar)", 1831, 50750, "war",
     "author d. 1821; translation 1831 — public domain", 78),
    ("Henry Ford", "My Life and Work", 1922, 7213, "business", "published 1922 — public domain in the US", 40),
    ("Benjamin Franklin", "The Autobiography of Benjamin Franklin", 1791, 148, "politics", "author d. 1790 — public domain", 30),
    ("Marcus Aurelius", "Meditations (tr. George Long)", 1862, 2680, "wisdom", "author d. 180; translation 1862 — public domain", 30),
    ("Sun Tzu", "The Art of War (tr. Lionel Giles)", 1910, 132, "war", "translation 1910 — public domain", 30),
    ("Carl von Clausewitz", "On War (tr. J. J. Graham)", 1873, 1946, "war", "translation 1873 — public domain", 30),
    ("Andrew Carnegie", "Autobiography of Andrew Carnegie", 1920, 17976, "business", "published 1920 — public domain in the US", 30),
    ("Winston Churchill", "Liberalism and the Social Problem", 1909, 18419, "politics", "published 1909 — public domain", 25),
    ("Theodore Roosevelt", "Theodore Roosevelt: An Autobiography", 1913, 3335, "politics", "published 1913 — public domain", 30),
    # 2026-10-02, Matt: "add Lincoln, Washington, and the other similar greats. Gather wisdom."
    ("Abraham Lincoln", "The Papers and Writings of Abraham Lincoln (complete)", 1865, 3253, "politics", "author d. 1865 — public domain", 120),
    ("George Washington", "Rules of Civility & Decent Behaviour in Company and Conversation (the 110 rules)", 1747, 12029, "politics", "author d. 1799 — public domain", 40),
    ("Thomas Jefferson", "The Writings of Thomas Jefferson", 1826, 21002, "politics", "author d. 1826 — public domain", 30),
    ("Ulysses S. Grant", "Personal Memoirs of U. S. Grant", 1885, 4367, "war", "published 1885 — public domain", 30),
    ("William T. Sherman", "Memoirs of General William T. Sherman", 1875, 4361, "war", "published 1875 — public domain", 30),
    ("Niccolò Machiavelli", "The Prince (tr. W. K. Marriott)", 1908, 1232, "politics", "translation 1908 — public domain", 30),
    ("Julius Caesar", "Commentaries on the Gallic War (tr. McDevitte & Bohn)", 1869, 10657, "war", "translation 1869 — public domain", 25),
    ("Thucydides", "The History of the Peloponnesian War (tr. Richard Crawley)", 1874, 7142, "war", "translation 1874 — public domain", 30),
    ("Epictetus", "The Enchiridion (tr. Elizabeth Carter)", 1758, 45109, "wisdom", "translation 1758 — public domain", 25),
    ("Seneca", "Seneca's Morals of a Happy Life, Benefits, Anger and Clemency (tr. L'Estrange)", 1678, 56075, "wisdom", "translation 1678 — public domain", 30),
    ("Confucius", "The Analects (tr. James Legge)", 1861, 3330, "wisdom", "translation 1861 — public domain", 30),
    ("Plutarch", "Lives of the Noble Grecians and Romans (tr. Dryden, rev. Clough)", 1864, 674, "wisdom", "translation 1864 — public domain", 50),
    ("Antoine-Henri Jomini", "The Art of War (tr. Mendell & Craighill)", 1862, 13549, "war", "translation 1862 — public domain", 30),
    ("Alfred Thayer Mahan", "The Influence of Sea Power Upon History, 1660-1783", 1890, 13529, "war", "published 1890 — public domain", 25),
]

# Author-LABELLED maxims: a source whose author numbered his rules — accepted by construction.
# gutenberg id -> (heading regex, block terminator regex or None)
LABELLED = {
    50750: (r"^MAXIM [IVXLC]+\.?\s*$", r"\nNOTE"),                 # Napoleon: MAXIM I. … NOTE.
    12029: (r"^\d{1,3}(?:st|nd|rd|d|th)\.\s+", None),               # Washington: "1st. Every Action…" … "110th." (column 0, with the period — the editor's genealogy says "1st, Ester" and must not split)
}

_MAXIM = re.compile(r"^MAXIM [IVXLC]+\.?\s*$", re.M)
_GUT_START = re.compile(r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\n")
_GUT_END = re.compile(r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _body_of(raw: str) -> str:
    m = _GUT_START.search(raw)
    s = raw[m.end():] if m else raw
    e = _GUT_END.search(s)
    return s[: e.start()] if e else s


def _labelled_blocks(text: str, gid: int) -> list:
    """The author's own numbered maxims/rules: the block after each heading, up to the terminator (if
    any) or the next heading. Napoleon's MAXIM I. … NOTE.; Washington's 1st … 110th."""
    spec = LABELLED.get(gid)
    if not spec:
        return []
    head_re, term = spec
    parts = re.split(head_re, text, flags=re.M)
    out = []
    for blk in parts[1:]:
        if term:
            blk = re.split(term, blk, maxsplit=1)[0]
        blk = blk.strip()
        if blk:
            out.append(blk)
    return out


def fetch() -> None:
    TEXTS.mkdir(parents=True, exist_ok=True)
    for _fig, _work, _year, gid, *_ in SOURCES:
        dest = TEXTS / f"pg{gid}.txt"
        if dest.exists() and dest.stat().st_size > 10_000:
            continue
        url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
        print(f"fetched #{gid} -> {dest}")


def _card(cid, kind, title, body, box, bands, subject, conns, extra, source):
    return {"id": cid, "kind": kind, "title": title[:180], "body": body, "source": source,
            "shelf": "strategy", "box": box, "bands": bands, "subject": subject, "connections": conns,
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
            "extra": extra}


def build_cards(texts_dir: Path = TEXTS) -> list:
    cards = [_card(SPINE_ID, "reference", "The principles of those who won — in their own words",
                   "The stated rules of figures who repeatedly succeeded — Napoleon, Lincoln, Washington, Ford, "
                   "Franklin, Jefferson, Grant, Sherman, Caesar, Thucydides, Machiavelli, Jomini, Mahan, Sun Tzu, "
                   "Clausewitz, Carnegie, Churchill, Roosevelt, and the wisdom of Marcus Aurelius, Epictetus, Seneca, "
                   "Confucius and Plutarch — gathered verbatim from their "
                   "public-domain works, each tagged to the patterns of the Strategy Concordance so that 'repeatedly "
                   "proven' is a count (distinct figures, arenas, dated cases), and applied to a present situation "
                   "by the same resolution. Who said it, where it won, where to read it — the discernment stays yours.",
                   "spine", ["strategy", "principles", "spine"], "the principles of those who won",
                   [{"to_card_id": STRATEGY_SPINE, "relationship": "part_of",
                     "evidence": "the principles shelf of the Strategy Concordance"}],
                   {"span": "history"},
                   {"label": "The principles of those who won — public-domain words, attributed", "url": "",
                    "domain": "strategy", "authority_tier": "reference"})]
    for fig, work, year, gid, arena, pd_basis, cap in SOURCES:
        p = texts_dir / f"pg{gid}.txt"
        if not p.exists():
            print(f"  missing text for {fig} (#{gid}) — run --fetch", file=sys.stderr)
            continue
        text = _body_of(p.read_text(encoding="utf-8", errors="replace"))
        blocks = _labelled_blocks(text, gid) or None
        found = P.identify(text, labelled_blocks=blocks, limit=cap)
        url = f"https://www.gutenberg.org/ebooks/{gid}"
        for i, f in enumerate(found, 1):
            h = hashlib.sha1(f["quote"].encode("utf-8")).hexdigest()[:10]
            pats = sorted(f["patterns"])
            conns = [{"to_card_id": SPINE_ID, "relationship": "member_of",
                      "evidence": f"a principle stated by {fig} in {work} ({year})"}]
            for pid in pats:
                conns.append({"to_card_id": f"card_pattern_{pid}", "relationship": "instance_of",
                              "evidence": f"names the move: {', '.join(f['patterns'][pid])}"})
            cards.append(_card(
                f"card_principle_{_slug(fig)}_{h}", "principle",
                f"{fig}: {f['quote'][:110]}", f["quote"], "principle",
                ["strategy", "principle", arena, _slug(fig)] + pats + (["untagged"] if not pats else []),
                fig, conns,
                {"figure": fig, "work": work, "year": year, "gutenberg": gid, "arena": arena,
                 "patterns": pats, "stems": f["patterns"], "cues": f["cues"], "labelled": f["labelled"],
                 "pd_basis": pd_basis},
                {"label": f"{fig}, {work} ({year}) — Project Gutenberg #{gid}, public domain", "url": url,
                 "domain": "strategy", "authority_tier": "primary"}))
    return cards


def cmd_mint() -> int:
    cards = build_cards()
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE, "w", encoding="utf-8", newline="\n") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    n = sum(1 for c in cards if c["kind"] == "principle")
    print(f"minted {n} principles (+1 spine) -> {STORE}")
    return 0


def cmd_check() -> int:
    cards = [c for c in P.load_principles(ROOT / "data")]
    if not cards:
        print("no principle cards — run --mint"); return 3
    ids = [c["id"] for c in cards]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print("duplicate ids:", dup[:5]); return 3
    by_fig = {}
    for c in cards:
        by_fig.setdefault(c["extra"]["figure"], []).append(c)
    untagged = [c for c in cards if not c["extra"]["patterns"]]
    print(f"{len(cards)} principles from {len(by_fig)} figures; {len(untagged)} untagged "
          f"({100*len(untagged)//max(1,len(cards))}%)")
    for fig, cs in sorted(by_fig.items()):
        print(f"  {fig:22s} {len(cs):3d}  untagged {sum(1 for c in cs if not c['extra']['patterns'])}")
    pats, cases = P.load_patterns(ROOT / "data")
    print("per-pattern proof (figures / arenas / cases; proven = ≥2 figures AND ≥2 arenas):")
    for pid in sorted(P.PATTERN_LEXICON):
        pr = P.proof(pid, cards, cases)
        flag = "PROVEN" if pr["proven"] else "      "
        print(f"  {flag} {pid:26s} figures {pr['figures']:2d} arenas {len(pr['arenas'])} cases {pr['cases']:2d}  {', '.join(pr['who'])[:70]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--mint", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", metavar="SITUATION")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.mint:
        cmd_mint()
    if a.check:
        return cmd_check()
    if a.apply:
        print(json.dumps(P.apply(a.apply, data_dir=ROOT / "data"), ensure_ascii=False, indent=1)[:6000])
    if not (a.fetch or a.mint or a.check or a.apply):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
