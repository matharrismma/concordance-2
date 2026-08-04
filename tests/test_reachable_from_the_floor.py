"""Everything can be walked back to the Floor — and where it cannot, the number does not grow.

Contract §5.3 asks that every spine be reachable from the Floor. The overview's counts answer a
weaker question cheaply (does a card carry any relation at all?), and this file answers the real one
expensively: starting at `card_k_floor_of_discovery` and walking BOTH planes — the nesting skeleton
and the semantic edges — what does the keeping actually reach?

Why the real check lives HERE and not in `graph.overview()`: measured 2026-07-28, building the
undirected adjacency and running the BFS costs **11.7 s and ~162 MB peak**. `overview()` serves a
public endpoint on services already holding ~2.8 GB RSS, so paying that on a request — even once,
memoized — is the wrong trade. The gate can afford twelve seconds; a reader cannot.

The state it pins, honestly:
  * `isolated` (carries NO relation at all) must be **0**. Strict, and true.
  * `unreachable from the Floor` must also be **0** — RESOLVED 2026-07-28. The 552 island cards
    (codex notes and Boethius sections bound by `same_section`, on 1.0-era shelves minted before the
    spine convention) were rooted by Matt's decision with SHELF SPINES — the found relation, same
    rule as the tortoise fix: "this card is on this shelf" is a fact the card already carries.
    `tools/graft_shelf_spines.py` minted nine spines rooted in the Floor, redirected dictionary's
    and chemistry's bare cards to their siblings' established parents, and grafted 5,187 cards.
    The per-card scripture matching (codex "Revelation 5" -> that scripture card) remains NOT done —
    choosing the match is authoring, and rooting did not require it.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"

# Was 552 (measured 2026-07-28); lowered to 0 the same day after the shelf-spine graft. A RATCHET:
# any rise means something new was stranded, and the fix is the minting path, not this constant.
KNOWN_ISLAND_CARDS = 0

# THE REAL KEEPING, LOADED HERE, ON PURPOSE.
#
# This file may not read corpus.default_corpus(). That singleton is built once per process from
# whatever CONCORDANCE_DATA_DIR happened to be set when it was first touched, and 53 test modules
# point that variable at a scratch temp directory in their import preamble. Which corpus wins is
# therefore a race, settled differently depending on what else was collected.
#
# MEASURED with tools/vacuity_plugin.py over the whole suite: under the FULL gate the singleton
# does hold the real keeping — 182 tests called default_corpus() and none received an empty one.
# An earlier version of this comment claimed the gate was walking an empty corpus; that came from
# a subset run and was wrong. But in any SUBSET run the hijack does win, this file walks nothing,
# and a walk over nothing finds nothing wrong and reports a pass.
#
# Discovered 2026-08-03 while fixing the missing teardown in tests/test_floor.py, whose five-card
# fixture DID leak into this file's walk and made it fail or pass by collection order. A guarantee
# that the whole keeping is reachable is worth nothing if the reader cannot tell which corpus
# produced it.
#
# So the real cards are loaded straight from the repo's data directory, once, independent of the
# singleton and of every sibling's environment. The docstring's 11.7 s is the honest price.
def _real_cards():
    """One shared loader, in tests/conftest.py — see the note there for why it must not be the
    process-wide singleton. Imported lazily so this file still runs directly, not only under
    pytest."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from conftest import real_cards
    return real_cards()


def _walk():
    cards = _real_cards()
    adj: dict = {}
    for cid, c in cards.items():
        if c.get("kind") == "connection":
            continue
        for l in (c.get("connections") or []):
            t = l.get("to_card_id")
            if not t:
                continue
            adj.setdefault(cid, set()).add(t)
            adj.setdefault(t, set()).add(cid)
    seen = {FLOOR}
    q = deque([FLOOR])
    while q:
        x = q.popleft()
        for y in adj.get(x, ()):
            if y not in seen:
                seen.add(y)
                q.append(y)
    return cards, seen


def test_the_floor_itself_is_in_the_keeping():
    """If the Floor id ever changes, every assertion below would pass vacuously on an empty walk."""
    cards = _real_cards()
    assert FLOOR in cards, "the Floor is missing — the walk would be meaningless"
    # ...and the corpus must be the real one. Five cards is not a keeping, and a walk over five
    # cards that reports success is exactly the vacuous pass the line above exists to prevent.
    assert len(cards) > 100_000, (
        f"only {len(cards):,} cards loaded — this file must measure the REAL keeping, not a "
        f"fixture. Check that data/ is present and that nothing redirected the load.")


def test_nothing_carries_no_relation_at_all():
    """The strict invariant: no card carries zero relations.

    Computed here from the real cards rather than read from `graph.overview()`. The overview is
    memoized off the process-wide corpus singleton, so it answers for whatever that singleton
    happened to hold — which included tests/test_floor.py's five-card fixture whenever that file
    ran first, and that is precisely how this invariant came to report `1` for a card no one had
    added to the keeping. Same definition as the overview's `isolated_nodes`: a card carrying no
    outbound relation at all.
    """
    cards = _real_cards()
    isolated = [cid for cid, c in cards.items()
                if c.get("kind") != "connection" and not (c.get("connections") or [])]
    assert not isolated, (
        f"{len(isolated)} card(s) carry no relation at all — e.g. {isolated[:5]} — see "
        f"tools/graft_orphans.py, and fix the path that created them")


def test_the_overview_buckets_account_for_every_card():
    """nested + semantic_only + isolated == total, exactly — so no category can hide in a
    difference. (The mistake this guards against was made on 2026-07-28: `connected_nodes` was read
    as an orphan count, and 313,944 fully-nested cards were reported as unconnected.)"""
    from concordance import graph
    o = graph.overview()
    assert o["nested_nodes"] + o["semantic_only_nodes"] + o["isolated_nodes"] == o["total_nodes"]
    for c in o["clusters"]:
        assert c["nested"] + c["semantic_only"] + c["isolated"] == c["count"], c["shelf"]


def test_every_count_says_what_it_counted():
    """A number without a `means` is a number waiting to be misread — the /capabilities rule."""
    from concordance import graph
    m = graph.overview().get("means") or {}
    for k in ("total_nodes", "total_edges", "connected_nodes", "nested_nodes",
              "semantic_only_nodes", "isolated_nodes"):
        assert m.get(k), f"{k} is reported with no explanation of what it counted"
    assert "NOT unconnected" in m["connected_nodes"], (
        "connected_nodes must warn against the exact misreading that happened")


def test_the_unrooted_islands_do_not_grow():
    cards, seen = _walk()
    unreachable = [(cid, c.get("shelf")) for cid, c in cards.items()
                   if c.get("kind") != "connection" and cid not in seen]
    by_shelf = Counter(s for _, s in unreachable)
    assert len(unreachable) <= KNOWN_ISLAND_CARDS, (
        f"unrooted cards grew to {len(unreachable)} (was {KNOWN_ISLAND_CARDS}) — something new was "
        f"stranded in an island that never reaches the Floor. By shelf: {by_shelf.most_common(6)}")


def test_the_islands_are_unrooted_not_broken():
    """Their edges all point at cards that EXIST — the clusters are whole, just not grafted. If this
    ever fails, the problem is dangling references, which is a different (worse) bug."""
    cards, seen = _walk()
    dangling = [(cid, l.get("to_card_id")) for cid, c in cards.items()
                if c.get("kind") != "connection" and cid not in seen
                for l in (c.get("connections") or [])
                if l.get("to_card_id") not in cards]
    assert not dangling, f"{len(dangling)} edge(s) point at cards that do not exist: {dangling[:5]}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the walk from the Floor is measured, not assumed.")
