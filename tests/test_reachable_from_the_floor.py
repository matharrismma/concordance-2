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
  * `isolated` (carries NO relation at all) must be **0**. Strict, and currently true.
  * `unreachable from the Floor` is **not** zero — 552 cards sit in closed ISLANDS: codex notes and
    Boethius sections bound to one another by `same_section` with no edge out to anything rooted.
    None of their edges dangle; the clusters are simply unrooted. Grafting e.g. the codex note
    "Revelation 5" to its scripture card is a real relation, but CHOOSING that match is authoring,
    not finding — so this ratchets the number instead of pretending it is solved. If it drops, lower
    the constant. If it rises, something new was stranded and that is a regression.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"

# Measured 2026-07-28 against the local corpus. A RATCHET, not a target: never let it grow.
KNOWN_ISLAND_CARDS = 552


def _walk():
    from concordance import corpus
    cards = corpus.default_corpus().cards
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
    from concordance import corpus
    assert FLOOR in corpus.default_corpus().cards, "the Floor is missing — the walk would be meaningless"


def test_nothing_carries_no_relation_at_all():
    """The strict invariant. `graph.overview()` reports this cheaply as `isolated_nodes`."""
    from concordance import graph
    o = graph.overview()
    assert o["isolated_nodes"] == 0, (
        f"{o['isolated_nodes']} card(s) carry no relation at all — see tools/graft_orphans.py, and "
        f"fix the path that created them")


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
