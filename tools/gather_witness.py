#!/usr/bin/env python3
"""Gather a PD WITNESS'S WORDS into the Cloud of Witnesses (`witness.py`), attributed and provenance-sealed.

`mentors.py` names the cloud; this reads ONE public-domain witness's actual work into `data/witnesses.jsonl`
so `witness.voice()`/`see()` can frame an answer with the witness's VERBATIM words. Ellen G. White first
(d.1915 — every work she wrote is US public domain; a work published before 1929 is PD unconditionally).

The laws, held: NOTHING GENERATED — passages are the witness's exact paragraphs, verbatim, never rewritten.
STRICT-PD ONLY — the gather REFUSES unless the work is proven public domain (published before 1929, i.e.
the federal pre-1929 tier — or the caller asserts author-death + life+70 elapsed). ATTRIBUTED — every
passage carries witness, work, reference, and SOURCE. NET-GROW, NEVER OVERWRITE — existing passages are
kept; only new ids are appended (idempotent, re-runnable).

    python tools/gather_witness.py --witness "Ellen G. White" --work "Steps to Christ" \
        --pub-year 1892 --author-death 1915 --source <url> path/to/steps-to-christ.txt
    python tools/gather_witness.py ... --url <raw-plaintext-url>          # fetch verbatim, then gather
    python tools/gather_witness.py ... --check path.txt                  # count passages, write nothing

Stdlib only. Verbatim in, verbatim out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

OUT = Path("data/witnesses.jsonl")
_MIN, _MAX = 60, 2400          # a passage worth voicing: a real paragraph, not a fragment or a whole chapter
_PD_CUTOFF = 1929              # published before this year -> unconditionally US public domain

# Project Gutenberg wraps its texts in these markers; everything between them is the work itself.
_PG_START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I | re.S)
_PG_END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I | re.S)


def _strip_gutenberg(text: str) -> str:
    """Drop the Project Gutenberg license header/footer, keeping only the work's own words."""
    m = _PG_START.search(text)
    if m:
        text = text[m.end():]
    m = _PG_END.search(text)
    if m:
        text = text[:m.start()]
    return text


def _trim(text: str, start_after: str, stop_before: str) -> str:
    """Keep only the WITNESS'S OWN PROSE: cut everything up to and including `start_after` (front matter —
    a source's metadata, license note, or a publisher's foreword that is not the witness's words), and
    everything from `stop_before` on (back matter — indexes, apparatus). Source-specific knowledge lives
    in the invocation, auditable, not baked into the tool. Both are literal substrings; empty = no cut."""
    if start_after:
        i = text.find(start_after)
        if i >= 0:
            text = text[i + len(start_after):]
    if stop_before:
        j = text.find(stop_before)
        if j >= 0:
            text = text[:j]
    return text


# A source's own FRONT MATTER / APPARATUS is not the witness's words: CCEL cache metadata ("Title:",
# "Creator(s):", "Rights:", a "Reformed or Calvinistic Churches ______" divider), a producer credit, an
# index line. Voicing it as the witness would misattribute the commons to him, so it is dropped — the
# witness's own prose is what rides into the cloud.
_META = re.compile(
    r"^\s*(title|creator\(s\)|creator|rights|source\(s\)|source|subject|print basis|lc call|"
    r"contributor|description|language|publisher|date|produced by|this ebook|\[illustration|"
    r"early christian literature|classic christian ebooks)\b", re.I)


def _is_apparatus(para: str) -> bool:
    if _META.search(para) or "______" in para:          # source metadata, or a divider rule
        return True
    letters = sum(1 for c in para if c.isalpha() or c.isspace())
    return letters / max(1, len(para)) < 0.72            # a table/index/apparatus line, not prose


def _paragraphs(text: str):
    """The work's real paragraphs — blank-line separated, whitespace-normalized, within length bounds,
    with source front matter / apparatus dropped so only the witness's own prose is gathered."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for chunk in re.split(r"\n\s*\n", text):
        para = re.sub(r"\s+", " ", chunk).strip()
        if _MIN <= len(para) <= _MAX and re.search(r"[a-zA-Z]", para) and not _is_apparatus(para):
            yield para


def _pid(witness: str, work: str, ref: str, text: str) -> str:
    return "wit_" + hashlib.sha256(f"{witness}|{work}|{ref}|{text}".encode("utf-8")).hexdigest()[:16]


def _load_text(args) -> str:
    if args.url:
        import urllib.request
        req = urllib.request.Request(args.url, headers={"User-Agent": "narrowhighway-witness-gather/1"})
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 — caller-supplied PD source
            return r.read().decode("utf-8", "replace")
    if not args.path:
        print("give a text file path or --url", file=sys.stderr); sys.exit(2)
    return Path(args.path).read_text(encoding="utf-8", errors="replace")


def _existing_ids(path: Path) -> set:
    ids = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(json.loads(line).get("id"))
                except Exception:  # noqa: BLE001
                    pass
    return ids


def main() -> int:
    ap = argparse.ArgumentParser(description="Gather a public-domain witness's words into the cloud")
    ap.add_argument("path", nargs="?", help="path to a plaintext PD work")
    ap.add_argument("--url", help="raw plaintext URL of a PD work (fetched verbatim)")
    ap.add_argument("--witness", required=True, help='e.g. "Ellen G. White"')
    ap.add_argument("--work", required=True, help='e.g. "Steps to Christ"')
    ap.add_argument("--pub-year", type=int, required=True, help="year first published (proves PD if <1929)")
    ap.add_argument("--author-death", type=int, help="author's death year (life+70 tier, recorded)")
    ap.add_argument("--source", required=True, help="provenance URL/citation of the PD source")
    ap.add_argument("--start-after", default="", help="cut front matter up to & incl. this literal marker")
    ap.add_argument("--stop-before", default="", help="cut back matter from this literal marker on")
    ap.add_argument("--check", action="store_true", help="count passages, write nothing")
    args = ap.parse_args()

    # The strict-PD gate: refuse to gather unless the work is proven public domain.
    if args.pub_year >= _PD_CUTOFF:
        print(f"REFUSED: {args.work} pub {args.pub_year} is not proven PD (need pre-{_PD_CUTOFF}, or assert "
              f"author-death + life+70). Copyrighted witnesses are characterized in mentors.py, not voiced.",
              file=sys.stderr)
        return 3

    raw = _trim(_strip_gutenberg(_load_text(args)), args.start_after, args.stop_before)
    passages = []
    for n, para in enumerate(_paragraphs(raw), start=1):
        ref = f"p{n}"
        passages.append({
            "text": para, "witness": args.witness, "work": args.work, "ref": ref,
            "id": _pid(args.witness, args.work, ref, para), "source": args.source,
            "public_domain": True, "pub_year": args.pub_year, "author_death": args.author_death,
        })

    print(f"{args.witness} — {args.work}: {len(passages)} passages (pub {args.pub_year}, PD; source {args.source})")
    if args.check:
        for p in passages[:2]:
            print("  e.g.:", p["ref"], "—", p["text"][:70] + "…")
        return 0
    if not passages:
        print("no passages found — nothing to gather (a gap stays a gap)"); return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    have = _existing_ids(OUT)
    added = 0
    with open(OUT, "a", encoding="utf-8") as f:                 # APPEND — net-grow, never overwrite
        for p in passages:
            if p["id"] in have:
                continue
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
            have.add(p["id"])
            added += 1
    print(f"gathered {added} new passage(s) -> {OUT} (skipped {len(passages) - added} already present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
