"""Graft every card that has no connection at all onto its shelf spine.

The keeping's rule is that nothing is isolated — every card is at least `member_of` its shelf
spine, and 465,991 of 466,006 cards already are. The 15 that were not all came from ONE path: the
tortoise (`find._mint_doc`) wrote `"connections": []`, so every public-domain source it went and
fetched was born an orphan. That leak is fixed at the source; this backfills what it already
stranded.

The graft is FOUND, not authored — "this card is on this shelf" is a fact already in the card, so
there is no risk of the weak-edge failure that the 53-false-edge cleanup exists to prevent.

Deliberately reads the LIVE corpus rather than a hardcoded id list: an earlier tool in this project
assumed a card id that did not exist, and the dry run is what caught it. If nothing is stranded,
this writes nothing and says so.

    python tools/graft_orphans.py --dry-run      # show what would change
    python tools/graft_orphans.py                # write it
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import corpus, find  # noqa: E402


def _store() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data")
    return Path(base) / "web_cache.jsonl"


def main() -> int:
    dry = "--dry-run" in sys.argv
    cards = corpus.default_corpus().cards

    stranded = [(cid, c) for cid, c in cards.items()
                if c.get("kind") != "connection" and not (c.get("connections") or [])]
    if not stranded:
        print("nothing stranded — every card carries at least its nesting. Wrote nothing.")
        return 0

    by_shelf: dict = {}
    for cid, c in stranded:
        by_shelf.setdefault(c.get("shelf") or "?", []).append(cid)

    print(f"stranded cards: {len(stranded)}")
    ungraftable = []
    for shelf, ids in sorted(by_shelf.items()):
        known = shelf in find._SPINES
        print(f"  {shelf:<14} {len(ids):>4}   spine: {find._SPINES.get(shelf, ('(none known)',))[0]}")
        if not known:
            ungraftable.extend(ids)

    if ungraftable:
        # Never invent a home — a spine chosen by guesswork is exactly the authored edge this
        # project forbids. But do not hold the unambiguous cards hostage to the unclear ones
        # either: graft what is certain, name what is not, and exit non-zero so it stays visible.
        print(f"\nNOT GRAFTING {len(ungraftable)} card(s) — their shelf has no considered spine:")
        for cid in ungraftable[:10]:
            print(f"    {cid}  shelf={cards[cid].get('shelf')}  {str(cards[cid].get('title'))[:46]}")
        print("  These need a decision, not a default. Add the shelf to find._SPINES only with a")
        print("  spine that states the material's real authority tier — or remove the cards.")
        stranded = [(cid, c) for cid, c in stranded if (c.get("shelf") or "") in find._SPINES]
        by_shelf = {s: ids for s, ids in by_shelf.items() if s in find._SPINES}
        if not stranded:
            print("\nnothing left that can be grafted safely.")
            return 1

    path = _store()
    have = set()
    if path.exists():
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    have.add(json.loads(ln).get("id"))
                except ValueError:
                    pass

    new_spines = [find._spine_card(s) for s in sorted(by_shelf) if find._spine_card(s)
                  and find._spine_card(s)["id"] not in have]
    print(f"\nspines to write : {[s['id'] for s in new_spines] or 'none (already present)'}")
    print(f"cards to graft  : {len(stranded)}")

    if dry:
        print("\n--dry-run: nothing written.")
        return 0

    # Rewrite the store with the grafts applied, spines first so nothing dangles.
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    graft_ids = {cid for cid, _ in stranded}
    out = []
    for s in new_spines:
        out.append(json.dumps(s, ensure_ascii=False))
    changed = 0
    for ln in lines:
        if not ln.strip():
            continue
        try:
            c = json.loads(ln)
        except ValueError:
            out.append(ln)
            continue
        if c.get("id") in graft_ids and not (c.get("connections") or []):
            c["connections"] = find._member_of(c.get("shelf") or "")
            if c["connections"]:
                changed += 1
        out.append(json.dumps(c, ensure_ascii=False))

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\nwrote {path}  —  {len(new_spines)} spine(s) added, {changed} card(s) grafted.")
    if changed != len(stranded):
        print(f"NOTE: {len(stranded) - changed} stranded card(s) were not in {path.name} — "
              "they come from another source file and still need a home.")
    return 1 if ungraftable else 0


if __name__ == "__main__":
    raise SystemExit(main())
