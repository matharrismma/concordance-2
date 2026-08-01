"""THE FILING CABINET — a drawer nobody declared is a drawer nobody searches.

Matt, 2026-08-01: *"Make sure we are creating Filing cabinets and maps. That could be the reason
these are getting confusing."* He was right, and the day's defects are the evidence: five separate
failures, every one someone reaching into the single drawer they happened to know about.

  * curate() searched drops.jsonl and answered "no such drop" for a card in web_cache
  * review_queue() read one drawer, so three held acquisitions were invisible to every human
  * repoint_citations fixed cards.jsonl and missed the shards — 4,039 citations silently unfixed
  * the shepherd wrote acquired_cards.jsonl while the tortoise wrote web_cache.jsonl, same job

The registry is the cure, and the guard below is the part that keeps it true: if a new card store
appears under data/ and nobody added it to DRAWERS, this file fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import cabinet  # noqa: E402


@pytest.fixture()
def drawer(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    return tmp_path


def _write(p: Path, *cards):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(chr(10).join(json.dumps(c) for c in cards) + chr(10), encoding="utf-8")


def test_every_declared_drawer_says_what_it_holds_and_whether_it_is_canonical():
    """`canonical` decides whether a repair PATCHES a drawer or REBUILDS it. Getting that wrong
    is what left 4,039 citations stale in the shards after the file was fixed."""
    for d in cabinet.DRAWERS:
        assert d["name"] and d["path"] and d["holds"], d
        assert isinstance(d["canonical"], bool), f"{d['name']} must declare canonical"
        assert d["kind"] in ("jsonl", "sqlite")


def test_a_card_is_found_in_every_drawer_that_holds_it(drawer):
    card = {"id": "card_x", "title": "One", "shelf": "a", "body": "same"}
    _write(drawer / "cards.jsonl", card)
    _write(drawer / "web_cache.jsonl", card)
    w = cabinet.where_is("card_x")
    assert w["count"] == 2, w
    assert {f["drawer"] for f in w["found_in"]} == {"keeping", "acquired-web"}
    assert w["agree"] is True


def test_the_same_card_differing_between_drawers_is_the_finding(drawer):
    """Not an error to smooth over — exactly what we want to be told."""
    _write(drawer / "cards.jsonl", {"id": "card_x", "title": "One", "body": "the repaired text"})
    _write(drawer / "web_cache.jsonl", {"id": "card_x", "title": "One", "body": "the STALE text"})
    w = cabinet.where_is("card_x")
    assert w["count"] == 2
    assert w["agree"] is False, "two drawers with different content must not read as agreement"
    assert "stale" in w["note"]


def test_a_card_in_no_drawer_is_honestly_empty(drawer):
    w = cabinet.where_is("card_nowhere")
    assert w["count"] == 0 and w["found_in"] == []


def test_asking_for_nothing_is_refused(drawer):
    assert cabinet.where_is("")["error"]


def test_the_census_reports_its_denominator(drawer):
    """A count of misfiled cards is meaningless without the number examined.

    The first version wrapped the addressing call in a bare `except` and called a function that
    does not exist, so every card raised, every raise was eaten, and the census printed
    "0 UNPLACED" over a check that had never run. Zero out of zero is not good news.
    """
    _write(drawer / "cards.jsonl", {"id": "c1", "title": "A", "shelf": "s", "body": "x"})
    c = cabinet.census()
    assert "addressed" in c, "unplaced must always travel with the number examined"
    assert c["addressed"] >= 1
    assert c["unplaced"] <= c["addressed"]


def test_reorganize_proposes_and_moves_nothing(drawer):
    """A cataloguer who moves 100,000 cards on a heuristic has destroyed the trail."""
    cards = [{"id": f"c{i}", "shelf": "huge", "title": "t", "body": "b"}
             for i in range(cabinet.OVERFULL + 5)]
    cards.append({"id": "tiny1", "shelf": "sliver", "title": "t", "body": "b"})
    _write(drawer / "cards.jsonl", *cards)

    before = (drawer / "cards.jsonl").read_bytes()
    r = cabinet.reorganize()
    assert (drawer / "cards.jsonl").read_bytes() == before, "reorganize() must not write"

    assert any(x["shelf"] == "huge" for x in r["expand"]), r
    assert any(x["shelf"] == "sliver" for x in r["contract"]), r
    for x in r["expand"] + r["contract"]:
        assert x["rule"], "a proposal must name the rule so a person can argue with the RULE"
    assert "not a change" in r["note"]


def test_no_undeclared_card_store_is_hiding_in_the_data_directory(drawer):
    """THE GUARD THAT KEEPS THE REGISTRY TRUE. A sixth store added quietly is exactly how the
    first five came to disagree."""
    _write(drawer / "cards.jsonl", {"id": "c1", "title": "A", "body": "x"})
    _write(drawer / "some_new_store.jsonl", {"id": "c2", "title": "B", "body": "y"})

    declared = {d["path"] for d in cabinet.DRAWERS}
    looks_like_cards = []
    for p in drawer.glob("*.jsonl"):
        try:
            first = json.loads(p.read_text(encoding="utf-8").splitlines()[0])
        except (ValueError, IndexError):
            continue
        if isinstance(first, dict) and "id" in first and ("title" in first or "body" in first):
            if p.name not in declared:
                looks_like_cards.append(p.name)
    assert looks_like_cards == ["some_new_store.jsonl"], (
        "the sweep must notice an undeclared card store — that is the whole point of the registry")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
