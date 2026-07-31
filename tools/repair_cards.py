#!/usr/bin/env python3
"""THE ACTING HALF of the card assay — repair one named kind at a time, or retract what is empty.

    PYTHONPATH=src python tools/repair_cards.py --kind render_title --dry-run
    PYTHONPATH=src python tools/repair_cards.py --kind render_title --limit 500
    PYTHONPATH=src python tools/repair_cards.py --retract --by "Matt Harris" --dry-run

Matt, 2026-07-30: *"We need a process of improving or removing cards."* `tools/assay_cards.py` is
the judging half and it changes nothing; this is the half that acts. They stay separate on purpose,
and the separation earned itself on the assay's first run: a truncation rule that was too broad
flagged 157,130 Scripture verses (29% of the library) because a verse is punctuated to carry into
the next one. Report-only meant a bad rule cost one measurement instead of 157,130 edits.

So this tool refuses to be a sweep:

  * ONE `--kind` per run. Never "fix everything the assay found" — every kind is a different
    argument about what is wrong, and they deserve to be judged one at a time.
  * `--dry-run` prints the before and the after, card by card, so a person can read the change
    before it exists.
  * `--limit` bounds a run, and what the limit LEFT is printed. A silent truncation reads as
    "that was all of them".
  * Anything the rule cannot fully parse is COUNTED AND NAMED, never guessed at. The `_xxx`
    retraction (246 cards where a Roman numeral XXX was read as a placeholder) is why.
  * A removal is a retraction card with a reason and a name, never a deletion. The original stays
    exactly where it is.

Atomic write; every line this tool does not change is passed through byte for byte.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
DEFAULT_PATH = os.path.join(ROOT, "data", "cards.jsonl")

from concordance import assay  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

_ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def roman_to_int(s: str):
    """Strict: returns None unless the whole string is a well-formed Roman numeral.

    Deliberately unforgiving. `_xxx` in a citation slug is THIRTY, and reading it as a placeholder
    cost this project a public retraction of 246 cards. A parser that guesses is worse than one
    that declines.
    """
    s = s.lower()
    if not s or any(ch not in _ROMAN for ch in s):
        return None
    total, prev = 0, 0
    for ch in reversed(s):
        v = _ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    # round-trip: only accept a numeral that renders back to itself, so "iiii" or "xxxx" is refused
    return total if int_to_roman(total) == s else None


def int_to_roman(n: int) -> str:
    if n <= 0 or n > 3999:
        return ""
    pairs = ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
             (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i"))
    out = []
    for v, r in pairs:
        while n >= v:
            out.append(r)
            n -= v
    return "".join(out)


# §aur_07_xxiii  ·  §laroch_264  ·  §som_10_giving_in_secret
_SLUG = re.compile(r"§([a-z][a-z0-9]*)_([0-9]{1,3})_([ivxlcdm]{1,12})(?=[:\s]|$)")
_SLUG_NUM = re.compile(r"§([a-z][a-z0-9]*)_([0-9]{1,4})(?=[:\s]|$)")


def render_title(title: str):
    """`Aurelius, Meditations §aur_07_xxiii: Out of Plato.` -> `... 7.23: Out of Plato.`

    Returns (new_title, None) on success, or (None, why-not) when the slug is not one this rule
    can read — a sermon slug like `§som_10_giving_in_secret` carries words, not a section number,
    and inventing "10.?" for it would be a guess.

    EVERY slug in the title, or none of it. A connection card is titled `A → B` and both sides
    carry one; the first version of this rule rewrote only the first and produced
    `Meditations 4.33 → Meditations §aur_08_v`, which is worse than leaving it alone — it reads
    as finished. The dry-run showed it before a single card was written, which is what the
    dry-run is for. If any slug present cannot be read, the whole card is declined.
    """
    spans = []
    for m in _SLUG.finditer(title):
        sec = roman_to_int(m.group(3))
        if sec is None:
            return None, f"unreadable numeral {m.group(3)!r}"
        spans.append((m.start(), m.end(), f"{int(m.group(2))}.{sec}"))
    taken = [(a, b) for a, b, _ in spans]
    for m in _SLUG_NUM.finditer(title):
        if any(a <= m.start() < b for a, b in taken):   # already covered by the fuller pattern
            continue
        spans.append((m.start(), m.end(), m.group(2)))
    if not spans:
        return None, "no slug this rule can read"
    out, last = [], 0
    for a, b, rep in sorted(spans):
        out.append(title[last:a]); out.append(rep); last = b
    out.append(title[last:])
    return "".join(out), None


KINDS = {"render_title": render_title}


def _shards(dirname: str, kind: str, dry: bool, show: int) -> int:
    """A CARD DOES NOT LIVE IN ONE PLACE. 24 shelves are frozen into SQLite shards and rehydrated
    on read, so a repair that only touches cards.jsonl leaves the reader looking at the old card.
    Learnt the hard way on 2026-07-31: 4,039 of 4,743 repointed citations were still broken after
    the file was fixed and both services restarted.

    The server opens these `immutable=1` — a promise the file does not change underneath it — so
    both services MUST be stopped before applying.
    """
    import sqlite3
    from pathlib import Path

    total, per_db, declined, shown = 0, {}, {}, 0
    for db in sorted(Path(dirname).glob("*.db")):
        conn = sqlite3.connect(str(db))
        try:
            updates = []
            for cid, raw in conn.execute("select id, json from cards").fetchall():
                try:
                    card = json.loads(raw)
                except ValueError:
                    continue
                a = assay.assay(card)
                if a["verdict"] != assay.IMPROVABLE or \
                        (a.get("improvement") or {}).get("kind") != kind:
                    continue
                new_title, why = KINDS[kind](str(card.get("title") or ""))
                if new_title is None:
                    declined[why] = declined.get(why, 0) + 1
                    continue
                if shown < show:
                    print(f"  {cid}\n    - {card.get('title')}\n    + {new_title}")
                    shown += 1
                card["title"] = new_title
                updates.append((json.dumps(card, ensure_ascii=False), cid))
            if updates and not dry:
                conn.executemany("update cards set json = ? where id = ?", updates)
                conn.commit()
            per_db[db.name] = len(updates)
            total += len(updates)
        finally:
            conn.close()

    print(f"\n{'PROPOSED' if dry else 'APPLIED'} — {total:,} × {kind} in the frozen shelves")
    for name, n in sorted(per_db.items(), key=lambda x: -x[1]):
        if n:
            print(f"  {n:>6,}  {name}")
    for why, n in sorted(declined.items(), key=lambda x: -x[1]):
        print(f"  {n:>6,}  DECLINED — {why}")
    if dry:
        print("\nNothing was written. Both services must be STOPPED before applying — the shards "
              "are opened immutable.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=DEFAULT_PATH)
    ap.add_argument("--kind", choices=sorted(KINDS), help="the ONE repair to apply")
    ap.add_argument("--retract", action="store_true", help="retract the EMPTY cards (mints a card)")
    ap.add_argument("--by", default="", help="who is doing this — required for --retract")
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show", type=int, default=6)
    ap.add_argument("--shards", metavar="DIR", help="also repair the frozen shelves in DIR/*.db")
    args = ap.parse_args()

    if bool(args.kind) == bool(args.retract):
        print("choose exactly one: --kind <repair> or --retract")
        return 2
    if args.retract and not args.by:
        print("--retract needs --by: no anonymous removals")
        return 2
    if args.shards:
        if args.retract:
            print("--retract writes a new card; the shards hold copies, not the record. "
                  "Retract against cards.jsonl.")
            return 2
        return _shards(args.shards, args.kind, args.dry_run, args.show)

    out_lines, minted = [], []
    done = skipped = left = 0
    declined: dict = {}
    shown = 0

    with open(args.path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                out_lines.append(line)
                continue
            try:
                card = json.loads(s)
            except ValueError:
                out_lines.append(line)
                continue

            a = assay.assay(card)
            want_kind = args.kind and a["verdict"] == assay.IMPROVABLE and \
                (a.get("improvement") or {}).get("kind") == args.kind
            want_retract = args.retract and a["verdict"] == assay.EMPTY
            if not (want_kind or want_retract):
                out_lines.append(line)
                continue

            if args.limit and done >= args.limit:
                left += 1
                out_lines.append(line)
                continue

            if want_kind:
                new_title, why = KINDS[args.kind](str(card.get("title") or ""))
                if new_title is None:
                    declined[why] = declined.get(why, 0) + 1
                    skipped += 1
                    out_lines.append(line)
                    continue
                if shown < args.show:
                    print(f"  {card.get('id')}\n    - {card.get('title')}\n    + {new_title}")
                    shown += 1
                card["title"] = new_title
                out_lines.append(json.dumps(card, ensure_ascii=False) + "\n")
                done += 1
            else:
                r = assay.retraction(str(card.get("id")), a.get("reason") or "", args.by)
                if not r.get("ok"):
                    declined[r.get("error", "?")] = declined.get(r.get("error", "?"), 0) + 1
                    skipped += 1
                    out_lines.append(line)
                    continue
                if shown < args.show:
                    print(f"  RETRACT {card.get('id')}  {str(card.get('title'))[:60]}\n"
                          f"    reason: {a.get('reason')}")
                    shown += 1
                out_lines.append(line)          # the original STAYS — a removal is a record
                minted.append(json.dumps(r["card"], ensure_ascii=False) + "\n")
                done += 1

    what = args.kind or "retraction"
    print(f"\n{'PROPOSED' if args.dry_run else 'APPLIED'} — {done:,} × {what}")
    if minted:
        print(f"  {len(minted):,} retraction card(s) minted; every original left exactly where it is")
    for why, n in sorted(declined.items(), key=lambda x: -x[1]):
        print(f"  {n:>6,}  DECLINED — {why}")
    if left:
        print(f"  {left:,} more match this rule and were NOT touched (--limit {args.limit})")

    if args.dry_run:
        print("\nNothing was written. Re-run without --dry-run to apply.")
        return 0
    if not done:
        print("nothing to do")
        return 0

    tmp = args.path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.writelines(out_lines)
        fh.writelines(minted)
    os.replace(tmp, args.path)
    print(f"wrote {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
