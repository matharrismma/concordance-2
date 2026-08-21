"""Serve — a member's wants become the hive's work, and genuine answers come back.

returns() keeps only real matches (a gap stays a gap); take() opens deduped hive wants. Pure — search
and relevance are injected for returns; take writes to a temp keeping.
"""
from concordance import serve


def test_returns_keeps_only_genuine_matches():
    fire = {"id": "c1", "title": "Making and keeping a fire", "shelf": "survival"}
    knot = {"id": "c2", "title": "The knots worth knowing", "shelf": "survival"}
    r = serve.returns(
        ["start a fire", "tan a deer hide"],
        search_fn=lambda q, n: [fire, knot] if "fire" in q else [],
        relevant_fn=lambda q, c: "fire" in c["title"].lower())
    assert r["met"] == 1 and r["of"] == 2
    met = next(s for s in r["served"] if s["want"] == "start a fire")
    assert met["met"] and met["cards"][0]["id"] == "c1"          # a genuine answer came back
    seeking = next(s for s in r["served"] if s["want"] == "tan a deer hide")
    assert seeking["met"] is False and seeking["cards"] == []    # still sought — honest, not faked


def test_take_opens_deduped_hive_wants(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = serve.take(["a manual on digging wells", "how to keep bees", "x"])   # 'x' too short -> skipped
    assert r["count"] == 2 and len(r["opened"]) == 2
    again = serve.take(["a manual on digging wells", "how to keep bees"])    # deduped by the hive
    assert set(again["opened"]) == set(r["opened"])             # same wants -> same ids, no spam


def test_returns_is_honest_when_the_keeping_is_empty():
    r = serve.returns(["anything at all"], search_fn=lambda q, n: [], relevant_fn=lambda q, c: True)
    assert r["met"] == 0 and r["served"][0]["cards"] == []
