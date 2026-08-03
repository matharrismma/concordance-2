"""The floor, made visible — the structure behind /floor.html.

Guards: the rooted design walks DOWN from the Floor of Discovery via the nesting's directional
edges (bounded, with real child-counts); the two-tree grafts are labelled correctly (science vs.
Scripture); and the payload carries the crown verse (Proverbs 9:10) — so seeing the design turns
the eye upward.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-floor-"))

from concordance import corpus, floor, graph  # noqa: E402

# a tiny floor: the root, a spine that contains it, and members hanging off the spine
_CARDS = {
    floor.ROOT: {"id": floor.ROOT, "title": "The Floor of Discovery", "shelf": "codex",
                 "connections": [{"to_card_id": "sp", "relationship": "contains"}]},
    "sp": {"id": "sp", "title": "The created order — the science of the floor", "shelf": "science",
           "connections": [{"to_card_id": floor.ROOT, "relationship": "nested_in"},
                           {"to_card_id": "el1", "relationship": "has_member"},
                           {"to_card_id": "el2", "relationship": "has_member"}]},
    "el1": {"id": "el1", "title": "Hydrogen (H) — element 1", "shelf": "chemistry",
            "connections": [{"to_card_id": "sp", "relationship": "member_of"},
                            {"to_card_id": "eas", "relationship": "names_the_created_thing"}]},
    "el2": {"id": "el2", "title": "Gold (Au) — element 79", "shelf": "chemistry", "connections": []},
    "eas": {"id": "eas", "title": "Easton: Hydrogen", "shelf": "dictionary",
            "connections": [{"to_card_id": "el1", "relationship": "names_the_created_thing"}]},
}


_ABSENT = object()


def _pin(monkey_cards):
    cor = corpus.default_corpus()
    cor.cards.update(monkey_cards)          # add the tiny fixture into the live corpus for the test
    return cor


def _snapshot(ids):
    cards = corpus.default_corpus().cards
    return {i: cards.get(i, _ABSENT) for i in ids}


def _restore(snap):
    """Put back exactly what was there — including cards the fixture OVERWROTE, not only the ones
    it added. Measured on 2026-08-03: card_k_floor_of_discovery is a real card carrying 70
    relations, and the fixture replaced it with a stand-in carrying 1."""
    cards = corpus.default_corpus().cards
    for i, prior in snap.items():
        if prior is _ABSENT:
            cards.pop(i, None)
        else:
            cards[i] = prior
    # graph.overview() memoizes into a module-global. A memo computed while the fixture was in
    # place is a lie for every later reader, so the cache dies with the fixture.
    graph._GRAPH = None


@pytest.fixture(autouse=True)
def _leave_the_corpus_as_we_found_it():
    """These tests pin a tiny fake floor into the PROCESS-WIDE corpus singleton. Without this,
    the fixture outlives the test.

    The symptom was a mystery failure elsewhere: tests/test_reachable_from_the_floor.py asserts
    that no card carries zero relations, and it failed with "1 card(s)" whenever it happened to
    run after this file — because the fixture's `el2` (Gold) is defined with connections: [] and
    graph.overview() counts exactly that. Run alone it passed; run in the suite it failed; the
    full gate passed only because the ordering happened to be kind. That is the worst shape a
    defect can take, so the cleanup is a fixture rather than a convention someone must remember.
    """
    snap = _snapshot(_CARDS)
    try:
        yield
    finally:
        _restore(snap)


def test_the_tree_roots_in_the_floor_and_walks_down():
    _pin(_CARDS)
    t = floor.tree(max_depth=4, max_children=10)
    assert t and t["id"] == floor.ROOT
    spine = t["children"][0]
    assert "created order" in spine["title"]
    assert spine["child_count"] == 2                 # two elements hang from it
    titles = {c["title"] for c in spine["children"]}
    assert any("Hydrogen" in x for x in titles)
    # the parent is never re-descended into from a child (no cycles)
    assert all(c["id"] != floor.ROOT for c in spine["children"])


def test_grafts_label_science_and_scripture_correctly():
    _pin(_CARDS)
    g = floor.grafts()
    hit = next((x for x in g if "Hydrogen" in x["science"]), None)
    assert hit and "element" in hit["science"].lower()      # the element is the SCIENCE side
    assert "Easton" in hit["scripture"]                     # the dictionary card is the SCRIPTURE side


def test_payload_carries_the_crown_verse_and_stays_a_conduit():
    _pin(_CARDS)
    p = floor.payload()
    assert p["verse"]["ref"] == "Proverbs 9:10"
    assert "fear of the LORD" in p["verse"]["text"]
    assert "does not generate" in p["note"] and p["root"]["id"] == floor.ROOT


def test_the_fixture_is_fully_reversible():
    """The cleanup is itself load-bearing, so it gets a test rather than trust.

    Guards both halves: a card the fixture ADDED must be gone afterwards, and a card it
    OVERWROTE must be the original object again — not a copy, not a rebuild.
    """
    cards = corpus.default_corpus().cards
    before = _snapshot(_CARDS)
    _pin(_CARDS)
    assert cards["el2"] is _CARDS["el2"]                    # the fixture really is in place
    assert cards[floor.ROOT] is _CARDS[floor.ROOT]          # ...including over a real card

    _restore(before)
    for cid, prior in before.items():
        if prior is _ABSENT:
            assert cid not in cards, f"{cid} was added by the fixture and outlived it"
        else:
            assert cards[cid] is prior, f"{cid} was overwritten and not put back"
    assert graph._GRAPH is None, "a memo built over the fixture survived the cleanup"


def test_no_card_the_fixture_pins_carries_zero_relations_afterwards():
    """The exact invariant whose breach caused the mystery failure, asserted at the source.

    tests/test_reachable_from_the_floor.py owns this rule for the whole corpus; this checks that
    THIS file stops being the thing that breaks it.
    """
    _pin(_CARDS)
    _restore(_snapshot({}))          # no-op restore: only clears the memo
    _restore({cid: _ABSENT for cid in _CARDS if cid != floor.ROOT})
    cards = corpus.default_corpus().cards
    assert "el2" not in cards
    assert graph.overview()["isolated_nodes"] == 0


if __name__ == "__main__":
    # The autouse fixture only runs under pytest, so the standalone runner does the same cleanup
    # by hand — otherwise this path quietly reintroduces the very leak the fixture removes.
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        _snap = _snapshot(_CARDS)
        try:
            fn()
        finally:
            _restore(_snap)
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} floor tests passed — the design is visible, rooted, and turns the eye upward.")
