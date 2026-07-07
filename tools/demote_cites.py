#!/usr/bin/env python3
"""Demote the auto-detected 'cites' connection cards to 'references' — cite-fair honesty.

Every 'cites' connection card in the keeping is an ENGINE-DERIVED book-name co-mention
(source label "Auto-detected citation", body "Auto-detected via book-name match"): the
card's text merely names a book, it does not cite a passage (none carry a chapter:verse
ref). Calling that a citation overclaims — "Herodias cites John" reads as if Herodias
quoted the gospel, when the Herodias entry just mentions the word. So we relabel the
relationship_kind (and the human-facing title / bands / source label) from 'cites' to
'references', the truthful verb. The edge stays on the map; only the claim is corrected.

Deterministic, idempotent (a second run changes 0), and reversible (only the ~2k matched
cards change; every other line is passed through BYTE-FOR-BYTE). Writes atomically.

    python tools/demote_cites.py [path/to/cards.jsonl] [--dry-run]

Not a 2.0 generator fix: these edges were imported from the 1.0 upstream, so there is no
2.0 code path that would reintroduce 'cites'. If the 1.0 auto-citer is ever re-run, re-run
this after the import (or gate it at the source — the deferred proper ch:v re-citer).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "cards.jsonl")
OLD, NEW = "cites", "references"
OLD_LABEL, NEW_LABEL = "Auto-detected citation", "Auto-detected reference"


def _demote(card: dict, now_iso: str) -> bool:
    """Mutate one card in place if it is an OLD-kind connection. Return True if changed."""
    if card.get("kind") != "connection":
        return False
    ex = card.get("extra")
    if not isinstance(ex, dict) or ex.get("relationship_kind") != OLD:
        return False
    ex["relationship_kind"] = NEW
    # human-facing title: "X cites Y" -> "X references Y" (the middle verb only)
    title = card.get("title")
    if isinstance(title, str) and f" {OLD} " in title:
        card["title"] = title.replace(f" {OLD} ", f" {NEW} ", 1)
    # bands: swap the 'cites' tag, keep the rest, de-dupe preserving order
    bands = card.get("bands")
    if isinstance(bands, list):
        seen, out = set(), []
        for b in bands:
            b2 = NEW if b == OLD else b
            if b2 not in seen:
                seen.add(b2)
                out.append(b2)
        card["bands"] = out
    # box grouping key: dictionary_cites_matthew -> dictionary_references_matthew
    box = card.get("box")
    if isinstance(box, str) and f"_{OLD}_" in box:
        card["box"] = box.replace(f"_{OLD}_", f"_{NEW}_")
    # source label: stop calling a co-mention a citation
    src = card.get("source")
    if isinstance(src, dict) and src.get("label") == OLD_LABEL:
        src["label"] = NEW_LABEL
    card["updated_at"] = now_iso
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=DEFAULT_PATH)
    ap.add_argument("--dry-run", action="store_true", help="report counts, write nothing")
    args = ap.parse_args(argv)

    if not os.path.exists(args.path):
        print(f"ERROR: no such file: {args.path}", file=sys.stderr)
        return 2

    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat()
    total = conns = changed = 0
    out_lines = []
    sample = []
    with open(args.path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                out_lines.append(raw if raw.endswith("\n") else raw + "\n")
                continue
            total += 1
            card = json.loads(line)
            if card.get("kind") == "connection":
                conns += 1
            if _demote(card, now_iso):
                changed += 1
                if len(sample) < 5:
                    sample.append(card.get("title"))
                out_lines.append(json.dumps(card, ensure_ascii=False) + "\n")
            else:
                out_lines.append(line + "\n")  # unchanged: pass through

    print(f"file:            {args.path}")
    print(f"total cards:     {total}")
    print(f"connection cards:{conns}")
    print(f"demoted '{OLD}' -> '{NEW}': {changed}")
    for t in sample:
        print(f"   e.g. {t}")
    if args.dry_run:
        print("(dry-run — nothing written)")
        return 0
    if changed == 0:
        print("(no change — already clean; nothing written)")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(out_lines)
    os.replace(tmp, args.path)  # atomic on POSIX + Windows
    print(f"OK — rewrote {args.path} ({changed} cards demoted).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
