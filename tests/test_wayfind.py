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


def test_floorplan_is_on_topic(real_corpus):
    # Was "guarded on a provisioned corpus (some envs isolate data)" — an `if not search: return`
    # that reported a pass. Measured 2026-08-03: under the gate the corpus is ALWAYS empty, so
    # this assertion had never run. The real_corpus fixture provisions it, so it runs now.
    from concordance import corpus
    assert corpus.search("water", limit=1), "the real corpus must answer 'water'"
    r = wayfind.path(q="how to purify water")
    assert r["here"] is not None, "wayfind found no neighbourhood in the real keeping"
    assert isinstance(r["near"], list)
    # every "toward" room is drawn from "near" (the connected neighborhood) — never off-topic
    near_ids = {n["id"] for n in r["near"]}
    assert all(t["id"] in near_ids for t in r["toward"]), "toward must stay within the neighborhood"
