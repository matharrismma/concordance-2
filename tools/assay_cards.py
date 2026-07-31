#!/usr/bin/env python3
"""Run THE CARD ASSAY over the keeping and report. Judges; never changes anything.

    PYTHONPATH=src python tools/assay_cards.py            # the whole library
    PYTHONPATH=src python tools/assay_cards.py --shelf lexicon
    PYTHONPATH=src python tools/assay_cards.py --worklist > worklist.txt

Matt, 2026-07-30: *"We need a process of improving or removing cards."* This is the judging half.
Acting on a verdict — repairing a card, or retracting one with `assay.retraction()` — is a separate
and explicit step, on purpose: a rule that both judges and executes can eat a library before anyone
reads its output.

That separation earned itself on the first run. The truncation rule was too broad and flagged
157,130 cards (29% of the library) that turned out to be Scripture verses ending in a comma, because
a verse is punctuated to carry into the next one. Report-only meant a bad rule cost one measurement
instead of 157,130 edits. See `src/concordance/assay.py` for the narrowed rule and why.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import assay, corpus  # noqa: E402

# The library holds Hebrew, Greek, and typographic punctuation; a Windows console is cp1252 and
# raises on the first of them. Report on what the cards SAY, not on what the terminal can render.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001 — a stream that cannot be reconfigured is already fine
    pass


def main() -> int:
    args = sys.argv[1:]
    shelf = args[args.index("--shelf") + 1] if "--shelf" in args else None
    worklist = "--worklist" in args

    c0 = corpus.default_corpus()
    cards = list(c0.cards.values()) if hasattr(c0, "cards") else []
    if shelf:
        cards = [c for c in cards if (c or {}).get("shelf") == shelf]
    if not cards:
        print(f"no cards{' on shelf ' + shelf if shelf else ''} — nothing to assay")
        return 1

    if worklist:
        # One line per card that has a named repair — feed it to whoever does the work.
        for c in cards:
            a = assay.assay(c)
            if a["verdict"] == assay.IMPROVABLE:
                imp = a.get("improvement") or {}
                print(f"{imp.get('kind','?')}\t{c.get('id')}\t{imp.get('how','')}")
        return 0

    # Check what each card PROMISES too, not only what it says. Resolvers are injected so the
    # module stays I/O-free; the seal store and the corpus are the caller's business.
    from concordance import cas
    s = assay.survey(cards, resolve_card=corpus.get_card, resolve_seal=cas.fetch)
    total = s["total"]
    print(f"THE CARD ASSAY — {total:,} cards{' on ' + shelf if shelf else ''}\n")
    for v in (assay.STANDS, assay.IMPROVABLE, assay.CANNOT_CHECK, assay.EMPTY):
        n = s["counts"].get(v, 0)
        print(f"  {v:<13} {n:>8,}  {100 * n / total:5.1f}%")

    if s["improvements"]:
        print("\n  repairs available (each names what to do):")
        for k, n in sorted(s["improvements"].items(), key=lambda x: -x[1]):
            print(f"     {n:>8,}  {k}")

    for v in (assay.EMPTY, assay.CANNOT_CHECK, assay.IMPROVABLE):
        for e in s["examples"].get(v, []):
            print(f"\n  {v}: {e['id']}\n     {e['title']}\n     → {e['reason']}")

    # The shelves carrying the most unfinished work — where a person should start.
    worst = sorted(((sh, d.get(assay.IMPROVABLE, 0) + d.get(assay.EMPTY, 0))
                    for sh, d in s["by_shelf"].items()), key=lambda x: -x[1])[:8]
    if worst and worst[0][1]:
        print("\n  shelves with the most work waiting:")
        for sh, n in worst:
            if n:
                print(f"     {n:>8,}  {sh}")

    if s.get("broken_promises"):
        print(f"\n  BROKEN PROMISES — {s['cards_with_a_broken_promise']:,} cards point at "
              f"something that does not arrive:")
        for k, n in sorted(s["broken_promises"].items(), key=lambda x: -x[1]):
            print(f"     {n:>8,}  {k}")
    if s.get("unchecked"):
        print(f"\n  NOT CHECKED (never counted as sound): {', '.join(s['unchecked'])}")

    removable = s["counts"].get(assay.EMPTY, 0)
    print(f"\n  Nothing here is removed by running this. {removable:,} card(s) hold no content; "
          f"retiring one is a separate act that mints a `retracts` card with a reason.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
