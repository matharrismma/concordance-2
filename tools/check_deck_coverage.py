#!/usr/bin/env python3
"""Deck ↔ shelf coverage guard — the durable §4 win (consolidation, 2026-09-24).

`decks.py` (the Hare) is a hand-curated retrieval overlay, and it ROTS against the shelves the
seeders actually produce. Two silent failures it cannot see for itself:

  * a DEAD deck token — a deck routes to a shelf that no card carries (the `nuclear physics` space
    typo was one; a query to that deck silently misses those cards);
  * an UNROUTED shelf — a produced content shelf sits in NO deck, so the Hare can never reach it
    (the Floor's 217 theories, the Bible dictionaries and the trades were all unreachable this way
    until deck-4 routed them).

A hermetic unit test cannot know what the seeders produce (they mint shelves dynamically), so the
authoritative check is against the LIVE keeping — the same lesson as the shard rebuild: verify shelf
existence against the corpus, never a grep. This walks the per-shelf counts and reports BOTH failures.
ADDITIVE and read-only: it reports and exits non-zero on drift; it changes nothing and removes no
capability. Run it after any `decks.py` edit, or point it at the box to gate a deploy.

    PYTHONPATH=src python tools/check_deck_coverage.py                                   # local corpus
    PYTHONPATH=src python tools/check_deck_coverage.py --url https://narrowhighway.com   # live /cards/stats
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Infrastructure / edge shelves that are unrouted BY DESIGN — not content a query should reach via a
# deck. `connections` is the found-edges plane; `seals`/`sources`/`spine`/`web_cache`/`growth` are ops
# records; `reference`/`domains` are internal scaffolds. Anything else unrouted is a real finding.
OPS_SHELVES: Set[str] = frozenset({
    "connections", "seals", "sources", "spine", "web_cache", "growth", "reference", "domains",
    "concepts", "atlas", "document_validation",   # internal/meta scaffolds, not query-facing content
})

# Deck shelves whose data is refused by the license gate (not seedable public) — the deck is kept
# (removing it would cut a planned capability). Reported as pending, not as drift. `oeis` is
# CC-BY-NC-SA (non-commercial + share-alike), refused. (`languages` was here until 2026-09-24, when
# it was seeded license-clean from Glottolog CC-BY 4.0 — PHOIBLE's CC-BY-SA phonology stays out.)
PENDING_SHELVES: Set[str] = frozenset({"oeis"})


def coverage(by_shelf: Dict[str, int], deck_shelves: Set[str]) -> Dict[str, object]:
    """The pure diff — testable without a corpus or a network. Given the produced per-shelf counts
    and the union of all deck shelves, return the drift lists (dead tokens, unrouted content) plus
    the pending decks (kept-but-unseeded)."""
    produced = {s for s, n in by_shelf.items() if s and int(n or 0) > 0}
    dead = sorted(s for s in deck_shelves if s not in produced and s not in PENDING_SHELVES)
    pending = sorted(s for s in deck_shelves if s not in produced and s in PENDING_SHELVES)
    unrouted = sorted(s for s in produced if s not in deck_shelves and s not in OPS_SHELVES)
    return {"produced": len(produced), "routed": len(deck_shelves),
            "dead_deck_shelves": dead, "pending_deck_shelves": pending,
            "unrouted_content_shelves": unrouted}


def _by_shelf_live(base_url: str) -> Dict[str, int]:
    url = base_url.rstrip("/") + "/cards/stats"
    with urllib.request.urlopen(url, timeout=30) as r:      # noqa: S310 — operator-run against our box
        return dict(json.loads(r.read().decode("utf-8")).get("by_shelf", {}))


def _by_shelf_local() -> Dict[str, int]:
    from concordance import corpus
    return dict(corpus.stats().get("by_shelf", {}))


def main(argv: List[str]) -> int:
    from concordance import decks
    deck_shelves: Set[str] = set()
    for d in decks._DECKS:
        deck_shelves |= set(d["shelves"])

    if "--url" in argv:
        base = argv[argv.index("--url") + 1]
        print(f"reading live shelf counts from {base}/cards/stats …")
        by_shelf = _by_shelf_live(base)
    else:
        print("reading shelf counts from the local corpus …")
        by_shelf = _by_shelf_local()

    rep = coverage(by_shelf, deck_shelves)
    print(f"\n{rep['produced']} produced shelves · {rep['routed']} deck shelves\n")

    dead = rep["dead_deck_shelves"]
    unrouted = rep["unrouted_content_shelves"]
    pending = rep["pending_deck_shelves"]
    if pending:
        print("PENDING decks (kept; data planned but not yet seeded -- not drift):")
        for s in pending:
            print(f"  [PENDING]  {s}")
    if dead:
        print("DEAD deck tokens (a deck routes here but no card carries this shelf):")
        for s in dead:
            print(f"  [MISSING]  {s}")
    if unrouted:
        print("UNROUTED content shelves (produced, but reachable by NO deck -- route them, or add to "
              "OPS_SHELVES if infrastructure):")
        for s in unrouted:
            print(f"  [UNROUTED] {s}  ({by_shelf.get(s, 0):,} cards)")
    if not dead and not unrouted:
        print("OK: every deck shelf is produced, and every produced content shelf is routed by a deck.")
        return 0
    print(f"\nDRIFT: {len(dead)} dead token(s), {len(unrouted)} unrouted shelf(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
