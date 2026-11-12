#!/usr/bin/env python3
"""THE CANON LAYERS' BUILD: the books beyond the 66, fetched from eBible.org, checked, and written for the box
(run 2026-11-11-full-canons). tools/box_build.py runs it as tools/box_builds.txt lists it:

    python -I -S tools/build_canon_layers.py INPUTS OUTPUT

INPUTS holds exactly the three listed tables, each at its repository path:
  tools/canon_tables/text_pins.json     each edition's source, URL, zip member, that member's sha256, its licence
  tools/canon_tables/book_codes.json    eBible's book codes: the 66's (skipped), each added book's name, codes
                                        skipped on purpose with the reason, and where each Greek addition stands
  tools/canon_tables/verse_counts.json  the verse lines each added book holds in each edition, measured and committed

For each edition: fetch the zip over https from eBible.org; take its verse-per-line member; refuse it unless its
sha256 is the pinned one (the zip is never pinned, since every member carries its build time); parse every line,
'CODE C:V text' in eBible's own codes; refuse a line that does not parse, a carriage return, a verse twice, a code
neither mapped nor skipped, a count that is not the committed one, and a span the tables name that the text does not
hold. Only when every edition passes does it write anything:

  OUTPUT/<edition>.jsonl  one row per verse line of an added book, in the file's order: book, chapter, verse, text.
                          A verse id with a letter keeps it as its label ('4:7a' is verse "7a"), never folded into a
                          whole number; an empty line is written with empty text, which the reader reads as missing.
  OUTPUT/layers.json      each edition's name, source, URL, member, text sha256, licence and numbering; its books in
                          the file's order with their codes, verse lines and chapters; the codes it skipped (the
                          66's, under one reason, and any other with its own); and where each addition stands, its
                          span read from the text.

It writes bytes with '\\n' line ends, and every value it writes is parsed, never copied, so a checkout's line endings
cannot reach the output and the output hashes the same wherever it runs. Any failure exits 1 and writes nothing, so
tools/box_build.py lands no directory. Stdlib only, like every build tool.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile

TABLES = {
    "pins": "tools/canon_tables/text_pins.json",
    "codes": "tools/canon_tables/book_codes.json",
    "counts": "tools/canon_tables/verse_counts.json",
}
SOURCE_PREFIX = "https://ebible.org/Scriptures/"
MAX_ZIP_BYTES = 64 * 1024 * 1024
FETCH_TIMEOUT_S = 180
# eBible's CDN refuses Python's own client name (403, measured 2026-11-11), so the build names itself, generically.
USER_AGENT = "canon-layers-build/1"
LINE = re.compile(r"([0-9A-Z]{3}) ([0-9]{1,3}):([0-9]{1,3})([a-z]?)(?: (.*))?")
CODE = re.compile(r"[0-9A-Z]{3}")
HEX64 = re.compile(r"[0-9a-f]{64}")
CV = re.compile(r"([0-9]{1,3}):([0-9]{1,3})")


class Refused(Exception):
    """The build refuses; nothing is written."""


# ------------------------------------------------------------------------------------------------ the tables

def _load(inputs: str, rel: str) -> dict:
    path = os.path.join(inputs, *rel.split("/"))
    try:
        with open(path, "rb") as fh:
            held = json.loads(fh.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise Refused(f"{rel} cannot be read as JSON: {type(e).__name__}") from None
    if not isinstance(held, dict):
        raise Refused(f"{rel} is not a JSON object")
    return held


def read_tables(inputs: str) -> dict:
    """The three tables, from exactly the three staged inputs."""
    found = []
    for dirpath, _dirs, files in os.walk(inputs):
        for f in files:
            found.append(os.path.relpath(os.path.join(dirpath, f), inputs).replace(os.sep, "/"))
    if sorted(found) != sorted(TABLES.values()):
        raise Refused(f"the inputs are {sorted(found)}, not the three tables {sorted(TABLES.values())}")
    return {k: _load(inputs, rel) for k, rel in TABLES.items()}


def _str(v, what: str) -> str:
    if not isinstance(v, str) or not v.strip() or "\n" in v or "\r" in v:
        raise Refused(f"{what} is not a one-line string")
    return v


def _int(v, what: str) -> int:
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        raise Refused(f"{what} is not a whole number from 1")
    return v


def check_tables(tables: dict) -> list:
    """The editions, checked against each other: the same editions in all three tables, a pin and a source for
    each, a count for exactly each mapped book. Returns the edition ids in their sorted order."""
    pins = tables["pins"].get("editions")
    codes = tables["codes"].get("editions")
    counts = tables["counts"].get("editions")
    if not all(isinstance(x, dict) and x for x in (pins, codes, counts)):
        raise Refused("each table must hold a non-empty 'editions' object")
    if not set(pins) == set(codes) == set(counts):
        raise Refused(f"the tables name different editions: {sorted(pins)}, {sorted(codes)}, {sorted(counts)}")
    the_66 = tables["codes"].get("the_66") or {}
    held = the_66.get("codes")
    if not isinstance(held, list) or len(held) != 66 or len(set(held)) != 66 or not all(
            isinstance(c, str) and CODE.fullmatch(c) for c in held):
        raise Refused("the_66 must list 66 distinct book codes")
    _str(the_66.get("why"), "the_66's reason")
    for ed in sorted(pins):
        p = pins[ed]
        if not isinstance(p, dict):
            raise Refused(f"{ed}: its pin is not an object")
        for k in ("source", "url", "member", "sha256", "license"):
            _str(p.get(k), f"{ed}: the pin's {k}")
        if not p["url"].startswith(SOURCE_PREFIX) or not p["url"].endswith(".zip"):
            raise Refused(f"{ed}: the source is not an eBible.org zip: {p['url']}")
        if not HEX64.fullmatch(p["sha256"]):
            raise Refused(f"{ed}: the pin is not a sha256")
        c = codes[ed]
        if not isinstance(c, dict):
            raise Refused(f"{ed}: its book table is not an object")
        _str(c.get("name"), f"{ed}: its name")
        _str(c.get("numbering"), f"{ed}: its numbering")
        books, skip = c.get("books"), c.get("skip")
        if not isinstance(books, dict) or not books or not isinstance(skip, dict):
            raise Refused(f"{ed}: its books and skips must be objects")
        for code, name in list(books.items()) + list(skip.items()):
            if not CODE.fullmatch(code):
                raise Refused(f"{ed}: {code!r} is not a book code")
            _str(name, f"{ed}: {code}'s entry")
        both = set(books) & (set(skip) | set(held))
        if both:
            raise Refused(f"{ed}: codes both mapped and skipped: {sorted(both)}")
        if set(skip) & set(held):
            raise Refused(f"{ed}: a skip repeats a code of the 66")
        n = counts[ed]
        if not isinstance(n, dict) or set(n) != set(books):
            raise Refused(f"{ed}: the counts name {sorted(n) if isinstance(n, dict) else n}, "
                          f"not exactly the mapped books {sorted(books)}")
        for code, k in n.items():
            _int(k, f"{ed}: {code}'s count")
        for part in ("within", "in_the_66"):
            spans = c.get(part)
            if not isinstance(spans, dict):
                raise Refused(f"{ed}: '{part}' must be an object")
            for key, span in spans.items():
                _str(key, f"{ed}: a name in {part}")
                if not isinstance(span, dict) or not isinstance(span.get("code"), str):
                    raise Refused(f"{ed}: {part} {key} names no code")
                if part == "within" and span["code"] not in books:
                    raise Refused(f"{ed}: {key} stands within {span['code']}, which is not a book of the layer")
                if part == "in_the_66":
                    if span["code"] not in held:
                        raise Refused(f"{ed}: {key} is printed in {span['code']}, which is not a code of the 66")
                    _str(span.get("book"), f"{ed}: {key}'s book of the 66")
    return sorted(pins)


# ------------------------------------------------------------------------------------------------ the text

def fetch_https(url: str) -> bytes:
    """The zip, over https, from eBible.org; any failure refuses."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_S) as r:
            if getattr(r, "status", 200) != 200:
                raise Refused(f"{url} answered {r.status}")
            data = r.read(MAX_ZIP_BYTES + 1)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Refused(f"{url} could not be fetched: {type(e).__name__}: {e}") from None
    if len(data) > MAX_ZIP_BYTES:
        raise Refused(f"{url} is larger than {MAX_ZIP_BYTES} bytes")
    return data


def pinned_text(zip_bytes: bytes, member: str, sha256: str, ed: str) -> bytes:
    """The zip's verse-per-line member, only when it hashes to its pin."""
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            raw = z.read(member)
    except (zipfile.BadZipFile, KeyError, OSError, RuntimeError, ValueError) as e:
        raise Refused(f"{ed}: {member} cannot be read from the zip: {type(e).__name__}") from None
    got = hashlib.sha256(raw).hexdigest()
    if got != sha256:
        raise Refused(f"{ed}: {member} hashes to {got}, not to its pin {sha256}: the text changed, so nothing is "
                      f"built; a new pin is a new step")
    return raw


def parse(raw: bytes, ed: str) -> list:
    """Every verse line of a vpl.txt as (code, chapter, label, text), in the file's order."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused(f"{ed}: the text is not UTF-8") from None
    if "\r" in text:
        raise Refused(f"{ed}: the text holds a carriage return")
    if text.startswith("﻿"):
        raise Refused(f"{ed}: the text opens with a byte-order mark")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out, seen = [], set()
    for n, ln in enumerate(lines, 1):
        m = LINE.fullmatch(ln)
        if not m:
            raise Refused(f"{ed}: line {n} is not 'CODE C:V text'")
        code, ch, v, letter, body = m.groups()
        label = str(int(v)) + letter
        key = (code, int(ch), label)
        if key in seen:
            raise Refused(f"{ed}: {code} {ch}:{label} is in the text twice")
        seen.add(key)
        out.append((code, int(ch), label, body or ""))
    if not out:
        raise Refused(f"{ed}: the text holds no verse")
    return out


def _has(verses: list, code: str, ch: int, v: int) -> bool:
    return (code, ch, str(v)) in verses


def _span(ed: str, key: str, span: dict, keys: set, by_code: dict, name: str) -> dict:
    """Where an addition stands, read from the text: the chapter's own first and last verse when the table names
    only a chapter, and only spans whose every named end the text holds."""
    code = span["code"]
    out = {"book": name}
    if "from" in span or "to" in span:
        ends = []
        for end in ("from", "to"):
            m = CV.fullmatch(span.get(end) or "")
            if not m or not _has(keys, code, int(m.group(1)), int(m.group(2))):
                raise Refused(f"{ed}: {key}'s {end} {span.get(end)!r} is not a verse of {code}")
            ends.append(f"{int(m.group(1))}:{int(m.group(2))}")
        out.update({"from": ends[0], "to": ends[1]})
        return out
    if "chapter" not in span:
        if code not in by_code:
            raise Refused(f"{ed}: {key} stands in {code}, which the text does not hold")
        return out
    ch = _int(span["chapter"], f"{ed}: {key}'s chapter")
    whole = sorted(int(label) for (c, cc, label) in keys if c == code and cc == ch and label.isdigit())
    if not whole:
        raise Refused(f"{ed}: {key} stands in {code} {ch}, which the text does not hold")
    named = "first" in span or "last" in span
    first, last = span.get("first", whole[0]), span.get("last", whole[-1])
    for end in (first, last):
        if not _has(keys, code, ch, _int(end, f"{ed}: {key}'s span")):
            raise Refused(f"{ed}: {key}'s span {ch}:{first}-{last} is not in {code}")
    if first > last:
        raise Refused(f"{ed}: {key}'s span {ch}:{first}-{last} runs backwards")
    out.update({"chapter": ch, "first": first, "last": last, "whole_chapter": not named})
    return out


def build_edition(ed: str, raw: bytes, tables: dict) -> tuple:
    """(rows, manifest) of one edition from its pinned text."""
    c = tables["codes"]["editions"][ed]
    p = tables["pins"]["editions"][ed]
    counts = tables["counts"]["editions"][ed]
    the_66 = set(tables["codes"]["the_66"]["codes"])
    books, skip = c["books"], c["skip"]
    verses = parse(raw, ed)
    unknown = sorted({code for code, _c, _v, _t in verses} - set(books) - set(skip) - the_66)
    if unknown:
        raise Refused(f"{ed}: codes neither mapped nor skipped: {unknown}")
    lines, chapters, order = {}, {}, []
    for code, ch, _label, _t in verses:
        if code in books:
            if code not in lines:
                order.append(code)
            lines[code] = lines.get(code, 0) + 1
            chapters.setdefault(code, set()).add(ch)
    wrong = {code: (lines.get(code, 0), n) for code, n in counts.items() if lines.get(code, 0) != n}
    if wrong:
        raise Refused(f"{ed}: verse lines (found, committed) differ: {dict(sorted(wrong.items()))}")
    keys = {(code, ch, label) for code, ch, label, _t in verses}
    by_code = {code for code, _c, _v, _t in verses}
    rows = []
    for code, ch, label, body in verses:
        if code in books:
            rows.append({"book": books[code], "chapter": ch, "verse": int(label) if label.isdigit() else label,
                         "text": body})
    within = {key: _span(ed, key, span, keys, by_code, books[span["code"]]) for key, span in c["within"].items()}
    in_the_66 = {key: _span(ed, key, span, keys, by_code, span["book"]) for key, span in c["in_the_66"].items()}
    present_66 = sorted(by_code & the_66)
    manifest = {
        "name": c["name"], "source": p["source"], "url": p["url"], "member": p["member"],
        "text_sha256": p["sha256"], "license": p["license"], "numbering": c["numbering"],
        "books": [{"code": code, "name": books[code], "verse_lines": lines[code],
                   "chapters": len(chapters[code])} for code in order],
        "skipped": {code: skip[code] for code in skip if code in by_code},
        "skipped_66": present_66,
        "within": within, "in_the_66": in_the_66,
    }
    return rows, manifest


def build(tables: dict, fetch=None) -> dict:
    """Every output file, name to bytes. Nothing is written here; any refusal raises Refused. `fetch` stands in
    for the network in the tests, which never fetch."""
    fetch = fetch or fetch_https
    editions = check_tables(tables)
    files, layers = {}, {}
    for ed in editions:
        p = tables["pins"]["editions"][ed]
        raw = pinned_text(fetch(p["url"]), p["member"], p["sha256"], ed)
        rows, manifest = build_edition(ed, raw, tables)
        files[f"{ed}.jsonl"] = b"".join(
            json.dumps(r, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n" for r in rows)
        layers[ed] = manifest
    files["layers.json"] = (json.dumps({"build": "canon-layers", "editions": layers,
                                        "the_66": tables["codes"]["the_66"]["why"]},
                                       ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")
    return files


def write(out: str, files: dict) -> None:
    for name in sorted(files):
        with open(os.path.join(out, name), "xb") as fh:
            fh.write(files[name])


def main(argv: list) -> int:
    if len(argv) != 2:
        print("usage: build_canon_layers.py INPUTS OUTPUT", file=sys.stderr)
        return 2
    inputs, out = argv
    if not os.path.isdir(inputs) or not os.path.isdir(out) or os.listdir(out):
        print("build_canon_layers: INPUTS must be a directory and OUTPUT an empty one", file=sys.stderr)
        return 2
    try:
        files = build(read_tables(inputs))
    except Refused as e:
        print(f"build_canon_layers: refused: {e}", file=sys.stderr)
        return 1
    write(out, files)
    for name in sorted(files):
        print(f"wrote {name}: {len(files[name])} bytes, sha256 {hashlib.sha256(files[name]).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
