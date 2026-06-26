"""Corpus ranker test (primitive #7) — relevance + the surface filter.

Proves: a query surfaces the relevant card; the secular reach excludes witness-tagged
cards while the witness surface includes them; an empty query returns nothing. Uses a
small inline fixture with min_idf=0 (the production distinctiveness floor is tuned for a
large corpus). Runnable with `pytest` OR `python tests/test_corpus.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.corpus import Corpus  # noqa: E402

FIXTURE = {
    "c1": {"id": "c1", "title": "Photosynthesis", "surface": "secular", "shelf": "classics",
           "body": "plants convert sunlight into chemical energy via chlorophyll"},
    "c2": {"id": "c2", "title": "The Trinity", "surface": "witness", "shelf": "codex",
           "body": "Father Son and Holy Spirit, one God in three persons"},
    "c3": {"id": "c3", "title": "Mitochondria", "surface": "secular", "shelf": "classics",
           "body": "the powerhouse of the cell produces ATP, the energy currency"},
}


def _corpus():
    return Corpus(FIXTURE, min_idf=0.0)  # tiny fixture -> disable the large-corpus floor


def test_relevance_ranks_the_right_card():
    res = _corpus().search("chlorophyll sunlight")
    assert res and res[0]["id"] == "c1", res


def test_keeping_is_shared_includes_religious_cards():
    # the keeping is one shared library — the .com includes the religious cards too
    # (Matt, 2026-06-26: "the religious cards can be included"; "we are not hiding")
    res = _corpus().search("Trinity Father Spirit God")
    assert any(r["id"] == "c2" for r in res), "the shared keeping should include the witness card"


def test_optional_secular_only_view():
    # include_witness=False is the optional scrubbed view, should a caller want it
    res = _corpus().search("Trinity Father Spirit God", include_witness=False)
    assert all(r.get("surface") != "witness" for r in res), res
    assert not any(r["id"] == "c2" for r in res)


def test_empty_query_returns_nothing():
    assert _corpus().search("") == []


def test_limit_respected():
    res = _corpus().search("energy", limit=1)
    assert len(res) <= 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} corpus tests passed — ranked retrieval + the surface filter hold.")
