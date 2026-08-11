#!/usr/bin/env python3
"""Export the verified field library as a STANDALONE offline bundle — needs nothing but itself.

Matt, 2026-08-08: standalone is a REQUIREMENT of this project, not a feature — "we don't accept the
work is done unless WE do it." So the library must serve itself when everything else is gone. This
renders the clean-licensed, verified, cited field library — survival, communications, the field kit,
the playbook, and the practical stores — as self-contained HTML that a family reads in any browser
(no server) or runs with our OWN reader (serve.py, standard library only). It is ALSO compatible
with the offline-knowledge boxes others run (Kiwix / Internet-in-a-Box / Prepper Disk) — fellowship
with that same-purpose work is welcome — but the keeping never DEPENDS on them; it does the job by
its own hand.

Unlike a raw Wikipedia dump, this is DISCERNED and CITED: every card carries its public-domain
source, and the bundle carries its own SEAL (a MANIFEST of every file's sha256) plus a stdlib
re-hasher, so a copy proves itself unaltered and heals from what it holds. And it is CLEAN-LICENSED
by construction — public / CC0 / CC-BY only, never share-alike or non-commercial — so it may be
freely redistributed where a copyleft mirror legally cannot.

Sovereign: standard library only. The output is:
  * one self-contained HTML page per card (inline CSS, no network, no external asset);
  * index.html — every card by shelf, with an offline client-side search (inline JS);
  * MANIFEST.json + verify.py (the seal + a re-hasher) + README.txt;
  * ZIMREADY.txt — the one zimwriterfs command that turns this directory into a true .zim.

    PYTHONPATH=src python tools/export_commons_bundle.py            # cut + self-verify
    PYTHONPATH=src python tools/export_commons_bundle.py --check    # list what would be cut
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import corpus  # noqa: E402 — is_public / _is_share_alike, the one public boundary

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or (REPO / "data"))
RELEASES = Path(os.environ.get("CONCORDANCE_RELEASES", "").strip() or "D:/NarrowHighway-Releases")

# The practical field library — clean-licensed, directly-useful cards a family off-grid needs. The
# academic corpus (source_cards, scripture verses, commentary) is deliberately NOT bundled here:
# this is the survive-and-connect kit, kept small enough to browse on a phone. Each file is loaded
# only if present; a missing optional file is skipped, never a hole.
SHELF_FILES = [
    ("survival_cards.jsonl", "The field library"),
    ("firstaid_cards.jsonl", "First aid"),
    ("water_cards.jsonl", "Water"),
    ("food_cards.jsonl", "Food growing"),
    ("sanitation_cards.jsonl", "Sanitation & hygiene"),
    ("comms_cards.jsonl", "Communications"),
    ("navigation_cards.jsonl", "Navigation"),
    ("power_cards.jsonl", "Off-grid power"),
    ("fieldkit_cards.jsonl", "The field kit"),
    ("playbook_cards.jsonl", "The playbook"),
    ("practical_cards.jsonl", "Practical stores"),
    ("access_tools_cards.jsonl", "Free tools"),
]

_CSS = (
    "*{box-sizing:border-box}body{margin:0;background:#0a0b10;color:#e9e3d4;"
    "font:17px/1.7 Georgia,'Palatino Linotype',serif;-webkit-font-smoothing:antialiased}"
    "a{color:#c9a24a;text-decoration:none}a:hover{text-decoration:underline}"
    ".wrap{max-width:44rem;margin:0 auto;padding:1.4rem 1.2rem 4rem}"
    ".kick{color:#c9a24a;letter-spacing:.28em;text-transform:uppercase;font-size:.66rem}"
    "h1{font-weight:400;font-size:1.9rem;margin:.4rem 0 .8rem}"
    ".src{color:#8f8a7c;font-size:.82rem;margin-top:1.4rem;border-top:1px solid rgba(201,162,74,.16);padding-top:.8rem}"
    ".back{display:inline-block;margin-bottom:1rem;color:#8f8a7c;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase}"
    "input{width:100%;background:rgba(201,162,74,.06);border:1px solid rgba(201,162,74,.2);"
    "border-radius:6px;color:#e9e3d4;font:1rem Georgia,serif;padding:.7rem .85rem;margin:.6rem 0 1.2rem}"
    "h2{font-weight:400;font-size:1.05rem;color:#c9a24a;margin:1.6rem 0 .4rem;letter-spacing:.02em}"
    "ul{list-style:none;padding:0;margin:0}li{padding:.28rem 0}"
    ".note{color:#8f8a7c;font-size:.82rem;margin-top:2rem;border-top:1px solid rgba(201,162,74,.16);padding-top:1rem}"
)


def _esc(s: str) -> str:
    return html.escape(str(s or ""))


def _page(title: str, body_html: str) -> str:
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{_esc(title)} — Narrow Highway</title><style>{_CSS}</style></head>"
            f"<body><div class=wrap>{body_html}</div></body></html>")


def _card_html(c: dict) -> str:
    src = c.get("source") or {}
    label = src.get("label") or ""
    url = src.get("url") or ""
    src_line = _esc(label)
    if url:
        src_line = f"<a href='{_esc(url)}'>{_esc(label)}</a>"
    body = (
        "<a class=back href='index.html'>&larr; The field library</a>"
        f"<p class=kick>{_esc(c.get('shelf',''))}</p>"
        f"<h1>{_esc(c.get('title',''))}</h1>"
        f"<div>{_esc(c.get('body',''))}</div>"
        f"<p class=src>Source: {src_line}<br>Card id: {_esc(c.get('id',''))}</p>"
    )
    return _page(c.get("title", ""), body)


def _slug(cid: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in cid.lower()).strip("-")


def _load_clean_cards():
    """Every public, clean-licensed (never share-alike/NC) card from the curated field files."""
    groups = []  # (heading, [cards])
    total = 0
    for fname, heading in SHELF_FILES:
        p = DATA / fname
        if not p.exists():
            continue
        cards = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                continue
            if c.get("box") == "spine":
                continue
            if corpus.is_public(c) and not corpus._is_share_alike(c):
                cards.append(c)
        if cards:
            groups.append((heading, cards))
            total += len(cards)
    return groups, total


def _index_html(groups) -> str:
    total = sum(len(cs) for _h, cs in groups)
    items, sections = [], []
    for heading, cards in groups:
        rows = []
        for c in sorted(cards, key=lambda x: x.get("title", "")):
            href = f"card/{_slug(c['id'])}.html"
            t = _esc(c.get("title", ""))
            rows.append(f"<li data-t=\"{t.lower()}\"><a href='{href}'>{t}</a></li>")
        sections.append(f"<h2>{_esc(heading)}</h2><ul>" + "".join(rows) + "</ul>")
    js = (
        "<script>var q=document.getElementById('q'),L=document.querySelectorAll('li[data-t]');"
        "q.addEventListener('input',function(){var v=q.value.toLowerCase();"
        "L.forEach(function(li){li.style.display=li.dataset.t.indexOf(v)<0?'none':''});"
        "document.querySelectorAll('h2').forEach(function(h){var u=h.nextElementSibling,"
        "any=[].some.call(u.children,function(li){return li.style.display!=='none'});"
        "h.style.display=any?'':'none';u.style.display=any?'':'none'})});</script>"
    )
    body = (
        "<p class=kick>Narrow Highway · offline</p>"
        f"<h1>The field library</h1>"
        f"<p>{total} verified, public-domain reference cards — survival, communications, and the "
        "practical knowledge a household needs when the grid is down. Freely given, cited to source, "
        "and clean-licensed. Browse below or search. No account, no network, no cost.</p>"
        "<p style='margin:1.3rem 0;font-size:1.15rem'><a href='bible.html'>&#10015; The Holy Bible "
        "&mdash; the whole Word (World English Bible)</a></p>"
        "<input id=q type=text placeholder='Search the field library…' autocomplete=off>"
        + "".join(sections) +
        "<p class=note>This library is standalone — it needs nothing but itself: read it right here "
        "in your browser, or run <code>python serve.py</code> to have Narrow Highway serve it for you "
        "(no install, no internet, no other software). It carries its own seal — <code>python "
        "verify.py</code> re-hashes every file against MANIFEST.json to prove the copy is unaltered. "
        "(It is ALSO compatible with Kiwix / Internet-in-a-Box / Prepper Disk — see README.txt — but "
        "never depends on them.) The whole, searchable library lives at narrowhighway.com. Psalm "
        "119:105.</p>" + js
    )
    return _page("The field library", body)


VERIFIER = '''#!/usr/bin/env python3
"""Verify this bundle against its MANIFEST — standard library only.
    python verify.py            # from inside the bundle directory
"""
import hashlib, json, sys
from pathlib import Path
root = Path(__file__).resolve().parent
man = json.load(open(root / "MANIFEST.json", encoding="utf-8"))
bad = 0
for f in man["files"]:
    p = root / f["path"]
    if not p.is_file():
        print("MISSING   " + f["path"]); bad += 1; continue
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != f["sha256"]:
        print("ALTERED   " + f["path"]); bad += 1
print(("VERIFIED: %d files match their seal" % len(man["files"])) if not bad
      else ("FAILED: %d file(s) do not match" % bad))
sys.exit(1 if bad else 0)
'''

README = """THE FIELD LIBRARY — an offline keeping, freely given (Narrow Highway, narrowhighway.com)

WHAT THIS IS
  THE WHOLE BIBLE (World English Bible, public domain) — nothing in this library ever ships without
  the Word — open bible.html — PLUS {total} verified, public-domain reference cards — survival,
  communications (radio + the LoRa mesh), the field kit, the playbook, and practical stores — the
  survive-and-connect knowledge a household needs when the grid is down. Every card is cited to its
  public-domain source. Cut on {date}. No account, no network, no cost.

STANDALONE — this needs NOTHING but itself
  This library stands entirely on its own. You do NOT need Kiwix, Internet-in-a-Box, a Prepper Disk,
  the internet, or any other software to use it. Two ways to read it, both self-contained:
    1. Open index.html in any web browser (double-click it) — it works straight off the disk.
    2. Or run our own reader:  python serve.py   — then open the address it prints (default
       http://127.0.0.1:8000). Standard library only; no install, no network.
  Search works offline in the page itself. Copy the whole folder to a USB stick or SD card and it
  runs the same on the next machine. Sovereignty is a requirement of this project, not a feature:
  the keeping must work when everything else is gone, by our own hand.

WHY IT'S DIFFERENT FROM A RAW DUMP
  It is DISCERNED and CITED (each card names its source), it carries its own SEAL (MANIFEST.json +
  verify.py re-hash every file), and it is CLEAN-LICENSED — public domain / CC0 / CC-BY only, never
  share-alike or non-commercial — so it may be freely redistributed where a copyleft mirror cannot.

HOW TO VERIFY IT
  python verify.py     (standard library only; re-hashes every file against MANIFEST.json)

ALSO COMPATIBLE (a bonus, never a requirement)
  Because it is ordinary static HTML, it ALSO drops onto boxes those in the same work already run —
  Kiwix / Internet-in-a-Box / Prepper Disk (copy it into their served content), and ZIMREADY.txt has
  the single zimwriterfs command to make a true .zim. Fellowship with that movement is welcome; but
  this library never depends on it — it does the job by itself.

The disk carries the library; the radio carries the whisper. The whole, searchable keeping lives at
narrowhighway.com — this bundle is the anchor; the site is the spread. Psalm 119:105.
"""

SERVE_PY = '''#!/usr/bin/env python3
"""Serve this field library yourself — standard library only, no install, no network.
    python serve.py           # then open the printed address (default http://127.0.0.1:8000)
    python serve.py 9000      # choose a port
This is Narrow Highway's OWN reader: the keeping serves itself, needing no other software.
"""
import http.server, socketserver, sys
from pathlib import Path
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
root = Path(__file__).resolve().parent
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(root), **k)
    def log_message(self, *a):
        pass
print("The field library is served at  http://127.0.0.1:%d/  (Ctrl-C to stop)" % port)
print("Open that address in any browser. Everything is offline; nothing leaves this machine.")
with socketserver.TCPServer(("127.0.0.1", port), H) as s:
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        print("\\nstopped.")
'''

ZIMREADY = """MAKE A TRUE ZIM FROM THIS BUNDLE

This directory is a plain static website with a welcome page (index.html), so the openZIM tool
'zimwriterfs' turns it into a single .zim that Kiwix reads directly:

    zimwriterfs \\
      --welcome=index.html \\
      --language=eng \\
      --title="Narrow Highway — The Field Library" \\
      --description="Verified, public-domain survival & communications reference. Freely given." \\
      --creator="Narrow Highway" --publisher="Narrow Highway" \\
      --name="narrowhighway-field-library" \\
      .  narrowhighway-field-library.zim

(zimwriterfs is part of the openZIM project; install it from openzim.org. The bundle already
verifies itself with verify.py before you package it.)
"""


BIBLE_FILE = "bible_en.jsonl"   # the whole World English Bible, one row per verse (public domain)


def _load_bible():
    """The whole Bible in canonical (file) order: [(book, [(chapter, [(verse, text)])])]. Returns []
    if the source is absent — and main() then REFUSES to build: nothing ships without the Word."""
    from collections import OrderedDict
    p = DATA / BIBLE_FILE
    if not p.exists():
        return []
    books = OrderedDict()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = json.loads(line)
            ch, vs = int(v["chapter"]), int(v["verse"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        books.setdefault(v.get("book", "?"), OrderedDict()).setdefault(ch, []).append((vs, v.get("text", "")))
    return [(b, [(ch, sorted(vv)) for ch, vv in sorted(chs.items())]) for b, chs in books.items()]


def _bible_book_html(book, chapters):
    parts = ["<a class=back href='../index.html'>&larr; Library</a>"
             "<a class=back href='../bible.html' style='margin-left:1rem'>&larr; Books</a>",
             f"<p class=kick>The Word &middot; World English Bible</p><h1>{_esc(book)}</h1>"]
    for ch, verses in chapters:
        parts.append(f"<h2>{_esc(book)} {ch}</h2><p>")
        for vs, text in verses:
            parts.append(f"<sup style='color:#c9a24a'>{vs}</sup>&nbsp;{_esc(text)} ")
        parts.append("</p>")
    parts.append("<p class=src>World English Bible (public domain). The whole Bible ships with every "
                 "copy of this library &mdash; nothing goes without the Word. Psalm 119:105.</p>")
    return _page(book, "".join(parts))


def _bible_index_html(bible):
    rows = "".join(f"<li><a href='bible/{_slug(b)}.html'>{_esc(b)}</a></li>" for b, _ in bible)
    ch_total = sum(len(chs) for _, chs in bible)
    body = ("<a class=back href='index.html'>&larr; The field library</a>"
            "<p class=kick>The Word</p><h1>The Holy Bible</h1>"
            f"<p>The whole World English Bible &mdash; public domain, freely given. {len(bible)} books, "
            f"{ch_total} chapters. Nothing in this library ships without the Word (Psalm 119:105).</p>"
            "<ul>" + rows + "</ul>")
    return _page("The Holy Bible", body)


def main() -> int:
    check = "--check" in sys.argv
    groups, total = _load_clean_cards()
    bible = _load_bible()
    if not bible:
        print("REFUSING to build: the Bible (data/bible_en.jsonl) is missing. NOTHING ships without "
              "a full copy of the Word.")
        return 1
    if not total:
        print("REFUSING: no clean field cards found — nothing to give. (Are the data/*.jsonl present?)")
        return 1
    bible_ch = sum(len(chs) for _, chs in bible)
    print(f"bundle: THE WHOLE BIBLE ({len(bible)} books, {bible_ch} chapters) + {total} clean-licensed "
          f"cards across {len(groups)} shelves | " + " · ".join(f"{h} {len(cs)}" for h, cs in groups))
    if check:
        return 0

    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    dest = RELEASES / "field-library-html" / f"field-library-html-v1-{stamp}"
    (dest / "card").mkdir(parents=True, exist_ok=False)

    written = []

    def _emit(rel: str, text: str) -> None:
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        written.append(rel)

    _emit("index.html", _index_html(groups))
    for _heading, cards in groups:
        for c in cards:
            _emit(f"card/{_slug(c['id'])}.html", _card_html(c))
    # THE WORD — the whole Bible ships with every copy; nothing goes without it.
    _emit("bible.html", _bible_index_html(bible))
    for book, chapters in bible:
        _emit(f"bible/{_slug(book)}.html", _bible_book_html(book, chapters))
    _emit("verify.py", VERIFIER)
    _emit("serve.py", SERVE_PY)
    _emit("README.txt", README.format(total=total, date=stamp[:10]))
    _emit("ZIMREADY.txt", ZIMREADY)

    # the seal: every file's bytes + sha256 (verify.py re-checks against this)
    files = []
    for rel in written:
        p = dest / rel
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        files.append({"path": rel, "bytes": p.stat().st_size, "sha256": h.hexdigest()})
    manifest = {"bundle": "field-library-html", "version": "v1", "stamp": stamp,
                "cards": total, "shelves": {h: len(cs) for h, cs in groups}, "files": files,
                "license": "public domain / CC0 / CC-BY only (no share-alike, no non-commercial)"}
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    total_bytes = sum(f["bytes"] for f in files) + (dest / "MANIFEST.json").stat().st_size
    print(f"  wrote {len(written) + 1} files ({total_bytes/1e6:.2f} MB) -> {dest}")
    print("  self-verify:", end=" ")
    # confirm the manifest we just wrote matches on disk (catch a write race / encoding drift)
    bad = 0
    for f in files:
        h = hashlib.sha256()
        with open(dest / f["path"], "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != f["sha256"]:
            bad += 1
    print("OK — every file matches its seal" if not bad else f"FAILED — {bad} mismatch")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
