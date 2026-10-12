"""Verse-range overlap in the roots concordance (Matt, 2026-10-11).

A node rooted to a PASSAGE (a range, or a whole chapter) must surface for any verse inside it — so a
reader who lands on Ephesians 4:5 sees the node rooted to Ephesians 4:4-6, and the Console (which
weaves one verse at a time) shows the connection wherever they are in the passage. Overlap is a strict
SUPERSET of the old exact match: an exact ref still matches, and a verse outside the passage never does.
Self-contained: anchors written to a tmp data dir with verify=False, so no Bible is needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import roots  # noqa: E402

NODE = "floor:card_floor_x"


def _nodes(ref, data_dir):
    return [n["node"] for n in roots.nodes_rooted_at(ref, data_dir=data_dir)]


def test_verse_inside_range_matches(tmp_path):
    roots.anchor(NODE, ["Ephesians 4:4-6"], verify=False, data_dir=tmp_path)
    for v in ("Ephesians 4:4", "Ephesians 4:5", "Ephesians 4:6"):
        assert NODE in _nodes(v, tmp_path), v


def test_verse_outside_range_does_not_match(tmp_path):
    roots.anchor(NODE, ["Ephesians 4:4-6"], verify=False, data_dir=tmp_path)
    for v in ("Ephesians 4:3", "Ephesians 4:7", "Ephesians 5:5", "Ephesians 3:5"):
        assert NODE not in _nodes(v, tmp_path), v


def test_chapter_query_gathers_its_verses(tmp_path):
    roots.anchor(NODE, ["Genesis 11:1-9"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Genesis 11", tmp_path)        # the whole chapter gathers the ranged node
    assert NODE in _nodes("Genesis 11:5", tmp_path)
    assert NODE not in _nodes("Genesis 12", tmp_path)


def test_whole_chapter_anchor_matches_any_of_its_verses(tmp_path):
    roots.anchor(NODE, ["Psalm 19"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Psalm 19:1", tmp_path)
    assert NODE in _nodes("Psalm 19:14", tmp_path)
    assert NODE not in _nodes("Psalm 20:1", tmp_path)


def test_exact_ref_still_matches(tmp_path):
    roots.anchor(NODE, ["Genesis 1:1"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Genesis 1:1", tmp_path)
    assert NODE in _nodes("genesis  1:1", tmp_path)       # the old loose normal form still holds
    assert NODE not in _nodes("Genesis 1:2", tmp_path)


def test_different_book_does_not_match(tmp_path):
    roots.anchor(NODE, ["John 3:16"], verify=False, data_dir=tmp_path)
    assert NODE not in _nodes("Mark 3:16", tmp_path)


def test_one_chapter_book_bare_verse_matches(tmp_path):
    # a one-chapter book is normally cited "Jude 3" (the number is the VERSE); the stored form is "Jude 1:3"
    roots.anchor(NODE, ["Jude 1:3"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Jude 3", tmp_path)
    assert NODE in _nodes("Jude 1:3", tmp_path)
    assert NODE not in _nodes("Jude 4", tmp_path)
    # a verse inside a one-chapter-book range, cited bare
    roots.anchor(NODE, ["Philemon 1:4-7"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Philemon 6", tmp_path)


def test_book_alias_and_singular_plural_fold(tmp_path):
    roots.anchor(NODE, ["Psalms 23:1"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Psalm 23:1", tmp_path)        # singular spelling, the common query form
    assert NODE not in _nodes("Psalm 24:1", tmp_path)
    roots.anchor(NODE, ["Genesis 1:1"], verify=False, data_dir=tmp_path)
    assert NODE in _nodes("Gen 1:1", tmp_path)           # abbreviation folds to the canonical book


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
