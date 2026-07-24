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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-floor-"))

from concordance import corpus, floor  # noqa: E402

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


def _pin(monkey_cards):
    cor = corpus.default_corpus()
    cor.cards.update(monkey_cards)          # add the tiny fixture into the live corpus for the test
    return cor


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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} floor tests passed — the design is visible, rooted, and turns the eye upward.")
