#!/usr/bin/env python3
"""Repoint the citations that resolve to nothing — one rule per KIND of citation, never one rule
for all of them.

    PYTHONPATH=src python tools/repoint_citations.py --dry-run     # the proposal, card by card
    PYTHONPATH=src python tools/repoint_citations.py               # apply, atomically

4,743 cards carry a `source.url` that no longer lands where it says:

  * 2,619 cite `/encyclopedia.html?ref=X` — a 1,000-byte `noindex` JavaScript stub. The #1 page in
    the access log at 4,209 hits, and it is not a page.
  * 2,124 cite `/canon.html?ref=X` — 3,020 hard 404s on the witness host, and on the secular host a
    301 to `/bible.html` that DROPS the `?ref=`, so the reader lands on a generic Bible page having
    silently lost the reference. That one is worse than the 404: nothing reports it.

MEASURING THE 2,124 SPLIT THEM, and the split changed the plan. 468 name a real passage
("Revelation 5") — the Word can show that. 1,656 name an INTERNAL SLUG (`aurelius_aur_07_xxiii`,
`ignatius_trallians_ch8`) that no page has ever been able to resolve, and for those the citing card
IS the passage: the text of Aurelius §7.23 is the body of that very card.

So the third rule is NOT a redirect. Pointing a card's source at its own permalink would close a
circle — a provenance chain whose evidence is itself — and this project exists to prevent exactly
that. The URL is cleared and the LABEL kept: "Marcus Aurelius, Meditations (c. AD 170)" is true,
sufficient, and no longer pretends there is somewhere else to go. The card renderer already draws a
label with no link (api.render_card_html), so the reader sees the authority and no false door.

That is the same judgement as the seal fix: 11,084 cards were shown "its seal" for a hash that was
not a seal, and the answer was to remove the claim, not to redirect it.

CLEARING THE URL ERASES NOTHING, and that was worth checking rather than assuming. Every one of
these cards already carries `source.ref` — `aur_07_xxiii`, `Revelation 5`, `Slave` — beside the
label. The reference and the authority both survive; only the door that opened onto nothing is
taken down. (Had `ref` been absent, this tool would have had to record the retired address first:
a removal is a record, never an erasure.)

Deterministic, idempotent (a second run changes 0), atomic write, and every line it does not touch
is passed through byte for byte.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "data", "cards.jsonl")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# A Scripture reference names a book and a chapter, optionally a verse: "Revelation 5", "John 3:16",
# "1 Kings 8:22". An internal slug does not — it is lowercase with underscores.
SCRIPTURE_REF = re.compile(r"^[1-3]?\s*[A-Za-z][A-Za-z ]+\s+\d{1,3}(?::\d{1,3})?$")

ENCYCLOPEDIA = "/encyclopedia.html"
CANON = "/canon.html"


def _ref_of(url: str) -> str:
    q = urllib.parse.urlparse(url).query
    return urllib.parse.unquote((urllib.parse.parse_qs(q).get("ref") or [""])[0]).strip()


def decide(card: dict):
    """(new_url, rule) for a card whose citation is broken, or None to leave it alone.

    `new_url` of "" means: clear the URL, keep the label — we have no honest destination.
    """
    url = str(((card.get("source") or {}).get("url")) or "")
    if ENCYCLOPEDIA in url:
        ref = _ref_of(url)
        if not ref:
            return None
        # The Dictionary is where an Easton entry is READ — the entry with every verse that
        # speaks of it, which is more than the card alone carries.
        return "/characters.html?search=" + urllib.parse.quote(ref), "easton -> the Dictionary"
    if CANON in url:
        ref = _ref_of(url)
        if not ref:
            return None
        if SCRIPTURE_REF.match(ref):
            return "/bible.html?ref=" + urllib.parse.quote(ref), "passage -> the Word"
        # An internal slug names no page anywhere, and this card IS the passage. Keep the label,
        # drop the door that goes nowhere. NOT a self-link: a source that cites itself is a circle.
        return "", "slug -> label only (no self-citation)"
    return None


def _shards(dirname: str, dry: bool) -> int:
    """A CARD DOES NOT LIVE IN ONE PLACE, and fixing the file only fixed half of them.

    24 shelves are FROZEN: their bodies ride SQLite shards under data/shards and are rehydrated on
    read, so the shard's copy is what a reader actually gets. After cards.jsonl was repointed, the
    codex cards (resident) served the new citation and the dictionary and classics cards (frozen)
    still served `/encyclopedia.html` and `/canon.html` — 4,039 of the 4,743, silently unfixed and
    reported as done by a check that only ever looked at the file.

    A full rebuild would need ~2.7 GB of RAM to reload the corpus, on a box with 3 GB free, so the
    affected rows are updated in place instead. That is sound because the SOURCE was corrected
    first: any later rebuild from cards.jsonl produces exactly this.

    The server opens these with `immutable=1`, which promises SQLite the file never changes —
    so both services MUST be stopped before this runs, or a reader can be served a page that no
    longer exists in the file underneath it.
    """
    import sqlite3
    from pathlib import Path

    total, per_db = 0, {}
    for db in sorted(Path(dirname).glob("*.db")):
        conn = sqlite3.connect(str(db))
        try:
            rows = conn.execute("select id, json from cards").fetchall()
            updates = []
            for cid, raw in rows:
                try:
                    card = json.loads(raw)
                except ValueError:
                    continue
                d = decide(card)
                if d is None:
                    continue
                new_url, _rule = d
                if str(((card.get("source") or {}).get("url")) or "") == new_url:
                    continue
                card["source"]["url"] = new_url
                updates.append((json.dumps(card, ensure_ascii=False), cid))
            if updates and not dry:
                conn.executemany("update cards set json = ? where id = ?", updates)
                conn.commit()
            per_db[db.name] = len(updates)
            total += len(updates)
        finally:
            conn.close()

    print(f"{'PROPOSED' if dry else 'APPLIED'} — {total:,} citations in the frozen shelves\n")
    for name, n in sorted(per_db.items(), key=lambda x: -x[1]):
        print(f"  {n:>6,}  {name}")
    if dry:
        print("\nNothing was written. Both services must be STOPPED before applying — the shards "
              "are opened immutable.")
    return 0


def main() -> int:
    # The gate runs alone (tools/check.py holds .gate.lock): a heavy job beside it has produced
    # three false failures by starving a wire test. Step aside rather than corrupt a verdict.
    if os.path.exists(os.path.join(ROOT, ".gate.lock")):
        print("the gate holds the floor — run this after it finishes")
        return 2
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=DEFAULT_PATH)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show", type=int, default=4, help="examples per rule")
    ap.add_argument("--shards", metavar="DIR", help="also repoint the frozen shelves in DIR/*.db")
    args = ap.parse_args()

    if args.shards:
        return _shards(args.shards, args.dry_run)

    counts: dict = {}
    examples: dict = {}
    out_lines = []
    changed = 0

    with open(args.path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                out_lines.append(line)
                continue
            try:
                card = json.loads(s)
            except ValueError:
                out_lines.append(line)          # not ours to touch
                continue
            d = decide(card)
            if d is None:
                out_lines.append(line)          # byte for byte
                continue
            new_url, rule = d
            old_url = str(((card.get("source") or {}).get("url")) or "")
            if old_url == new_url:
                out_lines.append(line)          # idempotent
                continue
            counts[rule] = counts.get(rule, 0) + 1
            examples.setdefault(rule, []).append((card.get("id"), card.get("title"), old_url, new_url))
            card["source"]["url"] = new_url
            out_lines.append(json.dumps(card, ensure_ascii=False) + "\n")
            changed += 1

    total = sum(counts.values())
    print(f"{'PROPOSED' if args.dry_run else 'APPLIED'} — {total:,} citations\n")
    for rule, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:>6,}  {rule}")
        for cid, title, old, new in examples[rule][:args.show]:
            print(f"          {cid}  {str(title)[:52]}")
            print(f"              {old}")
            print(f"           -> {new or '(no url — the label stands alone)'}")
        print()

    if args.dry_run:
        print("Nothing was written. Re-run without --dry-run to apply.")
        return 0
    if not changed:
        print("Nothing to change — already repointed.")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.writelines(out_lines)
    os.replace(tmp, args.path)                  # atomic
    print(f"wrote {args.path} — {changed:,} cards changed, the rest byte for byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
