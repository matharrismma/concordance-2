#!/usr/bin/env python3
"""Card the OpenStax open textbooks — CC-BY 4.0, purposefully free, modern reference substance.

Matt, 2026-09-26: broaden the gate to PD + CC0 + CC-BY (attribution honored), and grow the reference
section with "mathematics and theory" + a full encyclopedia of practical wisdom. OpenStax is exactly
that: ~129 college textbooks (calculus, physics, chemistry, biology, astronomy, anatomy, economics,
government, …) released CC-BY 4.0 — free to reuse WITH attribution, which is how the keeping already
works (every card keeps its source). So we GATHER, credit, and never author.

The FRONT-LOAD pipeline (fetch once → card → later verify/seal → bridge → shard): read the REX release
(archiveUrl + per-book version), walk each book's tree to its leaf SECTIONS, fetch each section's HTML
from the archive, strip it to prose, and mint one reference card per section — attributed to OpenStax
under CC-BY. Math sections whose bodies are mostly MathML strip thin; that's fine — the PROSE (concepts,
definitions, explanations) is the recall value, and the card always links back to the full section.

Conduit, not author: every card is a real OpenStax section, credited, generated=False. Writes
data/openstax_cards.jsonl (gitignored; register in corpus.py's extra sources) + a spine (git-tracked).

    python tools/card_openstax.py --slug calculus-volume-1        # one book (prototype)
    python tools/card_openstax.py --list                          # list the 129 books, write nothing
    python tools/card_openstax.py --all                           # the whole shelf (long, network-heavy)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_openstax"
_UA = {"User-Agent": "NarrowHighway/1.0 (CC-BY reference gathering; mharris.wcs@icloud.com)"}
_CMS = "https://openstax.org/apps/cms/api/v2/pages/?type=books.Book&limit=200&fields=title,cnx_id"
_REL = "https://openstax.org/rex/release.json"
_slug = re.compile(r"[^a-z0-9]+")
_TAG = re.compile(r"<[^>]+>")

# book slug/title keyword -> the domain shelf it belongs on (default "reference")
_SHELF = [
    ("calculus", "mathematics"), ("algebra", "mathematics"), ("trigonometr", "mathematics"),
    ("precalc", "mathematics"), ("statistic", "mathematics"), ("prealgebra", "mathematics"),
    ("physics", "physics"), ("astronomy", "astronomy"), ("chemistr", "chemistry"),
    ("biology", "biology"), ("microbiolog", "biology"), ("anatomy", "medicine"),
    ("economic", "economics"), ("government", "history"), ("history", "history"),
    ("psycholog", "psychology"), ("sociolog", "sociology"), ("philosoph", "philosophy"),
    ("accounting", "economics"), ("business", "economics"), ("nursing", "medicine"),
]


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _shelf_for(slug: str, title: str) -> str:
    hay = (slug + " " + title).lower()
    for kw, sh in _SHELF:
        if kw in hay:
            return sh
    return "reference"


def _get(url: str, tries: int = 3):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=45) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:  # noqa: BLE001 — network is flaky; retry with backoff
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


class _Strip(HTMLParser):
    """HTML -> prose. Drops script/style/figure/math/table (MathML and figures don't carry to text);
    keeps paragraph structure. os-text/os-number spans (titles) fall through as their text."""
    _SKIP = {"script", "style", "figure", "math", "table", "annotation"}
    _BREAK = {"p", "div", "li", "h1", "h2", "h3", "h4", "br", "section"}

    def __init__(self):
        super().__init__()
        self.buf = []
        self.skip = 0

    def handle_starttag(self, t, a):
        if t in self._SKIP:
            self.skip += 1
        if t in self._BREAK:
            self.buf.append("\n")

    def handle_endtag(self, t):
        if t in self._SKIP:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, d):
        if self.skip == 0:
            self.buf.append(d)

    def text(self):
        out = "".join(self.buf)
        out = re.sub(r"[ \t]+", " ", out)
        out = re.sub(r" *\n *", "\n", out)
        return re.sub(r"\n{3,}", "\n\n", out).strip()


def _plain_title(html_title: str) -> str:
    """A section title comes wrapped in os-number/os-text spans — flatten to 'N.N Title'."""
    t = _TAG.sub(" ", html_title or "")
    return re.sub(r"\s+", " ", t).strip()


def _leaves(node, out):
    if isinstance(node, dict):
        kids = node.get("contents")
        if node.get("id") and not kids:
            out.append((str(node["id"]).split("@")[0], node.get("title") or ""))
        for c in (kids or []):
            _leaves(c, out)


def _books():
    """slug -> (title, uuid) for all published OpenStax books."""
    d = _get(_CMS)
    out = {}
    for b in d.get("items", []):
        slug = (b.get("meta") or {}).get("slug") or ""
        if slug and b.get("cnx_id"):
            out[slug] = (b.get("title") or slug, b["cnx_id"])
    return out


def card_book(slug, title, uuid, arch, ver, min_chars=400):
    """Yield one reference card per SECTION of the book with enough prose to be worth recalling."""
    tree = _get(f"{arch}/contents/{uuid}@{ver}.json")
    book_title = tree.get("title") or title
    shelf = _shelf_for(slug, book_title)
    lv = []
    _leaves(tree.get("tree", {}), lv)
    n = 0
    for pid, raw_title in lv:
        sec_title = _plain_title(raw_title)
        low = sec_title.lower()
        if any(k in low for k in ("index", "answer key", "references", "the review questions")):
            continue
        try:
            pg = _get(f"{arch}/contents/{uuid}@{ver}:{pid}.json")
        except Exception:  # noqa: BLE001 — one bad section must not sink the book
            continue
        st = _Strip()
        st.feed(pg.get("content", "") or "")
        body = st.text()
        if len(body) < min_chars:
            continue                                  # front-matter / mostly-equation sections skipped
        body = body[:2400]
        url = f"https://openstax.org/books/{slug}/pages/{_slug.sub('-', sec_title.lower()).strip('-')}"
        yield {
            "id": f"card_src_openstax_{_sk(slug)}_{_sk(sec_title)[:40]}_{pid[:8]}", "kind": "reference",
            "title": f"{sec_title} — {book_title}"[:180], "body": body,
            "source": {"label": f"OpenStax: {book_title} (CC-BY 4.0)", "url": url,
                       "domain": shelf, "authority_tier": "reference"},
            "shelf": shelf, "box": "openstax",
            "bands": [w for w in re.split(r"[^a-z0-9]+", sec_title.lower()) if len(w) > 2]
                     + ["openstax", "textbook", shelf, "cc-by"],
            "subject": sec_title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"a section of {book_title}, an OpenStax open textbook"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False,
            "extra": {"openstax_slug": slug, "book": book_title, "section": sec_title, "license": "CC-BY 4.0"},
        }
        n += 1
    print(f"  {slug}: {n} sections carded (shelf={shelf})")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="one book slug (prototype)")
    ap.add_argument("--all", action="store_true", help="every book (long, network-heavy)")
    ap.add_argument("--list", action="store_true", help="list books, write nothing")
    args = ap.parse_args()

    books = _books()
    if args.list:
        for slug, (title, _uuid) in sorted(books.items()):
            print(f"  {slug:40s} {title}")
        print(f"total: {len(books)} OpenStax CC-BY books")
        return 0

    rel = _get(_REL)
    arch = "https://openstax.org" + rel["archiveUrl"]
    versions = rel.get("books", {})

    if args.slug:
        targets = {args.slug: books[args.slug]} if args.slug in books else {}
        if not targets:
            print(f"unknown slug {args.slug!r}; try --list", file=sys.stderr)
            return 2
    elif args.all:
        targets = books
    else:
        print("give --slug <book>, --all, or --list", file=sys.stderr)
        return 2

    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    spine = {
        "id": SPINE, "kind": "reference", "title": "OpenStax — the open textbooks",
        "body": ("The OpenStax open textbooks — calculus, physics, chemistry, biology, astronomy, "
                 "anatomy, economics and more — peer-reviewed college texts released free to all under "
                 "CC-BY 4.0. Gathered and credited, section by section: modern mathematics and theory "
                 "for the reference section, free to reuse with attribution."),
        "source": {"label": "OpenStax, Rice University (CC-BY 4.0)", "url": "https://openstax.org",
                   "domain": "reference", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["openstax", "textbooks", "mathematics", "science", "cc-by", "reference", "spine"],
        "subject": "the open textbooks",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the open textbooks, a shelf of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "openstax_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
    total = 0
    tmp = out / "openstax_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for slug, (title, uuid) in targets.items():
            ver = (versions.get(uuid) or {}).get("defaultVersion")
            if not ver:
                print(f"  {slug}: no version in release; skipped", file=sys.stderr)
                continue
            for card in card_book(slug, title, uuid, arch, ver):
                f.write(json.dumps(card, ensure_ascii=False) + "\n")
                total += 1
    (out / "openstax_cards.jsonl").write_bytes(tmp.read_bytes())
    tmp.unlink()
    print(f"[openstax] {total:,} section cards -> data/openstax_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
