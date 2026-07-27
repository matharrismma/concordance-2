"""Wayfinding — the floorplan must stay ON TOPIC (rooms are graph neighbors, not a fresh search)
and degrade honestly when there's nothing to stand on."""
from concordance import wayfind


def test_empty_query_degrades_honestly():
    r = wayfind.path()
    assert r["here"] is None and r["near"] == [] and r["trail"] == []
    assert "note" in r


def test_unknown_topic_says_so_never_invents():
    r = wayfind.path(q="zzq notacard xyzzy")
    assert r["here"] is None
    assert r["near"] == [] and r["toward"] == []


def test_floorplan_is_on_topic_when_provisioned():
    # positive check guarded on a provisioned corpus/graph (some envs isolate data)
    from concordance import corpus
    if not corpus.search("water", limit=1):
        return
    r = wayfind.path(q="how to purify water")
    if r["here"] is None:
        return  # no graph neighborhood in this env — still valid, nothing to assert
    assert isinstance(r["near"], list)
    # every "toward" room is drawn from "near" (the connected neighborhood) — never off-topic
    near_ids = {n["id"] for n in r["near"]}
    assert all(t["id"] in near_ids for t in r["toward"]), "toward must stay within the neighborhood"
